# 需求说明

本文说明项目**做什么、不做什么、以及做到什么程度算完成**。
规则细节见 [calculation-rules.md](../design/calculation-rules.md)，接口细节见
[api-reference.md](../reference/api-reference.md)。

## 1. 项目定位

绝区零（Zenless Zone Zero）**代理人面板计算器 + 攻略库**：
- **计算器**（`/calculator`）：输入一名代理人的基础面板与一套配装
  （音擎、核心技、驱动盘、二件套），输出最终面板数值与逐项计算明细；
- **攻略库**（`/strategy`）：按代理人收录加点优先级、音擎 / 驱动盘推荐、
  满配毕业面板、队伍搭配与文字攻略；
- **指南**（`/guide`）：讲清各字段口径与计算顺序。

它解决的实际问题：配装数值分散在多个页面与 Wiki 表格里，手工核对一遍要十几分钟，
且容易漏掉「先乘后加」的顺序细节。

## 2. 目标用户与使用场景

| 用户 | 场景 |
| --- | --- |
| 普通玩家 | 配完一套驱动盘，想知道最终面板到底有多少暴击、是否超过阈值 |
| 数据作者 / 攻略作者 | 验证一组新预设的数值是否自洽，需要可复算、可追溯的明细 |
| 本项目维护者 | 改了计算公式，需要确认没有把旧结果改坏（靠[三方对拍](../guides/testing.md)） |

**单人工具**，无账号、无协作、无服务端持久化。已部署为公开站点
<https://zzzstrategy.cc.cd>，但**没有任何用户数据面**。

## 3. 功能范围

### 3.1 必须有（已实现）

| 编号 | 功能 | 落地位置 |
| --- | --- | --- |
| F1 | 三种面板模式：通用 / 命破 / 锋御，随代理人的 `panelMode` 生效，显隐相应输入项并追加专属结果行。界面**无独立的模式切换器**；`通用` 只作模式名，不出现在代理人文案里（见 `HIDE_STANDARD_MODE_LABEL`） | `core/modes.py`、`usePanelMode` |
| F2 | 六大输入模块：基础面板、音擎、核心加成、驱动盘主词条、驱动盘副词条、二件套 | `components/calculator/` |
| F3 | 61 名代理人预设，含等级 60 基础面板与 A–F 核心加成合计 | `data/catalog/agents.json` |
| F4 | 101 项音擎预设，含基础攻击/防御力与固定副词条 | `data/catalog/weapons.json` |
| F5 | 副词条条数上限：单条36、总计 54，超出自动回退 | `useSubStatLimit` |
| F6 | 12～14 行最终面板 + 逐行计算明细（含来源追溯） | `core/breakdown.py` |
| F7 | 计算全部在后端完成，前端只做输入与渲染 | `api-reference.md` |
| F8 | 长文学习指南页（`/guide`） | `views/GuideView.vue` |
| F9 | 预设数据更新流程可重复执行且字节幂等 | `tools/sync_presets.py --check` |
| F12 | 计算器页支持**配装方案的存取**：`保存方案` 存到本机 `localStorage`（键 `zzz.builds.v1`）、`导出` 下载 `.json`、`导入` 读队友发来的 `.json`、`复制链接` 把配装编码进 URL 片段（`#build=…`）。**全部本地**——不落服务端（见 C7）；方案里不存基础面板（它随代理人预设走） | `frontend/src/types/build.ts`、`stores/buildStore.ts`、`composables/useBuildIO.ts`、`composables/useBuildPanel.ts` |
| F11 | 计算器页支持 **URL 直载**：`?mode=rupture` / `?mode=fengyu` 决定面板模式，`?agent=<slug 或预设 id>` 直接载入该代理人的基础面板与核心加成并切到它的模式。一条链接即可复现某位代理人的整套面板（分享需求，也是 UI 验收清单「状态由 URL 决定」的前提） | `views/CalculatorView.vue`、`composables/useAgentPreset.ts` |
| F10 | 启动页「代理人攻略」入口卡 → `/strategy` 代理人选择页（封面卡网格）→ `/strategy/<slug>` 攻略单页（Vue 路由 + 共享渲染器读取 `strategy/<slug>/data/`）。当前 61 个攻略数据目录、61 条登记 | `views/LauncherView.vue`、`views/StrategyPickerView.vue`、`views/StrategyView.vue`、`frontend/src/strategy/renderStrategy.ts`、`constants/strategyGuides.ts`、`vite.config.ts` |

### 3.2 明确不做

