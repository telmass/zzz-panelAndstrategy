# 开发辅助脚本

## 脚本一览

| 文件 | 用途 |
| --- | --- |
| `dev.ps1` | 一键启停本地开发服务（uvicorn :8000 + vite :5173） |
| `agent_deploy.py` | 代理人攻略一站式编排：身份解析 → 预设 → 抓取 → 图片 → 编辑骨架 → 毕业面板 → 登记表 → 闸门 → **同步收尾** |
| `agent_audit.py` | 攻略页体检：slug/图标/引用/额外能力/占位残留/生成物新鲜度，输出分级问题清单 |
| `archive_changelog.py` | changelog 归档：`docs/changelog.md` 只留最近 12 条，更早的按月归档到 `docs/changelog/<YYYY-MM>-archive.md` |
| `check_docs.py` | 文档一致性：相对链接、SKILL 里的反引号路径、失效引用，以及**数量类事实**（代理人数/音擎数/驱动盘数/规则表条目/命名映射/攻略页数/图片数与格式/前后端测试数）是否与数据源一致 |
| `fetch_agent_backgrounds.py` | 从 Gachabase 抓立绘背景到 `images/strategy/<slug>/background.webp` |
| `fetch_agent_films.py` | 从 Nanoka 抓角色框头像到 `images/strategy/<slug>/film.webp` |
| `images_to_webp.py` | 批量把 `frontend/public/images` 下的 PNG 转成 webp，并改写全仓引用 |
| `sync_manifest.py` | 刷新 / 校验 `data/manifest.json` 的派生字段（`count` / `sha256`），并查孤儿文件 |
| `sync_presets.py` | 规则表 `core/*.py` → `data/rules/calculator-rules.json`（单向） |
| `link_disc_effects.py` | 驱动盘套装 `2 件套效果 → 规则表 setOptions id` 的映射（`effect2` / `effect2Note`） |
| `bundle_worker_data.py` | 预设 `data/catalog/*.json` → `backend/src/zzz_panel/_bundled_data.py`，供 Cloudflare Worker 使用 |
| `check_ui_contrast.py` | 对比度闸门：令牌两两之间的实际对比度（WCAG 2.1） |
| `check_ui_scale.py` | 尺度闸门：字号 / 字重 / 间距 / 阴影是否都来自 `tokens.css` |
| `normalize_strategy.py` | 攻略页目录 / 数据文件名 / 图片引用归一，校验并可选重新抓取坏 JSON |
| `gen_strategy_guides.py` | 从 mapping + 攻略数据生成 `frontend/src/constants/strategyGuides.ts`（`--check` 供 CI） |
| `seed_main_stat_notes.py` | 为 `driveBuilds[].mainStats[]` 预留 `note: ""` 备注字段（`--check` 供 CI） |
| `dump_backend_responses.py` | 把 `legacy_cases.json` 的每条用例 POST 给后端并落盘，用于排查对拍差异 |

前端另有三个独立 Node 脚本，不参与构建，也不在任何 npm script 中：

| 文件 | 用途 |
| --- | --- |
| `frontend/tools/dump_legacy_cases.mjs` | 在 jsdom 里跑夹具，导出 `backend/tests/legacy_cases.json` 的期望值 |
| `frontend/tools/diff_breakdown.mjs` | 把落盘的后端响应与夹具实算明细逐行 diff，按 DOM 层级归类 |
| `frontend/tools/screenshot.mjs` | **CDP 驱动本机 Chrome** 拍 UI 验收图（任意视口宽度 + 整页 + 指定元素滚动/点击）。见 `docs/design/ui-system.md`「截图」 |

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

## 攻略数据归一

`normalize_strategy.py` 把历史攻略页的旧拼音 / 旧 slug 数据文件、图片引用与 `app.js`
数据 URL 统一到 `data/catalog/agent-index.json` 的规范 slug：

```powershell
python tools/normalize_strategy.py --check                 # 只报告，有漂移退出码 1
python tools/normalize_strategy.py --rescrape-invalid      # 重新抓取非 UTF-8 的抓取产物
python tools/normalize_strategy.py --remove-legacy         # 删除不在 mapping 中的目录
```

日常只需 `--check`；它会检查目录名、数据文件名、JSON 内的图片路径与 Skill 文档里的
`strategy/<slug>/` 示例。修复流程见
[docs/completeds/structure-review.md](../docs/completeds/structure-review.md) P0-1 / P0-2。

## 攻略登记表生成

`gen_strategy_guides.py` 从 `data/catalog/agent-index.json` 与
`strategy/<slug>/data/<slug>.json` 生成 `frontend/src/constants/strategyGuides.ts`：

```powershell
python tools/gen_strategy_guides.py          # 重新生成
python tools/gen_strategy_guides.py --check  # 与数据不一致时退出码 1
```

新增 / 改名代理人后运行生成器，不要手改 TS 数组。

## 主词条备注占位

`seed_main_stat_notes.py` 为所有攻略编辑 JSON 的
`driveBuilds[].mainStats[]` 预留 `note` 字符串：

```powershell
python tools/seed_main_stat_notes.py          # 补缺失的 note: ""
python tools/seed_main_stat_notes.py --check  # 缺字段时退出码 1
```

已有非空备注不会被覆盖；主词条表的第四列「备注」由该字段驱动。

## 数据同步脚本

| 文件 | 用途 |
| --- | --- |
| `sync_manifest.py` | 刷新 / 校验 `data/manifest.json` 的派生字段（`count` / `sha256`），并查孤儿文件 |
| `sync_presets.py` | 规则表 `core/*.py` → `data/rules/calculator-rules.json`（单向） |
| `link_disc_effects.py` | 驱动盘套装 `2 件套效果 → 规则表 setOptions id` 的映射（`effect2` / `effect2Note`） |
| `bundle_worker_data.py` | 预设 `data/catalog/*.json` → `backend/src/zzz_panel/_bundled_data.py`（Worker 产物） |

