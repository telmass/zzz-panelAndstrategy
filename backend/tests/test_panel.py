"""core 层纯函数回归测试。

EXAMPLE 与其期望值来自重构前的仓库根 ``main.py``，用于锁定迁移前后的数值一致。
模式专属数值与核心计算一并在此覆盖。
"""

from __future__ import annotations

import pytest

from zzz_panel.cli import EXAMPLE, _fmt
from zzz_panel.core.models import PanelInputs
from zzz_panel.core.modifiers import PanelSelection
from zzz_panel.core.options import SET_OPTIONS, find_option
from zzz_panel.core.panel import calculate_panel, calculate_selection

EXPECTED_EXAMPLE = {
    "hp": 7673.0,
    "atk": 1601.0,
    "def": 612.0,
    "cr": 48.2,
    "cd": 155.6,
    "dmg": 10.0,
    "pr": 0.0,
    "impact": 93.0,
    "anomaly_ctrl": 101.52,
    "energy_regen": 1.2,
    "anomaly_mastery": 93.0,
    "pen_value": 0.0,
}

#: `calculate_selection` 要求完整的基础面板键集，缺失的键按 0 处理。
_ZERO_BASE = {
    key: 0.0 for key in ("hp", "atk", "def", "cr", "cd", "pr", "am", "ac", "impact", "er")
}


@pytest.mark.parametrize("key,expected", sorted(EXPECTED_EXAMPLE.items()))
def test_example_matches_pre_refactor_output(key: str, expected: float) -> None:
    assert calculate_panel(EXAMPLE)[key] == pytest.approx(expected)


def test_percent_aggregation_is_additive() -> None:
    inputs = PanelInputs(base_cr=10.0, set_cr=8.0, sub_cr=4.8, disc_main={"cr": 24.0})
    assert calculate_panel(inputs)["cr"] == pytest.approx(46.8)


def test_flat_stats_use_base_times_percent_plus_flat() -> None:
    inputs = PanelInputs(
        base_hp=1000.0,
        sub_hp_pct=10.0,
        disc_main={"hp_flat": 200.0},
        sub_hp_flat=100.0,
    )
    assert calculate_panel(inputs)["hp"] == pytest.approx(1400.0)


def test_weapon_base_atk_joins_atk_before_percent() -> None:
    inputs = PanelInputs(base_atk=1000.0, weapon_base_atk=500.0, sub_atk_pct=20.0)
    assert calculate_panel(inputs)["atk"] == pytest.approx(1800.0)


def test_weapon_base_def_only_affects_def() -> None:
    inputs = PanelInputs(base_atk=1000.0, weapon_base_def=500.0, sub_atk_pct=20.0)
    result = calculate_panel(inputs)
    assert result["atk"] == pytest.approx(1200.0)
    assert result["def"] == pytest.approx(1100.0)


def test_ratio_stats_scale_base_by_percent() -> None:
    inputs = PanelInputs(
        base_impact=100.0,
        base_anomaly_ctrl=100.0,
        base_energy_regen=1.0,
        set_impact_pct=20.0,
        set_anomaly_ctrl_pct=30.0,
        set_energy_pct=50.0,
    )
    result = calculate_panel(inputs)
    assert result["impact"] == pytest.approx(120.0)
    assert result["anomaly_ctrl"] == pytest.approx(130.0)
    assert result["energy_regen"] == pytest.approx(1.5)


def test_weapon_substat_flat_kinds_are_not_treated_as_percent() -> None:
    inputs = PanelInputs(
        base_anomaly_mastery=0.0,
        weapon_sub_type="anomaly_mastery",
        weapon_sub_value=90.0,
    )
    assert calculate_panel(inputs)["anomaly_mastery"] == pytest.approx(90.0)


def test_weapon_substat_pct_kinds_are_not_treated_as_flat() -> None:
    inputs = PanelInputs(base_cd=50.0, weapon_sub_type="cd", weapon_sub_value=48.0)
    assert calculate_panel(inputs)["cd"] == pytest.approx(98.0)


def test_unknown_weapon_substat_contributes_nothing() -> None:
    inputs = PanelInputs(base_cd=50.0, weapon_sub_type="—", weapon_sub_value=48.0)
    assert calculate_panel(inputs)["cd"] == pytest.approx(50.0)


def test_default_inputs_are_all_zero_bonuses() -> None:
    result = calculate_panel(PanelInputs())
    assert result["hp"] == pytest.approx(8000.0)
    assert result["atk"] == pytest.approx(1000.0)
    assert result["def"] == pytest.approx(600.0)
    assert result["dmg"] == pytest.approx(0.0)


def test_rupture_mode_calculates_penetration_force_from_final_hp_and_atk() -> None:
    inputs = PanelInputs(
        mode="rupture",
        base_hp=1000.0,
        base_atk=500.0,
        disc_main={"hp_pct": 20.0, "atk_pct": 10.0},
    )

    result = calculate_panel(inputs)

    assert result["penforce"] == pytest.approx(0.3 * result["atk"] + 0.1 * result["hp"])


def test_armorer_mode_calculates_actual_crit_and_fixed_blast_damage() -> None:
    inputs = PanelInputs(
        mode="armorer",
        base_cr=20.0,
        base_cd=50.0,
        set_cr=8.0,
        set_dmg=37.0,
        weapon_sub_type="cd",
        weapon_sub_value=48.0,
    )

    result = calculate_panel(inputs)

    assert result["actual_cr"] == pytest.approx(result["cd"] * 0.35 + result["cr"])
    assert result["armorer_blast_dmg"] == pytest.approx(150.0)
    assert result["dmg"] == pytest.approx(37.0)
    assert "armorer_blast_dmg" not in calculate_panel(PanelInputs())


def test_unknown_panel_mode_fails_explicitly() -> None:
    with pytest.raises(ValueError, match="Unsupported panel mode"):
        calculate_panel(PanelInputs(mode="unknown"))


@pytest.mark.parametrize("ident", sorted(option.id for option in SET_OPTIONS))
def test_every_set_option_reaches_the_accumulator(ident: str) -> None:
    """每条二件套都要真的进到累加器，而不只是出现在下拉框里。

    条目缺失或 `to` 写错都不会报错——`find_option` 找不到就跳过，用户只会看到
    「这个效果选不到」。因此逐条断言它加到了哪个键、加了多少。
    """
    option = find_option(SET_OPTIONS, ident)
    assert option is not None

    result = calculate_selection(PanelSelection(sets=(ident, "", "")), _ZERO_BASE)

    assert result["sums"][option.to] == pytest.approx(option.value)


def test_set_penetration_rate_lands_on_the_penetration_rate_row() -> None:
    """回归：二件套「穿透率 +8%」曾经整条缺失，下拉框里选不到，且没有任何报错。

    `pr` 是纯加法行，故基础值与二件套数值直接相加。
    """
    assert find_option(SET_OPTIONS, "pr_8") is not None

    base = {**_ZERO_BASE, "pr": 4.0}
    result = calculate_selection(PanelSelection(sets=("pr_8", "", "")), base)

    assert result["totals"]["pr"] == pytest.approx(12.0)


@pytest.mark.parametrize(
    "value,as_percent,expected",
    [
        (7673.0, False, "7,673"),
        (101.52, False, "101.52"),
        (1.2, False, "1.2"),
        (48.2, True, "48.2%"),
    ],
)
def test_fmt(value: float, as_percent: bool, expected: str) -> None:
    assert _fmt(value, as_percent) == expected
