"""毕业面板脚本的**装备组**逻辑（第 4 步第 21 条）。

守的是一条容易被写错的规则：

    **6 件全来自同一套**（4 件套组 + 同一套的 2 件套组）时，实际生效的是
    **一组 2 件套效果 + 一个 4 件套效果**——同一套的 2 件套效果不会因为多穿
    两件而叠加。

脚本拿到的���「套装」而不是「效果」，所以它必须自己识别同套并把重复的
2 件套组并掉；不并掉就会多算一次 2 件套效果。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / ".github/skills/agent-strategy/scripts/calc_graduation_panel.py"


@pytest.fixture(scope="module")
def panel_script():
    spec = importlib.util.spec_from_file_location("calc_graduation_panel", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["calc_graduation_panel"] = module
    spec.loader.exec_module(module)
    return module


def _args(panel_script, **overrides):
    """造一份 argparse 结果（不真跑 main）。

    约定：空字符串 = 「没传，用默认」；``none`` = 「明确没有这一组」
    （2+2+2 时没有 4 件套组就传 ``none``）。
    """
    args = type("Args", (), {})()
    for key, value in overrides.items():
        setattr(args, key, value)
    return args


def test_same_set_in_four_and_two_groups_is_merged(panel_script) -> None:
    """4 件套组与 2 件套组是同一套时，重复的 2 件套组被并掉。"""
    discs = panel_script.load_all(
        REPO_ROOT / "data" / "catalog" / "drive-discs.json"
    )
    # 獠牙重金属 = ep-104，2 件套效果 dmg_10。
    args = _args(
        panel_script,
        set4_id="ep-104",
        set4_effect="dmg_10",
        set2_id="ep-104",
        set2_effect="dmg_10",
        set2b_id="none",
        set2b_effect="none",
        set2c_id="none",
        set2c_effect="none",
    )

    groups = panel_script.resolve_set_groups(args, discs)
    ids = [group["id"] for group in groups]

    assert ids == ["ep-104"], f"同套的 2 件套组没有被并掉：{ids}"
    # 4 件套组本身保留——它的 4 件套效果与 2 件套效果都生效。
    assert groups[0]["kind"] == "4"


def test_different_sets_keep_both_groups(panel_script) -> None:
    """不同的套不并——两组 2 件套效果都该生效。"""
    discs = panel_script.load_all(
        REPO_ROOT / "data" / "catalog" / "drive-discs.json"
    )
    args = _args(
        panel_script,
        set4_id="ep-1754",          # 沧浪行歌
        set4_effect="dmg_10",
        set2_id="ep-151",           # 激素朋克
        set2_effect="atk_pct_10",
        set2b_id="ep-152",          # 震星迪斯科
        set2b_effect="impact_pct_6",
        set2c_id="none",
        set2c_effect="none",
    )

    groups = panel_script.resolve_set_groups(args, discs)
    ids = [group["id"] for group in groups]

    assert ids == ["ep-1754", "ep-151", "ep-152"], ids


def test_two_piece_groups_alone_are_all_kept(panel_script) -> None:
    """2+2+2：三组 2 件套都在，没有 4 件套组。"""
    discs = panel_script.load_all(
        REPO_ROOT / "data" / "catalog" / "drive-discs.json"
    )
    args = _args(
        panel_script,
        set4_id="none",
        set4_effect="none",
        set2_id="ep-104",
        set2_effect="dmg_10",
        set2b_id="ep-151",
        set2b_effect="atk_pct_10",
        set2c_id="ep-152",
        set2c_effect="impact_pct_6",
    )

    groups = panel_script.resolve_set_groups(args, discs)

    assert [group["id"] for group in groups] == ["ep-104", "ep-151", "ep-152"]
    assert all(group["kind"] == "2" for group in groups)
