# 开发指南

面向要动手改这个仓库的人。命令均以**仓库根目录**为基准，PowerShell 语法。

## 1. 环境要求

| 工具 | 版本 | 校验方式 | 用途 |
| --- | --- | --- | --- |
| Python | >= 3.13 | `python --version` | 后端与抓取脚本 |
| uv | 最新 | `uv --version` | Python 依赖管理 |
| Node.js | 建议 20+ | `node --version` | 前端构建与测试 |
| npm | 随Node | `npm --version` | 前端依赖管理 |

后端用 uv，前端用 npm。**Python 版本是硬锁定的**（`.python-version` = 3.13）；
Node 只在本仓库文档里约定为 20+，没有 `engines` 字段或 `.nvmrc` 之类的机器可读约束。

## 2. 首次安装

```powershell
uv sync                # 安装 Python 依赖（含 dev 组：pytest、httpx、uvicorn[standard]）
cd frontend
npm install            # 含 naive-ui
cd ..
```

部署到 Cloudflare 还需要 Worker 工具链，它在单独的 `worker` 组，`uv sync` **不会**装：

```powershell
uv sync --group worker  # workers-py + workers-runtime-sdk，即 pywrangler
```

## 3. 运行

### 一条命令拉起前后端（推荐）

```powershell
pwsh tools/dev.ps1                # start（默认）
pwsh tools/dev.ps1 stop
pwsh tools/dev.ps1 restart
pwsh tools/dev.ps1 status
```

- 后端 `uvicorn` 监听 `:8000`，前端 Vite 监听 `:5173`
- Vite 把 `/api` 代理到 `http://127.0.0.1:8000`，**因此开发期不涉及 CORS**
- 打开 <http://localhost:5173/>
- 日志实时输出，`Ctrl+C` 停止

> Windows 执行策略拦截时用：
> `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\dev.ps1 start`

### 单独启动（调试用）

```powershell
uv run uvicorn zzz_panel.api.app:app --port 8000     # 后端
cd frontend; npm run dev                              # 前端
```

### 只跑后端计算（不启服务）

```powershell
uv run zzz-panel-and-strategy  # 等价于 uv run python -m zzz_panel
```

固定跑一组示例输入并打印 12 行结果。不接受参数——它是规则的可执行文档，
不是通用 CLI。

### 本地预览 Worker（可选）

想在本地看线上形态的真实行为，而不是先部署再试错：

```powershell
python tools/bundle_worker_data.py
cd frontend; npm run build; cd ..
uv run --group worker pywrangler dev
```

`pywrangler dev` 跑的是 workerd + Pyodide。首次运行要下载 Pyodide 解释器，较慢。

## 4. 测试

```powershell
uv run pytest                          # 后端 109 项
cd frontend; npm run test              # 前端 86 项
```

前端另外两个脚本：

```powershell
npm run typecheck      # vue-tsc --noEmit
npm run test:watch     # vitest 监听模式
```

**要求：pytest 必须 0 skip。** 任何 skip 都意味着某道护栏没真正执行——
尤其 `test_fmt_parity.py`，它会因「node 不可用」以外的原因跳过，
详见 [testing.md](testing.md)。看到 skip 要查原因，不要忽略。

> ⚠️ **不要并行跑 `uv run pytest` 与 `npm run test`。** 后者会拉起真实 uvicorn，
> 两者同时触发 `uv` 重装本包时 uvicorn 20 秒内报不出端口，表现为 4 个对拍用例
> 红灯——原因与对拍无关。串行执行。

## 5. 静态检查

| 命令 | 检查什么 |
| --- | --- |
| `npm run typecheck` | 前端 TS 类型（`strict` + `noUnusedLocals` + `noUnusedParameters`） |
| `npm run build` | 类型检查 + 打包 |
| `git diff --check` | 行尾空白与冲突标记 |

后端**没有配置任何 linter 或类型检查器**（无 ruff / flake8 / pylint / mypy）。
后端唯一的静态约束是 `backend/tests/` 里的 pytest。新增代码请遵循既有风格：
类型注解齐全、模块 docstring 说明职责与约束、行宽约 100。

## 6. 数据管线

`data/` 下的 JSON 是**唯一真实源**，但它们都是生成物，改了源头要重新生成。

```
Skill 抓取脚本                  core/options.py
（网络 → 官方Wiki）              （规则表权威源）
        │                              │
        ▼                              ▼
data/agent-presets.json      data/options.json
data/weapon-presets.json            │
        │                            │
        │ sync_presets.py --to-legacy│ 前端 @data 别名直接 import
        ▼                            ▼
tests/fixtures/legacy-calculator/  frontend/src/constants/
  data/*.js（对拍夹具）             calculatorOptions.ts

        （上面两个预设 JSON 还有第三条分支：部署到 Cloudflare 时）
        │  tools/bundle_worker_data.py
        ▼
backend/src/zzz_panel/_bundled_data.py（gitignored）
        │  pywrangler 只上传 .py，.json 会被静默丢弃
        ▼
Cloudflare Worker → GET /api/presets/*
```

