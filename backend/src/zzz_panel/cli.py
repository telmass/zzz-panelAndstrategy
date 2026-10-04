"""命令行入口（承自原仓库根目录 ``main.py`` 的打印块）。

用法：
    uv run zzz-panel-and-strategy
    python -m zzz_panel
"""

from __future__ import annotations

import sys

from .core.models import PanelInputs
from .core.panel import calculate_panel

EXAMPLE = PanelInputs(
    base_hp=7673.0,
    base_atk=888.0,
    base_def=612.0,
    base_cr=19.4,
    base_cd=50.0,
    base_pr=0.0,
    base_impact=93.0,
    base_anomaly_ctrl=94.0,
    base_energy_regen=1.2,
    base_anomaly_mastery=93.0,
    weapon_base_atk=713.0,
    weapon_sub_type="cd",
    weapon_sub_value=0.0,
    set_dmg=10.0,
    set_anomaly_ctrl_pct=8.0,
    disc_main={
        "hp_flat": 0.0,
        "atk_flat": 0.0,
        "def_flat": 0.0,
        "hp_pct": 0.0,
        "atk_pct": 0.0,
        "def_pct": 0.0,
        "cr": 0.0,
        "cd": 48.0,
        "impact_pct": 0.0,
        "anomaly_ctrl_pct": 0.0,
        "energy_pct": 0.0,
        "dmg_bonus": 0.0,
        "pen_rate": 0.0,
        "anomaly_mastery": 0.0,
        "pen_val": 0.0,
    },
    sub_cr=28.8,
    sub_cd=57.6,
)


def _fmt(value: float, as_percent: bool = False) -> str:
    if as_percent:
        return f"{value:.2f}%"
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.2f}"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    result = calculate_panel(EXAMPLE)
    print("面板计算结果（参考学习指南示例）")
    print(f"生命值：{_fmt(result['hp'])}")
    print(f"攻击力：{_fmt(result['atk'])}")
    print(f"防御力：{_fmt(result['def'])}")
    print(f"暴击率：{_fmt(result['cr'], as_percent=True)}")
    print(f"暴击伤害：{_fmt(result['cd'], as_percent=True)}")
    print(f"增伤：{_fmt(result['dmg'], as_percent=True)}")
    print(f"穿透率：{_fmt(result['pr'], as_percent=True)}")
    print(f"冲击力：{_fmt(result['impact'])}")
    print(f"异常掌控：{_fmt(result['anomaly_ctrl'])}")
    print(f"能量回复：{_fmt(result['energy_regen'])}")
    print(f"异常精通：{_fmt(result['anomaly_mastery'])}")
    print(f"穿透值：{_fmt(result['pen_value'])}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
