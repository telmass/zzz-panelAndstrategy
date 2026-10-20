# 项目文档索引

绝区零代理人面板计算器 + 攻略库的技术文档入口。**先读集成总览，再按需进入专题。**

## 从这里开始

| 顺序 | 文档 | 回答什么问题 |
| --- | --- | --- |
| 1 | [project-overview.md](project-overview.md) | **集成式总览**：项目定位、当前规模、架构、数据流、目录地图、常用命令、文档地图 |
| 2 | [requirements.md](requirements.md) | 做什么、不做什么、验收标准、已知限制 |
| 3 | [architecture.md](architecture.md) | 代码怎么分层、依赖方向为什么是这样 |
| 4 | [directory-layout.md](directory-layout.md) | 每个目录放什么、边界在哪 |
| 5 | [structure-review.md](structure-review.md) | **当前结构问题、证据、解决方案与修复顺序** |
| 6 | [completeds/repair-plan.md](completeds/repair-plan.md) | **全项目审计后的完整修复计划（英文）：P0/P1/P2、文件清单、执行顺序与验收命令** |

> 文档与代码冲突时**以代码为准**，并回头修正文档。数量类事实以
> [project-overview.md](project-overview.md) 的「当前规模」表为准，专题文档不再重复。

## 日常开发

| 文档 | 内容 |
| --- | --- |
| [development.md](development.md) | 环境搭建、运行命令、数据管线、常见坑 |
| [testing.md](testing.md) | 测试策略、三方对拍、当前覆盖缺口 |
| [api-reference.md](api-reference.md) | HTTP 接口、请求/响应结构、状态码 |
| [data-schema.md](data-schema.md) | 预设 JSON、规则表、驱动盘套装效果的字段定义与校验 |
| [calculation-rules.md](calculation-rules.md) | 计算公式、副词条数值、模式差异 |

## 部署与运维

| 文档 | 内容 |
| --- | --- |
| [deployment.md](deployment.md) | 构建、四种部署形态、Worker 数据打包、自检清单 |

## 历史

| 目录/文档 | 内容 |
| --- | --- |
| [changelog.md](changelog.md) | 影响使用方式或正确性的变更记录（历史状态，不代表当前实现） |
| [completeds/](completeds/) | 已完成事项归档。**不是当前状态的描述**，查阅前先看该目录的 README |

## 按角色的阅读路径

### 我要改计算公式

[calculation-rules.md](calculation-rules.md) → [architecture.md](architecture.md) 第 3 节
→ [development.md](development.md) 第 7 节 → [testing.md](testing.md) 第 2 节

⚠️ 改完必须跑 `cd frontend; npm run test`，其中 `legacy-parity.spec.ts` 的 4 个场景会验证
既有数值未被改变。

### 我要加一个代理人预设

[requirements.md](requirements.md) 第 3 节 → [data-schema.md](data-schema.md) 第 2 节
→ [development.md](development.md) 第 6 节

⚠️ 走 `.github/skills/do_calculatorModel/SKILL.md`，它封装了完整流程。

### 我要产出一个代理人攻略页

`.github/skills/agent-strategy/SKILL.md` → `strategy/README.md`
→ [directory-layout.md](directory-layout.md) 第 6.1 节

⚠️ 新增代理人 = `strategy/<slug>/data/` 数据目录 + 运行
`python tools/gen_strategy_guides.py` 生成登记表；页面由共享渲染器提供，不需要复制
`index.html/app.js/styles.css`。slug 必须以 `data/agent-name-mapping.json` 为准。
图片一律写 `/images/…` URL。`保存攻略` 会按 JSON 自动生成导出卡片（驱动盘主词条会带 `alt` 备选），毕业面板的 54 条在展示时拆成「大词条 + 小词条」，无需手工改数据。

### 我要改名或修攻略页引用

`.github/skills/fix-agent/SKILL.md`。它规定了 slug、数据文件名、图标路径
与 `strategyGuides.ts` 的对齐方式。

### 我要改前端界面

[directory-layout.md](directory-layout.md) 第 2 节 → [api-reference.md](api-reference.md)
→ [testing.md](testing.md) 第 5 节

⚠️ 前端不做算术。要改数值结果，改 `backend/src/zzz_panel/core/`。

### 我要加一个 API 端点

[architecture.md](architecture.md) 第 2 节 → [api-reference.md](api-reference.md)
→ `backend/tests/test_api.py`

### 我要部署

生产形态是 Cloudflare Worker：[deployment.md](deployment.md)。先读第 1 节选形态（生产选 D），
再照第 7 节自检。

## 文档维护约定

| 规则 | 说明 |
| --- | --- |
| **一处事实只写一次** | 数量、路径、命令优先写进 [project-overview.md](project-overview.md) 或对应专题，其他文档链接过去 |
| **代码是唯一权威** | 文档与代码冲突时以代码为准，并回头修文档 |
| **数字必须可核对** | 写「60 名 / 101 把 / 127 项」时附上数据文件或核对命令 |
| **专题文档只讲一个主题** | 接口、数据字段、公式、部署、测试各自独立，不互相复制 |
| **已知限制显式记录** | 技术债写进 [requirements.md](requirements.md) 第 7 节或 [structure-review.md](structure-review.md) |
| **完成事项归档** | 移入 `completeds/` 后修正所有指向它的链接 |
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
| `.github/skills/do_calculatorModel/SKILL.md` | 新增代理人预设 |
| `.github/skills/agent-strategy/SKILL.md` | 攻略页抓取 → 编辑 → 毕业面板 → 渲染/导出卡片 |
| `.github/skills/fix-agent/SKILL.md` | 按中文名修正单个代理人的攻略页引用 |
| `.github/skills/agent-background/SKILL.md` | 给攻略页加右侧全身背景图 |
| `.github/skills/read-zzz-agent-stats/SKILL.md` | 代理人预设抓取与刷新 |
| `.github/skills/read-zzz-engine-stats/SKILL.md` | 音擎预设抓取与刷新 |
| `.github/skills/read-zzz-drive-disc/SKILL.md` | 驱动盘套装效果与图标抓取 |
