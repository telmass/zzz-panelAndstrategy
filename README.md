#代理人面板计算器

绝区零（Zenless Zone Zero）代理人面板计算工具。输入一名代理人的基础面板与一套配装
（音擎、核心技、驱动盘、二件套），输出最终面板数值与逐项计算明细。

计算全部由后端 Python 完成，前端只负责输入与渲染——因此网页与命令行的结果必然一致。

## 核心功能

| 功能 | 说明 |
| --- | --- |
|三种面板模式 | 通用 / 命破 / 锋御。切换后输入区显隐相应字段，结果区追加专属行 |
| 六大输入模块 | 基础面板、音擎、核心加成、驱动盘主词条、驱动盘副词条、二件套 |
| 60 名代理人预设 | 等级 60 基础面板 + A–F 核心加成合计，附官方 Wiki 来源链接 |
| 100 项音擎预设 | 基础攻击/防御力 + 固定副词条 |
| 副词条上限 | 单条 36 条、总计 54 条（游戏内上限），超出自动回退 |
| 逐项计算明细 | 每行结果都附来源追溯，能看出「这个数从哪来」 |
| 长文学习指南 | 应用内 `/guide`，讲清各字段口径与计算顺序 |

**不做的**：伤害计算 / DPS 模拟、账号与云存档、养成建议、多语言。
理由见 [docs/requirements.md](docs/requirements.md) 第 3 节。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3.5 + TypeScript 5.7 + Vite 6 + Pinia 2 + Vue Router 4 |
| 样式 | 原生 CSS + CSS 变量设计令牌（无 UI 框架、无 Tailwind） |
| 后端 | Python 3.13+ + FastAPI + Pydantic v2 |
| 测试 | Vitest + @vue/test-utils + jsdom（前端）；pytest（后端） |
| 包管理 | uv（Python）、npm（前端） |
| 数据 | 官方 HoYoLAB Wiki 抓取 → `data/*.json` |

架构与依赖方向见 [docs/architecture.md](docs/architecture.md)。

## 快速开始

### 环境要求

Python >= 3.13、uv、Node.js 20+、npm。

### 安装

```powershell
uv sync                    # Python 依赖（含 pytest）
cd frontend; npm install; cd ..
```

### 运行

```powershell
pwsh tools/dev.ps1         # 一条命令拉起前后端
```

- 前端 <http://localhost:5173/>（Vite，`/api` 自动代理到后端，因此不涉及 CORS）
- 后端 `http://127.0.0.1:8000`，接口文档 `/docs`

子命令：`start`（默认）/ `stop` / `restart` / `status`。

> Windows 执行策略拦截时用：
> `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\dev.ps1 start`

### 单独启动（调试用）

```powershell
uv run uvicorn zzz_panel.api.app:app --port 8000     # 后端
cd frontend; npm run dev                              # 前端
```

### 只跑后端计算

```powershell
uv run zzz-panel           # 固定跑一组示例输入，打印 12 行结果
```

### 测试

```powershell
uv run pytest                           # 后端 87 项
cd frontend; npm run test               # 前端 64 项
```

> **pytest 必须 0 skip。** 任何 skip 都意味着某道护栏没真正执行。
> 详见 [docs/testing.md](docs/testing.md)。

更多命令与已知坑见 [docs/development.md](docs/development.md)。

## 目录结构

```
.
├── frontend/                前端工程（Vite root）
│   ├── src/
│   │   ├── views/           3 个路由页：启动 / 计算器 / 指南
│   │   ├── components/      layout · common · calculator · guide
│   │   ├── stores/          Pinia：panelStore（输入真源）· presetStore
│   │   ├── composables/     usePanelCalc · useAgentPreset · usePanelMode · useSubStatLimit
│   │   ├── api/             唯一网络出口
│   │   ├── types/ constants/ utils/ assets/styles/
│   │   └── main.ts App.vue
│   ├── tests/
│   │   ├── fixtures/legacy-calculator/   只读参照实现，供三方对拍
│   │   └── support/                      测试夹具层
│   ├── tools/               两个 Node 诊断脚本
│   └── public/images/       代理人/音擎 PNG（Vite 原样拷贝）
│
├── backend/                 Python 计算服务
│   ├── src/zzz_panel/
│   │   ├── core/            规则真源：纯函数、零 IO、零框架依赖
│   │   ├── api/ routes/     FastAPI，只做协议转换
│   │   ├── schemas/         Pydantic 请求/响应模型
│   │   ├── services/        用例编排，无公式
│   │   ├── presets/         加载（mtime 缓存）与语义校验
│   │   └── cli.py           命令行入口
│   └── tests/               pytest
│
├── data/                    唯一真实数据源（3 个 JSON，全部是生成物）
├── docs/                    技术文档（见下）
├── tools/                   开发脚本：dev.ps1 · sync_presets.py
└── .github/skills/          数据抓取 Skill（脚本位置固定，勿移动）
```

逐目录职责见 [docs/directory-layout.md](docs/directory-layout.md)。

## 数据来源

代理人与音擎预设由 `.github/skills/` 下的脚本从官方 HoYoLAB Wiki 抓取生成。
**唯一真实源是 [`data/*.json`](data/README.md)，不要手工编辑**——每次运行抓取脚本都会被整体覆盖。

```powershell
python .github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py
python .github/skills/read-zzz-engine-stats/scripts/refresh_weapon_presets.py
python tools/sync_presets.py --to-legacy      # 抓取后必须再跑
```

配装规则表的真源是 `backend/src/zzz_panel/core/options.py`，改了它要重新生成
`data/options.json`：

```powershell
python tools/sync_presets.py --options
```

数据管线全貌见 [docs/development.md](docs/development.md) 第 6 节。

## 文档

| 文档 | 内容 |
| --- | --- |
| [docs/README.md](docs/README.md) | **文档总索引**（含按角色的阅读路径） |
| [docs/requirements.md](docs/requirements.md) | 项目范围、非目标、已知限制 |
| [docs/architecture.md](docs/architecture.md) | 架构分层与设计决策 |
| [docs/api-reference.md](docs/api-reference.md) | HTTP 接口契约 |
| [docs/data-schema.md](docs/data-schema.md) | 预设与规则表结构、校验规则 |
| [docs/calculation-rules.md](docs/calculation-rules.md) | 计算公式与规则细节 |
| [docs/directory-layout.md](docs/directory-layout.md) | 目录职责详解 |
| [docs/development.md](docs/development.md) | 开发流程、数据管线、已知坑 |
| [docs/testing.md](docs/testing.md) | 测试策略与三方对拍 |
| [docs/deployment.md](docs/deployment.md) | 构建与部署形态 |
| [docs/changelog.md](docs/changelog.md) | 变更记录 |
| [docs/completeds/](docs/completeds/) | 已完成事项归档（迁移记录等） |

## 关于三方对拍

`frontend/tests/fixtures/legacy-calculator/` 保留了一份迁移前的原生实现，
**只读**，用途是让测试能逐字符验证「重构没有改变计算结果」：

```
旧 JS 实现（JSDOM 内跑） ≡ Vue3 页面 ≡ Python 后端
```

这是本项目最强的正确性护栏。**不要修改夹具内的任何文件**——改了基准，
对拍就变成自己和自己比，永远不会失败。

## 现状

本仓库已完成从「原生 HTML + 内联 JS 计算」到「Vue3 前端 + Python 计算服务」的迁移。
`frontend/src/` 与 `backend/` 是当前唯一实现。

已知技术债（死代码、口径不一文案的文案等）记录在
[docs/requirements.md](docs/requirements.md) 第 7 节。