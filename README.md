#代理人面板计算器

绝区零（Zenless Zone Zero）代理人面板计算工具。输入一名代理人的基础面板与一套配装
（音擎、核心技、驱动盘、二件套），输出最终面板数值与逐项计算明细。

计算全部由后端 Python 完成，前端只负责输入与渲染——因此网页与命令行的结果必然一致。

## 在线站点

**https://zzzstrategy.cc.cd**

已部署在 Cloudflare Workers 上，**公开访问、无需登录**（刻意如此，见
[docs/guides/deployment.md](docs/guides/deployment.md) 第 5.9 节）。同一个 Worker 同时提供前端静态
资源与 `/api/*` 接口，站点不依赖任何一台自有服务器——你的机器关机不影响访问。

只有一条路径需要本机代理：执行部署命令时（见下文「部署到 Cloudflare」）。

## 核心功能

| 功能 | 说明 |
| --- | --- |
|三种面板模式 | 通用 / 命破 / 锋御，由代理人的 `panelMode` 决定。输入区显隐相应字段，结果区追加专属行。界面无独立模式切换器 |
| 六大输入模块 | 基础面板、音擎、核心加成、驱动盘主词条、驱动盘副词条、二件套 |
| 61 名代理人预设 | 等级 60 基础面板 + A–F 核心加成合计，附官方 Wiki 来源链接 |
| 101 项音擎预设 | 基础攻击/防御力 + 固定副词条 |
| 副词条上限 | 单条 36 条、总计 54 条（游戏内上限），超出自动回退 |
| 逐项计算明细 | 每行结果都附来源追溯，能看出「这个数从哪来」 |
| 长文学习指南 | 应用内 `/guide`，讲清各字段口径与计算顺序 |
| 攻略同款排版 | 主页 / 计算器 / 指南三页统一为「页眉 + 回到顶部」，与代理人攻略页同一套视觉；指南页带左侧编号目录（滚动高亮 + 二级锚点），计算器六大模块带序号徽标 |
| 代理人攻略 | 应用内 `/strategy`：按代理人收录加点优先级、音擎 / 驱动盘推荐、满配毕业面板、队伍搭配与文字攻略（Vue 路由 + 共享渲染器，当前 61 个数据目录、61 条登记） |
| 直达链接 | `/calculator?mode=rupture` 定面板模式、`?agent=<slug 或预设 id>` 直接载入某位代理人的整套面板；配装方案另有 `#build=…` 链接 |
| 配装方案 | 计算器里可**保存方案**（本机 `localStorage`）、**导出 / 导入** `.json`、**复制链接**。全部本地，不落服务端 |
| 驱动盘「按套装」选 | 二件套可按**套装**选（30 套，显示图标与 2/4 件套文本），也可按**效果**选。30 套里 18 套的 2 件套效果可计入面板，12 套是属性伤害 / 条件触发，标注「不计入面板」 |

**不做的**：伤害计算 / DPS 模拟、账号与云存档、养成建议、多语言。
理由见 [docs/overview/requirements.md](docs/overview/requirements.md) 第 3 节。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3.5 + TypeScript 5.7 + Vite 6 + Pinia 2 + Vue Router 4 + naive-ui 2 |
| 样式 | 原生 CSS + CSS 变量设计令牌；代理人与音擎选择器都用 naive-ui 的 `n-cascader`，主题经 `n-config-provider` 接入既有令牌（无 Tailwind） |
| 后端 | Python 3.13+ + FastAPI + Pydantic v2 |
| 测试 | Vitest + @vue/test-utils + jsdom（前端）；pytest（后端） |
| 包管理 | uv（Python）、npm（前端） |
| 数据 | 官方 HoYoLAB Wiki 抓取 → `data/catalog/*.json`（路径登记在 `data/manifest.json`）+ `data/rules/calculator-rules.json`（由 `core/*.py` 生成） |

架构与依赖方向见 [docs/design/architecture.md](docs/design/architecture.md)。

## 快速开始

### 环境要求

Python >= 3.13（由 `.python-version` 锁定）、uv、Node.js 20+、npm。

> Python 版本是**硬锁定**的（`.python-version`）；Node 只在本仓库的文档里约定为 20+，
> 没有 `engines` 字段或 `.nvmrc` 之类的机器可读约束。

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
uv run zzz-panel-and-strategy  # 固定跑一组示例输入，打印 12 行结果
```

### 测试

```powershell
uv run pytest                           # 后端 439 项
cd frontend; npm run test               # 前端 185 项
```

> **pytest 必须 0 skip。** 任何 skip 都意味着某道护栏没真正执行。
> 后端测试当前全绿（435/435），详见 [docs/guides/testing.md](docs/guides/testing.md)；
> 此前的数据命名 / 编码红灯与修复记录见 [docs/completeds/structure-review.md](docs/completeds/structure-review.md)。

更多命令与已知坑见 [docs/guides/development.md](docs/guides/development.md)。

### 部署到 Cloudflare

线上站点的部署形态是 Cloudflare Worker（Python Workers + 静态 Assets）。三步都不能省：

```powershell
# 1. 编译预设数据进后端包（pywrangler 只上传 .py，.json 会被静默丢弃）
python tools/bundle_worker_data.py

