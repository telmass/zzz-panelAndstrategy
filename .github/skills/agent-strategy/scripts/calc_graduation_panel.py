#!/usr/bin/env python3
"""用仓库计算器（backend/services）计算任意代理人的「标准满词条毕业面板」。

面板不是手填的：从 ``data/agent-presets.json`` 取 60 级基础面板，从
``data/weapon-presets.json`` 取专武，从 ``data/drive-disc-presets.json`` 取两套驱动盘，
按下方 BUILD 组装一次 ``PanelRequest``，交给
``zzz_panel.services.panel_service`` 实算，再把 ``totals`` 与配装说明写回攻略 JSON 的
``graduationPanel`` 字段——与攻略页里展示的计算器同一份代码，保证口径一致。

用法（仓库根；默认值即叶瞬光参考实例，位于 strategy/ye-shunguang/）::

    uv run python .github/skills/agent-strategy/scripts/calc_graduation_panel.py \
        --agent-id ep-1687 --weapon-id ep-1751 --set4-id ep-1754 --set2-id ep-1000 \
        --core1 cr --core2 atk_base \
        --strategy strategy/ye-shunguang/data/ye-shunguang.strategy.json

换代理人只需换 id 与配装 flag，不必改脚本里的 BUILD 常量（不传 flag 时 BUILD 即默认值）::

    uv run python .github/skills/agent-strategy/scripts/calc_graduation_panel.py \
        --agent-id ep-1626 --weapon-id ep-1721 --set4-id ep-1347 --set2-id ep-1000 \
        --disc4 cd_48 --disc5 dmg_30 --disc6 hp_pct_30 \
        --set4-effect hp_pct_10 --set2-effect cd_16 \
        --sub-stats 'cr:20,cd:14,hp_pct:12,atk_pct:8' \
        --rows hp,penforce,cr,cd \
        --main-spec "4 号位暴击伤害 +48%，5 号位伤害加成 +30%，6 号位生命值 +30%" \
        --sub-spec "54 条满配：暴击率 ×20、暴击伤害 ×14、生命值% ×12、攻击力% ×8" \
        --strategy strategy/banyue/data/banyue.strategy.json

    # 只比对不写回（漂移检测，退出码非 0 即不一致）
    … 追加 --check

非满配面板（可选）：同一音擎 / 核心 / 套装，主词条与副词条都可另给（``--alt-disc4/5/6``
与 ``--alt-main-spec``，缺省沿用满配），实算后写入 ``graduationPanelAlt``
（页面渲染在满配面板下方，``--check`` 同时校验两份）::

    uv run python .github/skills/agent-strategy/scripts/calc_graduation_panel.py \
        --agent-id ep-1386 --weapon-id ep-1463 --set4-id ep-1551 --set2-id ep-1194 \
        --core1 ac --core2 atk_base --sub-stats atk_pct:24,am:16,atk_flat:5,hp_flat:4,def_flat:5 --rows atk,am,ac \
        --alt-sub-stats atk_pct:8 \
        --alt-disc4 atk_pct_30 --alt-disc5 atk_pct_30 --alt-disc6 ac_pct_30 \
        --alt-label "非满配毕业面板（8 词条）" \
        --alt-main-spec "4 号位攻击力 +30%，5 号位攻击力 +30%，6 号位异常掌控 +30%" \
        --alt-spec "8 条：攻击力% ×8" \
        --strategy strategy/yuye/data/yuye.strategy.json

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

def _find_repo_root() -> Path:
    """Walk up from this file until pyproject.toml is found (robust to nesting)."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise RuntimeError(f"Cannot find pyproject.toml above {current}")
REPO_ROOT = _find_repo_root()
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
#: 毕业面板展示哪些行由 ``--rows`` 决定，没有通用标准：
#: 叶瞬光（强攻，标准模式）默认 atk,cr,cd,pv；
#: 般岳（命破）用 hp,penforce,cr,cd——命破的伤害口径是贯穿力；
#: 克拉蕾（锋御）应含 actual_cr,blast_dmg——锋御看实际暴击率与锐暴伤害。
TOTAL_LABELS = {
    "hp": "生命值",
    "atk": "攻击力",
    "def": "防御力",
    "cr": "暴击率",
    "cd": "暴击伤害",
    "dmg": "增伤",
    "imp": "冲击力",
    "am": "异常精通",
    "ac": "异常掌控",
    "pr": "穿透率",
    "pv": "穿透值",
    "penforce": "贯穿力",
    "actual_cr": "实际暴击率",
    "blast_dmg": "锐暴伤害",
}

