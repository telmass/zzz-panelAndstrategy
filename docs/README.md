# 项目文档索引

绝区零代理人面板计算器的技术文档。**按「想了解什么」组织，而非按项目结构。**

## 第一次来

| 顺序 | 文档 | 回答什么问题 |
| --- | --- | --- |
| 1 | [requirements.md](requirements.md) | 这项目做什么、不做什么、做到什么算完成、有哪些已知限制 |
| 2 | [architecture.md](architecture.md) | 代码怎么分层、依赖方向为什么是这样 |
| 3 | [directory-layout.md](directory-layout.md) | 每个目录放什么、边界在哪 |

## 日常开发

| 文档 | 内容 |
| --- | --- |
| [development.md](development.md) | 环境搭建、运行命令、测试、数据管线、**8 个已知坑** |
| [testing.md](testing.md) | 测试策略、三方对拍机制、为什么必须 0 skip |
| [api-reference.md](api-reference.md) | HTTP 接口、请求/响应结构、状态码 |
| [data-schema.md](data-schema.md) | 预设 JSON 与规则表的字段定义、校验规则 |
| [calculation-rules.md](calculation-rules.md) | 计算公式、副词条数值、模式差异、明细呈现 |

## 部署与运维

| 文档 | 内容 |
| --- | --- |
| [deployment.md](deployment.md) | 构建、三种部署形态、预设数据定位、自检清单 |

## 历史

| 目录/文档 | 内容 |
| --- | --- |
| [changelog.md](changelog.md) | 影响使用方式或正确性的变更记录 |
| [completeds/](completeds/) | 已完成事项的归档。**不是当前状态的描述**，查阅前先看该目录的README |

## 按角色的阅读路径

### 我要改计算公式

[calculation-rules.md](calculation-rules.md) → [architecture.md](architecture.md) 第 3.4 节
→ [development.md](development.md) 第 7 节 → [testing.md](testing.md) 第 2 节

⚠️ 改完必须跑 `npm run test`，其中 `legacy-parity.spec.ts` 的 4 个对拍场景会验证你没有改变既有数值。

### 我要加一个代理人预设

[requirements.md](requirements.md) 第 3 节 → [data-schema.md](data-schema.md) 第 2 节
→ [development.md](development.md) 第 6 节

⚠️ 走 `.github/skills/do_calculatorModel` 这个 Skill，它封装了完整流程。

### 我要改前端界面

[directory-layout.md](directory-layout.md) 第 2 节 → [api-reference.md](api-reference.md)
→ [testing.md](testing.md) 第 5 节

⚠️ 前端不做算术。要改数值结果，改 `backend/src/zzz_panel/core/`。

### 我要加一个 API 端点

[architecture.md](architecture.md) 第 2 节铁律 → [api-reference.md](api-reference.md)
→ [backend/tests/test_api.py](../backend/tests/test_api.py)

### 我要把这个项目部署出去

[deployment.md](deployment.md)。先读第 1 节选形态，再照第 6 节自检。

## 文档维护约定

| 规则 | 说明 |
| --- | --- |
| **代码是唯一权威** | 文档与代码冲突时以代码为准，并**回头修文档**，而不是让代码迁就文档 |
| 数字与字段名必须核对 | 从不凭印象写；字段名逐字对照 Pydantic 模型与 TS 类型 |
| 状态码、路径、端口这类事实要能验证 | 文档里的每个断言都应能用一条命令验证 |
| 已知限制要显式记录 | 有技术债就写出来，不要让读者以为一切正常。见 [requirements.md](requirements.md) 第 7 节 |
| 完成的文档移入 `completeds/` | 归档后修正所有指向它的链接 |
| 链接用相对路径 | 保证在 GitHub、编辑器预览下都能跳转 |

## 文档索引之外

| 位置 | 内容 |
| --- | --- |
| [../README.md](../README.md) | 项目简介、技术栈、快速开始 |
| [../data/README.md](../data/README.md) | 数据文件说明与刷新命令 |
| [../tools/README.md](../tools/README.md) | 开发脚本清单 |
| [../frontend/src/README.md](../frontend/src/README.md) | 前端源码约定 |
| [../frontend/tests/README.md](../frontend/tests/README.md) | 前端测试结构 |
| [../backend/tests/README.md](../backend/tests/README.md) | 后端测试清单 |
| `.github/skills/*/SKILL.md` | 代理人与音擎数据抓取流程 |