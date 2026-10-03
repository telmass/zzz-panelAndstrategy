"""前后端格式化一致性（第 3 步验收项 15）。

以 legacy 参照实现的 ``fmt`` 为共同基准：本文件用 node **真正执行** 它的实现
（由 ``_fmt_driver.cjs`` 从 calculator.js 中提取函数体），再与 ``core.fmt.fmt``
逐值比对。因此这不是「照着抄一遍」，而是跨语言的实际对拍。

参照实现在 ``frontend/tests/fixtures/legacy-calculator/``，第 5 步从
``frontend/legacy/`` 原样搬来，**只读**：改了它对拍就变成自己跟自己比。

只有 node 不可用才跳过。基准文件缺失或无法执行一律**失败**——静默 skip 会让
这道护栏变成假绿灯，是比红灯更糟的失效方式。
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from zzz_panel.core.fmt import fmt

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parents[1]
LEGACY_JS = (
    REPO_ROOT / "frontend" / "tests" / "fixtures" / "legacy-calculator" / "scripts" / "calculator.js"
)
DRIVER = TESTS_DIR / "_fmt_driver.cjs"

# 覆盖整数 / 千分位 / 小数 / 尾零 / 负数 / 浮点噪声 / 极值
VALUES = [
    0.0, 1.0, -1.0, 5.0, 50.0, 100.0, 600.0, 784.0, 10200.0, 11544.0,
    1234567.0, 999999.0, 1000000.0,
    1.2, 1.44, 4.8, 48.2, 48.8, 101.52, 111.6, 2542.9, 3073.93, 1413.7,
    0.1, 0.01, 0.001, 2.5, 3.5, -2542.9, -0.3,
    0.1 + 0.2, 1896.4700000000003, 1188.0,
]


def _legacy_fmt(values: list[float]) -> list[str]:
    # 基准被挪动或误删时必须炸，不能降级为 skip。
    assert LEGACY_JS.is_file(), f"legacy fmt 基准不存在：{LEGACY_JS}"
    assert DRIVER.is_file(), f"node 驱动脚本不存在：{DRIVER}"

    result = subprocess.run(
        ["node", str(DRIVER), str(LEGACY_JS), json.dumps(values)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 0, f"无法执行 legacy fmt：{result.stderr.strip()}"
    return json.loads(result.stdout)


@pytest.mark.skipif(shutil.which("node") is None, reason="未安装 node，无法执行 legacy 的 fmt")
def test_fmt_matches_legacy_for_all_values() -> None:
    """Python 的 fmt 与 legacy 的 fmt 对同一组数值产出完全相同的字符串。"""
    expected = _legacy_fmt(VALUES)

    mismatches = [
        (value, want, fmt(value))
        for value, want in zip(VALUES, expected)
        if fmt(value) != want
    ]
    assert not mismatches, "以下数值与 legacy 不一致（值, legacy, Python）：" + repr(mismatches)


@pytest.mark.skipif(shutil.which("node") is None, reason="未安装 node，无法执行 legacy 的 fmt")
def test_fmt_uses_thousands_separator() -> None:
    """回归护栏：旧 cli._fmt 不带千分位，与前端不一致，本函数必须带。"""
    assert fmt(11336.0) == "11,336"
    assert fmt(7673.0) == "7,673"
