# 数据结构

本文描述**预设 JSON 与配装规则表**的字段定义与校验规则。
HTTP 接口的请求/响应结构见 **[api-reference.md](../reference/api-reference.md)**。

数据集的**路径**由 `data/manifest.json` 登记（见 [../data/README.md](../../data/README.md)），
本文只讲形状。

## 1. 数据文件总览

`data/` 下五个 JSON：四个是生成物，`catalog/agent-index.json` 是手工维护的规范 slug 表。

| 数据集 | 路径 | 内容 | 规模 | 源头 | 生成命令 |
| --- | --- | --- | --- | --- | --- |
| `agents` | `catalog/agents.json` | 代理人预设 | 61 条 | Skill 抓取脚本（联网读官方 Wiki） | 抓取脚本直接写 |
| `weapons` | `catalog/weapons.json` | 音擎预设 | 101 条 | 同上 | 同上 |
| `calculator-rules` | `rules/calculator-rules.json` | 配装规则表（7 张表） | 54 个条目 | `backend/src/zzz_panel/core/options.py` + `core/constants.py` | `sync_presets.py --options` |
| `drive-discs` | `catalog/drive-discs.json` | 驱动盘套装效果（2/4 件套） | 30 条 | Skill 抓取脚本（联网读官方 Wiki） | 抓取脚本直接写（另下载套装图标） |
| `agent-index` | `catalog/agent-index.json` | 中文名 / 英文名 → 规范 slug | 62 条（含 1 条未上线） | 手工维护 | 无 |

各文件的字段级说明见下文。数据管线与刷新流程见 [development.md](../guides/development.md) 第 6 节。

### 1.1 命名映射（`catalog/agent-index.json`）

```jsonc
[
  {
    "slug": "ye-shunguang",   // 唯一规范 slug：目录名、数据文件名、路由参数都用它
    "en": "Ye Shunguang",
    "cn_short": "叶瞬光",
    "cn_full": "叶瞬光"
  }
]
```

用途：

- `fix-agent` Skill 以它为准修正攻略页的 slug、数据文件名与图标路径；
- 攻略页目录名与 `strategyGuides.ts` 的 `slug` 必须与它一致；
- 新增代理人时先补映射，再建 `strategy/<slug>/`。

它不是抓取产物，**不要用 `refresh_*_presets.py` 覆盖**。由 gen_strategy_guides.py --check 与 test_strategy_data.py 守卫，
一致性检查方案见 [structure-review.md](../completeds/structure-review.md) P1-1。

## 2. 代理人预设

### 2.1 结构

```jsonc
{
  "id": "ep-1109",                 // 稳定 id，前端按它查表
  "name": "示例代理人",
  "attribute": "火",               // 10 个合法值之一，见 2.3
  "grade": "S",                    // S | A
  "roleTag": "强攻",               // 7 个合法值之一
  "panelMode": "standard",         // standard | rupture | fengyu
  "source": "https://baike.mihoyo.com/zzz/wiki/content/1109/detail",

  "base": {                        // 60 级基础面板，不含核心加成
    "hp": 7673, "atk": 888, "def": 612,
    "impact": 93, "cr": 19.4, "cd": 50,
    "ac": 94, "am": 93, "pr": 0, "er": 1.2
  },
  "baseExtra": {                   // 可选：命破代理人的专属基础属性
    "penforce": 93,                // 贯穿力
    "energyAccumulation": 0        // 闪能自动累积
  },
  "baseUnmodeled": [               // 可选：官方列出但计算器未建模的属性
    { "label": "某属性", "value": 12, "unit": "%" }
  ],

  "core": [                        // 满级核心技加成，展开后须恰好填满 2 个槽位
    {
      "optionId": "cd",            // 对应规则表 coreOptions[].id
      "optionCount": 2,            // 可选，等于 1 时省略
      "ranks": ["D", "E", "F"],     // 该加成覆盖的技能等级
      "label": "暴击伤害",
      "perRank": 9.6,              // 每级数值
      "totalValue": 28.8,          // 合计，须等于 perRank × ranks.length
      "unit": "%"
    }
  ]
}
```

### 2.2 关键点

