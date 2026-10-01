# 预设数据（唯一真实源）

本目录的 JSON 文件是**代理人/音擎预设的唯一真实源**。

## 与 legacy 的区别

| | 本目录 | `frontend/legacy/data/*.js` |
| --- | --- | --- |
| 格式 | JSON | JS 字面量（`window.AGENT_PRESETS`） |
| 角色 | 权威数据源 | 过渡期产物，由本目录生成 |
| 消费者 | 后端 `presets/loader.py`、前端经 API | 仅 legacy 页面 |
| 状态 | **待生成** | 当前生效（Skill 抓取产出） |

迁移到 Vue3 第 4 步时，由 `tools/sync_presets.py` 打通两个方向。

字段结构见 [../docs/data-schema.md](../docs/data-schema.md)。
