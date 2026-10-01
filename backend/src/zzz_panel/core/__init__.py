"""纯计算层：零 IO、零 Web 框架依赖。

本层是面板规则的唯一真源，供 API 与 CLI 共同调用。
"""

from .models import PanelInputs
from .panel import calculate_panel

__all__ = ["PanelInputs", "calculate_panel"]
