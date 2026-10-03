"""预设数据的加载与校验。

- ``loader``   读取 ``data/*.json``，按 mtime 缓存，失败统一抛 ``PresetLoadError``
- ``validate`` 跨字段语义校验，规则来源见 ``docs/data-schema.md``
"""

from .loader import PresetLoadError, load_agents, load_weapons
from .validate import AGENT_ROLE_TAGS, PresetValidationError, validate_agents, validate_weapons

__all__ = [
    "AGENT_ROLE_TAGS",
    "PresetLoadError",
    "PresetValidationError",
    "load_agents",
    "load_weapons",
    "validate_agents",
    "validate_weapons",
]