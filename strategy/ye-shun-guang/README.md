# 代理人攻略页模板 · 叶瞬光（参考实例）

从米游社绝区零官方 WIKI 抓取代理人攻略数据，落成两份结构化 JSON，用一个零依赖的
本地网页渲染「代理人攻略」单页。本文档同时是**复刻模板**：按第 9 节的步骤可为任意
代理人产出同规格页面（改数据，不改前端）。

```
strategy/                         ← 攻略板块根目录：一个子目录 = 一个代理人
└── ye-shun-guang/                ← 叶瞬光参考实例（目录名即主应用路由 slug）
    ├── data/
    │   ├── ye-shun-guang.json          # 抓取产物（基础信息/面板/技能/影画/背景图）
    │   └── ye-shun-guang.strategy.json # 攻略编辑内容（加点/武器/驱动盘/队伍/文字攻略）
    ├── index.html                # 页面外壳
    ├── styles.css                # 样式（浅色主题，与主应用「指南/计算器」同套设计令牌）
    ├── app.js                    # 渲染逻辑（读两份 JSON → DOM，无框架）
    ├── requirements.txt          # 抓取脚本依赖（requests + beautifulsoup4）
    └── README.md                 # 本文档
```

本目录**不放图片**：所有图片统一落在 `frontend/public/images/`，JSON 里一律写
`/images/…` URL（共享图标用 `skills/ icons/ grades/ attributes/`，每代理人独有的
立绘 / 称号 / 影画背景用 `strategy/<slug>/`），唯一图片根约定见第 7 节。
抓取脚本位于 `.github/skills/agent-strategy/scripts/scrape_agent_guide.py`。

本目录已被**主应用挂载**：`frontend/vite.config.ts` 的 `strategyPagesPlugin` 把
`strategy/<slug>/` 映射到 `/strategy/<slug>/`（开发期中间件直读、构建期拷入
`dist/`）。主应用的三级入口为：启动页「代理人攻略」入口卡 → `/strategy`
代理人选择页（卡片来自 `frontend/src/constants/strategyGuides.ts` 登记表）→
`/strategy/<slug>` iframe 舞台页。新增代理人在登记表追加一条即可出现在选择页。

## 1. 页面结构（模板契约）

```
┌─ hero ───────────────────────────────────────────────┐
│ [头像] ZENLESS ZONE ZERO — 代理人攻略                  │
│        叶瞬光 [属性][特性][等级][称号]  ← 四枚小图标    │
│        数据来源：米游社绝区零 WIKI，抓取于 …        [立绘]│
└──────────────────────────────────────────────────────┘
┌─ 左侧导航（sticky）──┐  ┌─ 内容区 ────────────────────┐
│ ZZZ 叶瞬光           │  │ 01 攻略   ② 基础面板        │
│  01 攻略             │  │ 03 技能   04 影画           │
│    ├ 加点优先级 …    │  │ （每模块 = 浅色面板 + 编号    │
│  02 基础面板         │  │   头部带 + 白色卡片）         │
│  03 技能             │  │                             │
│    ├ 普通攻击 …      │  │                             │
│  04 影画             │  │                             │
│  数据来源            │  │                             │
└──────────────────────┘  └─────────────────────────────┘
                                    [↑ 返回顶部] 右下角
```

**四大一级模块（顺序固定，编号与侧栏一致）**

| # | 模块 | 内容 |
| --- | --- | --- |
| 01 | 攻略 | 技能加点优先级（`>`/`=` 连接符链）· 武器推荐（按档级分组）· 驱动盘推荐（4+2、主词条首选/备选、副词条 `>`/`≈` 链）· 满配毕业面板（计算器实算 4 项数值 + 配装说明）· 队伍推荐（多支队伍，成员卡 = 左上头像名称 / 左下 4 件套图标 / 右侧定位说明）· 文字攻略（出招表、注意事项） |
| 02 | 基础面板 | 60 级（0 突破）10 项基础数据，5 列网格（2 行） |
| 03 | 技能 | 六大类；**每类内部按招式 tab 二级切换**（单招式类无 tab 直显面板）；面板含描述 + 可展开的各等级详细数据 |
| 04 | 影画 | 按命数分两组大框：**1-3 命共用一张 WIKI 影画展示图、4-6 命共用一张**（由 `cinemaBackdrops` 数据驱动分组），框内三列文字卡半透明叠加在展示图上 |

