# 项目总览（单一事实源）

本文是仓库的**集成式技术总览**：先读这一篇即可建立全局认识，细节再按文末索引进入专题文档。
文档与代码冲突时**以代码为准**，并回头修正本文与专题文档。

> 快照时间：2026-10-20。数量类事实由 `data/`、`strategy/`、`frontend/public/images/` 直接统计得出；
> 涉及测试的条目以当时实际执行结果为准。本次审查时工作区包含未提交的攻略页扩充，
> 结构性问题与修复顺序见 [structure-review.md](../completeds/structure-review.md)。

## 1. 项目是什么

绝区零（Zenless Zone Zero）**代理人面板计算器 + 代理人攻略库**。

- **计算器**：选择代理人、音擎、核心技、驱动盘主副词条与二件套，得到最终面板与逐项计算明细。
- **攻略库**：每个代理人一个数据驱动的攻略页（Vue 路由 + 共享渲染器），包含加点优先级、
  音擎 / 驱动盘推荐、满配毕业面板、队伍搭配与文字攻略；`保存攻略` 会按同一份 JSON 生成紧凑导出卡片。
- **边界**：只算面板，不做伤害计算 / DPS 模拟；无账号、无云存档、无多语言。

线上站点：<https://zzzstrategy.cc.cd>，生产形态是 Cloudflare Worker（Python Workers + 静态 Assets），
同一域名同时提供页面与 `/api/*`。

## 2. 当前规模（可核对）

| 项 | 当前值 | 核对方式 |
| --- | --- | --- |
| 代理人预设 | 61 条 | `data/catalog/agents.json` |
| 音擎预设 | 101 条 | `data/catalog/weapons.json` |
| 驱动盘套装效果 | 30 套（**18 套的 2 件套效果可计入面板**，12 套是属性伤害 / 条件触发） | `data/catalog/drive-discs.json` |
| 配装规则表 | 7 张，共 54 个条目 | `data/rules/calculator-rules.json` |
| 代理人命名映射 | 62 条（含 1 条未上线） | `data/catalog/agent-index.json` |
| 攻略页目录 | 61 个（全部已登记） | `strategy/` + `constants/strategyGuides.ts` |
| 图片资源 | 522 张 webp | `frontend/public/images/` |
| 前端测试 | 131 项通过 | `cd frontend; npm run test` |
| 后端测试 | 439 项全部通过 | `.venv/Scripts/python -m pytest` |

图片明细：代理人 61、音擎 101、驱动盘 30、职业 7、技能 6、属性 10、等级 2、攻略独有 305。
属性与职业图标文件名统一为小写 ASCII slug（如 `honed-edge.webp`、`attack.webp`）；
历史文档里的 `Honed Edge.png` / `honed_edge` 写法已过时。

## 3. 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3.5 + TypeScript 5.7 + Vite 6 + Pinia 2 + Vue Router 4 + naive-ui 2 |
| 样式 | 原生 CSS + `tokens.css` 设计变量；naive-ui 通过 `useNaiveTheme` 读取同一套变量 |
| 后端 | Python 3.13+ + FastAPI + Pydantic v2 |
| 测试 | Vitest + jsdom（前端）；pytest（后端） |
| 数据 | 官方 HoYoLAB Wiki 抓取 → `data/catalog/*.json`（路径登记在 `data/manifest.json`）+ `data/rules/calculator-rules.json`（由 `core/*.py` 生成）；攻略页另有 `strategy/<slug>/data/*.json` |
| 部署 | Cloudflare Workers（`backend/src/worker.py` + `frontend/dist/` Assets） |

## 4. 架构与依赖方向

```
浏览器
  │ 静态资源（Cloudflare Assets 或 Vite dev）
  ▼
frontend/src/views/*.vue ── StrategyView.vue ──> strategy/renderStrategy.ts（共享渲染器）
  │                                          ├─ strategyCard.ts（保存攻略导出卡片）
  │ 只经 src/api/*.ts 发请求                 └─ fetch /strategy/<slug>/data/*.json
  ▼
POST /api/panel/calc · GET /api/presets/*
  ▼
backend/src/zzz_panel/api/routes/     FastAPI：只做协议转换
  ▼
backend/src/zzz_panel/services/       用例编排，无公式
  ▼
backend/src/zzz_panel/core/           规则真源：纯函数、零 IO、零框架依赖
  ▲
  └── cli.py                           命令行入口，与网页共用同一 core
```

必须保持的边界：

1. `core/` 不 import FastAPI / Pydantic，不读文件，不 `print`。
2. `api/` 与 `cli.py` 不重复实现公式，统一走 `services/` → `core/`。
3. 前端组件不直接 `fetch`，一切网络访问经 `src/api/`。
4. 前端不做面板算术，只提交「选了什么」。
5. `frontend/tests/fixtures/legacy-calculator/` 是只读对拍基准，禁止修改。
6. 攻略数据与主应用共用唯一图片根 `frontend/public/images/`，JSON 只写 `/images/…` URL；
   攻略页由 `frontend/src/strategy/renderStrategy.ts` 统一渲染，`保存攻略` 由 `strategyCard.ts` 按 JSON 生成卡片，`strategy/<slug>/` 只放数据。

## 5. 数据流

### 5.1 面板计算

```
用户改下拉框 / 数字
  → panelStore（输入唯一真源）
  → usePanelCalc（200ms 防抖，buildRequest 只组装选择项）
  → POST /api/panel/calc
  → schemas 校验 → services 命名转换
  → core/modifiers 累加 → core/panel + core/modes 计算
  → core/breakdown 输出结构化明细
  → 前端 renderBreakdown 渲染
```

