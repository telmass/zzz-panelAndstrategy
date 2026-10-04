# 预设与规则表数据（唯一真实源）

本目录的 JSON 是**代理人/音擎预设与配装规则表的唯一真实源**。

## 三份文件，两个方向

| 文件 | 来源 | 方向 |
| --- | --- | --- |
| `agent-presets.json` / `weapon-presets.json` | Skill 抓取脚本 | 抓取脚本写 JSON，`sync_presets.py --to-legacy` 反向生成对拍夹具的 JS 包装 |
| `options.json` | `backend/src/zzz_panel/core/*.py` | 单向生成，`sync_presets.py --options` |

```powershell
python tools/sync_presets.py --options                # core/*.py → options.json
python tools/sync_presets.py --options --check        # 只报漂移
python tools/sync_presets.py --to-legacy --check      # 预设两侧是否同步
```

`options.json` 带 `_generated` 字段声明勿手改（JSON 没有注释语法）。
`backend/tests/test_options_json.py` 断言它与 Python 规则表一致，
改了 `core/*.py` 忘了重新生成就会测试失败。

规则表**不经接口**，前端在**构建期**通过 `@data` 别名直接 import 该文件——
下拉框要瞬时可用，不能等一次 HTTP 往返。预设则相反，走 `GET /api/presets/*`，
因为数据量大且需刷新。取舍见
[docs/architecture.md](../docs/architecture.md) 第 3 节「预设数据与规则表：故意不对称」。

## Worker 部署：磁盘之外的编译产物

`pywrangler` 部署时**只上传 `.py` 文件**，放在包里的 `.json` 会被静默丢弃
（不报错，只是线上读不到）。因此 `tools/bundle_worker_data.py` 把
`agent-presets.json` 与 `weapon-presets.json` 的原文编译进
`backend/src/zzz_panel/_bundled_data.py` 的两个字符串常量
`AGENTS_JSON` / `WEAPONS_JSON`。该模块是**生成物，已 gitignore**；
`options.json` 不收——它只在前端构建期被读，根本不经过后端。

```powershell
python tools/bundle_worker_data.py          # 生成/刷新编译产物
python tools/bundle_worker_data.py --check  # 漂移闸，退出码非 0 即产物已过期
```

`presets/loader.py` 的取值顺序是**磁盘优先、编译产物兜底**：

| 顺序 | 来源 | 何时命中 |
| --- | --- | --- |
| 1 | 磁盘上的 `data/*.json`。`data_dir()` 依次尝试 `ZZZ_PANEL_DATA_DIR` 环境变量、从 `__file__` 上溯找同时含 `pyproject.toml` 与 `data/` 的祖先目录 | 本地开发、仓库内的可编辑安装 |
| 2 | `zzz_panel._bundled_data` 的模块常量 | 包被上传到 Worker、仓库的 `data/` 不跟着上线时的**唯一一条路** |

两条路走**同一套**结构与语义校验，编译产物不享有豁免。

> ⚠️ **刷新 `agent-presets.json` 或 `weapon-presets.json` 后必须重跑
> `python tools/bundle_worker_data.py`。** 生成物不进版本库，不重跑就部署，
> 线上 `/api/presets/*` 会继续供旧数据；干净 clone 上直接部署则没有编译产物，
> 路由捕获 `PresetLoadError` 返回 **503**。两种症状都不报错在部署环节，
> `--check` 退出码非 0 即表示产物已过期。

## 与 JS 包装的区别

预设数据的 JS 副本（`frontend/tests/fixtures/legacy-calculator/data/*.js`）：

| | 本目录 | 夹具 `data/*.js` |
| --- | --- | --- |
| 格式 | JSON | JS 字面量（`window.AGENT_PRESETS`） |
| 角色 | 权威数据源 | 派生产物，由本目录生成 |
| 消费者 | 后端 `presets/loader.py`（磁盘优先，`_bundled_data.py` 兜底）、前端经 API | 仅三方对拍的参照实现 |
| 状态 | **已生成** | 与本目录同步 |

已验证「夹具 → JSON → 夹具」字节一致，故转换无损。改动任一侧后跑
`python tools/sync_presets.py --to-legacy --check`，退出码非 0 即表示两侧漂移。
预设的 `.js` 与 `.json` 都不可手工编辑。

之所以还要维护这份 JS 包装：参照实现在顶层直接读取 `window.AGENT_PRESETS` /
`window.WEAPON_PRESETS`，删了它三方对拍就跑不起来。

字段结构见 [../docs/data-schema.md](../docs/data-schema.md)。
