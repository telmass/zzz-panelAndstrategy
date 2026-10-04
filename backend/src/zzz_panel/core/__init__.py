"""纯计算层：零 IO、零 Web 框架依赖。

本层是面板规则的唯一真源，供 API 与 CLI 共同调用：两者都经 ``panel.calculate_panel``
与 ``panel.calculate_selection`` 落到同一份公式上。

调用方一律直接 import 子模块（``from .panel import calculate_panel``），不从这里取。
"""
