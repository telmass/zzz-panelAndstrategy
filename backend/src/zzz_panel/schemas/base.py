"""HTTP 契约的公共基类。

线格式统一为 camelCase（与前端 TypeScript 类型直接对应），Python 侧仍用
snake_case 字段名书写，避免 `def_`、`base_kind` 这类 Python 保留字/风格差异
渗进业务代码。`populate_by_name` 让测试与 Python 侧调用可以按字段名构造。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


__all__ = ["CamelModel"]