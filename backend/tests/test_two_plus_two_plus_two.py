"""2+2+2 装法的**计算语义**。

驱动盘不一定只有「4+2」——6 个槽位也可以是 **2+2+2**（三组 2 件套），
或 4+2+2。这三个用例把语义钉死：

1. **两份同效果的 2 件套都生效。** 月光骑士颂与摇摆爵士的 2 件套效果都是
   「能量自动回复 +20%」；它们是两套**不同**的套装，两份效果都该进面板。
2. **百分比是相加，不是叠乘。** 同一修正量的多个来源，百分比**相加**后一次性
   作用——这与游戏一致（「+20%」与「+20%」得到 +40%，不是 ×1.2×1.2）。
3. **组序不影响结果。** 槽位是集合语义，三组谁先谁后一样。

> 对照：**同一套装**的 2 件套效果不会因为多穿两件而叠加——那由
> ``calc_graduation_panel.py`` 的「同套并组」处理（见
> ``test_graduation_panel_groups.py``）。
"""

from __future__ import annotations

import pytest

from zzz_panel.schemas.panel import PanelRequest
from zzz_panel.services.panel_service import calculate

# 洛克茜 ep-2152：基础能量回复 1.2
BASE = {
    "hp": 8418,
    "atk": 666,
    "def": 641,
    "impact": 100,
    "cr": 5,
    "cd": 50,
    "ac": 110,
    "am": 63,
    "pr": 0,
    "er": 1.2,
}

# 绯月银棺 ep-2234：基础攻击 713，固定副词条「能量自动回复 +60%」
WEAPON = {
    "base_kind": "atk",
    "base_value": 713,
    "substat": {
        "label": "能量自动回复",
        "value": 60,
        "kind": "pct",
        "target": "er_pct",
        "to": "er_pct",
    },
}


def panel_for(sets: tuple[str, str, str]) -> dict:
    request = PanelRequest(
        base=BASE,
        weapon=WEAPON,
        core={"core1": "cr", "core2": "atk_base"},
        disc_main={"disc4": "cd_48", "disc5": "atk_pct_30", "disc6": "atk_pct_30"},
        sub_stats={"cr": 24, "atk_pct": 12, "cd": 11, "atk_flat": 5, "pen_val": 2},
        sets={"set0": sets[0], "set1": sets[1], "set2": sets[2]},
        mode="standard",
    )
    return calculate(request).totals


class TestTwoPlusTwoPlusTwo:
    def test_two_sets_with_the_same_effect_both_apply(self) -> None:
        """月光骑士颂 + 摇摆爵士：两份「能量回复 +20%」都生效。

        能量回复 = 1.2 × (1 + (60 + 20 + 20) / 100) = 2.4
        只有一份时 = 1.2 × (1 + (60 + 20) / 100) = 2.16
        """
        two = panel_for(("er_pct_20", "er_pct_20", ""))
        one = panel_for(("er_pct_20", "", ""))
        assert one["er"] == pytest.approx(2.16)
        assert two["er"] == pytest.approx(2.4)

    def test_percentages_add_rather_than_multiply(self) -> None:
        """同一修正量的多个来源，百分比**相加**后一次性作用。

        这是游戏的语义：「+20%」与「+20%」得到 +40%，不是 ×1.2×1.2。
        叠乘会得到 2.7648，与实际不符。
        """
        two = panel_for(("er_pct_20", "er_pct_20", ""))["er"]
        assert two == pytest.approx(2.4)
        assert two != pytest.approx(1.2 * 1.6 * 1.2 * 1.2)

    def test_group_order_does_not_matter(self) -> None:
        """组序不影响结果——槽位是集合语义。"""
        first = panel_for(("er_pct_20", "er_pct_20", "cr_8"))
        second = panel_for(("cr_8", "er_pct_20", "er_pct_20"))
        assert first == second

    def test_2plus2plus2_differs_from_4plus2_only_by_the_sets(self) -> None:
        """2+2+2 与 4+2 的差异只来自套装本身。"""
        four_plus_two = panel_for(("dmg_10", "er_pct_20", ""))
        two_plus_two_plus_two = panel_for(("er_pct_20", "er_pct_20", "cr_8"))

        # 攻击力 / 暴击伤害 / 穿透值不受这两组影响
        for key in ("atk", "cd", "pv"):
            assert four_plus_two[key] == two_plus_two_plus_two[key]
        # 暴击率：2+2+2 多了啄木鸟电音的 +8%
        assert two_plus_two_plus_two["cr"] - four_plus_two["cr"] == pytest.approx(8.0)
        # 能量回复：2+2+2 多一份 +20%
        assert two_plus_two_plus_two["er"] - four_plus_two["er"] == pytest.approx(0.24)
