# 预设与规则表数据（唯一真实源）

本目录的 JSON 是**代理人/音擎预设与配装规则表的唯一真实源**。

## 三份文件，两个方向

| 文件 | 来源 | 方向 |
| --- | --- | --- |
| `agent-presets.json` / `weapon-presets.json` | Skill 抓取脚本 | 抓取脚本写 JSON，`sync_presets.py --to-legacy` 反向生成 legacy 的 JS 包装 |
| `options.json` | `backend/src/zzz_panel/core/*.py` | 单向生成，`sync_presets.py --options` |

```powershell
python tools/sync_presets.py --options                # core/*.py → options.json
python tools/sync_presets.py --options --check        # 只报漂移
python tools/sync_presets.py --to-legacy --check      # 预设两侧是否同步
```

`options.json` 带 `_generated` 字段声明勿手改（JSON 没有注释语法）。
`backend/tests/test_options_json.py` 断言它与 Python 规则表一致，
改了 `core/*.py` 忘了重新生成就会测试失败。

规则表**不经接口**，前端通过 `@data` 别名直接读该文件——下拉框要瞬时可用，
不能等一次 HTTP 往返。预设则相反，走 `GET /api/presets/*`，
因为数据量大且需刷新，见 `docs/migration-vue3.md` 第 4 步第 18、20 条。

## 与 legacy 的区别

预设数据的 legacy 副本：

| | 本目录 | `frontend/legacy/data/*.js` |
| --- | --- | --- |
| 格式 | JSON | JS 字面量（`window.AGENT_PRESETS`） |
| 角色 | 权威数据源 | 过渡期产物，由本目录生成 |
| 消费者 | 后端 `presets/loader.py`、前端经 API | 仅 legacy 页面 |
| 状态 | **已生成** | 与本目录同步 |

已验证「legacy → JSON → legacy」字节一致，故转换无损。改动任一侧后跑
`python tools/sync_presets.py --to-legacy --check`，退出码非 0 即表示两侧漂移。
预设的 `.js` 与 `.json` 都不可手工编辑。

字段结构见 [../docs/data-schema.md](../docs/data-schema.md)。
