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
| `skills` | 六大类技能（`key`: basic/dodge/assist/special/chain/core），每类含 `moves[]`：`title` / `text` / `growth[]`。核心技的 `moves[]` 有两条：①`核心技：XXX`（满级正文 + A–F 成长表）②`额外能力：XXX`（**无** `growth`）；页面按招式切成二级页 |
| `cinemas` | 影画 1–6：`level` / `name` / `text` |
| `cinemaBackdrops` | `{ "1".."6": { image, imageRemote } }`，1–3 命共用 `cinema-2.webp`，4–6 命共用 `cinema-3.webp` |

### `<slug>.strategy.json`（编辑内容）

| 字段 | 内容 |
| --- | --- |
| `_meta` | `agentId`、`name`、`note`、`editorialSources`、`officialGuide` |
| `background` | 可选，右侧全身背景图 URL；`保存攻略` 导出卡片会把它放在左侧作为人物图 |
| `cinemaPriority` | 可选，关键命座（影画）推荐：`image`（命座图标 URL）+ `keyLevels`（关键影画编号数组，如 `[1,2,6]`）+ `note`（文字说明；仅页面展示，导出卡片不带说明） |
| `skillPriority` | 加点优先级链：每项 `key` / `label` / `icon` / `level` / `maxLevel` / `next` |
| `weapons` | 音擎推荐：`tier` / `items[]`（`name` / `stats` / `icon`）/ `note` |
| `driveBuilds` | 驱动盘方案数组：`name` / `set4`（对象或数组，**可空**）/ `set2` / `set2b` / `set2c`（第 1/2/3 组 2 件套，**可空**）/ `mainStats[]` / `subPriority` / 可选 `note`。**只要 4 件套不同，就写成独立方案（分页）**，即使 2 件套 / 主词条 / 副词条完全相同（参考 roxy：非锋御队 4 山大王 vs 锋御队 4 静听嘉音，共用同一份 set2/mainStats/subPriority）。方案名以使用场景开头（如 "非锋御队：…" / "锋御队：…"）。同一个 4 件套不应出现在多个方案中 |
| `driveBuilds[].mainStats[]` | 主词条：`slot` / `main` / `alt` / `note`；`note` 为第四列备注。`保存攻略` 导出卡片按 4/5/6 号位给三个小框，首选与备选放在同一个框内，且只显示词条名、不显示 `+数值`（如 `异常精通 +92` → `异常精通`）；详情页仍保留完整数值。`alt` 写 `"无"` 时自动隐藏。主词条按方案分组：所有方案共用同一套主词条时只渲染一行「主词条」，不同时每个方案各自渲染一行（行首为方案名） |
| `graduationPanel` | 满配毕业面板：`build`（文案对象）/ `totals[]`（`label` / `value` / `unit`）/ `note` / `computedAt`。`build.subStats` 仍写完整 54 条；页面/导出卡片由 `substats.ts` 拆成「大词条 + 小词条」展示（如洛茜 47+7） |
| `graduationPanelAlt` | 可选，非满配面板（同上结构，多一个 `title`） |
| `teams` | 队伍推荐：`name` / `members[]`（`agentId` / `name` / `role` / `avatar` / `note` / `set4`） |
| `textGuide` | 文字攻略：`title` / `lines[]` |

### 驱动盘套装组：不一定只有「4+2」

每个代理人有 **6 个驱动盘槽位**，实际只考虑两种装法：

| 装法 | 生效的 2 件套效果 | 生效的 4 件套效果 | 契约 |
| --- | --- | --- | --- |
| **4+2**（多数攻略页） | 2 组（4 件套自带的那组 + 一组 2 件套） | 1 | `set4` + `set2` |
| **2+2+2** | 3 组 | 0 | `set2` + `set2b` + `set2c`，`set4` 为 `null` |

两条**不能混**的轴：

- **组**（并列，都要装）：`set2` / `set2b` / `set2c`——第 1/2/3 组 2 件套。
  6 个槽位最多三组（每组 2 片）。
- **候选**（二选一）：组内的 `main` / `alt`——首选 / 备选套装。
  两者各自还可以是**数组**，表示「多套同效果的候选」
  （如「物理伤害 +10%」有獠牙重金属与沧浪行歌两套；参考 nangong-yu 的
  「4 件套三选一 + 2 件套互补」）。

`set4` 是第三条轴：**4 件套的候选列表**（三选一，每个带 `scene` 说明什么场景用哪个），
**不是**「同时生效多个 4 件套」。

> **一个代理人最多生效一个 4 件套。** 4 件套组必然带来它自己的 2 件套效果；
> 而 4+4 装不下（8 片 > 6 槽），所以不存在「同时两个 4 件套」的配装。
> 同理 **4+2+2 也不存在**（8 片 > 6 槽）——有 4 件套组时就只能再有一组 2 件套。

**真实用例（洛克茜 `roxy`）**：第三种配装「自身循环：2 月光 + 2 摇摆 + 2 啄木鸟」是
**2+2+2**——`set4: null`，三组 2 件套各一套：

```jsonc
"set2":  { "main": [{ "name": "月光骑士颂", "label": "能量自动回复 +20%" }] },
"set2b": { "main": [{ "name": "摇摆爵士",   "label": "能量自动回复 +20%" }] },
"set2c": { "main": [{ "name": "啄木鸟电音", "label": "暴击率 +8%" }] }
```

