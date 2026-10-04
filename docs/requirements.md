# 需求说明

本文说明项目**做什么、不做什么、以及做到什么程度算完成**。
规则细节见 [calculation-rules.md](calculation-rules.md)，接口细节见
[api-reference.md](api-reference.md)。

## 1. 项目定位

绝区零（Zenless Zone Zero）**代理人面板计算器**：输入一名代理人的基础面板与一套
配装（音擎、核心技、驱动盘、二件套），输出最终面板数值与逐项计算明细。

它解决的实际问题：配装数值分散在多个页面与 Wiki 表格里，手工核对一遍要十几分钟，
且容易漏掉「先乘后加」的顺序细节。

## 2. 目标用户与使用场景

| 用户 | 场景 |
| --- | --- |
| 普通玩家 | 配完一套驱动盘，想知道最终面板到底有多少暴击、是否超过阈值 |
| 数据作者 / 攻略作者 | 验证一组新预设的数值是否自洽，需要可复算、可追溯的明细 |
| 本项目维护者 | 改了计算公式，需要确认没有把旧结果改坏（靠[三方对拍](testing.md)） |

**单人工具**，无账号、无协作、无服务端持久化。已部署为公开站点
<https://zzzstrategy.cc.cd>，但**没有任何用户数据面**。

## 3. 功能范围

### 3.1 必须有（已实现）

| 编号 | 功能 | 落地位置 |
| --- | --- | --- |
| F1 | 三种面板模式：通用 / 命破 / 锋御，随代理人的 `panelMode` 生效，显隐相应输入项并追加专属结果行。界面**无独立的模式切换器**；`通用` 只作模式名，不出现在代理人文案里（见 `HIDE_STANDARD_MODE_LABEL`） | `core/modes.py`、`usePanelMode` |
| F2 | 六大输入模块：基础面板、音擎、核心加成、驱动盘主词条、驱动盘副词条、二件套 | `components/calculator/` |
| F3 | 60 名代理人预设，含等级 60 基础面板与 A–F 核心加成合计 | `data/agent-presets.json` |
| F4 | 100 项音擎预设，含基础攻击/防御力与固定副词条 | `data/weapon-presets.json` |
| F5 | 副词条条数上限：单条36、总计 54，超出自动回退 | `useSubStatLimit` |
| F6 | 12～14 行最终面板 + 逐行计算明细（含来源追溯） | `core/breakdown.py` |
| F7 | 计算全部在后端完成，前端只做输入与渲染 | `api-reference.md` |
| F8 | 长文学习指南页（`/guide`） | `views/GuideView.vue` |
| F9 | 预设数据更新流程可重复执行且字节幂等 | `tools/sync_presets.py --check` |

### 3.2 明确不做

| 不做 | 理由 |
| --- | --- |
| 账号体系、登录、云端存档 | 单人本地工具，加了只是负担 |
| 伤害计算 / DPS 模拟 | 本项目只算**面板**，不含战斗模拟。这是刻意的边界，越界会让规则验证失效 |
| 遗器（音擎）与驱动盘的**获取与养成**建议 | 只做数值计算，不做掉落概率或养成规划 |
| 代理人 / 音擎的**实时抓取** | 抓取由独立的 Skill 脚本离线完成，本项目只读产物。理由见 [architecture.md](architecture.md) 的「预设走接口、规则表走本地」 |
| 多语言 | 全站简体中文 |
| 移动端原生应用 | 响应式网页已覆盖窄屏 |

### 3.3 已删除的功能

| 功能 | 删除时间 | 去向 |
| --- | --- | --- |
| 命破 / 锋御独立计算器页 | 迁移第 1 步 | 统一为 `/calculator?mode=` |
| 「测试范例计算器模板」独立示例页 | 迁移第 5 步 | **不恢复**：其计算逻辑与统一计算器完全重复 |
| 仓库根目录 6 个中文书签兼容页 | 迁移第 5 步 | 直接访问 `/` |

## 4. 关键设计约束

这些是需求的一部分，实现时不得违反。详细论证见 [architecture.md](architecture.md)。

