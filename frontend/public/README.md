# frontend/public — 原样拷贝的静态资源

Vite 会把本目录内容**原样拷贝**到 `dist/` 根，不做指纹化、不做依赖分析。

## 放置规则

- 适合：运行时按 URL 取得的资源（图片、字体、robots.txt 等）
- **不能被 `import`**，只能按路径引用：`/images/agents/ep-1109.png`
- 未被 `import` 的资源放进 `src/assets/` **不会**进入构建产物

## 当前内容

| 路径 | 内容 |
| --- | --- |
| `images/agents/` | 60 张代理人 PNG，文件名 `ep-{id}.png` |
| `images/weapons/` | 100 张音擎 PNG，文件名 `ep-{id}.png` |

这些图片**目前没有任何代码引用**，属预留素材；文件名与预设数据的 `id` 一一对应
（`data/agent-presets.json` 的 `id` 即 `ep-1109` 形式），接入时按
`/images/agents/${id}.png` 拼路径即可。
