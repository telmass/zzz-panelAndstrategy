# 代理人面板计算器

绝区零（Zenless Zone Zero）代理人面板计算工具。

本仓库正在从「原生 HTML + 内联 JS 计算」迁移到「Vue3 前端 + Python 计算服务」。
迁移期间两套实现并存：`frontend/legacy/` 是当前可用的原生实现，
`frontend/src/` 与 `backend/` 是迁移目标骨架。

## 快速开始

### 使用计算器（当前可用，无需构建）

直接用浏览器打开：

```
frontend/legacy/pages/index.html          启动界面
frontend/legacy/pages/calculator.html     统一计算器
frontend/legacy/pages/calculator.html?mode=rupture   命破模式
frontend/legacy/pages/calculator.html?mode=fengyu    锋御模式
frontend/legacy/pages/guide.html          面板计算方式学习指南
```

仓库根目录保留了 6 个同名中文重定向页，用于兼容旧书签，Vue3 迁移完成后删除。

### Python 计算库（当前可用）

```powershell
uv sync                    # 安装依赖
uv run zzz-panel           # 运行示例计算
uv run python -m zzz_panel # 等价入口
uv run pytest              # 运行回归测试
```

### 本地开发服务

前后端都已实现，用一条命令同时拉起（uvicorn :8000 + vite :5173，日志实时输出，
`Ctrl+C` 停止）：

```powershell
pwsh tools/dev.ps1            # start（默认）/ stop / restart / status
```

打开 http://localhost:5173/calculator 。单独启动时后端用
`uv run uvicorn zzz_panel.api.app:app --port 8000`，前端用 `npm run dev`。
详见 [tools/README.md](tools/README.md)。

## 目录结构

```
test/
├── frontend/                  前端工程（Vite + Vue3 + TS）
│   ├── public/images/         静态图片（Vite 原样拷贝，不支持 import）
│   ├── src/                   Vue3 源码
│   │   ├── assets/            经 Vite 处理的图片/字体/全局样式
│   │   ├── components/        layout / common / calculator
│   │   ├── views/             路由级页面
│   │   ├── router/ stores/ composables/ api/ types/ constants/ utils/ data/
│   │   └── main.ts App.vue
│   ├── tests/                 Vitest
│   └── legacy/                过渡期原生实现，迁移完成后整体删除
│       ├── pages/ styles/ scripts/ data/
├── backend/                   Python 计算服务
│   ├── src/zzz_panel/
│   │   ├── core/              纯计算层（零 IO、零 Web 框架）
│   │   ├── api/               FastAPI 传输层（预留）
│   │   ├── schemas/           Pydantic 模型（预留）
│   │   ├── services/          用例编排（预留）
│   │   └── presets/           预设加载与校验（预留）
│   └── tests/                 pytest
├── data/                      预设 JSON 的唯一真实源（待生成）
├── docs/                      项目文档
├── tools/                     开发辅助脚本
└── .github/skills/            数据抓取 Skill（脚本位置固定，勿移动）
```

完整说明见 [docs/directory-layout.md](docs/directory-layout.md)。

## 数据来源

代理人与音擎预设由 Skill 脚本从米游社官方 WIKI 抓取生成。
**唯一真实源是仓库根 [`data/*.json`](data/README.md)，不要手工编辑**——
每次运行抓取脚本都会被整体覆盖。

`frontend/legacy/data/*.js` 是 legacy 页面用的派生产物，由
`tools/sync_presets.py --to-legacy` 从 JSON 反向生成，同样不可手工编辑。

刷新方式（需在仓库根目录执行，抓取后必须再跑一次同步）：

```powershell
python .github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py
python .github/skills/read-zzz-engine-stats/scripts/refresh_weapon_presets.py
python tools/sync_presets.py --to-legacy
```

改了配装规则表（`backend/src/zzz_panel/core/*.py`）后重新生成前端用的规则表：

```powershell
python tools/sync_presets.py --options
```

## 相关文档

- [docs/architecture.md](docs/architecture.md) 架构与数据流
- [docs/directory-layout.md](docs/directory-layout.md) 目录职责详解
- [docs/calculation-rules.md](docs/calculation-rules.md) 面板计算规则
- [docs/data-schema.md](docs/data-schema.md) 预设数据与 API 契约
- [docs/migration-vue3.md](docs/migration-vue3.md) Vue3 迁移进度与步骤
- [docs/legacy-pages.md](docs/legacy-pages.md) legacy 页面说明与删除时机
