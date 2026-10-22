"""配装对比（音擎 / 主词条 / 两档门槛）的测试。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend" / "src"))

from zzz_panel.core import options as option_table  # noqa: E402
from zzz_panel.schemas.panel import (  # noqa: E402
    BaseStatsIn,
    CoreIn,
    DiscMainIn,
    PanelRequest,
    SetsIn,
    WeaponIn,
    WeaponSubIn,
)
from zzz_panel.services.compare_service import (  # noqa: E402
    MAIN_STAT_EXCLUDES,
    compare_main_stats,
    compare_weapons,
    tier_curve,
)


def _request(**overrides) -> PanelRequest:
    payload = {
        "base": BaseStatsIn(hp=8000.0, atk=1000.0, def_=600.0, impact=90.0, cr=5.0, cd=50.0),
        "weapon": WeaponIn(
            base_kind="atk",
            base_value=713.0,
            substat=WeaponSubIn(label="暴击率", value=24.0, kind="pct", target="cr"),
        ),
        "core": CoreIn(core1="cr", core2="atk_base"),
        "disc_main": DiscMainIn(disc4="cr_24", disc5="pr_24", disc6="atk_pct_30"),
        "sub_stats": {"cr": 13, "cd": 16, "atk_pct": 16, "atk_flat": 5, "pen_val": 4},
        "sets": SetsIn(),
    }
    payload.update(overrides)
    return PanelRequest(**payload)


# ------------------------------------------------------------------ 音擎对比


def test_weapon_comparison_is_sorted_by_damage() -> None:
    """音擎对比按伤害降序。"""
    candidates = [
        {
            "id": "ep-a",
            "name": "甲",
            "grade": "S",
            "base": {"kind": "atk", "value": 713.0},
            "substat": {"label": "暴击率", "value": 24.0, "kind": "pct", "to": "cr"},
        },
        {
            "id": "ep-b",
            "name": "乙",
            "grade": "A",
            "base": {"kind": "atk", "value": 600.0},
            "substat": {"label": "暴击伤害", "value": 48.0, "kind": "pct", "to": "cd"},
        },
    ]
    results = compare_weapons(_request(), candidates)
    assert len(results) == 2
    assert results[0]["damage"] >= results[1]["damage"]


def test_weapon_comparison_distinguishes_substats() -> None:
    """两把音擎的副词条不同 → 伤害不同。"""
    candidates = [
        {
            "id": "ep-a",
            "name": "甲",
            "grade": "S",
            "base": {"kind": "atk", "value": 713.0},
            "substat": {"label": "暴击率", "value": 24.0, "kind": "pct", "to": "cr"},
        },
        {
            "id": "ep-b",
            "name": "乙",
            "grade": "S",
            "base": {"kind": "atk", "value": 713.0},
            "substat": {"label": "暴击伤害", "value": 48.0, "kind": "pct", "to": "cd"},
        },
    ]
    results = compare_weapons(_request(), candidates)
    assert results[0]["damage"] != pytest.approx(results[1]["damage"])


# ------------------------------------------------------------------ 主词条取舍


def test_main_stat_comparison_covers_every_option() -> None:
    """4 号位每个候选主词条都参与比较，并按伤害降序。"""
    results = compare_main_stats(_request(), slot="disc4")
    assert len(results) == len(option_table.DISC4_OPTIONS)
    damages = [item["damage"] for item in results]
    assert damages == sorted(damages, reverse=True)


def test_main_stat_excludes_are_the_single_source() -> None:
    """主词条排除表来自 core/options.py（前端同源）。"""
    assert MAIN_STAT_EXCLUDES["cr_24"] == "cr"
    assert MAIN_STAT_EXCLUDES["atk_pct_30"] == "atk_pct"
    assert MAIN_STAT_EXCLUDES["pr_24"] is None


def test_main_stat_choice_reallocates_excluded_substats() -> None:
    """换主词条会联动重排副词条：选了排除暴击率的主词条，暴击率条数会下降。"""
    results = compare_main_stats(_request(), slot="disc4")
    by_id = {item["optionId"]: item for item in results}
    # 4 号位选「暴击伤害」会排除暴击伤害副词条 -> 它的条数应低于原值
    cd_item = by_id["cd_48"]
    assert cd_item["subStats"]["cd"] < _request().sub_stats["cd"]
    assert cd_item["excluded"] == "暴击伤害"


def test_main_stat_comparison_changes_the_damage() -> None:
    """不同主词条给出不同伤害（否则取舍无从谈起）。"""
    results = compare_main_stats(_request(), slot="disc4")
    assert results[0]["damage"] != pytest.approx(results[-1]["damage"])


# ------------------------------------------------------------------ 两档门槛


def test_tier_curve_starts_at_full_and_declines() -> None:
    """门槛曲线从满配开始，条数递减、伤害递减。"""
    curve = tier_curve(_request(), steps=4)
    assert curve[0]["count"] == sum(_request().sub_stats.values())
    assert curve[0]["ratio"] == pytest.approx(1.0)
    for earlier, later in zip(curve, curve[1:]):
        assert later["count"] < earlier["count"]
        assert later["damage"] < earlier["damage"]
        assert later["ratio"] < earlier["ratio"]
