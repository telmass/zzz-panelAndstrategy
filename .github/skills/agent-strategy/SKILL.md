---
name: agent-strategy
description: Produce a complete "代理人攻略" (agent strategy) page for any Zenless Zone Zero agent — scrape the official HoYoLAB Wiki, structure guide data (skills, cinemas, base panel, showcase art), author the editorial strategy content, compute a fully-geared graduation panel with the repo calculator, and render the local responsive web template. Reference implementation: 叶瞬光 in `strategy/ye-shun-guang/`.
---

# ZZZ Agent Strategy Page

Use this skill when the user names a ZZZ agent and asks for a 攻略 page / strategy page /
agent guide page (加点、武器、驱动盘、毕业面板、队伍、文字攻略) in the style of the
`strategy/ye-shun-guang/` reference implementation (叶瞬光).

The output is a local web page mounted into the main app, one folder per agent under
`strategy/` (folder name = the route slug in the main app):

```
strategy/<slug>/                # workdir；slug 同时是主应用 /strategy/<slug> 路由
├── data/<slug>.json           # 抓取产物（scrape_agent_guide.py）
├── data/<slug>.strategy.json  # 攻略编辑内容（手写 + 计算脚本写入毕业面板）
└── index.html / styles.css / app.js / requirements.txt   # 页面模板（自 strategy/ye-shun-guang/ 复制）
```

**图片一律不放这里**：唯一图片根是 `frontend/public/images/`，JSON 里只写
`/images/…` URL——共享图标（技能 / 职业 / 等级 / 属性）落 `images/{skills,icons,grades,attributes}/`，
每代理人独有的立绘 / 称号 / 影画背景落 `images/strategy/<slug>/`。
**禁止**页相对 `assets/…` 路径。

## Inputs to confirm with the user first

Editorial content is **not** derivable from the Wiki. Before writing
`<slug>.strategy.json`, confirm (ask once, batch the questions):

1. 技能加点优先级链（形如 `核心技 > 连携 = 普攻 = 特殊 > 支援 > 闪避`）与各技能目标等级（核心技上限 7；其余通常 12，闪避可 11）。
2. 武器推荐档位（首选专武 / 下位 / 备选 / 四星）与每档音擎名单。
3. 驱动盘 4 件套与 2 件套（首选 + 备选）、4/5/6 号位主词条首选/备选、副词条优先级链。
4. 毕业面板口径：专武、套装、主词条、副词条 54 条分配。
5. 队伍推荐（1~3 支三人队）与每队一句话总结。
6. 文字攻略（出招表 / 注意事项）——依据抓取到的技能机制文本撰写，不得编造机制。

If the user only says "照叶瞬光的来", apply the 叶瞬光 instance (see §Verified example)
and say so explicitly.

## 铁律：毕业面板没有通用标准，必须按代理人定制

**每个代理人的毕业面板都不一样，禁止把某个代理人的口径默认套给其他代理人。**
叶瞬光与般岳两个实例已经证明了差异是系统性的，不是数值微调：

| 维度 | 叶瞬光（凛刃 · 强攻，标准模式） | 般岳（火 · 命破） | 由什么决定 |
| --- | --- | --- | --- |
| 展示行（`--rows`） | `atk,cr,cd,pv`（攻击 / 双爆 / 穿透值） | `hp,penforce,cr,cd`（生命值 / 贯穿力 / 双爆） | 特性与面板模式：命破的伤害口径是贯穿力，攻击力只是中间量，展示攻击力毫无意义 |
| 面板模式（`--mode`） | `standard` | `rupture`（贯穿力走命破公式） | 预设 `panelMode` |
| 主词条 | 5 / 6 号位攻击力 | 5 号位伤害加成 / 6 号位生命值 | 词条收益：命破贯穿力 = 0.3 × 攻击 + 0.1 × 生命，生命值%直接转化为战斗力 |
| 副词条 54 条分配 | CR 13（面板 50.6%）/ CD 21 / ATK% 20 | CR 20（面板 67.4%）/ CD 14 / HP% 12 / ATK% 8 | 专武局内加成与属性收益：专武给 50% 暴击时面板只需 50%，给 20% 时面板可以推到 67% |
| 暴击率目标 | 50% 档 | 67% 档 | 同上；**不要假设「13 条暴击率」或「50%」是放之四海的标准** |