**`base` 的 10 个键全部可缺失（`Optional`）。** 官方未提供的键**直接不写**——
「没写到的键」本身就是「官方没提供」这份事实。数据里**不再另存**
`unavailableBaseStats` 数组：同一件事存两份，就得靠校验器去证明它们没漂移。

「哪几项缺是合法的」由后端按规则判定（见 5.1）：

- **命破模式**缺 `pr` 与 `er` 合法——这两个位置被贯穿力 / 闪能自动累积取代；
- 其余模式十项必须齐全。

前端按同一条规则派生「官方未提供」的键（`useAgentPreset.ts` 的
`unavailableBaseKeys`），并据此决定要不要在载入提示里说明。

`base.def` 的 JSON 键名是 `def`（Python 侧字段名为 `def_`，带 `alias="def"`，
因为 `def` 是 Python 关键字）。

**`panelMode` 与 `roleTag` 是两个独立字段。** 不可从职业标签反推面板模式——
例如命破是职业标签，但并非命破标签的代理人一定是命破模式。

**`core[].optionCount`** 用一个已有选项重复 `N` 次来表达，
只在 `option.value × optionCount` **恰好等于** `totalValue` 时使用。

**`attribute` 与 `roleTag` 也是两个独立字段。** 属性类型不参与计算，
只用于展示与「特殊属性」判定（见 2.4）。

**`totalValue` 与 `unit` 保留在数据里**（虽然可由规则表推出）：接口响应与源
JSON **逐条等价**是本项目的一条硬性质——正因为它，前端才能删掉自己的数据副本。
冗余不会悄悄漂移：`presets/validate.py` 逐条核对
`每级数值 × 位次数 == 合计 == 选项值 × 槽位数`，任何一处对不上即加载失败。

### 2.3 属性与评级

`attribute` 与 `grade` 都直接来自官方 WIKI 页面 `role_base_info` 组件，
抓取脚本自动写入，无需人工填写。

**`attribute` 的 10 个合法值**（前端 `AGENT_ATTRIBUTES` / 后端 `AGENT_ATTRIBUTES`）：

| | | | | |
| --- | --- | --- | --- | --- |
| 火 | 冰 | 电 | 以太 | 物理 |
| 烈霜 | 玄墨 | 凛刃 | 风 | 流明 |

官方对 `electric` 的写法是**电**（社区口语常作「雷」），照抄页面。
`凛刃` 也不并入 `物理`——尽管页面自己称它是「更高阶的物理属性」。

**`grade`** 代理人口前只有 `S` 与 `A`（后端 `AGENT_GRADES`）。

### 2.4 特殊属性的判定规则

> **某个属性当前只有一名代理人持有（人数 == 1），即为特殊属性。**

规则只有这一条，不附加任何其他条件。后端实现
`backend/src/zzz_panel/presets/attributes.py` 的 `special_agent_attributes()`，
前端镜像 `frontend/src/composables/useAgentPreset.ts` 的 `specialAgentAttributes()`。

按当前 61 名代理人，特殊属性是 `烈霜`、`玄墨`、`凛刃`、`流明`（各 1 人）；
`风` 有 2 人，**不是**特殊属性——这正说明规则与「属性名新不新」无关。

结论随数据变化，因此**每次使用都按当前 `agents` 重算，不要缓存**。
代码里也不得写死上面这份名单：新属性登场时它会立刻过时。

## 3. 音擎预设

```jsonc
{
  "id": "ep-1107",
  "name": "示例音擎",
  "grade": "S",                   // S | A
  "roleTag": "强攻",
  "source": "https://baike.mihoyo.com/zzz/wiki/content/1107/detail",
  "base": {                        // 基础攻击或基础防御
    "kind": "atk",                 // atk 提供基础攻击力；def（锋御）提供基础防御力
    "value": 713
  },
  "substat": {                     // 固定副词条，必填
    "label": "暴击伤害",
    "value": 48,
    "kind": "pct",                 // pct | flat
    "to": "cd"                     // 累加器键名，见 calculation-rules.md
  }
}
```

`base` 是二元组。此前是三个字段（`baseKind` + `baseAttack` + `baseDefense`），
其中恒有一个是 0，消歧要靠 `baseKind`；二元组没有冗余。

## 4. 配装规则表（`rules/calculator-rules.json`）

由 `core/options.py` 与 `core/constants.py` **单向生成**，带 `_generated`
声明字段（JSON 没有注释语法）与 `schemaVersion`（形状版本）。**不要手工编辑。**