### 刷新预设数据

```powershell
python .github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py
python .github/skills/read-zzz-engine-stats/scripts/refresh_weapon_presets.py
python tools/sync_presets.py --to-legacy        # 必须再跑，否则夹具漂移
```

抓取脚本的输出是**整体覆盖**，不是增量。它会打印 `next: python tools/sync_presets.py --to-legacy`。

### 改了预设数据、且要部署到 Cloudflare

刷新或改过 `data/agent-presets.json` / `data/weapon-presets.json` 之后，必须再编译一次：

```powershell
python tools/bundle_worker_data.py             # 生成包内镜像（gitignored）
python tools/bundle_worker_data.py --check     # 漂移闸：产物与源不一致时退出码 1
```

漏掉的症状：页面能开、`/api/panel/calc` 200，但两个级联选择器只有职业分组、
`/api/presets/*` 返回 503（干净 clone 因为压根没有产物，也一定是 503）。
细节见 [deployment.md](deployment.md) 5.3。

`data/options.json` **不参与**这一步——它由前端在构建期经 `@data` 读真实源。

### 改了规则表

规则表的唯一权威源在 `backend/src/zzz_panel/core/options.py` 与 `core/constants.py`：

```powershell
python tools/sync_presets.py --options       # 重新生成 data/options.json
```

改完必须跑 `uv run pytest`。`backend/tests/test_options_json.py` 会断言 JSON
与 Python 当前值一致——忘了重新生成就会失败，这是设计意图。

### 同步脚本的四个模式

| 命令 | 方向 | 用途 |
| --- | --- | --- |
| `--from-legacy` | 夹具 `data/*.js` → `data/*.json` | 一次性引导，现已退化 |
| `--to-legacy` | `data/*.json` → 夹具 `data/*.js` | **常规流程**，抓取后必跑 |
| `--options` | `core/*.py` → `data/options.json` | 单向，改规则表后跑 |
| `--check` | 只比对不写，有漂移退出码 1 | CI 门禁 |

`--to-legacy` 与 `--from-legacy` 的往返是**字节一致**的，因此可用来证明转换无损。

数据抓取脚本**刻意不放 `tools/`**——它们是 Skill 契约的一部分，
必须留在 `.github/skills/*/scripts/`。

## 7. 改计算规则的正确姿势

计算规则真源在 `backend/src/zzz_panel/core/`。改动的落点通常是：

| 想改什么 | 改哪里 |
| --- | --- |
| 某个模式专属公式 | `core/modes.py` |
| 12 行基础面板的公式 | `core/panel.py` 的 `_apply_totals` |
| 加成如何累加、来源如何记录 | `core/modifiers.py` |
| 明细文案的分段与换行 | `core/breakdown.py` |
| 数字格式化（取整、千分位） | `core/fmt.py` |
| 规则表条目 | `core/options.py`，**然后跑 `--options`** |

改完**必须**跑 `npm run test`（在前端目录）。其中
`tests/legacy-parity.spec.ts` 会拉起真实后端，与只读参照实现逐字符比对结果与明细。
该测试失败说明新公式与旧实现行为不一致——先确认是有意改动，再决定是否更新夹具。

> ⚠️ **不要为了让测试变绿去改 `tests/fixtures/legacy-calculator/`。**
> 它是对拍基准，改了三方对拍就变成「自己和自己比」，永远不会失败。

## 8. 常见坑

这些都是实际踩过的，改动相关区域前值得先看。

### naive-ui 组件的测试与主题

代理人与音擎选择器都用 `n-cascader`，两者的选项图标与菜单文案由
`composables/useCascaderIcons.ts` 共用。改动相关代码前先知道三件事：

- 主题走 `App.vue` 的 `n-config-provider`，颜色由 `composables/useNaiveTheme.ts`
  **从 `tokens.css` 读 CSS 变量**转成 `themeOverrides`。新增 naive 组件时在
  `themeOverrides` 里补映射，**不要写死 hex**。
- **组件测试都绕过 `App.vue`**，因此测试里看不到主题映射，走的是 naive 默认色。
  这是已知的覆盖缺口，不是 bug；要给主题加断言得单独 mount 一层 provider。
- naive 的浮层依赖 `matchMedia` / `ResizeObserver` / `IntersectionObserver`，
  jsdom 一个都没有，全局桩在 `frontend/tests/support/setup.ts`。
  浮层 Teleport 到 `body`（`wrapper.find()` 查不到），选项在 `n-virtual-list` 里、
  jsdom 无布局时一项都不渲染——详见 [testing.md](testing.md) 第 5 节。

### Windows 上 `uv run` 是两层进程

`uv` → Python → uvicorn。只终止 `uv` 会留下孤儿 uvicorn 拖住 Vitest 退出。
`frontend/tests/support/backend.ts` 用 `killOrphanUvicorn()` 在三条路径上兜底：
正常停止、健康检查失败、未解析到端口。

### uvicorn 启动行在 stderr

