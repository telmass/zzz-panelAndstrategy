---
name: get-agent-strategy
description: 一站式为绝区零代理人建站或修站——补 mapping 与计算器预设、抓 WIKI 产物与立绘/角色框头像、克隆同职业参考页结构写攻略编辑内容、实算毕业面板、生成登记表与 Worker 产物、跑全量闸门。新代理人一键部署，已有代理人按体检报告修正补充。既有 agent-strategy / fix-agent / do_calculatorModel / agent-background 等 skill 均由本 skill 编排。
---

# 代理人攻略一站式部署（get-agent-strategy）

**这是代理人攻略流程的唯一入口。** 新增一位代理人、或修正补充已有代理人的攻略页，都走这里；
`agent-strategy` / `fix-agent` / `do_calculatorModel` / `agent-background` / `read-zzz-*` 是本 skill 编排的子流程，
也可单独使用。

## 两种模式

| 模式 | 判定 | 做法 |
| --- | --- | --- |
| **新建** | `data/catalog/agent-index.json` 里没有该 slug | 走 A→F 六个阶段 |
| **修正** | 已有 slug | 先 `python tools/agent_audit.py --slug <slug>` 拿体检报告，再按报告逐条修 |

> `severian`（赛维里安）等**官方未公开**的代理人只有 mapping 条目、没有攻略目录，属正常；
> 体检会报 INFO，不是 ERROR。

## 编排脚本

```powershell
python tools/agent_deploy.py --name 希希芙              # 新建：全阶段
python tools/agent_deploy.py --slug cissia --stages editorial,panel,register,verify
python tools/agent_deploy.py --name 希希芙 --dry-run    # 只看要做什么
```

阶段：`identity → presets → scrape → images → editorial → panel → register → verify`。
脚本只跑**机械环节**；编辑内容（阶段 D）由它生成骨架与待确认清单，**内容必须与用户逐项确认**。

## 阶段

### 阶段 0 · 模式判定

```powershell
python tools/agent_audit.py --slug <slug>     # 修正模式：先拿报告
```

### 阶段 A · 身份解析

中文名 → `slug` / WIKI 条目 id / 属性 / 职业 / 评级 / 面板模式。

- slug 以 `data/catalog/agent-index.json` 为唯一准绳（见 [`_shared/naming.md`](../_shared/naming.md)）
- 面板模式（通用/命破/锋御）**不可由职业推断**，须用户确认

### 阶段 B · 数据层

```powershell
python .github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py
python .github/skills/read-zzz-engine-stats/scripts/refresh_weapon_presets.py
python .github/skills/read-zzz-drive-disc/scripts/refresh_disc_presets.py
python tools/link_disc_effects.py                 # 重建驱动盘的 effect2 / effect2Note
python tools/sync_manifest.py                   # 数据集登记表（count / sha256）
python tools/bundle_worker_data.py              # Worker 产物（生成物，gitignored）
```

### 阶段 C · 抓取与图片

```powershell
python .github/skills/agent-strategy/scripts/scrape_agent_guide.py --entry-page-id <id> --slug <slug> --output strategy/<slug>/data/<slug>.json
python tools/fetch_agent_backgrounds.py         # Gachabase 立绘 → background.webp
python tools/fetch_agent_films.py               # Nanoka 角色框头像 → film.webp
```

**技能文本口径（R1–R6）见 [`_shared/deploy-checklist.md`](../_shared/deploy-checklist.md)**：
核心技正文取成长表最后一级（F）的「详情」span = **满级**文本；「额外能力/额外被动」单独成一条 move；
成品不得出现「此处数据为初始数据」。

### 阶段 D · 编辑内容

脚本从**同职业**参考页克隆**结构**，把具体值全部置为 `TODO` 并打印待确认清单
（清单来源见 [`_shared/editorial-fields.md`](../_shared/editorial-fields.md)）。
逐项与用户确认后写入真实值。

### 阶段 E · 面板与注册

```powershell
python .github/skills/agent-strategy/scripts/calc_graduation_panel.py --strategy strategy/<slug>/data/<slug>.strategy.json
python tools/gen_strategy_guides.py
python tools/bundle_worker_data.py
```

### 阶段 F · 校验与交付

```powershell
python tools/normalize_strategy.py --check
python tools/seed_main_stat_notes.py --check
python tools/gen_strategy_guides.py --check
python .github/skills/agent-strategy/scripts/calc_graduation_panel.py --check-all
python .github/skills/agent-strategy/scripts/calc_graduation_panel.py --check  # 参考实例实算
python tools/sync_manifest.py --check           # 数据集登记表
python tools/sync_presets.py --options --check  # 配装规则表
python tools/bundle_worker_data.py --check
python tools/agent_audit.py --all
python tools/check_ui_contrast.py --check       # 对比度闸门
python tools/check_ui_scale.py --check          # 尺度闸门（字号 / 字重 / 间距 / 阴影）
uv run pytest
cd frontend; npm run test; npm run typecheck; npm run build
```

### 阶段 G · 同步收尾（必做）

**改了内容就必须同步对应的文档/代码，否则项目内容不统一。**
完整对照表见 [`_shared/deploy-checklist.md`](../_shared/deploy-checklist.md)「同步收尾」一节，摘要：