#: 默认展示行（可被 --rows 覆盖）。
DEFAULT_ROWS = ("atk", "cr", "cd", "pv")

#: 百分比行（与计算器渲染一致；锐暴伤害在主界面也带 % 后缀）。
PCT_ROWS = {"cr", "cd", "dmg", "pr", "actual_cr", "blast_dmg"}

DEFAULT_STRATEGY = REPO_ROOT / "strategy" / "ye-shunguang" / "data" / "ye-shunguang.strategy.json"


def load_preset(path: Path, preset_id: str) -> dict:
    items = json.loads(path.read_text(encoding="utf-8"))
    for item in items:
        if item["id"] == preset_id:
            return item
    raise SystemExit(f"在 {path} 中找不到 {preset_id}")


def load_all(path: Path) -> dict:
    return {item["id"]: item for item in json.loads(path.read_text(encoding="utf-8"))}


def parse_sub_stats(text: str) -> dict:
    """解析副词条分配：紧凑格式 ``cr:13,cd:16,...`` 或 JSON 字符串。

    紧凑格式优先：Windows shell 传参时 JSON 的双引号会被吃掉。
    """
    text = text.strip()
    try:
        if text.startswith("{"):
            return {str(k): int(v) for k, v in json.loads(text).items()}
        sub_stats = {}
        for pair in text.split(","):
            key, _, value = pair.partition(":")
            sub_stats[key.strip()] = int(value)
        return sub_stats
    except (ValueError, AttributeError) as error:
        raise SystemExit(
            f"--sub-stats 无法解析：{error}；"
            "支持 '{\"cr\":13}' 或紧凑格式 cr:13,cd:16"
        )


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
    # 套装效果不存在可用选项时（如山大王的「失衡值+6%」选项表没有对应项）传 none 占位
    if args.set4_effect and args.set4_effect != "none":
        sets["set0"] = args.set4_effect
    elif args.set4_effect == "none":
        sets["set0"] = ""
    if args.set2_effect:
        sets["set2"] = args.set2_effect

    sub_stats = parse_sub_stats(args.sub_stats) if args.sub_stats else dict(BUILD["sub_stats"])

    spec_main = args.main_spec or SPEC_MAIN_STATS
    spec_sub = args.sub_spec or SPEC_SUB_STATS
    if sum(sub_stats.values()) != 54:
        print(f"注意：副词条合计 {sum(sub_stats.values())} 条，标准满配为 54 条。", file=sys.stderr)

    # 非满配面板：同一配装，副词条数由 --alt-sub-stats 人为界定（不要求 54 条）
    alt_sub_stats = parse_sub_stats(args.alt_sub_stats) if args.alt_sub_stats else None
    if alt_sub_stats is not None:
        alt_spec = args.alt_spec or f"{sum(alt_sub_stats.values())} 条：" + "、".join(
            f"{key}×{value}" for key, value in alt_sub_stats.items()
        )
    else:
        alt_spec = args.alt_spec

    return {
        "disc_main": disc_main,
        "sets": sets,
        "sub_stats": sub_stats,
        "main_spec": spec_main,
        "sub_spec": spec_sub,
        "alt_sub_stats": alt_sub_stats,
        "alt_spec": alt_spec,
    }