# 2. 构建前端产物（wrangler.jsonc 的 assets.directory 指向 frontend/dist）
cd frontend; npm run build; cd ..

# 3. 部署（需要本地 HTTP 代理；部署机在中国大陆时 workers.dev 直连不通）
$env:NODE_USE_ENV_PROXY = "1"
$env:HTTPS_PROXY = "http://127.0.0.1:7892"   # 换成你自己的代理端口
$env:HTTP_PROXY  = "http://127.0.0.1:7892"
uv run --group worker pywrangler deploy
```

域名绑定、代理配置、故障排查见 [docs/guides/deployment.md](docs/guides/deployment.md)。

## 目录结构

```
.
├── index.html                 根目录跳转页（纯指引，不参与构建）
├── wrangler.jsonc             Cloudflare Worker 配置（部署形态 D）
├── pylock.toml                Worker 工具链的依赖锁，**必须提交**
├── .python-version            Python 版本锁定（3.13）
├── frontend/                前端工程（Vite root）
│   ├── src/
│   │   ├── views/           6 个路由页：启动 / 计算器 / 指南 / 攻略选择 / 攻略详情 / 兜底
│   │   ├── components/      layout · common · calculator · guide
│   │   ├── stores/          Pinia 三个：panelStore（输入真源）· presetStore · buildStore（配装方案，存 localStorage）
│   │   ├── composables/     usePanelCalc · useAgentPreset · usePanelMode · useSubStatLimit · useCascaderIcons · useScrollSpy · useNaiveTheme · useCoreSummary · useBuildIO · useBuildPanel
│   │   ├── api/             唯一网络出口
│   │   ├── types/           panel · agentPresets · weaponPresets · build
│   │   ├── constants/       calculatorOptions · discPresets · dataManifest · strategyGuides · guideContent · navigation
│   │   ├── utils/ assets/styles/   样式：tokens.css（设计令牌唯一真源）· base.css · components.css
│   │   ├── strategy/        攻略页共享渲染器 + basePanel（基础面板由预设派生）+ 唯一一份攻略样式
│   │   └── main.ts App.vue
│   ├── tests/
│   │   ├── fixtures/legacy-calculator/   只读参照实现，供三方对拍
│   │   └── support/                      测试夹具层
│   ├── tools/               三个 Node 脚本（对拍导出 / 明细 diff / CDP 截图）
│   └── public/images/       代理人 / 音擎 / 驱动盘 / 职业 / 技能 / 属性 / 等级 / 攻略独有 webp（522 张，唯一图片根）
│
├── backend/                 Python 计算服务
│   ├── src/
│   │   ├── worker.py        Cloudflare Python Worker 入口（与 zzz_panel 同级）
│   │   └── zzz_panel/
│   │       ├── core/            规则真源：纯函数、零 IO、零框架依赖
│   │       ├── api/ routes/     FastAPI，只做协议转换
│   │       ├── schemas/         Pydantic 请求/响应模型
│   │       ├── services/        用例编排，无公式
│   │       ├── presets/         加载（mtime 缓存）与语义校验
│   │       └── cli.py           命令行入口
│   └── tests/               pytest
│
├── data/                    唯一真实数据源（manifest.json 登记 5 个数据集：catalog/ 游戏事实 + rules/ 配装规则）
├── strategy/                代理人攻略数据目录（61 个，data/ 两份 JSON；页面由 Vue 共享渲染器提供）
├── docs/                    技术文档，按 overview / design / guides / reference 四类分目录（见下）
├── tools/                   开发脚本：dev.ps1 · sync_manifest.py · sync_presets.py · link_disc_effects.py · bundle_worker_data.py · normalize_strategy.py · gen_strategy_guides.py · seed_main_stat_notes.py · check_ui_contrast.py · check_ui_scale.py · check_docs.py · agent_audit.py · agent_deploy.py · dump_backend_responses.py
└── .github/skills/          数据抓取 Skill（脚本位置固定，勿移动）
```

逐目录职责见 [docs/overview/directory-layout.md](docs/overview/directory-layout.md)。

## 数据来源

代理人、音擎与驱动盘套装数据由 `.github/skills/` 下的脚本从官方 HoYoLAB Wiki 抓取生成。
**唯一真实源是 [`data/`](data/README.md)，不要手工编辑**——每次运行抓取脚本都会被整体覆盖。
数据集的**路径只写一处**：`data/manifest.json` 登记每个数据集的位置，后端、Worker 打包脚本、
前端 Vite 配置、Skill 脚本与开发工具都从它取。
例外是 `data/catalog/agent-index.json`：它是手工维护的规范 slug 表，供攻略页与 `fix-agent`
Skill 使用，不要用抓取脚本覆盖。

```powershell
python .github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py
python .github/skills/read-zzz-engine-stats/scripts/refresh_weapon_presets.py
python tools/sync_manifest.py                  # 抓取后必须再跑（数据集登记表）
python tools/bundle_worker_data.py             # 部署到 Cloudflare 前必须再跑

