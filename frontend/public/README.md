# frontend/public — 原样拷贝的静态资源

Vite 会把本目录内容**原样拷贝**到 `dist/` 根，不做指纹化、不做依赖分析。

## 放置规则

- 适合：运行时按 URL 取得的资源（图片、字体、robots.txt 等）
- **不能被 `import`**，只能按路径引用：`/images/agents/ep-1109.png`
- 未被 `import` 的资源放进 `src/assets/` **不会**进入构建产物

## 当前内容

| 路径 | 内容 |
| --- | --- |
| `images/agents/` | 60 张代理人 PNG，文件名 `ep-{id}.png`（代理人 `n-cascader` 选中卡片与选项前缀已引用） |
| `images/weapons/` | 100 张音擎 PNG，文件名 `ep-{id}.png`（音擎 `n-cascader` 选中卡片与选项前缀已引用） |
| `images/icons/` | 7 张 roletag 类别图标（两个 `n-cascader` 的一级选项前缀已引用） |

`images/agents/` 与 `images/weapons/` 的文件名与预设数据的 `id` 一一对应
（`data/agent-presets.json`、`data/weapon-presets.json` 的 `id` 即 `ep-1109` 形式），
故按 `/images/{agents,weapons}/${id}.png` 拼路径即可，无需改名。

`images/icons/` 的文件名是 roletag 的**英文 slug**，与 roletag 的映射集中在
`composables/useCascaderIcons.ts` 的 `ROLE_ICON`（两个选择器共用）。
slug 取自官方 Wiki 的 profession key，
与 `.github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py` 同源：

| roletag | 文件名 |
| --- | --- |
| 强攻 | `strike.png` |
| 击破 | `pierce.png` |
| 异常 | `abnormal.png` |
| 支援 | `support.png` |
| 防护 | `guard.png` |
| 命破 | `rupture.png` |
| 锋御 | `armero.png` |

> 文件名一律小写 ASCII。曾用中文名（`强攻.png`），虽可用但在 URL 里需百分号编码，
> 跨平台与工具链下容易出问题，已全部重命名。