def build_request(
    args,
    sub_stats: dict | None = None,
    sub_spec: str | None = None,
    disc_main: dict | None = None,
    main_spec: str | None = None,
) -> tuple[PanelRequest, dict]:
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
            # 锋御音擎的基础属性是防御力（baseKind=def），不能一律取 baseAttack
            "baseKind": weapon.get("baseKind") or "atk",
            "baseValue": weapon["baseDefense"] if weapon.get("baseKind") == "def" else weapon["baseAttack"],
            "substat": {
                "target": weapon["substat"]["to"],
                "value": weapon["substat"]["value"],
                "kind": weapon["substat"]["kind"],
                "label": weapon["substat"]["label"],
            },
        },
        # 满级核心加成：两个核心选项（叶瞬光/般岳 = 暴击率 cr + 基础攻击力 atk_base；
        # 克拉蕾 = 只有暴击率 cr，第二个用 none 占位——PowerShell 传不了空参数）。
        core={
            "core1": "" if args.core1 in ("", "none") else args.core1,
            "core2": "" if args.core2 in ("", "none") else args.core2,
        },
        disc_main=build["disc_main"] if disc_main is None else disc_main,
        sub_stats=build["sub_stats"] if sub_stats is None else sub_stats,
        sets=build["sets"],
    )
    spec = {
        "agent": agent["name"],
        "weapon": weapon["name"],
        "core": args.core_spec,
        "set4": set4["name"],
        "set2": set2["name"],
        "mainStats": build["main_spec"] if main_spec is None else main_spec,
        "subStats": build["sub_spec"] if sub_spec is None else sub_spec,
    }
    return request, spec


def compute_panel(args, request: PanelRequest, spec: dict) -> dict:
    response = calculate(request)
    rows = [key.strip() for key in (args.rows or ",".join(DEFAULT_ROWS)).split(",") if key.strip()]
    unknown = [key for key in rows if key not in TOTAL_LABELS]
    if unknown:
        raise SystemExit(f"--rows 含未知键 {unknown}；可用：{sorted(TOTAL_LABELS)}")
    # penforce / actual_cr 在 mode_stats 里；blast_dmg 是顶层字段（锋御固有属性）
    values = dict(response.totals)
    values.update(response.mode_stats or {})
    if getattr(response, "blast_dmg", None) is not None:
        values["blast_dmg"] = response.blast_dmg
    totals = []
    for key in rows:
        if key not in values:
            continue
        # 不截断：锋御的多重暴击让面板暴击率可以（也应该）超过 100%，
        # 与主界面 ResultPanel 的展示口径保持一致。
        value = values[key]
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


def compute(args) -> tuple[dict, dict | None]:
    """返回 (满配面板, 非满配面板 or None)。"""
    request, spec = build_request(args)
    panel = compute_panel(args, request, spec)

    build = resolve_build(args)
    if build["alt_sub_stats"] is None:
        return panel, None
    # 非满配：音擎 / 核心 / 套装与满配一致；主词条可另给（--alt-disc4/5/6，
    # 缺省沿用满配），副词条换成人为界定的条数
    alt_disc_main = dict(build["disc_main"])
    for slot in ("disc4", "disc5", "disc6"):
        override = getattr(args, f"alt_{slot}", None)
        if override:
            alt_disc_main[slot] = override
    alt_request, alt_spec_base = build_request(
        args,
        sub_stats=build["alt_sub_stats"],
        sub_spec=build["alt_spec"],
        disc_main=alt_disc_main,
        main_spec=args.alt_main_spec or build["main_spec"],
    )
    alt_spec = dict(alt_spec_base)
    alt = compute_panel(args, alt_request, alt_spec)
    alt["title"] = args.alt_label or "非满配毕业面板"
    return panel, alt


def strip_timestamp(panel: dict | None) -> dict | None:
    if not panel:
        return None
    return {key: value for key, value in panel.items() if key != "computedAt"}


