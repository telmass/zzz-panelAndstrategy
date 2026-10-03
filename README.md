# 代理人面板计算器

绝区零（Zenless Zone Zero）代理人面板计算工具。

本仓库已完成从「原生 HTML + 内联JS 计算」到「Vue3 前端 + Python 计算服务」的迁移。
`frontend/src/` 与 `backend/` 是当前唯一实现；旧的原生实现已删除，仅在
`frontend/tests/fixtures/legacy-calculator/` 保留一份**只读**的计算部分，
供三方对拍测试作为参照基准（见 [docs/legacy-pages.md](docs/legacy-pages.md)）。

## 快速开始

### 使用计算器

```powershell
pwsh tools/dev.ps1            # start（默认）/ stop / restart / status
```

打开 http://localhost:5173/ ：启动界面，`/calculator` 统一计算器，
`/guide` 面板计算方式学习指南。计算由后端 FastAPI 完成，前端不再本地计算。

### Python 计算库

```powershell
uv sync                    # 安装依赖
uv run zzz-panel           # 运行示例计算
uv run python -m zzz_panel # 等价入口
uv run pytest              # 运行回归测试
```

### 单独启动（调试用）

后端 `uv run uvicorn zzz_panel.api.app:app --port 8000`，前端 `npm run dev`。
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
│   │   └── fixtures/legacy-calculator/  只读参照实现，供三方对拍，不参与构建
├── backend/                   Python 计算服务
│   ├── src/zzz_panel/
│   │   ├── core/              纯计算层（零 IO、零 Web 框架）
│   │   ├── api/               FastAPI 传输层
│   │   ├── schemas/           Pydantic 模型
│   │   ├── services/          用例编排
│   │   └── presets/           预设加载与校验
│   └── tests/                 pytest
├── data/                      预设 JSON 与规则表的唯一真实源
├── docs/                      项目文档
├── tools/                     开发辅助脚本
└── .github/skills/            数据抓取 Skill（脚本位置固定，勿移动）
```

完整说明见 [docs/directory-layout.md](docs/directory-layout.md)。

## 数据来源

代理人与音擎预设由 Skill 脚本从米游社官方 WIKI 抓取生成。
**唯一真实源是仓库根 [`data/*.json`](data/README.md)，不要手工编辑**——
每次运行抓取脚本都会被整体覆盖。

`frontend/tests/fixtures/legacy-calculator/data/*.js` 是对拍夹具用的派生产物，由
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
- [docs/legacy-pages.md](docs/legacy-pages.md) 旧原生页面的来历、删除记录与遗留夹具
