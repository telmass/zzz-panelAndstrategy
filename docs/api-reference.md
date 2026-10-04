# 接口文档

后端 HTTP 接口的权威说明。字段名与默认值均取自
`backend/src/zzz_panel/schemas/` 的 Pydantic 模型，与实现逐字一致。

在线交互式文档（后端运行时可访问）：<http://127.0.0.1:8000/docs>

## 通用约定

| 项 | 约定 |
| --- | --- |
| 基址 | 开发期前端用相对路径 `/api`，由 Vite 代理到 `http://127.0.0.1:8000`；跨域部署时由 `VITE_API_BASE_URL` 改为绝对地址 |
| 编码 | 请求与响应均为 `application/json; charset=utf-8` |
| 字段命名 | **线上 camelCase，Python 侧 snake_case。** `CamelModel` 用 `alias_generator=to_camel` + `populate_by_name=True`，因此请求体两种写法都接受 |
| 认证 | **无。** 本项目是单机个人工具，不含用户体系与鉴权 |
| 缓存 | 预设接口按文件 mtime 缓存，进程内生效；`/api/panel/calc` 每次实算 |

### 状态码

| 码 | 何时 | 触发方 |
| --- | --- | --- |
| 200 | 成功 | — |
| 422 | 请求体不满足 schema | FastAPI 自动。典型：非法 `mode`、枚举值越界、类型不符 |
| 503 | 预设数据不可用（文件缺失／JSON 非法／结构或语义校验失败） | `api/routes/presets.py` 捕获 `PresetLoadError` |

503 而非 500 的理由：数据源坏了不等于服务器崩了，这样前端能给出可操作的提示
（「预设数据加载失败」而非「服务器内部错误」）。

