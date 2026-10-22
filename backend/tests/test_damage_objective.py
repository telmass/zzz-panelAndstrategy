"""伤害目标函数的测试——「面板」能不能变成「可比的伤害」。

这一组测试守的是线三的核心主张：**用伤害引擎反推最优配装**。
如果目标函数只看面板不看配装，或者对不同配装给不出区分，那 A2 / D1-Wpn /
D1-Main 全都无从谈起。

编号 ``O1``~``O8`` 是本文件自己的编号（不属于规格第 6 节的 30 条契约）。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend" / "src"))

from zzz_panel.core.damage.targets import STANDARD_TARGET, to_params  # noqa: E402
from zzz_panel.schemas.panel import (  # noqa: E402
    BaseStatsIn,
    CoreIn,
    DiscMainIn,
    PanelRequest,
    SetsIn,
    WeaponIn,
    WeaponSubIn,
)
from zzz_panel.services.damage_service import compare_builds, score_build  # noqa: E402


def _request(
    atk: float = 1000.0,
    cr: float = 5.0,
    cd: float = 50.0,
    dmg: float = 0.0,
    pr: float = 0.0,
    pv: float = 0.0,
    disc4: str = "cr_24",
    disc5: str = "pr_24",
    disc6: str = "atk_pct_30",
    core1: str = "cr",
    core2: str = "atk_base",
    weapon_base: float = 0.0,
    weapon_substat: tuple[str, float, str] | None = ("cr", 24.0, "pct"),
    sub_stats: dict | None = None,
) -> PanelRequest:
    """构造一次面板请求（默认值取自官方算例的常见配置）。"""
    return PanelRequest(
        base=BaseStatsIn(hp=8000.0, atk=atk, def_=600.0, impact=90.0, cr=cr, cd=cd),
        weapon=WeaponIn(
            base_kind="atk",
            base_value=weapon_base,
            substat=(
                WeaponSubIn(
                    label=weapon_substat[0],
                    value=weapon_substat[1],
                    kind=weapon_substat[2],
                    target=weapon_substat[0],
                )
                if weapon_substat
                else None
            ),
        ),
        core=CoreIn(core1=core1, core2=core2),
        disc_main=DiscMainIn(disc4=disc4, disc5=disc5, disc6=disc6),
        sub_stats=sub_stats if sub_stats is not None else {"cr": 24, "cd": 24},
        sets=SetsIn(),
    )


# ------------------------------------------------------------------ O1~O2


def test_O1_score_is_reproducible() -> None:
    """O1：同一份配装，两次算出的伤害完全一致（目标函数必须是纯函数）。"""
    request = _request()
    first = score_build(request).total
    second = score_build(request).total
    assert first == pytest.approx(second)
    assert first > 0


def test_O2_higher_panel_never_scores_lower() -> None:
    """O2：面板更高 → 伤害不更低（单调性；伤害是面板的**函数**，不是别的）。"""
    low = score_build(_request(atk=1000.0)).total
    high = score_build(_request(atk=1200.0)).total
    assert high > low


# ------------------------------------------------------------------ O3~O4 配装敏感


def test_O3_score_distinguishes_substat_allocations() -> None:
    """O3：两套不同的副词条分配 → 伤害不同（目标函数真的在看配装，不只是面板）。"""
    crit_heavy = score_build(_request(sub_stats={"cr": 30, "cd": 24})).total
    cd_heavy = score_build(_request(sub_stats={"cr": 24, "cd": 30})).total
    assert crit_heavy != pytest.approx(cd_heavy)


def test_O4_score_distinguishes_weapons() -> None:
    """O4：不同音擎 → 伤害不同（这是「专武 vs 下位」对比的基础能力）。"""
    crit_weapon = score_build(
        _request(weapon_substat=("cr", 24.0, "pct"), weapon_base=713.0)
    ).total
    cd_weapon = score_build(
        _request(weapon_substat=("cd", 48.0, "pct"), weapon_base=713.0)
    ).total
    assert crit_weapon != pytest.approx(cd_weapon)


# ------------------------------------------------------------------ O5 主词条取舍


def _five_slot_score(damage_bonus_pct: float, disc5: str) -> float:
    """在给定增伤水平下，5 号位选「穿透率」还是「属性伤害」的得分。

    ``damage_bonus_pct`` 是**原有**增伤（不含 5 号位那一项）。
    """
    request = _request(
        dmg=damage_bonus_pct,
        disc5=disc5,
        sub_stats={"cr": 24, "cd": 24},
    )
    return score_build(request).total


def test_O5_main_stat_5_tradeoff_is_visible_in_the_panel_scope() -> None:
    """O5：5 号位「属性伤害 30%」与「穿透率 24%」的取舍在面板口径下可见。

    **面板口径的增伤只有 5 号位这一项**（F3 之后没有套装再提供属性伤害），
    所以增伤区只可能是 1.0 或 1.3——远低于官方阈值 199.17%。
    这条测试因此断言的是**面板口径下**的结论：
    属性伤害（1.3 × 0.4545）优于穿透率（1.0 × 0.5230）。

    官方的阈值判断是**局内**的（还含音擎被动、影画、4 件套、队伍的增伤），
    面板口径给不出那个结论——引擎层面的阈值由契约 C30 覆盖。
    """
    attribute = _five_slot_score(0.0, "dmg_30")
    penetration = _five_slot_score(0.0, "pr_24")
    assert attribute > penetration

    # 面板口径的增伤区上限：5 号位属性伤害 30% 是唯一的增伤来源
    result = score_build(_request(disc5="dmg_30", sub_stats={"cr": 24, "cd": 24}))
    assert result.zones["增伤区"] == pytest.approx(1.30)


# ------------------------------------------------------------------ O6~O7 基准目标


def test_O6_standard_target_matches_the_official_anchor() -> None:
    """O6：标准目标下，防御区就是官方的 0.4545（**不带穿透**的那一档）。"""
    result = score_build(_request(disc5="dmg_30"))
    assert result.zones["防御区"] == pytest.approx(0.4545, abs=1e-4)


def test_O7_weakness_and_resistance_attribute_change_the_score() -> None:
    """O7：打弱点属性比打抗性属性伤害高（抗性区 1.2 vs 0.8）。"""
    request = _request()
    weak = score_build(request, attribute_resistance=-0.2).total
    resist = score_build(request, attribute_resistance=0.2).total
    assert weak > resist


# ------------------------------------------------------------------ O8 排序


def test_O8_compare_builds_sorts_descending() -> None:
    """O8：比较函数按伤害得分**降序**返回（最优配装在第一个）。"""
    requests = [_request(atk=1000.0), _request(atk=1400.0), _request(atk=1200.0)]
    scored = compare_builds(requests)
    assert [score for _, score in scored] == sorted(
        [score for _, score in scored], reverse=True
    )
    assert scored[0][1] == pytest.approx(max(score for _, score in scored))


def test_standard_target_is_the_boss_anchor() -> None:
    """标准目标就是官方算例里的那个首领锚点。"""
    assert STANDARD_TARGET.id == "boss-60"
    assert STANDARD_TARGET.base_defense == 60.0
    params = to_params(STANDARD_TARGET)
    assert params.base_defense == 60.0