**交互与动效**

- 左侧导航：四大区块 + 技能六大类子链接 + 攻略六个子链接；滚动侦测高亮（子区块优先于父区块），**触底时兜底高亮页面最后一个目标**（末尾区块不足一屏也能正确切换）；窄屏（≤960px）折叠为顶部「目录」条
- 返回顶部按钮：滚动超过一屏后淡入
- 动效：主模块进入视口淡入上移（一次性）、招式 tab 切换面板淡入、卡片 hover 边框加深/微上移；全部遵循 `prefers-reduced-motion`，且在无 `IntersectionObserver`/`matchMedia` 环境下内容直接可见（不白屏）

## 2. 视觉规范速查

- **主题**：浅色。页面底 `#f2f3f5` → 模块面板 `#f7f8fb` → 卡片纯白 `#fff`，三级层次
- **强调色 = 属性色**（数据驱动）：`app.js` 渲染时由 `ATTRIBUTE_TILE_COLORS[profile.attribute]` 派生三个 CSS 变量——
  - `--attr-color`（本色）：模块编号方块、ZZZ 徽章、侧栏激活左条、导航激活边框
  - `--attr-color-soft`（90% 白混合）：侧栏激活浅底
  - `--attr-color-text`（35% 黑混合）：侧栏激活文字
  - 凛刃 = `#8598b4`；新属性需在 `ATTRIBUTE_TILE_COLORS` 补一行代表色
- **六大类技能类别色**（承袭计算器六模块）：普攻靛 `#6366f1` / 闪避琥珀 `#f59e0b` / 支援绿 `#10b981` / 特殊粉 `#ec4899` / 连携紫 `#8b5cf6` / 核心技橙 `#f97316`——用于板块左侧色条、类名、招式标题、激活 tab 下划线
- **字号**：在基准上整体 ×1.125（约"大一号"），现行档位 12.5 / 13 / 13.5 / 14 / 14.5 / 15 / 16 / 17 / 19 / 22.5 / 34px；调整时统一比例缩放，勿单点改
- **间距/圆角**：4/8/12/16/20/24 与 3/5/8/10px；卡片阴影仅 `0 1px 2px rgb(16 19 24 / 5%)` 发丝线
- 容器最大宽度 1440px；影画网格桌面固定 3 列、窄屏单列

## 3. 环境准备与运行

```powershell
cd C:\code\zzz-panelAndstrategy
uv pip install -r strategy/ye-shun-guang/requirements.txt   # requests + beautifulsoup4（已装可跳过）

# ① 抓取（产出 ye-shun-guang/data/ye-shun-guang.json 与 public/images/ 下的图片）
python .github/skills/agent-strategy/scripts/scrape_agent_guide.py

# ② 计算满配毕业面板（调仓库后端 core 逻辑，写入 strategy JSON）
uv run python .github/skills/agent-strategy/scripts/calc_graduation_panel.py --check    # 校验一致性

# ③ 经主应用打开（唯一入口，攻略页没有独立服务器）
npm run dev --prefix frontend        # 访问 http://localhost:5173/ →「代理人攻略」入口卡
```

进入路径：启动页「代理人攻略」卡 → `/strategy` 选择页 → 叶瞬光卡片 →
`/strategy/ye-shun-guang`（iframe 内是零依赖静态页，自行滚动）。

