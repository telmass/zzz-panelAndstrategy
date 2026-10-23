# 项目文档索引

绝区零代理人面板计算器 + 攻略库的技术文档入口。**先读集成总览，再按需进入专题。**

文档按主题分四类目录，避免十几个平铺文件互相引用：

| 目录 | 放什么 |
| --- | --- |
| [overview/](overview/) | 项目全貌：定位与规模、需求与验收、目录与边界 |
| [design/](design/) | 设计与数据规则：分层架构、字段契约、计算公式 |
| [guides/](guides/) | 操作指南：怎么开发、怎么测、怎么部署 |
| [reference/](reference/) | 接口参考：HTTP 契约 |
| [changelog.md](changelog.md) + [changelog/](changelog/) | 变更记录（当前 / 归档） |
| [completeds/](completeds/) | 已完成事项归档。**不是当前状态的描述**，查阅前先看该目录的 README |

## 从这里开始

| 顺序 | 文档 | 回答什么问题 |
| --- | --- | --- |
| 1 | [overview/project-overview.md](overview/project-overview.md) | **集成式总览**：项目定位、当前规模、架构、数据流、目录地图、常用命令、文档地图 |
| 2 | [overview/requirements.md](overview/requirements.md) | 做什么、不做什么、验收标准、已知限制 |
| 3 | [design/architecture.md](design/architecture.md) | 代码怎么分层、依赖方向为什么是这样 |
| 4 | [overview/directory-layout.md](overview/directory-layout.md) | 每个目录放什么、边界在哪 |
| 5 | [completeds/structure-review.md](completeds/structure-review.md) | **历史结构问题与修复记录**（已归档） |
| 6 | [completeds/repair-plan.md](completeds/repair-plan.md) | **全项目审计后的完整修复计划（英文）：P0/P1/P2、文件清单、执行顺序与验收命令** |

> 文档与代码冲突时**以代码为准**，并回头修正文档。数量类事实以
> [overview/project-overview.md](overview/project-overview.md) 的「当前规模」表为准，专题文档不再重复
> （`python tools/check_docs.py` 会核对这条不变量）。

## 日常开发

| 文档 | 内容 |
| --- | --- |
| [guides/development.md](guides/development.md) | 环境搭建、运行命令、数据管线、常见坑 |
| [guides/testing.md](guides/testing.md) | 测试策略、三方对拍、当前覆盖缺口 |
| [reference/api-reference.md](reference/api-reference.md) | HTTP 接口、请求/响应结构、状态码 |
| [design/data-schema.md](design/data-schema.md) | 预设 JSON、规则表、驱动盘套装效果的字段定义与校验 |
| [design/calculation-rules.md](design/calculation-rules.md) | 计算公式、副词条数值、模式差异 |
| [design/damage-mechanism-guide.md](design/damage-mechanism-guide.md) | **伤害机制读本 + 配装求解设计**：白板环境（§17）、局内效果层（§18）、代理人计算档案（§19）、理论循环（§20）、词条最优分配（§21）、驱动盘评分（§22）、影画/音擎相对值（§23）、非满配边际收益（§24） |
| [design/ui-system.md](design/ui-system.md) | **前端视觉体系**：设计令牌、字号 / 字重 / 间距 / 阴影阶梯、颜色语义、UI 闸门与截图工具 |
| [design/ui-review-checklist.md](design/ui-review-checklist.md) | **UI 人工验收清单**：三档分层、截图节点、验收表模板 |
| [design/ui-review-log.md](design/ui-review-log.md) | UI 验收记录与先例表（跨轮次一致性的依据） |
| [plans/damage-solving-engine.md](plans/damage-solving-engine.md) | **待执行**：伤害求解层落地计划（白板口径、局内效果、计算器档案、词条优化、报告与策略页；P0–P7 + 验收 + 迁移） |

## 部署与运维

| 文档 | 内容 |
| --- | --- |
| [guides/deployment.md](guides/deployment.md) | 构建、四种部署形态、Worker 数据打包、自检清单 |

## 历史

| 目录/文档 | 内容 |
| --- | --- |
| [changelog.md](changelog.md) | 影响使用方式或正确性的变更记录（**当前**，只保留最近若干条） |
| [changelog/](changelog/) | 变更记录归档：`YYYY-MM-archive.md`，按月一个文件 |
| [completeds/](completeds/) | 已完成事项归档。**不是当前状态的描述**，查阅前先看该目录的 README |

## 按角色的阅读路径

### 我要改计算公式

[calculation-rules.md](design/calculation-rules.md) → [architecture.md](design/architecture.md) 第 3 节
→ [development.md](guides/development.md) 第 7 节 → [testing.md](guides/testing.md) 第 2 节

⚠️ 改完必须跑 `cd frontend; npm run test`，其中 `legacy-parity.spec.ts` 的 4 个场景会验证
既有数值未被改变。

### 我要加一个代理人预设

[requirements.md](overview/requirements.md) 第 3 节 → [data-schema.md](design/data-schema.md) 第 2 节
→ [development.md](guides/development.md) 第 6 节

⚠️ 走 `.github/skills/do_calculatorModel/SKILL.md`，它封装了完整流程。

### 我要产出一个代理人攻略页

