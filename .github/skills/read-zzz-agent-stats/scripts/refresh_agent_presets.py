"""Refresh frontend/legacy/data/agent-presets.js from the official HoYoLAB ZZZ Wiki.

Scans the whole entry_page_id space through the public content API, keeps every
page carrying a `role_base_info` component (only agent pages have one), and
writes one preset per agent with:

  * level-60 (0 突破) base panel, merged field by field from the 初始数据 and
    满级数据 rows of the 晋升需求 slider;
  * fully upgraded core skill, grouped per attribute from ranks A-F;
  * the official 特性 tag and the matching calculator panel mode.

Default paths are relative to the repository root; run from there:

Usage:
    python .github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py
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

PROFESSION_TAGS = {
    "strike": ("强攻", "standard"),
    "pierce": ("击破", "standard"),
    "abnormal": ("异常", "standard"),
    "support": ("支援", "standard"),
    "guard": ("防护", "standard"),
    "rupture": ("命破", "rupture"),
    "armero": ("锋御", "fengyu"),
}

# Wiki label variants (older agent pages abbreviate) -> calculator base field.
BASE_ALIASES = {
    "生命值": "hp", "生命": "hp", "生命力": "hp",
    "攻击力": "atk", "攻击": "atk",
    "防御力": "def", "防御": "def",
    "冲击力": "impact",
    "暴击率": "cr", "暴击": "cr",
    "暴击伤害": "cd", "暴伤": "cd",
    "异常掌控": "ac",
    "异常精通": "am",
    "穿透率": "pr",
    "能量自动回复": "er", "锐能自动累积": "er",
    "贯穿力": "penforce",
    "闪能自动累积": "energyAccumulation",
    "闪能自动积累": "energyAccumulation",
    "闪能自动累计": "energyAccumulation",
}
BASE_FIELDS = ("hp", "atk", "def", "impact", "cr", "cd", "ac", "am", "pr", "er")
EXTRA_FIELDS = {"penforce": "penforce", "energyAccumulation": "energyAccumulation"}

# Core-skill effect wording -> CORE_OPTIONS id. Every entry is a real in-game
# core bonus; the value per rank is read from the Wiki, never assumed.
CORE_EFFECT_TO_OPTION = {
    ("暴击率", 4.8): "cr",
    ("基础攻击力", 25.0): "atk_base",
    ("基础能量自动回复", 0.12): "er_base",
    ("异常掌控", 12.0): "ac",
    ("基础冲击力", 6.0): "impact_base",
    ("暴击伤害", 9.6): "cd",
    ("生命值百分比", 6.0): "hp_pct",
    ("异常精通", 18.0): "am",
    ("基础生命值", 140.0): "hp_base",
    ("穿透率", 4.8): "pr",
    ("异常精通", 30.0): "am_90",
    ("攻击力百分比", 7.0): "atk_pct_21",
}
GRADE_ORDER = {"S": 0, "A": 1}


def fetch(entry_page_id):
    for attempt in range(3):
        try:
            req = urllib.request.Request(API.format(entry_page_id), headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            time.sleep(0.6 * (attempt + 1))
    return None


def plain(text):
    return re.sub(r"<[^>]+>", "", text or "")


def talent_blocks(page):
    for module in page.get("modules") or []:
        for comp in module.get("components") or []:
            if comp.get("component_id") != "role_talent":
                continue
            try:
                yield json.loads(comp["data"])
            except (ValueError, KeyError):
                continue


def row_text(block):
    for child in block.get("children") or []:
        for row in child.get("row") or []:
            return " ".join(plain(cell) for cell in row)
    return ""


def stat_row(text):
    return {key: float(val) for key, val in re.findall(r"([一-龥A-Za-z]+)\s*[：:]\s*([\d.]+)%?", text)}


def base_panel(page):
    initial, maxed = {}, {}
    for talent in talent_blocks(page):
        for item in talent.get("list") or []:
            for child in item.get("children") or []:
                if "滑块" not in (child.get("desc") or ""):
                    continue
                for entry in child.get("growth") or []:
                    values = stat_row(row_text(entry))
                    if not values:
                        continue
                    if entry.get("name") == "初始":
                        initial = values
                    elif entry.get("name") == "满级":
                        maxed = values
    merged = dict(initial)
    merged.update(maxed)
    return merged


def core_ranks(page):
    ranks = []
    for talent in talent_blocks(page):
        for item in talent.get("list") or []:
            if item.get("tab_name") != "核心技":
                continue
            for child in item.get("children") or []:
                for entry in child.get("growth") or []:
                    if entry.get("name") not in list("ABCDEF"):
                        continue
                    head = row_text(entry).split("[")[0].strip()
                    if head:
                        ranks.append((entry["name"], head))
    return ranks


def core_bonuses(ranks, core_options):
    groups = {}
    for rank, text in ranks:
        match = re.match(r"^(.+?)提升([\d.]+)(%?)(?:点?/秒|点|秒)?$", text)
        if not match:
            raise ValueError("无法解析核心效果：{}".format(text))
        label, value, pct = match.group(1), float(match.group(2)), match.group(3) == "%"
        key = (label, value)
        if key not in CORE_EFFECT_TO_OPTION:
            raise ValueError("未登记的核心效果：{}".format(text))
        entry = groups.setdefault(key, {"ranks": [], "unit": "%" if pct else ""})
        entry["ranks"].append(rank)
    bonuses = []
    for (label, value), entry in groups.items():
        option_id = CORE_EFFECT_TO_OPTION[(label, value)]
        option = core_options[option_id]
        ranks_list = entry["ranks"]
        total = value * len(ranks_list)
        count = total / option["value"]
        if abs(count - round(count)) > 1e-9 or round(count) < 1:
            raise ValueError("核心加成无法由选项 {} 表示：{} ×{} = {}".format(option_id, label, len(ranks_list), total))
        bonus = {
            "optionId": option_id,
            "ranks": ranks_list,
            "label": label,
            "perRankValue": value,
            "totalValue": total,
            "unit": entry["unit"],
        }
        if round(count) > 1:
            bonus["optionCount"] = int(round(count))
        bonuses.append(bonus)
    return bonuses


def load_core_options(config_path):
    text = open(config_path, encoding="utf-8").read()
    block = re.search(r"const CORE_OPTIONS = \[(.*?)\];", text, re.S).group(1)
    options = {}
    for entry in re.finditer(r"\{ id: '([^']+)', label: '([^']+)', value: ([\d.]+)", block):
        options[entry.group(1)] = {"label": entry.group(2), "value": float(entry.group(3))}
    return options


def num(value):
    return int(value) if float(value).is_integer() else value


def build(agent, core_options):
    tag, mode = PROFESSION_TAGS.get(agent["profession"], ("", "standard"))
    merged = agent["base"]
    base, additional, unmodeled, unavailable = {}, {}, [], []
    for label, value in merged.items():
        field = BASE_ALIASES.get(label)
        if field in BASE_FIELDS:
            base[field] = num(value)
        elif field in EXTRA_FIELDS:
            additional[field] = num(value)
        else:
            unmodeled.append({"label": label, "value": num(value), "unit": "%" if "%" in label else ""})
    for field in BASE_FIELDS:
        if field not in base:
            unavailable.append(field)
    preset = {
        "id": "ep-{}".format(agent["id"]),
        "name": agent["name"],
        "roleTag": tag,
        "panelMode": mode,
        "source": agent["source"],
        "base": base,
    }
    if unavailable:
        preset["unavailableBaseStats"] = unavailable
    if additional:
        preset["additionalBaseStats"] = additional
    if unmodeled:
        preset["unmodeledBaseStats"] = unmodeled
    preset["coreBonuses"] = core_bonuses(agent["core"], core_options)
    if agent.get("grade") in GRADE_ORDER:
        preset["grade"] = agent["grade"]
    return preset


def scan(max_id):
    found, done = [], 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        for resp in pool.map(fetch, range(1, max_id + 1)):
            done += 1
            if not resp or resp.get("retcode") != 0:
                continue
            page = (resp.get("data") or {}).get("page") or {}
            base_info = None
            for module in page.get("modules") or []:
                for comp in module.get("components") or []:
                    if comp.get("component_id") == "role_base_info":
                        base_info = json.loads(comp["data"])
            if not base_info:
                continue
            agent = {
                "id": int(page.get("id")),
                "name": base_info.get("name"),
                "grade": base_info.get("grade"),
                "profession": base_info.get("role_profession"),
                "base": base_panel(page),
                "core": core_ranks(page),
                "source": "https://baike.mihoyo.com/zzz/wiki/content/{}/detail?mhy_presentation_style=fullscreen".format(page.get("id")),
            }
            found.append(agent)
            if done % 250 == 0:
                print("scanned {} ids, {} agents".format(done, len(found)), flush=True)
    found.sort(key=lambda item: item["id"])
    return found


def render(presets):
    lines = ["window.AGENT_PRESETS = ["]
    for preset in presets:
        lines += [
            "  {",
            "    id: '{}',".format(preset["id"]),
            "    name: '{}',".format(preset["name"]),
            "    roleTag: '{}',".format(preset["roleTag"]),
            "    panelMode: '{}',".format(preset["panelMode"]),
            "    source: '{}',".format(preset["source"]),
            "    base: {",
        ]
        for field in BASE_FIELDS:
            if field in preset["base"]:
                lines.append("      {}: {},".format(field, preset["base"][field]))
        lines.append("    },")
        if "unavailableBaseStats" in preset:
            lines.append("    unavailableBaseStats: [{}],".format(", ".join("'{}'".format(f) for f in preset["unavailableBaseStats"])))
        if "additionalBaseStats" in preset:
            lines.append("    additionalBaseStats: {")
            for field, value in preset["additionalBaseStats"].items():
                lines.append("      {}: {},".format(field, value))
            lines.append("    },")
        if "unmodeledBaseStats" in preset:
            lines.append("    unmodeledBaseStats: [")
            for stat in preset["unmodeledBaseStats"]:
                lines.append("      {{ label: '{}', value: {}, unit: '{}' }},".format(stat["label"], stat["value"], stat["unit"]))
            lines.append("    ],")
        lines.append("    coreBonuses: [")
        for bonus in preset["coreBonuses"]:
            lines.append("      {")
            if "optionCount" in bonus:
                lines.append("        optionId: '{}',".format(bonus["optionId"]))
                lines.append("        optionCount: {},".format(bonus["optionCount"]))
            else:
                lines.append("        optionId: '{}',".format(bonus["optionId"]))
            lines.append("        ranks: [{}],".format(", ".join("'{}'".format(r) for r in bonus["ranks"])))
            lines.append("        label: '{}',".format(bonus["label"]))
            lines.append("        perRankValue: {},".format(num(bonus["perRankValue"])))
            lines.append("        totalValue: {},".format(num(bonus["totalValue"])))
            lines.append("        unit: '{}',".format(bonus["unit"]))
            lines.append("      },")
        lines.append("    ],")
        lines.append("  },")
    lines.append("];")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-id", type=int, default=2600)
    parser.add_argument("--config", default="frontend/legacy/scripts/calculator-config.js")
    parser.add_argument("--out", default="frontend/legacy/data/agent-presets.js")
    args = parser.parse_args()

    core_options = load_core_options(args.config)
    agents = scan(args.max_id)
    presets, problems = [], []
    for agent in agents:
        try:
            presets.append(build(agent, core_options))
        except ValueError as error:
            problems.append((agent["id"], agent["name"], str(error)))
    presets.sort(key=lambda item: (GRADE_ORDER.get(item["grade"], 9), item["id"]))
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(render(presets))
    print("agents found: {}".format(len(agents)))
    print("presets written: {} -> {}".format(len(presets), args.out))
    for problem in problems:
        print("SKIPPED:", problem)


if __name__ == "__main__":
    main()