常用参数：`--entry-page-id <id>` 换条目；`--slug <slug>` 指定独有图片 URL 前缀（默认
`ye-shun-guang`）；`--output` 指定 JSON 路径；`--assets-dir` 指定独有图片目录（默认
`frontend/public/images/strategy/<slug>/`）；`--no-images` 跳过下载（JSON 保留远程 URL，前端回退显示）。

## 4. 数据是怎么抓到的

WIKI 详情页是 SPA，解析 HTML 只能拿到空壳；真正内容走公开内容接口：

```
GET https://act-api-takumi.mihoyo.com/hoyowiki/zzz/wapi/entry_page_v2?entry_page_id=<id>
    （需 Referer: https://baike.mihoyo.com/ 与 x-rpc-wiki_app: zzz，否则 403）
```

按 `data.page.modules[].components[].component_id` 抽取：

| component_id | 抽取内容 |
| --- | --- |
| `role_base_info` | 姓名 / 评级 / 属性 slug / 职业 slug / 称号（`addition_text`）+ 称号配图（`addition_img`）/ 自定义字段 / 立绘 / 页面头像 |
| `role_talent`（技能展示） | 6 个 tab：普攻 / 闪避 / 支援技 / 特殊技 / 终结技 / 核心技；每 tab 的图标与招式（标题 + HTML 描述 + 1-16 级或 A-F 级成长数据） |
| `role_talent`（晋升需求） | 滑块初始行（全量字段）+ 满级行（覆盖生命/攻击/防御），合并为 60 级（0 突破）基础面板，与仓库 `data/agent-presets.json` 的 `base` 同源同值 |
| `double_col_table` | 影画表（表头「影画名称 / 效果展示」，`LEVEL1..6` 行） |
| `map_desc` | `影画展示1/2/3` 原图 URL（影画卡片背景） |

**六大类 ↔ WIKI tab 对应**：普攻→普通攻击、闪避→闪避、支援技→支援技、特殊技→特殊技、
**终结技→连携技**（WIKI 把连携技与终结技合并在同一 tab，本页整体作「连携技」展示）、
核心技→核心技（成长数据为 A-F 级）。

其他自动处理：技能富文本（手柄按键图标、颜色 span、`[技能名]`）清洗为纯文本；
「变体条目」（只有标题无正文的跳转锚点，约占三成）过滤；核心技 desc 固定展示 A 级
数值，脚本从 A-F 成长数据汇总各级增量改写为满级数值（句末标注「满级数据」）。

## 5. JSON 契约 A：抓取产物（`<slug>.json`）

```jsonc
{
  "meta":    { "agentId": "ep-1687", "entryPageId": 1687, "name": "叶瞬光",
               "source": "https://baike.mihoyo.com/zzz/wiki/content/1687/detail", "scrapedAt": "…" },
  "profile": { "name": "叶瞬光", "attribute": "凛刃", "roleTag": "强攻", "grade": "S",
               "factionTitle": "虚狩·青溟司命",
               "customFields": [ { "key": "出生日期", "value": "1/20" } ],
               "intro": "【角色TAG】…\n【角色详情】…",
                "icons": { "profession": "/images/icons/strike.png",
                           "grade": "/images/grades/s.png",
                           "attribute": "/images/attributes/honed_edge.png",   // 无图则 ""
                           "title": "/images/strategy/ye-shun-guang/title.png" } },   // 无称号则 ""
   "basePanel": [ { "label": "生命值", "value": 7673, "unit": "" }, { "label": "暴击率", "value": 5, "unit": "%" } ],
   "assets":  { "avatar": "/images/agents/ep-1687.png", "avatarRemote": "https://…",
                "tachie": "/images/strategy/ye-shun-guang/tachie.png", "tachieRemote": "https://…" },
   "skills":  [ { "key": "basic", "name": "普通攻击", "wikiTab": "普攻",
                  "icon": "/images/skills/basic.png", "iconRemote": "https://…",
                  "moves": [ { "title": "普通攻击：快剑", "text": "点按发动：\n…",
                               "growth": [ { "level": "1", "groups": [ { "name": "伤害倍率", "rows": ["一段伤害倍率：79.4%\n…"] } ] } ] } ] } ],
   "cinemas": [ { "level": 1, "name": "梦中身", "text": "进入战场时，获得6点[青溟剑势]…\n\n无数次午夜梦回…" } ],
   "cinemaBackdrops": { "1": { "image": "/images/strategy/ye-shun-guang/cinema-2.png", "imageRemote": "https://…" },
                         "4": { "image": "/images/strategy/ye-shun-guang/cinema-3.png", "imageRemote": "https://…" } }
}
```