`.github/skills/get-agent-strategy/SKILL.md`（**一键部署的唯一入口**）
→ `strategy/README.md`（数据契约）→ [directory-layout.md](overview/directory-layout.md) 第 6.1 节
→ `.github/skills/_shared/`（命名映射 / 信息采集矩阵 / 抓取口径 / 已知坑）

⚠️ 整页部署直接跑 `python tools/agent_deploy.py --name <中文名>`：它串起预设刷新、WIKI 抓取、
立绘与角色框头像、编辑内容骨架、毕业面板实算、登记表与生成物、最后跑全量闸门。
编辑类内容（加点链、音擎推荐、驱动盘方案、毕业面板口径、队伍、文字攻略）**无法从 WIKI 推导**，
脚本只生成骨架与待确认清单，需逐项与用户确认。修正已有页面先跑 `python tools/agent_audit.py --slug <slug>`
拿体检报告（引用断链、图标错配、核心技缺额外能力、机制归属写错、占位残留…）。
页面由共享渲染器提供，不需要复制 `index.html/app.js/styles.css`；slug 必须以
`data/catalog/agent-index.json` 为准，图片一律写 `/images/…` URL。

### 我要改名或修攻略页引用

`.github/skills/fix-agent/SKILL.md`（子流程）或 `python tools/agent_audit.py --slug <slug>`（体检报告）。
它规定了 slug、数据文件名、图标路径与 `strategyGuides.ts` 的对齐方式。

### 我要改前端界面

[directory-layout.md](overview/directory-layout.md) 第 2 节 → [api-reference.md](reference/api-reference.md)
→ [testing.md](guides/testing.md) 第 5 节

⚠️ 前端不做算术。要改数值结果，改 `backend/src/zzz_panel/core/`。

### 我要加一个 API 端点

[architecture.md](design/architecture.md) 第 2 节 → [api-reference.md](reference/api-reference.md)
→ `backend/tests/test_api.py`

### 我要部署

生产形态是 Cloudflare Worker：[deployment.md](guides/deployment.md)。先读第 1 节选形态（生产选 D），
再照第 7 节自检。

## 文档维护约定

| 规则 | 说明 |
| --- | --- |
| **一处事实只写一次** | 数量、路径、命令优先写进 [overview/project-overview.md](overview/project-overview.md) 或对应专题，其他文档链接过去 |
| **代码是唯一权威** | 文档与代码冲突时以代码为准，并回头修文档 |
| **数字必须可核对** | 写「61 名 / 101 把 / 131 项」时附上数据文件或核对命令；`python tools/check_docs.py` 会核对数量类事实是否与数据源一致 |
| **专题文档只讲一个主题** | 接口、数据字段、公式、部署、测试各自独立，不互相复制 |
| **文档分目录归类** | overview / design / guides / reference 四类，新文档先想清楚该放哪一类；移动文件后要修正所有指向它的链接（`check_docs.py` 会报断链） |
| **已知限制显式记录** | 技术债写进 [overview/requirements.md](overview/requirements.md) 第 7 节或 [completeds/structure-review.md](completeds/structure-review.md) |
| **完成事项归档** | 移入 `completeds/` 后修正所有指向它的链接 |
| **changelog 过长要归档** | [changelog.md](changelog.md) 只保留最近若干条（默认 12），更早的条目按月归档到 `changelog/YYYY-MM-archive.md`；用 `python tools/archive_changelog.py` 执行 |
| **链接用相对路径** | 保证 GitHub、编辑器预览都能跳转 |

## 索引之外

| 位置 | 内容 |
| --- | --- |
| [../README.md](../README.md) | 项目简介、技术栈、快速开始、部署三步 |
| [../data/README.md](../data/README.md) | 数据文件说明、生成命令与 Worker 编译产物 |
| [../tools/README.md](../tools/README.md) | 开发、同步、打包与诊断脚本 |
| [../frontend/src/README.md](../frontend/src/README.md) | 前端源码约定 |
| [../frontend/tests/README.md](../frontend/tests/README.md) | 前端测试结构 |
| [../backend/tests/README.md](../backend/tests/README.md) | 后端测试清单 |
| [../strategy/README.md](../strategy/README.md) | 攻略数据契约、渲染架构与新增流程 |
| `.github/skills/get-agent-strategy/SKILL.md` | **代理人攻略的一站式入口**：新增/修正代理人的阶段表、按职业分组的参考页表、待确认清单 |
| `.github/skills/_shared/` | 各 skill 共享的规程：命名映射、信息采集矩阵、部署闸门与抓取口径（不是 skill） |
| `.github/skills/do_calculatorModel/SKILL.md` | 新增代理人预设 |
| `.github/skills/agent-strategy/SKILL.md` | 攻略页抓取 → 编辑 → 毕业面板 → 渲染/导出卡片 |
| `.github/skills/fix-agent/SKILL.md` | 按中文名修正单个代理人的攻略页引用 |
| `.github/skills/agent-background/SKILL.md` | 给攻略页加右侧全身背景图与角色框头像 |
| `.github/skills/read-zzz-agent-stats/SKILL.md` | 代理人预设抓取与刷新 |
| `.github/skills/read-zzz-engine-stats/SKILL.md` | 音擎预设抓取与刷新 |
| `.github/skills/read-zzz-drive-disc/SKILL.md` | 驱动盘套装效果与图标抓取 |
