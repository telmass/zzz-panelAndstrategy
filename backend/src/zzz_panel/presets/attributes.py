"""代理人属性（属性类型）与评级的取值校验，以及**特殊属性判定**。

两个概念必须分开：

- ``attribute`` 是官网页面显示的属性类型，来自 WIKI 的
  ``role_base_info.role_attribute``（英文 slug），中文名由抓取脚本的
  ``ATTRIBUTE_LABELS`` 翻译后写进 ``data/agent-presets.json``。
  这里只做**白名单校验**，不重复维护 slug 表——slug→中文的唯一真实源在
  ``.github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py``，
  抄一份进来只会在新代理人到来时变成两份互相矛盾的映射。

- **特殊属性**不是「官方新出的属性」，而是一个纯粹由当前数据集推导出的结论：
  **该属性当前只有一名代理人持有**（人数 == 1）。

  刻意不写成「烈霜/玄墨/凛刃/流明」这样的硬编码名单：那样一旦官方再出
  一个单人属性就得改代码，而规则本身与具体是哪些属性无关。
  同样刻意不加「属性名不在常规五项内」这类附加条件——按需求只数人数。

  判定随数据变化：某个属性一旦被第二名代理人持有，它就不再是特殊属性。
  因此调用方不应缓存结果，每次按当前 ``agents`` 重算。
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from ..schemas.presets import AgentPreset

#: 属性类型全集，用于校验 ``attribute``。与前端 ``AGENT_ATTRIBUTES`` 同源。
#:
#: 官方对 ``electric`` 的写法是**电**（社区口语常作「雷」），照抄页面。
AGENT_ATTRIBUTES = frozenset(
    {"火", "冰", "电", "以太", "物理", "烈霜", "玄墨", "凛刃", "风", "流明"}
)

#: 官方评级全集，用于校验 ``grade``。
AGENT_GRADES = frozenset({"S", "A"})


def attribute_counts(agents: Iterable[AgentPreset]) -> dict[str, int]:
    """每个属性当前的持有人数。"""
    return dict(Counter(agent.attribute for agent in agents))


def special_agent_attributes(agents: Iterable[AgentPreset]) -> frozenset[str]:
    """返回当前**仅有一名代理人持有**的属性，即特殊属性。

    规则只有一条：人数为 1。人数为 2 及以上（哪怕只有两人）都不是特殊属性。
    """
    return frozenset(key for key, count in attribute_counts(agents).items() if count == 1)


def is_special_attribute(attribute: str, agents: Iterable[AgentPreset]) -> bool:
    """单个属性是否为特殊属性。语义与 :func:`special_agent_attributes` 一致。"""
    return attribute_counts(agents).get(attribute, 0) == 1


__all__ = [
    "AGENT_ATTRIBUTES",
    "AGENT_GRADES",
    "attribute_counts",
    "is_special_attribute",
    "special_agent_attributes",
]