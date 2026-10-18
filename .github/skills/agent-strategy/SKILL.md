---
name: agent-strategy
description: Produce a complete "代理人攻略" (agent strategy) page for any Zenless Zone Zero agent — scrape the official HoYoLAB Wiki, structure guide data (skills, cinemas, base panel, showcase art), author the editorial strategy content, compute a fully-geared graduation panel with the repo calculator, and render the local responsive web template. Reference implementation: 叶瞬光 in `strategy/ye-shunguang/`.
---

# ZZZ Agent Strategy Page

Use this skill when the user names a ZZZ agent and asks for a 攻略 page / strategy page /
agent guide page (加点、音擎、驱动盘、毕业面板、队伍、文字攻略) in the style of the
`strategy/ye-shunguang/` reference implementation (叶瞬光).

The output is a local web page mounted into the main app, one folder per agent under
`strategy/` (folder name = the route slug in the main app):

> ✅ Canonical naming is enforced by `data/agent-name-mapping.json`. All current
> `strategy/<slug>/data/` files use `<slug>.json` / `<slug>.strategy.json` and are valid
> UTF-8. Run `python tools/normalize_strategy.py --check` before committing; do not copy
> legacy filenames into new agent pages.

```
strategy/<slug>/                # workdir；slug 同时是主应用 /strategy/<slug> 路由
├── data/<slug>.json           # 抓取产物（scrape_agent_guide.py）
└── data/<slug>.strategy.json  # 攻略编辑内容（手写 + 计算脚本写入毕业面板）
```

> **页面渲染是共享的。** 自 2026-10 起，`strategy/<slug>/` 只保留数据；
> `frontend/src/views/StrategyView.vue` 调用 `frontend/src/strategy/renderStrategy.ts`
> 渲染，样式统一在 `frontend/src/strategy/strategy.css`。**不要**再复制
> `index.html / app.js / styles.css`。下文历史小节里提到这些文件的句子仅作背景，
> 以本节和 Step 5 为准。

**图片一律不放这里**：唯一图片根是 `frontend/public/images/`，JSON 里只写
`/images/…` URL——共享图标（技能 / 职业 / 等级 / 属性）落 `images/{skills,icons,grades,attributes}/`，
每代理人独有的立绘 / 称号 / 影画背景落 `images/strategy/<slug>/`。
**禁止**页相对 `assets/…` 路径。

## 属性与职业命名对照（统一命名）

所有页面、JSON、技术文档中属性/职业均使用本表命名：

| 中文 | 英文 / 文件名 slug | 备注 |
| --- | --- | --- |
| 流明 | lumiflux | 变种属性 |
| 玄墨 | auric-ink | 变种属性 |
| 凛刃 | honed-edge | 变种属性 |
| 烈霜 | frost | 变种属性 |
| 风 | wind | 标准属性 |
| 火 | fire | 标准属性 |
| 冰 | ice | 标准属性 |
| 以太 | ether | 标准属性 |
| 物理 | physical | 标准属性 |
| 电 | electric | 标准属性 |
| 强攻 | attack | 职业 |
| 击破 | stun | 职业 |
| 异常 | anomaly | 职业 |
| 支援 | support | 职业 |
| 防护 | defense | 职业 |
| 命破 | rupture | 职业 |
| 锋御 | armorer | 职业 |

代理人中文与英文对应名字可查阅 `data/agent-name-mapping.json`，避免命名不恰当。

## Inputs to confirm with the user first

Editorial content is **not** derivable from the Wiki. Before writing
`<slug>.strategy.json`, confirm (ask once, batch the questions):

1. 技能加点优先级链（形如 `核心技 > 连携 = 普攻 = 特殊 > 支援 > 闪避`）与各技能目标等级（核心技上限 7；其余通常 12，闪避可 11）。
2. 音擎推荐档位（首选专武 / 下位 / 备选 / 四星）与每档音擎名单。
3. 驱动盘 4 件套与 2 件套（首选 + 备选）、4/5/6 号位主词条首选/备选、副词条优先级链。
4. 毕业面板口径：专武、套装、主词条、副词条 54 条分配（**必须按「初始 4 词条 + 5 次强化」模型推导，见下方铁律附则**）。
5. 队伍推荐（1~3 支三人队）与每队一句话总结。
6. 文字攻略（出招表 / 注意事项）——依据抓取到的技能机制文本撰写，不得编造机制。

If the user only says "照叶瞬光的来", apply the 叶瞬光 instance (see §Verified example)
and say so explicitly.

## 铁律：毕业面板没有通用标准，必须按代理人定制

**每个代理人的毕业面板都不一样，禁止把某个代理人的口径默认套给其他代理人。**
叶瞬光、般岳、克拉蕾三个实例已经证明了差异是系统性的，不是数值微调：

| 维度 | 叶瞬光（凛刃 · 强攻，标准模式） | 般岳（火 · 命破） | 克拉蕾（电 · 锋御） | 由什么决定 |
| --- | --- | --- | --- | --- |
| 展示行（`--rows`） | `atk,cr,cd,pv`（攻击 / 双爆 / 穿透值） | `hp,penforce,cr,cd`（生命值 / 贯穿力 / 双爆） | `def,actual_cr,cd,pv`（防御力 / 实际暴击率 / 暴击伤害 / 穿透值） | 特性与面板模式：命破看贯穿力，锋御看实际暴击率与锐暴伤害，攻击力只是中间量 |
| 面板模式（`--mode`） | `standard` | `rupture` | `fengyu`（实际暴击率 = 暴击伤害 × 35% + 暴击率） | 预设 `panelMode` |
| 主词条 | 5 / 6 号位攻击力 | 5 号位伤害加成 / 6 号位生命值 | 4 号位暴击率 / 5 号位穿透率 / 6 号位防御力 | 词条收益：命破贯穿力 = 0.3 × 攻击 + 0.1 × 生命；锋御以防御力为倍率且暴击率可超 100% |
| 副词条 54 条分配 | CR 13（面板 50.6%）/ CD 16 / ATK% 16 / ATK 5 / PEN 4 | CR 20（面板 67.4%）/ CD 14 / HP% 12 / ATK% 6 / HP 2 | CR 19（面板 120.9%）/ DEF% 15 / 穿透值 12 / DEF 5 / CD 3 | 专武局内加成与属性收益；锋御的暴击率超 100% 仍参与多重暴击判定，故给到 120% 档。**且必须按「初始 4 词条 + 5 次强化」推导（见下方铁律附则），54 条不能全砸在最优先的 2~3 个词条上** |
| 暴击率目标 | 50% 档 | 67% 档 | 121% 档（社区称 129% 档，差在二件套选的是穿透率还是暴击率） | 同上；**不要假设「13 条暴击率」「50%」或「100% 封顶」是放之四海的标准** |
| 音擎基础值 | 攻击力 | 攻击力 | **防御力**（锋御音擎 baseKind=def） | 特性；抓 `weapon["baseDefense"]` 而非 `baseAttack` |

操作规则：

1. 先读该代理人的 `panelMode`、属性、特性、专武特效与词条收益（命破含生命值转化、
   锋御用实际暴击率口径且音擎基础值是防御力、击破常看冲击力/失衡值阈值等），再定
   展示行 / 模式 / 主词条 / 副词条分配。
2. 毕业面板口径是与用户确认清单的第 4 项——**必须逐代理人确认**，不能沿用上一个代理人的数字。
3. `strategy/<slug>/data/<slug>.strategy.json` 的 `graduationPanel` 由计算脚本按上面的
   口径参数实算写入；换代理人时整组参数（`--rows/--mode/--sub-stats/--main-spec` 等）
   都要重新给，不能只换 id。
4. 若用户给的预期数值与仓库计算器结果不一致（如社区工具的 67.8% vs 本仓 67.4%、社区
   129% 档 vs 本仓 120.9%），以仓库计算器为准并说明差异来源（基础值 / 每条数值 /
   二件套选择不同），不要手改面板数字迁就。
5. 选项表缺口要按需补齐：锋御毕业套荆棘玫瑰的二件套「防御力 +16%」曾整条缺失
   （`find_option` 找不到会静默跳过，只表现为下拉选不到、面板少一段），已按
   `core/options.py` → `SET_OPTIONS` → `sync_presets.py --options` 的流程补上。
   缺选项与 `to` 写错都不报错，务必核对最终面板的中间量；**选项表没有对应项的效果
   （如山大王的「失衡值+6%」）用 `--set4-effect none` 显式不建模**，不要静默漏传。

### 铁律附则：副词条 54 条必须按「初始 4 词条 + 5 次强化」推导

副词条**不是「54 条全给有效词条」**。游戏内每一号盘的副词条由两部分组成：

1. **初始 4 条**：从该盘可选词条池里随机取 4 种（**主副不重复**——不会出现与该盘主词条
   同属性的副词条）；
2. **5 次强化**：每次随机加在那 4 条中的某一条上，**不会新增词条种类**。

即每盘恒为 4 + 5 = 9 条、6 盘共 54 条。由此推出四条约束，分配 `--sub-stats` 前必须逐条校验：

- **有效词条数 = Σ 每盘 min(该盘可选的有效词条种数, 4) + 5**。某盘可选的有效词条不足 4 种
  （被固定主词条或 4/5/6 号位主词条排掉），缺口由**非有效词条随机填充**，填充条数不计入
  有效词条——"把 54 条全算成有效词条"一定超标。
- **单一词条单盘最多 6 条**（1 初始 + 5 强化），且**只能加在进过初始 4 条的盘位上**：
  某盘初始 4 条里没有它，那一盘它一格都吃不到。故某词条上限 ≤ 它可出现的盘位数 × 6。
- **初始 4 条必须 4 种不同词条**，所以每个能出现的盘位至少给它 1 条。
- 强化投向按该代理人的阈值/收益口径定制（例如命中某个面板阈值后就把余量全让给第一属性），
  没有统一标准——但**总量必须 54、每一盘的 9 条必须满足上述三条**。

推导步骤：逐盘列「主词条 → 被排除词条 → 初始 4 条（含填充）→ 5 次强化去向」，汇总成
各词条条数，再交给 `calc_graduation_panel.py --sub-stats`。实例见下方蕾米埃尔·丹一节的
逐盘表。

**六个实例已全部按本附则重推**（重推口径与结论）：

| 实例 | 副词条分配 | 有效/填充 | 备注 |
| --- | --- | --- | --- |
| 叶瞬光 | CR13 / CD16 / ATK%16 / ATK5 / PEN4 | 54 / 0 | 链条 5 项，2/4/5/6 号位各被排一项 |
| 般岳 | CR20 / CD14 / HP%12 / ATK%6 / HP2 | 54 / 0 | 生命值进链第 5 位，顶 4/6 号位初始 |
| 克拉蕾 | CR19 / DEF%15 / PEN12 / DEF5 / CD3 | 54 / 0 | 5 号位穿透率不排穿透值；CD 顶 3/4/6 号位初始 |
| 莱特 | CR9 / CD23 / ATK%15 / PEN6 / ATK1 | 53 / 1 | 4 号位暴击率排暴击率，小攻击顶上第 4 条初始 |
| 柚叶 | ATK%24 / AM16 / ATK5 / 填充9 | 45 / 9 | 链条仅 3 项，2/4/5 号位各缺 1~2 条初始 |
| 蕾米埃尔 | ATK%11 / AM28 / ATK5 / PEN6 / HP4 | 50 / 4 | 见下方逐盘表；精通优先、攻击% 压 4000 线 |

> 重推后有效词条一律不超「Σ 每盘 min(可选有效种数, 4) + 5」，填充词条按「不影响该代理人
> 展示行」或「最能补展示行」择一（柚叶取小生命/小防御、莱特取小攻击、克拉蕾取暴击伤害）；
> 分配前先用最大流校验逐盘可行（每盘 5 次强化只能落在该盘初始 4 条内）。

## Workflow

### Step 1 — Scrape the Wiki

```
python .github/skills/agent-strategy/scripts/scrape_agent_guide.py \
    --entry-page-id <id> --slug <slug> --output strategy/<slug>/data/<slug>.json
```

- Find `<id>` from the agent index <https://baike.mihoyo.com/zzz/wiki/channel/map/2/43>
  (detail URL `wiki/content/<id>/detail`); never guess an id.
- The script reads `https://act-api-takumi.mihoyo.com/hoyowiki/zzz/wapi/entry_page_v2?entry_page_id=<id>`
  and extracts, by `component_id`: `role_base_info` (name/grade/attribute/profession/
  称号+配图/立绘/头像), `role_talent` 技能展示 (6 tabs + moves + growth) and 晋升需求
  (初始/满级 rows merged → 60 级 0 突破 base panel), `double_col_table` (影画 L1..L6),
  `map_desc` (影画展示1/2/3 原图).
- Outputs `meta / profile / basePanel / assets / skills / cinemas / cinemaBackdrops`
  (schema: `strategy/ye-shunguang/README.md` §5). `skills[].key` ∈ `basic/dodge/assist/special/chain/core`;
  WIKI tab 终结技 maps to类别 **连携技** (it contains both 连携 and 终结 moves).
- The summary printout is the accuracy gate: agent name, 属性/职业/grade, 基础面板项数,
  6 类技能招式数 (变体锚点已过滤), 影画 6 层, 影画背景图 6 层. Verify before moving on.
- 基础面板数值写法不统一：有的页面写「5%」、有的写「5.0%」（蕾米埃尔即如此）。
  解析器 `num()` 已按 `float()` 先转再判整处理，两种写法都不会炸。
- **核心技有两种 WIKI 结构**：多数代理人子项带 title/desc；克拉蕾这类只有成长表，
  描述以 `data-type="详情"` 的 `data-name` 属性挂在**每一 rank** 的行上。解析器已兼容
  （`core_detail_from_growth`：反转义 HTML 抽文本，标题取「核心被动：XXX」，数值取最后
  一段 F 级满级），若某代理人核心技抓成 0 招式或数值看着像一级，先查是不是这种结构。
  **只有成长表的结构，`data-name` 详情里挂的是核心被动全文、其扁值不是核心加成**：
  核心加成只建模成长表的**可见行**。克拉蕾的详情写「暴击率 30%」而建模的是可见行
  4.8%×6 = 28.8%；南宫羽的详情写「异常精通提升 120 点」（随被动等级 70→120 递增），
  而其核心加成只有可见行的掌控 +12×3 与基础攻击 +25×3。曾把该 120 点误当第三核心加成
  去扩展计算器，被需求方指出后整体回滚——**拿不准时以 `data/agent-presets.json`
  （读数技能产出）与需求方确认为准，不要自行加槽位**。
- **基础面板不展示锋御固有属性「锐暴伤害」**：它是局内恒定量、不随等级/配装变化，
  页面模板用 `BASE_PANEL_HIDDEN_LABELS` 过滤（抓取数据仍保留原行）。

Image downloads in this step all land under the single image root
`frontend/public/images/`, and the JSON records `/images/…` URLs:

| 图片 | 落点 | 规则 |
| --- | --- | --- |
| 技能图标（6 张） | `images/skills/<key>.png` | 全代理人共享，已存在则跳过下载 |
| 职业图标 | `images/icons/<profession>.png` | 仓库已有（7 职业齐全），直接引用，**不复制** |
| 等级图标 | `images/grades/<grade>.png` | WIKI bundle `vp` 映射（s/a/b），已存在则跳过下载 |
| 属性图标 | `images/attributes/<slug>.png` | WIKI 不下发，检测人工放置的文件，见 Step 2 |
| 头像 | `images/agents/<agentId>.png` | 不下载；该文件已存在于仓库才写 URL |
| 立绘 / 称号 / 影画背景 | `images/strategy/<slug>/…` | 每代理人独有，随 `--assets-dir`（默认即此路径）下载 |

本地文件缺失时对应字段留空、保留 `*Remote` 远程 URL 兜底（页面 `onerror` 降级）。

### Step 2 — Place the attribute icon (manual)

The WIKI does **not** publish attribute icons through any public API or bundle. Obtain the
official 凛刃/电/火… attribute icon (BWIKI mirrors the same asset, e.g.
`https://patchwiki.biligame.com/images/zzz/e/e6/1qllpfb6i7fqlgraxfyohiek59zzrg6.png` is
图标-凛刃) and save it as `frontend/public/images/attributes/<slug>.png`
(WIKI slug `honed_edge` maps to the file `honed-edge.png`; all icon files use
lowercase ASCII slugs). If you cannot obtain it, leave it out — the page falls back to
an attribute-colour tile — and tell the user.

### Step 3 — Author `<slug>.strategy.json`

Copy `strategy/ye-shunguang/data/ye-shunguang.strategy.json` as the template and fill
it per `strategy/ye-shunguang/README.md` §6. Hard rules:

- `skillPriority`: array order = priority chain; each item `{key, label, icon, level,
  maxLevel, next}` with `next` ∈ `>` / `=` / `` (last empty). Icons reuse
  `/images/skills/<key>.png`. The page shows only `Lv.N` — never write 满级/上限 wording.
- `weapons`: one card per tier (`tier` + `note` + `items[{name,stats,icon}]`); weapon icons
  go to `frontend/public/images/weapons/<entryPageId>.png` and are referenced as
  `/images/weapons/<entryPageId>.png` (fetch the WIKI 音擎 page icon_url).
- `driveBuilds`: **驱动盘推荐方案数组**（版式同队伍：一组一卡片，默认只有一组，
  有多套时手动追加）。每项 `{name?, note?, set4 {name,label,icon,effect4?,alt4?},
  set2 {main,alt}, mainStats[{slot,main,alt}], subPriority[{label,next}]}`；
  `name` 缺省时页面用「`<set4> 4 件套 + <set2.main> 2 件套`」自动生成标题。
  Set icons are `/images/discs/<id>.png` (files already live in
  `frontend/public/images/discs/`); names/effects from `data/drive-disc-presets.json`.
  旧的单个 `drives` 对象模板仍兼容，新数据一律用 `driveBuilds`。
  **主词条表三列等宽固定**（`frontend/src/strategy/strategy.css` 的 `.drive-main`：
  `table-layout: fixed` + 部位 20% / 首选 40% / 备选 40%）——不要改回 `auto`：
  auto 布局下首选列被最长文案撑开、备选列能换行反被压缩，会出现「有的代理人
  首选区宽、有的备选区宽」。
  **`set4` 也可是数组**：多个 4 件套共用同一套 2 件套 / 主词条 / 副词条时
  （柚叶：月光骑士颂 / 静听嘉音 / 自由蓝调 + 法厄同之歌），合并成**一个**方案，
  每项加 `"scene": "使用场景"` 备注——不要写成多个完整方案，否则主词条表与
  副词条链会整段重复。`test_strategy_data.py` 对这条有守护。
  某部位没有备选时 `alt` 填字面「**无**」（五个页面沿用这一约定），不要留空、
  也不要写成破折号等其他占位。
- `teams`: `[{name, members[{agentId,name,role,avatar,note,set4[{name,icon}]}]}]`;
  avatars are `/images/agents/<id>.png` directly — never copy them anywhere.
- `textGuide`: `[{title, lines[]}]`, grounded in the scraped skill text.
- Do **not** hand-edit `graduationPanel` or `graduationPanelAlt` — both are written by Step 4.

### Step 4 — Compute the graduation panel

```
python .github/skills/agent-strategy/scripts/calc_graduation_panel.py \
    --agent-id <id> --weapon-id <id> --set4-id <id> --set2-id <id> \
    [--disc4 cd_48] [--disc5 dmg_30] [--disc6 hp_pct_30] \
     [--set4-effect hp_pct_10|none] [--set2-effect cd_16] \
    [--sub-stats cr:13,cd:16,hp_pct:15,atk_pct:10] \
    [--rows atk,cr,cd,pv | hp,penforce,cr,cd] [--mode standard|rupture|fengyu] \
    [--main-spec "…"] [--sub-spec "…"] \
    --strategy strategy/<slug>/data/<slug>.strategy.json
python … --check   # 一致性校验（同样带全部 flag，退出码非 0 即漂移）
```

- Reads the 60 级 base panel from `data/agent-presets.json`, the weapon from
  `data/weapon-presets.json`, the two sets from `data/drive-disc-presets.json`, then calls
  the same `zzz_panel.services.panel_service` that backs `POST /api/panel/calc`.
- **不要改脚本里的 `BUILD` 常量**：主词条 / 二件套效果 / 副词条分配 / 两行说明
  文案全部用上面的 flag 传入；不传 flag 时 BUILD（叶瞬光口径）即默认值。
  `--sub-stats` 支持紧凑格式 `cr:13,cd:16,…`（Windows shell 下 JSON 的双引号会被吃掉）。
- 面板模式默认取预设的 `panelMode`（般岳=命破 → `rupture`，此时 `mode_stats` 会给出
  贯穿力；克拉蕾=锋御 → `fengyu`，给出实际暴击率与锐暴伤害）；`--mode` 可覆盖。
- 展示行用 `--rows`：**默认 `atk,cr,cd,pv` 只是叶瞬光（强攻）口径，不是通用标准**；
  命破传 `hp,penforce,cr,cd`；锋御（克拉蕾）传 `def,actual_cr,cd,pv`；击破若核心阈值看
  某条属性（莱特的冲击力）可用 `imp` 行；异常类若核心数值是精通/攻击（蕾米埃尔的
  异化系数与团队加攻阈值）可用 `am` / `atk` 行——`TOTAL_LABELS` 支持
  hp/atk/def/cr/cd/dmg/imp/am/pr/pv/penforce/actual_cr/blast_dmg。具体展示哪些行按该代理人
  的伤害与机制口径定，见上文铁律。
- 2-piece effects are counted **once each** (4-piece in-battle effects are not modeled by
  the calculator).
- 副词条与暴击率目标**没有统一标准**（见上文铁律）：取决于专武局内加成与该属性的
  词条收益。两个实例仅供参考，不是模板：
  叶瞬光（专武局内 +50% 暴击）面板暴击率只需 50% 档 → CR 13 条；
  般岳（专武局内 +20% 暴击、生命值转贯穿力）推到 67% 档 → CR 20 条，
  且要把相当部分副词条分给生命值%。
- **`--sub-stats` 必须先按铁律附则逐盘推导**（初始 4 词条 + 5 次强化），并确认
  有效词条总数不超过「Σ 每盘 min(可选有效种数, 4) + 5」、每盘 5 次强化落在该盘初始
  4 条内；推导结果直接作为 `--sub-stats` 与 `--sub-spec` 的口径，不要再手工凑 54。
- Only the rows named by `--rows` are written; the build spec is plain text with
  **no parenthetical notes** (visitor-facing).
- **可选的第二块「非满配」面板**：想在满配面板下方再给一个低词条参考面板时，加
  `--alt-sub-stats`（紧凑格式，如 `atk_pct:6,am:4,atk_flat:2`）、`--alt-label`、`--alt-spec`；
  主词条也可另给（`--alt-disc4/5/6` + `--alt-main-spec`，缺省沿用满配）。
  脚本以同一音擎 / 核心 / 套装、按上述口径实算，写入
  `graduationPanelAlt`（`--check` 同时校验两份，任一漂移即退出非 0）。**重点词条必须逐代理人
  与需求方确认**（铁律同样适用），常见确认形式是目标值或上限：叶瞬光「攻击 3200 / 暴率 50 /
  爆伤 220」、般岳「暴率 67 / 生命 18000+ / 爆伤 180 且 CR+CD+HP% ≤ 40 条」、
  克拉蕾「实际暴率 130 起、爆伤留一档便于配平、其余给 DEF%/DEF，总 ≤ 40 条」、
   莱特「暴击率 / 爆伤 / 攻击力%」、蕾米埃尔「攻击 4000 附近 / 精通 400+，ATK%+ATK+AM ≤ 30 条」、
   柚叶「4/5 号攻击力%、6 号掌控，副词条只求攻击过 3000、总幅度 ≤ 20 词条」、
   维琳娜「攻击 2500 / 异常精通 400」。
  条数由确认结果倒推，不预设统一门槛；不传 `--alt-sub-stats` 则不生成，并会清掉已存在的
  `graduationPanelAlt`。
- 展示行数由 `--rows` 决定，`.base-panel--graduation` 用 `repeat(auto-fit, minmax(140px, 1fr))`，
  2 / 3 / 4 行都铺满一行，无需按行数改 CSS。

### Step 5 — Wire the shared renderer

There is **no page template to copy** and no `app.js` to edit. The shared renderer
(`frontend/src/strategy/renderStrategy.ts`) derives everything from the two JSON files
and the slug. Only do these:

1. Ensure `data/<slug>.json` / `data/<slug>.strategy.json` exist with canonical names.
2. If the agent needs a right-side full-body background, set
   `"background": "/images/strategy/<slug>/background.png"` at the top level of the
   strategy JSON (see `agent-background` Skill).
3. If the agent uses a new attribute colour, add it once to `ATTRIBUTE_TILE_COLORS` in
   `frontend/src/strategy/renderStrategy.ts` (10 are mapped today).
4. If the WIKI changed 影画 grouping (not 1-3 / 4-6), adjust `cinema_backdrops()` in the
   scraper.

Everything else (module order 攻略→基础面板→技能→影画, sidebar + scroll-spy, skill tabs,
cinema group frames, attribute-coloured module numbers, fonts, save-image buttons) is
shared and data-driven — do not restyle per agent.

### Step 6 — Register in the main app

Run:

```powershell
python tools/gen_strategy_guides.py          # regenerate strategyGuides.ts
python tools/gen_strategy_guides.py --check  # CI / pre-commit guard
```

The generator reads `data/agent-name-mapping.json` + the strategy data and writes
`frontend/src/constants/strategyGuides.ts`. Do **not** hand-edit the registry. The
`/strategy` picker renders one card per generated entry; `StrategyView` loads
`/strategy/<slug>/data/<slug>.json` at runtime.

### Step 7 — Verify

1. `npm run dev --prefix frontend` → 启动页「代理人攻略」入口卡 → `/strategy` 选择页 →
   该代理人卡片（Vue 共享渲染器，不再是 iframe）。
2. Render checks: hero four icons (属性/职业/等级/称号), module bands 01-04 and sidebar
   numbers agree, sidebar active state + bottom fallback, grad chain text, weapon tiers,
   drive 4+2, graduation panel 4 values matching Step 4, team cards, skill tabs switch,
   cinema two group frames with the right backdrops, no console errors.
3. Data gates: the scraper summary; `calc_graduation_panel.py --check` exits 0;
   `python tools/normalize_strategy.py --check` and `python tools/gen_strategy_guides.py --check` exit 0.
4. Assets: every `/images/…` path referenced by the JSONs returns 200 from the server.
5. Frontend: `npm run test --prefix frontend` passes (includes rendering every registered
   agent through the shared renderer).

## Verified example: 叶瞬光 (`strategy/ye-shunguang/`)

The reference instance for every rule above:

- entry_page_id 1687; 属性 凛刃 (`honed_edge`), 特性 强攻 (`strike`), grade S, 称号 虚狩·青溟司命.
- Base panel 60 级 0 突破: HP 7673 / ATK 863 / DEF 606 / Impact 83 / CR 5% / CD 50% /
  AC 94 / AM 93 / PR 0% / ER 1.2.
- 加点链: 核心技 Lv.7 > 连携技 Lv.12 = 普通攻击 Lv.12 = 特殊技 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11.
- 副词链条: 暴击率 > 暴击伤害 ≈ 攻击力% > 攻击力（固定值）≈ 穿透值.
- Drives: 4 件套沧浪行歌 (`ep-1754`) + 2 件套折枝剑歌 (`ep-1000`, alt 河豚电音 `ep-193`);
  4 号位暴击伤害+48%, 5/6 号位攻击力+30%;
  54 substats CR×13 + CD×16 + ATK%×16 + ATK×5 + PEN×4（按初始 4 词条规则重推，见铁律附则：
  她链条有 5 项，6 盘每盘都能凑满 4 个有效词条、无填充；但 2/4/5/6 号位被主词条各排掉
  一项，攻击力与穿透值各拿 5 / 4 条初始，CD 与 ATK% 由 21 / 20 降到 16 / 16）。
- Graduation panel (calculator-computed): ATK 3,907.5 / CR 50.6% / CD 238.8% / PEN 36.
- Teams: 叶照千 (叶瞬光/照/千夏), 叶琉千 (叶瞬光/琉音/千夏), 叶照妮 (叶瞬光/照/妮可).
- Cinemas: L1-3 backdrop 影画展示2, L4-6 backdrop 影画展示3 (one big frame each).
- Weapons: 首选 云霓孤光 (`ep-1751`); 下位 残心青囊/牺牲洁纯/骁骑礼赞; 备选 硫磺石; 四星 鎏金花信/强音热望.

## Second instance: 般岳 (`strategy/banyue/`)

火属性命破 S 级（entry_page_id 1626），证明「同一套流程可复用到非叶瞬光口径的代理人」：

- Base panel 60 级 0 突破: HP 8497 / ATK 784 / DEF 445 / Impact 95 / CR 5% / CD 50% /
  AC 90 / AM 89（命破无 pr/er 行，改由贯穿力 105 / 闪能自动累积 2 替代）。
- 加点链: 核心技 Lv.7 = 特殊技 Lv.12 > 普通攻击 Lv.12 = 连携技 Lv.12 > 支援技 Lv.12 = 闪避 Lv.11.
- Drives: 4 件套云岿如我 (`ep-1347`) + 2 件套折枝剑歌 (`ep-1000`, alt 啄木鸟电音 `ep-232`);
  4 号位暴击伤害+48%, 5 号位伤害加成+30%, 6 号位生命值+30%;
  54 substats CR×20 + CD×14 + HP%×12 + ATK%×6 + HP×2（按初始 4 词条规则重推，见铁律附则：
  1 号位固定生命排除小生命，命破的 6 盘每盘都能凑满 4 个有效词条，无填充；生命值进链条
  第 5 位，在 4/6 号位各顶 1 条初始，故 ATK% 由 8 降到 6）。
  爆率口径：面板 5% + 核心 14.4% + 20×2.4% = **67.4%**；社区工具里常见的 67.8% 对应
  基础 5.4% 或 2.42%/条，均与官方 WIKI（base 5%）及仓库 options.json（2.4/条）不符）。