def check_all_strategy_panels() -> int:
    """Structural check: every strategy/*.strategy.json has a valid graduationPanel."""
    strategy_root = REPO_ROOT / "strategy"
    problems = []
    checked = 0
    for path in sorted(strategy_root.glob("*/data/*.strategy.json")):
        slug = path.parent.parent.name
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            problems.append(f"{slug}: cannot parse JSON ({e})")
            continue
        panel = data.get("graduationPanel")
        if not panel:
            problems.append(f"{slug}: missing graduationPanel")
            continue
        build = panel.get("build")
        if not build or not isinstance(build, dict):
            problems.append(f"{slug}: graduationPanel.build missing or not a dict")
            continue
        totals = panel.get("totals")
        if not totals or not isinstance(totals, list) or len(totals) < 1:
            problems.append(f"{slug}: graduationPanel.totals missing or empty")
            continue
        for item in totals:
            if not isinstance(item, dict) or "label" not in item or "value" not in item:
                problems.append(f"{slug}: graduationPanel.totals has malformed entry")
                break
        alt = data.get("graduationPanelAlt")
        if alt is not None:
            alt_totals = alt.get("totals")
            if not alt_totals or not isinstance(alt_totals, list):
                problems.append(f"{slug}: graduationPanelAlt.totals missing or invalid")
        checked += 1
    if problems:
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        print(f"check-all: {len(problems)} problem(s) in {checked} file(s)", file=sys.stderr)
        return 1
    print(f"check-all: {checked} strategy files have structurally valid graduation panels")
    return 0


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
        "--alt-sub-stats",
        default="",
        help="非满配面板的副词条分配（紧凑格式 atk_pct:6,am:4,atk_flat:2）；不传则不生成非满配面板",
    )
    parser.add_argument("--alt-label", default="", help="非满配面板标题文案，默认「非满配毕业面板」")
    parser.add_argument("--alt-spec", default="", help="非满配面板的副词条文案，缺省按条数自动生成")
    parser.add_argument("--alt-disc4", default="", help="非满配面板 4 号位主词条选项 id，缺省沿用满配")
    parser.add_argument("--alt-disc5", default="", help="非满配面板 5 号位主词条选项 id，缺省沿用满配")
    parser.add_argument("--alt-disc6", default="", help="非满配面板 6 号位主词条选项 id，缺省沿用满配")
    parser.add_argument("--alt-main-spec", default="", help="非满配面板的主词条文案，缺省沿用满配")
    parser.add_argument(
        "--mode",
        default="",
        help="面板模式（standard/rupture/fengyu），默认取预设的 panelMode；般岳=rupture 才会算贯穿力",
    )
    parser.add_argument(
        "--rows",
        default="",
        help=f"毕业面板展示行（逗号分隔，可用键 {sorted(TOTAL_LABELS)}），默认 {','.join(DEFAULT_ROWS)}；"
        "般岳（命破）传 hp,penforce,cr,cd；克拉蕾（锋御）传 def,actual_cr,blast_dmg,cr,cd",
    )
    parser.add_argument("--strategy", type=Path, default=DEFAULT_STRATEGY, help=f"攻略 JSON 路径，默认 {DEFAULT_STRATEGY}")
    parser.add_argument("--check", action="store_true", help="只比对，不写回")
    parser.add_argument(
        "--check-all",
        action="store_true",
        help="结构化校验所有 strategy/*/data/*.strategy.json 的 graduationPanel（不实算，只验形状）",
    )
    args = parser.parse_args()

    if args.check_all:
        return check_all_strategy_panels()

    panel, alt = compute(args)

    if not args.strategy.is_file():
        print(f"攻略文件不存在：{args.strategy}", file=sys.stderr)
        print("请先创建该文件（含其余攻略内容），再运行本脚本写入毕业面板。", file=sys.stderr)
        return 1

    strategy = json.loads(args.strategy.read_text(encoding="utf-8"))
    stored_alt = strategy.get("graduationPanelAlt")
    if (
        strip_timestamp(strategy.get("graduationPanel")) == strip_timestamp(panel)
        and strip_timestamp(stored_alt) == strip_timestamp(alt)
    ):
        print("毕业面板已是最新。")
        return 0

    if args.check:
        print("有漂移：攻略中的毕业面板与计算结果不一致", file=sys.stderr)
        return 1

    strategy["graduationPanel"] = panel
    if alt is not None:
        strategy["graduationPanelAlt"] = alt
    elif "graduationPanelAlt" in strategy:
        del strategy["graduationPanelAlt"]
    args.strategy.write_text(json.dumps(strategy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写入 {args.strategy}")
    for item in panel["totals"]:
        print(f"  {item['label']}: {item['value']}{item['unit']}")
    if alt is not None:
        print(f"  [{alt['title']}]")
        for item in alt["totals"]:
            print(f"  {item['label']}: {item['value']}{item['unit']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
