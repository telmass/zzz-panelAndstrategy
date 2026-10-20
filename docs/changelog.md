# 变更记录

记录影响使用方式或正确性的变更。纯内部重构不逐条记录，见
[git 历史](https://github.com)。

版本号见 `pyproject.toml` 与 `frontend/package.json`，当前均为 `0.1.0`。

## 2026-10-19 · 「保存攻略」改为 JSON 驱动的攻略缩略图

| 变更 | 说明 |
| --- | --- |
| 保存攻略 | 不再截取 hero + 攻略区块，改为按 `strategy/<slug>/data/*.json` 生成 1360px 白底攻略卡片，导出 PNG |
| 卡片内容 | 左侧使用攻略 `background` 立绘；右侧六条分支：技能加点 / 命座（01–06 关键命座高亮）/ 武器 / 驱动盘 / 队伍 / 毕业面板（满配 + 非满配） |
| 可读性 | 正文、标签与连接线统一改为深色；技能、武器、驱动盘、队伍等条目使用白色不透明单元背景，避免透出立绘 |
| 词条展示 | 毕业面板按「大词条 + 小词条」展示：计算仍用完整 54 条实算，展示改成如洛茜 `47+7 词条`、莱特 `47+7`、克拉蕾 `37+17`、叶瞬光 `45+9`；小词条（小攻击/小防御/小生命、穿透值、无效词条）只计数不展开 |
| 驱动盘卡片 | 导出图的驱动盘推荐改为「配装行 + 4/5/6 号位主词条卡片」，每格同时展示首选与备选，无备选时自动隐藏 |
| 样式隔离 | 导出卡片增加 `strategy-card--export` 修饰类，覆盖启动页代理人卡片同名的 `.strategy-card` / `.strategy-card__tachie` 规则，避免立绘绝对定位后铺满整张导出图 |
| 保存一图流 | 保持原有整页截图逻辑不变 |
| 测试 | 新增 `tests/strategy-card.spec.ts` 与 `tests/substats.spec.ts`，覆盖卡片字段映射、词条 47+7 拆分与登记表内全部代理人 |

验证：`npm run typecheck`、`npm test`（127 passed）、`npm run build` 通过；Chrome + html2canvas 实测复核洛茜（含驱动盘主词条备选）与叶瞬光卡片版式。

## 2026-10-18 · 新增凯撒·金攻略页 + 全项目修复计划（Phase 1 P0）

| 变更 | 说明 |
| --- | --- |
| 新代理人 | 新增 `strategy/caesar/`：物理 / 防护 / S 级，entry_page_id 801；抓取产物含基础面板 10 项、技能 15 招、影画 6 层 |
| 编辑内容 | 加点链、音擎三档、驱动盘、队伍"凯爱耀"、出招表与注意事项均按需求方确认写入 |
| 配装口径 | 专武奔袭獠牙 + 原始朋克 4 件套 + 震星迪斯科 2 件套；4 号位防御、5 号位生命、6 号位冲击力 |
| 毕业面板 | 计算器实算：冲击力 182.0 / 生命值 20859.4 / 防御力 1900.6 / 攻击力 2167.2 |
| 登记 | `strategyGuides.ts` 重新生成，登记 60 名代理人；攻略图片增至 183 张、总图片 398 张 |
| P0 修复 | 补齐 5 名代理人缺失的 profile.icons；生成器增加属性/职业/评级图标兜底映射；修正 trigger 队伍成员错误 ID（ep-2074→ep-1191）；移除 burnice/yanagi 占位音擎；补 zhao 驱动盘名称；修正 claret 音擎名与预设一致 |
| 新增守卫 | `calc_graduation_panel.py --check-all` 结构化校验全部 60 个攻略文件的 graduationPanel（build/totals 形状）；已加入 CI |
| 修复计划 | 新增 `docs/repair-plan.md`（三阶段修复计划，含 P0/P1/P2 共 36 项发现） |

验证：`pytest` 310 passed；`npm run typecheck` / `npm run test` 118 passed；`normalize_strategy.py --check`、`gen_strategy_guides.py --check`、`seed_main_stat_notes.py --check`、`calc_graduation_panel.py --check-all` 均通过。`calc_graduation_panel.py --check`（单文件实算比对）仍需按代理人传完整参数方可复现，结构化 `--check-all` 已覆盖全部文件。

## 2026-10-18 · 音擎/驱动盘密度重构与主词条备注列

| 变更 | 说明 |
| --- | --- |
| 音擎两列 | `.weapon-card` 改为「左侧档位+音擎列表 / 右侧说明」两列；单把音擎不再只占卡片左侧、说明不再另起一行；≤720px 回落单列 |
| 驱动盘 tabs | 多方案（`driveBuilds.length > 1`）改用 ARIA tabs，仅显示当前方案；移动端方案名换行，避免隐藏第二个方案 |
| 驱动盘三段 | 上段 4 件套（左）/ 2 件套（右）分栏，中段主词条表，下段副词条优先级；主词条表恢复全宽，保证四列（部位/首选/备选/备注）有足够宽度 |
| 套装摘要 | 4 件套 / 2 件套由分组标题区分，行内只保留图标/名称、二/四件套效果与适用；去除行内重复的“4 件套 / 2 件套”小标题 |
| 导航栏姓名 | 攻略详情页左侧导航（含移动端目录条）改用 `agent-name-mapping.json` 的 `cn_short` 中文缩写；hero 与浏览器标题仍显示全名 |
| 备注列 | `mainStats[].note` 为手动备注；新增 `tools/seed_main_stat_notes.py` 为 59 个 strategy JSON 的 180 条主词条补 `""` 占位；空值显示 `—`，支持 `\n` 换行 |
| 测试 | `strategy-view.spec.ts` 增至 10 项；后端新增 mainStats note 守护；前端 118、后端 307 |

验证：`npm run typecheck`、`npm run test`（118 passed）、`npm run build` 通过；`pytest` 307 passed；截图检查 390/1024/1440。

## 2026-10-18 · 攻略详情页 UI/UX 优化

| 变更 | 说明 |
| --- | --- |
| 设计令牌 | 新增 12/13/14/15/17/20/clamp 字号阶梯、行高、字距、8px 间距与 focus ring；弱文本色改为满足 AA 的 `#5f6673` |
| 对比度 | 属性色牌/编号/侧栏徽标按亮度自动选择黑/白前景；属性/职业术语与六类技能文字改用深色变体；影画面纱提高到 84–96% |
| 视觉层级 | section 头部改白底 + 属性色左边条；移除内层卡片阴影，减少“盒中盒”；攻略块恢复单列阅读顺序，内部音擎/队伍/影画使用自适应网格 |
| 响应式 | 基础面板/队伍/影画/音擎改 auto-fit；修复 1024 宽度侧栏被全局 `grid-column` 拉满导致内容错位；移动端返回按钮改文档流内，目录 actions 随目录展开 |
| 溢出/对齐 | 主词条表加横向滚动容器；移除音擎/驱动盘/队伍名称的 `nowrap`；补 `min-width:0` 与 `overflow-wrap`；修复全局 `.weapon-card { display:flex }` 导致的攻略音擎卡错排 |
| 无障碍 | 技能 tab 补 `role=tab` / `aria-selected` / `aria-controls` / 方向键；scroll spy 补 `aria-current`；加载/错误态补 `role=status`/`alert`；新增 skip link、main landmark、路由切换焦点管理；清理 iframe 死样式 |
| 测试 | `strategy-view.spec.ts` 增至 7 项；前端测试总数 115 |

验证：`npm run typecheck`、`npm run test`（115 passed）、`npm run build` 通过；截图检查 390 / 768 / 1024 / 1440。

## 2026-10-18 · 攻略页迁入 Vue、登记表自动生成

| 变更 | 说明 |
| --- | --- |
| 攻略页架构 | `strategy/<slug>/` 只保留两份 JSON；新增 `frontend/src/strategy/renderStrategy.ts` 为唯一渲染器，`strategy.css` 为唯一一份样式（收窄在 `.strategy-detail`） |
| 去 iframe | `StrategyView.vue` 直接拉取 `/strategy/<slug>/data/*.json` 并挂载渲染器；删除 59 个目录的 `index.html` / `app.js` / `styles.css`（共 177 个文件） |
| Vite 插件 | `strategyPagesPlugin` → `strategyDataPlugin`，只服务 / 拷贝两份 JSON 到 `dist/strategy/<slug>/data/` |
| 登记表生成 | 新增 `tools/gen_strategy_guides.py`，从 mapping + 攻略数据生成 `strategyGuides.ts`；`--check` 进入漂移闸 |
| 渲染回归 | 新增 `strategy-view.spec.ts`，逐个渲染登记表内全部 59 名代理人；测试总数 306（后端）/ 112（前端） |
| 背景图 | agent-background 改为在 strategy JSON 顶层写 `background`，由共享渲染器读取；`.page-bg` 用负 z-index + `.app` stacking context 固定在内容下方 |
| CI | 新增 `.github/workflows/ci.yml`：六条数据漂移闸 + pytest + Vitest + typecheck + build |

验证：`pytest` 306 passed；`npm run test` 112 passed；`npm run typecheck`、`npm run build` 通过；
`normalize_strategy.py --check`、`gen_strategy_guides.py --check` 与三条预设闸均通过。

## 2026-10-18 · 攻略数据归一、UTF-8 修复与图标命名统一

| 变更 | 说明 |
| --- | --- |
| 数据命名归一 | 29 个攻略目录的数据文件改为 `<slug>.json` / `<slug>.strategy.json`；`app.js`、JSON、`strategyGuides.ts` 引用同步 |
| 清理遗留目录 | 删除重复的 `strategy/ye-shun-guang/`，规范目录为 `strategy/ye-shunguang/` |
| 修复坏 JSON | 21 份非 UTF-8 的抓取产物按 `entryPageId` 从官方 Wiki 重新抓取，补齐本地图标 / 立绘 / 影画路径 |
| 图片命名统一 | 属性 / 职业图标统一为小写 ASCII slug（`honed-edge.png`、`attack.png` 等），数据、Skill 与文档同步 |
| 回归守卫 | 新增目录 / 数据文件名 / UTF-8 / 图片引用 / 登记表一致性测试；音擎计数改为从数据文件动态读取 |
| 新增工具 | `tools/normalize_strategy.py`：`--check`、`--rescrape-invalid`、`--remove-legacy` |

验证：`pytest` 307 passed；`npm run test` 108 passed；`npm run typecheck`、`npm run build` 通过。

## 2026-10-18 · 文档集成与结构审查

| 变更 | 说明 |
| --- | --- |
| 新增集成总览 | [project-overview.md](project-overview.md)：项目定位、当前规模、架构、数据流、目录地图、常用命令、文档地图 |
| 新增结构审查 | [structure-review.md](structure-review.md)：记录攻略数据命名 / UTF-8 / 模板重复 / 文档漂移等问题，附证据、影响、解决方案与修复顺序 |
| 重写文档索引 | [README.md](README.md) 改为「总览 → 专题」索引，并写明一处事实只写一次的维护规则 |
| 校准当前事实 | 音擎预设 100 → 101；后端测试 136 → 244（当时 184 通过 / 60 失败，随后修复至 306/306）；图片 213 → 395；攻略页 2 → 59 个目录 / 59 条登记；新增 `data/agent-name-mapping.json` 说明 |
| 规范路径 | 当前状态描述中的 `ye-shun-guang` / `ban-yue` 统一为 `ye-shunguang` / `banyue`；历史条目保持原样 |
| 同步 Skill 文档 | `agent-strategy` / `fix-agent` 的参考实例路径改为规范 slug，并标注遗留数据文件迁移中 |

## 2026-10-16 · 猫宫 又奈攻略页（`strategy/mao-you/`）

按 agent-strategy skill 流程产出代理人攻略；物理属性强攻 S 级（六分街）：

| 变更 | 说明 |
| --- | --- |
| 新增 `strategy/mao-you/` | 猫宫 又奈（`ep-378`，entry_page_id 378，物理 / 强攻 / S 级，六分街）：抓取产物 + 编辑攻略 + 页面模板 |
| 登记表 | `constants/strategyGuides.ts` 追加一条，`/strategy` 选择页出现新卡 |
| 加点链 | 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心暴击率+14.4%、基础攻击力+75） |
| 音擎定位 | 首选 **残心青囊** (`ep-991`，S 713 副词条见预设表）；下位/备选按音擎页补全 |
| 驱动盘 | 4 件套 **獠牙重金属** (`ep-104`，`--set4-effect dmg_10`）+ 2 件套 **啄木鸟电音** (`ep-232`，`--set2-effect cr_8`)；主词条 4 号位cd_48/ 5 号位dmg_30/ 6 号位atk_pct_30；副词条优先级：按职业口径 |
| 满配毕业面板 | `--rows atk,cr,cd,dmg`（标准模式，计算器实算）: 攻击力 **3,232.2** / 暴击率 **58.6%** / 爆伤 **222.8%** / 增伤 **40%** |
| 非满配毕业面板 | 同配置、30 词条（30 条：暴击率 ×6、爆伤 ×13、攻击力% ×8、小攻击 ×3）：攻击力 **2,872.4** / 暴击率 **41.8%** / 爆伤 **208.4%** / 增伤 **40%** |
| Teams | 猫又 `ep-378` 獠牙重金属 / 比利 `ep-371` 獠牙重金属 / 耀嘉音 `ep-1109` 静听嘉音） |

未建模机制：物理强攻速切主 C，[强化霰弹]/[终结技：终幕演出]短时爆发机制写进文字攻略。

验证：抓取摘要（物理/强攻/S、10 项基础面板、6 类招式、影画 6 层、背景 6 层）；两份 JSON 引用的 `/images/…` 全部存在；dev server 实测 URL 全部 200；`--check` 退出 0；后端/前端测试、typecheck、build 通过。

## 2026-10-16 · 「11号」攻略页（`strategy/shi-yi-hao/`）

按 agent-strategy skill 流程产出代理人攻略；火属性强攻 S 级（特务科）：

| 变更 | 说明 |
| --- | --- |
| 新增 `strategy/shi-yi-hao/` | 「11号」（`ep-73`，entry_page_id 73，火 / 强攻 / S 级，特务科）：抓取产物 + 编辑攻略 + 页面模板 |
| 登记表 | `constants/strategyGuides.ts` 追加一条，`/strategy` 选择页出现新卡 |
| 加点链 | 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心暴击率+14.4%、基础攻击力+75） |
| 音擎定位 | 首选 **十方锻星** (`ep-1503`，S 713 副词条见预设表）；下位/备选按音擎页补全 |
| 驱动盘 | 4 件套 **炎狱重金属** (`ep-192`，`--set4-effect dmg_10`）+ 2 件套 **啄木鸟电音** (`ep-232`，`--set2-effect cr_8`)；主词条 4 号位cd_48/ 5 号位dmg_30/ 6 号位atk_pct_30；副词条优先级：按职业口径 |
| 满配毕业面板 | `--rows atk,cr,cd,dmg`（标准模式，计算器实算）: 攻击力 **3,674.0** / 暴击率 **58.6%** / 爆伤 **174.8%** / 增伤 **40%** |
| 非满配毕业面板 | 同配置、30 词条（30 条：暴击率 ×6、爆伤 ×13、攻击力% ×8、小攻击 ×3）：攻击力 **3,318.8** / 暴击率 **41.8%** / 爆伤 **160.4%** / 增伤 **40%** |
| Teams | 11号火耀（1121号 `ep-73` 炎狱重金属 / 耀嘉音 `ep-1109` 静听嘉音 / 安东 `ep-147` 山大王+震星迪斯科） |

未建模机制：火强攻主 C，[点火]/[强化特殊技]燃烧机制写进文字攻略。

验证：抓取摘要（火/强攻/S、10 项基础面板、6 类招式、影画 6 层、背景 6 层）；两份 JSON 引用的 `/images/…` 全部存在；dev server 实测 URL 全部 200；`--check` 退出 0；后端/前端测试、typecheck、build 通过。

## 2026-10-16 · 珂蕾妲·贝洛伯格攻略页（`strategy/ke-lei-da/`）

按 agent-strategy skill 流程产出代理人攻略；火属性击破 S 级（犯罪搜查组）：

| 变更 | 说明 |
| --- | --- |
| 新增 `strategy/ke-lei-da/` | 珂蕾妲·贝洛伯格（`ep-318`，entry_page_id 318，火 / 击破 / S 级，犯罪搜查组）：抓取产物 + 编辑攻略 + 页面模板 |
| 登记表 | `constants/strategyGuides.ts` 追加一条，`/strategy` 选择页出现新卡 |
| 加点链 | 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心基础冲击力+18、基础攻击力+75） |
| 音擎定位 | 首选 **首席跟班** (`ep-2088`，S 713 副词条见预设表）；下位/备选按音擎页补全 |
| 驱动盘 | 4 件套 **山大王** (`ep-1346`，`--set4-effect none`显式不建模）+ 2 件套 **震星迪斯科** (`ep-152`，`--set2-effect impact_pct_6`)；主词条 4 号位cr_24/ 5 号位dmg_30/ 6 号位impact_pct_24；副词条优先级：按职业口径 |
| 满配毕业面板 | `--rows imp,cr,cd,atk`（标准模式，计算器实算）: 冲击力 **174.2** / 暴击率 **74.6%** / 爆伤 **160.4%** / 攻击力 **2,434.6** |
| 非满配毕业面板 | 同配置、30 词条（30 条：暴击率 ×6、爆伤 ×13、攻击力% ×8、穿透 ×3）：冲击力 **174.2** / 暴击率 **67.4%** / 爆伤 **112.4%** / 攻击力 **2,111.5** |
| Teams | 珂蕾妲 `ep-318` 山大王 / 耀嘉音 `ep-1109` 静听嘉音 / 零号·安比 `ep-1190` 如影相随） |

未建模机制：火击破后场辅助，失衡易伤机制写进文字攻略；失衡值+6% 二件套选项表无对应项，--set4-effect none 显式不建模。

验证：抓取摘要（火/击破/S、10 项基础面板、6 类招式、影画 6 层、背景 6 层）；两份 JSON 引用的 `/images/…` 全部存在；dev server 实测 URL 全部 200；`--check` 退出 0；后端/前端测试、typecheck、build 通过。

## 2026-10-16 · 格莉丝·霍华德攻略页（`strategy/ge-li-si/`）

按 agent-strategy skill 流程产出代理人攻略；电属性异常 S 级（特务科）：

| 变更 | 说明 |
| --- | --- |
| 新增 `strategy/ge-li-si/` | 格莉丝·霍华德（`ep-150`，entry_page_id 150，电 / 异常 / S 级，特务科）：抓取产物 + 编辑攻略 + 页面模板 |
| 登记表 | `constants/strategyGuides.ts` 追加一条，`/strategy` 选择页出现新卡 |
| 加点链 | 核心技 Lv.7 > 特殊技 Lv.12 = 普通攻击 Lv.12 = 连携技 Lv.12 = 支援技 Lv.12 > 闪避 Lv.11（核心异常掌控+36、基础攻击力+75） |
| 音擎定位 | 首选 **淬锋钳刺** (`ep-760`，S 713 副词条见预设表）；下位/备选按音擎页补全 |
| 驱动盘 | 4 件套 **獠牙重金属** (`ep-104`，`--set4-effect dmg_10`）+ 2 件套 **法厄同之歌** (`ep-1194`，`--set2-effect ac_pct_8`)；主词条 4 号位am_92/ 5 号位atk_pct_30/ 6 号位ac_pct_30；副词条优先级：按职业口径 |
| 满配毕业面板 | `--rows atk,am,ac`（标准模式，计算器实算）: 攻击力 **2,928.8** / 异常精通 **460** / 异常掌控 **208.4** |
| 非满配毕业面板 | 同配置、30 词条（30 条：异常精通 ×10、攻击力% ×8、小攻击 ×4、穿透 ×3、暴击率 ×2、爆伤 ×2、生命值% ×1）：攻击力 **2,760.5** / 异常精通 **388** / 异常掌控 **208.4** |
| Teams | 格莉丝 `ep-150` 獠牙重金属 / 耀嘉音 `ep-1109` 静听嘉音 / 零号·安比 `ep-1190` 如影相随） |

未建模机制：电异常主 C，异常积累与紊乱触发机制写进文字攻略。

验证：抓取摘要（电/异常/S、10 项基础面板、6 类招式、影画 6 层、背景 6 层）；两份 JSON 引用的 `/images/…` 全部存在；dev server 实测 URL 全部 200；`--check` 退出 0；后端/前端测试、typecheck、build 通过。

---

## 历史归档

更早的 2026-10 变更记录已归档到 [changelog/2026-10-archive.md](changelog/2026-10-archive.md)。
