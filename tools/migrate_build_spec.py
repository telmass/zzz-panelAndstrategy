"""把攻略 JSON 里**手写**的毕业面板配装文案，迁移成机器可读的 ``buildSpec``。

背景
----
毕业面板的数值是实算的（``backend`` 同一份 ``core`` 公式），但**计算参数
只存在于命令行参数里**——``calc_graduation_panel.py`` 有 27 个 flag，跑完
就把结果固化成一段中文文案（「4 号位暴击率 +24%，5 号位穿透率 +24%」）
和一个中文串（「54 条满配：暴击率 ×9、爆伤 ×23、…」）。

于是「61 份面板里只有 1 份能复算」：其余 60 份的数值无法被重新验证，
文案与规则表各改各的。

本脚本把这两段文案**反推**成结构化的 ``buildSpec``，写进攻略 JSON：

```jsonc
"buildSpec": {
  "agentId": "ep-1687",
  "weaponId": "ep-1751",
  "mode": "standard",
  "rows": ["atk", "cr", "cd", "pv"],
  "discMain": {"disc4": "cr_24", "disc5": "pr_24", "disc6": "atk_pct_30"},
  "setGroups": [{"kind": "4", "discId": "ep-1754", "effectId": "dmg_10"},
                {"kind": "2", "discId": "ep-1000", "effectId": "cd_16"}],
  "core": ["cr", "atk_base"],
  "subStats": {"cr": 13, "cd": 16, "atk_pct": 16, "atk_flat": 5, "pen_val": 4},
  "tier": "full",
  "subStatBudget": {"total": 54, "source": "gameCap"}
}
```

**迁移必须自证**：每个反推出来的 spec 都要用 ``calc_graduation_panel.py``
的实算重跑一遍，结果与页面里存的 ``totals`` 逐值相等才算通过。
对不上的文件**原样保留、不写 buildSpec**，并在报告里点名——宁可少迁，
也不能迁出错值。

用法::

    python tools/migrate_build_spec.py            # 迁移（写回）
    python tools/migrate_build_spec.py --check    # 只报告，不写
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SKILL_SCRIPT = (
    ROOT / ".github" / "skills" / "agent-strategy" / "scripts" / "calc_graduation_panel.py"
)
CATALOG = ROOT / "data" / "catalog"
STRATEGY_DIR = ROOT / "strategy"


def _load_calc_script():
    """加载 ``calc_graduation_panel.py``（带 ``.github`` 路径的脚本，不是包）。"""
    spec = importlib.util.spec_from_file_location("calc_graduation_panel", SKILL_SCRIPT)
    if spec is None or spec.loader is None:  # pragma: no cover - 路径写错才会发生
        raise SystemExit(f"找不到 {SKILL_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CALC = _load_calc_script()
def _backend_on_path() -> None:
    """把后端源码目录挂到 sys.path（要读 core 的规则表）。"""
    backend_src = ROOT / "backend" / "src"
    if str(backend_src) not in sys.path:
        sys.path.insert(0, str(backend_src))


_backend_on_path()
from zzz_panel.core import options as option_table  # noqa: E402

#: 副词条 id 列表（真源在 core/options.py 的 SUB_STATS）。
SUBSTAT_IDS: tuple[str, ...] = tuple(substat.id for substat in option_table.SUB_STATS)


# ---------------------------------------------------------------- 文本 -> id

#: 主词条文案的**别名** -> 规则表里的规范选项名。
#:
#: 只在「选项名原样出现」都匹配不上时才用。别名给的是**规范名**，
#: 选项 id 由规则表反查——写死 id 会在选项改名后失效。
_SLOT_ALIASES: dict[str, tuple[tuple[tuple[str, ...], str], ...]] = {
    "disc4": (),
    "disc5": (
        (("属性增伤",), "属性伤害"),
        (("属性伤害", "伤害", "增伤"), "属性伤害"),
    ),
    "disc6": (
        (("能量自动回复", "回能"), "能量回复"),
    ),
}

#: 副词条文案 -> 副词条 id。
#:
#: 攻略里「爆伤」「穿透」「小攻击」都是简称；「无效词条」「其余词条」
#: 是**占位**（对数值无贡献），单独归一类。
SUB_STAT_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("hp_pct", ("生命值%",)),
    ("hp_flat", ("生命值", "小生命")),
    ("atk_pct", ("攻击力%",)),
    ("atk_flat", ("攻击力", "小攻击")),
    ("def_pct", ("防御力%",)),
    ("def_flat", ("防御力", "小防御")),
    ("cr", ("暴击率",)),
    ("cd", ("暴击伤害", "爆伤")),
    ("pen_val", ("穿透值", "穿透")),
    ("am", ("异常精通",)),
)

FILLER_LABELS = ("无效词条", "其余词条", "填充")


def _sub_spec_is_complete(text: str) -> bool:
    """副词条文案是不是**完整枚举**。

    两种写法：

    - **完整枚举**：「54 条满配：暴击率 ×9、爆伤 ×23、…、无效词条 ×1」
      或「生命值% ×20、防御力% ×15、…」——每一条词条都带条数，能还原分配。
    - **散文摘要**：「低词条参考：暴击率 ×10，穿透 90% 无提升」——
      只提了几项，还有别的数字没交代，**无法还原完整分配**。
      这类文案不能反推，否则只能靠猜（实测会把已发布的面板数值改错）。

    判据：把「N 条」（总条数）与「词条 ×N」（条目）都去掉之后，
    **剩下的数字就都是散文里的数**——有就不算完整枚举。
    括号里的补充说明（「受初始4词条约束，无填充」）先剥掉：它是注释，
    不是词条分配的一部分。
    """
    text = re.sub(r"（[^）]*）|\([^)]*\)", "", text)
    rest = re.sub(r"\d+\s*条", "", text)
    rest = re.sub(r"[^，,、。;；\s]{1,10}\s*[×xX]\s*\d+", "", rest)
    return not re.search(r"\d", rest)


def _catalog_by_name(path: Path, key: str = "name") -> dict[str, dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {item[key]: item for item in payload}


def _catalog_by_id(path: Path) -> dict[str, dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {item["id"]: item for item in payload}


def _pick_main_stat(text: str, slot: str, rules: dict) -> str | None:
    """一段主词条文案（「暴击率 +24%」）-> 规则表选项 id。

    先按规则表里的**选项名**精确匹配（选项名是权威口径），
    名称对不上时再按**别名**兜底（「电伤害」「火属性伤害」都指属性伤害，
    「能量自动回复」指能量回复）。别名只给**规范名**，选项 id 从规则表反查——
    写死 id 会在选项改名后失效（冲击力 24% -> 18% 就踩过）。
    """
    options = rules[f"{slot}Options"]
    for option in options:
        name = option.get("name") or ""
        if name and name in text:
            return option["id"]
    for aliases, canonical in _SLOT_ALIASES.get(slot, ()):
        if any(word in text for word in aliases):
            for option in options:
                if option.get("name") == canonical:
                    return option["id"]
    return None


def _parse_main_stats(text: str, rules: dict) -> dict[str, str]:
    """「4 号位暴击率 +24%，5 号位穿透率 +24%，6 号位攻击力 +30%」-> 三个选项 id。

    攻略里还有合并写法（「4 / 5 / 6 号位生命值 +30%」「5 / 6 号位攻击力 +30%」），
    一段文案对应多个槽位，逐个记。
    """
    result: dict[str, str] = {}
    for chunk in re.split(r"[、,，;；]", text):
        chunk = chunk.strip()
        if not chunk:
            continue
        match = re.search(r"([456](?:\s*/\s*[456])*)\s*号位", chunk)
        if not match:
            continue
        for number in re.findall(r"[456]", match.group(1)):
            slot = f"disc{number}"
            ident = _pick_main_stat(chunk, slot, rules)
            if ident:
                result[slot] = ident
    return result


def _parse_sub_stats(text: str) -> dict[str, int]:
    """副词条文案 -> {副词条 id: 条数}。填充词条单列，不进数值。"""
    result: dict[str, int] = {}
    for chunk in re.split(r"[、,，;；]", text):
        chunk = chunk.strip()
        if not chunk:
            continue
        match = re.search(r"([^\d×xX+]+?)\s*[×xX]\s*(\d+)", chunk)
        if not match:
            continue
        label = re.sub(r"\s+", "", match.group(1))
        count = int(match.group(2))
        if any(filler in label for filler in FILLER_LABELS):
            continue
        for ident, keywords in SUB_STAT_KEYWORDS:
            if any(word in label for word in keywords):
                result[ident] = result.get(ident, 0) + count
                break
    return result


def _parse_core(text: str, rules: dict) -> list[str]:
    """核心加成文案 -> 两个核心选项 id。

    按「名称 + 数值」精确匹配（「异常精通 +90」是 ``am_90``，不是 ``am`` 的 +54）。
    数值对不上时（例如克拉蕾「暴击率 +28.8%」其实是两个 +14.4%）退回按名称匹配。
    """
    picked: list[str] = []
    for chunk in re.split(r"[、,，;；]", text):
        chunk = chunk.strip()
        if not chunk or chunk.startswith("（") or chunk.startswith("("):
            continue
        matched = False
        for name, value in re.findall(r"([^\d+]+?)\s*\+?\s*([\d.]+)", chunk):
            name = name.strip()
            try:
                number = float(value)
            except ValueError:
                continue
            for option in rules["coreOptions"]:
                if option["name"] == name and float(option["value"]) == number:
                    if option["id"] not in picked:
                        picked.append(option["id"])
                    matched = True
                    break
        if matched:
            continue
        for option in rules["coreOptions"]:
            if option["label"] in chunk or option["name"] in chunk:
                if option["id"] not in picked:
                    picked.append(option["id"])
                break
    # 「按两个 14.4% 选项计入」这类补注：数量不足时用第一个补齐。
    while len(picked) < 2 and picked:
        picked.append(picked[0])
    return picked[:2]


def _set_ids(names: Any, discs: dict[str, dict]) -> list[str]:
    """套装名（字符串或数组）-> 套装 id 列表。"""
    if not names:
        return []
    items = names if isinstance(names, list) else [names]
    result: list[str] = []
    for item in items:
        match = next((d for d in discs.values() if d["name"] == item), None)
        if match:
            result.append(match["id"])
    return result

def _rows_from_totals(totals: list[dict]) -> list[str]:
    """页面里存的面板行 -> 展示行 key 列表（**按页面上的顺序**）。

    展示行逐代理人都不同（叶瞬光 atk/cr/cd/pv，般岳 hp/penforce/cr/cd，
    克拉蕾 def/actual_cr/cd/pv），所以不能套默认值——要从页面实际存的
    那一组行反推。
    """
    by_label = _label_to_key()
    rows: list[str] = []
    for row in totals:
        key = by_label.get(row.get("label"))
        if key:
            rows.append(key)
    return rows


def _core_slots(agent: dict) -> list[str]:
    """代理人的核心加成 -> 两个核心槽位的选项 id。

    **以预设为准，不从文案反推**：``data/catalog/agents.json`` 的 ``core[]``
    是权威事实（``optionId`` + ``optionCount``），而攻略页的「配装说明」是
    手写描述——两者会漂移（实测：orphie-magus 的文案写「暴击率 +14.4%」，
    预设里其实是「基础能量自动回复」）。**事实侧为准，文案由事实派生。**

    ``optionCount`` 是该选项占几个槽位（克拉蕾的核心全是暴击率，占两槽）。
    """
    slots: list[str] = []
    for entry in agent.get("core") or []:
        count = int(entry.get("optionCount") or 1)
        slots.extend([entry["optionId"]] * count)
    return slots[:2]


def _core_text(agent: dict) -> str:
    """代理人的核心加成 -> 配装说明里的核心文案（由预设派生）。"""
    parts: list[str] = []
    for entry in agent.get("core") or []:
        count = int(entry.get("optionCount") or 1)
        total = float(entry.get("totalValue") or 0)
        per = total / count if count else total
        text = f"{per:g}"
        parts.extend([f"{entry.get('label') or entry['optionId']} +{text}"] * count)
    return "、".join(parts)


def _option_label(rules: dict, slot: str, ident: str) -> str:
    """规则表里某个槽位选项的展示串（「暴击率 +24%」）。

    **不直接用规则表的 label**：驱动盘各表的 label 写法不统一（DISC 表没有
    「+」，CORE 表有），而攻略页的文案一直写「+24%」。这里按「名称 + 数值」
    重新拼，保证派生出来的文案与历史措辞一致。
    """
    for option in rules[f"{slot}Options"]:
        if option["id"] == ident:
            unit = "%" if option["kind"] == "pct" else ""
            return f"{option['name']} +{option['value']:g}{unit}"
    return ident


def _main_text(disc_main: dict, rules: dict) -> str:
    """主词条文案：由 ``discMain`` + 规则表派生。

    顺带解决历史文案的三类问题：属性伤害的各种写法（「电伤害」「火属性伤害」）
    统一成规则表的规范名；**选项改名后文案自动跟上**（冲击力 24% → 18%）。
    """
    parts = []
    for slot, prefix in (("disc4", "4 号位"), ("disc5", "5 号位"), ("disc6", "6 号位")):
        ident = disc_main.get(slot)
        if ident:
            parts.append(f"{prefix}{_option_label(rules, slot, ident)}")
    return "，".join(parts)


def _sub_text(sub_stats: dict, declared: int, rules: dict, tier: str) -> str:
    """副词条文案：由 ``subStats`` + 规则表的展示名派生。

    填充条目（「无效词条」）在数值上是 0，但**占条数**，所以留在文案里；
    ``buildSpec.subStats`` 只放真正有贡献的词条，
    总条数记在 ``subStatBudget.total``。
    """
    labels = rules["displayNames"]["subStatLabels"]
    effective = sum(sub_stats.values())
    parts = [f"{labels.get(ident, ident)} ×{count}" for ident, count in sub_stats.items()]
    if declared > effective:
        parts.append(f"无效词条 ×{declared - effective}")
    prefix = f"{declared} 条满配：" if tier == "full" else f"{declared} 条："
    return prefix + "、".join(parts)

def _solve_from_rows(
    build: dict,
    catalogs: dict,
    rules: dict,
    totals: list[dict],
    agent: dict | None,
) -> dict | None:
    """副词条文案是**散文摘要**时，从面板的展示行**反解**条数。

    像「低词条参考：暴击率 ×10，穿透 90% 无提升」这种文案只列了部分词条，
    剩下的「其余词条」没有交代——但它们**不影响面板展示的那几行**（否则
    文案早就说不清了）。

    于是可以这样解：

    1. 副词条全空时算一次面板，得到基准值；
    2. 每种副词条各加 1 条算一次，得到它对每一行的**单位效果**；
    3. 每个展示行的缺口 = Σ(条数 × 单位效果)，反解出条数；
    4. 用解出来的条数重算，与页面对不上就放弃（宁缺勿错）。

    解不出的行（效果不整除、或两种词条同时影响一行且无法区分）→ 返回 None。
    """
    if not totals or not agent:
        return None
    disc_main = _parse_main_stats(build.get("mainStats", ""), rules)
    if len(disc_main) != 3:
        return None
    core = _core_slots(agent)
    if not core:
        return None
    set_groups: list[dict] = []
    for kind, names in (("4", build.get("set4")), ("2", build.get("set2"))):
        for disc_id in _set_ids(names, catalogs["discs"]):
            effect = catalogs["discs"][disc_id].get("effect2")
            set_groups.append({"kind": kind, "discId": disc_id, "effectId": effect or ""})
    weapon = next(
        (w for w in catalogs["weapons"].values() if w["name"] == build.get("weapon")), None
    )
    if weapon is None:
        return None

    label_to_key = _label_to_key()

    def _panel(sub_stats: dict[str, int]) -> dict[str, float]:
        args = CALC.args_from_build_spec(
            {
                "agentId": agent["id"],
                "weaponId": weapon["id"],
                "mode": agent.get("panelMode") or "standard",
                "rows": [label_to_key.get(t.get("label"), "") for t in totals],
                "discMain": disc_main,
                "setGroups": set_groups,
                "core": core,
                "subStats": sub_stats,
            }
        )
        request, _ = CALC.build_request(args)
        panel = CALC.compute_panel(args, request, {})
        return {row["label"]: float(row["value"]) for row in panel["totals"]}

    label_to_key = _label_to_key()
    baseline = _panel({})
    unit: dict[str, dict[str, float]] = {}
    for substat_id in SUBSTAT_IDS:
        delta = _panel({substat_id: 1})
        unit[substat_id] = {
            label: delta.get(label, 0.0) - baseline.get(label, 0.0)
            for label in baseline
        }

    solved: dict[str, int] = dict(_parse_sub_stats(build.get("subStats", "")))
    for row in totals:
        label = row.get("label")
        key = label_to_key.get(label)
        if key is None:
            return None
        residual = float(row["value"]) - baseline.get(label, 0.0)
        # 先扣掉文案里已经写明的条数
        for substat_id, count in solved.items():
            residual -= count * unit[substat_id].get(label, 0.0)
        if abs(residual) <= 1e-6:
            continue  # 这一行已经被文案交代清楚了
        contributors = [
            substat_id
            for substat_id in SUBSTAT_IDS
            if substat_id not in solved
            and abs(unit[substat_id].get(label, 0.0)) > 1e-9
        ]
        if not contributors:
            return None  # 缺口无法用副词条解释 → 放弃
        if len(contributors) > 1:
            # 两种词条影响同一行（如攻击力% 与攻击力）→ 无法区分，放弃。
            return None
        step = unit[contributors[0]][label]
        count = residual / step
        if count < -1e-6 or abs(count - round(count)) > 1e-6:
            return None
        solved[contributors[0]] = solved.get(contributors[0], 0) + int(round(count))
    if not solved:
        return None
    declared = _declared_total(build.get("subStats", ""))
    effective = sum(solved.values())
    return {
        "agentId": agent["id"],
        "weaponId": weapon["id"],
        "mode": agent.get("panelMode") or "standard",
        "rows": [label_to_key.get(t.get("label"), "") for t in totals],
        "discMain": disc_main,
        "setGroups": set_groups,
        "core": core,
        "subStats": solved,
        "tier": "near",
        "subStatBudget": {
            "total": declared or effective,
            "effective": effective,
            "source": "solved" if declared and declared != effective else "gameCap",
        },
    }


def _spec_from_build(
    build: dict, catalogs: dict, rules: dict, totals: list[dict], agent: dict | None = None
) -> dict | None:
    """从 ``graduationPanel.build`` 文案反推 buildSpec。解析不了返回 None。"""
    agents = catalogs["agents"]
    weapons = catalogs["weapons"]
    discs = catalogs["discs"]

    agent = next((a for a in agents.values() if a["name"] == build.get("agent")), None)
    weapon = next((w for w in weapons.values() if w["name"] == build.get("weapon")), None)
    if agent is None or weapon is None:
        return None
    disc_main = _parse_main_stats(build.get("mainStats", ""), rules)
    if len(disc_main) != 3:
        return None

    set_groups: list[dict] = []
    four = _set_ids(build.get("set4"), discs)
    for disc_id in four:
        effect = discs[disc_id].get("effect2")
        set_groups.append(
            {"kind": "4", "discId": disc_id, "effectId": effect or ""}
        )
    for disc_id in _set_ids(build.get("set2"), discs):
        effect = discs[disc_id].get("effect2")
        set_groups.append(
            {"kind": "2", "discId": disc_id, "effectId": effect or ""}
        )

    core = _core_slots(agent) if agent else _parse_core(build.get("core", ""), rules)
    if not core:
        return None

    sub_stats = _parse_sub_stats(build.get("subStats", ""))
    if not sub_stats:
        return None
    if not _sub_spec_is_complete(build.get("subStats", "")):
        return None
    if not _sub_spec_is_complete(build.get("subStats", "")):
        return None

    # 总条数取**文案声明的那个**（「54 条满配」），不是有效条数之和——
    # 差值就是填充条目（「无效词条」）：它占条数但对数值没有贡献。
    declared = _declared_total(build.get("subStats", ""))
    effective = sum(sub_stats.values())
    total = declared or effective
    return {
        "agentId": agent["id"],
        "weaponId": weapon["id"],
        "mode": agent.get("panelMode") or "standard",
        "rows": _rows_from_totals(totals),
        "discMain": disc_main,
        "setGroups": set_groups,
        "core": core,
        "subStats": sub_stats,
        "tier": "full",
        "subStatBudget": {
            "total": total,
            "effective": effective,
            "source": "gameCap" if total == 54 else "editorial",
        },
    }


def _args_from_spec(spec: dict) -> SimpleNamespace:
    """buildSpec -> ``calc_graduation_panel.py`` 认识的参数命名空间。"""
    groups = spec["setGroups"]
    four = [g for g in groups if g["kind"] == "4"]
    two = [g for g in groups if g["kind"] == "2"]

    def group_flag(index: int, prefix: str) -> tuple[str, str]:
        if prefix == "set4":
            group = four[index] if index < len(four) else None
        elif prefix == "set2":
            group = two[index] if index < len(two) else None
        else:
            group = None
        if group is None:
            # **必须显式传 "none"**：脚本把「空 flag」当成「用 BUILD 默认值」，
            # 于是没用到的装备组会悄悄继承参考实例（叶瞬光）的套装。
            return "none", "none"
        return group["discId"], group.get("effectId") or "none"

    set4_id, set4_effect = group_flag(0, "set4")
    set2_id, set2_effect = group_flag(0, "set2")
    set2b_id, set2b_effect = group_flag(1, "set2")
    set2c_id, set2c_effect = group_flag(2, "set2")

    sub_stats = ",".join(f"{key}:{value}" for key, value in spec["subStats"].items())
    return SimpleNamespace(
        agent_id=spec["agentId"],
        weapon_id=spec["weaponId"],
        set4_id=set4_id,
        set2_id=set2_id,
        set2b_id=set2b_id,
        set2c_id=set2c_id,
        core1=spec["core"][0] if spec["core"] else "",
        core2=spec["core"][1] if len(spec["core"]) > 1 else "",
        core_spec="",
        disc4=spec["discMain"]["disc4"],
        disc5=spec["discMain"]["disc5"],
        disc6=spec["discMain"]["disc6"],
        set4_effect=set4_effect,
        set2_effect=set2_effect,
        set2b_effect=set2b_effect,
        set2c_effect=set2c_effect,
        sub_stats=sub_stats,
        main_spec="",
        sub_spec="",
        alt_sub_stats=None,
        alt_spec="",
        alt_disc4="",
        alt_disc5="",
        alt_disc6="",
        alt_main_spec="",
        alt_label="",
        label="",
        mode=spec["mode"],
        rows=",".join(spec["rows"]),
    )


def _label_to_key() -> dict[str, str]:
    """展示名 -> 面板行 key。

    除当前规则表里的展示名外，还认**旧展示名**（``增伤`` -> ``dmg``）——
    改过展示名之后，尚未重算的旧页面仍然写着旧名，比对时不能因此判成「不一致」。
    """
    mapping = {label: key for key, label in CALC.TOTAL_LABELS.items()}
    mapping.setdefault("增伤", "dmg")
    return mapping


def _totals_match(spec: dict, expected: list[dict]) -> bool:
    """用 buildSpec 重算，面板各行数值是否与页面里存的一致。

    **按行 key 比，不按展示名比**——展示名改过（增伤 -> 属性伤害）不该判成数值漂移。
    """
    args = CALC.args_from_build_spec(spec)
    request, _ = CALC.build_request(args)
    computed = CALC.compute_panel(args, request, {"agent": "", "weapon": ""})
    mapping = _label_to_key()
    got = {mapping.get(row["label"], row["label"]): row["value"] for row in computed["totals"]}
    want = {mapping.get(row["label"], row["label"]): row["value"] for row in expected}
    return got == want


def _declared_total(text: str) -> int:
    """副词条文案里声明的总条数（「54 条满配：…」-> 54）。"""
    match = re.search(r"(\d+)\s*条", text)
    return int(match.group(1)) if match else 0


def _spec_candidates(
    build: dict, catalogs: dict, rules: dict, totals: list[dict]
) -> list[dict]:
    """反推出的 buildSpec 候选（按可信度排序）。

    正常只有一个候选。文案里写了「无效词条 ×N」而页面数值又把那 N 条
    算成了某种具体词条时（页面的数值是当初实算出来的），补一个候选：
    把这 N 条**整份**归到某一种词条上，逐种试。
    """
    spec = _spec_from_build(build, catalogs, rules, totals)
    if spec is None:
        return []
    candidates = [spec]

    declared = _declared_total(build.get("subStats", ""))
    actual = sum(spec["subStats"].values())
    filler = declared - actual
    if filler > 0:
        for ident in SUB_STAT_KEYWORDS:
            variant = json.loads(json.dumps(spec))
            variant["subStats"][ident[0]] = (
                variant["subStats"].get(ident[0], 0) + filler
            )
            variant["subStatBudget"] = {"total": declared, "source": "gameCap"}
            candidates.append(variant)
    return candidates


def migrate_file(path: Path, catalogs: dict, rules: dict, check_only: bool) -> tuple[bool, str]:
    """反推 buildSpec 并写进攻略 JSON。

    **判定口径**（2026-10-22 定）：事实侧为准，数值一律重算。

    - **事实侧**（``data/catalog/`` + 规则表）是权威：代理人的核心加成取
      ``agents.json``，套装效果取 ``drive-discs.json`` 的 ``effect2``，
      主词条按**名称**匹配规则表（选项改名后仍能对上）。
    - **意图侧**（攻略页的配装说明）只提供「选了哪条主词条 / 副词条各几条」。
    - **数值**：由 ``calc_graduation_panel.py`` 重算，不迁就旧值——旧值是
      旧目录口径下的快照，目录变了它就该跟着变（差异由调用方打印出来核对）。

    所以这里**不再**要求「重算结果 == 页面里存的数值」；对不上的页面，
    数值会被刷新成当前口径，差异写进变更记录。
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    problems: list[str] = []
    migrated = 0
    stale = 0
    agents = catalogs["agents"]
    for key, tier in (("graduationPanel", "full"), ("graduationPanelAlt", "near")):
        panel = data.get(key)
        if not panel:
            continue
        build = panel.get("build") or {}
        agent = next((a for a in agents.values() if a["name"] == build.get("agent")), None)
        spec = _spec_from_build(build, catalogs, rules, panel.get("totals") or [], agent)
        if spec is None:
            # 文案是散文摘要 -> 从展示行反解条数（见 _solve_from_rows）
            spec = _solve_from_rows(build, catalogs, rules, panel.get("totals") or [], agent)
        if spec is None:
            problems.append(f"{key} 无法从文案反推 buildSpec")
            # **清掉可能存在的旧 buildSpec**：它是用散文摘要硬猜出来的，
            # 留着会让闸门拿它去重算，把已发布的数值算错。
            if "buildSpec" in panel:
                del panel["buildSpec"]
                data[key] = panel
                stale += 1
            continue
        spec["tier"] = tier
        panel["buildSpec"] = spec
        # 配装说明文案也由 buildSpec 派生：核心取预设、主词条取规则表、
        # 副词条取解析结果——**文案与数值同源**，不再各写各的。
        build = dict(panel.get("build") or {})
        if agent:
            build["core"] = _core_text(agent)
        build["mainStats"] = _main_text(spec["discMain"], rules)
        build["subStats"] = _sub_text(
            spec["subStats"], spec["subStatBudget"]["total"], rules, tier
        )
        panel["build"] = build
        data[key] = panel
        migrated += 1

    if problems:
        # **按面板粒度处理**：一个面板反推不出来，不该连坐另一个能反推出来的。
        # 只要有面板成功，就落盘（成功的写进去，失败的清掉旧 spec）。
        if not check_only and (migrated or stale):
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        return bool(migrated), "；".join(problems)
    if not check_only:
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
    return True, "已迁移" if not check_only else "可迁移"


