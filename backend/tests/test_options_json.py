"""``data/options.json`` 的防漂移测试（第 4 步第 20 条）。

规则表的唯一真实源是 ``core/options.py`` 与 ``core/constants.py``，
``data/options.json`` 是它们的派生产物。改了 Python 侧却忘了跑
``python tools/sync_presets.py --options`` 时，本测试失败。
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
OPTIONS_JSON = REPO_ROOT / "data" / "options.json"

sys.path.insert(0, str(REPO_ROOT / "tools"))
sync_presets = importlib.import_module("sync_presets")

TABLES = [
    ("coreOptions", "CORE_OPTIONS"),
    ("disc4Options", "DISC4_OPTIONS"),
    ("disc5Options", "DISC5_OPTIONS"),
    ("disc6Options", "DISC6_OPTIONS"),
    ("setOptions", "SET_OPTIONS"),
    ("subStats", "SUB_STATS"),
]


@pytest.fixture(scope="module")
def on_disk() -> dict:
    assert OPTIONS_JSON.is_file(), (
        f"缺少 {OPTIONS_JSON.name}，运行 python tools/sync_presets.py --options 生成"
    )
    return json.loads(OPTIONS_JSON.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def from_python() -> dict:
    return sync_presets.build_options()


def test_options_json_matches_python(on_disk: dict, from_python: dict) -> None:
    assert on_disk == from_python, (
        "data/options.json 与 core/ 规则表不一致，"
        "运行 python tools/sync_presets.py --options 重新生成"
    )


def test_generator_is_idempotent(from_python: dict) -> None:
    """连续生成两次必须字节一致，否则 --check 会一直报漂移。"""
    assert sync_presets.dump_json(from_python) == sync_presets.dump_json(
        sync_presets.build_options()
    )


def test_check_mode_detects_drift(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """改坏 JSON 后 --check 必须报漂移并返回非 0。"""
    monkeypatch.setattr(sync_presets, "OPTIONS_JSON", tmp_path / "options.json")
    assert sync_presets.run_options(check_only=True) == 1

    assert sync_presets.run_options(check_only=False) == 0
    assert sync_presets.run_options(check_only=True) == 0


def test_notice_marks_the_file_as_generated(on_disk: dict) -> None:
    """JSON 没有注释语法，靠 _generated 字段标明勿手改。"""
    assert "勿手改" in on_disk["_generated"]


@pytest.mark.parametrize(("json_key", "attr"), TABLES)
def test_every_table_is_present_and_typed(on_disk: dict, json_key: str, attr: str) -> None:
    options = importlib.import_module("zzz_panel.core.options")
    rows = on_disk[json_key]
    source = getattr(options, attr)
    assert len(rows) == len(source) > 0
    for row, option in zip(rows, source):
        assert row == {"id": option.id, "label": option.label, "value": option.value,
                       "kind": option.kind, "to": option.to}


def test_disc_fixed_stats_come_from_constants(on_disk: dict) -> None:
    constants = importlib.import_module("zzz_panel.core.constants")
    rows = on_disk["discFixedStats"]
    assert len(rows) == len(constants.DISC_FIXED_STATS) == 3
    for row, stat in zip(rows, constants.DISC_FIXED_STATS):
        assert row == {"slot": stat.slot, "label": stat.label, "value": stat.value,
                       "target": stat.target}
    # 明细文案里的「1号主词条」按 slot 取，槽位号不能变
    assert [row["slot"] for row in rows] == [1, 2, 3]