前端通过 `@data` 别名直接 import，由 `constants/calculatorOptions.ts` 转成
`RuleOption[]`。这是**唯一**的 `@data` 消费点。

### 4.1 七张表

| 表 | 条目数 | 用途 |
| --- | --- | --- |
| `coreOptions` | 12 | 核心加成，两个槽位 |
| `disc4Options` | 6 | 4 号主词条 |
| `disc5Options` | 5 | 5 号主词条 |
| `disc6Options` | 6 | 6 号主词条 |
| `subStats` | 10 | 副词条，按条数换算 |
| `setOptions` | 12 | 二件套效果，三组各选一个（含荆棘玫瑰的「防御力 +16%」） |
| `discFixedStats` | 3 | 1/2/3 号固定主词条（**恒定生效，不可选**） |

### 4.2 条目结构

```jsonc
{
  "id": "cr_24",                              // 稳定标识，前端与预设都引用它
  "name": "暴击率",                            // 规范名：只含词条本身
  "label": "暴击率 +24%",                      // 下拉框显示文案（含数值）
  "value": 24,                                // 数值，供计算使用
  "kind": "pct",                              // pct | flat | base
  "to": "cr"                                  // 累加器键名
}
```

| `kind` | 含义 | 生效方式 |
| --- | --- | --- |
| `pct` | 百分比 | 与基础值相乘前先除以 100 |
| `flat` | 固定值 | 与基础值相加 |
| `base` | 基础值 | 并入基础值，再参与百分比计算 |

**`name` 与 `label` 的分工**：`label` 是展示串，含数值且各表格式不统一
（「暴击伤害 +28.8%」「攻击力 30%」「小生命」四种写法并存）；`name` 是规范名，
只含词条本身。分开后，展示文案可以自由调整格式而不用改规范名；代理人预设里的
核心加成 `label`（Wiki 原始措辞）也可以与 `name` 比对，不一致时给出**告警**
（例：`ep-1791` 把「攻击力」写作「攻击力百分比」——措辞差异，不是数据错误）。

### 4.3 用 id 而非数组下标

这是**迁移期的关键修正**。旧实现用数组下标表达含义
（`CORE_OPTIONS[i]`、`DISC4_OPTIONS[i]`），导致前后端必须共享同一份数组顺序。
现在 id 写在数据里，前端读规则表 JSON、后端读 `options.py`，
各自独立演进。改选项表顺序不会再让对拍错位。

`backend/tests/test_options_json.py` 断言 JSON 与 Python 当前值一致——
改了 Python 忘了重新生成就会失败。

### 4.4 `discFixedStats` 的特殊性

```jsonc
"discFixedStats": [
  { "slot": 1, "name": "固定生命", "label": "固定生命", "value": 2200, "to": "hp_flat" },
  { "slot": 2, "name": "固定攻击", "label": "固定攻击", "value": 316,  "to": "atk_flat" },
  { "slot": 3, "name": "固定防御", "label": "固定防御", "value": 184,  "to": "def_flat" }
]
```

- **恒定生效**，不占用用户的下拉框选择
- 数组顺序必须与 `slot` 顺序一致（`test_options_json.py` 有断言）
- 字段名是 `to`（与其余六张表一致）。此前 Python 侧叫 `target`、前端手工翻译成
  `to`，现已统一，前端不再做那层翻译

### 4.5 副词条上限不在数据里

单条 36、总计 54 这两个上限是前端常量
（`SUB_STAT_LIMIT_PER_KEY` / `SUB_STAT_TOTAL_LIMIT`），
**不在规则表中**——后端对条数只做向下取整与归零，不设上限，
因此没有对应的表。这一点在
[requirements.md](../overview/requirements.md) 的已知限制中记录。

## 5. 校验的两层分工

| 层 | 位置 | 负责 |
| --- | --- | --- |
| 结构与类型 | `backend/src/zzz_panel/schemas/presets.py`（Pydantic） | 类型、必填项、`panelMode` / `base.kind` / `substat.kind` 枚举 |
| 语义 | `backend/src/zzz_panel/presets/validate.py` | 见下 |

`presets/loader.py` 把两层的失败统一转成 `PresetLoadError`，
路由返回 **503**——预设数据非法是「数据源坏了」，不是「服务器崩了」。