| 不做 | 理由 |
| --- | --- |
| 账号体系、登录、云端存档 | 单人本地工具，加了只是负担 |
| 伤害计算 / DPS 模拟 | 本项目只算**面板**，不含战斗模拟。这是刻意的边界，越界会让规则验证失效 |
| 遗器（音擎）与驱动盘的**获取与养成**建议 | 只做数值计算，不做掉落概率或养成规划 |
| 代理人 / 音擎的**实时抓取** | 抓取由独立的 Skill 脚本离线完成，本项目只读产物。理由见 [architecture.md](../design/architecture.md) 的「预设走接口、规则表走本地」 |
| 多语言 | 全站简体中文 |
| 移动端原生应用 | 响应式网页已覆盖窄屏 |

### 3.3 已删除的功能

| 功能 | 删除时间 | 去向 |
| --- | --- | --- |
| 命破 / 锋御独立计算器页 | 迁移第 1 步 | 统一为 `/calculator?mode=` |
| 「测试范例计算器模板」独立示例页 | 迁移第 5 步 | **不恢复**：其计算逻辑与统一计算器完全重复 |
| 仓库根目录 6 个中文书签兼容页 | 迁移第 5 步 | 直接访问 `/` |

## 4. 关键设计约束

这些是需求的一部分，实现时不得违反。详细论证见 [architecture.md](../design/architecture.md)。

| 编号 | 约束 | 原因 |
| --- | --- | --- |
| C1 | `core/` 零IO、零 Web 框架依赖 | 让网页、CLI、批量计算共用一份规则 |
| C2 | 预设走 HTTP 接口，配装规则表走本地 JSON | 前者是易变大需刷新的数据，后者要瞬时可用 |
| C3 | 前端组件内禁止直接 `fetch` | 单一网络出口，便于统一错误处理 |
| C4 | 选项用稳定 id，不用数组下标 | 预设在后端、选项表在前端，两侧独立演进 |
| C5 | 参照实现 `tests/fixtures/legacy-calculator/` **只读** | 它是对拍基准，改了就没有基准了 |
| C6 | 生产部署形态是 Cloudflare Worker：后端只能装纯 Python / 带 PyEmscripten wheel 的包，且**只有 `.py` 会被上传** | 决定了预设数据必须编译成 Python 模块（`tools/bundle_worker_data.py`），也决定了 uvicorn 只能待在 dev 组。见 [deployment.md](../guides/deployment.md) 5.6 |
| C7 | 线上站点**刻意公开**，不配 Cloudflare Access，也不在 Worker 内写鉴权 | 全站无账号、无个人信息、无可写数据面。依据与残留风险见 [deployment.md](../guides/deployment.md) 5.9 |

## 5. 数据准确性要求

| 要求 | 保证方式 |
| --- | --- |
| 每个数值都可追溯到来源 | `breakdown` 的 `sources` 字段列出每项加成的出处 |
| 前端与后端结果一致 | 前端不计算，只渲染后端结果 |
| 网页与命令行结果一致 | 两者共用 `core/` 的同一份公式：CLI 走 `core.panel.calculate_panel`，网页走 `services` → `core.panel.calculate_selection`，最终都落到 `_apply_totals` 与 `calculate_mode_stats` |
| 重构不改变既有数值 | [三方对拍](../guides/testing.md)：旧 JS 实现 ≡ Vue3 页面 ≡ Python 后端，逐字符比对 |

**公式与参照实现在冲突时，以参照实现的输出为准**——它代表用户已经习惯的数字。

## 6. 验收标准

功能开发完成需同时满足：

| 项 | 标准 |
| --- | --- |
| 前端类型检查 | `npm run typecheck` 无错 |
| 前端构建 | `npm run build` 通过 |
| 前端测试 | `npm run test` 全绿（当前 185 项） |
| 后端测试 | `uv run pytest` 全绿，**且无 skip**（439 项全部通过） |
| 数据同步门禁 | `sync_manifest.py --check`、`sync_presets.py --options --check`、`bundle_worker_data.py --check` 均退出 0 |
| 部署门禁 | `wrangler.jsonc` 为纯 ASCII；带代理执行 `pywrangler deploy` 成功 |
| 手工验收 | `/`、`/calculator`、`/guide`、`/strategy` 可打开；抽查 `/strategy/ye-shunguang`、`/strategy/banyue`、`/strategy/roxy`、`/strategy/cissia` 等攻略页无控制台报错、图片正常；攻略页「核心技」应能切出「核心技」与「额外能力」两个招式页 |

## 7. 已知限制

诚实记录当前的技术债，避免误认为已实现：

