# 数据结构与 API 契约

> 本文描述预设数据的结构与 API 契约。FastAPI 已在第 3 步落地，
> 落地情况见文末「实现状态」。

## 预设数据

### 权威形态

`data/agent-presets.json` 与 `data/weapon-presets.json` 是唯一真实源。
前端不再持有副本，经 `GET /api/presets/*` 获取。

### JS 包装（仅供对拍夹具）

`frontend/tests/fixtures/legacy-calculator/data/agent-presets.js` 定义
`window.AGENT_PRESETS`，`.../weapon-presets.js` 定义 `window.WEAPON_PRESETS`。
两者都是 JS 字面量，由 `tools/sync_presets.py --to-legacy` 从 JSON 生成，
**不可手工编辑**。

这份包装曾经供迁移前的原生页面使用；那些页面已删除，现在唯一的读者是三方对拍
测试加载的参照实现。保留它是因为旧实现要在顶层直接读取这两个全局量——
改了它，对拍就变成自己跟自己比。

### 校验的两层分工

| 层 | 位置 | 负责 |
| --- | --- | --- |
| 结构与类型 | `schemas/presets.py`（Pydantic） | 类型、必填项、`panelMode` / `baseKind` / `kind` 枚举 |
| 语义 | `presets/validate.py` | id 唯一、roleTag 合法、核心加成能否由选项表示、能否填满两个槽位、缺失基础键是否已声明 unavailable |

`loader.py` 把两层的失败统一转成 `PresetLoadError`，路由返回 **503**——
预设数据非法是「数据源坏了」，不是「服务器崩了」。
前端启动时一次性装载（`main.ts` 在 `mount` 前 `await loadAll()`），
因此各 getter 保持同步派生，不需要在使用点处理加载态。

### 代理人预设

```jsonc
{
  "id": "ep-1109",
  "name": "示例代理人",
  "roleTag": "强攻",              // 强攻/击破/异常/支援/防护/命破/锋御
  "panelMode": "standard",        // standard / rupture / fengyu
  "source": "https://baike.mihoyo.com/zzz/wiki/content/1109/detail?...",
  "base": {                       // 60 级基础面板（不含核心）
    "hp": 7673, "atk": 888, "def": 612,
    "impact": 93, "cr": 19.4, "cd": 50,
    "ac": 94, "am": 93, "pr": 0, "er": 1.2
  },
  "additionalBaseStats": {        // 可选：贯穿力、闪能自动累积
    "penforce": 0,
    "energyAccumulation": 0
  },
  "unavailableBaseStats": ["pr"], // 可选：官方基础面板未提供的字段
  "unmodeledBaseStats": [         // 可选：官方列出但计算器未建模的属性（锐暴伤害除外，见下）
    { "label": "贯穿力", "value": 0, "unit": "" }
  ],
  "coreBonuses": [                // 满级核心技加成
    {
      "optionId": "cd",           // 对应 calculator-config.js 的 CORE_OPTIONS.id
      "optionCount": 2,           // 可选，等于 1 时省略
      "ranks": ["D", "E", "F"],
      "label": "暴击伤害",
      "perRankValue": 9.6,
      "totalValue": 28.8,
      "unit": "%"
    }
  ],
  "grade": "S"                    // 可选
}
```

### 音擎预设

```jsonc
{
  "id": "ep-1107",
  "name": "示例音擎",
  "grade": "S",                   // S / A / B
  "roleTag": "强攻",
  "source": "https://baike.mihoyo.com/zzz/wiki/content/1107/detail?...",
  "baseKind": "atk",              // atk 提供基础攻击力；def（锋御）提供基础防御力
  "baseAttack": 713,
  "baseDefense": 0,
  "substat": {
    "label": "暴击伤害",
    "value": 48,
    "kind": "pct",                // pct / flat
    "to": "cd"                    // 对应 calculator-config.js 的累加器键名
  }
}
```

### 校验规则

从 `frontend/tests/fixtures/legacy-calculator/scripts/calculator.js:47-58`
与 `applyAgentPreset` 迁入，改为**启动时一次性校验，失败即报错**
（而非运行时逐条抛错）：

