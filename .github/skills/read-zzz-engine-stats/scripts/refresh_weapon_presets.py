"""Refresh data/weapon-presets.json from the official HoYoLAB ZZZ Wiki.

Scans the wiki entry_page_id space through the public content API, keeps every
page whose 晋升需求 table uses the weapon-specific 突破前基础 / 突破后基础 keys,
and extracts the level-60 (0 突破) base ATK plus the fixed high-level substat.

``data/weapon-presets.json`` 是全仓库唯一真实源；参照实现夹具所需的
``frontend/tests/fixtures/legacy-calculator/data/weapon-presets.js`` 由
``tools/sync_presets.py --to-legacy`` 从本文件反向生成，不要直接写它。
序列化复用 sync_presets 的规范化实现。

Default paths are relative to the repository root; run from there:

Usage:
    python .github/skills/read-zzz-engine-stats/scripts/refresh_weapon_presets.py
    python .github/skills/read-zzz-engine-stats/scripts/refresh_weapon_presets.py --max-id 2600
"""

import argparse
import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

API = "https://act-api-takumi.mihoyo.com/hoyowiki/zzz/wapi/entry_page_v2?entry_page_id={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://baike.mihoyo.com/",
    "x-rpc-wiki_app": "zzz",
}
#: 默认输出。仓库根 ``data/`` 是唯一真实源；legacy 的 JS 包装由
#: ``tools/sync_presets.py --to-legacy`` 反向生成，不在本脚本的职责内。
OUTPUT = "data/weapon-presets.json"

#: 仓库根。本脚本从 ``.github/skills/<skill>/scripts/`` 上溯四层到达。
REPO_ROOT = Path(__file__).resolve().parents[4]


def load_sync_presets():
    """导入 ``tools/sync_presets.py`` 以复用其规范化与 JSON 序列化。

    刻意不复制一份序列化逻辑：预设 JSON 的键序与缩进由该脚本单一定义，
    ``sync_presets.py --to-legacy --check`` 依赖两侧字节一致。这里若各写一套，
    重新抓取后 ``--check`` 就会一直报漂移，而漂移原因极难定位。
    """
    if str(REPO_ROOT / "tools") not in sys.path:
        sys.path.insert(0, str(REPO_ROOT / "tools"))
    import sync_presets

    return sync_presets

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
    """序列化为规范化的预设 JSON。

    键序与缩进由 ``tools/sync_presets.py`` 单一定义，因此重新抓取后
    ``sync_presets.py --to-legacy --check`` 仍能通过。
    """
    sync_presets = load_sync_presets()
    skipped = []
    ordered = sorted(records, key=lambda item: (GRADE_ORDER.get(item["grade"], 9), item["id"]))
    presets = []
    for item in ordered:
        mapped = SUBSTAT_TO_CALCULATOR.get(item["substatLabel"])
        if mapped is None or (mapped[1] == "pct" and not item["substatIsPct"]):
            skipped.append((item["id"], item["name"], item["substatLabel"]))
            continue
        to, kind = mapped
        presets.append({
            "id": "ep-{}".format(item["id"]),
            "name": item["name"],
            "grade": item["grade"],
            "roleTag": item["roleTags"][0] if item["roleTags"] else "",
            "source": "https://baike.mihoyo.com/zzz/wiki/content/{}/detail?mhy_presentation_style=fullscreen".format(item["id"]),
            "baseKind": item.get("baseKind", "atk"),
            # 整值收敛成 int：JSON 里整值就该是整数，否则与既有
            # data/*.json 的字面量不一致，--check 会一直报漂移。
            "baseAttack": int(item["baseAttack"]),
            "baseDefense": int(item["baseDefense"]),
            "substat": {
                "label": item["substatLabel"],
                "value": int(item["substatValue"]) if float(item["substatValue"]).is_integer() else item["substatValue"],
                "kind": kind,
                "to": to,
            },
        })
    normalized = [sync_presets.order_preset(preset, agent=False) for preset in presets]
    sync_presets.check_ids(normalized, OUTPUT)
    return sync_presets.dump_json(normalized), skipped, len(ordered) - len(skipped)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-id", type=int, default=2600)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--out", default=OUTPUT)
    args = parser.parse_args()

    records = scan(args.max_id, args.workers)
    content, skipped, written = render(records)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8", newline="\n")
    print("engines found: {}".format(len(records)))
    print("presets written: {} -> {}".format(written, args.out))
    print("next: python tools/sync_presets.py --to-legacy")
    for entry in skipped:
        print("SKIPPED (unmapped substat):", entry)


if __name__ == "__main__":
    main()