要点：`skills[].key` 固定为 `basic/dodge/assist/special/chain/core`（前端按此排序与上色）；
所有图片字段一律是 `/images/…` URL（禁止页相对 `assets/…`），本地文件缺失时留空、
由 `*Remote` 远程 URL 兜底；`cinemaBackdrops` **按共享图片分组**——同一张图覆盖的命数会
被渲染成同一个大框（当前 1-3 命→影画展示2，4-6 命→影画展示3，分组规则完全由该字段决定）。

## 6. JSON 契约 B：攻略编辑内容（`<slug>.strategy.json`）

与抓取产物分文件维护（重跑抓取不会覆盖手写攻略）。`graduationPanel` 由计算脚本写入，勿手改。

```jsonc
{
  "skillPriority": [                          // 连接符链：数组顺序即优先级
    { "key": "core", "label": "核心技", "icon": "/images/skills/core.png",
      "level": 7, "maxLevel": 7, "next": ">" }
    // next 取值 ">" / "=" / ""（末项空）；页面显示「核心技 Lv.7 > 连携技 Lv.12 = …」
  ],
  "weapons": [                                // 一档一张卡，卡内多把音擎并列一行
    { "tier": "首选", "note": "专武：…",
      "items": [ { "name": "云霓孤光", "stats": "S 级 · 基础攻击 743 · 暴击伤害 48%",
                   "icon": "/images/weapons/ep-1751.png" } ] }
    // tier 例：首选 / 下位 / 备选 / 四星
  ],
  "drives": {
    "set4": { "name": "沧浪行歌", "label": "物理伤害 +10%", "icon": "/images/discs/ep-1754.png",
              "effect4": "装备者处于任意[以太帷幕]中时，…" },        // 四件套原文，可省
    "set2": { "main": { "name": "折枝剑歌", "label": "暴击伤害 +16%", "icon": "/images/discs/ep-1000.png" },
              "alt":  { "name": "河豚电音", "label": "穿透率 +8%",   "icon": "/images/discs/ep-193.png" } },
    "mainStats": [ { "slot": "4 号位", "main": "暴击伤害 +48%", "alt": "攻击力 +30%" } ],
    "subPriority": [ { "label": "暴击率", "next": ">" } ]   // next 取值 ">" / "≈" / ""
  },
  "teams": [
    { "name": "叶照千",
      "members": [ { "agentId": "ep-1687", "name": "叶瞬光", "role": "主 C · 驻场输出",
                     "avatar": "/images/agents/ep-1687.png", "note": "双形态核心，…",
                     "set4": [ { "name": "沧浪行歌", "icon": "/images/discs/ep-1754.png" } ] } ] }
  ],
  "textGuide": [ { "title": "出招表（驻场循环）", "lines": ["① 启动：…", "② 开帷幕：…"] } ],
  "graduationPanel": { "build": { "agent": "叶瞬光", "weapon": "云霓孤光", "core": "…",
                                  "set4": "沧浪行歌", "set2": "折枝剑歌",
                                  "mainStats": "…", "subStats": "…" },
                       "totals": [ { "label": "攻击力", "value": 4014.2, "unit": "" } ],
                       "note": "…", "computedAt": "…" }
}
```