```powershell
python tools/sync_manifest.py                       # 刷新登记表的 count / sha256
python tools/sync_manifest.py --check               # 只校验，退出码 1 = 漂移或有孤儿文件
python tools/sync_presets.py --options              # 规则表 core/*.py → data/rules/calculator-rules.json
python tools/sync_presets.py --options --check      # 规则表是否已重新生成
python tools/bundle_worker_data.py                  # 生成/刷新 Worker 编译产物
python tools/bundle_worker_data.py --check          # 产物是否已过期
```

**抓取之后必跑 `sync_manifest.py`。** 抓取脚本会改变数据集的条目数与内容摘要，
不刷新登记表的派生字段，`sync_manifest.py --check` 就会红——这不是误报，正是它
在提醒「数据变了，登记没跟上」。抓取脚本自己也会打印
`next: python tools/sync_manifest.py`。

**对拍夹具不再同步。** `frontend/tests/fixtures/legacy-calculator/data/*.js` 是三方
对拍的参照实现，它的输入必须是一个**不动点**——参照实现的价值在于它是过去某个
确定时刻的正确实现；若输入跟着当前数据一起漂移，就再也说明不了「旧实现算得对」。
因此它已冻结为快照，不再由脚本生成；原先的 `--to-legacy` / `--from-legacy` 模式
随之移除。等价性改由 `backend/tests/test_legacy_fixture_snapshot.py` 断言：夹具里
用到的代理人与音擎必须与当前数据集在**语义上等值**（基础面板逐项、核心加成的
选项与每级数值、面板模式）。

规则表只有一个方向：`data/rules/calculator-rules.json` 是派生产物，前端不再持有副本。
`core` 层零第三方依赖，脚本用 `sys.path` 加 `backend/src` 直接 import，
因此**纯 stdlib 的 `python` 即可运行**，不必 `uv run`。
`backend/tests/test_options_json.py` 断言该 JSON 与 Python 当前值一致。

三个抓取脚本（两个 `refresh_*_presets.py` 加驱动盘的 `refresh_disc_presets.py`）
也**复用本模块的序列化**（`load_sync_presets()`），不各写一套——否则重新抓取后
`--check` 会一直报漂移且原因极难定位。`backend/tests/test_presets.py` 断言
`data/catalog/*.json` 已是规范形式，且两个预设脚本的 `render()` 喂入已提交数据后
能原样重现该文件。驱动盘脚本复用同一序列化。

## Worker 编译产物（部署硬闸）

```powershell
python tools/bundle_worker_data.py                            # 生成/刷新
python tools/bundle_worker_data.py --check                    # 只比对，有漂移则退出码 1
python tools/bundle_worker_data.py --data-dir <目录> --dest <目标.py>   # 覆盖输入与输出路径
```

`pywrangler` 部署时**只上传 `.py` 文件**，入口目录下的 `.json` / `.html` 会被
**静默**丢弃——部署不报错，线上却读不到。预设数据因此必须以 Python 模块的形式
跟着上线：`data/catalog/agents.json` 与 `data/catalog/weapons.json` 的原文按
「每行一个相邻字符串字面量」编译成
`backend/src/zzz_panel/_bundled_data.py` 的 `AGENTS_JSON` / `WEAPONS_JSON`。
放在 `backend/src/` 之下才会被附加，pywrangler 只附加 Worker 入口
`backend/src/worker.py` 所在目录的整棵树。

几条关键性质：

- **生成物，不提交**（`.gitignore` 已列），唯一真实源永远是仓库根的 `data/`。
- 与源文件**逐字节**一致，因此 `--check` 能可靠判定漂移；不依赖虚拟文件系统的
  任何行为，也不需要 `importlib.resources`。
- 只收这两个预设 JSON。`data/rules/calculator-rules.json` **不收**——它由前端在**构建期**经 Vite
  别名 `@data` 读真实源，根本不经过后端。
- 内容已是最新时报「已是最新」且**不写盘**，重复执行无 diff；源文件缺失时报错
  并返回 1。
- `--data-dir` / `--dest` 只供测试写到临时目录，日常不用。

`backend/tests/test_worker_bundle.py` 的 15 项覆盖逐字节还原、幂等、check 模式，
以及 `loader.py` 的编译产物回退分支（含校验同样生效、报错文案、两侧模块名对得上）。

> ⚠️ **刷新 `data/catalog/*.json` 后必须重跑**，否则线上 `/api/presets/*` 会继续供旧数据；
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
| `.github/skills/read-zzz-drive-disc/scripts/refresh_disc_presets.py` | 从官方 WIKI 抓取驱动盘 2/4 件套效果，并下载套装图标到 `frontend/public/images/discs/` |

三个脚本默认路径均相对**仓库根目录**，需在根目录执行：

```powershell
python .github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py
python .github/skills/read-zzz-engine-stats/scripts/refresh_weapon_presets.py
python .github/skills/read-zzz-drive-disc/scripts/refresh_disc_presets.py
```

驱动盘脚本与另两个的区别：抓完**不需要**再跑 `bundle_worker_data.py`（不进 Worker 产物），
但**仍要**跑 `sync_manifest.py`（它同样登记在 `data/manifest.json` 里）；
也不进 `_bundled_data.py`——计算器不消费它（当前消费者是攻略页按
`/images/discs/…` 取图，见 data/README.md）。