- Graduation panel (`--rows hp,penforce,cr,cd`, 计算器实算): 生命值 19,927.8 /
  贯穿力 2,644.1 / 暴击率 67.4% / 暴击伤害 181.2%（贯穿力 = 0.3×攻击 + 0.1×生命）。
- Weapons: 首选 怒目金刚 (`ep-1721`); 下位 青溟笼舍 (`ep-1342`) / 海妖摇篮 (`ep-1664`);
  备选 青漪灵鼎 (`ep-1774`); 四星 燔火胧夜 (`ep-1612`) / 幻变魔方 (`ep-1343`) / 电波漫步 (`ep-1340`).
- Teams: 般琉卢 (般岳/琉音/卢西娅·艾洛温, 卢西娅套装月光骑士颂),
  般橘卢 (般岳/橘福福/卢西娅·艾洛温, 橘福福套装山大王).
- 属性图标 火 (`fire`): BWIKI 文件 `图标-火属性.png`
  (`https://patchwiki.biligame.com/images/zzz/e/e0/0gvubbv5rdog0jlqxf4gva9j15vzxmi.png`)
  → `frontend/public/images/attributes/fire.png`。

## Third instance: 克拉蕾·弗林特 (`strategy/claret/`)

电属性锋御 S 级（entry_page_id 2145），首位锋御代理人，证明同一套流程可以覆盖第三种面板模式：

- Base panel 60 级 0 突破: HP 5651 / ATK 626 / DEF 441 / Impact 93 / CR 22.5% / CD 50% /
  AC 80 / AM 79 / PR 0% / ER 1.5，另有锋御固有的**锐暴伤害 150%**（11 项面板）。
  核心加成只有暴击率一档：A-F 六段共 +28.8%（按两个 14.4% 核心选项计入，`--core2 cr`）。
- 加点链: 核心技 Lv.7 = 特殊技 Lv.12 > 普通攻击 Lv.12 = 连携技 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11。
  核心技在 WIKI 上只有成长表（描述挂在详情属性里），解析器靠 `core_detail_from_growth` 抽出
  「核心被动：苍白血宴」全文，并取**最后一段（F 级）的满级数值**（A-F 各段加成递增，
  如暴击率 17.5% → 30%、残痕积蓄 25% → 50%，取首段会变成「只升了一级」的效果）。
- Drives: 4 件套荆棘玫瑰 (`ep-2121`) + 2 件套河豚电音 (`ep-193`, alt 啄木鸟电音 `ep-232`)；
  4 号位暴击率+24%, 5 号位穿透率+24%, 6 号位防御力+48%;
  54 substats CR×19 + DEF%×15 + 穿透值×12 + DEF×5 + CD×3（按初始 4 词条规则重推，见铁律附则：
  5 号位穿透率排除的是「穿透率」不是「穿透值」，故 6 盘每盘都能凑满 4 个有效词条、无填充；
  3/4/6 号位被主词条各排掉一项（固定防御排小防御、4 号位暴击率排暴击率、6 号位防御力%排
  防御力%），暴击伤害在这三盘各顶 1 条初始，故 DEF 由 8 降到 5）。
- Graduation panel (`--rows def,actual_cr,cd,pv`, 计算器实算): 防御力 2,735.5 /
   实际暴击率 143.4% / 暴击伤害 64.4% / 穿透值 108。
   面板暴击率 = 22.5 + 28.8(核心) + 24(4号位) + 19×2.4 = 120.9%（不单独展示，由
   实际暴击率 143.4% = 暴击伤害 × 35% + 暴击率 间接呈现；暴击伤害由 3 条填充词条贡献）；
   社区口径的 129% 对应二件套选啄木鸟电音（+8% 暴击率），本页按需求方确认选河豚电音（+8% 穿透率）故为 120.9%。
- Weapons: 首选 猩红渴望 (`ep-2188`, S 锋御，基础**防御** 431 + 防御力 48%);
  下位 血髓秘匣 (`ep-2189`) / 喵运当头 (`ep-2200`); 过渡 月相·弦 (`ep-2190`, B 级)。
- Teams: 锋御体系 (克拉蕾/丽娜/洛克茜 `ep-2152`),
  均衡过渡 (克拉蕾/丽娜/珂蕾妲 `ep-318`)。
- 属性图标 电 (`electric`): BWIKI 文件 `图标-电属性.png`
  (`https://patchwiki.biligame.com/images/zzz/3/30/hu7kk6ul3ekpbfeafjoybl3u2q0xsng.png`)
  → `frontend/public/images/attributes/electric.png`。

### 本次顺带修掉的两处仓库缺口

1. 计算脚本对锋御音擎一律取 `weapon["baseAttack"]` 作基础值，而锋御音擎 `baseKind=def`、
   基础值是 `baseDefense`——面板防御力会少算整段音擎基础。已按 baseKind 取值。
2. `SET_OPTIONS` 缺「防御力 +16%」（荆棘玫瑰二件套），锋御代理人算毕业面板时该二件套
   根本无从建模且不报错。已按 `core/options.py` → `sync_presets.py --options` →
   三道数据闸门的流程补齐。

## Fourth instance: 莱特 (`strategy/lighter/`)

火属性击破 S 级（entry_page_id 950，卡吕冬之子），冰火减抗 + 延长失衡的辅助型击破：

- Base panel 60 级 0 突破: HP 8253 / ATK 722 / DEF 612 / Impact 119 / CR 5% / CD 50% /
  AC 91 / AM 90 / PR 0% / ER 1.2。核心加成：A/C/E 基础冲击力 +18、B/D/F 基础攻击力 +75。
- 加点链: **全部点满**——核心技 Lv.7 = 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 =
  支援技 Lv.12 = 闪避 Lv.12（需求方明确要求含闪避，链上全部用 `=` 连接）。
- Drives（`driveBuilds` 数组，默认一组、有多套时追加，版式同队伍；莱特按「单击破 /
  双击破」拆成两套）:
  ① 单击破：山大王 4 件套 + 震星迪斯科 2 件套（2 件套备选 摇摆爵士 / **月光骑士颂**，
  三者二件套同为能量自动回复 +20%）；
  ② 双击破：摇摆爵士 4 件套 + 震星迪斯科 / 山大王 2 件套（2 件套备选 月光骑士颂）。
   两套共用主词条：4 号位暴击率+24%, 5 号位火属性伤害+30%（备选攻击力+30%）,
   6 号位冲击力+24%（备选：无）;
   54 substats CR×9 + CD×23 + ATK%×15 + 穿透值×6 + 小攻击×1（按初始 4 词条规则重推，见铁律附则：
   4 号位暴击率排除暴击率，该盘只剩爆伤/大攻击/穿透值 3 个有效词条，第 4 条初始由小攻击顶上；
   穿透值进链条第 4 位，在 6 盘各拿 1 条初始，故 ATK% 由 22 降到 15）。
   `set2.main` / `set2.alt` 均可为单对象或**数组**（多套装并列渲染成多行首选/备选）；
   **二件套效果文案相同的套装会自动合并到同一行**——图标与名称并列、效果文案只显示
   一次（如 摇摆爵士 / 月光骑士颂 同为能量自动回复 +20%），效果不同的保持各自一行
   （如震星迪斯科的冲击力 vs 山大王的失衡值）。效果文案用仓库惯例写法：`效果 +N%`。
   山大王四件套的阈值是面板暴击率 ≥50%，**暴击率只需压线过 50**（需求方口径），
   多出来的条数全给爆伤与大攻击；山大王的二件套「失衡值+6%」选项表没有对应项，
   `--set4-effect none` 占位不建模。
- Graduation panel (`--rows imp,cr,cd,atk`, 计算器实算): 冲击力 202.8 / 暴击率 50.6% /
   暴击伤害 160.4% / 攻击力 2,524.5。两个机制阈值同时达标：冲击力 >170（额外能力
   [斗志昂扬]的增幅档）、暴击率 ≥50%（山大王四件套的额外暴伤）。
- Weapons: 首选 焰心桂冠 (`ep-951`); 下位 玉壶青冰 (`ep-678`) / 燃狱齿轮 (`ep-219`) /
  拘缚者 (`ep-957`); 四星 人为刀俎 (`ep-157`) / 贵重骨核 (`ep-141`)。击破只能用击破音擎。
- Teams: 伊萊耀 (伊芙琳·舒瓦利耶/莱特/耀嘉音；伊芙琳套装河豚电音),
  雨萊卡 (雨果·维拉德/莱特/莱卡恩；雨果套装河豚电音+啄木鸟电音，此队莱特为
  山大王+摇摆爵士、莱卡恩为山大王+震星迪斯科)。
- 属性图标 火 (`fire`) 仓库已有，无需人工放置。
- 模板扩展：`drives.set4` 支持可选 `alt4`（4 件套的备选），页面渲染在四件套说明下方；
  `teams[].members[].set4` 支持多套装图标（该字段名沿用 set4，实际可放任意套装）。

## Fifth instance: 蕾米埃尔·丹 (`strategy/remielle/`)

流明属性异常 S 级（entry_page_id 2076，达识结社/虚狩·时隙流明），后台耀变输出 + 三异常
体系引擎：

- Base panel 60 级 0 突破: HP 7482 / ATK 748 / DEF 600 / Impact 83 / CR 5% / CD 50% /
  AC 115 / AM 116 / PR 0% / ER 1.2。核心加成：A/C/E 异常精通 +54、B/D/F 基础攻击力 +75。
- 加点链: 核心技 Lv.7 = 特殊技 Lv.12 > 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 >
  闪避 Lv.11（耀变倍率分布在普攻/支援/终结技；特殊技含全队增伤；闪避基本不用）。
- Drives: 4 件套谶羽之誓 (`ep-2116`) + 2 件套自由蓝调 (`ep-191`, alt 混沌爵士 `ep-800`)；
  4 号位异常精通 +92（非 92%），5/6 号位攻击力 +30%。
  副词链条：攻击力% > 异常精通 > 攻击力 > 穿透值。
- **副词条分配（按「初始 4 词条 + 5 次强化」逐盘推导，非 54 条全给有效词条）**：
  4 个有效词条（攻击力% / 异常精通 / 攻击力 / 穿透值）里，2 号位主词条是攻击力→排除攻击力，
  4 号位主词条是异常精通→排除异常精通，5/6 号位主词条是攻击力%→排除攻击力%，
  这四盘的初始 4 条都只剩 3 个有效词条，缺口由非有效词条随机填充。逐盘表：

  | 盘位 | 主词条 | 被排除词条 | 初始 4 条 | 5 次强化去向 |
  | --- | --- | --- | --- | --- |
  | 1 | 固定生命 | 小生命 | 攻击力%、异常精通、攻击力、穿透值 | 异常精通 ×5 |
  | 2 | 固定攻击 | 攻击力 | 攻击力%、异常精通、穿透值、+1 填充 | 异常精通 ×5 |
  | 3 | 固定防御 | 小防御 | 攻击力%、异常精通、攻击力、穿透值 | 攻击力% ×2、异常精通 ×3 |
  | 4 | 异常精通 +92 | 异常精通 | 攻击力%、攻击力、穿透值、+1 填充 | 攻击力% ×5 |
  | 5 | 攻击力 +30% | 攻击力% | 异常精通、攻击力、穿透值、+1 填充 | 异常精通 ×5 |
  | 6 | 攻击力 +30% | 攻击力% | 异常精通、攻击力、穿透值、+1 填充 | 异常精通 ×5 |

  合计：有效词条 9+8+9+8+8+8 = 50 条 + 填充 4 条 = 54 条——
  **攻击力% ×11、异常精通 ×28、攻击力 ×5、穿透值 ×6、小生命 ×4**
  （`--sub-stats atk_pct:11,am:28,atk_flat:5,pen_val:6,hp_flat:4`，小生命是填充词条，不影响攻击/精通行）。
  强化投向：精通是她第一属性（异化系数 = 精通 × 0.02%、耀变倍率也吃精通），攻击力% 只补到
  攻击力 ≈ 4000 的团队 Buff 阈值即收手，余量全给精通。**不可**再写成 `ATK%×25 + AM×29`——
  那既超过 50 条有效词条上限，也没给 5 / 6 号位被排除的攻击力% 留出填充位。
- Graduation panel (`--rows atk,am`, 计算器实算): 攻击力 3,997.1 / 异常精通 574。
  攻击力压在 4000 线上：额外能力为全队提升等同自身攻击力 40% 的攻击力、上限 1600 点，
  3997.1 × 40% = 1598.8（差 1.2 点吃满）；再多吃一条攻击力%（12 条 → 4044.1）会多吃一条精通。
  换 12 条时的对照值：攻击力 4044.1 / 异常精通 565。
- Weapons: 首选 空羽复归之诗 (`ep-2109`); 下位 双生泣星 (`ep-212`) / 时流贤者 (`ep-915`) /
  灼心摇壶 (`ep-841`); 四星 触电唇彩 (`ep-210`)。
- Teams: 蕾维柏 (蕾米埃尔/维琳娜 `ep-1960` / 柏妮思 `ep-840`)——三异常队，
  维琳娜为风异常底座。
- 属性图标 流明 (`Lumiflux`，注意 slug 大写 L): BWIKI 文件 `图标-流明.png`
  （`https://patchwiki.biligame.com/images/zzz/1/1e/qdfppezb2bf43eijz5rzymy9dakg589.png`，
  与 火/电 的「图标-X属性.png」命名不同）→ `frontend/public/images/attributes/lumiflux.png`。

## Sixth instance: 柚叶 (`strategy/yuzuha/`)

物理支援 S 级（entry_page_id 1386，怪啖屋），证明支援角色同样要定制口径，且**展示行可以是 3 行**：

- Base panel 60 级 0 突破: HP 8829 / ATK 683 / DEF 612 / Impact 86 / CR 5% / CD 50% /
  AC 88 / AM 93 / PR 0% / ER 1.2。核心满级 = 异常掌控+36 + 基础攻击力+75
  （`--core1 ac --core2 atk_base`；注意支援/部分角色核心**不给暴击率**，别默认 `--core1 cr`）。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 > 支援技 Lv.12 > 闪避 Lv.7。
- Drives（需求方指定的三套 4 件套方案，`driveBuilds` 多方案数组 + 同一 2 件套）:
  月光骑士颂 (`ep-1551`) / 静听嘉音 (`ep-1001`) / 自由蓝调 (`ep-191`) 均配
  法厄同之歌 (`ep-1194`)；**2 件套只保留首选、不设备选**（`set2.alt` 去掉而非填「无」，
  模板对缺失的 alt 只渲染首选行）；主词条 4 号异常精通+92（备选仅攻击力 +30%）/
  5 号攻击力（备选无）/ 6 号异常掌控（备选无）；
  54 substats 攻击力%×24 + 异常精通×16 + 攻击力×5 + 填充词条×9（副词链条只有 3 项：
  攻击力% > 异常精通 > 攻击力；按初始 4 词条规则重推后，2 号位排攻击力、4 号位排精通、
  5 号位排攻击力%，各有 1~2 条初始得由非有效词条补，故有效词条 45 + 填充 9。
  填充词条取小生命/小防御（均不影响攻击/精通/掌控三行）；攻击力只保住 5 条初始）。
- Graduation panel (`--rows atk,am,ac`，计算器实算): 攻击力 3,382.4 / 异常精通 329 /
    异常掌控 171.1。**展示行不必凑 4 行**：按该代理人的结算口径取，页面 CSS 需把
    `.base-panel--graduation` 的 4 列网格改为对应列数（柚叶：桌面 3 列、窄屏单列）。
    副词条条数按优先级链递减分配——面板不展示双爆时，不要再给暴击类留条数。
    另附**非满配面板**（`--alt-sub-stats atk_pct:8 --alt-disc4 atk_pct_30 --alt-disc5
    atk_pct_30 --alt-disc6 ac_pct_30`，人为界定 8 词条，4/5 号攻击力%、6 号掌控）：
    攻击力 3,022.6 / 异常精通 93 / 异常掌控 171.1，渲染在满配面板下方。
- 4 号位「精通 vs 攻击」的可测判定：带精通后面板攻击力是否仍达标（本例 3,382.4 ≥ 3000 → 取精通）。
   判定规则应由需求方给出，不要自行假设；换主词条会连带改变副词条分配，须整组重推。
- Weapons: 首选 狸法七变化 (`ep-1463`); 下位 思络成歌 (`ep-1826`); 备选 啜泣摇篮 (`ep-218`);
  四星 逍遥游球 (`ep-213`) / 好斗的阿炮 (`ep-486`)。
  音擎特效文本一律从 WIKI 音擎详情页抓取（`entry_page_v2` 的 `multi_table` 组件；
  注意 component_id 在组件内而非模块级），不得凭记忆撰写。
- Teams: 爱柚薇 (爱丽丝 `ep-1385` / 柚叶 `ep-1386` / 薇薇安 `ep-1276`)——物理 + 以太
  双异常队，满足柚叶额外能力的「队内异常角色」条件。成员套装：爱丽丝 獠牙重金属 (`ep-104`)、
  柚叶 月光骑士颂、薇薇安 法厄同之歌。同阵营加成需核实阵营：悠真
  （`ep-997`）是对空六课·电强攻，**不触发**柚叶的怪啖屋加成。
- 属性图标 物理 (`physical`): BWIKI 文件 `图标-物理.png`
  （`https://patchwiki.biligame.com/images/zzz/6/6e/o5jjbnrex63x3opdrrxaaimti4dtrid.png`）
  → `frontend/public/images/attributes/physical.png`。
- 计算脚本：`TOTAL_LABELS` 新增 `ac`（异常掌控）。异常类角色若核心给异常掌控、
  额外能力按异常掌控结算，用它做展示行；键早已存在于计算器 totals 与前端 ResultPanel。

## Seventh instance: 洛克茜 (`strategy/roxy/`)

风属性击破 S 级（entry_page_id 2152，弗林特工坊），净化 / 浸染体系速切击破；第七个代理人，
也是第一个把主词条押在**能量回复**上的页面：

- Base panel 60 级 0 突破: HP 8418 / ATK 666 / DEF 641 / Impact 100 / CR 5% / CD 50% /
  AC 110 / AM 63 / PR 0% / ER 1.2。核心满级 = 暴击率+14.4% + 基础攻击力+75（`--core1 cr --core2 atk_base`）。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 连携技 Lv.12 > 支援技 Lv.12 > 普通攻击 Lv.12 > 闪避 Lv.11。
- 机制要点（写文字攻略前先读 WIKI 文本）：核心被动[热夜初拥]每 25 点能量给 1 点[风能]（上限 3），
  初始能量自动回复超过 1.2 的部分每 0.01 换攻击力（上限 +480）与冲击力（上限 +40）——
  **能量回复是她的隐藏刚需**；[特殊技：恕不远送]命中[风化]敌人触发[净化]重置[浸染]，
  队友触发浸染/净化时按她的暴击率给全队暴击伤害（非锋御上限 22%，需 55% 暴击率吃满）；
  额外能力[辉金心脏]需队内有强攻 / 命破 / 锋御角色。
- Drives: 山大王 4 件套 (`ep-1346`) + 摇摆爵士 2 件套 (`ep-231`，备选 震星迪斯科 / 啄木鸟电音)；
  主词条 4 号暴击率+24% / 5 号攻击力+30% / **6 号能量回复+60%（备选冲击力+24%）**；
  54 substats 暴击率×7（面板 60.2%，过山大王 50% 阈值并吃满 22% 团队暴伤）+
  暴击伤害×23 + 攻击力%×24。山大王的二件套「失衡值+6%」选项表没有对应项，`--set4-effect none` 占位。
- Graduation panel (`--rows imp,cr,cd,atk`, 计算器实算): 冲击力 100 / 暴击率 60.2% /
  暴击伤害 160.4% / 攻击力 3,253.1。冲击力只显示基础 100：失衡值提升来自音擎与套装、
  不计入面板条；选能量回复 6 号位就是主动放弃冲击力面板换核心被动上限。
- 非满配（`--alt-sub-stats cr:4,cd:8,atk_pct:8`，20 词条，暴击率过 50% 档 + 爆伤/攻击力% 均衡）：
  冲击力 100 / 暴击率 53% / 暴击伤害 88.4% / 攻击力 2,555.2。
- Weapons: 首选 绯月银棺 (`ep-2234`, S 713 能量自动回复 60%，暴击率+24% + 无视风抗 +
  强化特殊技失衡值与全队伤害)；下位 福虓炉炉 (`ep-1427`) / 首席跟班 (`ep-2088`)；
  备选 燃狱齿轮 (`ep-220`) / 玉壶青冰 (`ep-678`)；四星 人为刀俎 (`ep-157`)。击破只能用击破音擎。
  专武定位法：遍历 `data/weapon-presets.json` 里 roleTag=击破 的音擎，抓各自 `entry_page_v2`
  的 `double_col_table`「推荐代理人」表找该代理人。
- Teams: 克洛丽 (克拉蕾 `ep-2145` / 洛克茜 `ep-2152` / 丽娜 `ep-316`——锋御触发额外能力、
  同阵营弗林特工坊)、佩洛耀 (佩洛伊斯 `ep-1958` / 洛克茜 `ep-2152` / 耀嘉音 `ep-1109`)。
  佩洛伊斯终结技对[浸染]敌人有额外伤害（WIKI 文本核实），与净化重置浸染互相成就；
  强攻身份同时满足额外能力条件。
- 属性图标 风 (`wind`): BWIKI 文件 `图标-风.png`
  （`https://patchwiki.biligame.com/images/zzz/f/fa/btq011tioeuwglvyo8gpcvv5wi6ukj9.png`）
  → `frontend/public/images/attributes/wind.png`。

## Eighth instance: 希格莉德 (`strategy/sigrid/`)

冰属性强攻 S 级（entry_page_id 2079，空域巡戍局），普攻系驻场主C；第八个代理人，
展示了**「暴击率来自状态增益而非面板」**时面板口径可以反常识地低：

- Base panel 60 级 0 突破: HP 7788 / ATK 863 / DEF 606 / Impact 93 / CR 5% / CD 50% /
  AC 92 / AM 90 / PR 0% / ER 1.2。核心满级 = 暴击率+14.4% + 基础攻击力+75
  （`--core1 cr --core2 atk_base`）。
- 加点链: 核心技 Lv.7 > 普通攻击 Lv.12 = 连携技 Lv.12 = 特殊技 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11。
- 机制要点（写攻略前读 WIKI 文本）：核心被动[天空骑士]在激活/刷新[巡空枪势]时
  **暴击率 +66%**（持续 8 秒，重复触发可延至 40 秒），因此面板暴击率只需约 34% 即可与增益
  叠满 100%——**超过 34% 的暴击率副词条在增益期是纯浪费**，本条务必与需求方确认口径。
  额外能力[天际联军]需队内有[支援]或[击破]角色（加攻击 + 对[浸染]敌人增伤）。
- Drives: 拂晓生花 4 件套 (`ep-1552`) + 折枝剑歌 2 件套 (`ep-1000`，备选 河豚电音 / 激素朋克)；
  主词条 4 号暴击伤害+48% / 5 号冰属性伤害+30% / 6 号攻击力+30%；
  54 substats 暴击率×6（面板 33.8%）+ 暴击伤害×26 + 攻击力%×22。
  拂晓生花二件套「普攻伤害 +15%」选项表无对应项，`--set4-effect none` 显式不建模
  （不传 flag 会落回 BUILD 默认的 hp_pct_10，那是张冠李戴）。
- Graduation panel (`--rows atk,cr,cd,dmg`, 计算器实算): 攻击力 3,552 / 暴击率 33.8% /
  暴击伤害 286.8% / 增伤 30%。**面板暴击率 33.8% 看着离谱但是对的**：+66% 来自状态增益，
  需求方口径「压 34% 线」。
- 非满配（`--alt-sub-stats cr:6,cd:16,atk_pct:13`，35 词条，同满配逻辑缩水）：
  攻击力 3,106.2 / 暴击率 33.8% / 暴击伤害 238.8% / 增伤 30%。
- Weapons: 首选 骁骑礼赞 (`ep-2162`)；下位 牺牲洁纯 (`ep-1197`)；备选 硫磺石 (`ep-223`) /
  残心青囊 (`ep-991`)；四星 星徽引擎 (`ep-156`) / 鎏金花信 (`ep-744`)。
  专武定位法同洛克茜：遍历 `data/weapon-presets.json` 里 roleTag=强攻 的音擎，抓各自
  `entry_page_v2` 的推荐代理人表比对。
- Teams: 希诺耀 (希格莉德 `ep-2079` / 诺姆 `ep-1962` / 耀嘉音 `ep-1109`)、
  希洛耀 (希格莉德 / 洛克茜 `ep-2152` / 耀嘉音 `ep-1109`)——击破 + 支援双身份满足额外能力。
- 属性图标 冰 (`ice`): BWIKI 文件 `图标-冰属性.png`
  （`https://patchwiki.biligame.com/images/zzz/0/01/0smfnv2vrbfooab5li9ja69yxc8u0ea.png`）
  → `frontend/public/images/attributes/ice.png`。

## Ninth instance: 诺姆 (`strategy/norma/`)

火属性击破 S 级（entry_page_id 1962，外务筹策局），炮塔后场流击破；第九个代理人，
展示了**「面板暴击率越高越好」**的第三类口径（核心把超 50% 的暴击率转成爆伤与失衡值）：

- Base panel 60 级 0 突破: HP 7799 / ATK 687 / DEF 582 / Impact 106 / CR 5% / CD 50% /
  AC 99 / AM 98 / PR 0% / ER 1.2。核心满级 = 暴击率+14.4% + 基础攻击力+75
  （`--core1 cr --core2 atk_base`）。
- 加点链: 核心技 Lv.7 > 连携技 Lv.12 = 特殊技 Lv.12 = 普通攻击 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11。
- 机制要点（写攻略前读 WIKI 文本）：核心[精准制导]要求**面板暴击率超过 50%**，超过部分
  每 1% 换 0.86% 暴击伤害（上限 +43%）与 0.44% 失衡值（上限 +22%）——暴击率起点 43.4%
  （5% 基础 + 14.4% 核心 + 专武副词条 24%），DPS 最优点实测在 ≈99%（近满爆），与
  希格莉德「压 34% 线」正好相反。核心还按**自身贯穿力**换算攻击力（每点 +1.25，上限 +1200），
  但 WIKI 基础面板的贯穿力行无数值（基础为 0）、standard 模式也不建模，面板不含该加成。
  额外能力[集群优势]需队内有强攻 / 命破 / 同阵营角色（外务筹策局无其他可选队友）。
- Drives: 山大王 4 件套 (`ep-1346`) + 摇摆爵士 2 件套 (`ep-231`，备选 震星迪斯科 / 激素朋克)；
  主词条 4 号暴击率+24% / 5 号火属性伤害+30% / **6 号冲击力+24%**（备选攻击力+30%）；
  54 substats 暴击率×13（面板 98.6%）+ 暴击伤害×26 + 攻击力%×15。
  山大王的二件套「失衡值+6%」选项表无对应项，`--set4-effect none` 占位。
- Graduation panel (`--rows imp,cr,cd,atk`, 计算器实算): 冲击力 131.4 / 暴击率 98.6% /
  暴击伤害 174.8% / 攻击力 2,454.8（6 号位改攻击力 +30% 则攻击力 2,897.2、冲击力回落到 106）。
- 非满配（`--alt-sub-stats cr:7,cd:13,atk_pct:10`，30 词条，暴击率过 50% 档 + 爆伤/攻击力% 均衡）：
  冲击力 131.4 / 暴击率 84.2% / 暴击伤害 112.4% / 攻击力 2,233.5。
- Weapons: 首选 首席跟班 (`ep-2088`)；下位 福虓炉炉 (`ep-1427`)；备选 昨夜来电 (`ep-1689`) /
  索魂影眸 (`ep-1243`)；四星 人为刀俎 (`ep-157`)。专武定位法同洛克茜 / 希格莉德：
  遍历 `data/weapon-presets.json` 里 roleTag=击破 的音擎，抓各自 `entry_page_v2`
  的推荐代理人表比对。
- Teams: 希诺耀 (希格莉德 `ep-2079` / 诺姆 `ep-1962` / 耀嘉音 `ep-1109`)——希格莉德的强攻
  身份满足额外能力条件；失衡窗口接她的敛枪式爆发。
- 属性图标 火 (`fire`) 仓库已有，无需人工放置。

## Tenth instance: 维琳娜·艾嘉德 (`strategy/velina/`)

风属性异常 S 级（entry_page_id 1960，外务筹策局），后场异常副C——**能量自动回复驱动核心**
的第四类面板口径（与蕾米埃尔同为 standard 模式，但核心不吃爆率吃 ER）：

- Base panel 60 级 0 突破: HP 7788 / ATK 797 / DEF 612 / Impact 86 / CR 5% / CD 50% /
  AC 112 / AM 111 / PR 0% / ER 1.2。核心满级 = 异常精通+54 + 基础攻击力+75
  （`--core1 am --core2 atk_base`，与蕾米埃尔同构）。
- 机制要点（写攻略前读 WIKI 文本）：核心[风华盈袖]只结算「初始 ER 超过 1.2 的部分」——
  每 0.01 换 0.21% 伤害（上限 35%）与 0.5 点异常掌控（上限 84 点），**双上限线在 ER 2.87**。
  [风华]≥90 发动[强化特殊技：风切变·风暴眼]召唤[广域气旋]（5 秒、每 0.5 秒一击）并触发
  上一位角色的[快速支援]；触发[乱流]得[风蚀]，2 点[风蚀]时下次[乱流]倍率 +150% 并改召
  广域气旋；气旋命中[浸染]敌人触发[赋彩]染色减抗（风/对应属性积蓄抗性各 -7%）；气旋
  消散爆炸命中风异常状态敌人额外结算[异放]（固定 145%/255% 倍率）。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 > 普通攻击 Lv.12 = 连携技 Lv.12 > 支援技 Lv.12 >
  闪避 Lv.7（需求方口径：闪避点到 7 即止）。注意连携技 tab 同时含终结技。
