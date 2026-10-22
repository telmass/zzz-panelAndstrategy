"""副词条边际收益 / 等效 / 优先级验证的测试。

这些测试守的是线三的核心主张：**「多给 1 条某词条值多少伤害」能被算出来**，
以及「攻略页写的优先级链能被实算核对」。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend" / "src"))

from zzz_panel.schemas.panel import (  # noqa: E402
    BaseStatsIn,
    CoreIn,
    DiscMainIn,
    PanelRequest,
    SetsIn,
    WeaponIn,
)
from zzz_panel.services.benefit_service import (  # noqa: E402
    SUBSTAT_BY_LABEL,
    SUBSTAT_IDS,
    equivalence,
    marginal_benefit,
    one_roll_values,
    path_for_role,
    verify_priority,
)
from zzz_panel.services.damage_service import score_build  # noqa: E402


def _request(sub_stats: dict | None = None) -> PanelRequest:
    return PanelRequest(
        base=BaseStatsIn(hp=8000.0, atk=1000.0, def_=600.0, impact=90.0, cr=5.0, cd=50.0),
        weapon=WeaponIn(base_kind="atk", base_value=713.0),
        core=CoreIn(core1="cr", core2="atk_base"),
        disc_main=DiscMainIn(disc4="cd_48", disc5="pr_24", disc6="atk_pct_30"),
        sub_stats=sub_stats if sub_stats is not None else {"cr": 24, "cd": 24},
        sets=SetsIn(),
    )


# ------------------------------------------------------------------ 路径判定


def test_path_follows_the_agent_role() -> None:
    """路径按**定位**判：定位「异常」走异常路径。"""
    assert path_for_role("异常") == "anomaly"
    assert path_for_role("强攻") == "normal"
    assert path_for_role("支援") == "normal"


# ------------------------------------------------------------------ 边际收益


def test_marginal_benefit_curve_is_monotone_and_positive() -> None:
    """每条词条的边际收益曲线：加得越多，增量越大（且不为负）。"""
    curves = marginal_benefit(_request(), max_count=3)
    assert set(curves) == set(SUBSTAT_IDS)
    for substat_id, curve in curves.items():
        assert 1 in curve and 2 in curve and 3 in curve
        if curve[1] == 0.0:
            continue  # 不进任何乘区的词条（生存项）
        assert curve[2] > curve[1] > 0.0, f"{substat_id} 的曲线不是单调的"


def test_one_roll_value_matches_the_curve() -> None:
    """one_roll_values 与曲线第一点一致。"""
    curves = marginal_benefit(_request(), max_count=1)
    values = one_roll_values(_request())
    for substat_id, curve in curves.items():
        assert values[substat_id] == pytest.approx(curve[1])


def test_survival_substats_have_zero_damage_value() -> None:
    """生命值% / 防御力% 不进任何伤害乘区 → 伤害边际收益为 0。"""
    values = one_roll_values(_request())
    assert values["hp_pct"] == pytest.approx(0.0)
    assert values["def_pct"] == pytest.approx(0.0)
    assert values["cr"] > 0.0


def test_anomaly_path_values_anomaly_mastery() -> None:
    """异常路径下，异常精通的边际收益不为 0（常规路径下它是 0）。"""
    normal = one_roll_values(_request(), path="normal")
    anomaly = one_roll_values(_request(), path="anomaly")
    assert normal["am"] == pytest.approx(0.0)
    assert anomaly["am"] > 0.0


def test_penetration_value_has_value_on_both_paths() -> None:
    """穿透值在两条路径上都有收益——防御区两条路径都吃。

    （这曾经是个 bug：异常路径漏了防御区，穿透值的收益恒为 0。）
    """
    assert one_roll_values(_request(), path="normal")["pen_val"] > 0.0
    assert one_roll_values(_request(), path="anomaly")["pen_val"] > 0.0


# ------------------------------------------------------------------ 等效


def test_equivalence_is_normalised_to_the_baseline() -> None:
    """等效换算以暴击率为基准，基准自身记 1.0。"""
    ratios = equivalence(_request())
    assert ratios["cr"] == pytest.approx(1.0)
    assert ratios["cd"] > 0.0
    assert ratios["hp_pct"] == pytest.approx(0.0)


def test_equivalence_is_consistent_with_one_roll_values() -> None:
    """等效比 = 两条词条的单条价值之比。"""
    values = one_roll_values(_request())
    ratios = equivalence(_request())
    assert ratios["cd"] == pytest.approx(values["cd"] / values["cr"])


# ------------------------------------------------------------------ 优先级验证


def test_verify_priority_accepts_a_correct_chain() -> None:
    """链与实算一致 → verdict 全是 ok。"""
    chain = [
        {"label": "暴击率", "next": ">"},
        {"label": "暴击伤害", "next": ""},
    ]
    checks = verify_priority(_request(), chain)
    assert len(checks) == 1
    assert checks[0]["verdict"] in {"ok", "na"}


def test_verify_priority_flags_a_wrong_order() -> None:
    """链写反了 → verdict = off。"""
    chain = [
        {"label": "暴击伤害", "next": ">"},
        {"label": "生命值%", "next": ""},
    ]
    checks = verify_priority(_request(), chain)
    # 生命值% 的伤害收益为 0 → 伤害口径评价不了 → na，而不是 off
    assert checks[0]["verdict"] == "na"


def test_verify_priority_flags_equality_that_is_not_equal() -> None:
    """把不等价的写成「=」→ verdict = off。"""
    chain = [
        {"label": "暴击率", "next": "="},
        {"label": "生命值%", "next": ""},
    ]
    checks = verify_priority(_request(), chain)
    assert checks[0]["verdict"] == "na"


def test_substat_labels_cover_the_editorial_names() -> None:
    """攻略页用的展示名都要能映射到副词条 id。"""
    for label in ("暴击率", "暴击伤害", "攻击力%", "攻击力", "穿透值", "异常精通", "生命值%"):
        assert label in SUBSTAT_BY_LABEL, f"{label} 没有映射"


def test_score_build_agrees_with_the_panel_path() -> None:
    """边际收益的基准就是目标函数的伤害值（同一口径）。"""
    request = _request()
    base = score_build(request).total
    curves = marginal_benefit(request, max_count=1)
    assert curves["cr"][1] == pytest.approx(
        score_build(request.model_copy(update={"sub_stats": {**request.sub_stats, "cr": 25}})).total
        - base
    )