注意月光骑士颂与摇摆爵士的 2 件套效果**相同**（都是「能量自动回复 +20%」），
但它们是**两套不同的套装**——两份效果都生效（该修正量 +40 个百分点），
因为**组**是「都要装」，而组内的 `main` / `alt` 才是「二选一」。
计算语义见 `backend/tests/test_two_plus_two_plus_two.py`。

规则：

- `set4` **可空**——2+2+2 没有 4 件套组，写 `null`（此时页面**不渲染**「4 件套」那一栏，
  而不是留一个「暂无数据」）。
- `set4` 有值时**只能有一组** 2 件套（`set2`），`set2b` / `set2c` 留空。
- 多个 2 件套组在页面上编号 ①②③，单组时沿用「2 件套」不带编号。
- 方案名建议写成「属性伤害三件套：混沌重金属 + 流光咏叹 + 拂晓行纪」这类**不带结构词**的描述；
  省略 `name` 时页面会按套装名自动生成。

> 计算器侧**不用改**：二件套效果固定三个槽位（`set0` / `set1` / `set2`），
> 4 件套组占一个槽、每组 2 件套各占一个槽，各种装法都表达得下——
> 计算器只建模 2 件套效果，不建模 4 件套效果（多数是条件触发，公式工作量与收益不匹配）。


`graduationPanel` 由 `calc_graduation_panel.py` 写入，**不要手改**。

## 新增一个代理人

**一键部署**（含预设、抓取、图片、面板、登记表、生成物与全量闸门）：

```powershell
python tools/agent_deploy.py --name <中文名>
```

细节见 skill [`get-agent-strategy`](../.github/skills/get-agent-strategy/SKILL.md)（阶段表、参考页表、待确认清单）
与共享规程 [`_shared/`](../.github/skills/_shared/README.md)（命名映射 / 信息采集矩阵 / 抓取口径 / 已知坑）。
手工执行时按下面的顺序：

1. **补 mapping**：把中文名 / 英文名 / 规范 slug 加进 `data/catalog/agent-index.json`
2. **抓取**：
   ```powershell
   python .github/skills/agent-strategy/scripts/scrape_agent_guide.py \
     --entry-page-id <id> --slug <slug> \
     --output strategy/<slug>/data/<slug>.json
   ```
   抓取产物的技能文本按「满级 + 额外能力独立成条」的口径产出（见 `_shared/deploy-checklist.md` 的 R1–R6）
3. **写编辑内容**：新建 `strategy/<slug>/data/<slug>.strategy.json`（可从**同职业**参考页克隆结构后逐项确认）
4. **补图片**：立绘 / 称号 / 影画背景放 `frontend/public/images/strategy/<slug>/`；共享图标放 `frontend/public/images/{skills,icons,grades,attributes}/`；
   右侧背景用 `python tools/fetch_agent_backgrounds.py`（Gachabase），角色框头像用 `python tools/fetch_agent_films.py`（Nanoka）
5. **可选背景**：在 strategy JSON 顶层加 `"background": "/images/strategy/<slug>/background.webp"`
6. **算毕业面板**：
   ```powershell
   python .github/skills/agent-strategy/scripts/calc_graduation_panel.py \
     --strategy strategy/<slug>/data/<slug>.strategy.json
   ```
7. **生成登记表与生成物**：
   ```powershell
   python tools/gen_strategy_guides.py      # 攻略页登记表
   python tools/sync_manifest.py            # 数据集登记表（count / sha256）
   python tools/bundle_worker_data.py       # Worker 产物（生成物，gitignored）
   ```
8. **验证**：
   ```powershell
   python tools/normalize_strategy.py --check
   python tools/gen_strategy_guides.py --check
   python tools/sync_manifest.py --check
   python tools/bundle_worker_data.py --check
   python tools/agent_audit.py --all
   python .github/skills/agent-strategy/scripts/calc_graduation_panel.py --check-all
   cd frontend; npm run test; npm run build
   ```

## 渲染约定

- 模块顺序固定：攻略 → 基础面板 → 技能 → 影画
- 侧边目录（紧凑版：主链接 32px / 子链接 26px / 操作按钮并排，全部内容在 768px 视口内免滚动）、滚动高亮、技能二级切换、影画分组、属性色、保存按钮都在共享渲染器里
- 两个保存按钮：`保存攻略` 由 `frontend/src/strategy/strategyCard.ts` 按 JSON 生成 1360px 白底卡片（左侧 `background`、六条分支、驱动盘主词条 + 备选、毕业面板满配/非满配），`保存一图流` 仍截取整页；词条展示的 47+7 拆分在 `substats.ts`，计算仍用完整 54 条
- **不要**为单个代理人改 `renderStrategy.ts` / `strategyCard.ts` / `substats.ts` / `strategy.css`；确需新能力时改共享层，并为核心逻辑补测试（`tests/strategy-card.spec.ts`、`tests/substats.spec.ts`）
- 属性/职业图标文件名统一小写 slug：`honed-edge.webp`、`attack.webp` 等
- **所有攻略专属图片文件名统一小写**：`film.webp`（命座推荐图）、`tachie.webp`、`background.webp`、`cinema-2.webp`、`cinema-3.webp`。JSON 中的 `/images/…` URL 与磁盘文件名的大小写必须完全一致（部署到 Cloudflare 后 URL 区分大小写）