撰写口径（叶瞬光实例，供参考）：加点链 `核心技 Lv.7 > 连携技 Lv.12 = 普通攻击 Lv.12 = 特殊技 Lv.12 > 支援技 Lv.12 > 闪避 Lv.11`（核心技上限 7、闪避 11、其余 12）；
副词链条 `暴击率 > 暴击伤害 ≈ 攻击力% > 攻击力（固定值）≈ 穿透值`；页面**不显示**「满级 / 上限 N」类状态字，只显示 `Lv.N`。

## 7. 图片落点（唯一图片根约定）

**唯一图片根 = `frontend/public/images/`。** 本目录不存图片，JSON 一律写 `/images/…` URL；
本地文件缺失时字段留空、由 `*Remote` 远程 URL 兜底（页相对 `assets/…` 已废弃，禁止再出现）。

| URL 前缀 | 来源 | 说明 |
| --- | --- | --- |
| `/images/skills/<key>.png` | WIKI 技能 tab 图标 | basic/dodge/assist/special/chain/core，全代理人共享，已存在则跳过下载 |
| `/images/icons/<slug>.png` | 仓库 `frontend/public/images/icons/<slug>.png` | 强攻=strike；7 职业齐全，直接引用不复制 |
| `/images/grades/<g>.png` | WIKI 前端 bundle `vp` 映射（fastcdn） | 抓取脚本 `GRADE_ICON_URLS` 已备 s/a/b，已存在则跳过下载 |
| `/images/attributes/<slug>.png` | **需人工放置**（WIKI 接口不下发属性图标） | 凛刃=`attributes/honed_edge.png`；缺失时前端显示属性色牌兜底 |
| `/images/agents/<id>.png` | 仓库 `frontend/public/images/agents/<id>.png` | 头像 / 队伍成员头像，直接引用不复制、不另存 |
| `/images/weapons/<id>.png` | WIKI 音擎页 `icon_url` | 推荐音擎图标，全代理人共享 |
| `/images/discs/<id>.png` | 仓库 `frontend/public/images/discs/<id>.png` | 驱动盘套装图标，直接引用不复制 |
| `/images/strategy/<slug>/tachie.png` | WIKI `role_base_info.tachie_pc` | 每代理人独有，抓取脚本自动下载 |
| `/images/strategy/<slug>/title.png` | WIKI `role_base_info.addition_img` | 称号配图（虚狩专属），无称号的代理人为空 |
| `/images/strategy/<slug>/cinema-<n>.png` | WIKI `map_desc` 影画展示 N | 1-3 命与 4-6 命各一张，每代理人独有 |

## 8. 满配毕业面板（计算器实算）

`.github/skills/agent-strategy/scripts/calc_graduation_panel.py` 从
`data/agent-presets.json` 取 60 级基础面板、从 `data/weapon-presets.json` 取专武、
从 `data/drive-disc-presets.json` 取两套驱动盘，按 **flag 传入的配装口径**（二件套各计一次、
4/5/6 号位主词条、副词条 54 条分配；不传 flag 时用脚本顶部 `BUILD` 常量=叶瞬光口径）
组装 `PanelRequest`，调用与 `POST /api/panel/calc` 同源的 `zzz_panel.services.panel_service`
计算，把 `build`（纯文案，无括号注释）与 `totals` 写进 strategy JSON。面板只展示
攻击 / 双爆 / 穿透值四项，其余行不写入。

常用 flag：`--agent-id / --weapon-id / --set4-id / --set2-id / --disc4 / --disc5 /
--disc6 / --set4-effect / --set2-effect / --sub-stats cr:13,cd:16,… / --main-spec /
--sub-spec / --rows / --mode / --strategy`。命破与锋御代理人的预设没有 `pr`/`er` 行，
脚本按 0 处理；面板模式默认取预设 `panelMode`（般岳=命破 → rupture，才会算贯穿力），
展示行用 `--rows`：默认 `atk,cr,cd,pv`（叶瞬光），命破一般用 `hp,penforce,cr,cd`。

