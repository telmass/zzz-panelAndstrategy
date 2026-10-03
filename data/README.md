# 预设数据（唯一真实源）

本目录的 JSON 文件是**代理人/音擎预设的唯一真实源**。

## 与 legacy 的区别

| | 本目录 | `frontend/legacy/data/*.js` |
| --- | --- | --- |
| 格式 | JSON | JS 字面量（`window.AGENT_PRESETS`） |
| 角色 | 权威数据源 | 过渡期产物，由本目录生成 |
| 消费者 | 后端 `presets/loader.py`、前端经 API | 仅 legacy 页面 |
| 状态 | **已生成** | 与本目录同步（Skill 抓取产出） |

第 4 步第 17 条已用 `tools/sync_presets.py` 打通两个方向。当前数据是从 legacy
一次性引导而来（`--from-legacy`），此后由 Skill 抓取脚本直接写 JSON，
legacy 的 JS 包装由 `--to-legacy` 反向生成。

已验证「legacy → JSON → legacy」字节一致，故转换无损。改动任一侧后跑

```powershell
python tools/sync_presets.py --check --to-legacy
```

退出码非 0 即表示两侧漂移。`.js` 与 `.json` 都不可手工编辑。

字段结构见 [../docs/data-schema.md](../docs/data-schema.md)。
