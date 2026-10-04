"""预设数据的加载与校验。

- ``loader``     读取 ``data/*.json``，按 mtime 缓存，失败统一抛 ``PresetLoadError``
- ``validate``   跨字段语义校验，规则来源见 ``docs/data-schema.md``
- ``attributes`` 属性/评级取值校验与**特殊属性判定**（人数 == 1）

本包只做数据层，**不做 HTTP**。调用方一律直接 import 子模块
（``from .loader import load_agents``），不从这里取。
"""