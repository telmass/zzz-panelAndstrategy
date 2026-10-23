#!/usr/bin/env python3
"""用仓库计算器（backend/services）计算任意代理人的「标准满词条毕业面板」。

面板不是手填的：从 ``data/catalog/agents.json`` 取 60 级基础面板，从
``data/catalog/weapons.json`` 取专武，从 ``data/catalog/drive-discs.json`` 取两套驱动盘，
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

   **装备组**（驱动盘）不只有「4+2」：
   * ``--set4-id`` 是 4 件套组，``--set2-id`` / ``--set2b-id`` / ``--set2c-id`` 是第
     1/2/3 组 2 件套。**4+2** 只用到前两个；**2+2+2** 用后三个、4 件套组传 ``none``。
   * 组序即槽位序：4 件套组占 set0，2 件套组依次占 set1 / set2。
   * **空字符串 = 没传（用默认）；``none`` = 明确没有这一组。**
   * **6 件全来自同一套**（4 件套组 + 同一套的 2 件套组）时，实际生效的是
     **一组 2 件套效果 + 一个 4 件套效果**——同一套的 2 件套效果不会因为多穿两件
     而叠加。脚本会把重复的 2 件套组并掉（并打一行提示），不额外占槽位。
   * 某套装的 2 件套效果**不可算**时（属性伤害 / 条件触发，见
     ``data/catalog/drive-discs.json`` 的 ``effect2Note``），那个组不占槽位——
     它仍然记在毕业面板的套装名里，但不贡献数值。

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

# 管道输出固定 UTF-8：Windows 上管道默认用系统代码页（本机 GBK），
# 父工具按 UTF-8 读会抛 UnicodeDecodeError 或读出乱码。控制台输出保持
# 系统代码页，否则用户在自己的终端里会看到乱码。
if hasattr(sys.stdout, "reconfigure") and not sys.stdout.isatty():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
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
#: set0/set2 的值为仓库选项表（data/rules/calculator-rules.json）中的二件套效果 id。
#: 副词的「面板暴击率 50% 档」只适用于专武局内再 +50% 的强攻代理人。
BUILD = {
    "disc_main": {"disc4": "cd_48", "disc5": "atk_pct_30", "disc6": "atk_pct_30"},
    # 默认装备组（叶瞬光参考实例 = 4+2）。组序即二件套效果的槽位序：
    # 4 件套组占 set0、2 件套组依次占 set1 / set2。
    "set_groups": [
        {"kind": "4", "id": "ep-1754", "effect": "dmg_10"},
        {"kind": "2", "id": "ep-1000", "effect": "cd_16"},
    ],
    # 叶瞬光参考实例的副词条分配——必须与 strategy/ye-shunguang/ 里已发布的
    # 毕业面板一致，否则 --check 会报漂移，页面上的面板也对不上脚本的输出。
    "sub_stats": {"cr": 13, "cd": 16, "atk_pct": 16, "atk_flat": 5, "pen_val": 4},
    # 非满配面板：叶瞬光参考实例的 29 词条版。攻略 JSON 里同时存着满配与非满配
    # 两份面板，因此默认也得能算出来——否则 --check 永远报漂移。
    "alt_sub_stats": {"cr": 13, "cd": 12, "atk_pct": 4},
    "alt_label": "非满配毕业面板（29 词条）",
}

#: 副词条 id -> 配装说明里的展示文案。
#:
#: 刻意**不**用规则表里的选项名（小攻击% / 大攻击% / 穿透值……）：攻略页的
#: 配装说明一直写成「攻击力% / 攻击力 / 穿透值」，改了会让已发布的毕业面板
#: 与实算结果对不上，--check 报漂移。
SUB_STAT_LABELS = {
    "hp_flat": "生命值",
    "hp_pct": "生命值%",
    "atk_flat": "攻击力",
    "atk_pct": "攻击力%",
    "def_flat": "防御力",
    "def_pct": "防御力%",
    "cr": "暴击率",
    "cd": "暴击伤害",
    "pen_val": "穿透值",
    "am": "异常精通",
}


def format_sub_spec(sub_stats: dict) -> str:
    """把副词条分配拼成配装说明文案。

    满配（54 条）写「54 条满配：…」，其余写「N 条：…」——与已发布的毕业面板
    里的文案逐字一致，改了会让 ``--check`` 报漂移。
    """
    total = sum(sub_stats.values())
    parts = "、".join(
        f"{SUB_STAT_LABELS.get(key, key)} ×{value}" for key, value in sub_stats.items()
    )
    prefix = "54 条满配：" if total == 54 else f"{total} 条："
    return prefix + parts


#: 配装说明文案（与 BUILD 实际一致；页面展示，勿加括号注释）。
SPEC_MAIN_STATS = "4 号位暴击伤害 +48%，5 / 6 号位攻击力 +30%"
SPEC_SUB_STATS = "54 条满配：暴击率 ×13、暴击伤害 ×16、攻击力% ×16、攻击力 ×5、穿透值 ×4"

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


#: 驱动盘「装备组」：6 个槽位不止「4+2」一种装法。
#:
#: - 4+2（最常见）：4 件套组 + 一组 2 件套
#: - 4+2+2：4 件套组 + 两组 2 件套
#: - 2+2+2：三组 2 件套，没有 4 件套组
#:
#: 计算器只建模**二件套效果**（4 件套效果多数是条件触发，不建模），
#: 所以每个装备组恰好贡献一个二件套效果，落到 ``set0`` / ``set1`` / ``set2``
#: 三个槽位上——三种装法都表达得下，**计算侧不需要改**。
#:
#: 每组：``(kind, id, effect)``，kind 是 "4" 或 "2"。
SET_GROUP_FLAGS = (
    # (kind, --id flag, --effect flag)
    ("4", "set4_id", "set4_effect"),
    ("2", "set2_id", "set2_effect"),
    ("2", "set2b_id", "set2b_effect"),
    ("2", "set2c_id", "set2c_effect"),
)


def _set_names(groups: list[dict]) -> dict:
    """装备组 -> 毕业面板 build 块里的套装名。

    ``set4`` 一组（没有则不出现该键）；``set2`` 一组时是字符串、多组时是数组。
    """
    names: dict = {}
    four = [group["name"] for group in groups if group["kind"] == "4" and group["name"]]
    if four:
        names["set4"] = four[0]
    two = [group["name"] for group in groups if group["kind"] == "2" and group["name"]]
    if two:
        names["set2"] = two[0] if len(two) == 1 else two
    return names


def resolve_set_groups(args, discs: dict) -> list[dict]:
    """把命令行给的装备组整理成有序列表。

    4 件套组在前、2 件套组按组序在后——顺序即二件套效果的槽位顺序
    （``set0`` / ``set1`` / ``set2``）。

    每组默认取 ``BUILD['set_groups']`` 里同序的默认组；命令行给了就覆盖。
    传 ``none`` 表示「这一组没有」（2+2+2 时没有 4 件套组）。
    """
    defaults = list(BUILD.get("set_groups") or [])
    groups: list[dict] = []
    for index, (kind, id_flag, effect_flag) in enumerate(SET_GROUP_FLAGS):
        default = defaults[index] if index < len(defaults) else {}
        set_id = getattr(args, id_flag, "") or default.get("id", "")
        effect = getattr(args, effect_flag, "") or default.get("effect", "")
        if set_id in ("", "none"):
            set_id, effect = "", ""
        if effect == "none":
            effect = ""
        if not set_id and not effect:
            continue
        name = discs[set_id]["name"] if set_id else ""
        groups.append(
            {"kind": kind, "id": set_id, "effect": effect, "name": name}
        )

    # 6 件全来自同一套（4 件套组 + 同一套的 2 件套组）时，实际生效的是
    # **一组 2 件套效果 + 一个 4 件套效果**——同一套的 2 件套效果不会因为
    # 多穿两件而叠加。重复的 2 件套组并掉，不额外占槽位。
    seen: set[str] = set()
    deduped: list[dict] = []
    for group in groups:
        if group["id"] and group["id"] in seen:
            print(
                f"注意：{group['name']} 同时出现在 4 件套组与 2 件套组里——"
                "同一套的 2 件套效果只生效一次，已并入 4 件套组。",
                file=sys.stderr,
            )
            continue
        if group["id"]:
            seen.add(group["id"])
        deduped.append(group)
    return deduped


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

    discs = load_all(REPO_ROOT / "data" / "catalog" / "drive-discs.json")
    set_groups = resolve_set_groups(args, discs)

    # 二件套效果按装备组顺序落进 set0 / set1 / set2 三个槽位。
    # 4+2 时是 set0=4 件套组、set1=2 件套组①；2+2+2 时三组各占一个槽位。
    #
    # **没有效果的组不占槽位**——比如某套装的 2 件套效果不可算（属性伤害 /
    # 条件触发，见 data/catalog/drive-discs.json 的 effect2Note），它仍然
    # 是「身上穿的那套」，但对面板数值毫无贡献，不该把后面的组挤掉。
    sets = {"set0": "", "set1": "", "set2": ""}
    for index, group in enumerate([g for g in set_groups if g["effect"]][:3]):
        sets[f"set{index}"] = group["effect"]

    sub_stats = parse_sub_stats(args.sub_stats) if args.sub_stats else dict(BUILD["sub_stats"])

    spec_main = args.main_spec or SPEC_MAIN_STATS
    spec_sub = args.sub_spec or (format_sub_spec(sub_stats) if args.sub_stats else SPEC_SUB_STATS)
    if sum(sub_stats.values()) != 54:
        print(f"注意：副词条合计 {sum(sub_stats.values())} 条，标准满配为 54 条。", file=sys.stderr)

    # 非满配面板：同一配装，副词条数由 --alt-sub-stats 人为界定（不要求 54 条）
    alt_sub_stats = (
        parse_sub_stats(args.alt_sub_stats)
        if args.alt_sub_stats
        else BUILD.get("alt_sub_stats")
    )
    if alt_sub_stats is not None:
        alt_spec = args.alt_spec or format_sub_spec(alt_sub_stats)
    else:
        alt_spec = args.alt_spec

    return {
        "disc_main": disc_main,
        "sets": sets,
        "set_groups": set_groups,
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
    agent = load_preset(REPO_ROOT / "data" / "catalog" / "agents.json", args.agent_id)
    weapon = load_preset(REPO_ROOT / "data" / "catalog" / "weapons.json", args.weapon_id)
    discs = load_all(REPO_ROOT / "data" / "catalog" / "drive-discs.json")
    build = resolve_build(args)
    # 装备组里的套装 id 必须存在。4 件套组可以没有（2+2+2），传 ``none`` 占位。
    for group in build["set_groups"]:
        if group["id"] and group["id"] not in discs:
            raise SystemExit(
                f"在 data/catalog/drive-discs.json 中找不到套装 {group['id']}"
            )
    base = agent["base"]
    # 模式按预设的 panelMode 推导（standard / rupture / armorer），般岳是命破 → rupture，
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
            # 音擎基础值是 v2 的二元组 base: {kind, value}——锋御音擎的 kind 是
            # "def"（基础防御力），不能一律当基础攻击力取。
            "baseKind": weapon["base"]["kind"],
            "baseValue": weapon["base"]["value"],
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
        # 套装名：4 件套组一组、2 件套组可能多组（2+2+2）。
        # 多组时写成数组，页面逐个渲染「图标 + 名称」。
        **_set_names(build["set_groups"]),
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
    alt["title"] = args.alt_label or BUILD.get("alt_label") or "非满配毕业面板"
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


def _help(text: str) -> str:
    """转义 help 串里的 ``%``。

    argparse 会对 help 串做一次 ``%``-格式化（``_expand_help``），字面的
    ``%`` 不转义就会抛 ``ValueError: unsupported format character``——
    于是 ``--help`` 直接崩掉。插值进来的文案里常有「+48%」这种百分号。
    """
    return text.replace("%", "%%")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--agent-id", default="ep-1687", help="代理人预设 id（data/catalog/agents.json）")
    parser.add_argument("--weapon-id", default="ep-1751", help="专武预设 id（data/catalog/weapons.json）")
    parser.add_argument("--set4-id", default="ep-1754", help="4 件套预设 id（data/catalog/drive-discs.json）")
    parser.add_argument("--set2-id", default="ep-1000", help="2 件套预设 id（data/catalog/drive-discs.json）")
    parser.add_argument("--core1", default="cr", help="核心选项 1（满级核心加成对应的选项 id）")
    parser.add_argument("--core2", default="atk_base", help="核心选项 2（满级核心加成对应的选项 id）")
    parser.add_argument("--core-spec", default="暴击率 +14.4%、基础攻击力 +75", help="配装说明里的核心技文案")
    parser.add_argument("--disc4", default="", help=_help(f"4 号位主词条选项 id，默认 {BUILD['disc_main']['disc4']}"))
    parser.add_argument("--disc5", default="", help=_help(f"5 号位主词条选项 id，默认 {BUILD['disc_main']['disc5']}"))
    parser.add_argument("--disc6", default="", help=_help(f"6 号位主词条选项 id，默认 {BUILD['disc_main']['disc6']}"))
    parser.add_argument("--set4-effect", default="", help=_help(f"4 件套二件套效果选项 id，默认 {BUILD['set_groups'][0]['effect']}"))
    parser.add_argument("--set2-effect", default="", help=_help(f"2 件套二件套效果选项 id，默认 {BUILD['set_groups'][1]['effect']}"))
    parser.add_argument(
        "--set2b-id",
        default="",
        help=_help("第 2 组 2 件套的套装 id（2+2+2 / 4+2+2 用）"),
    )
    parser.add_argument(
        "--set2b-effect",
        default="",
        help=_help("第 2 组 2 件套的 2 件套效果选项 id（占 set2 槽位）"),
    )
    parser.add_argument(
        "--set2c-id",
        default="",
        help=_help("第 3 组 2 件套的套装 id（2+2+2 用）"),
    )
    parser.add_argument(
        "--set2c-effect",
        default="",
        help=_help("第 3 组 2 件套的 2 件套效果选项 id（占 set2 槽位）"),
    )
    parser.add_argument("--sub-stats", default="", help=_help('副词条分配 JSON，如 \'{"cr":13,"cd":16,"hp_pct":15,"atk_pct":10}\''))
    parser.add_argument("--main-spec", default="", help=_help(f"配装说明主词条文案，默认 {SPEC_MAIN_STATS}"))
    parser.add_argument("--sub-spec", default="", help=_help(f"配装说明副词条文案，默认 {SPEC_SUB_STATS}"))
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
        help="面板模式（standard/rupture/armorer），默认取预设的 panelMode；般岳=rupture 才会算贯穿力",
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
