#!/usr/bin/env python3
"""用仓库计算器（backend/services）计算任意代理人的「标准满词条毕业面板」。

面板不是手填的：从 ``data/agent-presets.json`` 取 60 级基础面板，从
``data/weapon-presets.json`` 取专武，从 ``data/drive-disc-presets.json`` 取两套驱动盘，
按下方 BUILD 组装一次 ``PanelRequest``，交给
``zzz_panel.services.panel_service`` 实算，再把 ``totals`` 与配装说明写回攻略 JSON 的
``graduationPanel`` 字段——与攻略页里展示的计算器同一份代码，保证口径一致。

用法（仓库根；默认值即叶瞬光参考实例，位于 strategy/ye-shun-guang/）::

    uv run python .github/skills/agent-strategy/scripts/calc_graduation_panel.py \
        --agent-id ep-1687 --weapon-id ep-1751 --set4-id ep-1754 --set2-id ep-1000 \
        --core1 cr --core2 atk_base \
        --strategy strategy/ye-shun-guang/data/ye-shun-guang.strategy.json

换代理人只需换 id 与配装 flag，不必改脚本里的 BUILD 常量（不传 flag 时 BUILD 即默认值）::

    uv run python .github/skills/agent-strategy/scripts/calc_graduation_panel.py \
        --agent-id ep-1626 --weapon-id ep-1721 --set4-id ep-1347 --set2-id ep-1000 \
        --disc4 cd_48 --disc5 dmg_30 --disc6 hp_pct_30 \
        --set4-effect hp_pct_10 --set2-effect cd_16 \
        --sub-stats 'cr:20,cd:14,hp_pct:12,atk_pct:8' \
        --rows hp,penforce,cr,cd \
        --main-spec "4 号位暴击伤害 +48%，5 号位伤害加成 +30%，6 号位生命值 +30%" \
        --sub-spec "54 条满配：暴击率 ×20、暴击伤害 ×14、生命值% ×12、攻击力% ×8" \
        --strategy strategy/ban-yue/data/ban-yue.strategy.json

    # 只比对不写回（漂移检测，退出码非 0 即不一致）
    … 追加 --check

换代理人必须同步调整（详见 SKILL.md Step 4）：
* ``--agent-id / --weapon-id / --set4-id / --set2-id / --core1 / --core2`` 指向新代理人的
  预设 id；核心两个选项取该代理人满级核心加成对应的选项 id（叶瞬光：暴击率 cr + 基础攻击力 atk_base）。
* 配装口径全部用 flag 传入，**不要改脚本里的常量**：``--disc4/5/6``、``--set4-effect/
  --set2-effect``、``--sub-stats``、``--main-spec/--sub-spec``、``--rows``、``--mode``。
  不传 flag 时 BUILD 即叶瞬光口径——那只是参考实例的默认值，不是通用标准。

**毕业面板没有通用标准，必须按代理人定制**（SKILL.md「铁律」一节）。展示行、模式、
主词条、副词条分配与暴击率目标都随代理人的属性 / 特性 / 专武局内加成而变：
叶瞬光（凛刃强攻，专武局内 +50% 暴击）面板 50% 档、展示攻击 / 双爆 / 穿透值；
般岳（火命破，专武局内 +20% 暴击、生命值转贯穿力）面板 67% 档、展示生命值 /
贯穿力 / 双爆，副词条要分相当比例给生命值%。换代理人时整组参数重新给，不能只换 id。

配装口径（满词条参考，非唯一解）：
* 二件套各计一次（四件套局内特效计算器不建模）；
* 面板模式默认取预设 ``panelMode``（命破 → rupture，才会算贯穿力），``--mode`` 可覆盖；
* 毕业面板展示哪些行由 ``--rows`` 决定（默认 ``atk,cr,cd,pv`` 是叶瞬光口径；命破一般用
  ``hp,penforce,cr,cd``）；配装说明为纯文案，不带括号注释。
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "backend" / "src"))

from zzz_panel.schemas.panel import PanelRequest  # noqa: E402
from zzz_panel.services.panel_service import calculate  # noqa: E402

#: 满词条配装默认值 = **叶瞬光参考实例口径，不是通用标准**（见 SKILL.md 铁律）。
#: 展示行 / 模式 / 主词条 / 副词条分配随代理人的属性、特性、专武局内加成而变：
#: 般岳（火命破）是 hp,penforce,cr,cd + CR 20 条 + 生命值% 副词条。
#: set0/set2 的值为仓库选项表（data/options.json）中的二件套效果 id。
#: 副词的「面板暴击率 50% 档」只适用于专武局内再 +50% 的强攻代理人。
BUILD = {
    "disc_main": {"disc4": "cd_48", "disc5": "atk_pct_30", "disc6": "atk_pct_30"},
    "sets": {"set0": "dmg_10", "set1": "", "set2": "cd_16"},
    "sub_stats": {"cr": 13, "cd": 21, "atk_pct": 20},
}

#: 配装说明文案（与 BUILD 实际一致；页面展示，勿加括号注释）。
SPEC_MAIN_STATS = "4 号位暴击伤害 +48%，5 / 6 号位攻击力 +30%"
SPEC_SUB_STATS = "54 条满配：暴击率 ×13、暴击伤害 ×21、攻击力% ×20"

#: totals / mode_stats 键 -> 展示文案（与计算器 ResultPanel 的行一致）。
#: 毕业面板展示哪些行由 ``--rows`` 决定：叶瞬光（强攻，标准模式）默认
#: 攻击 / 双爆 / 穿透值；般岳（命破）用 hp,penforce,cr,cd——
#: 生命值 / 贯穿力 / 双爆，贯穿力来自命破模式专属行（ rupture mode_stats ）。
TOTAL_LABELS = {
    "hp": "生命值",
    "atk": "攻击力",
    "cr": "暴击率",
    "cd": "暴击伤害",
    "pv": "穿透值",
    "penforce": "贯穿力",
}

#: 默认展示行（可被 --rows 覆盖）。
DEFAULT_ROWS = ("atk", "cr", "cd", "pv")

#: 百分比行（与计算器渲染一致）。
PCT_ROWS = {"cr", "cd", "dmg", "pr"}

DEFAULT_STRATEGY = REPO_ROOT / "strategy" / "ye-shun-guang" / "data" / "ye-shun-guang.strategy.json"


def load_preset(path: Path, preset_id: str) -> dict:
    items = json.loads(path.read_text(encoding="utf-8"))
    for item in items:
        if item["id"] == preset_id:
            return item
    raise SystemExit(f"在 {path} 中找不到 {preset_id}")


def load_all(path: Path) -> dict:
    return {item["id"]: item for item in json.loads(path.read_text(encoding="utf-8"))}


def resolve_build(args) -> dict:
    """BUILD 常量 + 同名 CLI 覆盖。默认（不传 flag）即叶瞬光参考实例口径。

    换代理人时不必再改脚本常量：主词条 / 二件套效果 / 副词条分配 / 两行说明
    文案都能用 flag 传入，见 ``--help``。
    """
    disc_main = dict(BUILD["disc_main"])
    for slot in ("disc4", "disc5", "disc6"):
        override = getattr(args, slot, None)
        if override:
            disc_main[slot] = override

    sets = dict(BUILD["sets"])
    if args.set4_effect:
        sets["set0"] = args.set4_effect
    if args.set2_effect:
        sets["set2"] = args.set2_effect

    sub_stats = dict(BUILD["sub_stats"])
    if args.sub_stats:
        text = args.sub_stats.strip()
        try:
            if text.startswith("{"):
                sub_stats = {str(k): int(v) for k, v in json.loads(text).items()}
            else:
                # 紧凑格式 cr:13,cd:16,hp_pct:15,atk_pct:10——避免 Windows  shell
                # 传参时 JSON 的双引号被吃掉。
                sub_stats = {}
                for pair in text.split(","):
                    key, _, value = pair.partition(":")
                    sub_stats[key.strip()] = int(value)
        except (ValueError, AttributeError) as error:
            raise SystemExit(
                f"--sub-stats 无法解析：{error}；"
                "支持 '{\"cr\":13}' 或紧凑格式 cr:13,cd:16"
            )

    spec_main = args.main_spec or SPEC_MAIN_STATS
    spec_sub = args.sub_spec or SPEC_SUB_STATS
    if sum(sub_stats.values()) != 54:
        print(f"注意：副词条合计 {sum(sub_stats.values())} 条，标准满配为 54 条。", file=sys.stderr)

    return {
        "disc_main": disc_main,
        "sets": sets,
        "sub_stats": sub_stats,
        "main_spec": spec_main,
        "sub_spec": spec_sub,
    }


def build_request(args) -> tuple[PanelRequest, dict]:
    agent = load_preset(REPO_ROOT / "data" / "agent-presets.json", args.agent_id)
    weapon = load_preset(REPO_ROOT / "data" / "weapon-presets.json", args.weapon_id)
    discs = load_all(REPO_ROOT / "data" / "drive-disc-presets.json")
    set4 = discs.get(args.set4_id)
    set2 = discs.get(args.set2_id)
    if set4 is None:
        raise SystemExit(f"在 data/drive-disc-presets.json 中找不到套装 {args.set4_id}")
    if set2 is None:
        raise SystemExit(f"在 data/drive-disc-presets.json 中找不到套装 {args.set2_id}")
    build = resolve_build(args)
    base = agent["base"]
    # 模式按预设的 panelMode 推导（standard / rupture / fengyu），般岳是命破 → rupture，
    # 贯穿力由命破模式专属公式给出；也可用 --mode 覆盖。
    mode = args.mode or agent.get("panelMode") or "standard"
    request = PanelRequest(
        mode=mode,
        base={
            "hp": base["hp"], "atk": base["atk"], "def": base["def"], "impact": base["impact"],
            "cr": base["cr"], "cd": base["cd"], "ac": base["ac"], "am": base["am"],
            # 命破 / 锋御代理人的预设不含 pr / er（改由贯穿力、闪能自动累积等专属行替代），缺省按 0。
            "pr": base.get("pr", 0), "er": base.get("er", 0),
        },
        weapon={
            "baseKind": weapon["baseKind"],
            "baseValue": weapon["baseAttack"],
            "substat": {
                "target": weapon["substat"]["to"],
                "value": weapon["substat"]["value"],
                "kind": weapon["substat"]["kind"],
                "label": weapon["substat"]["label"],
            },
        },
        # 满级核心加成：两个核心选项（叶瞬光/般岳 = 暴击率 cr + 基础攻击力 atk_base）
        core={"core1": args.core1, "core2": args.core2},
        disc_main=build["disc_main"],
        sub_stats=build["sub_stats"],
        sets=build["sets"],
    )
    spec = {
        "agent": agent["name"],
        "weapon": weapon["name"],
        "core": args.core_spec,
        "set4": set4["name"],
        "set2": set2["name"],
        "mainStats": build["main_spec"],
        "subStats": build["sub_spec"],
    }
    return request, spec


def compute(args) -> dict:
    request, spec = build_request(args)
    response = calculate(request)
    rows = [key.strip() for key in (args.rows or ",".join(DEFAULT_ROWS)).split(",") if key.strip()]
    unknown = [key for key in rows if key not in TOTAL_LABELS]
    if unknown:
        raise SystemExit(f"--rows 含未知键 {unknown}；可用：{sorted(TOTAL_LABELS)}")
    # penforce 等模式专属行在 mode_stats 里，其余在 totals 里
    values = dict(response.totals)
    values.update(response.mode_stats or {})
    totals = []
    for key in rows:
        if key not in values:
            continue
        value = values[key]
        if key in PCT_ROWS:
            value = min(value, 100.0) if key in {"cr"} else value
        totals.append(
            {
                "label": TOTAL_LABELS[key],
                "value": int(value) if float(value).is_integer() else round(float(value), 1),
                "unit": "%" if key in PCT_ROWS else "",
            }
        )
    return {
        "build": spec,
        "totals": totals,
        "note": "由仓库计算器（POST /api/panel/calc 同一份 core 逻辑）实算后固定，非手填。",
        "computedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    }


def strip_timestamp(panel: dict | None) -> dict | None:
    if not panel:
        return None
    return {key: value for key, value in panel.items() if key != "computedAt"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--agent-id", default="ep-1687", help="代理人预设 id（data/agent-presets.json）")
    parser.add_argument("--weapon-id", default="ep-1751", help="专武预设 id（data/weapon-presets.json）")
    parser.add_argument("--set4-id", default="ep-1754", help="4 件套预设 id（data/drive-disc-presets.json）")
    parser.add_argument("--set2-id", default="ep-1000", help="2 件套预设 id（data/drive-disc-presets.json）")
    parser.add_argument("--core1", default="cr", help="核心选项 1（满级核心加成对应的选项 id）")
    parser.add_argument("--core2", default="atk_base", help="核心选项 2（满级核心加成对应的选项 id）")
    parser.add_argument("--core-spec", default="暴击率 +14.4%、基础攻击力 +75", help="配装说明里的核心技文案")
    parser.add_argument("--disc4", default="", help=f"4 号位主词条选项 id，默认 {BUILD['disc_main']['disc4']}")
    parser.add_argument("--disc5", default="", help=f"5 号位主词条选项 id，默认 {BUILD['disc_main']['disc5']}")
    parser.add_argument("--disc6", default="", help=f"6 号位主词条选项 id，默认 {BUILD['disc_main']['disc6']}")
    parser.add_argument("--set4-effect", default="", help=f"4 件套二件套效果选项 id，默认 {BUILD['sets']['set0']}")
    parser.add_argument("--set2-effect", default="", help=f"2 件套二件套效果选项 id，默认 {BUILD['sets']['set2']}")
    parser.add_argument("--sub-stats", default="", help='副词条分配 JSON，如 \'{"cr":13,"cd":16,"hp_pct":15,"atk_pct":10}\'')
    parser.add_argument("--main-spec", default="", help=f"配装说明主词条文案，默认 {SPEC_MAIN_STATS}")
    parser.add_argument("--sub-spec", default="", help=f"配装说明副词条文案，默认 {SPEC_SUB_STATS}")
    parser.add_argument(
        "--mode",
        default="",
        help="面板模式（standard/rupture/fengyu），默认取预设的 panelMode；般岳=rupture 才会算贯穿力",
    )
    parser.add_argument(
        "--rows",
        default="",
        help=f"毕业面板展示行（逗号分隔，可用键 {sorted(TOTAL_LABELS)}），默认 {','.join(DEFAULT_ROWS)}；"
        "般岳传 hp,penforce,cr,cd（生命值/贯穿力/双爆）",
    )
    parser.add_argument("--strategy", type=Path, default=DEFAULT_STRATEGY, help=f"攻略 JSON 路径，默认 {DEFAULT_STRATEGY}")
    parser.add_argument("--check", action="store_true", help="只比对，不写回")
    args = parser.parse_args()

    panel = compute(args)

    if not args.strategy.is_file():
        print(f"攻略文件不存在：{args.strategy}", file=sys.stderr)
        print("请先创建该文件（含其余攻略内容），再运行本脚本写入毕业面板。", file=sys.stderr)
        return 1

    strategy = json.loads(args.strategy.read_text(encoding="utf-8"))
    if strip_timestamp(strategy.get("graduationPanel")) == strip_timestamp(panel):
        print("毕业面板已是最新。")
        return 0

    if args.check:
        print("有漂移：攻略中的毕业面板与计算结果不一致", file=sys.stderr)
        return 1

    strategy["graduationPanel"] = panel
    args.strategy.write_text(json.dumps(strategy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写入 {args.strategy}")
    for item in panel["totals"]:
        print(f"  {item['label']}: {item['value']}{item['unit']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