操作规则：

1. 先读该代理人的 `panelMode`、属性、特性、专武特效与词条收益（命破含生命值转化、
   锋御用实际暴击率口径等），再定展示行 / 模式 / 主词条 / 副词条分配。
2. 毕业面板口径是与用户确认清单的第 4 项——**必须逐代理人确认**，不能沿用上一个代理人的数字。
3. `strategy/<slug>/data/<slug>.strategy.json` 的 `graduationPanel` 由计算脚本按上面的
   口径参数实算写入；换代理人时整组参数（`--rows/--mode/--sub-stats/--main-spec` 等）
   都要重新给，不能只换 id。
4. 若用户给的预期数值与仓库计算器结果不一致（如社区工具的 67.8% vs 本仓 67.4%），
   以仓库计算器为准并说明差异来源（基础值 / 每条数值口径不同），不要手改面板数字迁就。

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
  (schema: `strategy/ye-shun-guang/README.md` §5). `skills[].key` ∈ `basic/dodge/assist/special/chain/core`;
  WIKI tab 终结技 maps to类别 **连携技** (it contains both 连携 and 终结 moves).
- The summary printout is the accuracy gate: agent name, 属性/职业/grade, 基础面板项数,
  6 类技能招式数 (变体锚点已过滤), 影画 6 层, 影画背景图 6 层. Verify before moving on.

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
图标-凛刃) and save it as `frontend/public/images/attributes/<role_attribute>.png`
(`role_attribute` is the slug in `profile`, e.g. `honed_edge`). If you cannot obtain it,
leave it out — the page falls back to an attribute-colour tile — and tell the user.

### Step 3 — Author `<slug>.strategy.json`

Copy `strategy/ye-shun-guang/data/ye-shun-guang.strategy.json` as the template and fill
it per `strategy/ye-shun-guang/README.md` §6. Hard rules:

- `skillPriority`: array order = priority chain; each item `{key, label, icon, level,
  maxLevel, next}` with `next` ∈ `>` / `=` / `` (last empty). Icons reuse
  `/images/skills/<key>.png`. The page shows only `Lv.N` — never write 满级/上限 wording.
- `weapons`: one card per tier (`tier` + `note` + `items[{name,stats,icon}]`); weapon icons
  go to `frontend/public/images/weapons/<entryPageId>.png` and are referenced as
  `/images/weapons/<entryPageId>.png` (fetch the WIKI 音擎 page icon_url).
- `drives`: `set4 {name,label,icon,effect4?}`, `set2 {main,alt}`,
  `mainStats[{slot,main,alt}]`, `subPriority[{label,next}]` with `next` ∈ `>` / `≈` / ``.
  Set icons are `/images/discs/<id>.png` (files already live in
  `frontend/public/images/discs/`); names/effects from `data/drive-disc-presets.json`.
- `teams`: `[{name, members[{agentId,name,role,avatar,note,set4[{name,icon}]}]}]`;
  avatars are `/images/agents/<id>.png` directly — never copy them anywhere.
- `textGuide`: `[{title, lines[]}]`, grounded in the scraped skill text.
- Do **not** hand-edit `graduationPanel` — it is written by Step 4.

### Step 4 — Compute the graduation panel

