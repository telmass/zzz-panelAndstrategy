# 部署流程、闸门与已知坑

## 六阶段流程

```
阶段 0  模式判定      slug 在 mapping 里？→ 新建模式 : 修正模式（先跑 agent_audit.py）
阶段 A  身份解析      中文名 → slug / entry_page_id / attribute / roleTag / grade / panelMode
阶段 B  数据层        mapping 补录 → agents → weapons → drive-discs → sync_manifest
阶段 C  抓取与图片    scrape_agent_guide.py → fetch_agent_backgrounds.py → fetch_agent_films.py
阶段 D  编辑内容      骨架克隆（同职业参考页的结构，值置占位）→ 逐项与用户确认 → 写入
阶段 E  面板与注册    calc_graduation_panel.py → gen_strategy_guides.py → bundle_worker_data
阶段 F  校验与交付    闸门清单全跑 → agent_audit.py 归零 → 输出「改了哪些文件 + 来源 + 待确认项」
阶段 G  同步收尾      按下面的表同步文档/代码 → check_docs 复核（见「同步收尾」一节）
```

阶段 B/C/E 是机械环节，`tools/agent_deploy.py` 可一键串联；阶段 D 必须人机确认；
阶段 G 是**必做**的收尾——改了内容不同步文档/代码，项目就会「内容不统一」。

## 同步收尾（阶段 G）：改了什么 → 必须同步哪里

| 改了什么 | 必须同步 |
| --- | --- |
| 新增 / 删除代理人 | `data/catalog/agent-index.json` → 攻略目录与两份 JSON → `frontend/src/constants/strategyGuides.ts`（`gen_strategy_guides.py`）→ `docs/overview/project-overview.md`「当前规模」表的**代理人预设 / 命名映射 / 攻略页目录** → `docs/design/data-schema.md` 的数据表 → `docs/overview/requirements.md` F3 |
| 抓取产物的面板 / 核心变了 | `data/catalog/agents.json` → `tools/sync_manifest.py`（数据集登记表）→ `tools/bundle_worker_data.py`（Worker 产物） |
| 音擎 / 驱动盘预设变了 | `data/catalog/weapons.json` → `tools/sync_manifest.py` → `tools/bundle_worker_data.py`（Worker 产物）；`data/catalog/drive-discs.json` → `tools/sync_manifest.py`（不进 Worker 产物） |
| 攻略编辑内容变了 | `frontend/src/constants/strategyGuides.ts`（`gen_strategy_guides.py`）→ `calc_graduation_panel.py --check-all`（面板形状） |
| 新增 / 替换图片 | 必须是 **webp**（`tools/images_to_webp.py` 批量转）；JSON 里的 `/images/…` 与磁盘文件名**逐字一致**（含大小写与扩展名） |
| 新增 / 改名工具脚本 | `tools/README.md`「脚本一览」→ `docs/guides/development.md` 的脚本段 → `docs/README.md` 的索引（若面向使用流程） |
| 改了攻略 JSON 的字段契约 | `strategy/README.md`（契约表）→ `docs/design/data-schema.md` → 前端类型 `frontend/src/types/` |
| 改了 skill / 流程 / 规则 | `.github/skills/_shared/`（共享规程的唯一事实源）→ 相关 `SKILL.md` → `docs/README.md` 技能表 → `strategy/README.md` 的新增流程 |
| 任何「数量类事实」变了 | `docs/overview/project-overview.md`「当前规模」表（**唯一事实源**，其它文档引用它，不要各写一份） |
| changelog 变长了 | `docs/changelog.md` 只保留最近 12 条，更早的按月归档到 `docs/changelog/<YYYY-MM>-archive.md`（`python tools/archive_changelog.py`） |
| 文档改了位置 / 分类 | 移动后修正**所有**指向它的链接（相对链接 + 反引号里的仓库相对路径），`python tools/check_docs.py` 会报断链 |
| 改了页面可见内容 | `docs/overview/requirements.md` 的手工验收抽样页 → `docs/changelog.md` 补条目 |

**复核命令**（阶段 G 必跑）：

```powershell
python tools/gen_strategy_guides.py        # 攻略页登记表
python tools/sync_manifest.py              # 数据集登记表（count / sha256）
python tools/bundle_worker_data.py         # Worker 产物
python tools/check_docs.py                 # 链接 / 反引号路径 / 规模数字 三项一致性
python tools/agent_audit.py --all          # 攻略页体检
```

`tools/check_docs.py` 会核对文档里的**数量类事实**（代理人数、音擎数、驱动盘数、规则表条目、
命名映射、攻略页数、图片数与格式、前后端测试数）是否与数据源一致——新增代理人或改了图片/测试后
忘记改文档，它会直接报出来。


## 每阶段命令

