"""Refresh data/weapon-presets.js from the official HoYoLAB ZZZ Wiki.

Scans the wiki entry_page_id space through the public content API, keeps every
page whose 晋升需求 table uses the weapon-specific 突破前基础 / 突破后基础 keys,
extracts the level-60 (0 突破) base ATK and the fixed high-level substat, and
rewrites window.WEAPON_PRESETS.

Usage:
    python .github/skills/read-zzz-engine-stats/scripts/refresh_weapon_presets.py
    python .github/skills/read-zzz-engine-stats/scripts/refresh_weapon_presets.py --max-id 2600
"""

import argparse
import json
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

API = "https://act-api-takumi.mihoyo.com/hoyowiki/zzz/wapi/entry_page_v2?entry_page_id={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://baike.mihoyo.com/",
    "x-rpc-wiki_app": "zzz",
}
OUTPUT = "data/weapon-presets.js"

# 初始面板：基础攻击力+50 暴击伤害+19.2%   满级面板：基础攻击力+743 暴击伤害+48%
# 锋御 engines use 基础防御力 instead of 基础攻击力 (初始面板：基础防御力+29  防御力+19.2%).
# 异常精通 substats carry no % sign, so the percent group is optional.
PANEL_RE = re.compile(
    r"(初始面板|满级面板)[：:]\s*基础(攻击力|防御力)\+?([\d.]+)\s*([一-龥A-Za-z]+)\+([\d.]+)(%?)"
)
ATK_RE = re.compile(r"(?:基础)?攻击力\+?([\d.]+)")
TAG_RE = re.compile(r"\[(强攻|异常|防护|命破|击破|支援|锋御)\]")

SUBSTAT_TO_CALCULATOR = {
    "暴击伤害": ("cd", "pct"),
    "暴击率": ("cr", "pct"),
    "攻击力": ("atk_pct", "pct"),
    "生命值": ("hp_pct", "pct"),
    "防御力": ("def_pct", "pct"),
    "冲击力": ("impact_pct", "pct"),
    "能量自动回复": ("er_pct", "pct"),
    "穿透率": ("pr", "pct"),
    "异常掌控": ("ac_pct", "pct"),
    "异常精通": ("am", "flat"),
}
GRADE_ORDER = {"S": 0, "A": 1, "B": 2}


def fetch(entry_page_id):
    for attempt in range(3):
        try:
            req = urllib.request.Request(API.format(entry_page_id), headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            time.sleep(0.6 * (attempt + 1))
    return None


def components(page):
    out = {}
    for module in page.get("modules") or []:
        for comp in module.get("components") or []:
            cid, data = comp.get("component_id"), comp.get("data")
            if not cid or not data:
                continue
            try:
                out.setdefault(cid, []).append(json.loads(data))
            except ValueError:
                pass
    return out


def plain(text):
    return re.sub(r"<[^>]+>", "", text or "")


def is_weapon(comps):
    for item in comps.get("role_ascension") or []:
        for row in item.get("list") or []:
            for pair in row.get("attr") or []:
                if pair.get("key") in ("突破前基础", "突破后基础"):
                    return True
    return False


def tables_text(comps):
    text = ""
    for table in comps.get("multi_table") or []:
        for block in table.get("tables") or []:
            for row in block.get("row") or []:
                text += plain(" ".join(row))
    return text


def breakthrough_base(comps):
    best = None
    for item in comps.get("role_ascension") or []:
        for row in item.get("list") or []:
            for pair in row.get("attr") or []:
                if pair.get("key") == "突破后基础":
                    found = ATK_RE.search(plain(pair.get("value")))
                    if found:
                        value = float(found.group(1))
                        best = value if best is None else max(best, value)
    return best


def parse(page):
    comps = components(page)
    if not is_weapon(comps):
        return None
    text = tables_text(comps)
    panels = {}
    for label, stat_kind, atk, stat, value, pct in PANEL_RE.findall(text):
        panels.setdefault(
            label,
            {
                "kind": "def" if stat_kind == "防御力" else "atk",
                "atk": float(atk),
                "stat": stat,
                "value": float(value),
                "pct": bool(pct),
            },
        )
    if "满级面板" not in panels:
        return None
    grade = ""
    for info in comps.get("material_base_info") or []:
        grade = info.get("grade") or ""
    tags = TAG_RE.findall(text)
    init, maxed = panels.get("初始面板", {}), panels["满级面板"]
    return {
        "id": int(page.get("id")),
        "name": page.get("name"),
        "grade": grade,
        "baseKind": maxed["kind"],
        "baseAttack": maxed["atk"] if maxed["kind"] == "atk" else 0,
        "baseDefense": maxed["atk"] if maxed["kind"] == "def" else 0,
        "initBaseValue": init.get("atk"),
        "substatLabel": maxed["stat"],
        "substatValue": maxed["value"],
        "substatIsPct": maxed["pct"],
        "initSubstatValue": init.get("value"),
        "roleTags": tags,
        "breakthroughBaseAt50": breakthrough_base(comps),
    }


def scan(max_id, workers):
    records, seen = [], 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for resp in pool.map(fetch, range(1, max_id + 1)):
            seen += 1
            if not resp or resp.get("retcode") != 0:
                continue
            page = (resp.get("data") or {}).get("page") or {}
            record = parse(page)
            if record:
                records.append(record)
            if seen % 250 == 0:
                print("scanned {} ids, {} engines".format(seen, len(records)), flush=True)
    records.sort(key=lambda item: item["id"])
    return records


def render(records):
    lines = ["window.WEAPON_PRESETS = ["]
    skipped = []
    ordered = sorted(records, key=lambda item: (GRADE_ORDER.get(item["grade"], 9), item["id"]))
    for item in ordered:
        mapped = SUBSTAT_TO_CALCULATOR.get(item["substatLabel"])
        if mapped is None or (mapped[1] == "pct" and not item["substatIsPct"]):
            skipped.append((item["id"], item["name"], item["substatLabel"]))
            continue
        to, kind = mapped
        value = item["substatValue"]
        value_text = str(int(value)) if float(value).is_integer() else str(value)
        base_kind = item.get("baseKind", "atk")
        lines += [
            "  {",
            "    id: 'ep-{}',".format(item["id"]),
            "    name: '{}',".format(item["name"]),
            "    grade: '{}',".format(item["grade"]),
            "    roleTag: '{}',".format(item["roleTags"][0] if item["roleTags"] else ""),
            "    source: 'https://baike.mihoyo.com/zzz/wiki/content/{}/detail?mhy_presentation_style=fullscreen',".format(item["id"]),
            "    baseKind: '{}',".format(base_kind),
            "    baseAttack: {},".format(int(item["baseAttack"])),
            "    baseDefense: {},".format(int(item["baseDefense"])),
            "    substat: {",
            "      label: '{}',".format(item["substatLabel"]),
            "      value: {},".format(value_text),
            "      kind: '{}',".format(kind),
            "      to: '{}',".format(to),
            "    },",
            "  },",
        ]
    lines.append("];")
    return "\n".join(lines) + "\n", skipped, len(ordered) - len(skipped)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-id", type=int, default=2600)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--out", default=OUTPUT)
    args = parser.parse_args()

    records = scan(args.max_id, args.workers)
    content, skipped, written = render(records)
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    print("engines found: {}".format(len(records)))
    print("presets written: {} -> {}".format(written, args.out))
    for entry in skipped:
        print("SKIPPED (unmapped substat):", entry)


if __name__ == "__main__":
    main()
