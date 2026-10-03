"""数值格式化。

规则逐条对齐 ``frontend/src/utils/fmt.ts`` 的 ``fmt``：

1. 先用 ``round(value, 10)`` 消化浮点误差；
2. 与四舍五入后的整数差小于 1e-7 时，按**千分位**整数输出；
3. 否则保留两位小数。

第 3 步要求前后端格式化结果一致，``tests/test_fmt_parity.py`` 以
``frontend/legacy/scripts/calculator.js`` 为共同基准逐值比对。

注意：旧的 ``cli._fmt`` 不带千分位，与前端不一致，本模块取代它。
"""

from __future__ import annotations

_EPSILON = 1e-7


def fmt(value: float) -> str:
    """按 legacy 规则格式化数值。"""
    fixed = round(float(value), 10)
    nearest = round(fixed)
    if abs(fixed - nearest) < _EPSILON:
        return f"{nearest:,d}"
    return f"{round(fixed, 2):.2f}".rstrip("0").rstrip(".") or "0"


def fmt_pct(value: float) -> str:
    """百分比数值，追加 ``%``。"""
    return f"{fmt(value)}%"
