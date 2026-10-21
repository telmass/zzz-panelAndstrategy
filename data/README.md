# 数据集（唯一真实源）

本目录下的 JSON 是**代理人/音擎预设、配装规则表与驱动盘套装效果数据的唯一真实源**。

## `manifest.json`：路径的唯一真源

数据集的**路径只在这里声明一次**。后端 loader、Worker 打包脚本、前端 Vite 配置、
四个 Skill 抓取脚本与十余个开发工具都从它取路径，不再各记一份文件名——改一次路径
要动十几处、漏改的那处只会静默读到旧路径或 404，是很难排查的一类故障。

| 字段 | 含义 |
| --- | --- |
| `path` | 相对 `data/` 的路径 |
| `role` | `source`（真源）/ `generated`（生成物） |
| `maintained` | `skill`（抓取脚本维护）/ `manual`（手工维护）/ `code`（由代码维护） |
| `generator` | 产出这个文件的脚本；手工维护的为 `null` |
| `schema` | 该数据集的形状定义在哪 |
| `distribution` | 谁消费它：后端接口 / Worker 编译产物 / 前端构建期 / 工具 |
| `worker` | 是否编译进 Worker 的数据模块 |
| `count` / `sha256` | **派生值**，由 `tools/sync_manifest.py` 写入与校验 |

```powershell
python tools/sync_manifest.py            # 刷新 count 与 sha256
python tools/sync_manifest.py --check    # 只校验，有漂移或孤儿文件则退出码 1
```

`sync_manifest.py --check` 同时会检查 `data/` 下**没有未登记的文件**——某个工具
偷偷把产物写进 `data/` 而忘了登记，会在这里被点名。

## 数据集与各自流向

| 数据集 | 路径 | 维护 | 方向 |
| --- | --- | --- | --- |
| `agents` | `catalog/agents.json` | 抓取脚本 | 抓取脚本写 JSON；`tools/bundle_worker_data.py` 把它编译进 Worker |
| `weapons` | `catalog/weapons.json` | 抓取脚本 | 同上 |
| `drive-discs` | `catalog/drive-discs.json` | 抓取脚本 | 抓取脚本写 JSON 与套装图标；计算器**按套装**选择器读它（构建期静态 import）；**不编译进 Worker** |
| `agent-index` | `catalog/agent-index.json` | **手工维护** | 规范 slug / 中英文名映射；`fix-agent` Skill 与攻略页目录名以它为准 |
| `calculator-rules` | `rules/calculator-rules.json` | 代码 | **单向生成**：`sync_presets.py --options` 从 `core/*.py` 生成 |

```powershell
python tools/sync_presets.py --options                # core/*.py → calculator-rules.json
python tools/sync_presets.py --options --check        # 只报漂移
python .github/skills/read-zzz-drive-disc/scripts/refresh_disc_presets.py   # 驱动盘套装
```

`calculator-rules.json` 带 `_generated` 字段声明勿手改（JSON 没有注释语法），
并带 `schemaVersion` 声明形状版本。`backend/tests/test_options_json.py` 断言它与
Python 规则表一致，改了 `core/*.py` 忘了重新生成就会测试失败。

规则表**不经接口**，前端在**构建期**通过 `@data` 别名直接 import 该文件——
下拉框要瞬时可用，不能等一次 HTTP 往返。预设则相反，走 `GET /api/presets/*`，
因为数据量大且需刷新。取舍见
[docs/design/architecture.md](../docs/design/architecture.md) 第 3 节「预设数据与规则表：故意不对称」。

> **前端为什么不用 manifest 拼路径**：Vite 的静态导入要求路径可静态分析，没法在
> 运行时按登记表拼 `import()`。前端仍用字面量 `import` 读数据文件，登记表只作为
> **参照**——`frontend/tests/data-manifest.spec.ts` 断言「静态导入的文件 = 登记项」，
> 漏改时测试会指名道姓地失败。

## Worker 部署：磁盘之外的编译产物

`pywrangler` 部署时**只上传 `.py` 文件**，放在包里的 `.json` 会被静默丢弃
（不报错，只是线上读不到）。因此 `tools/bundle_worker_data.py` 把
`agents.json` 与 `weapons.json` 的原文编译进
`backend/src/zzz_panel/_bundled_data.py` 的两个字符串常量
`AGENTS_JSON` / `WEAPONS_JSON`。该模块是**生成物，已 gitignore**；
规则表不收——它只在前端构建期被读，根本不经过后端。

