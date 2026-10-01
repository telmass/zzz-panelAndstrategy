# 开发辅助脚本

## 计划中的脚本

| 文件 | 用途 | 状态 |
| --- | --- | --- |
| `dev.ps1` | 一键启动后端（uvicorn :8000）+ 前端（vite dev :5173） | 待实现 |
| `sync_presets.py` | 双向同步预设：抓取脚本 → `data/*.json` → `frontend/legacy/data/*.js` | 待实现 |

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
