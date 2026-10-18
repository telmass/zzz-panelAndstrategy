# 代理人攻略数据契约（参考实例：叶瞬光）

`strategy/<slug>/` 现在**只保存数据**。页面由主应用统一渲染，新增代理人不需要复制
`index.html / app.js / styles.css`。

- `strategy/<slug>/data/<slug>.json`：抓取产物；
- `strategy/<slug>/data/<slug>.strategy.json`：攻略编辑内容；
- 渲染器：[`frontend/src/strategy/renderStrategy.ts`](../../frontend/src/strategy/renderStrategy.ts)；
- 样式：[`frontend/src/strategy/strategy.css`](../../frontend/src/strategy/strategy.css)（收窄在 `.strategy-detail`）；
- 路由：[`frontend/src/views/StrategyView.vue`](../../frontend/src/views/StrategyView.vue) + `router/index.ts`；
- 登记表：`frontend/src/constants/strategyGuides.ts`，由 `tools/gen_strategy_guides.py` 生成。

## 目录结构

```text
strategy/ye-shunguang/
└── data/
    ├── ye-shunguang.json          # 抓取产物
    └── ye-shunguang.strategy.json # 编辑内容（含毕业面板）
```

没有页面模板、没有 iframe、没有 per-agent 依赖文件。图片仍统一放
`frontend/public/images/`，JSON 只写 `/images/…` URL。

## 数据契约

### `<slug>.json`（抓取产物）

| 字段 | 内容 |
| --- | --- |
| `meta` | `agentId`、官方 Wiki 来源、抓取时间、`entryPageId` |
| `profile` | 姓名、属性、职业、评级、称号、自定义字段、简介、`icons`（属性/职业/评级/称号图标） |
| `assets` | 本地路径 + `*Remote` 兜底：`avatar`、`tachie` |
| `basePanel` | 60 级 / 0 突破基础面板，字段 `label` / `value` / `unit` |
| `skills` | 六大类技能，每类 `moves[]`：`title` / `text` / `growth[]` |
| `cinemas` | 影画 1–6：`level` / `name` / `text` |
| `cinemaBackdrops` | `{ "1".."6": { image, imageRemote } }`，1–3 命共用 `cinema-2.png`，4–6 命共用 `cinema-3.png` |

### `<slug>.strategy.json`（编辑内容）

| 字段 | 内容 |
| --- | --- |
| `_meta` | `agentId`、`name`、`note`、`editorialSources`、`officialGuide` |
| `background` | 可选，右侧全身背景图 URL |
| `skillPriority` | 加点优先级链：`key` / `label` / `note` |
| `weapons` | 音擎推荐：`name` / `stats` / `icon` |
| `drives` | 驱动盘方案：`builds[]`（名称、场景、4 件套、2 件套、主词条、副词条） |
| `graduationPanel` | 满配毕业面板：`title` / `totals[]` / `build` |
| `graduationPanelAlt` | 可选，非满配面板 |
| `teams` | 队伍推荐：`name` / `members[]`（角色、备注、4 件套） |
| `textGuide` | 文字攻略：`title` / `lines[]` |

完整字段示例见 `data/ye-shunguang.strategy.json`。`graduationPanel` 由
`calc_graduation_panel.py` 写入，**不要手改**。

## 新增一个代理人

1. **补 mapping**：把中文名 / 英文名 / 规范 slug 加进
   `data/agent-name-mapping.json`。
2. **抓取**：

   ```powershell
   python .github/skills/agent-strategy/scripts/scrape_agent_guide.py \
     --entry-page-id <id> --slug <slug> \
     --output strategy/<slug>/data/<slug>.json
   ```

3. **写编辑内容**：新建 `strategy/<slug>/data/<slug>.strategy.json`。
4. **补图片**：立绘 / 称号 / 影画背景放
   `frontend/public/images/strategy/<slug>/`；共享图标放
   `frontend/public/images/{skills,icons,grades,attributes}/`。
5. **可选背景**：在 strategy JSON 顶层加
   `"background": "/images/strategy/<slug>/background.png"`。
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

- 模块顺序固定：攻略 → 基础面板 → 技能 → 影画。
- 侧边目录、滚动高亮、技能二级切换、影画分组、属性色、保存图片按钮都在共享渲染器里。
- **不要**为单个代理人改 `renderStrategy.ts` 或 `strategy.css`；确需新能力时改共享层，
  并为核心逻辑补测试。
- 属性/职业图标文件名统一小写 slug：`honed-edge.png`、`attack.png` 等。

## 与旧模板的关系

2026-10 之前每个目录各有一份 `index.html / app.js / styles.css`。这些文件已删除，
历史差异（如 roxy 的保存图片功能）已合并进共享渲染器。旧文档或旧 Skill 若提到复制
这些文件，以本 README 和 `agent-strategy` Skill 的 Step 5 为准。