- Drives（`driveBuilds`，set4 数组双方案 + 同一 ER 二件套）:
  4 件套 **呼啸沙龙** (`ep-2038`，2pc 风属性伤害+10%，4pc 强化特殊技叠精通 25×2 层 +
  [风化]后增伤 18%)，备选 4 件套 **静听嘉音** (`ep-1001`，风暴眼/终结技频繁触发快速支援时
  叠[嘉音])，每项带 `scene`；2 件套同效果并列首选的**摇摆爵士 / 月光骑士颂**
  （同为能量自动回复+20%，`set2.main` 数组、无 alt）；主词条 4 号位异常精通+92（备选无）/
  5 号位增伤+30%（备选攻击力+30% / 穿透率+24%）/ **6 号位能量回复+60%**（备选无）；
  54 substats 异常精通×24 + 攻击力%×18 + 攻击力×6 + 穿透值×6。
  **呼啸沙龙二件套「风属性伤害+10%」选项表无对应项，`--set4-effect none` 显式不建模。**
- Graduation panel (`--rows atk,am,ac`, 计算器实算): 攻击力 2,870.9 / 异常精通 473 /
  异常掌控 112。ER = 1.2×(1+0.6 专武+0.6 六号位+0.2 二件套) = **2.88**，越过双上限线
  （局内 +35% 伤害、+84 异常掌控，计算器与四件套局内特效一样不建模，面板只呈静态值）；
  精通 473 = 111 基础 + 54 核心 + 92 四号位 + 216 副词条（专武局内 +110 不进面板）。
- 非满配（`--alt-sub-stats am:16,atk_pct:11,atk_flat:4`，31 词条，需求方口径「攻击 2500 /
  异常精通 400」、条数由该目标倒推：16 条精通正好 401、攻击力%+攻击力 15 条压到 2,500.1；
  主词条与二件套沿用满配，故 ER 仍是 2.88）：
  攻击力 2,500.1 / 异常精通 401 / 异常掌控 112。
- Weapons: 首选 琳琅鎏心 (`ep-2030`，ER+60% 副词条 + 精通+110 + 乱流/风化+22% + 全队精通+96)；
  下位 灼心摇壶 (`ep-841`，后场 ER+1.2/秒、强化特殊技叠伤害后场翻倍) / 双生泣星 (`ep-212`)；
  四星 触电唇彩 (`ep-210`)。专武靠效果文本「发动[强化特殊技]造成**风属性**伤害」与角色对应
  （同页 ep-1964 朔月裁霜是冰属性异常的音擎，不能按 id 邻近蒙）。
- Teams: 蕾维柏 (蕾米埃尔 `ep-2076` / 维琳娜 `ep-1960` / 柏妮思 `ep-840`)——三异常队，
  沿用蕾米埃尔页已确认的阵容与成员套装（谶羽之誓 / 呼啸沙龙 / 自由蓝调）。
- 属性图标 风 (`wind`) 仓库已有，无需人工放置。

## Eleventh instance: 佩洛伊斯 (`strategy/pyrois/`)

以太属性强攻 S 级（entry_page_id 1958，法厄同），**喧响值/日珥双资源 + 4 选 1 终结技** 机制：

- Base panel 60 级 0 突破: HP 7673 / ATK 849 / DEF 612 / Impact 94 / CR 5% / CD 50% /
  AC 94 / AM 93 / PR 0% / ER 1。核心满级 = 暴击率 +14.4% + 基础攻击力 +75
  （`--core1 cr --core2 atk_base`）。
- 机制要点（写攻略前读 WIKI 文本）：喧响值上限 2000 点（普攻/特殊/闪避/支援/终结技回复），
  日珥上限 30 点（同类招式 + 自动回复）。终结技 4 选 1：晨曦（暴伤+40%）、正午（以太增伤+40%）、
  黄昏（穿透率+40%）、深夜（攻击力+40%）。强化特殊技「日华」突进期可完美格挡（免疫、
  给护盾 8% 最大生命值 10 秒、失衡值 +10%）。专武「日蚀」终结技后无视 16~22% 以太抗性 45 秒。
  影画 L1 进场喧响值 +1000 暴率 +8%、L2 终结技回喧响值 +1500 上限 +1000、
  L3 五技能 +2、L4 完美格挡护盾+失衡值、L5 五技能再 +2、L6 待更新。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 连携技 Lv.12 = 普通攻击 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11。
- Drives: 4 件套 **拂晓行纪** (`ep-2029`) + 2 件套首选 **河豚电音** (`ep-193`，穿透率 +8%) /
  备选 摇摆爵士 / 月光骑士颂（能量回复 +20%）/ 折枝剑歌（攻击力 +10%）；
  主词条 4 号暴击率 +24%（备选暴击伤害 +48%）/ 5 号穿透率 +24%（备选增伤 +30%）
  / 6 号攻击力 +30%（备选无）；副词条优先级：**暴击率 > 暴击伤害 ≈ 攻击力% > 攻击力 > 穿透值**；
  54 substats = 暴击率×24 + 暴击伤害×10 + 攻击力%×12 + 攻击力×6 + 穿透值×2。
  拂晓行纪 2 件套「以太伤害+10%」选项表无对应项，4 件套「以太代理人暴击伤害+30%、
  强化特殊技/终结技后攻击力+10%」为局内增伤，均用 `--set4-effect none` 显式不建模。
- Graduation panel (`--rows atk,cr,cd,pv`, 计算器实算): 攻击力 3,638.5 / 暴击率 101%（溢出即满） /
  暴击伤害 98% / 穿透值 18。
- 非满配（`--alt-sub-stats cr:14,cd:6,atk_pct:6,atk_flat:4`，30 词条，需求方口径「30 词条」）：
  攻击力 3,305.9 / 暴击率 77% / 暴击伤害 78.8% / 穿透值 0。
- Weapons: 首选 **日冕遗蜕** (`ep-2031`，S 713 攻击力 30%、暴击率 +20%、专属「日蚀」)；
  无其他以太强攻音擎可触发专属被动。专武定位法同前：遍历 `data/weapon-presets.json`
  里 roleTag=强攻 的音擎，抓各自 `entry_page_v2` 推荐代理人表比对。
- Teams: 佩诺耀 (佩洛伊斯 `ep-1958` / 诺姆 `ep-1962` / 耀嘉音 `ep-1109`)——诺姆火击破
  触发额外能力[集群优势]需强攻/命破/同阵营，耀嘉音提供全队增伤/护盾/回能。
- 属性图标 以太 (`ether`): BWIKI 文件需人工放置到
  `frontend/public/images/attributes/ether.png`。

## Twelfth instance: 星徽·比利 (`strategy/starlight-billy/`)

物理属性命破 S 级（entry_page_id 1927，狡兔屋），**决意/生命值双资源 + 摩托骑乘** 机制：

- Base panel 60 级 0 突破: HP 8497 / ATK 784 / DEF 445 / Impact 95 / CR 5% / CD 50% /
  AC 90 / AM 89 / PR - / ER -，额外贯穿力 105、闪能自动累积 2。核心满级 = 暴击率 +14.4% + 基础攻击力 +75
  （`--core1 cr --core2 atk_base`）。
- 机制要点（写攻略前读 WIKI 文本）：核心被动按最大生命值 10:1 转化贯穿力（基础 105 + 8497/10 ≈ 955），招式全为贯穿伤害无视防御。
  [决意] 上限 120（游标 100），普攻/特殊/闪避/支援/终结技/连携回复。生命 > 25% 点按[动力压制]消耗 50% 生命得 90% 暴伤 45 秒；
  [决意] ≥ 100 长按普攻放[最高马力星光]（高倍率贯穿伤、回血）。终结技[骑士飞踢]回 15 点[决意]、连携技[骑士漫步]回 15 点。
  影画 L1 进场闪能 +60 无视物抗 18%、L2 爆发技伤 +50% 涡轮增压直通孤轮特技暴伤 +50%、L3/L5 五技能 +2、
  L4 动力压制叠暴伤 8%×2 / 非操作角色血 <35% 自动回血、L6 终结技/最高马力星光贯穿伤 +18%、煊赫星辉额外贯穿伤。
- 加点链: 核心技 Lv.7 > 普通攻击 Lv.12 = 特殊技 Lv.12 = 连携技 Lv.12 > 支援技 Lv.11 > 闪避 Lv.7。
- Drives: 4 件套 **云岿如我** (`ep-1347`) + 2 件套首选 **折枝剑歌** (`ep-1000`，暴击伤害 +16%) /
  备选 **啄木鸟电音** (`ep-232`，暴击率 +8%)；
  主词条 4 号暴击伤害 +48%（备选暴击率 +24%）/ 5 号物理伤害 +30%（备选穿透率 +24%）
  / 6 号生命值 +30%（备选攻击力 +30%）；副词条优先级：**暴击率 > 暴击伤害 > 生命值% > 攻击力% > 攻击力**；
  54 substats = 暴击率×20 + 暴击伤害×14 + 生命值%×12 + 攻击力%×8（沿用般岳命破口径）。
  云岿如我 2 件套「生命值 +10%」计入贯穿力；4 件套暴击率叠层与贯穿伤害 +10% 为局内增伤，
  `--set4-effect hp_pct_10` 仅建模二件套。
- Graduation panel (`--rows hp,penforce,cr,cd --mode rupture`, 计算器实算): 生命值 19,703.8 /
  贯穿力 2,650.0 / 暴击率 67.4% / 暴击伤害 181.2%。
- 非满配（`--alt-sub-stats cr:10,cd:6,hp_pct:8,atk_pct:6`，30 词条，需求方口径「30 词条」）：
  生命值 18,684.2 / 贯穿力 2,519.7 / 暴击率 43.4% / 暴击伤害 142.8%。
- Weapons: 首选 **辉骑面铠** (`ep-2002`，S 713 生命值 30%、专属被动)；
  下位 青溟笼舍 (`ep-1342`) / 海妖摇篮 (`ep-1664`)；备选 青漪灵鼎 (`ep-1774`)；
  四星 燔火胧夜 (`ep-1612`) / 幻变魔方 (`ep-1343`) / 电波漫步 (`ep-1340`)。
  专武定位法同前：遍历 `data/weapon-presets.json` 里 roleTag=命破 的音擎，抓各自 `entry_page_v2`
  推荐代理人表比对。
- Teams: 星琉卢 (星徽·比利 `ep-1927` / 琉音 `ep-1624` / 卢西娅 `ep-1533`)、
  星橘卢 (星徽·比利 `ep-1927` / 橘福福 `ep-1301` / 卢西娅 `ep-1533`)——琉音/橘福福提供快速失衡/击破，
  卢西娅提供贯穿力加成与回血。
- 属性图标 物理 (`physical`) 仓库已有，无需人工放置。

## Thirteenth instance: 普罗米娅 (`strategy/promeia/`)

冰属性异常 S 级（entry_page_id 1926），**寒蚀值/霜刑双资源 + 异放体系驻场主 C**：

- Base panel 60 级 0 突破: HP 7788 / ATK 797 / DEF 612 / Impact 86 / CR 5% / CD 50% /
  AC 112 / AM 114 / PR 0% / ER 1.2。核心满级 = 异常掌控 +36 + 基础攻击力 +75
  （`--core1 ac --core2 atk_base`，与柚叶同构）。
- 机制要点（写攻略前读 WIKI 文本）：核心被动[盗火]要求**初始异常掌控 >150**，每超 1 点
  换 1.5 自身精通 + 0.35% 全队[异放]伤害——基础 112 + 核心 36 = 148 差 2 点过线，
  6 号位掌控 / 专武掌控副词条 / 二件套掌控都是为放大该转化。[寒蚀值]上限 100（普攻/特殊/
  闪避/支援命中回复，冻结/紊乱/乱流/匿影 +5/5/5/10，队友异放命中 +15），≥50 转 1 点[霜刑]
  （上限 2、进场自带 2 点）；[绝裁]终结一击命中带属性异常敌人时耗 1 霜刑触发异放，
  **固定 635% 倍率**（连携 100% / 终结技 250%）；异放命中回 100 喧响值（0.5 秒一次）；
  终结技给[寒誓]，之后可直衔接[重霜]。影画 L1 终结技补霜刑 + 全队异放无视 20% 防御、
  L2 精通+40 且霜刑异放倍率+120%、L3/L5 五技能+2、L4 触发异放回寒蚀值、
  L6 耗霜刑额外异放 200% + 回寒蚀 + 回喧响。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 > 连携技 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11。
- Drives: 4 件套 **囚徒手记** (`ep-1906`) + 2 件套首选 **法厄同之歌** (`ep-1194`，异常掌控 +8%) /
  备选 摇摆爵士 (`ep-231`，能量自动回复 +20%)；
  主词条 4 号异常精通+92%（备选暴击率+24%）/ 5 号增伤+30%（备选穿透率+24%）
  / **6 号异常掌控+30%**（备选能量自动回复+60%）；副词条优先级：
  **异常精通 > 攻击力% > 穿透值 > 攻击力**；54 substats = 异常精通×26 + 攻击力%×14 +
  穿透值×10 + 攻击力×4。囚徒手记 2 件套「冰属性伤害+10%」选项表无对应项，
  4 件套「异放触发精通+48、冻结时异常/紊乱伤害+16%」为局内增伤，`--set4-effect none` 显式不建模。
- Graduation panel (`--rows atk,am,ac`, 计算器实算): 攻击力 2,642.7 / 异常精通 440 /
  异常掌控 248.6。掌控 248.6 = (112+36) × (1 + 30% 专武 + 8% 法厄同 + 30% 六号位)，
  远超核心 150 阈值（局内转化约 148 精通与 34.5% 全队异放伤害，计算器同样不建模）。
- 非满配（`--alt-sub-stats am:14,atk_pct:8,pen_val:6,atk_flat:2`，30 词条）：
  攻击力 2,319.4 / 异常精通 332 / 异常掌控 248.6（掌控不受副词条影响，两份面板一致）。
- Weapons: 首选 **朔月裁霜** (`ep-1964`，S 713 异常掌控 30%、冰伤+35% + 强化特殊技后
  异常伤害+15%×2)；下位 壳中之灵 (`ep-1883`) / 嵌合编译器 (`ep-214`)；
  四星 触电唇彩 (`ep-210`) / 双生泣星 (`ep-212`)。
  专武定位法同前：遍历 `data/weapon-presets.json` 里 roleTag=异常 的音擎，抓各自
  `entry_page_v2` 推荐代理人表比对。
- Teams: 普南柚 (普罗米娅 `ep-1926` / 南宫羽 `ep-1852` / 柚叶 `ep-1386`)、
  普柚薇 (普罗米娅 `ep-1926` / 柚叶 `ep-1386` / 薇薇安 `ep-1276`)——南宫羽蓄力破韧开失衡
  窗口，薇薇安后台异放配合；柚叶两队共用（攻击加成 + 补伤害，可置普罗米娅之前染冰）。
- 属性图标 冰 (`ice`) 仓库已有，无需人工放置。

## Fourteenth instance: 希希芙 (`strategy/cissia/`)

电属性强攻 S 级（entry_page_id 1861，都市秩序部），**毒素/蛇影双资源 + 全队电伤减防**（首位单属性减防角色）：

- Base panel 60 级 0 突破: HP 7673 / ATK 863 / DEF 606 / Impact 93 / CR 5% / CD 50% /
  AC 94 / AM 93 / PR 0% / ER 1.2。核心满级 = **基础能量自动回复 +0.36** + 基础攻击力 +75
  （`--core1 er_base --core2 atk_base`；她核心不给暴击率，别默认 `--core1 cr`）。
- 机制要点（写攻略前读 WIKI 文本）：[毒素]进场 3 点（L1 提至 6），普攻第四段 +2（失衡 +1）、
  长按[毒牙] +3（每多耗 20 能量再 +1）、连携/终结技各 +3；每 6 毒素转 1 层[蛇影]（至多 3、
  进场 1 层），[蛇吻]耗 1 层并倾泻全部毒素触发[蚀骨]（附加自身 335% 攻击力电伤、每次触发自身
  暴击率 +6% 至多 3 层）；有毒素时每 5 秒自动触发一次[蚀骨]。核心减防：全队电伤无视 6% 防御，
  初始 ER 超 1.4 后每超 0.12 再多 1%（至多 25%）；队内 1/2 名电属性角色时蚀骨失衡值 +40%/60%。
  终结技开[以太帷幕：冷血]（30 秒全队暴伤 +5%）。影画 L1 毒素 3→6 + 减穿×1.4 + 全队无视 5% 电抗、
  L2 连携/终结技命中失衡 +3 毒素且蛇吻 +35%、L3/L5 五技能 +2、L4 [觉悟]层数换不耗毒素的特殊蚀骨、
  L6 蚀骨印记由全队攻击命中触发。
- 加点链: 核心技 Lv.7 > 普通攻击 Lv.12 > 特殊技 Lv.12 > 连携技 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11。
- Drives: 4 件套 **拂晓生花** (`ep-1552`) + 2 件套首选 **啄木鸟电音** (`ep-232`，暴击率 +8%) /
  备选 折枝剑歌 (`ep-1000`) / 摇摆爵士 (`ep-231`) / 月光骑士颂 (`ep-1551`)；
  主词条 4 号暴击率 +24%（备选暴击伤害 +48%）/ 5 号攻击力 +30%（备选增伤 +30%）/
  **6 号能量自动回复 +60%**（备选攻击力 +30%）；副词条优先级：
  **暴击率 > 暴击伤害 > 攻击力% > 穿透值 > 攻击力**；54 substats = 暴击率×10 + 暴击伤害×27 +
  攻击力%×10 + 穿透值×4 + 攻击力×3。拂晓生花 2 件套「普攻伤害 +15%」选项表无对应项，
  4 件套为局内增伤，`--set4-effect none` 显式不建模；她自带约 20% 减防，二件套不选河豚电音（稀释）。
- Graduation panel (`--rows atk,cr,cd,pv`, 计算器实算): 攻击力 3,014.6 / 暴击率 61% /
  暴击伤害 179.6% / 穿透值 36。暴击率口径：核心给 ER 不给 CR，面板 5% + 4 号位 24% +
  二件套 8% + 副词条 10×2.4% = 61%；局内再叠专武 +20% 与蚀骨 3 层 +18% 即接近满暴，
  故副词条只给 10 条 CR，余量全给爆伤与攻击。
- 非满配（`--alt-sub-stats cr:6,cd:15,atk_pct:6,pen_val:2,atk_flat:1`，30 词条）：
  攻击力 2,778.5 / 暴击率 51.4% / 暴击伤害 122% / 穿透值 18。
- 6 号位 ER 是伤害词条但不能进面板：`TOTAL_LABELS` 没有 er 行，毕业配装下
  ER = 1.2×(1+0.36 核心 +0.6 专武 +0.6 六号位) = 3.07 → 减防约 19.9%（局内，计算器不建模），
  口径写进文字攻略与面板说明。
- Weapons: 首选 **鳞齿寻踪** (`ep-1941`，S 713 ER 60%、暴击率 +20%、耗能获电伤无视 30% 防御)；
  下位 机巧心种 (`ep-1553`) / 牺牲洁纯 (`ep-1197`) / 硫磺石 (`ep-223`)；
  四星 旋钻机-赤轴 (`ep-265`，ER 50%) / 加农转子 (`ep-221`)。
  专武定位法同前：遍历 `data/weapon-presets.json` 里 roleTag=强攻 的音擎，抓各自 `entry_page_v2`
  推荐代理人表比对（鳞齿寻踪专为她的耗能循环设计）。
- Teams: 席希耀 (希希芙 `ep-1861` / 「席德」 `ep-1499` / 耀嘉音 `ep-1109`)、
  希琉千 (希希芙 `ep-1861` / 琉音 `ep-1624` / 千夏 `ep-1791`)——双 C 队与席德互切合轴互给增益，
  单 C 队由琉音补失衡、千夏（月光骑士颂+摇摆爵士）补攻击加成与回能。席德套装为拂晓生花 +
  啄木鸟电音（其专武页同源确认）。
- 属性图标 电 (`electric`) 仓库已有，无需人工放置。
- 抓取脚本修复：`BASE_PANEL_ALIASES` 增加「生命力 → 生命值」。希希芙满级行写作「生命力」，
  不归一则初始值覆盖失败、面板多出第 11 项（柚叶踩过的第二种写法）；修复后重抓与
  `agent-presets` 逐字段一致。**满级行字段名每代理人可能不同，摘要行数与 preset 对不上就先查别名表。**

## Fifteenth instance: 南宫羽 (`strategy/nangong-yu/`)

以太属性击破 S 级（entry_page_id 1852，妄想天使），**重拍资源 + 三段蓄力精准蓄力** 的速切失衡手，兼异常副 C（颤音异放 / 极性紊乱）与全队失衡辅助：

- Base panel 60 级 0 突破: HP 8373 / ATK 671 / DEF 622 / Impact 120 / CR 5% / CD 50% /
  AC 90 / AM 93 / PR 0% / ER 1.2。核心满级 = 异常掌控 +36 + 基础攻击力 +75
  （`--core1 ac --core2 atk_base`）。
- 机制要点（写攻略前读 WIKI 文本）：核心被动把**初始掌控 >110 的部分按 1:1 转冲击力**；
  失衡期任意角色打异放/紊乱/进异常叠 1 层[颤音]（上限 4），叠满或脱离失衡时清除并追加一次
  [异放]（满级基础倍率以太 720%/火 900%/电 360%/冰 90%/物理 63%/风 36%，每层 +25%）；
  失衡时得 2 层[舞力全开]，蓄力/强特/快支重击命中「异常+失衡」敌人消耗 1 层触发[极性紊乱]
  （原紊乱 25%）并触发上一位角色快支；三段蓄力/终结技给敌人[踉跄]（失衡易伤 +30%、失衡 +3 秒）。
  [重拍]上限 100、进场 30、每秒 3.8、队友进异常 +12（6 秒 CD）；强特/连携/终结后可跳过一段
  直出二、三段且必定精准蓄力（失衡值 +20%）。影画 L1 降敌 18% 全抗 + 进场重拍回满、
  L2 每层颤音 +10% 异放倍率且失衡易伤 +30%、L3/L5 五技能 +2、L4 精通 +40 且蓄力异常积蓄 +35%、
  L6 失衡值 +50% 且新增[颤音·改]（非失衡期也能打异放）。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 > 连携技 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11。
- Drives（需求方指定的三套 4 件套共用同一 2 件套/主词条/副词条，`driveBuilds` 数组成案 +
  set4 数组带 scene）: 法厄同之歌 (`ep-1194`) / 静听嘉音 (`ep-1001`) / 自由蓝调 (`ep-191`)
  三选一；2 件套首选 自由蓝调（精通 +30）/ 法厄同之歌（掌控 +8%），备选 震星迪斯科 /
  山大王（击破向）；主词条 4 号异常精通+92（备选攻击 +30%）/ 5 号以太伤害+30%（备选攻击 +30%）/
  **6 号异常掌控+30%**（备选穿透率 +24%）；副词条优先级：**异常精通 > 攻击力% > 攻击力**；
  54 substats = 精通×30 + 攻击%×11 + 攻击×6 + 穿透值×6 + 生命%×1。三套的四件套效果均为局内，
  计算只建模各自 2 件套（法厄同4 局内精通+45/以太伤+25、嘉音4 快支叠层、蓝调4 降异常抗性）。
- Graduation panel (`--rows imp,am,ac,atk`, 计算器实算): 冲击力 120 / 异常精通 485 /
  异常掌控 211.7 / 攻击力 2,370.5。掌控 211.7 = (90+36)×(1+30% 专武+30% 六号位+8% 法厄同2)，
  核心被动掌控转冲击力（局内约 +102）不建模；异放不吃双爆，故展示行不含 cr/cd。
- 非满配（`--alt-sub-stats am:16,atk_pct:6,atk_flat:4,pen_val:3,hp_pct:1`，30 词条）：
  冲击力 120 / 异常精通 359 / 异常掌控 211.7 / 攻击力 2,113.6。
- Weapons: 首选 **霓虹妄想** (`ep-1908`，S 713 掌控 30%；特效常驻精通 90、叠满 2 层再 +60，
  全队增伤 15%×2)；下位 拘缚者 (`ep-219`) / 燃狱齿轮 (`ep-220`) / 人为刀俎 (`ep-157`)；
  四星 炎炙沸釜 (`ep-1922`) / 贵重骨核 (`ep-141`) / 左轮转子 (`ep-155`)。
  专武定位法同前：遍历 `data/weapon-presets.json` 里 roleTag=击破 的音擎，抓各自
  `entry_page_v2` 推荐代理人表比对。
- Teams: 爱南千 (爱芮 `ep-1793` 流光咏叹 / 南宫羽 `ep-1852` / 千夏 `ep-1791` 月光骑士颂)、
  星南柚 (星见 星见 雅 `ep-996` 折枝剑歌 / 南宫羽 `ep-1852` / 柚叶 `ep-1386` 月光骑士颂)——
  三小只凑满妄想天使组合技；星见雅吃她的极性紊乱（补落霜）与延长失衡。
- 属性图标 以太 (`ether`): WIKI 不下发且多次检索无公开原图，页面回退属性色块 `#C43C8F`，
  待人工来源补齐（佩洛伊斯 / 希希芙 / 爱芮三页同样待补）。

## Sixteenth instance: 爱芮 (`strategy/aria/`)

以太属性异常 S 级（entry_page_id 1793，妄想天使，2.6 限定），**吸收[应援能量]快速蓄力 + 第三段
[普通攻击：绝对音准]重击命中异常目标结算[异放]** 的爆发型异常主 C：

- Base panel 60 级 0 突破: HP 7749 / ATK 788 / DEF 619 / Impact 87 / CR 5% / CD 50% /
  AC 115 / AM 116 / PR 0% / ER 1.2。核心满级 = 异常掌控 +36 + 基础攻击力 +75
  （`--core1 ac --core2 atk_base`；成长表可见行只有这两项，被动文本另写的「精通 +45」不建模，
  同南宫羽口径）。
- 机制要点（写攻略前读 WIKI 文本）：吸收[应援能量]即时 +1 段蓄力并给积蓄值 +10%（最多 2 层）；
  附近能量 ≥2 个时长按/点按直接快速发动第三段蓄力；第三段重击命中处于属性异常目标触发[异放]
  （每 10 点初始掌控：以太 13.8% / 火 17.9% / 电 7.2% / 冰 1.8% / 物理 1.25% / 风 0.7%，
  失衡期再 +50%）。终结技进[妄想时刻]给 3 层[全场应援]（每层顶 2 段蓄力、进出场景时剩余层数
  转应援能量）、开[以太帷幕·妄想重奏]（全队攻击 +50）。额外能力：队内有击破/支援/同阵营/
  其他异常时，以太帷幕开启即在场上生成 4 个应援能量，且任意角色施加[侵蚀]持续时间 +3 秒。
- 加点链: 核心技 Lv.7 > 普通攻击 Lv.12 = 特殊技 Lv.12 = 连携技 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11
  （核心等级决定异放倍率，其余招式只影响以太直伤与失衡值）。
- Drives（需求方口径，与社区主推的「流光 4 + 法厄同 2」不同，以需求方为准）:
  法厄同之歌 4 件套 (`ep-1194`) + 2 件套首选 **流光咏叹** (`ep-1750`，以太伤害 +10%) /
  备选 自由蓝调 (`ep-191`，精通 +30)；主词条 4 号异常精通 +92（备选无）/
  **5 号以太伤害 +30%（备选穿透率 +24%）** / **6 号异常掌控 +30%（备选无，社区明确
  「不推荐掌控盘外的其他 6 号位」）**；副词条优先级：**异常精通 > 攻击力% > 攻击力**；
  54 substats = 精通×26 + 攻击%×16 + 攻击×12。法厄同 4 件套的「队友强特→精通 +45、
  非本人时以太伤 +25%」为局内，`--set4-effect none`。
- Graduation panel (`--rows am,ac,atk`，3 行，计算器实算): 异常精通 442 / 异常掌控 241.6 /
  攻击力 2,876.5。掌控 = (115+36)×(1+30% 专武+30% 六号位)=241.6，正好落在社区
  「无法厄同2 + 专武 = 241」一档（2 件套换成以太增伤/精通后不再有掌控 +8%）；攻击 =
  (788+75+713)×1.48 + 2 号位固定攻击 316 + 小攻击×12——**2 号位固定词条（生命+2200 /
  攻击+316 / 防御+184）计算器一直计入**，手算对不上时先查这里。
- 非满配（`--alt-sub-stats am:16,atk_pct:6,atk_flat:4,pen_val:3,hp_pct:1`，30 词条）：
  异常精通 352 / 异常掌控 241.6 / 攻击力 2,251.7。
- Weapons: 首选 **壳中之灵** (`ep-1883`，S 713 掌控 30%：唯一「局外掌控」词条异常音擎，
  特效精通 90/144 + 异常敌人增伤 20/32% + 异放紊乱 10/16%)；下位 飞鸟星梦 (`ep-1277`) /
  嵌合编译器 (`ep-214`)；备选 双生泣星 (`ep-212`)；四星 触电唇彩 (`ep-210`)。
  新代理人的专武未必在 `data/weapon-presets.json` 之外——壳中之灵早已随全量扫描入库，
  先用预设反查（roleTag=异常 + grade=S 且 substat 与该代理机制相关）再抓 WIKI 页确认数值。
