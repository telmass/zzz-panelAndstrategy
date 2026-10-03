"""legacy 抽样用例对拍（第 3 步验收项 16）。

期望值由 ``frontend/tools/dump_legacy_cases.mjs`` 从**未经改动的 legacy 页面**
导出：它在 jsdom 里加载 ``frontend/legacy/pages/calculator.html`` 与四个原始脚本，
按真实交互路径设置表单后读取结果区。因此本文件断言的是「Python 与旧页面数值全等」。

四组场景与 ``frontend/tests/legacy-parity.spec.ts`` 一一对应：
默认空配置、满配、命破代理人、锋御代理人。

重新生成期望值::

    cd frontend && node tools/dump_legacy_cases.mjs ../backend/tests/legacy_cases.json
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from zzz_panel.core.modifiers import PanelSelection
from zzz_panel.core.panel import calculate_selection

FIXTURE = Path(__file__).with_name("legacy_cases.json")

# legacy 结果行标签 → Python 结果键。锋御模式下「能量回复」显示为「锐能自动累积」。
_ROW_KEY = {
    "生命值": "hp",
    "攻击力": "atk",
    "防御力": "def",
    "贯穿力": "penforce",
    "暴击率": "cr",
    "暴击伤害": "cd",
    "实际暴击率": "actual_cr",
    "锐暴伤害": "blast_dmg",
    "增伤": "dmg",
    "穿透率": "pr",
    "穿透值": "pv",
    "异常精通": "am",
    "异常掌控": "ac",
    "冲击力": "imp",
    "能量回复": "er",
    "锐能自动累积": "er",
}

# legacy 下拉项文案 → core 规则表 id。legacy 用数组下标，此处按文案对齐。
_CORE_BY_LABEL = {
    "暴击率 +14.4%": "cr",
    "暴击伤害 +28.8%": "cd",
    "基础生命值 +420": "hp_base",
    "基础攻击力 +75": "atk_base",
    "生命值百分比 +18%": "hp_pct",
    "攻击力 +21%": "atk_pct_21",
    "异常掌控 +36": "ac",
    "异常精通 +54": "am",
    "异常精通 +90": "am_90",
    "穿透率 +14.4%": "pr",
    "基础能量自动回复 +0.36": "er_base",
    "基础冲击力 +18": "impact_base",
}
_DISC4_BY_LABEL = {
    "攻击力 30%": "atk_pct_30",
    "生命值 30%": "hp_pct_30",
    "防御力 48%": "def_pct_48",
    "暴击率 24%": "cr_24",
    "暴击伤害 48%": "cd_48",
    "异常精通 92": "am_92",
}
_DISC5_BY_LABEL = {
    "攻击力 30%": "atk_pct_30",
    "生命值 30%": "hp_pct_30",
    "防御力 48%": "def_pct_48",
    "穿透率 24%": "pr_24",
    "增伤 30%": "dmg_30",
}
_DISC6_BY_LABEL = {
    "攻击力 30%": "atk_pct_30",
    "生命值 30%": "hp_pct_30",
    "防御力 48%": "def_pct_48",
    "冲击力 24%": "impact_pct_24",
    "异常掌控 30%": "ac_pct_30",
    "能量回复 60%": "er_pct_60",
}
_SET_BY_LABEL = {
    "生命 +10%": "hp_pct_10",
    "攻击力 +10%": "atk_pct_10",
    "防御力 +10%": "def_pct_10",
    "暴击率 +8%": "cr_8",
    "暴击伤害 +16%": "cd_16",
    "冲击力 +6%": "impact_pct_6",
    "异常掌控 +8%": "ac_pct_8",
    "能量回复 +20%": "er_pct_20",
    "增伤 +10%": "dmg_10",
    "异常精通 +30": "am_30",
}

# 夹具里的音擎：id → (基础值, 基础归属, 副词条目标, 副词条数值, 副词条单位, 副词条文案)
_FIXTURE_WEAPONS = {
    "ep-211": ("atk", 713.0, "cd", 48.0, "pct", "暴击伤害"),
}


def load_cases() -> list[dict]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _build(case: dict) -> tuple[PanelSelection, dict, dict]:
    """把夹具里的一组场景还原成 PanelSelection + 基础面板。"""
    mode = "standard"
    if case["name"] == "ep-1299":
        mode = "rupture"
    elif case["name"] == "ep-2145":
        mode = "fengyu"

    core = tuple(_CORE_BY_LABEL.get(label, "") for label in case.get("core", ("", "")))
    disc_raw = case.get("discMain", {})
    disc = {
        "disc4": _DISC4_BY_LABEL.get(disc_raw.get("disc4", ""), ""),
        "disc5": _DISC5_BY_LABEL.get(disc_raw.get("disc5", ""), ""),
        "disc6": _DISC6_BY_LABEL.get(disc_raw.get("disc6", ""), ""),
    }
    sets_raw = case.get("sets", ["", "", ""])
    sets = tuple(_SET_BY_LABEL.get(label, "") for label in sets_raw)

    weapon = case.get("weapon")
    if weapon:
        base_kind, base_value, sub_target, sub_value, sub_kind, sub_label = _FIXTURE_WEAPONS[weapon["id"]]
    else:
        base_kind, base_value, sub_target, sub_value, sub_kind, sub_label = "atk", 0.0, "", 0.0, "pct", ""

    selection = PanelSelection(
        mode=mode,
        core=core,
        disc_main=disc,
        sub_stats=dict(case.get("subStats", {})),
        sets=sets,
        weapon_sub_target=sub_target,
        weapon_sub_value=sub_value,
        weapon_sub_kind=sub_kind,
        weapon_sub_label=sub_label,
        weapon_base_atk=base_value if base_kind == "atk" else 0.0,
        weapon_base_def=base_value if base_kind == "def" else 0.0,
    )

    # 空配置场景没有 base 字段，用 legacy 的默认表单值
    defaults = {"hp": 8000.0, "atk": 1000.0, "def": 600.0, "impact": 90.0,
                "cr": 5.0, "cd": 50.0, "ac": 100.0, "am": 100.0, "pr": 0.0, "er": 1.2}
    base = case.get("base", defaults)
    return selection, dict(base), {"mode": mode}


def _expected(case: dict) -> dict:
    """legacy 行标签 + 数值 → Python 结果键 + 数值。"""
    out = {}
    for row in case["rows"]:
        key = _ROW_KEY.get(row["label"])
        assert key is not None, f"夹具出现未映射的行标签：{row['label']}"
        out[key] = row["num"]
    return out


def _actual(result: dict) -> dict:
    """Python 结果 → 与 ``_expected`` 同形状的字典。"""
    out = dict(result["totals"])
    mode_stats = dict(result["mode_stats"])
    # core 用 fengyu_blast_dmg 命名，legacy 行标签「锐暴伤害」映射为 blast_dmg，
    # 这里取别名后移除原键，避免同一行被计入两次。
    blast = mode_stats.pop("fengyu_blast_dmg", None)
    out.update(mode_stats)
    if blast is not None:
        out["blast_dmg"] = blast
    return out


CASES = load_cases()


@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_python_matches_legacy_page(case: dict) -> None:
    """同一组输入下，Python 计算结果与 legacy 页面逐行全等。"""
    selection, base, _ = _build(case)
    actual = _actual(calculate_selection(selection, base))
    expected = _expected(case)

    assert set(actual) == set(expected), (
        f"结果行不一致：Python 独有 {sorted(set(actual) - set(expected))}，"
        f"legacy 独有 {sorted(set(expected) - set(actual))}"
    )

    mismatches = {
        key: (expected[key], actual[key])
        for key in expected
        if actual[key] != pytest.approx(expected[key], rel=1e-9, abs=1e-6)
    }
    assert not mismatches, f"以下行与 legacy 不一致（期望, 实际）：{mismatches}"


@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_breakdown_covers_every_visible_legacy_row(case: dict) -> None:
    """结构化明细必须覆盖 legacy 的每一个可见结果行。"""
    selection, base, _ = _build(case)
    result = calculate_selection(selection, base)
    expected = _expected(case)

    assert set(result["breakdown"]) == set(expected)
    for lines in result["breakdown"].values():
        assert lines, "明细行不应为空"
