"""Pydantic 请求 / 响应模型。

与 ``core/`` 的 dataclass 解耦：``core/`` 保持框架无关，``schemas/`` 承担
入参校验与 OpenAPI 文档生成。字段需与 ``frontend/src/types/`` 一一对应。

- ``base.py``     共用的 ``CamelModel``（camelCase 线格式 + 按字段名构造）
- ``panel.py``    ``/api/health`` 与 ``/api/panel/calc`` 的模型
- ``presets.py``  ``/api/presets/*`` 的预设模型，同时被 ``presets/validate.py`` 复用
"""
