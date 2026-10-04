# 开发辅助脚本

## 脚本一览

| 文件 | 用途 |
| --- | --- |
| `dev.ps1` | 一键启停本地开发服务（uvicorn :8000 + vite :5173） |
| `sync_presets.py` | 预设 `data/*.json` ↔ 对拍夹具 `data/*.js`；规则表 `core/*.py` → `data/options.json` |
| `bundle_worker_data.py` | 预设 `data/*.json` → `backend/src/zzz_panel/_bundled_data.py`，供 Cloudflare Worker 使用 |
| `dump_backend_responses.py` | 把 `legacy_cases.json` 的每条用例 POST 给后端并落盘，用于排查对拍差异 |

前端另有两个独立 Node 诊断脚本，不参与构建，也不在任何 npm script 中：

| 文件 | 用途 |
| --- | --- |
| `frontend/tools/dump_legacy_cases.mjs` | 在 jsdom 里跑夹具，导出 `backend/tests/legacy_cases.json` 的期望值 |
| `frontend/tools/diff_breakdown.mjs` | 把落盘的后端响应与夹具实算明细逐行 diff，按 DOM 层级归类 |

## 一键启停

```powershell
pwsh tools/dev.ps1            # start（默认）
pwsh tools/dev.ps1 start
pwsh tools/dev.ps1 stop
pwsh tools/dev.ps1 restart
pwsh tools/dev.ps1 status
```

一条命令同时拉起前后端，两个日志按来源着色实时输出；`Ctrl+C` 等同 `stop`。
运行状态写在 `.dev/pids.json`，日志在 `.dev/logs/`（已 gitignore）。

已验证：`start` / `stop` / `restart` / `status` 四个动作，以及
`/api/health`、`/api/presets/agents`、`/calculator` 三个端点。

### 三个必须绕开的坑

- **`.ps1` 必须存成带 BOM 的 UTF-8**。Windows PowerShell 5.1 按 GBK 读无 BOM 的
  文件，中文字节被拆坏后直接抛 `ParserError`（报错信息本身也是乱码，容易误判为语法错误）。
  `pwsh` 7+ 无此问题，但要在 5.1 上跑就得带 BOM。
- **进程树有两层**。`uv run uvicorn` 是 `uv` → `python/uvicorn`，
  `npm run dev` 是 `npm.cmd` → `npm-cli` → `vite`。`taskkill /T` 的主进程一旦先死，
  其子孙会被 reparent，从已死的 PID 出发就找不到它们，于是 python 继续占着 8000。
  `stop` 因此分三层：`taskkill /T` → `taskkill /T /F` → 按命令行特征清理残留。
  与 `frontend/tests/support/backend.ts` 的 `killOrphanUvicorn()` 同思路。
- **原生命令的 stderr 会被升级成终止性错误**。脚本级
  `$ErrorActionPreference = 'Stop'` 下，`taskkill` 输出的
  `ERROR: ... could not be terminated` 会中断整个 `stop`，再也走不到强杀与兜底。
  `Invoke-TaskKill()` 临时降级为 `Continue` 再还原。

### 变量名不要撞参数名

PowerShell 变量大小写不敏感：`Start-Service` 里 `foreach ($file in ...)` 会覆盖
同名参数 `$File`，结果把日志文件当可执行文件去启动。改名 `$logPath` 即可。

残留清理用**多个片段同时命中**（如 `zzz_panel` + `uvicorn`、`vite` + `frontend`）
而不是单一关键词，避免误杀同机其它项目的同名进程。

## 双向同步脚本

| 文件 | 用途 |
| --- | --- |
| `sync_presets.py` | 预设 `data/*.json` ↔ `frontend/tests/fixtures/legacy-calculator/data/*.js`；规则表 `core/*.py` → `data/options.json` |

```powershell
python tools/sync_presets.py --from-legacy          # 夹具 JS → JSON（一次性引导）
python tools/sync_presets.py --to-legacy            # 预设 JSON → 夹具 JS（长期方向）
python tools/sync_presets.py --options              # 规则表 core/*.py → data/options.json
python tools/sync_presets.py --to-legacy --check    # 只报漂移，退出码 1 = 不同步
python tools/sync_presets.py --options --check      # 规则表是否已重新生成
```

预设的两个方向都先把数据规范化到脚本内定义的键序再写出，因此重复执行不产生 diff，
且 `夹具 → JSON → 夹具` 字节一致（已验证，可作无损性回归检查）。

脚本中的「legacy」特指只读参照实现夹具
`frontend/tests/fixtures/legacy-calculator/`——旧的原生页面已删除，
但三方对拍仍在读那份 `data/*.js`。