前端在 `main.ts` 里于 `mount` **之前** `await loadAll()`，
因此各 getter 可保持同步派生，不需要在使用点处理加载态。

### 5.1 语义校验规则

来源：参照实现的 `calculator.js` 与 `applyAgentPreset`，
改为**一次性全量校验，失败即拒绝整份数据**（旧实现是逐条丢弃坏数据）。

**通用**

- `id` 不重复

**代理人**

| 规则 | 说明 |
| --- | --- |
| `name` 非空 | |
| `attribute` 非空且属于 10 个合法值 | 火 / 冰 / 电 / 以太 / 物理 / 烈霜 / 玄墨 / 凛刃 / 风 / 流明 |
| `grade` 非空且属于 2 个合法值 | `S` / `A` |
| `roleTag` 非空且属于 7 个合法值 | 强攻 / 击破 / 异常 / 支援 / 防护 / 命破 / 锋御 |
| `base` 的键集合与面板模式匹配 | 命破模式可缺 `pr` / `er`；其余模式十项齐全；出现未知键即失败 |
| `baseExtra` 的键必须是 `penforce` / `energyAccumulation` | 防止拼写错误静默通过 |
| `panelMode` 为 `rupture` 时必须给出 `penforce` 与 `energyAccumulation` | 否则命破模式无法载入 |
| `core` 非空 | |
| `core` 展开后恰好填满 **2** 个槽位 | `sum(optionCount or 1) == 2` |
| 每项 `optionId` 必须存在于 `CORE_OPTIONS` | |
| `option.value × optionCount == totalValue` | 容差 `1e-7` |
| `perRank × len(ranks) == totalValue` | 容差 `1e-7`，且 `ranks` 非空 |

**音擎**

| 规则 | 说明 |
| --- | --- |
| `name` 非空 | |
| `roleTag` 非空且合法 | |
| `base.kind` 属于 `atk` / `def` | |
| `base.value` 必须为正 | 官方给出 0 是数据事实，但基础值不能没有 |
| `substat.kind` 属于 `pct` / `flat` | |
| `substat.to` 必须是已知累加器键 | 累加器必须有落点 |
| `substat.to` 不得与驱动盘 1/2/3 号固定主词条重复 | 那三条恒定生效 |

**告警级**（不失败，只提示）：核心加成的 `label` 与规则表 `name` 不一致。

### 5.2 刻意区别于旧实现

旧实现遇到坏数据是**逐条丢弃、继续用其余数据**。本实现是**全量校验、
整份拒绝**。理由：预设数据由脚本生成，出现坏数据意味着生成环节出了问题，
静默丢弃会让用户看到「少了几个代理人」却查不出原因。

### 5.3 已建模属性的例外：锐暴伤害

`锐暴伤害` **已完成建模**，数值固定 150%，仅在锋御最终面板显示，
不作为计算输入。抓取脚本为保持数据可追溯，仍会把该 Wiki 标签写入
`baseUnmodeled`；前端载入预设时通过 `MODELED_BASE_STAT_LABELS`
（`constants/calculatorOptions.ts`）将其过滤，因此它**不会**出现在
「官方还列有当前计算器尚未建模的属性」提示中。

结构校验仍覆盖全部条目，过滤只作用于提示文案。

## 6. 驱动盘套装效果（`catalog/drive-discs.json`）

只回答「这套驱动盘的 2 件套与 4 件套效果是什么」。主词条、副词条、
获取途径等栏目一概不收录。

```jsonc
[
  {
    "id": "ep-104",                // ep-<entry_page_id>，与 Wiki 详情页一一对应
    "name": "獠牙重金属",
    "source": "https://baike.mihoyo.com/zzz/wiki/content/104/detail?mhy_presentation_style=fullscreen",
    "setEffect2": "物理伤害+10%。",  // 二件套效果，Wiki 原文
    "setEffect4": "队伍中任意角色对敌人施加[强击]效果时，装备者对目标造成的伤害提升35%，持续12秒。",
    "image": "/images/discs/ep-104.webp",    // 套装图标，/images/… URL（文件落 frontend/public/images/discs/）
    "effect2": "dmg_10",          // 2 件套效果 → 规则表 setOptions 的 id；算不出来时为 null
    "effect2Note": "属性伤害"       // effect2 为 null 时说明原因；可算时缺省
   }
 ]
 ```