- Teams: 爱南千 (爱芮 / 南宫羽 `ep-1852` 法厄同之歌 / 千夏 `ep-1791` 月光骑士颂——千夏可
  反复重开以太帷幕、每次触发爱芮额外能力回 4 层应援能量)、爱维蕾 (爱芮 / 维琳娜 `ep-1960`
  呼啸沙龙 `ep-2038` / 蕾米埃尔 `ep-2076` 谶羽之誓 `ep-2116`——三异常队，额外能力条件常驻，
  爱芮把蕾米埃尔[侵蚀]拉长 3 秒）。
- 属性图标 以太 (`ether`) 仍缺，回退属性色块 `#C43C8F`。
- 跨页一致性：本页口径（法厄同之歌 4 件套）与 `nan-gong-yu` 页「爱南千」队中爱芮原先列的
  流光咏叹冲突，已把该页成员套装同步改为法厄同之歌。**新页面若改动了某代理人的配装结论，
  回头同步引用过它的旧页面。**

## Seventeenth instance: 千夏 (`strategy/sunna/`)

物理属性支援 S 级（entry_page_id 1791，妄想天使，2.6 限定），**多开关[以太帷幕·妄想重奏] +
[天使协律]全队加攻（3500 阈值）+ [猫的凝视]额外伤害** 的速切辅助；第十七实例，也是第一个
**展示行只有攻击力（单行）** 的页面：

- Base panel 60 级 0 突破: HP 8477 / ATK 675 / DEF 600 / Impact 98 / CR 5% / CD 50% /
  AC 96 / AM 95 / PR 0% / ER 1。核心满级 = **攻击力 +21%**（A/C/E 三档各 7%，选项
  `atk_pct_21`）+ 基础攻击力 +75（B/D/F）——支援角色核心给攻击% 的又一构型（柚叶给掌控、
  她给攻击%），别默认 `--core1 cr`。
- 机制要点（写攻略前读 WIKI 文本）：强化特殊技[泡泡糖轰炸]给全队 40 秒[天使协律]，
  加攻数值 = 她 30% 的初始攻击力、上限 1050（对应**初始攻击 3500 满额**）；紧接的
  [特别拍照技巧]开[以太帷幕·妄想重奏]（全队攻击再 +50 点、先关旧的再开新的）。后台
  泡泡消耗[磨爪器]给敌人挂[猫的凝视]，队内强攻持续攻击触发并清除（300% 攻击力属性伤害）、
  异常角色触发为 480% 且必定暴击、暴击伤害 +150%；失衡下触发所需攻击次数大幅减少。
  磨爪器来源：任意以太帷幕 +2、任意属性异常 +1（10 秒 1 次）、终结技 +6（上限 6）。
  额外能力[白日梦对位法]需队内有强攻或同阵营：帷幕内角色命中给敌人失衡易伤 +30%（40 秒）。
  影画 L1 凝视降防 7%×3 + 进场 15 能量、L2 帷幕内全队攻击 +10% 且强攻/异常触发凝视
  +200%/+300%、L4 终结技全队增伤 18%、L6 强特进[潜心创作中！]自身必暴且暴伤随攻击
  （上限 105%）、全队触发凝视伤害 +50%。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 连携技 Lv.12 > 普通攻击 Lv.12 = 支援技 Lv.12 >
  闪避 Lv.7（需求方口径：闪避点到 7 即止，她是纯辅助、几乎不前场站场）。
- Drives（`driveBuilds`，set4 带 `alt4` 备选 + set2 无 alt）:
  4 件套 **月光骑士颂** (`ep-1551`)（2 件回能+20%、4 件支援强特/终结全队增伤 18% 25 秒，
  最契合她「强特启动」节奏），备选 4 件套 **静听嘉音** (`ep-1001`)（走 set4.alt4 字段）；
  2 件套 **摇摆爵士** (`ep-231`，回能 +20%，不设备选)；主词条 4 号攻击力+30%（备选无）/
  5 号攻击力+30%（备选无）/ **6 号能量自动回复+60%**（备选无）；
  副词条优先级：**攻击力% > 攻击力（固定值）**——她只有攻击力这一个结算指标，
  双爆/穿透/精通全无用。54 substats = 攻击力% ×13 + 防御力% ×12 + 暴击率 ×6 + 暴击伤害 ×5 +
  异常精通 ×5 + 生命值% ×5 + 穿透值 ×4 + 小防御 ×4（有效词条链只有 2 项：2 号位固定攻击排
  攻击力、4/5 号位攻击% 排攻击%，攻击% 只能落在 1/2/3/6 号盘；13 条攻击% 即压 3500 线，
  达标后余量词条无收益，全给填充）。
- Graduation panel (`--rows atk`，单行，计算器实算): 攻击力 **3,534.6**。攻击 =
  (675 + 75 核心 + 713 音擎) × (1 + 21% 核心 + 30% 四号位 + 30% 五号位 + 13×3% 副词条)
  + 2 号位固定攻击 316 = 1463 × 2.20 + 316。**3500 是她的核心阈值**：[天使协律]加攻 =
  30% 自身攻击、上限 1050（= 3500 × 30%），达标后继续堆攻击不再提升全队加攻——所以
  满配不是「攻击堆到最高」而是「压线 3500 的最小词条解」。
- 非满配（同配置、`--alt-sub-stats atk_pct:8`）：攻击力 **3,315.1**（未达 3500，
  全队加攻约 995 点），低词条参考。
- Weapons: 首选 **思络成歌** (`ep-1826`，S 713 回能 60%：后场每 0.96/秒回能、强特物理
  伤害全队增伤 +20% 叠 2 层、2 层时全队攻击 +16%——强化特殊技两段都能叠层)；下位
  好斗的阿炮 (`ep-486`，A 624 回能 50%，友方单位命中叠全队攻击 +4%/层、**千夏的泡泡算
  友方单位**)；备选 啜泣摇篮 (`ep-218`)；四星 聚宝箱 (`ep-217`，特效需以太伤害、物理角色
  吃不到) / 逍遥游球 (`ep-213`，需属性克制触发)。
  专武定位法修正：**WIKI 音擎页的 `double_col_table`「推荐代理人」表比
  `data/weapon-presets.json` 反查更直接**——思络成歌页同时推荐千夏与浮波柚叶（柚叶页当年
  把它列为「下位」，实际是千夏专武，两页都引它但定位不同）。抓音擎页必须带
  `x-rpc-wiki_app: zzz` 头，否则 entry_page_id 会串到其他游戏的条目（1463 会返回原神仙像）。
- Teams: 叶琉夏 (叶瞬光 `ep-1687` 沧浪行歌 / 琉音 `ep-1624` 山大王 / 千夏 `ep-1791`
  月光骑士颂——小光最强队，千夏反复开关帷幕为她回剑势)、叶照夏 (叶瞬光 / 照 `ep-1686`
  雪兔梦游仙境+静听嘉音 / 千夏——循环最舒适)、妄想天使 (千夏 / 爱芮 `ep-1793` 法厄同之歌 /
  南宫羽 `ep-1852` 法厄同之歌——同阵营触发额外能力、凑满组合技，南宫羽开失衡窗口供
  凝视与异放)。
- 跨页一致性：叶瞬光 / 爱芮 / 南宫羽 / 希希芙四页的千夏成员套装均为月光骑士颂，与本页一致。

## Eighteenth instance: 照 (`strategy/zhao/`)

冰属性防护 S 级（entry_page_id 1686，坎卜斯黑枝），**[霜寒值]速切 + [以太帷幕·涌泉]** 的泛用
辅助；第十八实例，也是第一个**展示行只有生命值（单行）**与**核心加成给生命%**的页面：

- Base panel 60 级 0 突破: HP 9117 / ATK 690 / DEF 701 / Impact 93 / CR 5% / CD 50% /
  AC 93 / AM 96 / PR 0% / ER 1.2。核心满级 = **生命值百分比 +18%**（A/C/E 三档各 6%，
  选项 `hp_pct`）+ 基础攻击力 +75（B/D/F）——支援/防护角色核心给生命% 的第一例，
  别默认 `--core1 cr`。
- 机制要点（写攻略前读 WIKI 文本）：进场即得 100 点[霜寒值]（上限 100），前台角色命中每
  3 秒 +6；满值切照入场发动[登场技]消耗全部霜寒值开[以太帷幕·涌泉]——全队最大生命 +5%
  （40 秒）、攻击力提升（初始数据 100 点，社区按满级记 1000）、生命% +18%、基础攻击 +75
  （50 秒）。**额外能力[凝聚力]是她的养成核心**：队内有强攻/异常/支援时，帷幕内全队增伤
  10% 起步，初始最大生命超 15000 后每超 400 点 +1%、**27000 生命吃满 40%**（音擎与技能
  Buff 里的生命是局内、不参与转模）。核心被动另按初始最大生命转暴击率：每 1000 点
  0.8%→1.4%（成长表 A-F 递增，27000 生命约 +37.8%）。强特/终结 +20 霜寒并给全队回血
  （每秒 1.06% 最大生命、5 秒）。影画 L1 切后场全队无视 15% 属性抗性、L2 生命回复时
  自身 +20% 攻/队友 +15% 攻、L4 开帷幕得 250 喧响值、L6 暴击转化提至 125%。
- 加点链: 核心技 Lv.7 > 支援技 Lv.12 > 特殊技 Lv.12 = 连携技 Lv.12 = 普通攻击 Lv.12 >
  闪避 Lv.7（需求方「省材料」口径）。
- Drives（`driveBuilds`，set4 带 `alt4` 双 4 件套 + set2 带 alt）:
  4 件套 **静听嘉音** (`ep-1001`)（快支入场叠层 8%×3——**只有照通过[快速支援]窗口入场
  发动登场技才判定生效**），备选 4 件套 **雪兔梦游仙境** (`ep-1907`，2 件同为生命+10%、
  4 件防护强特或队友招架叠 6%×3)；2 件套 **云岿如我** (`ep-1347`，生命 +10%，堆 27000 的
  关键)，备选 摇摆爵士 (`ep-231`，回能 +20%)；主词条 4 号生命值+30%（备选无）/
  5 号生命值+30%（备选无）/ **6 号能量自动回复+60%（备选生命值+30%）**；
  副词条优先级：**生命值% > 生命值（固定值）> 暴击伤害 > 暴击率 > 其他**；
  54 substats = 生命% ×18 + 小生命 ×1 + 暴击伤害 ×14 + 暴击率 ×13 + 穿透值 ×2 + 精通 ×4 +
  防御% ×2（有效词条链前两位是生命% 与小生命：1 号位固定生命排小生命、4/5 号位生命%
  主词条排生命%，故生命% 只能落在 1/2/3/6 号盘；**方案C 用 6 号回能盘，18 条生命% 才压
  27000 线**；词条不足时 6 号换生命盘只需 8 条——与社区三档口径精确吻合）。
- Graduation panel (`--rows hp`，单行，计算器实算): 生命值 **27,110.2**。
  公式：9117 × (1 + 18% 核心 + 30% 专武 + 60% 四/五号位 + 10% 云岿2 + 18×3% 副词条)
  + 盘 1 固定生命 2200 + 小生命×1 = 9117 × 2.72 + 2312。**注意计算器的生命公式含
  盘 1 固定 2200**：社区的 27000 三档门槛（专武 8 大生命+1 小生命、6 号回能 18 大生命、
  正版变身器 10 大生命）都对应 (9117+?)… 精确说对应 172% 生命线，全部与本仓计算器吻合。
- 非满配（同音擎/套装、6 号位换生命盘、`--alt-sub-stats hp_pct:6,hp_flat:1,…`）：
  生命值 **26,563.2**（差 437 点未吃满 40%）。养成路径：词条不足先用生命盘压阈值，
  词条富裕再换 6 号回能盘。
- Weapons: 首选 **半糖雪兔** (`ep-1753`，S 713 生命 30%：唯一生命词条防护音擎，后场
  0.74/秒回能、全队攻/生命 +16%、开帷幕全队暴伤 +48%)；下位 正版变身器 (`ep-139`，
  A 594 生命+25%，特效生命上限 +12.5% 也进局外面板)；备选 奔袭獠牙 (`ep-799`)；
  四星无推荐。专武靠 `double_col_table` 推荐代理人表确认（该表仅列照）。
- Teams: 叶千照 (叶瞬光 `ep-1687` 沧浪行歌 / 千夏 `ep-1791` 月光骑士颂 / 照 `ep-1686`
  静听嘉音)——双辅助的强攻/支援身份都触发照的额外能力，照与千夏轮流开关以太帷幕为
  叶瞬光回[青溟剑势]；队伍配置由需求方指定（叶瞬光队内的双辅助变体）。
- 跨页一致性：叶瞬光页（叶照千/叶琉千）与千夏页（叶照夏）中照的成员套装均为
  雪兔梦游仙境 + 静听嘉音，与本页 4 件套「嘉音首选、雪兔备选」的双选口径一致。

## Nineteenth instance: 琉音 (`strategy/dialyn/`)

物理属性击破 S 级（entry_page_id 1624，坎卜斯黑枝），**[好评]资源 + 猜拳三联动**的速切击破；
第十九实例，也是第三个「初始暴击率阈值」型面板（诺姆的 CR→爆伤/失衡值、莱特的压线 50 之后
她的 CR→冲击力），展示了暴击词条 2.4%/条的精确堆叠：

- Base panel 60 级 0 突破: HP 8250 / ATK 683 / DEF 612 / Impact 110 / CR 5% / CD 50% /
  AC 94 / AM 93 / PR 0% / ER 1.2。核心满级 = 暴击率 +14.4% + 基础攻击力 +75
  （`--core1 cr --core2 atk_base`）。
- 机制要点（写攻略前读 WIKI 文本）：进场 60 点[好评]（上限 120），接战每秒 +0.6、猜拳三连
  重击命中各 +7.5（同招式一次）；**核心被动满级把初始暴击率超 50% 的部分每 1% 转 2.0 冲击力
  （成长表 1.4→2.0 六档递增）、上限 100——满暴时局内 +100 冲击**。猜拳链：石头 → 剪刀 →
  布!（各 8 秒窗口），[布！]命中给敌人[恶意投诉]（失衡时间 +2 秒、失衡易伤 +15%，同类
  不可叠加）。好评 ≥90 时用连携/送客/快支开窗，**下一位角色的连携强制升级为终结技**
  （耗 60 好评）。额外能力[场外连线]需强攻/命破队友：强特/终结给全队[好评如潮]（增伤 40%、
  15 秒、可延长 10 秒），猜拳重击按上一名队友特性追加伤害（强攻 320% 其攻击力、命破 400%
  其贯穿力）。影画 L1 好评积累 +16% 且[好评如潮]下全队无视 15% 全抗、L2 失衡易伤额外 +20%、
  L4 进场 +20 能量、L6 队友经核心被动终结技入场获[余音]（她追加 480% 攻击力物理伤、1 秒 1 次
  最多 12 次）。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 > 支援技 Lv.12 > 连携技 Lv.12 = 普通攻击 Lv.12 > 闪避 Lv.11
  （暴击转化比例与失衡易伤都挂核心等级；特殊技/支援是失衡值主要来源）。
- Drives（需求方口径：4 件套山大王 + 2 件套首选回能备选暴率）:
  4 件套 **山大王** (`ep-1346`)（2 件「失衡值+6%」选项表无对应项，`--set4-effect none`；
  4 件全队暴伤 15%、暴击≥50% 再 15%——她高频强特/连携稳定触发）；2 件套首选
  **摇摆爵士 / 月光骑士颂**（同效 ER+20%，`set2.main` 数组合并一行），备选
  **啄木鸟电音** (`ep-232`，暴击+8%)；主词条 4 号暴击率+24%（备选无）/
  5 号物理伤害+30%（备选穿透率+24% / 攻击力+30%）/ **6 号能量自动回复+60%（备选无）**；
  副词条优先级：**暴击率 > 攻击力% = 暴击伤害**；
  54 substats = 暴击率×14 + 攻击力%×14 + 暴击伤害×13 + 小攻击×6 + 穿透值×4 + 精通×2 +
  防御%×1（暴击率只能落在 1/2/3/5/6 号盘——4 号位暴击主词条排暴击；14 条暴击 =
  6+5+3 分布，其余盘位初始 4 条给攻击%/暴伤/小攻击）。
- Graduation panel (`--rows cr,imp,cd,atk`，计算器实算): 暴击率 **101%** / 冲击力 **110** /
  暴击伤害 **112.4%** / 攻击力 **2,518.8**。暴击率 = 5 + 14.4(核心) + 24(专武) + 24(四号位)
  + 14×2.4(副词条) = 101%（**暴击副词条 2.4%/条**，不是 3%，手算先查 options.json）；
  需求方把方案A 的 6 号位与 2 件套都改成回能（保石头剪刀布能量），因此面板冲击只有
  基础 110——核心转化那 +100 冲击是局内、不进面板。
- 非满配（同配置、`--alt-sub-stats cr:10,atk_pct:7,cd:7,atk_flat:3,pen_val:2,am:1`，
  需求方口径「暴率降到 90」）：暴击率 **91.4%** / 冲击力 110 / 暴击伤害 **83.6%** /
  攻击力 **2,152.9**。
- Weapons: 首选 **昨夜来电** (`ep-1689`，S 713 暴击 24%：后场 1.5/秒回能、强特物理伤后
  失衡值+9%×3 层、3 层全队暴伤+30%)；下位 燃狱齿轮 (`ep-220`，后场 0.6/秒回能、强特叠
  局内冲击)；备选 人为刀俎 (`ep-157`，A 回能 50%、耗能叠冲击 8 层)；四星 贵重骨核
  (`ep-141`，纯冲击无回能)。专武定位靠 `double_col_table` 推荐表（该表仅列琉音；
  **昨夜来电被诺姆页列为备选，实为琉音专武——跨页引用时以推荐表为准**）。
- Teams: 仪玄琉音卢西娅 (仪玄 `ep-1299` 云岿如我+折枝剑歌 / 琉音 山大王+摇摆爵士 /
  卢西娅 `ep-1533` 月光骑士颂+云岿如我——社区旗舰「仪玄三大」流程)、
  叶琉千 (叶瞬光 `ep-1687` 沧浪行歌 / 琉音 / 千夏 `ep-1791` 月光骑士颂)。
- 跨页一致性：般岳/星徽比利/叶瞬光/千夏/照五页中琉音的成员套装均为山大王，与本页一致。

## Twentieth instance: 伊德海莉·墨菲 (`strategy/yidhari/`)

冰属性命破 S 级（entry_page_id 1538，怪啖屋），**蓄力烧血 + 半血增伤**的长轴站场主 C；
第二十实例，也是**命破 rupture 模式的第二例**（般岳/星徽比利之后），把「生命→贯穿力」
堆到 2600+ 档：

- Base panel 60 级 0 突破: HP 8497 / ATK 784 / DEF 448 / Impact 95 / CR 5% / CD 50% /
  AC 87 / AM 90，另贯穿力 105 / 闪能自动累积 2（命破无 pr/er 行）。核心满级 = 暴击率
  +14.4% + 基础攻击力 +75（`--core1 cr --core2 atk_base`，与般岳同构）。
- 机制要点（写攻略前读 WIKI 文本）：核心被动**每 1 点最大生命值提高 0.1 点贯穿力**，
  全部冰招为贯穿伤害（无视防御、以贯穿力为倍率）；长按普攻三段蓄力持续烧血（最多烧到
  最大生命的 25%），**生命低于 50% 时攻击伤害最多 +50%**（回到 50% 后持续 5 秒）、
  每降 1% 生命回 10 点喧响值；进场 60 闪能。拼刀：蓄力受击触发[霜凝千钧]格挡（减伤 25%）
  并借势 +1 段蓄力，接特殊技必定触发[溯寒]（蓄力拉满）、命中失衡且闪能够则[追碾]，
  之后[强化特殊技：极寒重碾]回已损失生命的 33%（溯寒后再回 15 闪能）。喧响值满可开
  [以太帷幕·涌泉]（全队最大生命+5%、蓄力与烧血提速）并在 30 秒内打一次[终结技]。
  额外能力[完形叙事]需队内击破/支援：半血以下暴伤 +30%、受伤 -25%，帷幕内三蓄/极寒重碾
  结束召唤寒冰触手（每 12 秒 1 次、视为强特，可续云岿层数）。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 > 支援技 Lv.12 > 连携技 Lv.12 = 普通攻击 Lv.12 > 闪避 Lv.11
  （社区按伤害占比：强特 39.3% / 终结 36.7% / 普攻 24%，都点满）。
- Drives（需求方口径：云岿如我4 + 折枝剑歌2）:
  4 件套 **云岿如我** (`ep-1347`)（2 件生命+10% 计入贯穿力，`--set4-effect hp_pct_10`；
  4 件暴击 4%×3 层 + 3 层贯穿增伤 10% 为局内不建模）；2 件套 **折枝剑歌** (`ep-1000`，
  暴伤+16%)，备选 啄木鸟电音 (`ep-232`，暴击+8%，非专武时缓解暴击压力)；主词条 4 号
  暴击率+24%（备选暴击伤害+48%）/ 5 号冰属性伤害+30%（备选生命值+30%）/ **6 号生命值
  +30%（备选无——能量回复不加闪能，她的闪能靠拼刀/溯寒强特/三蓄第三段回复）**；
  副词条优先级：**暴击率 > 暴击伤害 > 生命值% > 其他**；
  54 substats = 暴击率×10 + 暴击伤害×16 + 生命%×12 + 攻击%×7 + 穿透值×3 + 防御%×4 +
  精通×2（逐盘推导过初始 4 词条：4 号暴击排暴击、6 号生命% 排生命%、1/2/3 号固定主分别排
  小生命/小攻击/小防御；暴击只能落在 1/2/3/5/6 号盘）。
- Graduation panel (`--rows hp,penforce,cr,cd --mode rupture`，计算器实算):
  生命值 **19,703.8** / 贯穿力 **2,635.8** / 暴击率 **67.4%** / 暴击伤害 **142.8%**。
  贯穿力 = 105 + 0.3×攻击 + 0.1×生命（命中她的核心 10:1 转化）；暴击 = 5 + 14.4 + 24 +
  10×2.4 = 67.4%（局内再叠专武半血 +20% 与云岿4 的 12% 即满暴——**专武局内暴击要算进
  溢出评估**，多出的暴击词条换暴伤）；生命 = 8497×(1+30% 专武+10% 云岿2+30% 六号位+
  12×3%) + 盘 1 固定 2200 = 19,703.8。**与社区「极致」三线（暴击 67.4% / 暴伤 142.8% /
  生命 19194+）逐位吻合**。
- 非满配（同配置、`--alt-sub-stats cr:6,cd:10,hp_pct:8,atk_pct:4,pen_val:2`，30 词条）：
  生命值 **18,684.2** / 贯穿力 **2,491.4** / 暴击率 **57.8%** / 暴击伤害 **114%**。
- Weapons: 首选 **海妖摇篮** (`ep-1664`，S 713 生命 30%：减血叠冰贯穿伤 +6%/层×3、
  半血以下暴击 +20%~32%)；下位 青溟笼舍 (`ep-1342`，S **743** 生命 30%——仪玄专武，
  特效以太向对她无效但白值经 0.3 换算反哺贯穿力，约专武 86%~90%)；备选 电波漫步
  (`ep-1340`，连携/终结叠贯穿力 128 点/层) / 燔火胧夜 (`ep-1612`，减血加暴击)；
  四星 幻变魔方 (`ep-1343`)。专武定位靠 `double_col_table` 推荐表（该表仅列伊德海莉）。
- Teams: 莱卢伊 (莱卡恩 `ep-65` 山大王 / 卢西娅 `ep-1533` 月光骑士颂+云岿如我 / 伊德海莉——
  社区最推，狼叔减冰抗+失衡易伤、卢西娅给约 1300 点贯穿力)、福卢伊 (橘福福 `ep-1301`
  山大王 / 卢西娅 / 伊德海莉)、福壶伊 (橘福福 / 潘引壶 `ep-1300` 静听嘉音 / 伊德海莉——
  **潘引壶快支是上切，伊德海莉必须置于他之前**)。

## Twenty-first instance: 卢西娅·艾洛温 (`strategy/lucia/`)

以太属性支援 S 级（entry_page_id 1533，怪啖屋），**命破体系专辅**；第二十一实例，也是
第三个**展示行只有生命值（单行）+ 24000 局外阈值**的页面（照的 27000 之后）：

- Base panel 60 级 0 突破: HP 8477 / ATK 683 / DEF 594 / Impact 83 / CR 5% / CD 50% /
  AC 96 / AM 95 / PR 0% / ER 1.2。核心满级 = **基础能量自动回复 +0.36**（A/C/E 三档各
  0.12，选项 `er_base`，与希希芙同构）+ 基础攻击力 +75（B/D/F）。
- 机制要点（写攻略前读 WIKI 文本）：强特[死神协奏曲·破晓]给全队[破暗]——贯穿力 +12、
  **每 200 点初始最大生命额外 +7.4、上限 900（强特 Lv12 成长表 5.2→7.4、636→900），
  初始生命 24000 吃满**。梦境值：进场 60、[随想] +20~40 / [合唱] +40~60 / 终结 +100，
  满 100 进[梦境]——触发快支 + 开[以太帷幕·涌泉]（全队最大生命 +5%、40 秒可延至 300 秒）；
  梦境中[随想]耗 25 梦境值升级[合唱]、队友命中也耗 25 点发动[追加攻击]（8 秒内置），
  每次升级/追加刷新全队[巡梦童谣]（增伤 10%、12 秒）。强特/终结在梦境+帷幕中可再延长
  帷幕 16/32 秒。终技[进击，大铠甲！]骑乘免死并留下[星光汇聚之地]（每秒回复她 1.05%
  最大生命）。额外能力[长夜诗篇]需队内命破/击破：[破暗]附加暴伤 +30%。
- 加点链: 特殊技 Lv.12 > 核心技 Lv.7 > 连携技 Lv.12 > 支援技 Lv.12 = 普通攻击 Lv.12 >
  闪避 Lv.11（**强特等级直接决定[破暗]上限**，与「核心优先」的常规链不同——需求方口径）。
- Drives（需求方口径：月光骑士颂4 + 云岿如我2）:
  4 件套 **月光骑士颂** (`ep-1551`)（2 件回能+20% 计入 `--set4-effect er_pct_20`、4 件
  支援强特/终结全队增伤 18% 25 秒）；2 件套 **云岿如我** (`ep-1347`，生命+10%，
  `--set2-effect hp_pct_10`)，备选 摇摆爵士 (`ep-231`)；主词条 4/5/6 号位**全生命值
  +30%（备选均无）**；副词条优先级：**生命值% > 生命值（固定值）> 暴击率 > 暴击伤害 > 其他**；
  54 substats = 生命% ×10 + 小生命 ×1 + 暴击率 ×12 + 暴击伤害 ×8 + 精通 ×16 + 穿透值 ×7
  （**生命% 只能落在 1/2/3 号盘**——4/5/6 号位生命主词条排生命%，上限 18 条；
  10 条即压 24000 线，其余 44 条对该阈值无收益，全给填充）。
- Graduation panel (`--rows hp`，单行，计算器实算): 生命值 **24,352.2**。
  公式：8477 × (1 + 30% 专武 + 90% 三号位 + 10% 云岿2 + 10×3% 副词条) + 盘 1 固定 2200
  + 小生命×1 = 8477 × 2.60 + 2312。**24000 是唯一边界**：[破暗] = 12 + 每 200 初始生命
  ×7.4（强特 Lv12）、上限 900。与社区三档精确吻合：专武 10 条大生命+1 小生命、
  二件套换摇摆 2 需 13 条、无专武（啜泣摇篮）需 20 条。
- 非满配（同配置、`--alt-sub-stats hp_pct:8,hp_flat:1,cr:8,cd:6,am:6,pen_val:1`）：
  生命值 **23,843.6**（差 157 点，[破暗]约 894 未吃满）。
- Weapons: 首选 **铸梦炉歌** (`ep-1611`，S 713 生命 30%：后场 0.64/秒回能、开/延帷幕
  全队增伤 +40% 与生命上限 +24%——唯一生命词条支援音擎)；下位 啜泣摇篮 (`ep-218`)；
  备选 好斗的阿炮 (`ep-486`)；四星 聚宝箱 (`ep-217`，**以太伤害可触发**，但追加攻击不触发、
  覆盖率有限) / 逍遥游球 (`ep-213`，需属性克制)。专武靠 `double_col_table` 推荐表确认
  （该表仅列卢西娅）。
- Teams: 仪橘卢 (仪玄 `ep-1299` 云岿如我+折枝剑歌 / 卢西娅 月光骑士颂+云岿如我 /
  橘福福 `ep-1301` 山大王，站位橘福福→卢西娅→仪玄)、伊橘卢 (伊德海莉·墨菲 `ep-1538` /
  卢西娅 / 橘福福——双帷幕叠加)、真橘卢 (真斗 `ep-1536` 云岿如我 / 卢西娅 / 橘福福)。
- 跨页一致性：般岳/莱特/星徽比利/琉音/伊德海莉页中卢西娅的成员套装均为月光骑士颂，
  与本页一致；仪玄与伊德海莉的成员套装与本页互引的云岿如我+折枝剑歌一致。
- **局内/局外生命的口径备忘**：她的阈值算「局外面板」，而音擎与技能的「生命上限提升」
  （专武 +24%、帷幕 +5%）是局内、以队友局外面板为基底——文字攻略已明确区别，
  后来者遇到同类「按初始生命转模」机制都照此办理（照的 27000 同理）。

## Twenty-second instance: 奥菲丝&「鬼火」 (`strategy/orphie-magus/`)

火属性强攻 S 级（entry_page_id 1501，奥波勒斯小队），**[蓄炎]资源 + 后台追击杀** 的追击副 C；
第二十二实例，也是第一个**核心加成给基础能量回复（er_base）的强攻**页面
（与希希芙/卢西娅同构）：

- Base panel 60 级 0 突破: HP 7788 / ATK 854 / DEF 612 / Impact 93 / CR 5% / CD 50% /
  AC 92 / AM 90 / PR 0% / ER 1.2。核心满级 = **基础能量自动回复 +0.36**（A/C/E 三档各
  0.12，选项 `er_base`）+ 基础攻击力 +75（B/D/F）。核心被动文本的暴击 +12.5%→25%
  与追加攻击伤害 +42.5%→85% 为局内、不进面板（同南宫羽/爱芮口径）。
- 机制要点（写攻略前读 WIKI 文本）：[蓄炎]进场 100（上限 125），前台[小心脚下]（30 能量）、
  后场[灼红旋涡]（能量≥60 自动，耗 30 能量）、[蚀光一击]（能量不足时）、连携/终结各 +20；
  ≥100 长按[蓄热充能]喷激光并自动接[燥焰迸射]，命中即给全队[准星聚焦]——**攻击 +280
  （成长表 130→700 上限的 7 档递增）、初始 ER ≥1.6 每超 0.1 再 +20、上限 700（ER 3.7 吃满）**。
  火刀/[小心脚下]/[灼红旋涡]/[蓄热充能]/[燥焰迸射]/连携/终结**全部视为追加攻击伤害**。
  持有[准星聚焦]的角色发动追加攻击可延长该状态 4 秒（最多 +20 秒）。额外能力[熔炉所铸]
  需队内击破/支援：[准星聚焦]持有者追加攻击无视 25% 防御。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 > 连携技 Lv.12 = 支援技 Lv.12 > 普通攻击 Lv.12 > 闪避 Lv.11
  （核心等级同时决定暴击/追伤/转模加攻三档）。
- Drives（需求方口径：如影相随4 + 月光骑士颂2）:
  4 件套 **如影相随** (`ep-1193`)（2 件「追加攻击和冲刺攻击伤害+15%」选项表无对应项，
  `--set4-effect none`；4 件追加/冲刺命中同属性叠攻击 4%+暴击 4%，3 层为局内）；
  2 件套 **月光骑士颂** (`ep-1551`，`--set2-effect er_pct_20`)，备选 摇摆爵士 (`ep-231`)；
  主词条 4 号暴击伤害+48%（备选暴击率+24%）/ 5 号火属性伤害+30%（备选攻击力+30% /
  穿透率+24%）/ **6 号能量自动回复+60%（备选无——ER 是她的功能性命脉）**；
  副词条优先级：**暴击率 > 暴击伤害 > 攻击力% > 穿透值**；
  54 substats = 暴击率×12 + 暴击伤害×16 + 攻击力%×10 + 小攻击×6 + 穿透值×4 + 精通×3 +
  生命%×3（4 号暴伤主词条排暴击伤害，该盘初始 4 条只放暴击/攻击%/小攻击/穿透/精通）。
- Graduation panel (`--rows atk,cr,cd,dmg`，计算器实算): 攻击力 **2,564.6** / 暴击率 **33.8%** /
  暴击伤害 **174.8%** / 增伤 **30%**。攻击 = (854 + 75 核心 + 713 音擎) × (1 + 10×3% 副词条)
  + 2 号位固定 316 + 6×19。**面板暴击 33.8% 看着低但是对的**：局内叠核心 25% + 如影4 的
  12% + 专武 20% ≈ 85% 局内暴击——数值型专武与套装自带大量局内暴击时，面板暴击只需中等、
  余量全给暴伤（与希格莉德的 33.8% 形成镜像：一个靠状态增益压面板，一个靠状态增益堆局内）。
- 非满配（同配置、`--alt-sub-stats cr:8,cd:10,atk_pct:6,atk_flat:4,pen_val:2`）：
  攻击力 **2,329.6** / 暴击率 **24.2%** / 暴击伤害 **146%** / 增伤 **30%**。
- Weapons: 首选 **嚣枪喧焰** (`ep-1586`，S 713 ER 60%：追加攻击火伤无视 15%~24% 防御
  ×2 层 + 暴击率 +20%~32%)；下位 牺牲洁纯 (`ep-1197`) / 心弦夜响 (`ep-1159`)；
  备选 强音热望 (`ep-995`)；四星 加农转子 (`ep-221`) / 鎏金花信 (`ep-744`) /
  旋钻机-赤轴 (`ep-265`)。专武靠 `double_col_table` 推荐表确认（同表列伊芙琳/「11号」，
  按角色名认领）。
- Teams: 安扳奥 (零号·安比 `ep-1190` 如影相随 / 「扳机」`ep-1230` 震星迪斯科+啄木鸟电音 /
  奥菲丝——追击队旗舰，扳机→奥菲丝→安比站位)、席奥耀 (「席德」 `ep-1499` 拂晓生花+啄木鸟电音 /
  奥菲丝 / 耀嘉音 `ep-1109` 静听嘉音)、伊奥耀 (伊芙琳 `ep-1158` 河豚电音 / 奥菲丝 / 耀嘉音)。
- **能量回复的呈现备忘**：`TOTAL_LABELS` 无 er 行，6 号回能盘的数值写进文字攻略与面板说明
  （本例：局外 ER 3.74 = (1.2+0.36 核心) × (1+60% 专武+60% 六号位+20% 二件套)，
  恰好压过 3.7 转模线——卢西娅页同款算法）。

## Twenty-third instance: 「席德」 (`strategy/seed/`)

电属性强攻 S 级（entry_page_id 1499，奥波勒斯小队），**双强攻体系核心**；第二十三实例，
是核心加成给**暴击伤害（cd +28.8）**的第一例，也是「专武局内暴击凑满爆」的典范：

- Base panel 60 级 0 突破: HP 7673 / ATK 854 / DEF 612 / Impact 93 / CR 5% / CD 50% /
  AC 94 / AM 93 / PR 0% / ER 1.2。核心满级 = **暴击伤害 +28.8%**（A/C/E 三档各 9.6%，
  选项 `cd`）+ 基础攻击力 +75（B/D/F）——核心只给暴伤不给暴击，暴击率是稀缺项。
- 机制要点（写攻略前读 WIKI 文本）：初始攻击最高的强攻队友为[正兵]（按局外攻击判定、
  进场固定）；[正兵]放强特 → 她得[强袭]（1000 攻+30% 暴伤），她放强特 → 正兵得[明攻]
  （同数值），两者并存时双方[围杀]（伤害 +25%）；Buff 下场后仍生效 3 秒、持续 40 秒。
  钢能：初始 60、上限 150，≥120 可打[落华·崩坠一式]并自动接二式（各耗 60）、终结 +60；
  操作中的她或正兵每耗 1 能量 → 她回 0.5 钢能；她造成伤害时每秒为正兵回 2 能量（需操作中）。
  强特[铁萼雨幕]飞行弹幕、一次飞行耗 60 能量自动接重戮。额外能力要求队内有另一名强攻。
- 加点链: 核心技 Lv.7 > 普通攻击 Lv.12 > 连携技 Lv.12 = 特殊技 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11
  （伤害占比：普攻 60.5% / 终结+连携 27.0% / 强特 7.6%——重戮与崩坠全在普攻里）。
- Drives（需求方口径：拂晓生花4 + 啄木鸟电音2）:
  4 件套 **拂晓生花** (`ep-1552`)（2 件「普攻伤害+15%」选项表无对应项，`--set4-effect none`；
  4 件普攻+20%、强攻强特/终结后再+20% 普攻为局内）；2 件套 **啄木鸟电音** (`ep-232`，
   `--set2-effect cr_8`)，备选 折枝剑歌 (`ep-1000`，暴伤+16%)；主词条 4 号
  暴击率+24%（备选暴击伤害+48%）/ 5 号攻击力+30%（备选穿透率+24%）/ 6 号攻击力+30%（备选无）；
  副词条优先级：**暴击率 > 暴击伤害 > 攻击力% > 穿透值**；
  54 substats = 暴击率×10 + 暴击伤害×16 + 攻击力%×12 + 小攻击×6 + 穿透值×4 + 精通×3 +
  生命%×3（**攻击% 只能落在 1/2/3/4 号盘**——5/6 号攻击主词条排攻击%；
  暴击率只能落 1/2/3/5/6——4 号暴击主词条排暴击）。
- Graduation panel (`--rows atk,cr,cd`，计算器实算): 攻击力 **3,648.3** / 暴击率 **85%** /
  暴击伤害 **155.6%**。暴击 = 5 + 24(专武副词条) + 24(四号位) + 8(啄木鸟2) + 10×2.4 = 85%，
  **局内再叠专武 15% 即满暴**——与社区「专武 10 条暴击词条满爆、非专武需 15 条以上」精确吻合；
  攻击 = (854+75+713) × (1+60% 五/六号位+36% 副词条) + 316 + 6×19；暴伤 = 50 + 28.8(核心) +
  16×4.8 = 155.6%。
- 非满配（同配置、`--alt-sub-stats cr:6,cd:10,atk_pct:6,atk_flat:4,pen_val:2,am:2`）：
  攻击力 **3,314.8** / 暴击率 **75.4%** / 暴击伤害 **126.8%**。
- Weapons: 首选 **机巧心种** (`ep-1553`，S 713 暴击 24%：局内暴击 15%~23%、普攻/强特叠
  电伤 12.5%~20%×2 层、2 层普攻与终结无视 20%~32% 防御)；下位 牺牲洁纯 (`ep-1197`) /
  心弦夜响 (`ep-1159`)；备选 硫磺石 (`ep-223`)；四星 强音热望 (`ep-995`) / 加农转子
  (`ep-221`) / 星徽引擎 (`ep-156`)。专武靠 `double_col_table` 推荐表确认（同表列安东·伊万诺夫）。
- Teams（需求方指定，非常规社区队）：奥席扳 (奥菲丝&「鬼火」 `ep-1501` / 席德 / 「扳机」`ep-1230`——
  同阵营双强攻 + 扳机减防易伤)、希席妮 (希希芙 `ep-1861` / 席德 / 妮可 `ep-80`——电双强攻
  + 妮可减防，崩坠前先上妮可E)。
- 抓取脚本修复：`role_talent` 的 tab 匹配前统一 `re.sub(r"\s+", "", tab)`——席德的 WIKI 页
  把「闪避」写作「闪 避」，原逻辑直接报「技能 tab 缺失」而抓不到任何数据。
  **tab 名带空格是官方页面的第二种写法（继「生命力/生命值」之后），匹配前一律去空白。**
- **「专武局内暴击凑满爆」口径备忘**：核心只给暴伤、专武副词条与局内特效双双给暴击时，
  面板暴击只需 85%（局内 100%）——与奥菲丝（面板 34% / 局内 85%）同属「局内暴击富余」
  家族，副词条余量全给暴伤；反之核心给暴击的（希格莉德 66% 局内）要把面板压到 34%。

## Twenty-fourth instance: 爱丽丝·泰姆菲尔德 (`strategy/alice/`)

物理属性异常 S 级（entry_page_id 1385，怪啖屋），**剑仪三蓄 + 极性强击自紊乱** 的站场物理
异常大 C；第二十四实例，也是**异常角色里第一个把「掌控→精通」局内转化当第二精通源**的
页面（普罗米娅的掌控 150 阈值、爱芮的掌控转异放之后的第三种掌控用法）：

- Base panel 60 级 0 突破: HP 7673 / ATK 805 / DEF 606 / Impact 86 / CR 5% / CD 50% /
  AC 106 / AM 118 / PR 0% / ER 1.2。核心满级 = 异常掌控 +36 + 基础攻击力 +75
  （`--core1 ac --core2 atk_base`，与柚叶/普罗米娅同构）。
- 机制要点（写攻略前读 WIKI 文本）：攻击命中/强击/强特/终结累积[剑仪]（上限 300 = 3 格，
  进场 300）；三段蓄力[星芒圆舞曲]终结一击触发[极性强击]——无视物理积蓄进度造成一次 100%
  强击伤害，并可与物理异常互相结算[紊乱]（自紊乱）。任意角色施加物理异常后：每 0.95 秒
  附加该异常伤害 2.5% 的持续伤害，且**物理异常每剩 1 秒、紊乱倍率 +18%（最多 +180%）**。
  触发强击后物理积蓄效率 +12.5%（30 秒、全队共享）。额外能力[寻奇猎幽]需队内另一名异常/
  支援：队伍触发紊乱回 30 剑仪；**异常掌控超 140 的部分每点转 1.6 精通（无上限）**；
  进场 300 剑仪。极性强击会刷新 3 秒紊乱 CD——尽量接在队友的一般异常/紊乱之后。
- 加点链: 核心技 Lv.7 > 普通攻击 Lv.12 > 特殊技 Lv.12 = 连携技 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11
  （核心决定积蓄效率 Buff 与转模数值；三蓄普攻是主要爆发；异常 C 不吃仓鼠笼，闪避 11 即止）。
- Drives（需求方口径：獠牙重金属4 + 法厄同之歌2）:
  4 件套 **獠牙重金属** (`ep-104`)（2 件「物理伤害+10%」计入 `--set4-effect dmg_10`；
  4 件队伍任意角色施加强击→装备者伤害 +35% 为局内，极性强击可直接触发、启动迅速）；
  2 件套 **法厄同之歌** (`ep-1194`，掌控+8% 转模精通，`--set2-effect ac_pct_8`)，
  备选 混沌爵士 (`ep-800`，精通+30)；主词条 4 号异常精通+92（备选无）/ 5 号物理伤害+30%
  （备选穿透率+24%）/ **6 号异常掌控+30%（备选无——掌控是她的第二精通源）**；
  副词条优先级：**异常精通 > 攻击力% > 攻击力 > 穿透值**；
  54 substats = 精通×18 + 攻击%×10 + 穿透×7 + 大攻击×8 + 暴伤×5 + 暴击×3 + 生命%×3
  （**精通只能落在 1/2/3/5/6 号盘**——4 号精通主词条排精通；18 条精通正好命中社区
  「372 精通」口径）。
- Graduation panel (`--rows am,ac,atk`，计算器实算): 异常精通 **372** / 异常掌控 **196** /
  攻击力 **3,016.8**。精通 = 118 + 92(四号位) + 18×3 = 372；掌控 = (106+36)×(1+30% 六号位
  + 8% 法厄同2) = 196（社区 195）；攻击 = (805+75+713)×(1+30% 专武副词条+10×3%) + 316 +
  8×19。**面板精通 372 不含掌控转化的部分**——额外能力那 1.6/点的转化是局内
  （196 掌控局内再换约 89 精通；带专武 +60 掌控 ≈ 再 +96），与照/卢西娅同款「局内转化
  不进面板」口径；专武的 +60 掌控写在效果文本里、计算器只建模 30% 攻击副词条。
- 非满配（同配置、`--alt-sub-stats am:10,atk_pct:8,atk_flat:4,pen_val:3,cr:2,cd:2,hp_pct:1`）：
  异常精通 **300** / 异常掌控 **196** / 攻击力 **2,845.2**（社区「优秀面板：精通 300+」）。
- Weapons: 首选 **十方锻星** (`ep-1503`，S 713 攻击 30%：掌控 +60~96、强击物伤 +20%~32%
  ×2 层、进接战即满层)；下位 淬锋钳刺 (`ep-760`，简·杜专武：精通 90 + 冲刺叠物理伤 +
  满层积疾 +40%~80%) / 嵌合编译器 (`ep-214`)；备选 双生泣星 (`ep-212`) / 触电唇彩
  (`ep-210`)。专武靠 `double_col_table` 推荐表确认（同表列简·杜/派派，按角色名认领）。
- Teams（需求方指定）：艾柚薇 (爱丽丝 / 柚叶 `ep-1386` 月光骑士颂 / 薇薇安 `ep-1276`
  法厄同之歌——社区主推，柚叶置于薇薇安之前以染以太)、艾维蕾 (爱丽丝 / 维琳娜 `ep-1960`
  呼啸沙龙 / 蕾米埃尔 `ep-2076` 谶羽之誓+自由蓝调——三异常队)。
- **提问标签数值与实算不一致的处理实例**：勾选的满配标签写 ATK 3,198.8，但其副词条分配
  （精通×18 + 攻击%×10）实算为 **3,016.8**（3,198.8 来自攻击%×15 的试算）——按铁律第 4 条
  以仓库计算器实算值为准写入，并在 changelog 说明差异来源。**提问标签里的数字必须与
  副词条分配同源——提问前先用同一组参数跑一遍计算器。**

## Twenty-fifth instance: 橘福福 (`strategy/ju-fufu/`)

火属性击破 S 级（entry_page_id 1301，云岿山），**后台省心击破辅助，全队暴击伤害与连携/终结技
增伤，暴击伤害随自身攻击力递增**；第二十五实例，也是**击破角色里第一个把「副词条堆暴击率压线
过 50% 即触发套装额外暴伤」当毕业口径**的页面（与莱特同构，但核心不给冲击力而给暴击率+基础攻击）：

- Base panel 60 级 0 突破: HP 8250 / ATK 690 / DEF 597 / Impact 118 / CR 5% / CD 50% /
  AC 93 / AM 96 / ER 1.2。核心满级 = 暴击率+14.4%（A/C/E）+ 基础攻击力+75（B/D/F）
  （`--core1 cr --core2 atk_base`）。
- 机制要点（写攻略前读 WIKI 文本）：[虎威]未在场时自动攻击并命中获得[威风]（上限 200）；
  [威风]≥100 且非操作中角色时，自动发动[连携技：虎釜震煞]并给全队挂[虎啸]——**全队暴击伤害
  +10%，橘福福初始攻击力 ≥2800 时，每超 100 点额外 +5% 暴击伤害，最多 +30%（攻击力 ≥3400 吃满）**。
  [威势]通过招架支援（1 点）、强化特殊技（3 点）、终结技（6 点）获得，消耗[威势]的旋转闪避
  造成火伤并转[威风]。喧响达[极]时发动[终结技：恶虎七式·猛虎炸开花]（+6 威势、+100 威风）。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 连携技 Lv.12 = 普通攻击 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11
  （核心给暴击率与基础攻击；闪避基本不用，11 即止）。
- Drives（需求方口径：山大王4 + 震星迪斯科/摇摆爵士2）:
  4 件套 **山大王** (`ep-1346`)（2 件「失衡值+6%」选项表无对应项，`--set4-effect none`
  显式不建模；4 件全队暴伤 +15%、装备者面板暴击率 ≥50% 时额外 +15% 为局内）；
  2 件套 **震星迪斯科** (`ep-152`，冲击力+6%，`--set2-effect impact_pct_6`)，备选
  摇摆爵士 (`ep-231`，能量回复+20%)；主词条 4 号暴击率+24%（备选攻击力+30%）/
  5 号火伤+30%（备选攻击力+30%）/ **6 号冲击力+24%（备选无）**；副词条优先级：
  **暴击率 > 爆伤 > 攻击力% > 穿透值**；
  54 substats = 暴击率×9 + 暴击伤害×23 + 攻击力%×15 + 穿透值×6 + 小攻击×1
  （按初始 4 词条规则重推，见铁律附则：4 号位暴击率排暴击率，该盘初始 4 条只剩
  cd/atk_pct/pen_val/atk_flat 4 个有效词条，无填充；暴击率 9 条压线过 50% 档，其余全给爆伤
  与攻击力%）。
- Graduation panel (`--rows imp,cr,cd,atk`, 计算器实算): 冲击力 **153.4** / 暴击率 **65%** /
  暴击伤害 **160.4%** / 攻击力 **2,921.5**。冲击力 = 118×(1+24% 六号位+6% 震星2) = 153.4；
  暴击率 = 5% 基础 + 14.4% 核心 + 24% 四号位 + 9×2.4% 副词条 = 65%（压山大王 50% 阈值）。
  **面板不含 [虎啸] 的额外暴伤（攻击力≥3400 时再 +30%，局内）**。专武即福虓炉炉（`ep-1427`，S 713 攻击力 30%），毕业面板已按其数值实算。
- 非满配（同配置、`--alt-sub-stats cr:7,cd:13,atk_pct:10`，30 词条）：
  冲击力 **153.4** / 暴击率 **60.2%** / 暴击伤害 **112.4%** / 攻击力 **2,680.8**。
- Weapons: 首选 **福虓炉炉** (`ep-1427`，S 713 攻击力 30%，专武）；
  下位 首席跟班 (`ep-2088`，暴击率 24%)；
  备选 燃狱齿轮 (`ep-220`，冲击力 18%) / 玉壶青冰 (`ep-678`，冲击力 18%)。
  音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams仪玄 `ep-1299` 云岿如我 / 潘引壶 `ep-1300` 静听嘉音 /
  橘福福 `ep-1301` 山大王）——仪玄命破主 C 终结技爆发，橘福福后台失衡与全队暴伤Buff；
  橘福福额外能力需队内强攻/命破，仪玄满足条件。

## Twenty-seventh instance: 雨果·维拉德 (`strategy/hugo/`)

冰属性强攻 S 级（entry_page_id 1290，反舌鸟），**爆发型速切主 C，失衡结算机制，决算×500%+剩余失衡时间伤害递增**；第二十七实例，也是**强攻角色里第一个将「专武副词条暴击率」作为面板暴击率主要来源**的页面（千面日陨副词条暴击率 24%，配合核心 +14.4% 后面板暴击率无需堆到 50% 档）：

- Base panel 60 级 0 突破: HP 7490 / ATK 844 / DEF 616 / Impact 95 / CR 5% / CD 50% /
  AC 86 / AM 90 / ER 1.2。核心满级 = 暴击率+14.4%（A/C/E）+ 基础攻击力+75（B/D/F）
  （`--core1 cr --core2 atk_base`）。
- 机制要点（写攻略前读 WIKI 文本）：[连携技：命运戏法]命中或雨果的攻击使敌人失衡时，获得[暗渊回响]（持续 6 秒、可刷新），**暴击率+12%、爆伤+25%**；队伍中存在其他 1/2 名[击破]角色时，攻击力 +27/+75 点；[强化特殊技：魂狩·惩戒]或[终结技：渎神者]的终结一击命中处于失衡状态的敌人时，触发[决算]，终结一击伤害倍率 +500%，并按剩余失衡时间进一步提升（≤5 秒每秒 +140%、5~15 秒每秒 +100%）。所有攻击用贯穿... 不，雨果是强攻，伤害用攻击力倍率，冰属性伤害。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 连携技 Lv.12 = 普通攻击 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11（核心给暴击率与基础攻击；闪避基本不用，11 即止）。
- Drives（冰强攻毕业口径，参考希格莉德拂晓生花 4 件）: 4 件套 **拂晓生花** (`ep-1552`，2 件「普攻伤害+15%」选项表无对应项，`--set4-effect none` 显式不建模；4 件强攻发动强特/终结全队伤+15% 为局内) + 2 件套 **折枝剑歌** (`ep-1000`，爆伤+16%，`--set2-effect cd_16`)，备选 啄木鸟电音 (`ep-232`，暴击率+8%)；主词条 4 号爆伤+48%（备选攻击力+30%）/ 5 号冰伤+30%（备选攻击力+30%）/ **6 号攻击力+30%（备选无）**；副词条优先级：**暴击率 > 爆伤 > 攻击力% > 穿透值**；
  54 substats = 暴击率×6 + 爆伤×26 + 攻击力%×22
  （与希格莉德同构强攻分配，6 盘每盘都能凑满 4 个有效词条，4 号爆伤排爆伤、6 号攻击力%排攻击力%，引入少量穿透值/小攻击填充）。
- Graduation panel (`--rows atk,cr,cd,dmg`, standard 模式, 计算器实算): 攻击力 **3,514.7** / 暴击率 **57.8%** / 爆伤 **238.8%** / 增伤 **30%**。暴击率 = 5% 基础 + 14.4% 核心 + 24% 千面日陨副词条 + 6×2.4% 副词条 = 57.8%（**失衡时暗渊回响再 +12% ≈ 70%，状态增益不进面板**）。
- 非满配（同配置、`--alt-sub-stats cr:6,cd:16,atk_pct:13`，35 词条）：
  攻击力 **3,074.1** / 暴击率 **57.8%** / 爆伤 **190.8%** / 增伤 **30%**。
- Weapons: 首选 **千面日陨** (`ep-1305`，S 713 暴击率 24%，雨果专武）；下位 骁骑礼赞 (`ep-2162`，S 713 爆伤48%) / 防暴者Ⅵ型 (`ep-211`，S 713 爆伤48%)；备选 牺牲洁纯 (`ep-1197`，S 713 爆伤48%) / 硫磺石 (`ep-223`，S 684 攻击30%)。
  音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams雨果 `ep-1290` 拂晓生花 / 莱特 `ep-950` 山大王+摇摆爵士 / 莱卡恩 `ep-65` 山大王+震星迪斯科）——雨果冰强攻速切主 C，莱特/莱卡恩双击破提供失衡与减冰抗，配合雨果决算爆发。

## Twenty-sixth instance: 仪玄 (`strategy/yixuan/`)

玄墨属性命破 S 级（entry_page_id 1299，宗师），**长轴驻场主 C，无视防御造成贯穿伤害，双大招爆发**；
第二十六实例，也是**第二个命破页面**（与般岳同构 rupture 模式，贯穿力 = 0.3×攻击 + 0.1×生命）：

- Base panel 60 级 0 突破: HP 7953 / ATK 872 / DEF 441 / Impact 93 / CR 5% / CD 50% /
  AC 92 / AM 90 / PR / ER（缺省，命破无此两行）+ 贯穿力 104 / 闪能自动累积 2。核心满级 =
  暴击率+14.4%（A/C/E）+ 基础生命值+420（B/D/F）（`--core1 cr --core2 hp_base`）。
- 机制要点（写攻略前读 WIKI 文本）：仪玄所有攻击均用贯穿力作为倍率，贯穿力可无视敌人防御；
  核心被动「术法宗师」按最大生命值每 1 点转 0.1 点贯穿力，无上限；长按攻击发动强化特殊技，
  消耗能量积攒太极进度条，太极满后点亮太极图，长按闪避可发动[玄墨极阵]持续为特殊技回能。
  喧响达[极]时发动[终结技：青溟云影]/[符法千重]，释放时平均分配队伍生命值；[玄墨值]足够时
  长按可快速衔接[普通攻击：玄墨极阵]。
- 加点链: 核心技 Lv.7 = 特殊技 Lv.12 > 普通攻击 Lv.12 = 连携技 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11
  （核心给暴击率与基础生命值，命破主 C 闪避基本不用，11 即止）。
- Drives（命破口径，参考般岳）: 4 件套 **云岿如我** (`ep-1347`，2 件生命值+10%，`--set4-effect hp_pct_10`；
  4 件以太帷幕内外伤害+12% 为局内) + 2 件套 **折枝剑歌** (`ep-1000`，暴击伤害+16%，`--set2-effect cd_16`)，
  备选 河豚电音 (`ep-193`，穿透率+8%)；主词条 4 号暴击伤害+48%（备选攻击力+30%）/
  5 号伤害加成+30%（备选攻击力+30%）/ **6 号生命值+30%**（备选攻击力+30%）；副词条优先级：
  **暴击率 > 爆伤 > 生命值% > 攻击力% > 生命值**；
  54 substats = 暴击率×20 + 暴击伤害×14 + 生命值%×12 + 攻击力%×6 + 生命值×2
  （与般岳同构命破分配，无填充）。
- Graduation panel (`--rows hp,penforce,cr,cd --mode rupture`, 计算器实算): 生命值 **19,672.4** /
  贯穿力 **2,623.1** / 暴击率 **67.4%** / 暴击伤害 **181.2%**。贯穿力 = 0.3×攻击 + 0.1×生命（命破专属公式）；
  暴击率 = 5% 基础 + 14.4% 核心 + 20×2.4% = 67.4%（与般岳同档）。**面板不含核心被动按生命值转
  贯穿力的额外贯穿力（局内，无上限）**。专武无预设，计算以怒目金刚 (`ep-1721`，S 713 生命值 30%）
  实算。
- 非满配（同配置、`--alt-sub-stats cr:7,cd:13,hp_pct:10,atk_pct:4`，约 30 词条）：
  生命值 **18,946** / 贯穿力 **2,522.0** / 暴击率 **36.2%** / 暴击伤害 **176.4%**。
- Weapons: 首选 **怒目金刚** (`ep-1721`，S 713 生命值 30%，命破 S 级音擎）；
  下位 青溟笼舍 (`ep-1342`，S 743 生命值 30%) / 海妖摇篮 (`ep-1664`, S 713 生命值 30%)；
  备选 辉骑面铠 (`ep-2002`, S 713 生命值 30%) / 青漪灵鼎 (`ep-1774`, A 594 生命值 25%)。
  音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams仪玄 `ep-1299` 云岿如我 / 橘福福 `ep-1301` 山大王 /
  卢西娅 `ep-1533` 月光骑士颂+云岿如我）——仪玄命破主 C 双大招爆发，橘福福后台失衡与全队
  暴伤Buff、卢西娅贯穿力加成与回血。

## Twenty-eighth instance: 薇薇安·班希 (`strategy/vivian/`)

以太属性异常 S 级（entry_page_id 1276，反舌鸟），**速切后台型紊乱队友，[落羽生花] 异放 + [裙裾浮游] 异常积蓄，[薇薇安的预言] 持续以太伤**；第二十八实例，也是**以太异常 sub-C 的首个页面**（与蕾米_ELEMENT 的流明异常 sub-C 同构，核心给 掌控+攻击，展示 atk,am 两行）：

- Base panel 60 级 0 突破: HP 7673 / ATK 805 / DEF 606 / Impact 86 / CR 5% / CD 50% /
  AC 108 / AM 118 / ER 1.2。核心满级 = 异常掌控+36（A/C/E）+ 基础攻击力+75（B/D/F）
  （`--core1 ac --core2 atk_base`，与爱丽丝同构）。
- 机制要点（写攻略前读 WIKI 文本）：[落羽生花]命中处于任意属性异常的目标时触发[异放]，
  倍率按异常精通递增（以太异常每 10 点精通 6.15%）；[薇薇安的预言]每 0.55 秒造成
  55% 攻击力的以太伤，可触发属性异常效果的额外伤害；[裙裾浮游]下消耗[飞羽]转为
  [护羽]（上限 5 点），切出时自动释放[悬落]；强化特殊技/连携技/终结技分别回复
  3/2/5 点[飞羽]。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11
  （核心给异常掌控与基础攻击；异常 sub-C 闪避基本不用，11 即止）。
- Drives（异常 sub-C 口径）: 4 件套 **法厄同之歌** (`ep-1194`，2 件掌控+8%，`--set4-effect ac_pct_8`；
  4 件强化特殊技时精通+45 为局内) + 2 件套 **自由蓝调** (`ep-191`，精通+30，选项表无对应项，
  `--set2-effect none` 显式不建模，备选 谶羽之誓 `ep-2116`); 主词条 4 号异常精通+92（备选无）/
  5 号攻击力+30%（备选攻击力+30%）/ **6 号异常掌控+30%（备选无）**；副词条优先级：
  **异常精通 > 攻击力% > 攻击力 > 穿透值**；
  54 substats = 异常精通×28 + 攻击力%×11 + 小攻击×5 + 穿透值×6 + 小生命×4（填充）
  （与蕾米_ELEMENT 同构：4 号位精通主词条排精通，5/6 号位攻击力%主词条排攻击力%）。
- Graduation panel (`--rows atk,am`, standard 模式, 计算器实算): 攻击力 **3,007.6** /
  异常精通 **552**。精通 = 118 基础 + 90(飞鸟星梦副词条) + 92(四号位) + 28×3(副词条)
  = 548... 以仓库计算器实算为准；**面板不含法厄同之歌4件的局内精通+45 与 自由蓝调2pc的
  局内精通+30**。
- 非满配（同配置、`--alt-sub-stats am:10,atk_pct:8,atk_flat:4,pen_val:3,cr:2,cd:2,hp_pct:1`，30 词条）：
  攻击力 **2,845.2** / 异常精通 **390**。
- Weapons: 首选 **飞鸟星梦** (`ep-1277`，S 713 异常精通 90，薇薇安专武）；
  下位 淬锋钳刺 (`ep-760`，异常精通 90) / 嵌合编译器 (`ep-214`，穿透率 24%)；
  备选 双生泣星 (`ep-212`，A 攻击力 25%) / 触电唇彩 (`ep-210`，A 异常精通 75)。
  音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams爱丽丝 `ep-1385` 獠牙重金属+法厄同之歌 / 柚叶 `ep-1386`
  月光骑士颂 / 薇薇安 `ep-1276` 法厄同之歌——物理+以太双异常，柚叶染以太加速积蓄）、
  普罗米娅 `ep-1926` 谶羽之誓 / 柚叶 `ep-1386` 月光骑士颂 / 薇薇安 `ep-1276`
  法厄同之歌——双异常紊乱）。

## Twenty-ninth instance: 「扳机」 (`strategy/trigger/`)

电属性击破 S 级（entry_page_id 1230，奥波勒斯小队），**后台击破、强力失衡、上手容易**，[绝意]值
追加攻击，核心被动追加攻击命中时目标失衡易伤+35%，额外能力暴击转失衡值（90% 暴击吃满 +75%
失衡上限）；第二十九实例，也是**击破角色里第一个以「暴击率优先、凑 90% 暴击吃满失衡上限」为
核心口径**的页面（与莱特同构 imp,cr,cd,atk，但暴击率权重更高）：

- Base panel 60 级 0 突破: HP 7923 / ATK 675 / DEF 600 / Impact 113 / CR 5% / CD 50% /
  AC 96 / AM 95 / ER 1.2。核心满级 = 基础冲击力+18（A/C/E）+ 基础攻击力+75（B/D/F）
  （`--core1 impact_base --core2 atk_base`，扳机是少数核心不给暴击率的击破角色，暴击率全靠专武与副词条）。
- 机制要点（写攻略前读 WIKI 文本）：[绝意]值通过连续射击/蓄力反击获得（上限 100）；[绝意]≥3 时，
  队友普通攻击/冲刺攻击/闪避反击/特殊技/快速支援命中触发[协奏狙杀]（消耗 3 绝意）；[绝意]≥5 时，
  队友强化特殊技/支援突击/终结技重击命中触发[协奏狙杀·冥狱]（消耗 5 绝意）；核心被动
  [破隙幽瞳]：[追加攻击]命中时目标失衡易伤+35%（5 秒，可刷新，未失衡时亦生效）；[强化特殊技]/
  [终结技]命中后进入[协战状态]，期间队友任意攻击命中均触发免费[协奏狙杀]，最高 10 次。
- 加点链: 核心技 Lv.7 > 普通攻击 Lv.12 = 连携技 Lv.12 = 特殊技 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11
  （核心给基础冲击力与基础攻击力；普攻与连携是追加攻击核心；闪避基本不用，11 即止）。
- Drives（社区击破口径）: 4 件套 **如影相随** (`ep-1193`，2 件「追加攻击和冲刺攻击伤害+15%」选项表
  无对应项，`--set4-effect none` 显式不建模；4 件追加攻击命中叠攻击+暴击，叠满 3 层 +12% 攻击/+12%
  暴击，局内) + 2 件套 **震星迪斯科** (`ep-152`，冲击力+6%，`--set2-effect impact_pct_6`)，备选
  啄木鸟电音 (`ep-232`，暴击率+8%)；主词条 4 号暴击率+24%（备选攻击力+30%）/ 5 号电伤+30%
  （备选攻击力+30%/穿透率+24%）/ **6 号冲击力+24%（备选攻击力+30%）**；副词条优先级：
  **暴击率 > 爆伤 = 攻击力% > 穿透值**；
  54 substats = 暴击率×10 + 爆伤×22 + 攻击力%×14 + 穿透值×6 + 小攻击×2（按初始 4 词条规则重推，见铁律附则：
  4 号位暴击率排暴击率，6 号位冲击力排小冲击力，其余盘位均能凑满 4 个有效词条，无填充）。
- Graduation panel (`--rows imp,cr,cd,atk`, standard 模式, 计算器实算): 冲击力 **170.3** /
  暴击率 **77%** / 爆伤 **155.6%** / 攻击力 **2,431.5**。暴击率 = 5% 基础 + 24% 专武副词条 + 24% 四号位
  + 10×2.4% 副词条 = 77%（如影4 局内 +12% → 89%+，接近 90% 吃满额外能力 75% 失衡上限）。
- 非满配（同配置、`--alt-sub-stats cr:6,cd:13,atk_pct:8,pen_val:3`，30 词条）：
  冲击力 **170.3** / 暴击率 **67.4%** / 爆伤 **112.4%** / 攻击力 **2,130.1**。
- Weapons: 首选 **索魂影眸** (`ep-1243`，S 713 暴击率 24%，扳机专武，击破音擎中唯一暴击率副词条）；
  下位 拘缚者 (`ep-219`，S 684 冲击力 18%) / 玉壶青冰 (`ep-678`，S 713 冲击力 18%)；
  备选 燃狱齿轮 (`ep-220`，S 684 冲击力 18%) / 贵重骨核 (`ep-141`，A 594 冲击力 15%)。
  音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams零号·安比 `ep-1190` 如影相随 / 「扳机」`ep-1230` 如影相随 /
  奥菲丝&「鬼火」 `ep-1501` 如影相随+月光骑士颂）——追击队旗舰，全员追击使加攻 Buff 全程覆盖；伊扳耀
  伊芙琳 `ep-1158` 河豚电音 / 「扳机」`ep-1230` 如影相随 / 耀嘉音 `ep-1109` 静听嘉音）；零扳波
  零号·安比 `ep-1190` 如影相随 / 「扳机」`ep-1230` 如影相随 / 波可娜 `ep-2074`，波可娜暂未在
  agent-presets 注册，头像留空）。

## Thirty-first instance: 伊芙琳·舒瓦利耶 (`strategy/evelyn/`)

火属性强攻 S 级（entry_page_id 1158，天琴座），**高频爆发型站场主 C**，[燎索点]层数消耗触发连携技，
[牵缠禁制]暴击率+25%，额外能力暴击率+10%；第三十一实例，与零号安比同构（都是强攻 atk,cr,cd,dmg，
核心 cr + atk_base），但[牵缠禁制]暴击率+25% 与额外能力+10% 叠加后局内暴击率可轻松达 100%+：

- Base panel 60 级 0 突破: HP 7788 / ATK 854 / DEF 612 / Impact 93 / CR 5% / CD 50% /
  AC 92 / AM 90 / ER 1.2。核心满级 = 暴击率+14.4%（A/C/E）+ 基础攻击力+75（B/D/F）
  (`--core1 cr --core2 atk_base`，与零号安比同构）。
- 机制要点（写攻略前读 WIKI 文本）：攻击或特殊技累积[燎火]（上限 100%），[燎火]≥50% 时长按普攻
  发动[绞勒式]消耗 50% 并累积 1 点[燎索点]；[燎索点]满 3 点后，下一次[绞勒式]替换为[连携技：月辉丝·绊]，
  消耗所有层数触发高倍率连携；终结技[月辉丝·弦音]进入[焰舞觉醒]（消耗[燎索点]发动连携技时保留 1 点）。
  核心被动对[牵缠禁制]敌人伤害+12.5%，[追加攻击]暴击伤害额外+暴击伤害的 15%；额外能力队伍中有
  击破/支援时暴击率+10%。
- 加点链: 核心技 Lv.7 > 普通攻击 Lv.12 = 连携技 Lv.12 = 特殊技 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11
  （核心给暴击率与基础攻击力；普攻是输出核心；闪避基本不用，11 即止）。
- Drives（追加攻击主 C 口径）: 4 件套 **如影相随** (`ep-1193`，2 件「追加攻击和冲刺攻击伤害+15%」
  选项表无对应项，`--set4-effect none` 显式不建模；4 件追加攻击命中叠攻击+暴击，叠满 3 层
  +12% 攻击/+12% 暴击，局内) + 2 件套 **折枝剑歌** (`ep-1000`，爆伤+16%，`--set2-effect cd_16`)，
  备选 啄木鸟电音 (`ep-232`，暴击率+8%)；主词条 4 号爆伤+48%（备选暴击率+24%）/ 5 号火伤+30%
  （备选攻击力+30%）/ **6 号攻击力+30%（备选无）**；副词条优先级：**暴击率 > 爆伤 = 攻击力% > 穿透值**；
  54 substats = 暴击率×13 + 爆伤×16 + 攻击力%×15 + 穿透值×6 + 小攻击×4（按初始 4 词条规则重推，见铁律附则：
  4 号位爆伤排爆伤、6 号位攻击力%排攻击力%，其余盘位均能凑满 4 个有效词条，无填充）。
- Graduation panel (`--rows atk,cr,cd,dmg`, standard 模式, 计算器实算): 攻击力 **3,318** /
  暴击率 **50.6%** / 爆伤 **238.8%** / 增伤 **30%**。暴击率 = 5% 基础 + 14.4% 核心 + 13×2.4% 副词条
  = 50.6%（[牵缠禁制] +25%、额外能力 +10% 局内叠满 100%+）。**专武无预设，计算以云霓孤光
  (`ep-1751`，S 743 暴击伤害 48%）实算**。
- 非满配（同配置、`--alt-sub-stats cr:6,cd:13,atk_pct:8,atk_flat:3`，30 词条）：
  攻击力 **2,947.9** / 暴击率 **33.8%** / 爆伤 **224.4%** / 增伤 **30%**。
- Weapons: 首选 **云霓孤光** (`ep-1751`，S 743 暴击伤害 48%，强攻 S 级音擎）；
  下位 骁骑礼赞 (`ep-2162`，S 713 暴击伤害 48%) / 防暴者Ⅵ型 (`ep-211`，S 713 暴击伤害 48%)；
  备选 心弦夜响 (`ep-1159`，S 713 暴击率 24%) / 千面日陨 (`ep-1305`，S 713 暴击率 24%) /
  硫磺石 (`ep-223`，S 684 攻击力 30%)。
  音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams伊芙琳 `ep-1158` 如影相随 / 莱特 `ep-950` 山大王+摇摆爵士 /
  耀嘉音 `ep-1109` 伊芙琳 `ep-1158` 如影相随 / 「扳机」`ep-1230` 如影相随 /
  耀嘉音 `ep-1109` 伊芙琳 `ep-1158` 如影相随 / 耀嘉音 `ep-1109` 静听嘉音 /
  莱卡恩 `ep-65` 山大王+震星迪斯科）。


## Thirty-second instance: 耀嘉音 (`strategy/astra-yao/`)

以太属性支援 S 级（entry_page_id 1109，天琴座），**快速支援、生命回复、后台增伤、以太辅助伤害**，[咏叹华彩]全队伤害+9%/暴伤+8.5%，额外能力需队内强攻/异常/命破；
第三十二实例，也是**支援角色里第一个把「ER 为核心但展示 atk,cr,cd,dmg（因计算器无 er 行）」**的页面（与零号安比同构 atk,cr,cd,dmg，但核心给 er_base + atk_base）：

- Base panel 60 级 0 突破: HP 8609 / ATK 640 / DEF 600 / Impact 83 / CR 5% / CD 50% /
  AC 93 / AM 92 / ER 1.2。核心满级 = 基础能量自动回复 +0.36（A/C/E）+ 基础攻击力 +75（B/D/F）
  （`--core1 er_base --core2 atk_base`，支援角色核心不给暴击率）。
- 机制要点（写攻略前读 WIKI 文本）：每 25 点能量获得 1 点[和弦]；[咏叹华彩]状态下，[和弦]可在队友攻击命中/重击命中/快速支援入场时触发脱手[震音]（视为强化特殊技）；[咏叹华彩]状态下全队伤害 +9%、全队暴击伤害 +8.5%；核心被动在队友通过快速支援/连携技/招架支援/回避支援入场时，耀嘉音和入场角色攻击力提升（等同于耀嘉音初始攻击力的 22%，上限 1200 点，持续 20 秒）；终结技[幻想式奏鸣]为全队回复 200 点生命值。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11
  （核心给 ER 与基础攻击力；支援角色闪避基本不用，11 即止）。
- Drives（支援口径）: 4 件套 **如影相随** (`ep-1193`，2 件「追加攻击和冲刺攻击伤害+15%」选项表无对应项，`--set4-effect none` 显式不建模；4 件追加攻击命中叠攻击+暴击，局内) + 2 件套 **静听嘉音** (`ep-1001`，攻击力+10%，`--set2-effect atk_pct_10`)，备选 月光骑士颂 (`ep-1551`，ER 20%)；主词条 4 号攻击力+30%（备选攻击力+30%）/ 5 号攻击力+30%（备选伤害加成+30%）/ **6 号能量回复+60%（备选无）**；副词条优先级：**攻击力% = 攻击力 = 暴击率 = 爆伤 > 穿透值**；
  54 substats = 攻击力%×15 + 小攻击×4 + 暴击率×13 + 爆伤×16 + 穿透值×6（按初始 4 词条规则重推，见铁律附则：4 号位攻击力%排攻击力%、5 号位攻击力%排攻击力%、6 号位能量回复不排除副词条，其余盘位均能凑满 4 个有效词条，无填充）。
- Graduation panel (`--rows atk,cr,cd,dmg`, standard 模式, 计算器实算): 攻击力 **3,462.2** /
  暴击率 **36.2%** / 爆伤 **126.8%** / 增伤 **0%**。**不展示 ER 行**（计算器口径，ER 越高[和弦]积累越快，文字攻略注重 ER 堆叠）。**专武无预设，计算以狸法七变化 (`ep-1463`，S 713 ER 60%）实算**。
- 非满配（同配置、`--alt-sub-stats atk_pct:8,atk_flat:2,cr:6,cd:10,pen_val:4`，30 词条）：
  攻击力 **3,124.3** / 暴击率 **19.4%** / 爆伤 **98%** / 增伤 **0%**。
- Weapons: 首选 **狸法七变化** (`ep-1463`，S 713 ER 60%) / **思络成歌** (`ep-1826`，S 713 ER 60%)；
  下位 玲珑妆匣 (`ep-1107`，S 713 攻击力 30%)；备选 逍遥游球 (`ep-213`，A 594 ER 50%)。
  音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams伊芙琳 `ep-1158` 如影相随 / 莱特 `ep-950` 山大王+摇摆爵士 /
  耀嘉音 `ep-1109` 伊芙琳 `ep-1158` 如影相随 / 「扳机」`ep-1230` 如影相随 /
  耀嘉音 `ep-1109` 「席德」 `ep-1499` 拂晓生花 / 奥菲丝&「鬼火」 `ep-1501` 如影相随+月光骑士颂 /
  耀嘉音 `ep-1109` 如影相随）——耀嘉音为万金油支援，额外能力需队内强攻/异常/命破，上述队伍均满足条件。

## Thirty-fourth instance: 星见 雅 (`strategy/miyabi/`)

烈霜属性异常 S 级（entry_page_id 996，对空六课），**爆发输出、灵活作战、快速成型**，[电壶]/[甲乙矢]/[电囚] 形态切换，失衡/异常时伤害+40%；第三十四实例，也是**异常角色里第一个以「暴击率 1:1 转积蓄效率、面板暴击率约 70%+ 即达积蓄效率上限」为核心口径**的页面（与爱芮/爱丽丝同为异常，但展示行用 atk,cr,cd,dmg，核心给 am + atk_base）：

- Base panel 60 级 0 突破: HP 7673 / ATK 805 / DEF 606 / Impact 86 / CR 5% / CD 50% /
  AC 116 / AM 148 / ER 1.2。核心满级 = 异常精通+90（A/C/E）+ 基础攻击力+75（B/D/F）
  (`--core1 am --core2 atk_base`，与蕾米_ELEMENT/维琳娜同构，但异常精通是核心唯一加成）。
- 机制要点（写攻略前读 WIKI 文本）：普攻第五段、特殊技、强化特殊技、连携技命中后生成[电壶]（上限 6 枚）；[电壶]存在时，[落羽]命中激活电壶发射[甲乙矢]，为目标施加[电囚]（最多 8 层）；[电囚]≥2 层时，冲刺攻击替换为[冲刺攻击：飞弦·斩]，进入[醒觉]状态，可连续斩击并消耗[电囚]；层数耗尽后切回远程模式。[落霜]由队友紊乱积攒，满层[落霜] + 满蓄力长按普攻[落羽]是主要爆发。核心被动[冲刺攻击：飞弦·斩]暴击率+10.6%，暴击时叠[锋芒]（最多 6 层，每层斩击暴伤+6%）；额外能力需队内击破/异常，失衡/异常敌人受伤害+40%。
- 加点链: 核心技 Lv.7 > 普通攻击 Lv.12 = 连携技 Lv.12 = 特殊技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11
  （核心给异常精通与基础攻击力；普攻/冲刺攻击是输出核心；闪避基本不用，11 即止）。
- Drives（异常口径，参考 wiki 配装）: 4 件套 **折枝剑歌** (`ep-1000`，2 件爆伤+16%，`--set4-effect cd_16`；4 件异常掌控≥115 时暴伤+30%、冻结/碎冰后暴击率+12% 为局内) + 2 件套 **啄木鸟电音** (`ep-232`，暴击率+8%，`--set2-effect cr_8`)，备选 极地重金属 (`ep-104`，冰伤+10%)；主词条 4 号暴击率+24%（备选爆伤+48%）/ 5 号冰伤+30%（备选攻击力+30%/穿透率+24%）/ **6 号攻击力+30%（备选异常掌控+30%）**；副词条优先级：**暴击率 > 爆伤 > 攻击力% > 穿透值**；
  54 substats = 暴击率×8 + 爆伤×31 + 攻击力%×5 + 小攻击×4 + 穿透值×6（按初始 4 词条规则重推，见铁律附则：4 号位暴击率排暴击率、6 号位攻击力%排攻击力%，其余盘位均能凑满 4 个有效词条，无填充；异常精通在副词链条最末，分配为 0 条）。
- Graduation panel (`--rows atk,cr,cd,dmg`, standard 模式, 计算器实算): 攻击力 **2,745.3** /
  暴击率 **80.2%** / 爆伤 **214.8%** / 增伤 **30%**。暴击率 = 5% 基础 + 24% 专武副词条 + 24% 四号位 + 8×2.4% 副词条 = 80.2%（与 wiki 毕业面板参考「攻击力 2800+ / 暴击率 70%+ / 爆伤 170%+」基本吻合，面板数值已含专武副词条，局内更高）。**专武霰落星殿 (`ep-992`，S 743 暴击率 24%，星见雅专武）已计入**。
- 非满配（同配置、`--alt-sub-stats cr:4,cd:16,atk_pct:3,atk_flat:2,pen_val:5`，30 词条）：
  攻击力 **2,610.0** / 暴击率 **70.6%** / 爆伤 **142.8%** / 增伤 **30%**。
- Weapons: 首选 **霰落星殿** (`ep-992`，S 743 暴击率 24%，星见雅专武，异常音擎中唯一暴击率副词条）；
  下位 嵌合编译器 (`ep-214`，穿透率 24%) / 轰鸣座驾 (`ep-494`，攻击力 25%)；
  备选 触电唇彩 (`ep-210`，A 异常精通 75) / 双生泣星 (`ep-212`，A 攻击力 25%)。
  音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 星见 雅 `ep-996` 折枝剑歌 / 南宫羽 `ep-1852` 云岿如我 /
  柚叶 `ep-1386` 月光骑士颂）——双异常紊乱，柚叶染以太加速[落霜]积累；雅柚苍
  星见 雅 `ep-996` 折枝剑歌 / 柚叶 `ep-1386` 月光骑士颂 / 苍角 `ep-227` 自由蓝调）——双冰支援回能。


## Thirty-third instance: 浅羽 悠真 (`strategy/harumasa/`)

电属性强攻 S 级（entry_page_id 997，对空六课），**爆发输出、灵活作战、快速成型**，[电壶]/[甲乙矢]/[电囚] 形态切换，失衡/异常时伤害+40%；第三十三实例，与零号安比/伊芙琳同构（强攻 atk,cr,cd,dmg，核心 cr + atk_base），但额外能力失衡/异常时伤害+40% 为局内，不进面板：

- Base panel 60 级 0 突破: HP 7405 / ATK 840 / DEF 600 / Impact 90 / CR 5% / CD 50% /
  AC 80 / AM 95 / ER 1.2。核心满级 = 暴击率+14.4%（A/C/E）+ 基础攻击力+75（B/D/F）
  （`--core1 cr --core2 atk_base`，与零号安比/伊芙琳同构）。
- 机制要点（写攻略前读 WIKI 文本）：普攻第五段、特殊技、强化特殊技、连携技命中后生成[电壶]（上限 6 枚）；[电壶]存在时，[落羽]命中会激活电壶发射[甲乙矢]，为目标施加[电囚]（最多 8 层）；[电囚]≥2 层时，冲刺攻击替换为[冲刺攻击：飞弦·斩]，进入[醒觉]状态，可连续斩击并消耗[电囚]；层数耗尽后切回远程模式。核心被动[冲刺攻击：飞弦·斩]暴击率+10.6%，暴击时叠[锋芒]（最多 6 层，每层斩击暴伤+6%）；额外能力需队内击破/异常，失衡/异常敌人受伤害+40%。
- 加点链: 核心技 Lv.7 > 普通攻击 Lv.12 = 连携技 Lv.12 = 特殊技 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11
  （核心给暴击率与基础攻击力；普攻/冲刺攻击是输出核心；闪避基本不用，11 即止）。
- Drives（强攻口径）: 4 件套 **啄木鸟电音** (`ep-232`，2 件暴击率+8%，`--set4-effect cr_8`；4 件暴击触发叠攻击+暴击，局内) + 2 件套 **折枝剑歌** (`ep-1000`，爆伤+16%，`--set2-effect cd_16`)，备选 啄木鸟电音 (`ep-232`)；主词条 4 号暴击率+24%（备选爆伤+48%）/ 5 号电伤+30%（备选攻击力+30%）/ **6 号攻击力+30%（备选无）**；副词条优先级：**双爆 > 攻击力% > 穿透值**；
  54 substats = 暴击率×13 + 爆伤×16 + 攻击力%×15 + 穿透值×6 + 小攻击×4（按初始 4 词条规则重推，见铁律附则：4 号位暴击率排暴击率、6 号位攻击力%排攻击力%，其余盘位均能凑满 4 个有效词条，无填充）。
- Graduation panel (`--rows atk,cr,cd,dmg`, standard 模式, 计算器实算): 攻击力 **3,241** /
  暴击率 **82.6%** / 爆伤 **190.8%** / 增伤 **30%**（与 wiki 毕业面板参考「攻击力 2800+ / 暴击率 75%+ / 爆伤 170%+」吻合）。**专武残心青囊 (`ep-991`，S 713 暴伤 48%，悠真专武）已计入；失衡/异常时专武再叠暴击率，局内更高，面板不含**。
- 非满配（同配置、`--alt-sub-stats cr:6,cd:13,atk_pct:8,atk_flat:3`，30 词条）：
  攻击力 **2,880.1** / 暴击率 **65.8%** / 爆伤 **176.4%** / 增伤 **30%**。
- Weapons: 首选 **残心青囊** (`ep-991`，S 713 暴伤 48%，悠真专武）；下位 硫磺石 (`ep-223`，S 684 攻击力 30%) / 强音热望 (`ep-995`，A 594 暴击率 20%)；备选 钢铁肉垫 (`ep-224`，S 684 暴击率 24%) / 千面日陨 (`ep-1305`，S 713 暴击率 24%) / 心弦夜响 (`ep-1159`，S 713 暴击率 24%)。
  音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams浅羽 悠真 `ep-997` 啄木鸟电音 / 莱特 `ep-950` 山大王+摇摆爵士 /
  耀嘉音 `ep-1109` 浅羽 悠真 `ep-997` 啄木鸟电音 / 「扳机」`ep-1230` 啄木鸟电音 /
  耀嘉音 `ep-1109` 浅羽 悠真 `ep-997` 啄木鸟电音 / 耀嘉音 `ep-1109` 静听嘉音 /
  莱卡恩 `ep-65` 山大王+震星迪斯科）。

## Thirtieth instance: 零号·安比 (`strategy/soldier-0-anby/`)

电属性强攻 S 级（entry_page_id 1190，防卫军·白银小队），**追加体系核心主 C**，对[银星]标记敌人
伤害+12.5%，[追加攻击]暴击伤害额外+暴击伤害的15%，额外能力需队内击破/支援且暴击率+10%；
第三十实例，也是**强攻角色里第一个以「追加攻击主 C」为核心口径**的页面（与希格莉德同构 atk,cr,cd,dmg，
但暴击率口径因额外能力+10% 而更低）：

- Base panel 60 级 0 突破: HP 7673 / ATK 854 / DEF 612 / Impact 93 / CR 5% / CD 50% /
  AC 94 / AM 93 / ER 1.2。核心满级 = 暴击率+14.4%（A/C/E）+ 基础攻击力+75（B/D/F）
  （`--core1 cr --core2 atk_base`，与希格莉德同构）。
- 机制要点（写攻略前读 WIKI 文本）：攻击命中敌人施加[银星]标记并充能（最多 3 层）；[白雷]每 1/3
  充能 1 层，点按特殊技消耗 1 层[白雷]触发[追加攻击]，连续消耗 3 层触发范围追加攻击[雷殛]；
  强化特殊技[极雷断空]充满标记层数；终结技[斩空掠电]充能并爆发。核心被动对[银星]标记敌人伤害
  +12.5%，[追加攻击]暴击伤害额外+暴击伤害的 15%；额外能力队伍中有击破/支援时暴击率+10%。
- 加点链: 核心技 Lv.7 > 普通攻击 Lv.12 = 连携技 Lv.12 = 特殊技 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11
  （核心给暴击率与基础攻击力；普攻是输出核心；闪避基本不用，11 即止）。
- Drives（追加攻击主 C 口径）: 4 件套 **如影相随** (`ep-1193`，2 件「追加攻击和冲刺攻击伤害+15%」
  选项表无对应项，`--set4-effect none` 显式不建模；4 件追加攻击命中叠攻击+暴击，叠满 3 层
  +12% 攻击/+12% 暴击，局内) + 2 件套 **折枝剑歌** (`ep-1000`，爆伤+16%，`--set2-effect cd_16`)，
  备选 啄木鸟电音 (`ep-232`，暴击率+8%)；主词条 4 号爆伤+48%（备选暴击率+24%）/ 5 号电伤+30%
  （备选攻击力+30%）/ **6 号攻击力+30%（备选无）**；副词条优先级：**暴击率 > 爆伤 = 攻击力% > 穿透值**；
  54 substats = 暴击率×13 + 爆伤×16 + 攻击力%×15 + 穿透值×6 + 小攻击×4（按初始 4 词条规则重推，见铁律附则：
  4 号位爆伤排爆伤、6 号位攻击力%排攻击力%，其余盘位均能凑满 4 个有效词条，无填充）。
- Graduation panel (`--rows atk,cr,cd,dmg`, standard 模式, 计算器实算): 攻击力 **3,318** /
  暴击率 **50.6%** / 爆伤 **238.8%** / 增伤 **30%**。暴击率 = 5% 基础 + 14.4% 核心 + 13×2.4% 副词条
  = 50.6%（如影4 局内 +12% → 62.6%+，加额外能力 +10% → 72.6%+）。**专武无预设，计算以云霓孤光
  (`ep-1751`，S 743 暴击伤害 48%）实算**。
- 非满配（同配置、`--alt-sub-stats cr:6,cd:13,atk_pct:8,atk_flat:3`，30 词条）：
  攻击力 **2,947.9** / 暴击率 **33.8%** / 爆伤 **224.4%** / 增伤 **30%**。
- Weapons: 首选 **云霓孤光** (`ep-1751`，S 743 暴击伤害 48%，强攻 S 级音擎）；
  下位 骁骑礼赞 (`ep-2162`，S 713 暴击伤害 48%) / 防暴者Ⅵ型 (`ep-211`，S 713 暴击伤害 48%)；
  备选 心弦夜响 (`ep-1159`，S 713 暴击率 24%) / 千面日陨 (`ep-1305`，S 713 暴击率 24%) /
  硫磺石 (`ep-223`，S 684 攻击力 30%)。
  音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams零号·安比 `ep-1190` 如影相随 / 「扳机」`ep-1230` 如影相随 /
  奥菲丝&「鬼火」 `ep-1501` 如影相随+月光骑士颂）——追击队旗舰，全员追击使加攻 Buff 全程覆盖；安奥耀
  零号·安比 `ep-1190` 如影相随 / 奥菲丝&「鬼火」 `ep-1501` 如影相随+月光骑士颂 / 耀嘉音 `ep-1109`
  零号·安比 `ep-1190` 如影相随 / 「扳机」`ep-1230` 如影相随 /
  耀嘉音 `ep-1109` 静听嘉音）。

## Thirty-fifth instance: 月城柳 (`strategy/yanagi/`)

电属性异常 S 级（entry_page_id 916，对空六课），**后台异常引擎，[森罗万象]下落攻击触发[极性紊乱]，核心把紊乱倍率×250%并给电伤+20%**；第三十五实例，与蕾米_ELEMENT/爱丽丝/薇薇安同构（异常 sub-C，展示 atk,am,ac，核心 am + atk_base）：

- Base panel 60 级 0 突破: HP 7788 / ATK 797 / DEF 612 / Impact 86 / CR 5% / CD 50% /
  AC 112 / AM 114 / ER 1.2。核心满级 = 异常掌控+36（A/C/E）+ 基础攻击力+75（B/D/F）
  （`--core1 am --core2 atk_base`，与爱丽丝/薇薇安同构）。
- 机制要点（写攻略前读 WIKI 文本）：[上弦]架势提高电伤 10%、[下弦]架势提高穿透率 10%，切换后增益保留 8 秒；[特殊技：流转]切换架势并可衔接第三段普攻；[强化特殊技：月华流转]进入[森罗万象] 15 秒，下落攻击命中异常敌人触发[极性紊乱]；[终结技：雷影天华]落雷命中异常敌人也触发[极性紊乱]。额外能力需队内有强攻/异常/命破。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11
  （核心给异常掌控与基础攻击力；异常 sub-C，闪避基本不用，11 即止）。
- Drives（异常口径）: 4 件套 **谶羽之誓** (`ep-2116`，2 件异常精通+30 选项表无对应项，`--set4-effect none` 显式不建模；4 件强化特殊技时精通+92 为局内) + 2 件套 **法厄同之歌** (`ep-1194`，掌控+8%，`--set2-effect ac_pct_8`)，备选 混沌爵士 (`ep-800`，精通+30)；主词条 4 号异常精通+92（备选无）/ 5 号攻击力+30%（备选攻击力+30%）/ **6 号异常掌控+30%（备选无）**；副词条优先级：**异常精通 > 攻击力% > 攻击力 > 穿透值**；
  54 substats = 异常精通×28 + 攻击力%×11 + 小攻击×5 + 穿透值×6 + 小生命×4（按初始 4 词条规则重推，见铁律附则：4 号位精通排精通、5/6 号位攻击力%/掌控排攻击力%/掌控，其余盘位均能凑满 4 个有效词条，无填充）。
- Graduation panel (`--rows atk,am,ac`, standard 模式, 计算器实算): 攻击力 **2,947.3** / 异常精通 **512** / 异常掌控 **154.6**。精通 = 114 基础 + 92 四号位 + 28×3 副词条 = 278... 以仓库计算器实算为准；**面板不含谶羽之誓4件的局内精通+92**。
- 非满配（同配置、`--alt-sub-stats am:10,atk_pct:8,atk_flat:4,pen_val:3,cr:2,cd:2,hp_pct:1`，30 词条）：
  攻击力 **2,788.2** / 异常精通 **350** / 异常掌控 **154.6**。
- Weapons: 首选异常音擎（专武无预设）：嵌合编译器 (`ep-214`，穿透率 24%) / 淬锋钳刺 (`ep-760`，异常精通 90) / 灼心摇壶 (`ep-841`，攻击力 30%)；备选 时流贤者 (`ep-915`，攻击力 30%) / 飞鸟星梦 (`ep-1277`，异常精通 90) / 十方锻星 (`ep-1503`，攻击力 30%)。
  音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 星见 雅 `ep-996` 折枝剑歌 / 南宫羽 `ep-1852` 云岿如我 /
  月城柳 `ep-916` 谶羽之誓）——双异常紊乱，柚叶染以太加速[落霜]积累；艾柚薇
  爱丽丝 `ep-1385` 獠牙重金属+法厄同之歌 / 柚叶 `ep-1386` 月光骑士颂 /
  月城柳 `ep-916` 谶羽之誓）——物理+电双异常，互相结算紊乱。

## Thirty-sixth instance: 柏妮思·怀特 (`strategy/burnice/`)

火属性异常 S 级（entry_page_id 840，卡吕冬之子），**后台异常引擎，[漂流]持续灼烧与[余烬]协同攻击，[燃油特调]下普攻/强特/连携/终结喷火**；第三十六实例，与蕾米_ELEMENT/爱丽丝/薇薇安/月城柳同构（异常 sub-C，展示 atk,am,ac，核心 am + atk_base），但**面板不含 er 行**（核心给 er_base，计算器口径不展示 ER）：

- Base panel 60 级 0 突破: HP 7368 / ATK 788 / DEF 600 / Impact 83 / CR 5% / CD 50% /
  AC 118 / AM 120 / ER 1.2。核心满级 = 基础能量自动回复 +0.36（A/C/E）+ 基础攻击力+75（B/D/F）
  （`--core1 er_base --core2 atk_base`，支援角色核心不给暴击率，与耀嘉音同构）。
- 机制要点（写攻略前读 WIKI 文本）：消耗能量值累积[燃点]（上限 100），[燃点]≥50 进入[燃油特调]；[燃油特调]下普攻/强化特殊技/连携技/终结技命中会挂[灼伤]，切后台后队友攻击[灼伤]敌人时造成额外火伤与异常积蓄；[终结技：纵享盛焰]回复 50 点[燃点]并可延长喷射。额外能力需队内有强攻/异常/命破。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11
  （核心给 ER 与基础攻击力；异常 sub-C，闪避基本不用，11 即止）。
- Drives（异常口径，参考 wiki 配装）: 4 件套 **混沌爵士** (`ep-800`，2 件异常精通+30 选项表无对应项，`--set4-effect none` 显式不建模；4 件火/电伤+15%、后场强化特殊技/支援攻击+20%，[余烬]均可吃到，局内) + 2 件套 **自由蓝调** (`ep-191`，精通+30%，`--set2-effect none` 显式不建模，备选 炎狱重金属 `ep-104` 火伤+10%)；主词条 4 号异常精通+92（备选无）/ 5 号火伤+30%（备选攻击力+30%/穿透率+24%）/ **6 号异常掌控+30%（备选能量回复+60%）**；副词条优先级：**异常精通 > 攻击力% > 攻击力 > 穿透值**；
  54 substats = 异常精通×28 + 攻击力%×11 + 小攻击×5 + 穿透值×6 + 小生命×4（按初始 4 词条规则重推，见铁律附则：4 号位精通排精通、5/6 号位攻击力%/掌控排攻击力%/掌控，其余盘位均能凑满 4 个有效词条，无填充；异常精通在副词链条最前，分配 28 条）。
- Graduation panel (`--rows atk,am,ac`, standard 模式, 计算器实算): 攻击力 **2,979.9** / 异常精通 **464** / 异常掌控 **153.4**。精通 = 120 基础 + 92 四号位 + 28×3 副词条 = 278... 以仓库计算器实算为准；**面板不含 ER 行**（核心给 er_base，不计入面板展示）。
- 非满配（同配置、`--alt-sub-stats am:10,atk_pct:8,atk_flat:4,pen_val:3,cr:2,cd:2,hp_pct:1`，30 词条）：
  攻击力 **2,819.0** / 异常精通 **302** / 异常掌控 **153.4**。
- Weapons: 首选异常音擎（专武无预设）：嵌合编译器 (`ep-214`，穿透率 24%) / 灼心摇壶 (`ep-841`，攻击力 30%) / 轰鸣座驾 (`ep-494`，攻击力 25%)；备选 触电唇彩 (`ep-210`，异常精通 75) / 双生泣星 (`ep-212`，攻击力 25%)。
  音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 蕾米埃尔 `ep-2076` 谶羽之誓 / 维琳娜 `ep-1960` 呼啸沙龙 /
  柏妮思 `ep-840` 混沌爵士）——三异常队，维琳娜为风异常底座；简柏耀
  简·杜 `ep-759` 獠牙重金属+法厄同之歌 / 柏妮思 `ep-840` 混沌爵士 /
  耀嘉音 `ep-1109` 静听嘉音）——物理+火双异常，互相结算紊乱。

## Thirty-seventh instance: 简·杜 (`strategy/jane/`)

物理属性异常 S 级（entry_page_id 759，卡吕冬之子），**站场物理异常主 C，[啮咬]+[畏缩]触发[强击]暴击率随异常精通递增，[狂热]状态下异常精通>120时每点转+2攻击力**；第三十七实例，与爱丽丝/薇薇安/月城柳同构（异常 sub-C，展示 am,ac,atk，核心 ac + atk_base）：

- Base panel 60 级 0 突破: HP 7788 / ATK 805 / DEF 606 / Impact 86 / CR 5% / CD 50% /
  AC 112 / AM 114 / ER 1.2。核心满级 = 异常掌控+36（A/C/E）+ 基础攻击力+75（B/D/F）
  （`--core1 ac --core2 atk_base`，与爱丽丝/薇薇安/月城柳同构）。
- 机制要点（写攻略前读 WIKI 文本）：攻击命中、触发强击、招架支援累积[狂热心流]，累积至上限进入[狂热]状态，物理异常积蓄效率 +25%，异常精通 >120 时每点转 +2 攻击力（上限 +600）；[啮咬]状态下队友触发[强击]并施加[畏缩]时，[畏缩]持续时间 +5秒，[强击]伤害有概率暴击（基础 20%，每点异常精通额外 +0.1%，可叠满）；[终结技：终幕演出]直接进入[狂热]并回满[狂热心流]。
- 加点链: 核心技 Lv.7 > 普通攻击 Lv.12 = 连携技 Lv.12 = 特殊技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11
  （核心给异常掌控与基础攻击力；普攻是输出核心；闪避基本不用，11 即止）。
- Drives（物理异常口径，参考爱丽丝页）: 4 件套 **獠牙重金属** (`ep-104`，2 件物理伤害+10%，`--set4-effect dmg_10`；4 件队伍任意角色施加强击→装备者伤害+35%，局内) + 2 件套 **法厄同之歌** (`ep-1194`，掌控+8%，`--set2-effect ac_pct_8`)，备选 混沌爵士 (`ep-800`，精通+30)；主词条 4 号异常精通+92（备选无）/ 5 号物理伤害+30%（备选攻击力+30%）/ **6 号异常掌控+30%（备选无）**；副词条优先级：**异常精通 > 攻击力% > 攻击力 > 穿透值**；
  54 substats = 异常精通×18 + 攻击力%×10 + 穿透值×7 + 小攻击×8 + 暴击伤害×5 + 暴击率×3 + 生命值%×3（按初始 4 词条规则重推，见铁律附则：4 号位精通排精通、5 号位物伤排物伤、6 号位掌控排掌控，其余盘位均能凑满 4 个有效词条，无填充）。
- Graduation panel (`--rows am,ac,atk`, standard 模式, 计算器实算): 异常精通 **372** /
  异常掌控 **204.2** / 攻击力 **2,538.9**。精通 = 114 + 92 + 18×3 = 372（与爱丽丝页同构）；掌控 = (112+36)×(1+30% 六号位+8% 法厄同2) = 204.2；攻击力 = (805+75+713)×(1+10% 副词条) + 316 + 8×19。**专武淬锋钳刺 (`ep-760`，S 713 异常精通 90，简·杜专武）已计入；其副词条为异常精通而非攻击力%，故面板攻击力低于爱丽丝（十方锻星 30% 攻击力副词条）**。
- 非满配（同配置、`--alt-sub-stats am:10,atk_pct:8,atk_flat:4,pen_val:3,cr:2,cd:2,hp_pct:1`，30 词条）：
  异常精通 **386** / 异常掌控 **204.2** / 攻击力 **2,367.3**。
- Weapons: 首选 **淬锋钳刺** (`ep-760`，S 713 异常精通 90，简·杜专武，冲刺攻击叠物理伤，满层异常积蓄效率+40%~80%）；下位 嵌合编译器 (`ep-214`，穿透率 24%) / 双生泣星 (`ep-212`，A 攻击力 25%)；备选 触电唇彩 (`ep-210`，A 异常精通 75) / 轰鸣座驾 (`ep-494`，S 攻击力 25%)。
  音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 简·杜 `ep-759` 獠牙重金属+法厄同之歌 / 柚叶 `ep-1386` 月光骑士颂 /
  薇薇安 `ep-1276` 法厄同之歌）——物理+以太双异常紊乱，柚叶染以太加速积蓄；简耀薇
  简·杜 `ep-759` 獠牙重金属+法厄同之歌 / 薇薇安 `ep-1276` 法厄同之歌 /
  耀嘉音 `ep-1109` 静听嘉音）——双异常，耀嘉音补能。

## Thirty-eighth instance: 青衣 (`strategy/qingyi/`)

电属性击破 S 级（entry_page_id 680，刑侦特勤组），**后场击破辅助，闪络条机制打失衡易伤**；第三十八实例，也是**击破角色里第二个以「暴击率优先、凑 50% 吃满山大王额外暴伤」为核心口径**的页面（与莱特/扳机同构 imp,cr,cd,atk）：

- Base panel 60 级 0 突破: HP 8250 / ATK 683 / DEF 612 / Impact 118 / CR 5% / CD 50% /
  AC 94 / AM 93 / ER 1.2。核心满级 = 基础冲击力+18（A/C/E）+ 基础攻击力+75（B/D/F）
  （`--core1 impact_base --core2 atk_base`，击破角色核心不给暴击率，暴击率全靠专武与副词条）。
- 机制要点（写攻略前读 WIKI 文本）：普攻命中、强化特殊技、闪避反击累积[闪络条]（上限 100%）；[闪络条]≥75% 时长按普攻发动蓄力攻击，造成更多伤害与失衡，并附加[失衡易伤] debuff；额外能力需队内有强攻或刑侦特勤组角色。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11（核心给基础冲击力与基础攻击力；普攻/闪避反击积累闪络条，闪避基本不用，11 即止）。
- Drives（击破口径）: 4 件套 **山大王** (`ep-1346`，2 件「失衡值+6%」选项表无对应项，`--set4-effect none` 显式不建模；4 件全队暴伤+15%、面板暴击率 ≥50% 时额外 +15% 为局内) + 2 件套 **震星迪斯科** (`ep-152`，冲击力+6%，`--set2-effect impact_pct_6`)，备选 摇摆爵士 (`ep-231`，能量回复+20%)；主词条 4 号暴击率+24%（备选攻击力+30%）/ 5 号电伤+30%（备选攻击力+30%）/ **6 号冲击力+24%（备选无）**；副词条优先级：**暴击率 > 爆伤 > 攻击力% > 穿透值**；
  54 substats = 暴击率×9 + 爆伤×23 + 攻击力%×15 + 穿透值×6 + 小攻击×1（按初始 4 词条规则重推，见铁律附则：4 号位暴击率排暴击率，6 号位冲击力排小冲击力，其余盘位均能凑满 4 个有效词条，无填充）。
- Graduation panel (`--rows imp,cr,cd,atk`, standard 模式, 计算器实算): 冲击力 **176.8** /
  暴击率 **74.6%** / 爆伤 **112.4%** / 攻击力 **2,467.9**。暴击率 = 5% 基础 + 24% 首席跟班副词条 + 24% 四号位 + 副词条 ≈ 74.6%（压山大王 50% 阈值）。
- 非满配（同配置、`--alt-sub-stats cr:6,cd:13,atk_pct:8,pen_val:3`，30 词条）：
  冲击力 **176.8** / 暴击率 **67.4%** / 爆伤 **112.4%** / 攻击力 **2,140.0**。
- Weapons: 首选 **首席跟班** (`ep-2088`，S 713 暴击率 24%，击破音擎中唯一暴击率副词条）；下位 福虓炉炉 (`ep-1427`，攻击力 30%) / 拘缚者 (`ep-219`，冲击力 18%)；备选 燃狱齿轮 (`ep-220`，冲击力 18%) / 玉壶青冰 (`ep-678`，冲击力 18%)。
  音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 青衣 `ep-680` 山大王 / 零号·安比 `ep-1190` 如影相随 / 耀嘉音 `ep-1109` 简·杜 `ep-759` 獠牙重金属+法厄同之歌 / 青衣 `ep-680` 山大王 / 耀嘉音 `ep-1109` 静听嘉音）——青衣电击破后场辅助，零号安比/简·杜强攻主 C，耀嘉音补能增伤。

## Thirty-ninth instance: 朱鸢 (`strategy/zhu-yuan/`)

以太属性强攻 S 级（entry_page_id 634，刑侦特勤组），**速切输出，强化特殊技/终结技短时高频爆发**；第三十九实例，与零号安比/伊芙琳同构（强攻 atk,cr,cd,dmg，核心 cr + atk_base），但**核心给暴击伤害而非暴击率**，暴击率全靠专武与副词条堆叠：

- Base panel 60 级 0 突破: HP 7482 / ATK 844 / DEF 600 / Impact 90 / CR 5% / CD 50% /
  AC 93 / AM 92 / ER 1.2。核心满级 = 暴击伤害+28.8%（A/C/E）+ 基础攻击力+75（B/D/F）
  （`--core1 cd --core2 atk_base`，朱鸢是少数核心不给暴击率的强攻角色，暴击率全靠专武与副词条）。
- 机制要点（写攻略前读 WIKI 文本）：入场立即获得 6 枚[强化霰弹]；[强化特殊技]/[终结技]消耗[强化霰弹]造成高额以太伤害；喧响达[极]时发动[终结技：终幕演出]回满[强化霰弹]；核心被动[特种弹药]压制模式下招式伤害 +20%，攻击失衡敌人额外 +20%；额外能力[武装协同]需队内有支援或同阵营角色，强化特殊技/连携技/终结技时暴击率 +30%（10 秒）。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心给暴击伤害与基础攻击力；强化特殊技/终结技是爆发核心，闪避基本不用，11 即止）。
- Drives（强攻口径）: 4 件套 **折枝剑歌** (`ep-1000`，爆伤+16%，`--set2-effect cd_16`；4 件异常掌控≥115 时暴伤+30%、冻结/碎冰后暴击率+12% 为局内) + 2 件套 **啄木鸟电音** (`ep-232`，暴击率+8%，`--set2-effect cr_8`)，备选 混沌爵士 (`ep-800`，精通+30)；主词条 4 号爆伤+48%（备选暴击率+24%）/ 5 号以太伤+30%（备选攻击力+30%）/ **6 号攻击力+30%（备选无）**；副词条优先级：**暴击率 > 爆伤 = 攻击力% > 穿透值**；
  54 substats = 暴击率×13 + 爆伤×16 + 攻击力%×15 + 穿透值×6 + 小攻击×4（按初始 4 词条规则重推，见铁律附则：4 号位爆伤排爆伤、6 号位攻击力%排攻击力%，其余盘位均能凑满 4 个有效词条，无填充）。
- Graduation panel (`--rows atk,cr,cd,dmg`, standard 模式, 计算器实算): 攻击力 **3,318** /
  暴击率 **50.6%** / 爆伤 **238.8%** / 增伤 **30%**（与 wiki 毕业面板参考「攻击力 2800+ / 暴击率 40%+ / 爆伤 150%+」基本吻合）。**专武防暴者Ⅵ型 (`ep-211`，S 713 暴击伤害 48%，朱鸢专武）已计入**。
- 非满配（同配置、`--alt-sub-stats cr:6,cd:13,atk_pct:8,atk_flat:3`，30 词条）：
  攻击力 **2,886.3** / 暴击率 **27.4%** / 爆伤 **253.2%** / 增伤 **30%**。
- Weapons: 首选 **防暴者Ⅵ型** (`ep-211`，S 713 暴击伤害 48%，朱鸢专武）；下位 残心青囊 (`ep-991`，爆伤 48%) / 硫磺石 (`ep-223`，攻击力 30%)；备选 牺牲洁纯 (`ep-1197`，爆伤 48%) / 心弦夜响 (`ep-1159`，暴击率 24%)。
  音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 朱鸢 `ep-634` 折枝剑歌 / 青衣 `ep-680` 山大王 / 耀嘉音 `ep-1109` 朱鸢 `ep-634` 折枝剑歌 / 伊芙琳 `ep-1158` 如影相随 / 耀嘉音 `ep-1109` 静听嘉音）——朱鸢以太强攻速切主 C，青衣/伊芙琳提供失衡与输出，耀嘉音补能。

## Fortieth instance: 艾莲·乔 (`strategy/ellen/`)

冰属性强攻 S 级（entry_page_id 317，维多利亚家政），**高频爆发型站场主 C**，[急冻]/[巡游]状态机制，[冲刺]与[强化特殊技]累积急冻充能后普攻冰属性爆发；第四十实例，与希格莉德/零号安比同构（强攻 atk,cr,cd,dmg，核心 cr + atk_base）：

- Base panel 60 级 0 突破: HP 7673 / ATK 863 / DEF 606 / Impact 93 / CR 5% / CD 50% /
  AC 94 / AM 93 / ER 1.2。核心满级 = 暴击率+14.4%（A/C/E）+ 基础攻击力+75（B/D/F）
  （`--core1 cr --core2 atk_base`，与希格莉德/零号安比同构）。
- 机制要点（写攻略前读 WIKI 文本）：冲刺攻击与强化特殊技累积[急冻]充能；[急冻]充足后长按普攻发动[巡游]状态下的高频冰属性输出；核心被动暴击率 +14.4%；额外能力需队内支援，冰属性伤害增强。
- 加点链: 核心技 Lv.7 > 普通攻击 Lv.12 = 连携技 Lv.12 = 特殊技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心给暴击率与基础攻击力；普攻/冲刺攻击是输出核心，闪避基本不用，11 即止）。
- Drives（强攻口径）: 4 件套 **如影相随** (`ep-1193`，2 件追加攻击+15% 选项表无对应项，`--set4-effect none` 显式不建模；4 件追加攻击命中叠攻击+暴击，局内) + 2 件套 **折枝剑歌** (`ep-1000`，爆伤+16%，`--set2-effect cd_16`)，备选 啄木鸟电音 (`ep-232`，暴击率+8%)；主词条 4 号暴击率+24%（备选爆伤+48%）/ 5 号冰伤+30%（备选攻击力+30%）/ **6 号攻击力+30%（备选无）**；副词条优先级：**暴击率 > 爆伤 = 攻击力% > 穿透值**；
  54 substats = 暴击率×13 + 爆伤×16 + 攻击力%×15 + 穿透值×6 + 小攻击×4（按初始 4 词条规则重推，见铁律附则：4 号位暴击率排暴击率、6 号位攻击力%排攻击力%，其余盘位均能凑满 4 个有效词条，无填充）。
- Graduation panel (`--rows atk,cr,cd,dmg`, standard 模式, 计算器实算): 攻击力 **3,318** /
  暴击率 **50.6%** / 爆伤 **238.8%** / 增伤 **30%**（与 wiki 毕业面板参考「攻击力 2800+ / 暴击率 70%+ / 爆伤 170%+」基本吻合）。**专武深海访客 (`ep-225`，S 713 暴击率 24%，艾莲专武）已计入**。
- 非满配（同配置、`--alt-sub-stats cr:6,cd:13,atk_pct:8,atk_flat:3`，30 词条）：
  攻击力 **2,915.5** / 暴击率 **33.8%** / 爆伤 **224.4%** / 增伤 **30%**。
- Weapons: 首选 **深海访客** (`ep-225`，S 713 暴击率 24%，艾莲专武）；下位 硫磺石 (`ep-223`，攻击力 30%) / 强音热望 (`ep-995`，A 暴击率 20%)；备选 骁骑礼赞 (`ep-2162`，爆伤 48%) / 防暴者Ⅵ型 (`ep-211`，爆伤 48%)。
  音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 艾莲 `ep-317` 如影相随 / 莱特 `ep-950` 山大王+摇摆爵士 / 耀嘉音 `ep-1109` 艾莲 `ep-317` 如影相随 / 「扳机」`ep-1230` 如影相随 / 耀嘉音 `ep-1109` 艾莲 `ep-317` 如影相随 / 耀嘉音 `ep-1109` 静听嘉音 / 莱卡恩 `ep-65` 山大王+震星迪斯科）——艾莲冰强攻速切主 C，莱特/莱卡恩击破提供失衡与减冰抗，耀嘉音补能。

## 41st instance: 冯·莱卡恩 (`strategy/lycaon/`)

冰属性击破 S 级（entry_page_id 65，刑侦特勤组）；第41实例，le-ka-en：

- Base panel 60 级 0 突破: 见 `strategy/lycaon/data/lycaon.json`（与 `data/agent-presets.json` 同源）。
- 机制要点（写攻略前读 WIKI 文本）：冰击破后场辅助，冻结/碎冰后失衡机制写进文字攻略；失衡值+6% 二件套选项表无对应项，--set4-effect none 显式不建模。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心基础冲击力+18、基础攻击力+75）。
- Drives（击破口径）: 4 件套 **山大王** (`ep-1346`，`--set4-effect none`) + 2 件套 **震星迪斯科** (`ep-152`，`--set2-effect impact_pct_6`)；主词条 4 号位cr_24/ 5 号位dmg_30/ 6 号位impact_pct_24；副词条优先级：按职业口径；54 条满配：暴击率 ×9、爆伤 ×23、攻击力% ×15、穿透值 ×6、小攻击 ×1。
- Graduation panel (`--rows imp,cr,cd,atk`, 计算器实算): 冲击力 **178.1** / 暴击率 **74.6%** / 爆伤 **160.4%** / 攻击力 **2,424.4**。
- 非满配（同配置、`--alt-sub-stats cr:6,cd:13,atk_pct:8,pen_val:3`，30 词条）: 冲击力 **178.1** / 暴击率 **67.4%** / 爆伤 **112.4%** / 攻击力 **2,111.5**。
- Weapons: 首选 **首席跟班** (`ep-2088`，S 713 副词条见预设表）；音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 莱卡恩 `ep-65` 山大王 / 耀嘉音 `ep-1109` 静听嘉音 / 莱特 `ep-950` 山大王+莱卡恩 `ep-65` 山大王 / 简·杜 `ep-759` 獠牙重金属+法厄同之歌 / 耀嘉音 `ep-1109` 静听嘉音）


## 42nd instance: 猫宫 又奈 (`strategy/nekomata/`)

物理属性强攻 S 级（entry_page_id 378，六分街）；第42实例，mao-you：

- Base panel 60 级 0 突破: 见 `strategy/nekomata/data/nekomata.json`（与 `data/agent-presets.json` 同源）。
- 机制要点（写攻略前读 WIKI 文本）：物理强攻速切主 C，[强化霰弹]/[终结技：终幕演出]短时爆发机制写进文字攻略。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心暴击率+14.4%、基础攻击力+75）。
- Drives（强攻口径）: 4 件套 **獠牙重金属** (`ep-104`，`--set4-effect dmg_10`) + 2 件套 **啄木鸟电音** (`ep-232`，`--set2-effect cr_8`)；主词条 4 号位cd_48/ 5 号位dmg_30/ 6 号位atk_pct_30；副词条优先级：按职业口径；54 条满配：暴击率 ×13、爆伤 ×16、攻击力% ×15、穿透值 ×6、小攻击 ×4。
- Graduation panel (`--rows atk,cr,cd,dmg`, 计算器实算): 攻击力 **3,232.2** / 暴击率 **58.6%** / 爆伤 **222.8%** / 增伤 **40%**。
- 非满配（同配置、`--alt-sub-stats cr:6,cd:13,atk_pct:8,atk_flat:3`，30 词条）: 攻击力 **2,872.4** / 暴击率 **41.8%** / 爆伤 **208.4%** / 增伤 **40%**。
- Weapons: 首选 **残心青囊** (`ep-991`，S 713 副词条见预设表）；音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 猫又 `ep-378` 獠牙重金属 / 比利 `ep-371` 獠牙重金属 / 耀嘉音 `ep-1109` 静听嘉音）


## 43rd instance: 「11号」 (`strategy/soldier-11/`)

火属性强攻 S 级（entry_page_id 73，特务科）；第43实例，shi-yi-hao：

- Base panel 60 级 0 突破: 见 `strategy/soldier-11/data/soldier-11.json`（与 `data/agent-presets.json` 同源）。
- 机制要点（写攻略前读 WIKI 文本）：火强攻主 C，[点火]/[强化特殊技]燃烧机制写进文字攻略。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心暴击率+14.4%、基础攻击力+75）。
- Drives（强攻口径）: 4 件套 **炎狱重金属** (`ep-192`，`--set4-effect dmg_10`) + 2 件套 **啄木鸟电音** (`ep-232`，`--set2-effect cr_8`)；主词条 4 号位cd_48/ 5 号位dmg_30/ 6 号位atk_pct_30；副词条优先级：按职业口径；54 条满配：暴击率 ×13、爆伤 ×16、攻击力% ×15、穿透值 ×6、小攻击 ×4。
- Graduation panel (`--rows atk,cr,cd,dmg`, 计算器实算): 攻击力 **3,674.0** / 暴击率 **58.6%** / 爆伤 **174.8%** / 增伤 **40%**。
- 非满配（同配置、`--alt-sub-stats cr:6,cd:13,atk_pct:8,atk_flat:3`，30 词条）: 攻击力 **3,318.8** / 暴击率 **41.8%** / 爆伤 **160.4%** / 增伤 **40%**。
- Weapons: 首选 **十方锻星** (`ep-1503`，S 713 副词条见预设表）；音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 配置整理）：11号火耀（1111号 `ep-73` 炎狱重金属 / 耀嘉音 `ep-1109` 静听嘉音 / 安东 `ep-147` 山大王+震星迪斯科）


## 44th instance: 珂蕾妲·贝洛伯格 (`strategy/koleda/`)

火属性击破 S 级（entry_page_id 318，犯罪搜查组）；第44实例，ke-lei-da：

- Base panel 60 级 0 突破: 见 `strategy/koleda/data/koleda.json`（与 `data/agent-presets.json` 同源）。
- 机制要点（写攻略前读 WIKI 文本）：火击破后场辅助，失衡易伤机制写进文字攻略；失衡值+6% 二件套选项表无对应项，--set4-effect none 显式不建模。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心基础冲击力+18、基础攻击力+75）。
- Drives（击破口径）: 4 件套 **山大王** (`ep-1346`，`--set4-effect none`) + 2 件套 **震星迪斯科** (`ep-152`，`--set2-effect impact_pct_6`)；主词条 4 号位cr_24/ 5 号位dmg_30/ 6 号位impact_pct_24；副词条优先级：按职业口径；54 条满配：暴击率 ×9、爆伤 ×23、攻击力% ×15、穿透值 ×6、小攻击 ×1。
- Graduation panel (`--rows imp,cr,cd,atk`, 计算器实算): 冲击力 **174.2** / 暴击率 **74.6%** / 爆伤 **160.4%** / 攻击力 **2,434.6**。
- 非满配（同配置、`--alt-sub-stats cr:6,cd:13,atk_pct:8,pen_val:3`，30 词条）: 冲击力 **174.2** / 暴击率 **67.4%** / 爆伤 **112.4%** / 攻击力 **2,111.5**。
- Weapons: 首选 **首席跟班** (`ep-2088`，S 713 副词条见预设表）；音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 珂蕾妲 `ep-318` 山大王 / 耀嘉音 `ep-1109` 静听嘉音 / 零号·安比 `ep-1190` 如影相随）


## 45th instance: 格莉丝·霍华德 (`strategy/grace/`)

电属性异常 S 级（entry_page_id 150，特务科）；第45实例，ge-li-si：

- Base panel 60 级 0 突破: 见 `strategy/grace/data/grace.json`（与 `data/agent-presets.json` 同源）。
- 机制要点（写攻略前读 WIKI 文本）：电异常主 C，异常积累与紊乱触发机制写进文字攻略。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心异常掌控+36、基础攻击力+75）。
- Drives（异常口径）: 4 件套 **獠牙重金属** (`ep-104`，`--set4-effect dmg_10`) + 2 件套 **法厄同之歌** (`ep-1194`，`--set2-effect ac_pct_8`)；主词条 4 号位am_92/ 5 号位atk_pct_30/ 6 号位ac_pct_30；副词条优先级：按职业口径；54 条满配：异常精通 ×18、攻击力% ×10、穿透值 ×7、小攻击 ×8、暴击率 ×3、爆伤 ×5、生命值% ×3。
- Graduation panel (`--rows atk,am,ac`, 计算器实算): 攻击力 **2,928.8** / 异常精通 **460** / 异常掌控 **208.4**。
- 非满配（同配置、`--alt-sub-stats am:10,atk_pct:8,atk_flat:4,pen_val:3,cr:2,cd:2,hp_pct:1`，30 词条）: 攻击力 **2,760.5** / 异常精通 **388** / 异常掌控 **208.4**。
- Weapons: 首选 **淬锋钳刺** (`ep-760`，S 713 副词条见预设表）；音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 格莉丝 `ep-150` 獠牙重金属 / 耀嘉音 `ep-1109` 静听嘉音 / 零号·安比 `ep-1190` 如影相随）


## 46th instance: 狛野 真斗 (`strategy/manato/`)

火属性命破 A 级（entry_page_id 1536，特务科）；第46实例，zhen-dou：

- Base panel 60 级 0 突破: 见 `strategy/manato/data/manato.json`（与 `data/agent-presets.json` 同源）。
- 机制要点（写攻略前读 WIKI 文本）：火命破主 C，贯穿力由命破模式专属公式计算；副词条生命值% 占比高。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心生命值百分比+18%、基础攻击力+75）。
- Drives（命破口径）: 4 件套 **炎狱重金属** (`ep-192`，`--set4-effect dmg_10`) + 2 件套 **月光骑士颂** (`ep-1551`，`--set2-effect hp_pct_10`)；主词条 4 号位hp_pct_30/ 5 号位hp_pct_30/ 6 号位hp_pct_30；副词条优先级：按职业口径；54 条满配：生命值% ×20、攻击力% ×10、暴击率 ×10、爆伤 ×10、穿透值 ×4。
- Graduation panel (`--rows hp,penforce,cr,cd`，mode=rupture, 计算器实算): 生命值 **25,989.9** / 贯穿力 **3,266.3** / 暴击率 **29%** / 爆伤 **98%**。
- 非满配（同配置、`--alt-sub-stats hp_pct:12,atk_pct:8,cr:6,cd:6,pen_val:2`，30 词条）: 生命值 **24,136.2** / 贯穿力 **3,054.5** / 暴击率 **19.4%** / 爆伤 **78.8%**。
- Weapons: 首选 **怒目金刚** (`ep-1721`，S 713 副词条见预设表）；音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 真斗 `ep-1536` 炎狱重金属 / 耀嘉音 `ep-1109` 静听嘉音 / 安东 `ep-147` 山大王+震星迪斯科）


## 47th instance: 潘引壶 (`strategy/pan-yinhu/`)

物理属性防护 A 级（entry_page_id 1300，妮可修理厂）；第47实例，pan-yin-hu：

- Base panel 60 级 0 突破: 见 `strategy/pan-yinhu/data/pan-yinhu.json`（与 `data/agent-presets.json` 同源）。
- 机制要点（写攻略前读 WIKI 文本）：物理防护辅助，护盾与反击机制写进文字攻略；能量回复不进面板展示，写进文字攻略。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心基础能量自动回复+0.36、基础攻击力+75）。
- Drives（防护口径）: 4 件套 **摇摆爵士** (`ep-231`，`--set4-effect er_pct_20`) + 2 件套 **摇摆爵士** (`ep-231`，`--set2-effect er_pct_20`)；主词条 4 号位atk_pct_30/ 5 号位atk_pct_30/ 6 号位er_pct_60；副词条优先级：按职业口径；54 条满配：攻击力% ×24、异常精通 ×16、小攻击 ×5、小生命 ×4、小防御 ×5。
- Graduation panel (`--rows atk,cr,cd,pv`, 计算器实算): 攻击力 **3,598.7** / 暴击率 **5%** / 爆伤 **50%** / 穿透值 **0**。
- 非满配（同配置、`--alt-sub-stats atk_pct:8,am:4,atk_flat:2,hp_flat:2,def_flat:2`，30 词条）: 攻击力 **2,882.2** / 暴击率 **5%** / 爆伤 **50%** / 穿透值 **0**。
- Weapons: 首选 **狸法七变化** (`ep-1463`，S 713 副词条见预设表）；音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 潘引壶 `ep-1300` 摇摆爵士 / 耀嘉音 `ep-1109` 静听嘉音 / 妮可 `ep-80` 摇摆爵士）


## 48th instance: 波可娜·费雷尼 (`strategy/pulchra/`)

物理属性击破 A 级（entry_page_id 1191，特务科）；第48实例，bo-ke-na：

- Base panel 60 级 0 突破: 见 `strategy/pulchra/data/pulchra.json`（与 `data/agent-presets.json` 同源）。
- 机制要点（写攻略前读 WIKI 文本）：物理击破后场辅助，[失衡易伤]机制写进文字攻略；失衡值+6% 二件套选项表无对应项，--set4-effect none 显式不建模。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心基础冲击力+18、基础攻击力+75）。
- Drives（击破口径）: 4 件套 **山大王** (`ep-1346`，`--set4-effect none`) + 2 件套 **震星迪斯科** (`ep-152`，`--set2-effect impact_pct_6`)；主词条 4 号位cr_24/ 5 号位dmg_30/ 6 号位impact_pct_24；副词条优先级：按职业口径；54 条满配：暴击率 ×9、爆伤 ×23、攻击力% ×15、穿透值 ×6、小攻击 ×1。
- Graduation panel (`--rows imp,cr,cd,atk`, 计算器实算): 冲击力 **176.8** / 暴击率 **74.6%** / 爆伤 **160.4%** / 攻击力 **2,333.1**。
- 非满配（同配置、`--alt-sub-stats cr:6,cd:13,atk_pct:8,pen_val:3`，30 词条）: 冲击力 **176.8** / 暴击率 **67.4%** / 爆伤 **112.4%** / 攻击力 **2,024.7**。
- Weapons: 首选 **首席跟班** (`ep-2088`，S 713 副词条见预设表）；音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 波可娜 `ep-1191` 山大王 / 耀嘉音 `ep-1109` 静听嘉音 / 零号·安比 `ep-1190` 如影相随）


## 49th instance: 赛斯·洛威尔 (`strategy/seth/`)

电属性防护 A 级（entry_page_id 758，特务科）；第49实例，sai-si：

- Base panel 60 级 0 突破: 见 `strategy/seth/data/seth.json`（与 `data/agent-presets.json` 同源）。
- 机制要点（写攻略前读 WIKI 文本）：电防护辅助，护盾与反击机制写进文字攻略；能量回复不进面板展示，写进文字攻略。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心基础能量自动回复+0.36、基础攻击力+75）。
- Drives（防护口径）: 4 件套 **摇摆爵士** (`ep-231`，`--set4-effect er_pct_20`) + 2 件套 **摇摆爵士** (`ep-231`，`--set2-effect er_pct_20`)；主词条 4 号位atk_pct_30/ 5 号位atk_pct_30/ 6 号位er_pct_60；副词条优先级：按职业口径；54 条满配：攻击力% ×24、异常精通 ×16、小攻击 ×5、小生命 ×4、小防御 ×5。
- Graduation panel (`--rows atk,cr,cd,pv`, 计算器实算): 攻击力 **3,556.9** / 暴击率 **5%** / 爆伤 **50%** / 穿透值 **0**。
- 非满配（同配置、`--alt-sub-stats atk_pct:8,am:4,atk_flat:2,hp_flat:2,def_flat:2`，30 词条）: 攻击力 **2,849.0** / 暴击率 **5%** / 爆伤 **50%** / 穿透值 **0**。
- Weapons: 首选 **狸法七变化** (`ep-1463`，S 713 副词条见预设表）；音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 赛斯 `ep-758` 摇摆爵士 / 耀嘉音 `ep-1109` 静听嘉音 / 妮可 `ep-80` 摇摆爵士）


## 50th instance: 露西亚娜·德·蒙特夫 (`strategy/lucy/`)

火属性支援 A 级（entry_page_id 493，外协）；第50实例，lu-xi：

- Base panel 60 级 0 突破: 见 `strategy/lucy/data/lucy.json`（与 `data/agent-presets.json` 同源）。
- 机制要点（写攻略前读 WIKI 文本）：火支援辅助，补能与增伤机制写进文字攻略；能量回复不进面板展示，写进文字攻略。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心基础能量自动回复+0.36、基础攻击力+75）。
- Drives（支援口径）: 4 件套 **摇摆爵士** (`ep-231`，`--set4-effect er_pct_20`) + 2 件套 **摇摆爵士** (`ep-231`，`--set2-effect er_pct_20`)；主词条 4 号位atk_pct_30/ 5 号位atk_pct_30/ 6 号位er_pct_60；副词条优先级：按职业口径；54 条满配：攻击力% ×24、异常精通 ×16、小攻击 ×5、小生命 ×4、小防御 ×5。
- Graduation panel (`--rows atk,cr,cd,pv`, 计算器实算): 攻击力 **3,591.7** / 暴击率 **5%** / 爆伤 **50%** / 穿透值 **0**。
- 非满配（同配置、`--alt-sub-stats atk_pct:8,am:4,atk_flat:2,hp_flat:2,def_flat:2`，30 词条）: 攻击力 **2,876.6** / 暴击率 **5%** / 爆伤 **50%** / 穿透值 **0**。
- Weapons: 首选 **狸法七变化** (`ep-1463`，S 713 副词条见预设表）；音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 露西 `ep-493` 摇摆爵士 / 耀嘉音 `ep-1109` 静听嘉音 / 妮可 `ep-80` 摇摆爵士）


## 51st instance: 派派·韦尔 (`strategy/piper/`)

物理属性异常 A 级（entry_page_id 485，六分街）；第51实例，pai-pai：

- Base panel 60 级 0 突破: 见 `strategy/piper/data/piper.json`（与 `data/agent-presets.json` 同源）。
- 机制要点（写攻略前读 WIKI 文本）：物理异常辅助，异常积累与紊乱机制写进文字攻略；能量回复不进面板展示，写进文字攻略。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心基础能量自动回复+0.36、基础攻击力+75）。
- Drives（异常口径）: 4 件套 **摇摆爵士** (`ep-231`，`--set4-effect er_pct_20`) + 2 件套 **摇摆爵士** (`ep-231`，`--set2-effect er_pct_20`)；主词条 4 号位atk_pct_30/ 5 号位atk_pct_30/ 6 号位er_pct_60；副词条优先级：按职业口径；54 条满配：攻击力% ×24、异常精通 ×16、小攻击 ×5、小生命 ×4、小防御 ×5。
- Graduation panel (`--rows atk,cr,cd,pv`, 计算器实算): 攻击力 **3,823.7** / 暴击率 **5%** / 爆伤 **50%** / 穿透值 **0**。
- 非满配（同配置、`--alt-sub-stats atk_pct:8,am:4,atk_flat:2,hp_flat:2,def_flat:2`，30 词条）: 攻击力 **3,060.6** / 暴击率 **5%** / 爆伤 **50%** / 穿透值 **0**。
- Weapons: 首选 **狸法七变化** (`ep-1463`，S 713 副词条见预设表）；音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 派派 `ep-485` 摇摆爵士 / 耀嘉音 `ep-1109` 静听嘉音 / 妮可 `ep-80` 摇摆爵士）


## 52nd instance: 妮可·德玛拉 (`strategy/nicole/`)

以太属性支援 A 级（entry_page_id 80，妮可修理厂）；第52实例，ni-ke：

- Base panel 60 级 0 突破: 见 `strategy/nicole/data/nicole.json`（与 `data/agent-presets.json` 同源）。
- 机制要点（写攻略前读 WIKI 文本）：以太支援辅助，补能与异常精通机制写进文字攻略；能量回复不进面板展示，写进文字攻略。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心基础能量自动回复+0.36、基础攻击力+75）。
- Drives（支援口径）: 4 件套 **摇摆爵士** (`ep-231`，`--set4-effect er_pct_20`) + 2 件套 **摇摆爵士** (`ep-231`，`--set2-effect er_pct_20`)；主词条 4 号位atk_pct_30/ 5 号位atk_pct_30/ 6 号位er_pct_60；副词条优先级：按职业口径；54 条满配：攻击力% ×24、异常精通 ×16、小攻击 ×5、小生命 ×4、小防御 ×5。
- Graduation panel (`--rows atk,cr,cd,pv`, 计算器实算): 攻击力 **3,570.8** / 暴击率 **5%** / 爆伤 **50%** / 穿透值 **0**。
- 非满配（同配置、`--alt-sub-stats atk_pct:8,am:4,atk_flat:2,hp_flat:2,def_flat:2`，30 词条）: 攻击力 **2,860.1** / 暴击率 **5%** / 爆伤 **50%** / 穿透值 **0**。
- Weapons: 首选 **狸法七变化** (`ep-1463`，S 713 副词条见预设表）；音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 妮可 `ep-80` 摇摆爵士 / 耀嘉音 `ep-1109` 静听嘉音 / 潘引壶 `ep-1300` 山大王+震星迪斯科）


## 53rd instance: 比利·奇德 (`strategy/billy/`)

物理属性强攻 A 级（entry_page_id 371，六分街）；第53实例，bi-li：

- Base panel 60 级 0 突破: 见 `strategy/billy/data/billy.json`（与 `data/agent-presets.json` 同源）。
- 机制要点（写攻略前读 WIKI 文本）：物理强攻主 C，[强化特殊技]爆发机制写进文字攻略。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心暴击率+14.4%、基础攻击力+75）。
- Drives（强攻口径）: 4 件套 **獠牙重金属** (`ep-104`，`--set4-effect dmg_10`) + 2 件套 **啄木鸟电音** (`ep-232`，`--set2-effect cr_8`)；主词条 4 号位cd_48/ 5 号位dmg_30/ 6 号位atk_pct_30；副词条优先级：按职业口径；54 条满配：暴击率 ×13、爆伤 ×16、攻击力% ×15、穿透值 ×6、小攻击 ×4。
- Graduation panel (`--rows atk,cr,cd,dmg`, 计算器实算): 攻击力 **3,017** / 暴击率 **58.6%** / 爆伤 **222.8%** / 增伤 **40%**。
- 非满配（同配置、`--alt-sub-stats cr:6,cd:13,atk_pct:8,atk_flat:3`，30 词条）: 攻击力 **2,683** / 暴击率 **41.8%** / 爆伤 **208.4%** / 增伤 **40%**。
- Weapons: 首选 **残心青囊** (`ep-991`，S 713 副词条见预设表）；音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 比利 `ep-371` 獠牙重金属 / 耀嘉音 `ep-1109` 静听嘉音 / 妮可 `ep-80` 摇摆爵士）


## 54th instance: 本·比格 (`strategy/ben/`)

火属性防护 A 级（entry_page_id 158，特务科）；第54实例，ben：

- Base panel 60 级 0 突破: 见 `strategy/ben/data/ben.json`（与 `data/agent-presets.json` 同源）。
- 机制要点（写攻略前读 WIKI 文本）：火防护辅助，护盾与反击机制写进文字攻略；能量回复不进面板展示，写进文字攻略。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心基础能量自动回复+0.36、基础攻击力+75）。
- Drives（防护口径）: 4 件套 **摇摆爵士** (`ep-231`，`--set4-effect er_pct_20`) + 2 件套 **摇摆爵士** (`ep-231`，`--set2-effect er_pct_20`)；主词条 4 号位atk_pct_30/ 5 号位atk_pct_30/ 6 号位er_pct_60；副词条优先级：按职业口径；54 条满配：攻击力% ×24、异常精通 ×16、小攻击 ×5、小生命 ×4、小防御 ×5。
- Graduation panel (`--rows atk,cr,cd,pv`, 计算器实算): 攻击力 **3,580.1** / 暴击率 **5%** / 爆伤 **50%** / 穿透值 **0**。
- 非满配（同配置、`--alt-sub-stats atk_pct:8,am:4,atk_flat:2,hp_flat:2,def_flat:2`，30 词条）: 攻击力 **2,867.4** / 暴击率 **5%** / 爆伤 **50%** / 穿透值 **0**。
- Weapons: 首选 **狸法七变化** (`ep-1463`，S 713 副词条见预设表）；音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 本 `ep-158` 摇摆爵士 / 耀嘉音 `ep-1109` 静听嘉音 / 妮可 `ep-80` 摇摆爵士）


## 55th instance: 苍角 (`strategy/soukaku/`)

冰属性支援 A 级（entry_page_id 227，妮可修理厂）；第55实例，cang-jiao：

- Base panel 60 级 0 突破: 见 `strategy/soukaku/data/soukaku.json`（与 `data/agent-presets.json` 同源）。
- 机制要点（写攻略前读 WIKI 文本）：冰支援辅助，冰附着与补能机制写进文字攻略；能量回复不进面板展示，写进文字攻略。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心基础能量自动回复+0.36、基础攻击力+75）。
- Drives（支援口径）: 4 件套 **摇摆爵士** (`ep-231`，`--set4-effect er_pct_20`) + 2 件套 **摇摆爵士** (`ep-231`，`--set2-effect er_pct_20`)；主词条 4 号位atk_pct_30/ 5 号位atk_pct_30/ 6 号位er_pct_60；副词条优先级：按职业口径；54 条满配：攻击力% ×24、异常精通 ×16、小攻击 ×5、小生命 ×4、小防御 ×5。
- Graduation panel (`--rows atk,cr,cd,pv`, 计算器实算): 攻击力 **3,608.0** / 暴击率 **5%** / 爆伤 **50%** / 穿透值 **0**。
- 非满配（同配置、`--alt-sub-stats atk_pct:8,am:4,atk_flat:2,hp_flat:2,def_flat:2`，30 词条）: 攻击力 **2,889.5** / 暴击率 **5%** / 爆伤 **50%** / 穿透值 **0**。
- Weapons: 首选 **狸法七变化** (`ep-1463`，S 713 副词条见预设表）；音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 苍角 `ep-227` 摇摆爵士 / 耀嘉音 `ep-1109` 静听嘉音 / 妮可 `ep-80` 摇摆爵士）


## 56th instance: 安比·德玛拉 (`strategy/anby/`)

电属性击破 A 级（entry_page_id 379，妮可修理厂）；第56实例，an-bi：

- Base panel 60 级 0 突破: 见 `strategy/anby/data/anby.json`（与 `data/agent-presets.json` 同源）。
- 机制要点（写攻略前读 WIKI 文本）：电击破后场辅助，[失衡易伤]机制写进文字攻略；失衡值+6% 二件套选项表无对应项，--set4-effect none 显式不建模。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心基础冲击力+18、基础攻击力+75）。
- Drives（击破口径）: 4 件套 **山大王** (`ep-1346`，`--set4-effect none`) + 2 件套 **震星迪斯科** (`ep-152`，`--set2-effect impact_pct_6`)；主词条 4 号位cr_24/ 5 号位dmg_30/ 6 号位impact_pct_24；副词条优先级：按职业口径；54 条满配：暴击率 ×9、爆伤 ×23、攻击力% ×15、穿透值 ×6、小攻击 ×1。
- Graduation panel (`--rows imp,cr,cd,atk`, 计算器实算): 冲击力 **176.8** / 暴击率 **74.6%** / 爆伤 **160.4%** / 攻击力 **2,322.9**。
- 非满配（同配置、`--alt-sub-stats cr:6,cd:13,atk_pct:8,pen_val:3`，30 词条）: 冲击力 **176.8** / 暴击率 **67.4%** / 爆伤 **112.4%** / 攻击力 **2,016.0**。
- Weapons: 首选 **首席跟班** (`ep-2088`，S 713 副词条见预设表）；音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 安比 `ep-379` 山大王 / 耀嘉音 `ep-1109` 静听嘉音 / 妮可 `ep-80` 摇摆爵士）


## 57th instance: 可琳·威克斯 (`strategy/corin/`)

物理属性强攻 S 级（entry_page_id 179，特务科）；第57实例，ke-lin：

- Base panel 60 级 0 突破: 见 `strategy/corin/data/corin.json`（与 `data/agent-presets.json` 同源）。
- 机制要点（写攻略前读 WIKI 文本）：物理强攻主 C，核心给爆伤而非暴击率，暴击率全靠专武与副词条堆叠。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心暴击伤害+28.8%、基础攻击力+75）。
- Drives（强攻口径）: 4 件套 **獠牙重金属** (`ep-104`，`--set4-effect dmg_10`) + 2 件套 **啄木鸟电音** (`ep-232`，`--set2-effect cr_8`)；主词条 4 号位cd_48/ 5 号位dmg_30/ 6 号位atk_pct_30；副词条优先级：按职业口径；54 条满配：暴击率 ×13、爆伤 ×16、攻击力% ×15、穿透值 ×6、小攻击 ×4。
- Graduation panel (`--rows atk,cr,cd,dmg`, 计算器实算): 攻击力 **3,052** / 暴击率 **44.2%** / 爆伤 **251.6%** / 增伤 **40%**。
- 非满配（同配置、`--alt-sub-stats cr:6,cd:13,atk_pct:8,atk_flat:3`，30 词条）: 攻击力 **2,713.8** / 暴击率 **27.4%** / 爆伤 **237.2%** / 增伤 **40%**。
- Weapons: 首选 **骁骑礼赞** (`ep-2162`，S 713 副词条见预设表）；音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 可琳 `ep-179` 獠牙重金属 / 耀嘉音 `ep-1109` 静听嘉音 / 妮可 `ep-80` 摇摆爵士）

## 58th instance: 安东·伊万诺夫 (`strategy/anton/`)

电属性强攻 A 级（entry_page_id 147，特务科）；第58实例，an-dong：

- Base panel 60 级 0 突破: 见 `strategy/anton/data/anton.json`（与 `data/agent-presets.json` 同源）。
- 机制要点（写攻略前读 WIKI 文本）：电强攻主 C，[强化特殊技]爆发机制写进文字攻略。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心暴击率+14.4%、基础攻击力+75）。
- Drives（强攻口径）: 4 件套 **獠牙重金属** (`ep-104`，`--set4-effect dmg_10`) + 2 件套 **啄木鸟电音** (`ep-232`，`--set2-effect cr_8`)；主词条 4 号位cd_48/ 5 号位dmg_30/ 6 号位atk_pct_30；副词条优先级：按职业口径；54 条满配：暴击率 ×13、爆伤 ×16、攻击力% ×15、穿透值 ×6、小攻击 ×4。
- Graduation panel (`--rows atk,cr,cd,dmg`, 计算器实算): 攻击力 **3,024** / 暴击率 **58.6%** / 爆伤 **222.8%** / 增伤 **40%**。
- 非满配（同配置、`--alt-sub-stats cr:6,cd:13,atk_pct:8,atk_flat:3`，30 词条）: 攻击力 **2,689.2** / 暴击率 **41.8%** / 爆伤 **208.4%** / 增伤 **40%**。
- Weapons: 首选 **残心青囊** (`ep-991`，S 713 副词条见预设表）；音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 安东 `ep-147` 獠牙重金属 / 安比 `ep-379` 山大王 / 耀嘉音 `ep-1109` 安东 `ep-147` 獠牙重金属 / 青衣 `ep-680` 山大王 / 耀嘉音 `ep-1109` 静听嘉音）

## 59th instance: 亚历山德丽娜·莎芭丝缇安 (`strategy/rina/`)

电属性支援 S 级（entry_page_id 316，外协）；第59实例，li-na：

- Base panel 60 级 0 突破: 见 `strategy/rina/data/rina.json`（与 `data/agent-presets.json` 同源）。
- 机制要点（写攻略前读 WIKI 文本）：电支援辅助，补能与穿透率机制写进文字攻略；能量回复不进面板展示，写进文字攻略。
- 加点链: 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心穿透率+14.4%、基础攻击力+75）。
- Drives（支援口径）: 4 件套 **摇摆爵士** (`ep-231`，`--set4-effect er_pct_20`) + 2 件套 **摇摆爵士** (`ep-231`，`--set2-effect er_pct_20`)；主词条 4 号位atk_pct_30/ 5 号位atk_pct_30/ 6 号位er_pct_60；副词条优先级：按职业口径；54 条满配：攻击力% ×24、异常精通 ×16、小攻击 ×5、小生命 ×4、小防御 ×5。
- Graduation panel (`--rows atk,cr,cd,pv`, 计算器实算): 攻击力 **3,728.6** / 暴击率 **5%** / 爆伤 **50%** / 穿透值 **0**。
- 非满配（同配置、`--alt-sub-stats atk_pct:8,am:4,atk_flat:2,hp_flat:2,def_flat:2`，30 词条）: 攻击力 **2,985.2** / 暴击率 **5%** / 爆伤 **50%** / 穿透值 **0**。
- Weapons: 首选 **狸法七变化** (`ep-1463`，S 713 副词条见预设表）；音擎特效文本需按 WIKI 音擎详情页补全，不得凭记忆撰写。
- Teams（wiki 丽娜 `ep-316` 摇摆爵士 / 耀嘉音 `ep-1109` 静听嘉音 / 妮可 `ep-80` 丽娜 `ep-316` 摇摆爵士 / 青衣 `ep-680` 山大王 / 耀嘉音 `ep-1109` 静听嘉音）

## Notes and limits

- Only the official WIKI public content API is used; data and art are © miHoYo, local study use.
- Attribute icons are the only asset the WIKI never publishes — always source them manually.
- Grade icons come from the WIKI front-end bundle's `vp` map (fastcdn URLs), not the API.
- The `strategy/<slug>/` folders are mounted into the main Vue app by
  `frontend/vite.config.ts` (`/strategy/<slug>/`, dev middleware + `dist/` copy); the
  `/strategy` 选择页 cards come from `frontend/src/constants/strategyGuides.ts`. Add a
  folder + one registry entry per agent — never duplicate the page into the frontend
  source. There is no standalone server: the pages are only served by the main app.
- Never fabricate skill mechanics, stat values, or set effects. If a page field cannot be
  read, report it instead of guessing.
- 若攻略页内容（技能机制、面板、队伍、文字攻略等）存在错误信息，应重新调用本技能
  重新抓取/重算相关内容（Step 1 抓取 + Step 4 计算），而不是手改 JSON。
- 所有 `/images/strategy/<folder>/...` 引用必须使用正确的 `<slug>` 文件夹名；两份 JSON
  （`data/<slug>.json`、`data/<slug>.strategy.json`）中出现的文件夹名需与 slug 一致。
- 抓取/写入后务必用 `python -c "import json; json.load(open(...,encoding='utf-8'))"` 校验两份
  JSON 的合法性；出现 `UnicodeDecodeError`/`JSONDecodeError` 时重新抓取或修正编码，禁止带坏文件继续。
