"""预设数据的加载与校验。

- ``loader``     读取 ``data/*.json``，按 mtime 缓存，失败统一抛 ``PresetLoadError``
- ``validate``   跨字段语义校验，规则来源见 ``docs/data-schema.md``
- ``attributes`` 属性/评级取值校验与**特殊属性判定**（人数 == 1）
"""

from .attributes import (
    AGENT_ATTRIBUTES,
    AGENT_GRADES,
    attribute_counts,
    is_special_attribute,
    special_agent_attributes,
)
from .loader import PresetLoadError, load_agents, load_weapons
from .validate import AGENT_ROLE_TAGS, PresetValidationError, validate_agents, validate_weapons

__all__ = [
    "AGENT_ATTRIBUTES",
    "AGENT_GRADES",
    "AGENT_ROLE_TAGS",
    "PresetLoadError",
    "PresetValidationError",
    "attribute_counts",
    "is_special_attribute",
    "load_agents",
    "load_weapons",
    "special_agent_attributes",
    "validate_agents",
    "validate_weapons",
]