`Uvicorn running on http://host:port` 走 stderr，且 `--log-level warning` 会把它
整行抑制掉。测试夹具必须监听 stderr 并以 info 级别启动，否则永远等不到端口。

### jsdom 联跑夹具时的作用域

`tests/legacy-parity.spec.ts` 把四个脚本**合并成一段内联脚本**再注入。
原因：真实浏览器中多个 `<script>` 共享全局词法作用域，而独立 `eval()` 各自成域，
`const CORE_OPTIONS` 将不可见。同理必须 `runScripts: 'dangerously'`，
否则 HTML 内联的 `onchange` 属性不会被编译，联动逻辑不执行。

### 每个对拍用例都要重建夹具窗口

夹具的 `clearAgentPresetFields` 只重置基础面板、核心与二件套，**不触碰**4/5/6 号
主词条与副词条。上一个用例遗留的配装会污染下一个。

### `@data` 别名要两处同步

`vite.config.ts` 与 `tsconfig.json` 各有一份定义，改一处必须改另一处，
否则 IDE 与构建行为不一致。且因为 `@data` 指向 `frontend/` 之外，
`server.fs.allow` 必须显式放行仓库根。

### PowerShell 读 UTF-8 中文 JSON

`Get-Content file.json -Raw | ConvertFrom-Json` 在 PowerShell 5.1 下会因编码丢失
中文而报「传入的对象无效」。这不是文件的问题，读 JSON 时加 `-Encoding UTF8`，
或直接用 Node / Python 读。

### wrangler 不读 Windows 系统代理

部署时如果浏览器能上 Cloudflare、命令却报
`The request to Cloudflare's API timed out`，原因是 wrangler 是 Node 程序，
不走 WinINET 系统代理。显式给三个环境变量（`NODE_USE_ENV_PROXY`、`HTTPS_PROXY`、
`HTTP_PROXY`）即可，写法见 [deployment.md](deployment.md) 5.8。

### `wrangler.jsonc` 必须是纯 ASCII

pywrangler 用 Python 的**本地编码**（中文 Windows 是 GBK）解析该文件，
任何非 ASCII 字节都会让部署在解析阶段就失败。所以它的注释一律英文，
中文说明只放在 [deployment.md](deployment.md) 里。

### 修改夹具的路径会连带三处

夹具从 `frontend/legacy/` 移到 `tests/fixtures/legacy-calculator/` 时，
以下位置都改了路径，一起搬才不会出现「三方对拍静默skip」：

| 文件 | 引用 |
| --- | --- |
| `frontend/tests/legacy-parity.spec.ts` | `LEGACY_ROOT` |
| `frontend/tools/dump_legacy_cases.mjs` | `LEGACY_ROOT` |
| `frontend/tools/diff_breakdown.mjs` | `LEGACY_ROOT` |
| `backend/tests/test_fmt_parity.py` | `LEGACY_JS` |
| `tools/sync_presets.py` | `LEGACY_DIR` |
| `.github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py` | `--config` 默认值 |

## 9. 诊断工具

排查数值差异时用，**不要当测试跑**（它们不做断言，退出码不代表通过）：

| 工具 | 回答什么问题 |
| --- | --- |
| `python tools/dump_backend_responses.py` | 后端这一侧到底算出了什么 |
| `cd frontend; node tools/diff_breakdown.mjs <legacy_cases.json> <backend_resp.json> [场景]` | 差在哪个字段、差了几个数量级 |
| `cd frontend; node tools/dump_legacy_cases.mjs <out.json>` | 重新导出参照实现的抽样用例 |

典型流程：先跑 `dump_backend_responses.py` 拿响应，再跑 `diff_breakdown.mjs`
看差异明细，最后回到对应 `core` 模块修正。

## 10. 提交前检查

```powershell
uv run pytest                      # 后端 109 项，0 skip
cd frontend
npm run typecheck                  # 类型
npm run test                       # 86 项，含三方对拍（与 pytest 串行跑）
cd ..
python tools/sync_presets.py --to-legacy --check
python tools/sync_presets.py --options --check
python tools/bundle_worker_data.py --check
git diff --check
```

部署（形态 D）时再加两步：`cd frontend; npm run build`，以及带代理的
`uv run --group worker pywrangler deploy`。完整流程见
[deployment.md](deployment.md) 第 5 节。

`pylock.toml` 是 Worker 环境的锁文件，**必须提交**；它与 `uv.lock` 都要在版本控制里。

## 11. 相关文档

- [requirements.md](requirements.md) —— 项目做什么、约束与已知限制
- [architecture.md](architecture.md) —— 分层与依赖方向
- [api-reference.md](api-reference.md) —— HTTP 接口
- [data-schema.md](data-schema.md) —— 预设与选项表结构
- [calculation-rules.md](calculation-rules.md) —— 计算公式
- [directory-layout.md](directory-layout.md) —— 目录职责
- [testing.md](testing.md) —— 测试策略
- [deployment.md](deployment.md) —— 部署
- [changelog.md](changelog.md) —— 变更记录