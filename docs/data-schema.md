# 数据结构

本文描述**预设 JSON 与配装规则表**的字段定义与校验规则。
HTTP 接口的请求/响应结构见 **[api-reference.md](api-reference.md)**。

## 1. 数据文件总览

`data/` 下三个 JSON **全部是生成物**，不存在手写副本。

| 文件 | 内容 | 规模 | 源头 | 生成命令 |
| --- | --- | --- | --- | --- |
| `agent-presets.json` | 代理人预设 | 60 条 | Skill 抓取脚本（联网读官方 Wiki） | 抓取脚本直接写 |
| `weapon-presets.json` | 音擎预设 | 100 条 | 同上 | 同上 |
| `options.json` | 配装规则表（7 张表） | 378 行 | `backend/src/zzz_panel/core/options.py` + `core/constants.py` | `sync_presets.py --options` |

各文件的字段级说明见下文。数据管线与刷新流程见 [development.md](development.md) 第 6 节。

## 2. 代理人预设

### 2.1 结构

```jsonc
{
  "id": "ep-1109",                 // 稳定 id，前端按它查表
  "name": "示例代理人",
  "roleTag": "强攻",// 7 个合法值之一
  "panelMode": "standard",        // standard | rupture | fengyu
  "source": "https://baike.mihoyo.com/zzz/wiki/content/1109/detail",

  "base": {                       // 60 级基础面板，不含核心加成
    "hp": 7673, "atk": 888, "def": 612,
    "impact": 93, "cr": 19.4, "cd": 50,
    "ac": 94, "am": 93, "pr": 0, "er": 1.2
  },

  "additionalBaseStats": {// 可选：命破代理人的专属基础属性
    "penforce": 93,               // 贯穿力
    "energyAccumulation": 0       // 锐能自动累积
  },
  "unavailableBaseStats": ["pr"], // 可选：官方基础面板未提供的键
  "unmodeledBaseStats": [         // 可选：官方列出但计算器未建模的属性
    { "label": "某属性", "value": 12, "unit": "%" }
  ],

  "coreBonuses": [                // 满级核心技加成，展开后须恰好填满 2 个槽位
    {
      "optionId": "cd",           // 对应 options.json 的 coreOptions[].id
      "optionCount": 2,           // 可选，等于 1 时省略
      "ranks": ["D", "E", "F"],   // 该加成覆盖的技能等级
      "label": "暴击伤害",
      "perRankValue": 9.6,        // 每级数值
      "totalValue": 28.8,         // 合计，须等于 perRankValue × ranks.length
      "unit": "%"
    }
  ],

  "grade": "S"                    // 可选
}
```

### 2.2 关键点

**`base` 的 10 个键全部可缺失（`Optional`）。** 官方未提供的键为 `null`，
**同时**必须列入 `unavailableBaseStats`。两个条件缺一不可：

- 只留 `null` 不声明 → 前端把 `null` 当 0 写进面板，用户看到错误的 0且无提示
- 只声明不置 `null` → 语义校验报错

`base.def` 的 JSON 键名是 `def`（Python 侧字段名为 `def_`，带 `alias="def"`，
因为 `def` 是 Python 关键字）。

**`panelMode` 与 `roleTag` 是两个独立字段。** 不可从职业标签反推面板模式——
例如命破是职业标签，但并非命破标签的代理人一定是命破模式。

**`coreBonuses[].optionCount`** 用一个已有选项重复 `N` 次来表达，
只在 `option.value × optionCount` **恰好等于** `totalValue` 时使用。

## 3. 音擎预设

```jsonc
{
  "id": "ep-1107",
  "name": "示例音擎",
  "grade": "S",                   // S | A | B
  "roleTag": "强攻",
  "source": "https://baike.mihoyo.com/zzz/wiki/content/1107/detail",
  "baseKind": "atk",              // atk 提供基础攻击力；def（锋御）提供基础防御力
  "baseAttack": 713,
  "baseDefense": 0,
  "substat": {                    // 固定副词条，必填
    "label": "暴击伤害",
    "value": 48,
    "kind": "pct",                // pct | flat
    "to": "cd"                    // 累加器键名，见 calculation-rules.md
  }
}
```

`baseKind` 决定 `baseAttack` 与 `baseDefense` 哪个生效，二者互斥。

## 4. 配装规则表（`options.json`）

由 `core/options.py` 与 `core/constants.py` **单向生成**，带 `_generated`
声明字段（JSON 没有注释语法）。**不要手工编辑。**

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
| `setOptions` | 10 | 二件套效果，三组各选一个 |
| `discFixedStats` | 3 | 1/2/3 号固定主词条（**恒定生效，不可选**） |

### 4.2 条目结构

```jsonc
{
  "id": "cr_24",                              // 稳定标识，前端与预设都引用它
  "label": "暴击率 +24%",                     // 下拉框显示文案
  "value": 24,                                // 数值，供计算使用
  "kind": "pct",                              // pct | flat | base
  "to": "cr"// 累加器键名
}
```

| `kind` | 含义 | 生效方式 |
| --- | --- | --- |
| `pct` | 百分比 | 与基础值相乘前先除以 100 |
| `flat` | 固定值 | 与基础值相加 |
| `base` | 基础值 | 并入基础值，再参与百分比计算 |

### 4.3 用 id 而非数组下标

