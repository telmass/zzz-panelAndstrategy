# 信息采集矩阵：应该寻找的点和相应修改的文件

新增/修正一位代理人时，下面每一行都要有落点。**来源标「用户」的必须逐项确认，不得凭印象填写。**

| 要找的点 | 来源 | 落到哪个文件 | 字段 | 必填 |
| --- | --- | --- | --- | --- |
| 中文名 / 英文名 / 规范 slug | WIKI + `data/catalog/agent-index.json` | `data/catalog/agent-index.json` | `slug` / `en` / `cn_short` / `cn_full` | ✔ |
| WIKI 条目 id | WIKI 代理人索引 | 中间量（供抓取脚本 `--entry-page-id`） | — | ✔ |
| 60 级基础面板（不含核心） | WIKI 晋升滑块「初始 / 满级」**逐字段合并** | `data/catalog/agents.json` | `base.*` | ✔ |
| 核心技 A–F 加成 | WIKI 核心技滑块**逐级**读 | `data/catalog/agents.json` | `core` | ✔ |
| 职业 / 属性 / 评级 | WIKI `role_base_info` | `data/catalog/agents.json` | `roleTag` / `attribute` / `grade` | ✔ |
| 面板模式（通用/命破/锋御） | **用户确认**（不可由职业推断） | `data/catalog/agents.json` | `panelMode` | ✔ |
| 音擎满级基础值 + 固定副词条 | WIKI | `data/catalog/weapons.json` | `base.kind` / `base.value` / `substat` | ✔ |
| 驱动盘 2/4 件套效果 + 图标 | WIKI | `data/catalog/drive-discs.json` | `setEffect2` / `setEffect4` / `image` | ✔ |
| 代理人抓取产物 | WIKI 抓取脚本 | `strategy/<slug>/data/<slug>.json` | 全文 | ✔ |
| **六类招式的满级正文** | WIKI 成长表最后一级的「详情」span | 同上 | `skills[].moves[].text` | ✔ |
| **额外被动 / 额外能力** | WIKI 核心技 desc 的对应段 | 同上 | `skills[core].moves[]` 第二条（`title` + `text`，**无 `growth`**） | ✔ |
| 立绘 / 称号 / 影画图 | WIKI 抓取脚本 | `images/strategy/<slug>/{tachie,title,cinema-2,cinema-3}.webp` | — | ✔ |
| 右侧全身背景图 | Gachabase | `images/strategy/<slug>/background.webp` + 顶层 `background` | — | ✔ |
| 角色框头像（命座推荐） | Nanoka | `images/strategy/<slug>/film.webp` + `cinemaPriority.image` | — | 选填 |
| 属性 / 职业 / 等级图标 | 共享图标集 | `images/{attributes,icons,grades}/<slug>.webp` + `profile.icons` | — | ✔ |
| 头像 | 抓取产物 | `images/agents/<agentId>.webp` + `assets.avatar` | — | ✔ |
| 加点优先级链 | 攻略源 / **用户** | `<slug>.strategy.json` | `skillPriority[]`（`key/label/icon/level/maxLevel/next`） | ✔ |
| 音擎推荐（专属 / 下位 / 备选 / 四星） | 攻略源 / **用户** | `<slug>.strategy.json` | `weapons[]` | ✔ |
| 驱动盘方案（4 件套不同就分页） | 攻略源 / **用户** | `<slug>.strategy.json` | `driveBuilds[]` | ✔ |
| 毕业面板（满配 / 非满配） | 攻略源 / **用户** + 脚本实算 | `<slug>.strategy.json` | `graduationPanel` / `graduationPanelAlt` | ✔ |
| 队伍推荐 | 攻略源 / **用户** | `<slug>.strategy.json` | `teams[].members[]` | ✔ |
| 文字攻略 | 攻略源 / **用户** | `<slug>.strategy.json` | `textGuide[]` | ✔ |
| 攻略页登记表 / Worker 产物 | 生成 | `frontend/src/constants/strategyGuides.ts`、`backend/src/zzz_panel/_bundled_data.py` | 自动 | — |

## 编辑类内容的硬规则

编辑类内容（加点链、音擎推荐、驱动盘方案、毕业面板、队伍、文字攻略）**无法从 WIKI 推导**：

1. 参考页只提供**字段结构**，克隆来的值一律重置为占位并写 `TODO`；
2. 逐项与用户确认后写入真实值；
3. `tools/agent_audit.py` 会检查占位残留，`graduationPanel` 由
   `.github/skills/agent-strategy/scripts/calc_graduation_panel.py` 实算写入，**不要手改**。

## 同职业借鉴的边界

同职业页面之间只借鉴**结构与思路**（字段组织、面板行选择、队伍写法、文字攻略分节），
数值、配装、口径、队伍组合必须按该代理人的实际机制逐条推导。常见差异源：

- 异常掌控 / 异常精通机制（异常与其它职业的堆法不同）
- 资源形态：能量、层数、标记、蓄力条
- 破防与减抗的替代关系（自带减防就不该再堆穿透）
- 副 C 还是主 C（面板行数与词条优先级不同）
- 面板模式（通用 / 命破 / 锋御）——毕业面板的行完全不同
