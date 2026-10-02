# 数据结构与 API 契约

> 本文描述**目标**结构。FastAPI 尚未实现，落地时需同步更新本文。

## 预设数据

### 当前形态（过渡期）

`frontend/legacy/data/agent-presets.js` 定义 `window.AGENT_PRESETS`，
`frontend/legacy/data/weapon-presets.js` 定义 `window.WEAPON_PRESETS`。
两者都是 JS 字面量，由 Skill 脚本整体覆盖生成，**不可手工编辑**。

### 目标形态

`data/agent-presets.json` 与 `data/weapon-presets.json` 是唯一真实源。
`frontend/legacy/data/*.js` 在迁移期由 `tools/sync_presets.py` 从 JSON 反向生成。

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

从 `frontend/legacy/scripts/calculator.js:47-58` 与 `applyAgentPreset` 迁入，
改为**启动时一次性校验，失败即报错**（而非运行时逐条抛错）：

- `id` / `name` / `roleTag` 非空，`roleTag` 属于 7 个合法职业之一
- 同类型内 `id` 不重复
- `panelMode` 属于 standard / rupture / fengyu
- `coreBonuses` 非空，且每项的 `totalValue` 能由 `optionId` × `optionCount` 精确表示
- 每项 `perRankValue × len(ranks)` 等于 `totalValue`
- `coreBonuses` 展开后恰好能填入 2 个核心槽位
- `unmodeledBaseStats` 每项的 `label` / `value` / `unit` 类型正确

### 已建模属性的例外：锐暴伤害

`锐暴伤害` **已完成建模**，数值固定为 150%，仅在锋御代理人的最终面板中显示，
不作为计算输入。抓取脚本为保持数据可追溯，仍会把该 WIKI 标签写入 `unmodeledBaseStats`；
加载时 `calculator.js` 通过 `MODELED_BASE_STAT_LABELS` 将其过滤，因此它**不会**出现在
「官方还列有当前计算器尚未建模的属性」提示中。结构校验仍覆盖全部条目，过滤只作用于提示文案。

## API 契约

```
GET  /api/health
     → { "status": "ok", "version": "0.1.0" }

GET  /api/presets/agents
     → { "items": [ /* 代理人预设数组 */ ] }

GET  /api/presets/weapons
     → { "items": [ /* 音擎预设数组 */ ] }

POST /api/panel/calculate
```

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