副词条分配口径：**每个代理人的毕业面板标准都不同，禁止把上面的数字默认套给其他代理人**
（依据 SKILL.md「铁律」）。叶瞬光（专武局内 +50% 暴击）面板暴击率到 50% 档，给 13 条；
般岳（专武局内 +20% 暴击、生命值转贯穿力）推到 67% 档，给 20 条并把相当比例副词条分给
生命值%。每个新代理人都要按它的属性 / 特性 / 专武局内加成重新定口径并与需求方确认，
之后 `--check`（带同一套 flag）校验一致性。

## 9. 复刻到新代理人的步骤

1. **建目录**：`strategy/<slug>/`（slug = 小写字母/数字/连字符，将同时是主应用路由）。
   把本目录的 `index.html / styles.css / app.js / requirements.txt` 复制进去，
   数据各自新建 `data/`（图片不再放本目录，见第 7 节）
2. **抓取**：`python .github/skills/agent-strategy/scripts/scrape_agent_guide.py --entry-page-id <id> --slug <slug> --output strategy/<slug>/data/<slug>.json`
   （独有图片默认落 `frontend/public/images/strategy/<slug>/`；共享技能/等级图标
   自动落 `frontend/public/images/{skills,grades}/`，已存在则跳过下载）
3. **补属性图标**：从 WIKI/BWIKI 取属性图标存为 `frontend/public/images/attributes/<role_attribute>.png`
   （`role_attribute` 见抓取产物 `profile`，如 `honed_edge`）；并在 `app.js` 的
   `ATTRIBUTE_TILE_COLORS` 补该属性代表色（已有 10 项）
4. **复用页面**：把 `app.js` 顶部的 `DATA_URL` / `STRATEGY_URL` 改为新文件名
5. **写攻略**：复制 `ye-shun-guang.strategy.json` 为模板，按第 6 节 schema 填写
   加点链 / 武器（图标从 WIKI 音擎页存到 `frontend/public/images/weapons/<id>.png`，
   写 `/images/weapons/<id>.png`）/ 驱动盘（套装图标写
   `/images/discs/<id>.png`，已在 `frontend/public/images/discs/`）/ 队伍（头像直接写
   `/images/agents/<id>.png`）/ 文字攻略
6. **算毕业面板**：按第 8 节用参数化脚本计算并写入 strategy JSON
7. **影画背景**：`cinemaBackdrops` 由抓取脚本按 1-3 / 4-6 命自动生成（用展示 2/3），
   如需调整分组规则改 `cinema_backdrops()` 的 `tab` 选择逻辑
8. **登记到主应用**：在 `frontend/src/constants/strategyGuides.ts` 追加一条
   （slug 与目录名一致），`/strategy` 选择页即出现该代理人的卡片，
   `/strategy/<slug>` 路由随之可达
9. 起前端逐项核对：四枚 hero 图标、加点链与 Lv.、武器分组、驱动盘 4+2、毕业面板四项、
   队伍卡、技能 tab 切换、影画两组大框、侧栏滚动高亮与触底兜底
   （`npm run dev --prefix frontend` → 启动页「代理人攻略」卡 → 选择页进该代理人）

## 10. 备注

- 仅抓取官方 WIKI 公开内容接口，本地学习用途；数据与素材版权归 miHoYo。
- 等级图标来自 WIKI 前端 bundle 的静态资源映射（非接口字段）；属性图标 WIKI 不下发，需人工放置。
- 毕业面板 `note`/`computedAt` 保留在 JSON 中作文档痕迹，页面不渲染。
- 攻略页经 `frontend/vite.config.ts` 挂载进主应用（dev 中间件 + 构建拷贝，
  挂载前缀 `/strategy/`，只放行小写 slug 与常见文件名片段）；`dist/strategy/<slug>/`
  由构建产出，其中的素材总体积较大（叶瞬光约 9MB），部署到 Cloudflare Assets 时按需取舍。