规则表只有一个方向：`data/options.json` 是派生产物，前端不再持有副本。
`core` 层零第三方依赖，脚本用 `sys.path` 加 `backend/src` 直接 import，
因此**纯 stdlib 的 `python` 即可运行**，不必 `uv run`。
`backend/tests/test_options_json.py` 断言该 JSON 与 Python 当前值一致。

两个抓取脚本 `refresh_*_presets.py` 也**复用本模块的序列化**（`load_sync_presets()`），
不各写一套——否则重新抓取后 `--check` 会一直报漂移且原因极难定位。
`backend/tests/test_presets.py` 断言 `data/*.json` 已是规范形式，
且两个脚本的 `render()` 喂入已提交数据后能原样重现该文件。

脚本内置一个 JS 字面量解析器，只支持抓取脚本产出的子集：单引号字符串、
**无转义序列**、键名不引号。遇到反斜杠会显式报错而非猜测。两个易踩的点：

- 剥注释必须字符串优先，否则 URL 里的 `//` 会被当行注释，把 `source` 整条截断。
- 抓取脚本对**对象键**也输出尾随逗号，对「值全为标量的扁平对象数组」
  （`unmodeledBaseStats`）则整元素单行渲染。这两条规则不还原就无法字节一致。

## Worker 编译产物（部署硬闸）

```powershell
python tools/bundle_worker_data.py                            # 生成/刷新
python tools/bundle_worker_data.py --check                    # 只比对，有漂移则退出码 1
python tools/bundle_worker_data.py --data-dir <目录> --dest <目标.py>   # 覆盖输入与输出路径
```

`pywrangler` 部署时**只上传 `.py` 文件**，入口目录下的 `.json` / `.html` 会被
**静默**丢弃——部署不报错，线上却读不到。预设数据因此必须以 Python 模块的形式
跟着上线：`data/agent-presets.json` 与 `weapon-presets.json` 的原文按
「每行一个相邻字符串字面量」编译成
`backend/src/zzz_panel/_bundled_data.py` 的 `AGENTS_JSON` / `WEAPONS_JSON`。
放在 `backend/src/` 之下才会被附加，pywrangler 只附加 Worker 入口
`backend/src/worker.py` 所在目录的整棵树。

几条关键性质：

- **生成物，不提交**（`.gitignore` 已列），唯一真实源永远是仓库根的 `data/`。
- 与源文件**逐字节**一致，因此 `--check` 能可靠判定漂移；不依赖虚拟文件系统的
  任何行为，也不需要 `importlib.resources`。
- 只收这两个预设 JSON。`options.json` **不收**——它由前端在**构建期**经 Vite
  别名 `@data` 读真实源，根本不经过后端。
- 内容已是最新时报「已是最新」且**不写盘**，重复执行无 diff；源文件缺失时报错
  并返回 1。
- `--data-dir` / `--dest` 只供测试写到临时目录，日常不用。

`backend/tests/test_worker_bundle.py` 的 15 项覆盖逐字节还原、幂等、check 模式，
以及 `loader.py` 的编译产物回退分支（含校验同样生效、报错文案、两侧模块名对得上）。

> ⚠️ **刷新 `data/*.json` 后必须重跑**，否则线上 `/api/presets/*` 会继续供旧数据；
> 干净 clone 上从未生成过则没有编译产物，路由捕获 `PresetLoadError` 返回 **503**。

## 第 3 步新增的诊断脚本

排查前后端对拍差异时用，**不做断言**，退出码不代表通过与否。

| 文件 | 用途 |
| --- | --- |
| `dump_backend_responses.py` | 把 `backend/tests/legacy_cases.json` 的每条用例 POST 给后端，落盘完整响应 JSON |
| `../frontend/tools/diff_breakdown.mjs` | 把落盘 JSON 与参照实现实算明细逐行 diff，按 DOM 层级归类 |

典型流程：先跑前者拿后端响应，再跑后者看差异明细，最后回到 `core/` 下对应模块修正。

## 不放这里的东西

**数据抓取脚本刻意保留在 `.github/skills/*/scripts/`**，因为 `SKILL.md` 依赖它们的
相对路径（`scripts/refresh_agent_presets.py`）。移动会破坏 Skill 契约。

| 脚本 | 作用 |
| --- | --- |
| `.github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py` | 从官方 WIKI 抓取代理人 60 级面板与满级核心加成 |
| `.github/skills/read-zzz-engine-stats/scripts/refresh_weapon_presets.py` | 从官方 WIKI 抓取音擎满级基础值与固定副词条 |

两者默认路径均相对**仓库根目录**，需在根目录执行：

```powershell
python .github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py
python .github/skills/read-zzz-engine-stats/scripts/refresh_weapon_presets.py
```