```
python .github/skills/agent-strategy/scripts/calc_graduation_panel.py \
    --agent-id <id> --weapon-id <id> --set4-id <id> --set2-id <id> \
    [--disc4 cd_48] [--disc5 dmg_30] [--disc6 hp_pct_30] \
    [--set4-effect hp_pct_10] [--set2-effect cd_16] \
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
  贯穿力）；`--mode` 可覆盖。
- 展示行用 `--rows`：**默认 `atk,cr,cd,pv` 只是叶瞬光（强攻）口径，不是通用标准**；
  命破代理人应传 `hp,penforce,cr,cd`（生命值 / 贯穿力 / 双爆）。贯穿力等模式专属行
  来自 `mode_stats`。具体展示哪些行按该代理人的伤害口径定，见上文铁律。
- 2-piece effects are counted **once each** (4-piece in-battle effects are not modeled by
  the calculator).
- 副词条与暴击率目标**没有统一标准**（见上文铁律）：取决于专武局内加成与该属性的
  词条收益。两个实例仅供参考，不是模板：
  叶瞬光（专武局内 +50% 暴击）面板暴击率只需 50% 档 → CR 13 条；
  般岳（专武局内 +20% 暴击、生命值转贯穿力）推到 67% 档 → CR 20 条，
  且要把相当部分副词条分给生命值%。
- Only the rows named by `--rows` are written; the build spec is plain text with
  **no parenthetical notes** (visitor-facing).

### Step 5 — Wire the page template

```
copy strategy/ye-shun-guang/{index.html,styles.css,app.js,requirements.txt}  →  strategy/<slug>/
```

Then edit only the top of `app.js`:

1. `DATA_URL` / `STRATEGY_URL` → the new `data/<slug>.json` / `data/<slug>.strategy.json`.
2. `ATTRIBUTE_TILE_COLORS` — add the agent's attribute colour if missing (10 attributes
   are mapped; new ones need one line).
3. If the WIKI changed the 影画 grouping (not 1-3 / 4-6), adjust `cinema_backdrops()` in the
   scraper script (it picks 影画展示2 for levels ≤3 and 影画展示3 above).

Everything else (module order 攻略→基础面板→技能→影画, sidebar + scroll-spy, skill tabs,
cinema group frames, attribute-coloured module numbers, fonts) is data-driven — do not
restyle per agent.

### Step 6 — Register in the main app

Append one entry to `STRATEGY_GUIDES` in `frontend/src/constants/strategyGuides.ts`
(`slug` must equal the folder name). `vite.config.ts` mounts every
`strategy/<slug>/` that contains `index.html` at `/strategy/<slug>/` (dev middleware +
build copy), and the `/strategy` 选择页 renders one avatar card per registry entry
（一行 5 个，只放头像 + 名字；条目字段只有 `slug` / `name` / `agentId`，职业、
属性、评级等信息不在这里冗余，都在攻略页内），so
after registration the agent is reachable with no other frontend change
（启动页「代理人攻略」入口卡是静态的，无需逐代理人添加）。

### Step 7 — Verify

1. `npm run dev --prefix frontend` → 启动页「代理人攻略」入口卡 → `/strategy` 选择页 →
   该代理人卡片（iframe 内即 `<slug>/` 零依赖静态页）。
2. Render checks: hero four icons (属性/职业/等级/称号), module bands 01-04 and sidebar
   numbers agree, sidebar active state + bottom fallback, grad chain text, weapon tiers,
   drive 4+2, graduation panel 4 values matching Step 4, team cards, skill tabs switch,
   cinema two group frames with the right backdrops, no console errors.
3. Data gates: the scraper summary; `calc_graduation_panel.py --check` exits 0.
4. Assets: every `/images/…` path referenced by the JSONs returns 200 from the server.
5. Launcher: `npm run test --prefix frontend` passes (router + launcher entry guardrails).

## Verified example: 叶瞬光 (`strategy/ye-shun-guang/`)

The reference instance for every rule above:

- entry_page_id 1687; 属性 凛刃 (`honed_edge`), 特性 强攻 (`strike`), grade S, 称号 虚狩·青溟司命.
- Base panel 60 级 0 突破: HP 7673 / ATK 863 / DEF 606 / Impact 83 / CR 5% / CD 50% /
  AC 94 / AM 93 / PR 0% / ER 1.2.
- 加点链: 核心技 Lv.7 > 连携技 Lv.12 = 普通攻击 Lv.12 = 特殊技 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11.
- 副词链条: 暴击率 > 暴击伤害 ≈ 攻击力% > 攻击力（固定值）≈ 穿透值.
- Drives: 4 件套沧浪行歌 (`ep-1754`) + 2 件套折枝剑歌 (`ep-1000`, alt 河豚电音 `ep-193`);
  4 号位暴击伤害+48%, 5/6 号位攻击力+30%; 54 substats CR×13 + CD×21 + ATK%×20.
- Graduation panel (calculator-computed): ATK 4,014.2 / CR 50.6% / CD 262.8% / PEN 0.
- Teams: 叶照千 (叶瞬光/照/千夏), 叶琉千 (叶瞬光/琉音/千夏), 叶照妮 (叶瞬光/照/妮可).
- Cinemas: L1-3 backdrop 影画展示2, L4-6 backdrop 影画展示3 (one big frame each).
- Weapons: 首选 云霓孤光 (`ep-1751`); 下位 残心青囊/牺牲洁纯/骁骑礼赞; 备选 硫磺石; 四星 鎏金花信/强音热望.

## Second instance: 般岳 (`strategy/ban-yue/`)

火属性命破 S 级（entry_page_id 1626），证明「同一套流程可复用到非叶瞬光口径的代理人」：

- Base panel 60 级 0 突破: HP 8497 / ATK 784 / DEF 445 / Impact 95 / CR 5% / CD 50% /
  AC 90 / AM 89（命破无 pr/er 行，改由贯穿力 105 / 闪能自动累积 2 替代）。
- 加点链: 核心技 Lv.7 = 特殊技 Lv.12 > 普通攻击 Lv.12 = 连携技 Lv.12 > 支援技 Lv.12 = 闪避 Lv.11.
- Drives: 4 件套云岿如我 (`ep-1347`) + 2 件套折枝剑歌 (`ep-1000`, alt 啄木鸟电音 `ep-232`);
  4 号位暴击伤害+48%, 5 号位伤害加成+30%, 6 号位生命值+30%;
  54 substats CR×20 + CD×14 + HP%×12 + ATK%×10（命破贯穿力含生命值转化，故给生命值%。
  爆率口径：面板 5% + 核心 14.4% + 20×2.4% = **67.4%**；社区工具里常见的 67.8% 对应
  基础 5.4% 或 2.42%/条，均与官方 WIKI（base 5%）及仓库 options.json（2.4/条）不符）。
- Graduation panel (`--rows hp,penforce,cr,cd`, 计算器实算): 生命值 19,703.8 /
  贯穿力 2,650 / 暴击率 67.4% / 暴击伤害 181.2%（贯穿力 = 0.3×攻击 + 0.1×生命）。
- Weapons: 首选 怒目金刚 (`ep-1721`); 下位 青溟笼舍 (`ep-1342`) / 海妖摇篮 (`ep-1664`);
  备选 青漪灵鼎 (`ep-1774`); 四星 燔火胧夜 (`ep-1612`) / 幻变魔方 (`ep-1343`) / 电波漫步 (`ep-1340`).
- Teams: 般琉卢 (般岳/琉音/卢西娅·艾洛温, 卢西娅套装月光骑士颂),
  般橘卢 (般岳/橘福福/卢西娅·艾洛温, 橘福福套装山大王).
- 属性图标 火 (`fire`): BWIKI 文件 `图标-火属性.png`
  (`https://patchwiki.biligame.com/images/zzz/e/e0/0gvubbv5rdog0jlqxf4gva9j15vzxmi.png`)
  → `frontend/public/images/attributes/fire.png`。

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