几个要点：

- **效果文本保持 Wiki 原文**。抓取脚本只剥 HTML 标签、折叠空白，
  不做任何数值化；Wiki 自身的全角「＋」（混沌爵士的「异常精通＋30点。」）
  也照抄，不静默改写。
- **一页是不是驱动盘页**，看它是否带 `driver_disk` 组件；2/4 件套文本
  取自**第一个表头含「二件套」的 `double_col_table`**（同一页还有一张
  「推荐角色」表，表头不同，不会误取）。
- `image` 是 **`/images/…` URL**（唯一图片根约定，见
  [directory-layout.md](../overview/directory-layout.md) 第 2.2 节），文件本体落在
  `frontend/public/images/discs/ep-<entry_page_id>.webp`，命名与 `images/agents`、
  `images/weapons` 的 `ep-<id>` 一致。
- **`effect2` 是 2 件套效果到规则表选项的映射**，由 `tools/link_disc_effects.py`
  建立、`frontend/tests/data-manifest.spec.ts` 守住。**30 套里 18 套可算、
  12 套算不出来**：
  - **属性伤害**（8 套）：面板**没有「属性伤害」这一行**——加一行会破坏三方
    对拍（参照实现的行集是固定的，夹具已冻结）；
  - **条件触发**（4 套）：如「[普通攻击]造成的伤害提升15%」，不是固定面板值。

  这两类写 `effect2: null` 并用 `effect2Note` 说明原因，UI 据此告诉用户
  「该套装的 2 件套效果不计入面板」。
- **没有校验层，计算器也未消费**：该文件不进 `presets/loader.py`、
  不进接口、不进 `_bundled_data.py`。前端在**构建期**通过 `@data` 别名读它
  （与规则表同一模式）。图标当前的消费者是
  攻略页（`strategy/<slug>/` 的驱动盘卡按 `/images/discs/<id>.webp` 取图）；
  计算器 UI 接入图标属待做（见 [requirements.md](../overview/requirements.md) 第 7 节）。
  重跑幂等——JSON 字节不变，图片仅在内容变化时才重写。

## 7. 攻略页的基础面板

`strategy/<slug>/data/<slug>.json` **不再携带 `basePanel`**。基础面板的唯一
真实源是代理人预设，攻略页由 `frontend/src/strategy/basePanel.ts` 从预设派生
（含命破的「贯穿力 / 闪能自动累积」与锋御的「锐能自动累积」文案替换）。

同一批数字曾在 61 份攻略 JSON 与预设数据里各存一份，已经发生过漂移（三名
代理人的属性名口径在两处不一致）。`backend/tests/test_strategy_data.py`
断言攻略 JSON 里不再有 `basePanel`，且 `meta.agentId` 必须对应一个已发布的预设。

## 8. 对拍夹具（冻结的参照实现）

`frontend/tests/fixtures/legacy-calculator/data/*.js` 定义
`window.AGENT_PRESETS` 与 `window.WEAPON_PRESETS`，是**三方对拍的参照实现**，
其输入必须是一个**不动点**。因此它已**冻结为快照**，不再由脚本生成
（原 `tools/sync_presets.py --to-legacy` / `--from-legacy` 模式已移除）。

守门换成 `backend/tests/test_legacy_fixture_snapshot.py`：断言夹具里用到的
代理人与音擎，与当前数据集在**语义上等值**（基础面板逐项、核心加成的选项与
每级数值、面板模式）。

保留原因：参照实现在顶层直接读取这两个全局量，删掉它三方对拍就跑不起来。
详见 [completeds/legacy-pages.md](../completeds/legacy-pages.md)。

## 9. 相关文档

- [api-reference.md](../reference/api-reference.md) —— HTTP 接口与响应结构
- [calculation-rules.md](calculation-rules.md) —— 各 `to` 键名的含义与公式
- [architecture.md](architecture.md) —— 为什么预设走接口、规则表走本地
- [ui-system.md](ui-system.md) —— 前端视觉体系与两道闸门
- [development.md](../guides/development.md) —— 数据管线与刷新流程
- [testing.md](../guides/testing.md) —— 漂移如何被守住
