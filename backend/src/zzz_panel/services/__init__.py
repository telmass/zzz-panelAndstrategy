"""用例编排层。

``panel_service.py`` 把「选了什么」组装成 ``core`` 的入参并返回 ``schemas``
定义的响应。它是 API 与 CLI 之间的公共前半段，因此「网页算的」与「命令行算的」
共用同一份 ``core/`` 公式。

注意口径：CLI 直接调 ``core.panel.calculate_panel``，网页走本层的
``calculate_selection``；两者最终都落到 ``core`` 的 ``_apply_totals`` 与
``calculate_mode_stats``，故结果一致，但入口函数并不相同。
"""