```powershell
python tools/bundle_worker_data.py          # 生成/刷新编译产物
python tools/bundle_worker_data.py --check  # 漂移闸，退出码非 0 即产物已过期
```

`presets/loader.py` 的取值顺序是**磁盘优先、编译产物兜底**：

| 顺序 | 来源 | 何时命中 |
| --- | --- | --- |
| 1 | 磁盘上的 `data/`。`manifest.data_dir()` 依次尝试 `ZZZ_PANEL_DATA_DIR` 环境变量、从 `__file__` 上溯找同时含 `pyproject.toml` 与 `data/manifest.json` 的祖先目录 | 本地开发、仓库内的可编辑安装 |
| 2 | `zzz_panel._bundled_data` 的模块常量 | 包被上传到 Worker、仓库的 `data/` 不跟着上线时的**唯一一条路** |

两条路走**同一套**结构与语义校验，编译产物不享有豁免。

> ⚠️ **刷新 `agents.json` 或 `weapons.json` 后必须重跑
> `python tools/bundle_worker_data.py`。** 生成物不进版本库，不重跑就部署，
> 线上 `/api/presets/*` 会继续供旧数据；干净 clone 上直接部署则没有编译产物，
> 路由捕获 `PresetLoadError` 返回 **503**。两种症状都不报错在部署环节，
> `--check` 退出码非 0 即表示产物已过期。

## 对拍夹具：冻结的参照实现

`frontend/tests/fixtures/legacy-calculator/data/*.js` 是三方对拍（legacy ≡ Vue3 ≡
Python）的**参照实现**，它的输入必须是一个**不动点**——参照实现的价值在于它是
过去某个确定时刻的正确实现；若它的输入跟着当前数据一起变，就再也说明不了
「旧实现算得对」。

因此该夹具已**冻结为快照**，不再由脚本生成（原 `sync_presets.py --to-legacy` /
`--from-legacy` 模式已移除）。守门换成
`backend/tests/test_legacy_fixture_snapshot.py`：它断言夹具里用到的代理人与音擎，
与当前数据集在**语义上等值**（基础面板逐项、核心加成的选项与每级数值、面板模式）。

| | 本目录 | 夹具 `data/*.js` |
| --- | --- | --- |
| 格式 | JSON | JS 字面量（`window.AGENT_PRESETS`） |
| 角色 | 权威数据源 | **冻结的快照** |
| 消费者 | 后端 `presets/loader.py`（磁盘优先，`_bundled_data.py` 兜底）、前端经 API | 仅三方对拍的参照实现 |
| 状态 | 随数据更新 | **不更新**（要更新需重跑三方对拍并人工确认数值一致） |

之所以还要维护这份 JS 包装：参照实现在顶层直接读取 `window.AGENT_PRESETS` /
`window.WEAPON_PRESETS`，删了它三方对拍就跑不起来。

字段结构见 [../docs/design/data-schema.md](../docs/design/data-schema.md)。

## 驱动盘套装效果（catalog/drive-discs.json）

由 `.github/skills/read-zzz-drive-disc/scripts/refresh_disc_presets.py` 从官方
HoYoLAB Wiki 抓取生成，**不可手工编辑**。扫描 `entry_page_id=1..2600`，
以页面是否带 `driver_disk` 组件判定驱动盘页，只收录 2 件套与 4 件套效果文本
（`setEffect2` / `setEffect4`，保留 Wiki 原文），按 `entry_page_id` 排序。

套装图标随抓取落到 `frontend/public/images/discs/ep-<entry_page_id>.webp`
（与 `images/agents`、`images/weapons` 的 `ep-<id>` 命名一致），
JSON 的 `image` 字段记录该图标的 **`/images/…` URL**（`/images/discs/ep-<entry_page_id>.webp`，
唯一图片根约定，见 [docs/overview/directory-layout.md](../docs/overview/directory-layout.md) 第 2.2 节），
不是仓库相对路径。重跑幂等：JSON 字节不变、图片仅在内容变化时才重写。

该文件**不进计算器、不编译进 Worker**，因此 `bundle_worker_data.py --check`
不涉及它。图标的当前消费者是攻略页（`strategy/<slug>/` 的驱动盘卡）；计算器
UI 接入图标属待做（见 [docs/overview/requirements.md](../docs/overview/requirements.md) 第 7 节）。