| 限制 | 位置 | 说明 |
| --- | --- | --- |
| `sources` 文案有「固定」重复 | `core/modifiers.py` | 拼接 `f"{slot}号固定{label}"` 而 `label` 本身是「固定生命」，产出「1号固定固定生命+2,200」。**界面上看不到**（hp/atk/def 的明细由 `breakdown` 内联片段渲染，不读 `sources`），仅 API 消费者会看到。改动它不影响三方对拍 |
| `base.penforce` / `base.energyAccumulation` 被接受但忽略 | `services/panel_service.py` | 贯穿力由最终攻防血反推；字段保留只为形状对齐 |
| `PanelInputs.base_pen_value` 不影响任何输出 | `core/panel.py` | 写入 `sums["pv"]`，但 `pv` 行读的是 `pen_val` |
| schema 无任何数值范围约束 | `backend/src/zzz_panel/schemas/` | 无 `ge` / `le` / `max_length`，越界值靠 `core` 兜底钳制 |
| 未知选项 id 静默忽略 | `core/options.py` | 不报错，配错时表现为「没生效」而非报错 |
| 503 响应会回显文件路径 | `presets/loader.py`、`api/routes/presets.py` | 预设加载失败时 `detail` 里带路径。Worker 上只是包内生成物的模块名，不含本机目录；但**不要把用户目录写进任何错误信息** |
| 免费额度可能被他人消耗 | Cloudflare Workers | 无鉴权意味着任何人都能调接口。计算是毫秒级纯函数，瓶颈是请求数不是 CPU。被刷了再上 WAF 限速 |
| 国内网络直连线上域名被重置 | — | 按 SNI 阻断，属本地网络环境问题，非站点故障。用代理访问即可 |
| `usePanelCalc()` 被实例化两次 | `ResultPanel.vue`、`CoreModule.vue` | 各自持有独立的防抖计时器与请求序号 |
| 二件套模块用共享件 | `SetEffectModule.vue` | 走 `common/SelectField`（与音擎 / 代理人选择器同一套样式与行为）；「按效果 / 按套装」两种填法共用同批槽位 |
| 核心加成条目数口径不一 | UI 文案说 8 项 / 9 选 2 | 实际 12 项；沿袭旧实现，UI 文案未同步 |
| 测试只覆盖本地，不覆盖线上 Worker | — | Cloudflare 的运行时、配额、域名绑定都不在测试范围内。部署后按 [deployment.md](../guides/deployment.md) 第 7 节人工自检 |
| `discs/` 图标只进了计算器的套装选择器 | `frontend/public/images/discs/` | 30 张套装图标随 `data/catalog/drive-discs.json` 的 `image`（URL）落地，**计算器的「按套装」选择器已用上**（选套装时显示图标 + 名称，4 件套效果文本悬停可见）。攻略页的驱动盘卡仍是另一条取图路径 |
| 12 套驱动盘的 2 件套效果不计入面板 | `data/catalog/drive-discs.json` | 8 套是**属性伤害**（面板没有「属性伤害」这一行——加一行会破坏三方对拍），4 套是**条件触发**（不是固定面板值）。这 12 套的 `effect2` 为 `null`、用 `effect2Note` 说明原因。**「按套装」选择器里仍可选**，但会标注「不计入面板」并说明原因。详见 [data-schema.md](../design/data-schema.md) 第 6 节 |
| 只有叶瞬光的毕业面板能实算复核 | `.github/skills/agent-strategy/scripts/calc_graduation_panel.py` | 除叶瞬光这个参考实例外，其余代理人的面板都是「写进去就不再看」。要都可复算，需把计算参数机器可读地存进策略文件——**待办**，先核对参数再上形状 |

> 上述限制**均不影响计算正确性**，因此不阻塞使用。清理它们属于重构范畴，
> 需配套对拍验证，改动前请先读[testing.md](../guides/testing.md)。

## 8. 相关文档

- [architecture.md](../design/architecture.md) —— 架构分层与依赖方向
- [api-reference.md](../reference/api-reference.md) —— HTTP 接口
- [data-schema.md](../design/data-schema.md) —— 预设与选项表结构
- [calculation-rules.md](../design/calculation-rules.md) —— 计算公式
- [directory-layout.md](directory-layout.md) —— 目录职责
- [development.md](../guides/development.md) —— 开发环境与流程
- [testing.md](../guides/testing.md) —— 测试策略
- [deployment.md](../guides/deployment.md) —— 部署
- [changelog.md](../changelog.md) —— 变更记录