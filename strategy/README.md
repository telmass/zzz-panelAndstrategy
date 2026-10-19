# 攻略数据契约

`strategy/<slug>/` 只保存数据。页面由主应用统一渲染。

- `strategy/<slug>/data/<slug>.json`：抓取产物
- `strategy/<slug>/data/<slug>.strategy.json`：攻略编辑内容
- 渲染器：`frontend/src/strategy/renderStrategy.ts`
- 样式：`frontend/src/strategy/strategy.css`（收窄在 `.strategy-detail`）
- 路由：`frontend/src/views/StrategyView.vue` + `router/index.ts`
- 登记表：`frontend/src/constants/strategyGuides.ts`（由 `tools/gen_strategy_guides.py` 生成）

## 目录结构

```text
strategy/<slug>/
└── data/
    ├── <slug>.json           # 抓取产物
    └── <slug>.strategy.json  # 编辑内容（含毕业面板）
```

没有页面模板、没有 iframe、没有 per-agent 依赖文件。图片仍统一放
`frontend/public/images/`，JSON 只写 `/images/…` URL。

## 数据契约

### `<slug>.json`（抓取产物）

| 字段 | 内容 |
| --- | --- |
| `meta` | `agentId`、官方 Wiki 来源（`source`）、抓取时间（`scrapedAt`）、`entryPageId` |
| `profile` | 姓名、属性、职业、评级、称号（`factionTitle`）、自定义字段、简介、`icons`（属性/职业/评级/称号图标 URL） |
| `assets` | 本地路径（`/images/…`）+ `*Remote` 兜底：`avatar`、`tachie` |
| `basePanel` | 60 级 / 0 突破基础面板，字段 `label` / `value` / `unit` |
| `skills` | 六大类技能（`key`: basic/dodge/assist/special/chain/core），每类含 `moves[]`：`title` / `text` / `growth[]` |
| `cinemas` | 影画 1–6：`level` / `name` / `text` |
| `cinemaBackdrops` | `{ "1".."6": { image, imageRemote } }`，1–3 命共用 `cinema-2.png`，4–6 命共用 `cinema-3.png` |

### `<slug>.strategy.json`（编辑内容）

| 字段 | 内容 |
| --- | --- |
| `_meta` | `agentId`、`name`、`note`、`editorialSources`、`officialGuide` |
| `background` | 可选，右侧全身背景图 URL |
| `skillPriority` | 加点优先级链：每项 `key` / `label` / `icon` / `level` / `maxLevel` / `next` |
| `weapons` | 音擎推荐：`tier` / `items[]`（`name` / `stats` / `icon`）/ `note` |
| `driveBuilds` | 驱动盘方案数组：`name` / `set4`（对象或数组）/ `set2`（`main` + `alt`）/ `mainStats[]` / `subPriority` / 可选 `note` |
| `driveBuilds[].mainStats[]` | 主词条：`slot` / `main` / `alt` / `note`；`note` 为第四列备注 |
| `graduationPanel` | 满配毕业面板：`build`（文案对象）/ `totals[]`（`label` / `value` / `unit`）/ `note` / `computedAt` |
| `graduationPanelAlt` | 可选，非满配面板（同上结构，多一个 `title`） |
| `teams` | 队伍推荐：`name` / `members[]`（`agentId` / `name` / `role` / `avatar` / `note` / `set4`） |
| `textGuide` | 文字攻略：`title` / `lines[]` |

`graduationPanel` 由 `calc_graduation_panel.py` 写入，**不要手改**。

## 新增一个代理人

1. **补 mapping**：把中文名 / 英文名 / 规范 slug 加进 `data/agent-name-mapping.json`
2. **抓取**：
   ```powershell
   python .github/skills/agent-strategy/scripts/scrape_agent_guide.py \
     --entry-page-id <id> --slug <slug> \
     --output strategy/<slug>/data/<slug>.json
   ```
3. **写编辑内容**：新建 `strategy/<slug>/data/<slug>.strategy.json`
4. **补图片**：立绘 / 称号 / 影院背景放 `frontend/public/images/strategy/<slug>/`；共享图标放 `frontend/public/images/{skills,icons,grades,attributes}/`
5. **可选背景**：在 strategy JSON 顶层加 `"background": "/images/strategy/<slug>/background.png"`
6. **算毕业面板**：
   ```powershell
   python .github/skills/agent-strategy/scripts/calc_graduation_panel.py \
     --strategy strategy/<slug>/data/<slug>.strategy.json
   ```
7. **生成登记表**：
   ```powershell
   python tools/gen_strategy_guides.py
   ```
8. **验证**：
   ```powershell
   python tools/normalize_strategy.py --check
   python tools/gen_strategy_guides.py --check
   cd frontend; npm run test; npm run build
   ```

## 渲染约定

- 模块顺序固定：攻略 → 基础面板 → 技能 → 影画
- 侧边目录、滚动高亮、技能二级切换、影画分组、属性色、保存图片按钮都在共享渲染器里
- **不要**为单个代理人改 `renderStrategy.ts` 或 `strategy.css`；确需新能力时改共享层，并为核心逻辑补测试
- 属性/职业图标文件名统一小写 slug：`honed-edge.png`、`attack.png` 等