| 改了什么 | 必须同步 |
| --- | --- |
| 新增 / 删除代理人 | `data/catalog/agent-index.json` → 攻略目录与两份 JSON → `strategyGuides.ts` → `docs/overview/project-overview.md`「当前规模」表（代理人数 / 命名映射 / 攻略页数）→ `docs/design/data-schema.md` → `docs/overview/requirements.md` F3 |
| 面板 / 核心 / 音擎 / 驱动盘预设变了 | `data/catalog/*.json` → `link_disc_effects.py`（驱动盘的 `effect2` 派生字段）→ `sync_manifest.py`（数据集登记表）→ `bundle_worker_data.py`（Worker 产物） |
| 攻略编辑内容变了 | `strategyGuides.ts`（`gen_strategy_guides.py`）→ `calc_graduation_panel.py --check-all` |
| 新增 / 替换图片 | 必须是 webp；`/images/…` 引用与磁盘文件名逐字一致 |
| 新增 / 改名脚本 | `tools/README.md` → `docs/guides/development.md` → `docs/README.md` 索引 |
| 改了 JSON 字段契约 | `strategy/README.md` → `docs/design/data-schema.md` → `frontend/src/types/` |
| 改了 skill / 流程 / 规则 | `.github/skills/_shared/`（唯一事实源）→ 相关 `SKILL.md` → `docs/README.md` 技能表 |
| 任何数量类事实变了 | `docs/overview/project-overview.md`「当前规模」表（唯一事实源） |
| changelog 变长了 | `python tools/archive_changelog.py`——`docs/changelog.md` 只留最近 12 条，更早的按月归档到 `docs/changelog/<YYYY-MM>-archive.md` |
| 文档改了位置 / 分类 | 修正所有指向它的链接（相对链接 + 反引号里的仓库相对路径），`python tools/check_docs.py` 会报断链 |

```powershell
python tools/gen_strategy_guides.py        # 攻略页登记表
python tools/sync_manifest.py              # 数据集登记表
python tools/bundle_worker_data.py         # Worker 产物
python tools/check_docs.py                 # 链接 / 反引号路径 / 规模数字 一致性
python tools/agent_audit.py --all          # 攻略页体检
```

`tools/check_docs.py` 会核对文档里的**数量类事实**（代理人数、音擎数、驱动盘数、规则表条目、
命名映射、攻略页数、图片数与格式、前后端测试数）是否与数据源一致——新增代理人或换了图片/测试后
忘了改文档，它会直接报出来。

## 参考页（按职业分组）

> **硬规则**：同职业页面只借鉴**结构与思路**（字段组织、面板行选择、队伍写法、文字攻略分节）。
> 数值、配装、口径、队伍组合必须按**该代理人的实际机制**逐条推导并与用户确认，**不得照抄**。
> 典型差异源：异常掌控机制、资源形态（能量/层数/标记）、破防与减抗的替代关系、
> 副 C 还是主 C、面板模式不同则毕业面板的行完全不同。

| 职业 | 现有攻略页（可借鉴结构） | 该职业典型差异点（必须逐条核实） |
| --- | --- | --- |
| 强攻（17） | `ye-shunguang` `seed` `pyrois` `zhu-yuan` `hugo` `nekomata` `harumasa` `corin` `ellen` `evelyn` `billy` `anton` `orphie-magus` `sigrid` `soldier-11` `soldier-0-anby` `cissia` | 资源获取与爆发窗口；专武/二件套给暴伤还是攻速；普攻系加成是否值得 4 件套；击破 vs 感电/贯穿分工 |
| 异常（13） | `miyabi` `aria` `alice` `grace` `burnice` `phoenix` `jane` `vivian` `remielle` `velina` `yanagi` `piper` `promeia` | 异常精通/掌控堆法与属性色；「异常精通 > … > 异常掌控」优先级；队伍是否吃异常位；直伤/异常伤害占比 |
| 击破（12） | `roxy` `anby` `nangong-yu` `lycaon` `dialyn` `lighter` `koleda` `ju-fufu` `norma` `trigger` `pulchra` `qingyi` | 失衡值来源与是否带「增伤」行；辅助向 vs 爆发向击破；秒伤与转 CD 取舍 |
| 支援（8） | `astra-yao` `nicole` `lucia` `lucy` `sunna` `soukaku` `yuzuha` `rina` | 支援技循环与能量；是否带「支援触发」类增益；面板是否只作参考 |
| 防护（5） | `ben` `caesar` `pan-yinhu` `zhao` `seth` | 防御/减抗是否进面板；护盾/减伤类机制不进计算器时的取舍；站场与前排分工 |
| 命破（5） | `banyue` `manato` `yixuan` `yidhari` `starlight-billy` | 贯穿力与特殊能量累积行；HP 词条优先级；与击破队友联动 |
| 锋御（1） | `claret` | 锐暴伤害是固定 150% 内在属性不作输入；锐能自动累积替代能量回复；两套 4 件套分页写法 |

## 交付说明

结束时要给出：**改了哪些文件**、**数据来源**（WIKI 链接 / 抓取时间）、**已验证数值**、**仍待用户确认的项**。

## 共享规则

- [`_shared/naming.md`](../_shared/naming.md) —— slug 唯一性、属性/职业/评级 → 图标 slug、图片命名
- [`_shared/editorial-fields.md`](../_shared/editorial-fields.md) —— 信息采集矩阵（应该寻找的点 → 修改的文件）
- [`_shared/deploy-checklist.md`](../_shared/deploy-checklist.md) —— 阶段闸门、技能文本口径 R1–R6、已知坑