def _new_rows(spec: dict) -> dict[str, float]:
    """buildSpec 重算出来的面板行（按行 key）。"""
    args = CALC.args_from_build_spec(spec)
    request, _ = CALC.build_request(args)
    computed = CALC.compute_panel(args, request, {"agent": "", "weapon": ""})
    mapping = _label_to_key()
    return {
        mapping.get(row["label"], row["label"]): row["value"]
        for row in computed["totals"]
    }


def _panel_diffs(path: Path) -> list[str]:
    """页面里存的数值 vs 按 buildSpec 重算的数值（只报不一致的）。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    mapping = _label_to_key()
    out: list[str] = []
    for key in ("graduationPanel", "graduationPanelAlt"):
        panel = data.get(key)
        if not panel or not panel.get("buildSpec"):
            continue
        old = {
            mapping.get(row["label"], row["label"]): row["value"]
            for row in panel.get("totals") or []
        }
        new = _new_rows(panel["buildSpec"])
        for label in sorted(set(old) | set(new)):
            if old.get(label) != new.get(label):
                out.append(
                    f"{key}.{label}: 页面 {old.get(label)} → 实算 {new.get(label)}"
                )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="只报告，不写文件")
    args = parser.parse_args()

    catalogs = {
        "agents": _catalog_by_name(CATALOG / "agents.json"),
        "weapons": _catalog_by_name(CATALOG / "weapons.json"),
        "discs": _catalog_by_id(CATALOG / "drive-discs.json"),
    }
    rules = json.loads((ROOT / "data" / "rules" / "calculator-rules.json").read_text(encoding="utf-8"))

    ok = failed = 0
    diffs: list[str] = []
    for path in sorted(STRATEGY_DIR.glob("*/data/*.strategy.json")):
        success, message = migrate_file(path, catalogs, rules, args.check)
        if not success:
            failed += 1
            print(f"  跳过 {path.relative_to(ROOT)}：{message}")
            continue
        ok += 1
        if not args.check:
            for line in _panel_diffs(path):
                diffs.append(f"{path.parent.parent.name}: {line}")
    print(f"迁移完成：{ok} 份成功，{failed} 份跳过" + ("（--check，未写文件）" if args.check else ""))
    if diffs:
        print(f"\n数值会被刷新的地方（{len(diffs)} 处）：")
        for line in diffs:
            print(f"  {line}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
