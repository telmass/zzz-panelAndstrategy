# 测试策略

本文说明测什么、怎么测、以及为什么这样组织。执行命令见
[development.md](development.md)。

## 1. 总览

| 套件 | 命令 | 用例数 | 覆盖 |
| --- | --- | --- | --- |
| 后端 | `uv run pytest` | 87 | 计算、格式化、预设校验、HTTP 契约 |
| 前端 | `npm run test` | 73 | 渲染、交互、请求构造、**三方对拍** |

测试状态以这两个命令的输出为准，共 154 项。

## 2. 核心资产：三方对拍

这是整个项目最重要的护栏，也是迁移期保留旧实现的唯一理由。

```
只读参照实现                      新实现
tests/fixtures/legacy-calculator/  frontend/src/  +  backend/
（原生 JS，JSDOM 内跑）                    │
        │                                    │
        └──────────逐字符比对───────────────┘
                tests/legacy-parity.spec.ts
```

四个场景，每个场景断言**两件事**：

1. 可见结果行的**行标签列表**完全一致
2. 每行的 `{ label, value, breakdown }` 快照完全一致

| 场景 | 行数 | 关注点 |
| --- | --- | --- |
| 默认空配置 | 12 | 基础链路与默认值 |
| 满配 | 12 | 全加成叠加后的数值与明细文案 |
| 命破代理人 `ep-1299` | 13 | 贯穿力行与命破专属字段 |
| 锋御代理人 `ep-2145` | 14 | 实际暴击率、锐暴伤害、锐能自动累积 |

### 为什么必须逐字符

数值相同但明细文案不同，说明计算过程不同。既然要证明「重构没改变行为」，
就必须比到最细的粒度——因为用户看得见的正是明细。

### 夹具的三条铁律

1. **禁止修改。** 一旦修改，基准就变成了新实现本身，对拍永远不会失败。
2. **禁止补功能。** 新需求一律实现在 Vue3 / Python 侧。
3. **子目录结构不能动。** `pages/calculator.html` 用 `../styles`、`../data`、
   `../scripts` 相对引用。

违反任何一条，这 4 个用例就退化成「自己和自己比」。

### 后端拉不起来时

整体 `skip` 并给出具体原因，而不是让 CI 变红。本机开发时这很方便，
但**在 CI 上必须把 skip 当失败看**——它意味着这 4 项根本没执行。

## 3. 跨语言格式对拍

`backend/tests/test_fmt_parity.py` 用 Node **真正执行**夹具里的 `fmt` 函数
（由 `_fmt_driver.cjs` 从 `calculator.js` 提取函数体），与 Python 的
`core.fmt.fmt` 逐值比对 33 个数值——覆盖整数、千分位、小数、尾零、负数、
浮点噪声与极值。

这不是「照着抄一遍」，而是跨语言实际执行。

### 曾经的假绿灯

该文件原本在 Node 退出码非 0 时 `pytest.skip`。基准文件被挪走就会命中这条路径：
**测试不报错，但检查已失效**。现已改为只有 Node 不可用才 skip，
基准缺失或执行失败一律断言失败。

> 这是本项目的一条通用原则：**护栏的失效方式必须是红灯，不许是绿灯。**

## 4. 后端测试（87 项）

| 文件 | 项数 | 覆盖 |
| --- | --- | --- |
| `test_presets.py` | 大头 | 目录定位、四类加载错误、语义校验的每条规则、响应与JSON 逐条等价、503 而非 500、id 唯一性 |
| `test_panel.py` | — | 加成链路、武器基础值并入顺序、百分比二次加成、取整向下、模式公式与非法模式 |
| `test_options_json.py` | — | `data/options.json` 与 Python 规则表一致；`DISC_FIXED_STATS` 顺序与槽位一致 |
| `test_legacy_parity.py` | — | Python 侧对 `legacy_cases.json`（由参照实现导出）逐条比对数值 |
| `test_fmt_parity.py` | 2 | 见上|
| `test_api.py` | — | 路由形状、CORS 预检、422 触发条件、负数条数被钳制、`def` 别名、响应键名大小写 |

几个刻意设计的断言：

- **响应键名大小写**：响应**字段**是 camelCase，但 `totals` 的键是 `imp`/`ac`/`pv`
  短名，`breakdown` / `sources` / `sums` 的键保持 snake_case 长名。
  这套混用有测试锁住，改了会红。
- **负数条数返回 200 而非 422**：schema 无 `ge` 约束，钳制发生在 `core`。
  测试明确记录这个行为，避免有人误加约束导致对拍失败。
- **空body `{}` 是合法请求**：所有字段都有默认值。

## 5. 前端测试（73 项）

