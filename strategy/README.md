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
| `background` | 可选，右侧全身背景图 URL；`保存攻略` 导出卡片会把它放在左侧作为人物图 |
| `cinemaPriority` | 可选，关键命座（影画）推荐：`image`（命座图标 URL）+ `keyLevels`（关键影画编号数组，如 `[1,2,6]`）+ `note`（文字说明；仅页面展示，导出卡片不带说明） |
| `skillPriority` | 加点优先级链：每项 `key` / `label` / `icon` / `level` / `maxLevel` / `next` |
| `weapons` | 音擎推荐：`tier` / `items[]`（`name` / `stats` / `icon`）/ `note` |
| `driveBuilds` | 驱动盘方案数组：`name` / `set4`（对象或数组）/ `set2`（`main` + `alt`）/ `mainStats[]` / `subPriority` / 可选 `note`。**只要 4 件套不同，就写成独立方案（分页）**，即使 2 件套 / 主词条 / 副词条完全相同（参考 roxy：非锋御队 4 山大王 vs 锋御队 4 静听嘉音，共用同一份 set2/mainStats/subPriority）。方案名以使用场景开头（如 "非锋御队：…" / "锋御队：…"）。同一个 4 件套不应出现在多个方案中 |
| `driveBuilds[].mainStats[]` | 主词条：`slot` / `main` / `alt` / `note`；`note` 为第四列备注。`保存攻略` 导出卡片会同时展示 `main` 与 `alt`（备选），`alt` 写 `"无"` 时自动隐藏 |
| `graduationPanel` | 满配毕业面板：`build`（文案对象）/ `totals[]`（`label` / `value` / `unit`）/ `note` / `computedAt`。`build.subStats` 仍写完整 54 条；页面/导出卡片由 `substats.ts` 拆成「大词条 + 小词条」展示（如洛茜 47+7） |
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
- 侧边目录（紧凑版：主链接 32px / 子链接 26px / 操作按钮并排，全部内容在 768px 视口内免滚动）、滚动高亮、技能二级切换、影画分组、属性色、保存按钮都在共享渲染器里
- 两个保存按钮：`保存攻略` 由 `frontend/src/strategy/strategyCard.ts` 按 JSON 生成 1360px 白底卡片（左侧 `background`、六条分支、驱动盘主词条 + 备选、毕业面板满配/非满配），`保存一图流` 仍截取整页；词条展示的 47+7 拆分在 `substats.ts`，计算仍用完整 54 条
- **不要**为单个代理人改 `renderStrategy.ts` / `strategyCard.ts` / `substats.ts` / `strategy.css`；确需新能力时改共享层，并为核心逻辑补测试（`tests/strategy-card.spec.ts`、`tests/substats.spec.ts`）
- 属性/职业图标文件名统一小写 slug：`honed-edge.png`、`attack.png` 等
- **所有攻略专属图片文件名统一小写**：`film.png`（命座推荐图）、`tachie.png`、`background.png`、`cinema-2.png`、`cinema-3.png`。JSON 中的 `/images/…` URL 与磁盘文件名的大小写必须完全一致（部署到 Cloudflare 后 URL 区分大小写）
