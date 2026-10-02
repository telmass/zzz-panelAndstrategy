"""面板模式专属公式与固有属性。"""

from __future__ import annotations

FENGYU_BLAST_DMG = 150.0
_PANEL_MODES = frozenset({"standard", "rupture", "fengyu"})


def calculate_mode_stats(
    mode: str,
    *,
    total_hp: float,
    total_atk: float,
    total_cr: float,
    total_cd: float,
) -> dict[str, float]:
    """返回模式专属的最终面板属性；通用模式不添加专属字段。"""
    if mode not in _PANEL_MODES:
        raise ValueError(f"Unsupported panel mode: {mode}")

    if mode == "rupture":
        return {"penforce": 0.3 * total_atk + 0.1 * total_hp}
    if mode == "fengyu":
        return {
            "actual_cr": total_cd * 0.35 + total_cr,
            "fengyu_blast_dmg": FENGYU_BLAST_DMG,
        }
    return {}