python .github/skills/read-zzz-drive-disc/scripts/refresh_disc_presets.py
python tools/link_disc_effects.py              # 重建驱动盘的 effect2 / effect2Note 映射
# 驱动盘 2/4 件套效果与图标；不进 Worker 产物，见 data/README.md
```

配装规则表的真源是 `backend/src/zzz_panel/core/options.py`，改了它要重新生成
`data/rules/calculator-rules.json`：

```powershell
python tools/sync_presets.py --options
```

十条数据漂移闸 + 两条 UI 闸（任一失败即说明数据与代码已经不一致，必须先修再提交）：

```powershell
python tools/sync_manifest.py --check           # 数据集登记表
python tools/sync_presets.py --options --check  # 配装规则表
python tools/bundle_worker_data.py --check      # Worker 产物
python tools/normalize_strategy.py --check
python tools/gen_strategy_guides.py --check
python tools/seed_main_stat_notes.py --check
python tools/link_disc_effects.py --check       # 驱动盘 effect2 映射
python tools/agent_audit.py --all              # 攻略页体检
python tools/check_docs.py                     # 文档链接 / 路径 / 规模数字
python tools/check_ui_contrast.py --check       # 对比度（WCAG 2.1）
python tools/check_ui_scale.py --check          # 字号 / 字重 / 间距 / 阴影
```

数据管线全貌见 [docs/guides/development.md](docs/guides/development.md) 第 6 节。

## 文档

| 文档 | 内容 |
| --- | --- |
| [docs/overview/project-overview.md](docs/overview/project-overview.md) | **集成式技术总览**：项目定位、当前规模、架构、数据流、目录地图、常用命令 |
| [docs/README.md](docs/README.md) | 文档总索引（含按角色的阅读路径） |
| [docs/completeds/structure-review.md](docs/completeds/structure-review.md) | **结构问题、证据、解决方案与修复顺序** |
| [docs/completeds/repair-plan.md](docs/completeds/repair-plan.md) | **全项目审计后的完整修复计划（英文）** |
| [docs/overview/requirements.md](docs/overview/requirements.md) | 项目范围、非目标、已知限制 |
| [docs/design/architecture.md](docs/design/architecture.md) | 架构分层与设计决策 |
| [docs/reference/api-reference.md](docs/reference/api-reference.md) | HTTP 接口契约 |
| [docs/design/data-schema.md](docs/design/data-schema.md) | 预设、规则表与驱动盘套装效果结构、校验规则 |
| [docs/design/calculation-rules.md](docs/design/calculation-rules.md) | 计算公式与规则细节 |
| [docs/overview/directory-layout.md](docs/overview/directory-layout.md) | 目录职责详解 |
| [docs/guides/development.md](docs/guides/development.md) | 开发流程、数据管线、已知坑 |
| [docs/guides/testing.md](docs/guides/testing.md) | 测试策略与三方对拍 |
| [docs/guides/deployment.md](docs/guides/deployment.md) | 构建与部署形态 |
| [docs/design/ui-system.md](docs/design/ui-system.md) | **前端视觉体系**：设计令牌、字号 / 字重 / 间距 / 阴影阶梯、颜色语义、UI 闸门 |
| [docs/design/ui-review-checklist.md](docs/design/ui-review-checklist.md) | **UI 人工验收清单**：A 机器 / B 二值 / C 锚点三档分层与截图节点 |
| [docs/design/ui-review-log.md](docs/design/ui-review-log.md) | UI 验收记录与先例表 |
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

本仓库已完成两项迁移：从「原生 HTML + 内联 JS 计算」到「Vue3 前端 + Python 计算服务」，
以及从「自建服务器 + Nginx 反代」到「Cloudflare Worker」。`frontend/src/` 与 `backend/`
是当前唯一实现，旧实现只作为对拍夹具保留在 `frontend/tests/fixtures/legacy-calculator/`。

攻略板块已扩充到 61 个数据目录（61 个已登记）。此前的命名 / UTF-8 / 模板重复问题已修复：
攻略页由 Vue 共享渲染器渲染，后端 439 项、前端 185 项测试全绿。结构审查记录见
[docs/completeds/structure-review.md](docs/completeds/structure-review.md)。

已知限制与仍在跟踪的取舍记录在 [docs/overview/requirements.md](docs/overview/requirements.md) 第 7 节；
变更历史见 [docs/changelog.md](docs/changelog.md)。