### 5.2 数据来源与生成物

| 文件 | 角色 | 源头 / 生成方式 |
| --- | --- | --- |
| `data/catalog/agents.json` | 代理人 60 级基础面板 + 核心加成 | `.github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py` |
| `data/catalog/weapons.json` | 音擎基础值 + 固定副词条 | `.github/skills/read-zzz-engine-stats/scripts/refresh_weapon_presets.py` |
| `data/rules/calculator-rules.json` | 7 张配装规则表 | `tools/sync_presets.py --options`（源头 `core/options.py` + `core/constants.py`） |
| `data/catalog/drive-discs.json` | 30 套驱动盘 2/4 件套效果 | `.github/skills/read-zzz-drive-disc/scripts/refresh_disc_presets.py` |
| `data/catalog/agent-index.json` | 中英文名 → 规范 slug | 手工维护；`fix-agent` Skill 的权威命名表 |
| `frontend/src/constants/strategyGuides.ts` | 攻略登记表 | `tools/gen_strategy_guides.py`（`--check` 守卫） |
| `strategy/<slug>/data/<slug>.json` | 攻略页抓取产物 | `.github/skills/agent-strategy/scripts/scrape_agent_guide.py` |
| `strategy/<slug>/data/<slug>.strategy.json` | 攻略编辑内容 + 毕业面板 | 手写；`calc_graduation_panel.py` 写入 `graduationPanel` |
| `backend/src/zzz_panel/_bundled_data.py` | Worker 内预设镜像 | `tools/bundle_worker_data.py`（gitignored） |

十条数据漂移闸 + 两条 UI 闸：

```powershell
python tools/sync_manifest.py --check
python tools/sync_presets.py --options --check
python tools/bundle_worker_data.py --check
python tools/normalize_strategy.py --check
python tools/gen_strategy_guides.py --check
python tools/seed_main_stat_notes.py --check
```

## 6. 目录地图

```text
.
├── frontend/                 Vue3 主应用（Vite root）
│   ├── src/                  views / components / composables / stores / api / types / constants / strategy
│   ├── public/images/        唯一图片根（/images/… URL）
│   ├── tests/                Vitest + legacy 只读夹具
│   └── tools/                三个 Node 脚本（对拍导出 / 明细 diff / CDP 截图）
├── backend/                  Python FastAPI 服务
│   ├── src/zzz_panel/        core / schemas / services / api / presets / cli
│   ├── src/worker.py         Cloudflare Worker 入口
│   └── tests/                pytest
├── strategy/<slug>/          每个代理人一个数据目录（data/ 两份 JSON，无页面模板）
├── data/                     生成数据与手写命名映射
├── docs/                     技术文档（本目录）
├── tools/                    开发、同步、打包脚本
└── .github/skills/           抓取与攻略生产 Skill（位置固定）
```

逐目录职责见 [directory-layout.md](directory-layout.md)。

## 7. 常用命令

```powershell
uv sync                         # Python 依赖
cd frontend; npm install; cd ..

pwsh tools/dev.ps1              # 一键启动前后端（推荐）
uv run pytest                   # 后端 439 项
cd frontend; npm run test       # 前端 185 项（不要与 pytest 并行）
cd frontend; npm run typecheck  # 类型检查
cd frontend; npm run build      # 构建 dist/
python tools/normalize_strategy.py --check   # 攻略数据命名/引用
python tools/gen_strategy_guides.py --check  # 登记表漂移
python tools/seed_main_stat_notes.py --check # 主词条备注占位
```

部署（Cloudflare Worker）：

```powershell
python tools/bundle_worker_data.py
cd frontend; npm run build; cd ..
uv run --group worker pywrangler deploy   # 国内网络需配置 HTTPS_PROXY
```

完整说明见 [development.md](../guides/development.md) 与 [deployment.md](../guides/deployment.md)。

## 8. 文档地图

| 想知道什么 | 去哪儿 |
| --- | --- |
| 项目定位、范围、非目标、已知限制 | [requirements.md](requirements.md) |
| 分层、依赖方向、关键设计决策 | [architecture.md](../design/architecture.md) |
| 每个目录放什么、边界在哪 | [directory-layout.md](directory-layout.md) |
| 开发流程、数据管线、常见坑 | [development.md](../guides/development.md) |
| 测试策略、三方对拍 | [testing.md](../guides/testing.md) |
| HTTP 接口契约 | [api-reference.md](../reference/api-reference.md) |
| 数据字段与校验规则 | [data-schema.md](../design/data-schema.md) |
| 计算公式与模式差异 | [calculation-rules.md](../design/calculation-rules.md) |
| 构建与部署形态 | [deployment.md](../guides/deployment.md) |
| 变更历史 | [changelog.md](../changelog.md) |
| 已完成事项归档 | [completeds/](../completeds) |
| **当前结构问题与解决方案** | [structure-review.md](../completeds/structure-review.md) |

## 9. 维护规则

1. **一处事实只写一次。** 数量、路径、命令优先写进本文或专题文档，其他文档链接过去，不再复制。
2. **数字必须可核对。** 新增「61 名 / 101 把 / 177 项」这类断言时，同时写出核对命令或数据文件。
3. **代码是权威。** 文档与实现冲突时改文档，而不是让代码迁就文档。
4. **完成事项移入 `completeds/`。** 归档后修正所有指向它的链接。
5. **结构变更同步结构审查。** 合入 P0/P1 修复后，更新 [structure-review.md](../completeds/structure-review.md) 的状态。