- `id` / `name` / `roleTag` 非空，`roleTag` 属于 7 个合法职业之一
- 同类型内 `id` 不重复
- `panelMode` 属于 standard / rupture / fengyu
- `coreBonuses` 非空，且每项的 `totalValue` 能由 `optionId` × `optionCount` 精确表示
- 每项 `perRankValue × len(ranks)` 等于 `totalValue`
- `coreBonuses` 展开后恰好能填入 2 个核心槽位
- `unmodeledBaseStats` 每项的 `label` / `value` / `unit` 类型正确
- `base` 中缺失的键必须显式列入 `unavailableBaseStats`，否则前端会把缺值当 0 写进面板且无提示
- `panelMode` 为 `rupture` 时 `additionalBaseStats` 必须给出 `penforce` 与 `energyAccumulation`

### 已建模属性的例外：锐暴伤害

`锐暴伤害` **已完成建模**，数值固定为 150%，仅在锋御代理人的最终面板中显示，
不作为计算输入。抓取脚本为保持数据可追溯，仍会把该 WIKI 标签写入 `unmodeledBaseStats`；
加载时 `calculator.js` 通过 `MODELED_BASE_STAT_LABELS` 将其过滤，因此它**不会**出现在
「官方还列有当前计算器尚未建模的属性」提示中。结构校验仍覆盖全部条目，过滤只作用于提示文案。

## API 契约

```
GET  /api/health
     → { "status": "ok" }

GET  /api/presets/agents
     → { "items": [ /* 代理人预设数组 */ ] }

GET  /api/presets/weapons
     → { "items": [ /* 音擎预设数组 */ ] }

POST /api/panel/calc
```

第 3 步已实现 `GET /api/health` 与 `POST /api/panel/calc`；
第 4 步第 18 条已实现 `GET /api/presets/agents` 与 `GET /api/presets/weapons`，
响应体均为 `{"items": [...]}`，内容与 `data/*.json` 逐条等价
（`backend/tests/test_presets.py` 有等价性断言）。

选项表不经接口，由 `core/options.py` 与 `core/constants.py` 单向生成本地
`data/options.json`，前端通过 `@data` 别名直接读该文件。理由与验收见
`migration-vue3.md` 第 4 步第 20 条；漂移由 `backend/tests/test_options_json.py` 守卫。

请求体：

```jsonc
{
  "mode": "standard",             // standard / rupture / fengyu
  "base":  { "hp": 0, "atk": 0, "def": 0, "impact": 0, "cr": 0, "cd": 0,
             "ac": 0, "am": 0, "pr": 0, "er": 0,
             "penforce": 0, "energyAccumulation": 0 },
  "weapon": { "presetId": "ep-1107", "baseValue": 713, "subType": "cd", "subValue": 48 },
  "core":  [ { "optionId": "cd" }, { "optionId": "atk_base" } ],
  "drives": { "d4": "atk_pct", "d5": "dmg", "d6": "ac_pct" },
  "substats": { "hp_flat": 0, "hp_pct": 0, "atk_flat": 0, "atk_pct": 0,
                "def_flat": 0, "def_pct": 0, "cr": 0, "cd": 0,
                "pr": 0, "am": 0 },
  "sets": [ null, null, null ]
}
```

响应体：

```jsonc
{
  "totals": {
    "hp": 0, "atk": 0, "def": 0,
    "cr": 0, "cd": 0, "dmg": 0, "pr": 0,
    "penforce": 0, "actualCr": 0, "fengyuBlastDmg": 0,
    "impact": 0, "ac": 0, "er": 0, "am": 0, "penVal": 0
  },
  "breakdown": {
    "hp": [ { "label": "1号固定生命+2200", "value": 2200 } ],
    "atk": []
  }
}
```

`penforce` 仅在 `rupture` 模式返回；`actualCr` 与固定 `fengyuBlastDmg: 150` 仅在
`fengyu` 模式返回。锐暴伤害不接受输入，也不参与其他属性的计算。

`breakdown` 采用**结构化数组**而非 HTML 字符串：Python 不必输出中文文案，
格式化与换行规则留在前端 `src/utils/fmt`。字段需与 `frontend/src/types/panel.ts` 一一对应。