## 接口一览

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/health` | 探活 |
| GET | `/api/presets/agents` | 代理人预设列表（60 条） |
| GET | `/api/presets/weapons` | 音擎预设列表（100 条） |
| POST | `/api/panel/calc` | 面板计算 |

---

## GET /api/health

无参数。恒返回 `{"status": "ok"}`，不做任何 IO。

```json
{ "status": "ok" }
```

前端测试夹具 `frontend/tests/support/backend.ts` 用它判断后端是否就绪。

---

## GET /api/presets/agents

响应体固定为 `{"items": [...]}`，不返回裸数组——便于后续加分页字段而不破坏客户端。

```json
{
  "items": [
    {
      "id": "ep-1109",
      "name": "示例代理人",
      "attribute": "火",
      "grade": "S",
      "roleTag": "强攻",
      "panelMode": "standard",
      "source": "https://baike.mihoyo.com/zzz/wiki/content/1109/detail",
      "base": { "hp": 7673, "atk": 888, "def": 612, "impact": 93, "cr": 19.4,
                "cd": 50, "ac": 94, "am": 93, "pr": 0, "er": 1.2 },
      "additionalBaseStats": { "penforce": 0, "energyAccumulation": 0 },
      "unavailableBaseStats": [],
      "unmodeledBaseStats": [],
      "coreBonuses": [
        { "optionId": "cd", "optionCount": 2, "ranks": ["D", "E", "F"],
          "label": "暴击伤害", "perRankValue": 9.6, "totalValue": 28.8, "unit": "%" }
      ]
    }
  ]
}
```

字段级校验规则见 [data-schema.md](data-schema.md)。要点：

- `base` 的 10 个键全部 `Optional`。官方未提供的键为 `null`，**同时**必须列入
  `unavailableBaseStats`，否则前端会把 `null` 当 0 写进面板且无任何提示。
- `base.def` 的线上键名是 `def`（Pydantic 侧字段名 `def_`，带 `alias="def"`）。
- `attribute` 与 `grade` 必填，取值白名单见 data-schema.md 第 2.3 节；
  「特殊属性」的判定规则（人数 == 1）见第 2.4 节。
- `response_model_exclude_none=True`：`None` 字段不出现在响应里，因此响应与
  `data/agent-presets.json` 逐字节等价（`backend/tests/test_presets.py` 有等价性断言）。

**503 响应体**沿用 FastAPI 标准形状：

```json
{ "detail": "agent-presets.json 语义校验失败：ep-9999：id 重复 ['ep-9999']" }
```

---

## GET /api/presets/weapons

同为 `{"items": [...]}`，10 条字段。

```json
{
  "items": [
    {
      "id": "ep-1107",
      "name": "示例音擎",
      "grade": "S",
      "roleTag": "强攻",
      "source": "https://baike.mihoyo.com/zzz/wiki/content/1107/detail",
      "baseKind": "atk",
      "baseAttack": 713,
      "baseDefense": 0,
      "substat": { "label": "暴击伤害", "value": 48, "kind": "pct", "to": "cd" }
    }
  ]
}
```

---

## POST /api/panel/calc

**请求只传「选了什么」，不传算出来的数值。** 前端不做任何算术，全部由后端计算。
这是第3 步计算下沉的核心约定。

### 请求体

所有字段都有默认值，`{}` 是合法请求（返回 12 行基础面板）。

```jsonc
{
  "mode": "standard",              // standard | rupture | fengyu
  "base": {                        // 12 个数值键，全部可选
    "hp": 8000, "atk": 1000, "def": 600,
    "impact": 90, "cr": 5, "cd": 50,
    "ac": 100, "am": 100, "pr": 0, "er": 1.2,
    "penforce": 0,                 // 见下方「被接受但忽略的字段」
    "energyAccumulation": 0        // 同上
  },
  "weapon": {
    "baseKind": "atk",             // atk | def，决定 baseValue 计入攻击还是防御
    "baseValue": 0,                // 音擎基础攻击/防御力
    "substat": {                   // 可为 null
      "target": "cd",              // 累加器键名，取值见 calculation-rules.md
      "value": 48,                 // 副词条数值
      "kind": "pct",               // pct | flat
      "label": "暴击伤害"// 仅用于回显，不参与计算
    }
  },
  "core":     { "core1": "cr", "core2": "cd" },       // 各为选项 id，共 2 槽
  "discMain": { "disc4": "atk_pct_30", "disc5": "dmg_30", "disc6": "impact_pct_24" },
  "subStats": { "hp_flat": 12, "cr": 9, "am": 11 },// 键为选项 id，值为条数
  "sets":     { "set0": "atk_pct_10", "set1": "cd_16", "set2": "er_pct_20" }
}
```

要点：

- **选项一律用稳定 id，不用数组下标。** id 取自 `data/options.json`，
  由 `backend/src/zzz_panel/core/options.py` 单向生成。
- **未知 id 静默忽略**，不报错（`core/options.py: find_option` 返回 `None`）。
- **副词条条数向下取整且不为负**：`count = max(0, floor(raw))`
  （`core/modifiers.py:121`）。传 `-5` 或 `3.9` 都不会报 422。
- 音擎基础值按 `baseKind` **互斥**计入攻击或防御，不会同时计入。

### 响应体

固定 9 个顶层字段。以下是**真实输出**（请求体 `{}`，`mode` 为默认 `standard`）：

```jsonc
{
  "mode": "standard",
  "totals": {                      // 恒为 12 键，与模式无关
    "hp": 10200, "atk": 1316, "def": 784,
    "cr": 5, "cd": 50, "dmg": 0,
    "pr": 0, "pv": 0,
    "am": 100, "ac": 100, "imp": 90, "er": 1.2
  },
  "modeStats": {},                 // 见下方「模式专属字段」
  "blastDmg": null,                // fengyu_blast_dmg 的顶层别名，否则 null
  "sums":    { "hp_flat": 2200, "atk_flat": 316, "def_flat": 184 },
  "sources": { "hp_flat": ["1号固定固定生命+2,200"],
               "atk_flat": ["2号固定固定攻击+316"],
               "def_flat": ["3号固定固定防御+184"] },
  "subFixed":  { "hp_flat": 0, "atk_flat": 0, "def_flat": 0 },
  "weaponBase": { "atk": 0, "def": 0 },
  "breakdown": { "hp": [ /* 见下 */ ] }
}
```

> `sources` 里「1号固定**固定**生命」的「固定」重复是已知的文案缺陷
> （`core/modifiers.py:165` 拼接时`stat.label` 本身已含「固定」）。
> 它**不会显示在界面上**——hp/atk/def 三行的明细由 `breakdown` 的内联片段渲染，
> 不读 `sources`。仅 API 消费者会看到。详见
> [requirements.md](requirements.md) 第 7 节。

**`totals` 的 12 个键恒定存在**，模式只影响 `modeStats` 与 `blastDmg`。
注意键名是缩写：`imp`(冲击力)、`ac`(异常掌控)、`pv`(穿透值)、`er`(能量回复)、
`am`(异常精通)；而 `sums` / `sources` / `subFixed` / `breakdown` 的键保持 snake_case
且用长名（`impact_pct`、`pen_val`）。这套混用是有意的，前端 `types/panel.ts` 与之对齐。

### 模式专属字段

同一请求体下切换 `mode` 的实测结果：

| mode | `modeStats` | `blastDmg` | `breakdown` 行数 |
| --- | --- | --- | --- |
| `standard` | `{}` | `null` | 12 |
| `rupture` | `{ "penforce": 1414.8 }` | `null` | 13（+贯穿力） |
| `fengyu` | `{ "actual_cr": 22.5, "fengyu_blast_dmg": 150 }` | `150` | 14（+实际暴击率、锐暴伤害） |

- 贯穿力 `= 0.3 × 最终攻击力 + 0.1 × 最终生命值` = `0.3×1316 + 0.1×10200` = **1414.8**
- 实际暴击率 `= 最终暴击伤害 × 35% + 原最终暴击率` = `50×0.35 + 5` = **22.5**
- 锐暴伤害 `= 150`（固定常量，不受任何输入影响）

`blastDmg` 与 `modeStats.fengyu_blast_dmg` 是同一个值的两个出口：前端结果面板读
顶层 `blastDmg`，明细生成读 `modeStats` 内的键。**合并两者会重复计数。**

### `breakdown` 结构

结构化数组，不是 HTML 字符串。后端不输出中文文案，格式化与换行由前端
`usePanelCalc.renderBreakdown` 负责（这样换行规则改动不必同步改后端）。

`breakdown.hp` 的真实内容（上面那个空配置请求）：

```jsonc
"hp": [
  { "type": "line", "wrapped": true, "parts": [
      { "type": "text", "text": "(" },
      { "type": "num",  "value": 8000, "bold": false, "unit": "" },
      { "type": "text", "text": ")" },
      { "type": "text", "text": "×(1+" },
      { "type": "kw",   "text": "0%" },
      { "type": "text", "text": ")" }
  ] },
  { "type": "line", "wrapped": true, "parts": [
      { "type": "text",    "text": "+" },
      { "type": "num",     "value": 2200, "bold": false, "unit": "" },
      { "type": "text",    "text": "（1号主词条）" },
      { "type": "text",    "text": "+" },
      { "type": "num",     "value": 0, "bold": false, "unit": "" },
      { "type": "text",    "text": "（副词条）" },
      { "type": "text",    "text": " = " },
      { "type": "num",     "value": 10200, "bold": true, "unit": "" }
  ] }
]
```

渲染效果（`<br>` 由 `wrapped: true` 产生）：

```
(8000)×(1+0%)
+2,200（1号主词条）+0（副词条） = 10,200
```

四种片段类型：

| `type` | 额外字段 | 前端渲染 |
| --- | --- | --- |
| `text` | `text: string` | 原样输出（**不转义**，文案由后端保证安全） |
| `kw` | `text: string` | `<span class="kw">`。上例中用于「0%」这类数值关键词 |
| `num` | `value: number`、`bold: bool`、`unit: string` | `<b>`，**`unit` 渲染在 `</b>` 之内**，与旧实现 `= <b>68.8%</b>` 的视觉一致 |
| `sources` | `items: string[]` | ` + ` 连接；空数组渲染为「无」。用于纯加法行（暴击率、增伤等） |

`breakdown` 的键集合恒等于结果区的可见行数（12 / 13 / 14），
`backend/tests/test_legacy_parity.py` 对此有断言。

### 被接受但忽略的字段

`base.penforce` 与 `base.energyAccumulation` 在 schema 中存在，**但计算时不参与**：

- 贯穿力由最终攻击与最终生命**反推**，不读输入（`core/modes.py:22`）
- `services/panel_service.py` 的 `_BASE_KEY_MAP` 未包含这两个键，因此它们不会被搬进 `core`

同理，CLI 用的 `PanelInputs.base_pen_value` 也不影响任何输出
（`core/panel.py:172` 写入 `sums["pv"]`，但 `pv` 行读的是 `pen_val`）。

保留这些字段是为了让请求体形状与代理人预设的 `base` 对齐，读代码时不必怀疑
「是不是漏算了」。

---

## 相关文档

- [data-schema.md](data-schema.md) —— 预设 JSON 与选项表的字段定义与校验规则
- [architecture.md](architecture.md) —— 分层与依赖方向铁律
- [calculation-rules.md](calculation-rules.md) —— 计算公式与选项 id 含义
- [testing.md](testing.md) —— 接口等价性如何被测试守住