| 编号 | 约束 | 原因 |
| --- | --- | --- |
| C1 | `core/` 零IO、零 Web 框架依赖 | 让网页、CLI、批量计算共用一份规则 |
| C2 | 预设走 HTTP 接口，配装规则表走本地 JSON | 前者是易变大需刷新的数据，后者要瞬时可用 |
| C3 | 前端组件内禁止直接 `fetch` | 单一网络出口，便于统一错误处理 |
| C4 | 选项用稳定 id，不用数组下标 | 预设在后端、选项表在前端，两侧独立演进 |
| C5 | 参照实现 `tests/fixtures/legacy-calculator/` **只读** | 它是对拍基准，改了就没有基准了 |
| C6 | 生产部署形态是 Cloudflare Worker：后端只能装纯 Python / 带 PyEmscripten wheel 的包，且**只有 `.py` 会被上传** | 决定了预设数据必须编译成 Python 模块（`tools/bundle_worker_data.py`），也决定了 uvicorn 只能待在 dev 组。见 [deployment.md](deployment.md) 5.6 |
| C7 | 线上站点**刻意公开**，不配 Cloudflare Access，也不在 Worker 内写鉴权 | 全站无账号、无个人信息、无可写数据面。依据与残留风险见 [deployment.md](deployment.md) 5.9 |

## 5. 数据准确性要求

| 要求 | 保证方式 |
| --- | --- |
| 每个数值都可追溯到来源 | `breakdown` 的 `sources` 字段列出每项加成的出处 |
| 前端与后端结果一致 | 前端不计算，只渲染后端结果 |
| 网页与命令行结果一致 | 两者共用 `core/` 的同一份公式：CLI 走 `core.panel.calculate_panel`，网页走 `services` → `core.panel.calculate_selection`，最终都落到 `_apply_totals` 与 `calculate_mode_stats` |
| 重构不改变既有数值 | [三方对拍](testing.md)：旧 JS 实现 ≡ Vue3 页面 ≡ Python 后端，逐字符比对 |

**公式与参照实现在冲突时，以参照实现的输出为准**——它代表用户已经习惯的数字。

## 6. 验收标准

功能开发完成需同时满足：

| 项 | 标准 |
| --- | --- |
| 前端类型检查 | `npm run typecheck` 无错 |
| 前端构建 | `npm run build` 通过 |
| 前端测试 | `npm run test` 全绿 |
| 后端测试 | `uv run pytest` 全绿，**且无 skip**（skip 会让检查变成假绿灯） |
| 数据同步门禁 | `sync_presets.py --to-legacy --check`、`--options --check`、`bundle_worker_data.py --check` 均退出 0 |
| 部署门禁 | `wrangler.jsonc` 为纯 ASCII；带代理执行 `pywrangler deploy` 成功 |
| 手工验收 | `/`、`/calculator`、`/guide` 三页在 dev server 下均可打开且无控制台报错 |

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
| 二件套模块绕过通用件 | `SetEffectModule.vue` | 直接用原生 `<select>`，未走 `common/SelectField` |
| 核心加成条目数口径不一 | UI 文案说 8 项 / 9 选 2 | 实际 12 项；沿袭旧实现，UI 文案未同步 |
| 测试只覆盖本地，不覆盖线上 Worker | — | Cloudflare 的运行时、配额、域名绑定都不在测试范围内。部署后按 [deployment.md](deployment.md) 第 7 节人工自检 |

> 上述限制**均不影响计算正确性**，因此不阻塞使用。清理它们属于重构范畴，
> 需配套对拍验证，改动前请先读[testing.md](testing.md)。

## 8. 相关文档

- [architecture.md](architecture.md) —— 架构分层与依赖方向
- [api-reference.md](api-reference.md) —— HTTP 接口
- [data-schema.md](data-schema.md) —— 预设与选项表结构
- [calculation-rules.md](calculation-rules.md) —— 计算公式
- [directory-layout.md](directory-layout.md) —— 目录职责
- [development.md](development.md) —— 开发环境与流程
- [testing.md](testing.md) —— 测试策略
- [deployment.md](deployment.md) —— 部署
- [changelog.md](changelog.md) —— 变更记录