这是**迁移期的关键修正**。旧实现用数组下标表达含义
（`CORE_OPTIONS[i]`、`DISC4_OPTIONS[i]`），导致前后端必须共享同一份数组顺序。
现在 id 写在数据里，前端读 `options.json`、后端读 `options.py`，
各自独立演进。改选项表顺序不会再让对拍错位。

`backend/tests/test_options_json.py` 断言 JSON 与 Python 当前值一致——
改了 Python 忘了重新生成就会失败。

### 4.4 `discFixedStats` 的特殊性

```jsonc
"discFixedStats": [
  { "slot": 1, "label": "固定生命", "value": 2200, "target": "hp_flat" },
  { "slot": 2, "label": "固定攻击", "value": 316,  "target": "atk_flat" },
  { "slot": 3, "label": "固定防御", "value": 184,  "target": "def_flat" }
]
```

- **恒定生效**，不占用用户的下拉框选择
- 数组顺序必须与 `slot` 顺序一致（`test_options_json.py` 有断言）
- JSON 里字段名是 `target`，前端转成 `to` 以统一命名

### 4.5 副词条上限不在数据里

单条 36、总计 54 这两个上限是前端常量
（`SUB_STAT_LIMIT_PER_KEY` / `SUB_STAT_TOTAL_LIMIT`），
**不在 `options.json` 中**——后端对条数只做向下取整与归零，不设上限，
因此没有对应的表。这一点在
[requirements.md](requirements.md) 的已知限制中记录。

## 5. 校验的两层分工

| 层 | 位置 | 负责 |
| --- | --- | --- |
| 结构与类型 | `backend/src/zzz_panel/schemas/presets.py`（Pydantic） | 类型、必填项、`panelMode` / `baseKind` / `kind` 枚举 |
| 语义 | `backend/src/zzz_panel/presets/validate.py` | 见下 |

`presets/loader.py` 把两层的失败统一转成 `PresetLoadError`，
路由返回 **503**——预设数据非法是「数据源坏了」，不是「服务器崩了」。

前端在 `main.ts` 里于 `mount` **之前** `await loadAll()`，
因此各 getter 可保持同步派生，不需要在使用点处理加载态。

### 5.1 语义校验规则

来源：参照实现的 `calculator.js:47-58` 与 `applyAgentPreset`，
改为**一次性全量校验，失败即拒绝整份数据**（旧实现是逐条丢弃坏数据）。

**通用**

- `id` 不重复

**代理人**

| 规则 | 说明 |
| --- | --- |
| `name` 非空 | |
| `roleTag` 非空且属于 7 个合法值 | 强攻 / 击破 / 异常 / 支援 / 防护 / 命破 / 锋御 |
| `base` 中缺失的键必须列入 `unavailableBaseStats` | 否则前端会把缺值当 0 且无提示 |
| `unavailableBaseStats` 的每项必须是合法基础键名 | 防止拼写错误静默通过 |
| `panelMode` 为 `rupture` 时必须给出 `penforce` 与 `energyAccumulation` | 否则命破模式无法载入 |
| `coreBonuses` 非空 | |
| `coreBonuses` 展开后恰好填满 **2** 个槽位 | `sum(optionCount or 1) == 2` |
| 每项 `optionId` 必须存在于 `CORE_OPTIONS` | |
| `option.value × optionCount == totalValue` | 容差 `1e-7` |
| `perRankValue × len(ranks) == totalValue` | 容差 `1e-7`，且 `ranks` 非空 |

**音擎**

| 规则 | 说明 |
| --- | --- |
| `name` 非空 | |
| `roleTag` 非空且合法 | |
| `baseKind == "atk"` 则 `baseAttack != 0` | |
| `baseKind == "def"` 则 `baseDefense != 0` | |
| `substat.to` 非空 | 累加器必须有落点 |

### 5.2 刻意区别于旧实现

旧实现遇到坏数据是**逐条丢弃、继续用其余数据**。本实现是**全量校验、
整份拒绝**。理由：预设数据由脚本生成，出现坏数据意味着生成环节出了问题，
静默丢弃会让用户看到「少了几个代理人」却查不出原因。

### 5.3 已建模属性的例外：锐暴伤害

`锐暴伤害` **已完成建模**，数值固定 150%，仅在锋御最终面板显示，
不作为计算输入。抓取脚本为保持数据可追溯，仍会把该 Wiki 标签写入
`unmodeledBaseStats`；前端载入预设时通过 `MODELED_BASE_STAT_LABELS`
（`constants/calculatorOptions.ts`）将其过滤，因此它**不会**出现在
「官方还列有当前计算器尚未建模的属性」提示中。

结构校验仍覆盖全部条目，过滤只作用于提示文案。

## 6. 对拍夹具的 JS 包装

`frontend/tests/fixtures/legacy-calculator/data/*.js` 定义
`window.AGENT_PRESETS` 与 `window.WEAPON_PRESETS`，由
`tools/sync_presets.py --to-legacy` 从 JSON 生成，**不可手工编辑**。

保留原因：参照实现在顶层直接读取这两个全局量，删掉它三方对拍就跑不起来。
详见 [completeds/legacy-pages.md](completeds/legacy-pages.md)。

## 7. 相关文档

- [api-reference.md](api-reference.md) —— HTTP 接口与响应结构
- [calculation-rules.md](calculation-rules.md) —— 各 `to` 键名的含义与公式
- [architecture.md](architecture.md) —— 为什么预设走接口、规则表走本地
- [development.md](development.md) —— 数据管线与刷新流程
- [testing.md](testing.md) —— 漂移如何被守住