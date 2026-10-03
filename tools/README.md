# 开发辅助脚本

## 计划中的脚本

| 文件 | 用途 | 状态 |
| --- | --- | --- |
| `dev.ps1` | 一键启动后端（uvicorn :8000）+ 前端（vite dev :5173） | 待实现 |
| `sync_presets.py` | 双向同步预设：抓取脚本 → `data/*.json` → `frontend/legacy/data/*.js` | 待实现 |

## 双向同步脚本

| 文件 | 用途 |
| --- | --- |
| `sync_presets.py` | `data/*.json` ↔ `frontend/legacy/data/*.js` 双向同步 |

```powershell
python tools/sync_presets.py --from-legacy          # JS → JSON（一次性引导）
python tools/sync_presets.py --to-legacy            # JSON → JS（长期方向）
python tools/sync_presets.py --to-legacy --check    # 只报漂移，退出码 1 = 不同步
```

两个方向都先把数据规范化到脚本内定义的键序再写出，因此重复执行不产生 diff，
且 `legacy → JSON → legacy` 字节一致（已验证，可作无损性回归检查）。

脚本内置一个 JS 字面量解析器，只支持抓取脚本产出的子集：单引号字符串、
**无转义序列**、键名不引号。遇到反斜杠会显式报错而非猜测。两个易踩的点：

- 剥注释必须字符串优先，否则 URL 里的 `//` 会被当行注释，把 `source` 整条截断。
- 抓取脚本对**对象键**也输出尾随逗号，对「值全为标量的扁平对象数组」
  （`unmodeledBaseStats`）则整元素单行渲染。这两条规则不还原就无法字节一致。

## 第 3 步新增的诊断脚本

排查前后端对拍差异时用，**不做断言**，退出码不代表通过与否。

| 文件 | 用途 |
| --- | --- |
| `dump_backend_responses.py` | 把 `backend/tests/legacy_cases.json` 的每条用例 POST 给后端，落盘完整响应 JSON |
| `../frontend/tools/diff_breakdown.mjs` | 把落盘 JSON 与 legacy 实算明细逐行 diff，按 DOM 层级归类 |

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