```powershell
# 阶段 B：预设
python .github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py
python .github/skills/read-zzz-engine-stats/scripts/refresh_weapon_presets.py
python .github/skills/read-zzz-drive-disc/scripts/refresh_disc_presets.py
python tools/sync_manifest.py                   # 数据集登记表（count / sha256）
python tools/bundle_worker_data.py              # Worker 产物（生成物，gitignored）

# 阶段 C：抓取与图片
python .github/skills/agent-strategy/scripts/scrape_agent_guide.py --entry-page-id <id> --slug <slug> --output strategy/<slug>/data/<slug>.json
python tools/fetch_agent_backgrounds.py         # Gachabase 立绘 → background.webp
python tools/fetch_agent_films.py               # Nanoka 角色框头像 → film.webp

# 阶段 E：面板与注册
python .github/skills/agent-strategy/scripts/calc_graduation_panel.py --strategy strategy/<slug>/data/<slug>.strategy.json
python tools/gen_strategy_guides.py

# 阶段 F：闸门
python tools/normalize_strategy.py --check
python tools/seed_main_stat_notes.py --check
python tools/gen_strategy_guides.py --check
python .github/skills/agent-strategy/scripts/calc_graduation_panel.py --check-all
python .github/skills/agent-strategy/scripts/calc_graduation_panel.py --check  # 参考实例实算
python tools/sync_manifest.py --check           # 数据集登记表
python tools/sync_presets.py --options --check  # 配装规则表
python tools/bundle_worker_data.py --check
python tools/agent_audit.py --all
uv run pytest
cd frontend; npm run test; npm run typecheck; npm run build
```

## 技能文本抓取口径（R1–R6）

WIKI 的招式描述（`desc`）展示的是**初始数值**；满级数值在成长表每一 rank 行内的
`<span data-type="详情" data-name="…">` 上（取最后一段 = 满级）。

| 规则 | 内容 |
| --- | --- |
| **R1 文本来源** | 核心技正文取成长表**最后一级（F）**的「详情」span = 满级正文；取不到才降级到 `desc` + 成长增量改写 |
| **R2 额外能力** | `desc` 里以「额外能力：」「额外被动：」开头的段**切出来单独成一条 move**（无 `growth`），排在核心技之后；详情 span 不含该段，从 `desc` 补 |
| **R3 标题归一** | 正文首行「核心被动：XXX」/「核心技：XXX」→ `title` 统一为「核心技：XXX」，首行从正文移除 |
| **R4 标记清理** | 成品不得出现「此处数据为初始数据」。核心技详情本身就是满级，标记按满级口径翻正；非核心技用成长表最后一级同名行改写数值（改不到就**保留原标记**，不产出无依据的数字），并在审计报告里列出 |
| **R5 六类统一** | 普通攻击 / 闪避 / 支援技 / 特殊技 / 连携技 / 终结技同样按 R1 取文本 |
| **R6 渲染零改动** | `renderStrategy.ts` 的 `skillCatHtml` 对 `moves.length > 1` 自动切招式二级页，额外能力自然成为第二个 tab |

抓取产物里「核心技 2 条」= ①核心技（含 A–F 成长表）②额外能力（无成长表）——与 `strategy/roxy/` 现状一致。

## 已知坑

| 坑 | 说明 / 规避 |
| --- | --- |
| 变体条目 | 成长表里只有标题、无描述的条目是页面内跳转锚点，必须跳过（`_skippedVariants` 计数） |
| 详情 span 只在核心技 | 非核心技的成长表只有数值行、没有「详情」span，满级值需从最后一级同名行改写 |
| 额外能力段没有成长表 | 额外能力里的「初始数据」句取不到满级值 → 保留原标记并进审计报告 |
| WIKI 临时清空字段 | 菲欧妮 2026-10 起 `addition_text`（称号）为空，「坎卜斯黑枝」改成阵营名；抓取器会保留旧产物里的称号，不抹掉已有信息 |
| 换装记录串图 | Nanoka / Gachabase 的换装记录其立绘哈希会串到别的代理人身上 → 按 id 取本体（最小 id 为本体），并用内容哈希去重报告复核 |
| 资产编号前导零 | `IconRolePiece01` / `09` / `05` 保留前导零；`IconInterKnotRole0069` 要去掉前导零得 `69` |
| 接口瞬时失败 | WIKI 接口批量抓取会偶发失败（403/超时）；抓取脚本要重试，失败页必须重抓而不是沿用旧文件 |
| 改 `data/catalog/agents.json` 后忘了同步 | `sync_manifest.py` 刷登记表的 `count` / `sha256`（漏了 CI 直接红）；`bundle_worker_data.py` 是 Cloudflare 部署硬闸（`pywrangler` 只传 .py，漏了线上仍是旧数据） |
| 回滚别用 git | 工作区常有未提交的大改动（如全量 webp 迁移），`git checkout` 会一起撤掉；备份放临时目录 |
| 登记表不能手改 | `frontend/src/constants/strategyGuides.ts` 由 `tools/gen_strategy_guides.py` 生成 |
| 夹具不能手改 | `frontend/tests/fixtures/legacy-calculator/` 是三方对拍的参照实现，**已冻结为快照**（不再生成）。改数据不会改它；`backend/tests/test_legacy_fixture_snapshot.py` 断言它与当前数据集**语义等值** |

## 参考页按职业分组

见 `get-agent-strategy/SKILL.md` 的「参考页表」——**按职业分组**，同职业只借鉴结构，机制差异必须逐条核实。