Vitest + jsdom，配置在 `vite.config.ts` 的 `test` 块（**没有独立的
`vitest.config.ts`**，容易找错）。

| 文件 | 项数 | 覆盖 |
| --- | --- | --- |
| `calculator-view.spec.ts` | 30 | 计算器骨架、启动页、子页返回导航、指南页 |
| `panel-interactions.spec.ts` | 39 | 音擎 cascader 分组与回填、选项前缀图标与菜单文案、副词条钳制、模式与锋御文案、代理人预设载入、后端对接 |
| `legacy-parity.spec.ts` | 4 | 三方对拍 |

### naive-ui 组件的三条测试约束

音擎选择器换成 `n-cascader` 后，这三点会反复绊到人：

- **浮层 Teleport 到 `body`**，不在 wrapper 树内。要断言浮层只能查
  `document.body`，`wrapper.find()` 一律查不到；且用例必须挂
  `enableAutoUnmount(afterEach)`，否则展开过的浮层会留给后续用例。
- **选项在 `n-virtual-list` 里**（naive-ui 默认 `virtualScroll` 为 `true`）。
  jsdom 没有布局引擎，容器高度算出来是 0，**一项都不会渲染**。因此
  「7 个一级项」只在 store 层断言，DOM 层只验证浮层打开。
- **placeholder 是覆盖层**，落在 `.n-base-selection-placeholder` 上，
  不是 `<input>` 的 `placeholder` 属性（后者为空字符串）。

### 渲染断言写得比数字断言重

例如基础面板断言「12 个字段 + 默认值 8000/1000/1.2 + 命破专属字段隐藏」；
副词条断言「10 个步进器 + 10 条确切标签 + 初始禁用状态 + `副词条总数：0 / 54`」。

原因：这类页面**靠 DOM 结构与视觉分层表达信息**，改动结构若无人察觉，功能就悄悄坏了。

### 几个具体的回归护栏

| 用例 | 挡什么 |
| --- | --- |
| `def_pct × 3 → 14.4%` | 浮点误差（`0.048×3` 不是精确的 `0.144`） |
| 载入预设后副词条**保留** | `clearAgentPresetFields` 误清副词条 |
| 锋御载入提示**不含**「锐暴伤害」 | 已建模属性被误报为未建模 |
| 切换等级清空下游 + 基础值归零 | 音擎联动不完整 |
| `usePanelCalc` 实例化两次 | 各组件独立持有 watcher 与计时器（见下方） |

### 夹具层

| 文件 | 作用 |
| --- | --- |
| `support/setup.ts` | 全局 stub `RouterLink` |
| `support/router.ts` | `RouterLinkStub` |
| `support/api.ts` | 假后端。**读真实的 `data/*.json`**，因此下拉框项数断言能发现数据漂移 |
| `support/backend.ts` | 拉起真实 uvicorn（端口 0自动分配），解析 stderr 拿端口，探活 `/api/health`，三条路径上清理孤儿进程 |
| `support/flush.ts` | 等待 260 ms（越过 200 ms 防抖）+ 微任务 + 两个宏任务 |

`support/backend.ts` 只服务于三方对拍——它让 4 个用例走完整 HTTP 链路，
而不是 mock 掉。

## 6. 没有覆盖的地方

诚实记录，避免误以为有护栏：

| 未覆盖 | 风险 | 建议 |
| --- | --- | --- |
| 前端**视觉回归** | 改CSS 不会变红 | 手工核对三个页面；引入截图对比需先解决 jsdom 无法渲染的问题 |
| 后端**并发与性能** | 个人工具，160 条预设 + 纯函数计算，实测无压力 | 暂不需要 |
| **`refresh_*_presets.py` 的端到端** | 需要联网抓 Wiki，CI 不跑 | 由 `test_presets.py` 间接保证 `render()` 与已提交文件一致 |
| **UI 死代码**（`useSubStatLimit.reset`、6 个后端常量） | 无害 | 见 [requirements.md](requirements.md) 已知限制 |

## 7. 加新测试放哪

| 你要测| 放哪 |
| --- | --- |
| 一个计算公式的边界 | `backend/tests/test_panel.py` |
| 一条预设校验规则 | `backend/tests/test_presets.py` |
| 请求体形状 / 状态码 | `backend/tests/test_api.py` |
| 组件渲染结构 | `frontend/tests/calculator-view.spec.ts` |
| 用户操作后的状态流转 | `frontend/tests/panel-interactions.spec.ts` |
| **旧实现与新实现的差异** | `frontend/tests/legacy-parity.spec.ts`（只在行为**有意**变更时改） |

## 8. 相关文档

- [development.md](development.md) —— 测试命令与常见坑
- [requirements.md](requirements.md) —— 验收标准
- [architecture.md](architecture.md) —— 为什么计算必须在后端