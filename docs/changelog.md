# 变更记录

记录影响使用方式或正确性的变更。纯内部重构不逐条记录，见
[git 历史](https://github.com)。

版本号见 `pyproject.toml` 与 `frontend/package.json`，当前均为 `0.1.0`。

## 2026-10-20 · 导出卡片补上 2+2+2 的排版

| 变更 | 说明 |
| --- | --- |
| 卡片忽略 `set2b` / `set2c` | 导出卡片的驱动盘只读 `build.set2`，**另外两组 2 件套被整组丢掉**。2+2+2 的配装在卡片上只显示一组——信息是错的，不是排版丑 |
| 空着的「4 件套」栏 | 2+2+2 没有 4 件套组（`set4` 为 `null`），卡片却照样渲染一个空的「4 件套」栏，看着像漏了内容 |
| 修法 | 按**装备组**渲染：`set2` / `set2b` / `set2c` 各出一栏，编号 ①②③；**没有 4 件套组时整个「4 件套」栏不渲染** |
| 标签口径 | 单组沿用旧口径（写**效果名**：一组候选常常同效果，名字没用）；多组时组内效果可能一样（两组都是「能量回复 +20%」），靠**套装名**才分得清，于是编号 + 名字 |
| 像素实测 | 洛克茜的卡片现在三行分别是「4 山大王 + 2 回能」「4 静听嘉音 + 2 回能」「2 件套 ① 月光骑士颂 / ② 摇摆爵士 / ③ 啄木鸟电音」；整卡 1600×833，**无横向溢出**（scrollWidth == clientWidth） |
| 新守卫 | `frontend/tests/strategy-card.spec.ts` 增 3 例：4+2 仍是两栏、2+2+2 是三栏且无「4 件套」栏、**洛克茜真实数据**在卡片上就是三组 |

## 2026-10-20 · 导出卡片加宽 + 「复制攻略」直接进剪贴板

| 变更 | 说明 |
| --- | --- |
| 导出卡片加宽 | 「保存攻略」导出的卡片从 **1360px → 1600px**。1360px 时「主词条」表的「备选」列（"穿透率 +24% / 攻击力 +30%"）会折行 |
| 主词条单元加宽 | 三个单元从**等分 183px** 改为**按内容分配**（`flex: 1 1 auto`）：实测 **238 / 319 / 251px**——文案长的那个盒子拿更多宽度。「主词条」标签列 96px → **76px**，省下的横向空间让给单元 |
| 「保存一图流」→「复制攻略」 | 按钮改名，`data-action` 由 `save-full` 改为 `copy-guide` |
| **同一张图，两种交付** | 「保存攻略」= 下载；「复制攻略」= **写进系统剪贴板**，拿到图就能直接粘贴，不用先下载再上传。剪贴板不可用（无 `ClipboardItem` / 非安全上下文 / 写入被拒）时**退回下载**——图必须拿到手 |
| 顺带删掉的能力 | 整页截图（「一图流」的原本含义）随按钮改用途一并移除；`renderStrategy.ts` 里那份与 `strategyCard.ts` 重复的 html2canvas 加载与整页截图代码随之删除（导出只剩卡片一条路径） |
| 新守卫 | `frontend/tests/strategy-card.spec.ts` 增 4 例：卡片宽度 1600px、主词条单元 `flex: 1 1 auto`、标签列 76px、剪贴板可用时写进 PNG 且不触发下载 |
| 文档 | `docs/design/architecture.md`（两个按钮的边界改述）、`.github/skills/agent-strategy/SKILL.md`（「复制攻略」的行为） |

验证：`npm run test` 182 passed、`npm run typecheck`、`npm run build` 通过；**像素实测**——导出卡片 1360→1600px，主词条单元 183→238/319/251px，「4 号位 暴击率」「6 号位 能量回复」不再折行。

## 2026-10-20 · 洛克茜第三种配装（2+2+2）—— 把「不只是 4+2」变成真实用例

| 变更 | 说明 |
| --- | --- |
| 洛克茜第三种配装 | `strategy/roxy/` 新增「自身循环：2 月光 + 2 摇摆 + 2 啄木鸟」——**2+2+2**：没有 4 件套组，三组 2 件套各一套（`set4: null` + `set2` / `set2b` / `set2c`），主词条与副词条优先级**与另外两种配装一致** |
| 为什么选它当用例 | 它同时踩中三件事：**没有 4 件套组**、**三组**、**其中两组的 2 件套效果相同**（月光骑士颂与摇摆爵士都是「能量自动回复 +20%」）。第三条正是「组（都要装）」与「候选（二选一）」两个维度最容易混的地方 |
| 计算语义（实测） | 洛克茜 + 绯月银棺，主副词条不变，只换驱动盘：<br>• 4+2（山大王 + 摇摆）→ 能量回复 **2.16**、暴击率 **77%**<br>• 2+2+2（月光 + 摇摆 + 啄木鸟）→ 能量回复 **2.4**、暴击率 **85%**<br>• 差值：能量回复 **+0.24（= +20 个百分点）**、暴击率 **+8（正是啄木鸟电音）**<br>→ **两份同效果的 2 件套都生效**，且同一修正量的百分比是**相加**后一次性作用（`+20% + 20% = +40%`），**不是**叠乘（叠乘会得到 2.7648，与实际不符）——这与游戏一致 |
| 组序无关 | 三组谁先谁后结果完全相同（槽位是集合语义） |
| 渲染验证 | 像素确认：三个 tab 并列、第三个里**没有「4 件套」栏**、三组 2 件套编号 ①②③ 并排、方案说明与主/副词条表照常 |
| 新守卫 | `backend/tests/test_two_plus_two_plus_two.py`（4 项）钉住上面的计算语义；`frontend/tests/strategy-view.spec.ts` 用**洛克茜真实数据**断言三组与无 4 件套栏（不再只靠 mock） |
| 工具增强 | `frontend/tools/screenshot.mjs` 加 `--url`：可拍任意路径，不必改工具里的节点列表 |
| 一个纠正 | 我原以为同效果的两份 2 件套会**叠乘**（1.2×1.6×1.2×1.2 = 2.7648）——**想错了**。实测是**相加**（2.4）。百分比修正量按目标累加后再作用，这本来就是游戏的语义；早先写在计划里的「叠加」措辞不准确 |

## 2026-10-20 · 文档与 Skill 全量对齐

| 变更 | 说明 |
| --- | --- |
| 全量审计 | 按当前代码逐份核对 `README.md` + `docs/**` + `strategy/README.md` + `frontend/src|tests/README.md` + `backend/tests/README.md` + `tools/README.md` + `data/README.md` + `.github/skills/**`，修正 **40 余处**过时内容 |
| 数据路径 | `data/agent-presets.json` 等旧平铺路径 → `data/catalog/*.json` + `data/rules/calculator-rules.json`；路径的唯一真源是 `data/manifest.json` |
| 预设字段名 | `coreBonuses → core`、`perRankValue → perRank`、`additionalBaseStats → baseExtra`、`unmodeledBaseStats → baseUnmodeled`、`unavailableBaseStats`（**已删除**）、音擎 `baseKind/baseAttack/baseDefense → base: {kind, value}` |
| 图片格式 | 全部 `.png` → `.webp`（仓库里已无 PNG；`/images/…` URL 与磁盘文件名逐字一致） |
| 已移除的命令 | 6 份 SKILL.md 仍在教人跑 `sync_presets.py --to-legacy`（该模式已随「对拍夹具冻结」移除）——**照着跑会当场 argparse 报错**，导入流程第一步就断 |
| 缺失的闸门步骤 | 各 skill 的流程里**没有** `sync_manifest.py`（数据集登记表）与 `bundle_worker_data.py`（Worker 产物）——agent 照着做会留下 CI 红的仓库。已补进 `read-zzz-agent-stats` / `read-zzz-engine-stats` / `read-zzz-drive-disc` / `agent-strategy` / `fix-agent` / `get-agent-strategy` / `strategy/README.md` |
| 2+2+2 契约 | `agent-strategy/SKILL.md` 写着「不要把多个 4 件套并进一个带 set4 数组的方案，该模式已废弃」——**与现行契约相反**：`set4` 数组是 4 件套的**候选**列表（三选一，各带 `scene`），`set2`/`set2b`/`set2c` 才是并列的 2 件套组。已改写并补上 `--set2b-*` / `--set2c-*` 与「同套只算一次」的口径 |
| 驱动盘 `effect2` | `read-zzz-drive-disc/SKILL.md` 没说 `effect2` / `effect2Note` 是什么、也没提 `tools/link_disc_effects.py`——重抓一次就把它冲掉了。已补：30 套里 18 套可算、12 套是属性伤害 / 条件触发 |
| 新特性补记 | `?agent=` 直载、配装方案存取（localStorage / 导出导入 / `#build=` 链接）、驱动盘「按套装」填法、UI 闸门、CDP 截图工具、13 个后端测试模块 / 11 个前端 spec——原先一个都没进文档 |
| 数量类事实 | 60 → 61 目录、100 → 101 音擎、310 → 435 后端、128 → 177 前端、398 → 522 图片、161 → 162 预设、31 → 33 条漂移闸 |
| 死链 | `docs/design/ui-system.md` 指向 `.kilo/plans/…`（临时规划产物，已不存在）；`docs/changelog/2026-10-archive.md` 的 4 个链接指向文档重组前的位置 |
| 结构描述 | 「Pinia 两个 store」→ 三个（`buildStore` 持久化）；「三个 Node 脚本」；「无字号令牌」→ 有 8 档；`constants/` 三个 → 六个；`router/` 5 条 → 6 条 |

验证：`python tools/check_docs.py` 通过（相对链接 + 反引号路径 + 规模数字全绿）；`python tools/check_ui_contrast.py --check` / `check_ui_scale.py --check` 通过；后端 435 passed、前端 177 passed。

## 2026-10-20 · 阶段 5：驱动盘套装接入计算器 + 配装方案存取

| 变更 | 说明 |
| --- | --- |
| 二件套「按套装」填法 | 模块 06 加**填法切换**：「按效果」（默认，行为与旧版完全一致）/「按套装」。按套装时每组一个套装选择器（30 套，按 2 件套效果分组排序），选中后自动把它的 2 件套效果写进该组，并显示套装图标 + 名称（4 件套效果文本悬停可见） |
| **计算口径不变** | 两种填法写的都是**效果 id**（`setEffects`），面板计算完全不受影响。按套装时额外记一份套装 id（`setDiscs`）用于显示与导出；手动改效果时清掉该组的套装记录 |
| 12 套不可算的套装 | 「按套装」里**仍可选**，但标注「不计入面板：属性伤害 / 条件触发」并说明原因。属性伤害要进面板得加一行，会**破坏三方对拍**（参照实现的行集固定、夹具已冻结）；条件触发不是固定面板值 |
| 静态读取 | 驱动盘数据走**构建期静态 import**（`@data/catalog/drive-discs.json`），与规则表同一模式。**不加** `GET /api/presets/discs`——为 30 条静态数据动 loader / schema / 校验 / 打包 / 接口五处不划算 |
| 配装方案存取 | 结果区加「保存方案 / 导出 / 导入 / 复制链接」。存本机 `localStorage`（键 `zzz.builds.v1`）、导出 `.json`、导入队友发来的 `.json`、链接把配装编码进 URL 片段（`#build=…`） |
| **全部本地** | 不落服务端——站点公开、无鉴权，没有可写的服务端数据面（C7）。链接里放的是**本地编码**的内容 |
| 方案不含基础面板 | 基础面板是代理人的**事实数据**（来自代理人预设），存进方案只会多一份可能过期的副本。载入方案时重新载入代理人预设，基础面板自然跟着代理人对 |
| 分享链接 | 计算器页挂载时读 `#build=…`，读不到就当没有——访客点开失效链接应看到正常页面而不是报错页。链接用**紧凑形状**（键名压到一个字母、空值省略） |
| **既有 bug：结果列底部够不到** | 像素验证发现：结果列是吸顶元素、但比视口高，页面滚到底时它的下缘仍在视口之外——「冲击力」「能量回复」两行和新增的方案操作**都点不着**。已给结果列加视口内高度上限 + 内部滚动 |
| 新守卫 | `frontend/tests/disc-picker.spec.ts`（7 例：两种填法、选套装写效果、不可算套装、模式切换、改效果清套装记录）；`frontend/tests/build-preset.spec.ts`（17 例：localStorage 往返、URL 编解码往返、导入的合法/非法路径、方案套用回面板、坏存档不让计算器崩） |
| 待办（保留） | **把每个代理人的计算参数机器可读地存进策略文件**——目前只有叶瞬光一个参考实例能实算复核。反解 build 块不可靠（主词条显示的是实际值、分隔符不统一、有括号备注），且参数尚未逐个核对过。**先核对参数，再上形状** |

验证：12 道闸门全绿；后端 `pytest` 435 passed、前端 `npm run test` 177 passed、`npm run typecheck`、`npm run build` 通过；**像素验证**——「按套装」模式的三个下拉、套装图标行、结果区底部的方案操作条，以及无 4 件套组时不渲染那一栏。

## 2026-10-20 · 驱动盘的 2+2+2 结构：攻略页契约 + 阶段 5 设计修订

| 变更 | 说明 |
| --- | --- |
| 2+2+2 结构 | **驱动盘不一定只有「4+2」。** 6 个槽位也可以是 2+2+2（三组 2 件套）。此前 65 个驱动盘方案全是 4+2，这种情况表达不了——只能把信息塞进备注 |
| 攻略页契约 | 新增 `driveBuilds[].set2b` / `set2c`——第 2/3 组 2 件套，形状与 `set2` 相同；`set4` 改为**可空**（2+2+2 没有 4 件套组，页面整栏不渲染而不是留「暂无数据」）。**「组」用平级字段而不是数组**——组内 `main` / `alt` 本身就是「多套同效果的候选」数组，用数组表达组会与之撞语义。契约写在 `strategy/README.md` |
| 三条轴不混 | **组**（`set2`/`set2b`/`set2c`，并列都要装）/ **候选**（组内 `main`/`alt`，二选一，各自可为同效果候选数组）/ **4 件套候选**（`set4` 数组 = 三选一，**不是**同时生效多个）。**一个代理人最多生效一个 4 件套**——4 件套组必然带来自己的 2 件套效果，4+4 与 4+2+2 都装不下（8 片 > 6 槽）。校验里加了「有 4 件套组时只能有一组 2 件套」这条物理约束 |
| 渲染器 | 多个 2 件套组编号 ①②③；无 4 件套组时不渲染那一栏；套装名查找（`findDiscIcon`）与毕业面板的套装名（多组时是数组）同步支持。`drive-spec__sets` 的列数改为 `auto-fit`，2 组 / 3 组 / 单组都自适应 |
| 毕业面板脚本 | `calc_graduation_panel.py` 引入**装备组**模型：4 件套组 + 最多三组 2 件套，按组序落进 `set0` / `set1` / `set2` 三个槽位。新增 `--set2b-id/-effect`、`--set2c-id/-effect`。参考实例（叶瞬光）的已发布面板**逐字不变** |
| 空行修复 | 毕业面板的 build 块里 `set4: null` 会渲染出一行**空的「4 件套」**——像素验证时发现的（读源码看不出来）。已改为跳过空值 |
| 计算器不用改 | 后端 `sets: (set0, set1, set2)` 三个槽位、`_apply_sets` 逐个累加，天然表达「最多三个 2 件套效果位」；计算器**只建模 2 件套效果**（4 件套效果多是条件触发，不建模），所以三种装法在计算上口径一致 |
| 阶段 5 数据前置 | `data/catalog/drive-discs.json` 增加 `effect2`（2 件套效果 → 规则表 `setOptions` 的 id）与 `effect2Note`。由 `tools/link_disc_effects.py` 建立、`frontend/tests/data-manifest.spec.ts` 守住 |
| **覆盖率：18/30** | 30 套里 **18 套可算、12 套算不出来**：8 套是**属性伤害**（面板没有「属性伤害」这一行——加一行会破坏三方对拍，参照实现的行集是固定的）、4 套是**条件触发**（不是固定面板值）。因此「按套装选」覆盖不了全部 30 套，这 12 套要标出来并说明「不计入面板」 |
| 阶段 5 设计修订 | 原方案「一个套装选择器 + 自动分配槽位」在 2+2+2 下语义不明（用户不知道自己的套装进了哪一组），改为**三个槽位各一个套装选择器**；读取方式从「后端 `GET /api/presets/discs`」改为**构建期静态 import**（`@data/catalog/drive-discs.json`，与规则表同一模式）——30 条静态数据不值当动 loader / schema / 校验 / 打包 / 接口五处 |
| 新守卫 | `backend/tests/test_strategy_data.py` 的 `test_drive_build_set_groups_are_well_formed`（`set4` 可空或为候选数组；`set2`/`set2b`/`set2c` 各是一个组对象，组数 ≤3；有 4 件套组时只能有一组 2 件套）；`frontend/tests/strategy-view.spec.ts` 的「驱动盘的 2+2+2 结构」4 个用例 |
| **6 件同套的口径** | 4 件套组与 2 件套组**是同一套**时，实际生效的是**一组 2 件套效果 + 一个 4 件套效果**——同一套的 2 件套效果不会因为多穿两件而叠加。`calc_graduation_panel.py` 现在会识别同套并把重复的 2 件套组**并掉**（不额外占槽位，并打一行提示） |
| 校验发现已有 8 例 | 新校验立刻抓到**已发布数据里就有 8 个代理人 × 2 个面板 = 16 例**同套（全是「4 件套摇摆爵士 + 2 件套摇摆爵士」）。它们的数值**恰好没错**——摇摆爵士的 2 件套效果是「能量回复 +20%」，而能量回复不在这些面板的展示行里。但这是运气：换一套影响攻击力/暴击伤害的套装，数值就会多算一次 |
| 守的是数值不是形状 | 精确判据：从规则表取该套的 `effect2` → 它的修正量 → 展示标签，断言那个标签**不在**面板的展示行里。另加 `backend/tests/test_graduation_panel_groups.py`（3 个用例）守住并组规则本身 |
| 不可算的组不占槽位 | 某套装的 2 件套效果不可算时（属性伤害 / 条件触发），那个组仍记在毕业面板的套装名里，但**不占槽位**——否则它会把后面的组挤掉 |

验证：12 道闸门全绿；后端 `pytest` 431 passed、前端 `npm run test` 153 passed、`npm run typecheck`、`npm run build` 通过；**像素验证**——把叶瞬光页临时改成 2+2+2 截图确认三栏并排、无 4 件套栏、毕业面板套装名带图标逐个列出（用完已还原）。

## 2026-10-20 · Skill 导入链路审计：文档漂移 + 毕业面板实算崩溃

| 变更 | 说明 |
| --- | --- |
| 导入链路审计 | 审计「用 skill 导入新代理人 / 音擎 / 驱动盘套装」的完整链路，发现**链路是断的**，修了 11 处 |
| Skill 文档漂移 | 6 个 SKILL.md 仍让人跑 `sync_presets.py --to-legacy`——该模式已随「对拍夹具冻结」移除，argparse 报「unrecognized arguments」，**导入流程当场断掉**。已全部改为新流程（`sync_manifest.py` + `bundle_worker_data.py`） |
| 缺一步闸门 | 新的 `sync_manifest.py` 漂移闸**没进任何 skill 流程**：抓完数据不刷新登记表，`sync_manifest.py --check` 必红、CI 必红。已补进 `_shared/deploy-checklist.md` 与三个抓取 skill |
| 毕业面板算不出来 | `calc_graduation_panel.py` 读 v1 音擎字段（`weapon["baseAttack"]`），预设改成 v2 后直接 **KeyError**——毕业面板**根本算不出来**。已改为读 `base: {kind, value}` |
| 默认配装与已发布面板脱节 | 脚本默认副词条分配（cr13/cd21/atk_pct20）与 `strategy/ye-shunguang/` 里已发布的（cr13/cd16/atk_pct16/atk_flat5/pen_val4）不同；默认也没算**非满配面板**，而攻略 JSON 里存着两份面板 → `--check` 永远报漂移。已对齐 |
| 文案生成用错名字 | 副词条文案自动生成时用的是**选项 id**（`暴击率×13`），已发布的面板用的是**展示名**（`暴击率 ×13`，满配还带「满配」二字）。已按展示名生成 |
| `--help` 崩溃 | argparse 会对 help 串做 `%`-格式化，插值进来的「+48%」让 `calc_graduation_panel.py --help` 直接抛 ValueError。已加转义 |
| 工具链解码炸了 | 4 处 `subprocess.run(..., encoding="utf-8")` 没带 `errors="replace"`：Windows 上子进程的管道输出是 GBK，读取线程被打死、输出截断。已修（`agent_audit` / `agent_deploy` / `check_docs`） |
| 工具输出不确定 | 工具脚本的**管道输出**改为固定 UTF-8（用 `isatty()` 区分管道与控制台——控制台保持系统代码页，否则用户在自己终端里会看到乱码） |
| 用例数核对静默失效 | `check_docs.py` 用**系统 python** 收集后端用例数，而系统 python 里没有 pytest → 收集失败 → 返回 None → **这项事实悄悄不再被核对**（文档写着 389 也不报）。已改为用装了 pytest 的解释器，收集失败会明确告警 |
| 编排工具输出旧字段 | `agent_deploy.py` 的待确认清单里是 v1 字段名（`core` / `baseAtk` / `fixedSubstat`），阶段 G 里的文档路径也是重组前的旧路径。已改 |
| 共享规程同样落后 | `_shared/editorial-fields.md` 也是 v1 字段名。已改 |
| **新闸门** · Skill 指令漂移 | 新增 `backend/tests/test_skill_instructions.py`（37 项）：把 SKILL.md 里的命令当作**可执行契约**——脚本必须存在、命令必须**真的能跑**（把参数换成 `--help` 实际执行一遍，抓「参数不再被接受」）、数据路径必须与登记表一致、抓取脚本的 `OUTPUT` 必须指向登记项 |
| **新闸门** · 导入链路端到端 | 新增 `backend/tests/test_import_flow.py`（4 项）：在临时副本上模拟「导入一位新代理人 / 一件新音擎 / 一套新套装」，逐步断言——登记表漂移闸报红 → 刷新后转绿 → Worker 产物含新条目 → 后端能加载并通过语义校验 → 体检会先报「登记表过期」直到刷新 |
| **新闸门** · 参考实例实算 | `calc_graduation_panel.py --check`（参考实例**实算**比对）进 CI、`agent_audit.py`、开发指南与 skill 流程。此前 `--check-all` **只验形状不实算**——上面那一串毕业面板的 bug 全部因此隐形 |

验证：10 道数据 / UI 闸门 + 2 道毕业面板闸门全绿；后端 `pytest` 430 passed、前端 `npm run test` 146 passed、`npm run typecheck` 通过。

> 这次审计的结论：**重构数据管线时改了数据的形状与路径，但没有把「文档里写的命令」当成契约来守**——
> 于是 skill 流程在第一步就断了，而 CI 全绿。修完补了三道闸门，让这类漂移下次在 CI 就失败。

## 2026-10-20 · UI 像素验证：可复现的截图工具 + `?agent=` 直载

| 变更 | 说明 |
| --- | --- |
| 截图工具 | 新增 `frontend/tools/screenshot.mjs`：**CDP 驱动本机 Chrome** 拍图，**不新增任何依赖**（Node 22 自带全局 `WebSocket`）。按清单拍 30 张（5 路由 × 4 视口 × 状态），支持 `--viewport-only` / `--scroll` / `--click` |
| 为什么不用 `--headless --screenshot` | Chrome 在 Windows 上把 `--window-size` 的**宽度钳到最小 500px**（实测 375 → 500、560 → 544、1280 → 1264）。截出的图按请求宽度**裁切**，页面却按 500px 渲染——**图在骗人**：看上去「窄屏没折叠」，其实是根本没截到窄屏。CDP 的 `Emulation.setDeviceMetricsOverride` 能设任意宽度，`Page.captureScreenshot` 还能整页截 |
| 截图两处易翻车点 | ① **视口外的区块在整页截图里全透明**——攻略页的 `.reveal` 靠 IntersectionObserver 淡入，工具改为截图前逐段滚到底再回顶；② `--click` 可打开浮层（cascader 下拉），B12 才能验 |
| `?agent=` 直载 | 计算器页新增 `?agent=<slug 或预设 id>`：直接载入该代理人的基础面板与核心加成，并切到它的面板模式。一条链接即可复现某位代理人的整套面板——既是**分享**需求，也是验收清单「状态由 URL 决定」的前提。补 5 条前端用例 |
| 排版修正 | ① **副标题不再受 40em 行长上限约束**——题引是一到两句的引子，上限会把一句 52 字的话折成「40 字 + 12 字」的碎块；② **「数据来源：<链接>」放进 `white-space: nowrap` 的 span**，中文换行不再把它折成「数据」+「来源：…」 |
| favicon | 新增 `frontend/public/favicon.svg`（纯 SVG，无二进制资源）+ `<link rel="icon">`。此前每页控制台一条 404 |
| 根指引页令牌 | `index.html` 的内联令牌此前抄的是**旧值**（`--color-text-muted: #6b7280`、`--color-accent: #6366f1`、`--shadow-module`），现与 `tokens.css` 重新对齐，字体与间距改用阶梯令牌 |
| 验收记录 | `docs/design/ui-review-log.md` 记入**第 1 轮像素验证**：B 档 14 条中 13 条通过（B11 键盘焦点遍历待人工验），并记下本轮发现并已修的 7 个问题。`docs/design/ui-review-checklist.md` 同步更新为可执行版本（截图节点、命令、A8 新增「PNG 宽度 = 声明的视口宽度」） |

> **本轮之前，UI 结论全部来自读源码（code-only）**——仓库无 playwright / puppeteer，
> 也没有可用截图工具。第一次真正看图就抓出 7 个问题，其中 3 个是**只有看图才会暴露**的
> （截图视口被钳到 500px、视口外区块全透明、`?agent=` 不受支持导致三张截图长得一样）。

验证：后端 `pytest` 389 passed、前端 `npm run test` 146 passed、`npm run typecheck`、
`npm run build` 通过；`check_docs.py` / `check_ui_contrast.py --check` /
`check_ui_scale.py --check` 全过。

---

---

## 2026-10-20 · 计算器数据层重构 + UI 体系重建

| 变更 | 说明 |
| --- | --- |
| 数据集登记表 | 新增 `data/manifest.json`：数据集的**路径只在这里写一次**。后端 loader、Worker 打包脚本、Vite 配置、4 个 Skill 抓取脚本与 7 个开发工具都从它取路径，不再各记一份文件名（原先 15 处硬编码，跨 Python / TypeScript / Skill 三种语言）。新增 `tools/sync_manifest.py` 刷新 / 校验派生的 `count` 与 `sha256`，并检查 `data/` 下有无未登记的孤儿文件；`backend/tests/test_data_manifest.py` 守护 |
| 目录分域 | `data/` 下按域分两处：`catalog/`（游戏事实：代理人 / 音擎 / 驱动盘套装 / 命名映射）与 `rules/`（配装规则表）。`agent-presets.json → catalog/agents.json`、`weapon-presets.json → catalog/weapons.json`、`drive-disc-presets.json → catalog/drive-discs.json`、`agent-name-mapping.json → catalog/agent-index.json`、`options.json → rules/calculator-rules.json` |
| 冻结对拍夹具 | `frontend/tests/fixtures/legacy-calculator/data/*.js` 曾由 `sync_presets.py --to-legacy` 从 JSON 生成。参照实现的输入必须是**不动点**——它证明的是「旧实现算得对」，输入跟着当前数据漂移就说明不了这一点。因此夹具**冻结为快照**，`--to-legacy` / `--from-legacy` 模式移除（连带删掉约 200 行 JS 解析器）。守门换成 `backend/tests/test_legacy_fixture_snapshot.py`：断言夹具里用到的代理人与音擎与当前数据集在**语义上等值** |
| 代理人预设 v2 | `unavailableBaseStats` **删除**——「官方没提供哪几项」存了两份（`base` 缺键 + 一个数组），同一件事存两份就得靠校验器去证明它们没漂移。缺键本身就是那份事实，「哪几项缺合法」改由后端按规则判定（命破模式缺 `pr` / `er` 合法，其余模式十项齐全）。`coreBonuses → core`、`perRank → perRank`、`baseExtra → baseExtra`、`baseUnmodeled → baseUnmodeled`。`totalValue` / `unit` **保留**（虽然可由规则表推出）——接口响应与源 JSON 逐条等价是硬性质，冗余由校验器逐条核对 |
| 音擎预设 v2 | `baseKind` + `baseAttack` + `baseDefense` 三元组（恒有一个是 0，消歧靠 `baseKind`）合并为 `base: {kind, value}` 二元组 |
| 规则表 v2 | `discFixedStats[].target → to`（与其余六张表统一，前端不再做那层手工翻译）；每条选项新增 `name`（规范名，只含词条本身）与既有 `label`（展示串，含数值）分工；新增 `schemaVersion`。后端 `core/options.py` 与 `core/constants.py` 是唯一真源，`sync_presets.py --options` 单向生成 |
| 修正量键漂移闸 | 前端的 `ModifierKey` 原本是手写的 21 个键的联合类型，与 Python 侧无任何自动校验。改为「先有运行时数组、再由数组推类型」，并新增 `frontend/tests/data-manifest.spec.ts` 断言规则表里每个 `to` 都在清单内、反之无多余键。查出 `def_base` 是「有累加器但无选项」的保留键（`core/options.py` 的 `RESERVED_MODIFIER_KEYS` 记录了原因） |
| 攻略页去重 | 61 份 `strategy/<slug>/data/<slug>.json` 各存一份 `basePanel`，与预设数据重复。同一批数字已经漂移过（三名代理人的属性名口径在两处不一致）。攻略 JSON 不再带 `basePanel`，页面改由 `frontend/src/strategy/basePanel.ts` 从预设派生（含命破「贯穿力 / 闪能自动累积」与锋御「锐能自动累积」文案替换）。抓取脚本改为解析滑块后**与预设对照**并告警 |
| UI · 对比度闸门 | 新增 `tools/check_ui_contrast.py`：按 WCAG 2.1 相对亮度公式核对 37 组令牌配对（正文 ≥4.5:1，大字与控件边界 ≥3:1）。修前 12 组不合格：说明文字 **2.54:1**（用户在计算器页读不到任何一条操作说明）、控件边界 **1.47:1**、6 个序号徽标 **2.15–4.47:1**、5 组标签 **3.07–4.21:1**、错误提示 **3.76:1**。修后全部达标 |
| UI · 尺度闸门 | 新增 `tools/check_ui_scale.py`：字号只允许 `var(--text-*)`、字重只允许 400/600/700、间距必须落在刻度上、阴影只能用 `--elevation-*`。修前 386 项越界：**21 个散落字号**（`tokens.css` 此前**没有字号令牌**）、**6 个字重**（含非标准的 650 / 750）、刻度外的零散间距、**6 处手写阴影**。修后全部达标 |
| UI · 体系 | `tokens.css` 重建：8 档字号、3 档字重、3 档文字色（原 5 档，最浅的只有 2.54:1）、2 档描边（装饰性 vs 控件边界，后者 ≥3:1）、间距刻度、5 级 elevation。文字色合并后浅色面上次要文字从 2.54:1 提到 5.43:1（**说明文字明显变深，是有意的可读性取舍**） |
| UI · 色相分层 | 模块序号徽标（01–06）改为**中性深底白字**（17.7:1）——它承载「这是第几块」，靠数字本身不靠颜色；颜色留给左侧色条与标题标签。6 个色条对白底都 ≥3:1（太浅的琥珀 / 青绿 / 橙已取到能看清的深档） |
| UI · 层级 | 六大模块**外距 14px → 24px**（原先外距反而小于内距，六个模块糊成一片）、内距 18px → 20px；正文行长上限 40em（`.note` / `.card p` / `.subtitle` / 攻略页 `.para`）；结果区新增状态行（说明下面这列数字是谁的，未载入代理人时显示「下列为通用默认值」）；「重置」改为红色 + 二次确认（一次误点会丢掉整套配装）；窄屏新增 ≤560 / ≤480 / ≤420px 三个折叠点（三列栅格在 375px 下每格约 90px，「攻击力 30%」需约 105px，会被裁切） |
| UI · 深度 | 卡片（`.card` / `.page-hero` / `.guide-card`）去掉描边，靠阴影 + 底色浮起——描边、阴影、底色三件套同时用会把页面切成一堆小格子；表单控件的描边保留（那是控件边界）；数字输入框去掉浏览器自带的上下箭头并改用等宽数字；`.to-top` / `.sidebar__toggle` 补焦点态 |
| 文档 | 新增 `docs/design/ui-system.md`（视觉体系与两道闸门）、`docs/design/ui-review-checklist.md`（人工验收清单：A 机器 / B 二值 / C 锚点二选一三档分层 + 8 条一致性机制）、`docs/design/ui-review-log.md`（验收记录与先例表）；`data/README.md` 重写为「manifest 是路径唯一真源」；`docs/design/data-schema.md` 按 v2 形状重写 |
| CI | 「Data drift gates」换成 `sync_manifest.py --check`，新增「UI gates」一步（两道 UI 闸门） |

验证：`python tools/check_docs.py` 通过（链接 + 反引号路径 + 规模数字全绿）；`sync_manifest.py --check` / `sync_presets.py --options --check` / `bundle_worker_data.py --check` / `normalize_strategy.py --check` / `gen_strategy_guides.py --check` / `seed_main_stat_notes.py --check` / `calc_graduation_panel.py --check-all` / `check_ui_contrast.py --check` / `check_ui_scale.py --check` 全过；后端 `pytest` 389 passed、前端 `npm run test` 141 passed、`npm run typecheck`、`npm run build` 通过；**三方对拍（legacy ≡ Vue3 ≡ Python）4/4 逐字符一致**。

> **UI 阶段未经像素验证**：仓库无 playwright / puppeteer，本环境也无可用截图工具，因此 UI 结论全部来自读源码（code-only）。`docs/design/ui-review-checklist.md` 的 B 档 14 条与 C 档 3 条仍待人工执行。

---

---

## 2026-10-20 · 技术文档分类重构 + changelog 归档机制

| 变更 | 说明 |
| --- | --- |
| 文档分类 | `docs/` 由 13 个平铺文件改为**按主题分四类目录**：`overview/`（project-overview、requirements、directory-layout）、`design/`（architecture、data-schema、calculation-rules）、`guides/`（development、testing、deployment）、`reference/`（api-reference）；`docs/README.md` 索引与「按角色的阅读路径」同步重写 |
| 历史件归位 | `docs/structure-review.md`（早已标注「历史归档」）移入 `docs/completeds/`；`docs/changelog/2026-10-archive.md` 补齐归档索引 |
| 链接修复 | 移动文件连带产生的 **184 处断链**全部重算修正（相对链接按「移动前目录」解析后再按新位置重算）；另修掉 Vue 迁移遗留的 9 处失效路径（`strategy/renderStrategy.ts` → `frontend/src/strategy/renderStrategy.ts`、`data/agent-presets.js` → `frontend/tests/fixtures/legacy-calculator/data/agent-presets.js`、已删除的 `frontend/legacy/`） |
| changelog 归档 | 新增 `tools/archive_changelog.py`：`docs/changelog.md` 只保留最近 12 条，更早的按条目日期归入 `docs/changelog/YYYY-MM-archive.md`（被移走的条目比归档里已有的更新，插到归档顶部）；`docs/README.md`「文档维护约定」与 skill 同步表都写明这条规则 |
| 校验增强 | `tools/check_docs.py` 的反引号路径检查从「只扫 SKILL.md」扩展到**当前态文档**（docs/ 全部 + 各 README），并容忍 `路径:行号` 写法；归档件（`completeds/`、`changelog/`）不参与，避免改动历史记录 |
| 归档执行 | 当前 changelog 从 16 条收敛到 12 条，4 条（2026-10-16 的猫宫又奈 / 11号 / 珂蕾妲 / 格莉丝）并入 `docs/changelog/2026-10-archive.md`（现 98 节） |

验证：`python tools/check_docs.py` 通过（链接 + 反引号路径 + 规模数字三项全绿）；其余数据闸与测试同前一轮全绿。

---

---

## 2026-10-20 · 攻略改动增加「同步收尾」阶段 G

| 变更 | 说明 |
| --- | --- |
| 阶段 G · 同步收尾 | `get-agent-strategy` 新增**阶段 G**：改了内容后必须按「改了什么 → 必须同步哪里」表同步文档/代码（新增/删除代理人 → mapping + 攻略目录 + 登记表 + `docs/overview/project-overview.md`「当前规模」表 + `data-schema.md` + `requirements.md`；预设变化 → `data/*.json` + 对拍夹具 + Worker 产物；图片 → 必须 webp 且引用与磁盘文件名逐字一致；脚本/契约/skill 变化 → 对应 README 与 `_shared/`）。完整对照表在 `.github/skills/_shared/deploy-checklist.md` |
| 脚本可执行 | `tools/agent_deploy.py` 新增 `sync` 阶段：打印上述对照表并自动跑 `gen_strategy_guides.py` / `sync_presets.py --to-legacy` / `bundle_worker_data.py` / `check_docs.py` / `agent_audit.py` |
| 文档一致性门禁 | `tools/check_docs.py` 新增**数量类事实核对**：代理人数、音擎数、驱动盘数、配装规则表条目、命名映射条数与未上线数、攻略页数、图片数与格式、前后端测试数——与数据源逐项比对，文档写了旧数字会直接报错（CI 已在跑该脚本） |
| 修掉既有漂移 | 核对发现并修正 27 处过期数字：`docs/overview/project-overview.md`（代理人数 60→61、攻略页 60→61、图片 398 张 PNG→522 张 webp、前端 128→131、后端 310→315、未上线 2→1）、`docs/reference/api-reference.md`、`docs/design/architecture.md`、`docs/design/data-schema.md`、`docs/guides/deployment.md`、`docs/guides/development.md`、`docs/overview/requirements.md`、`docs/guides/testing.md`、`README.md`、`backend/tests/README.md` |

验证：`python tools/check_docs.py` 通过（链接 + 反引号路径 + 规模数字三项全绿）；`tools/agent_deploy.py --slug cissia --stages identity,sync --dry-run` 输出阶段 G 对照表正常；其余闸门与测试同前一轮全绿。

---

---

## 2026-10-20 · 技能文本抓取质量修复 + skill 整合出 `get-agent-strategy`

| 变更 | 说明 |
| --- | --- |
| **技能文本口径** | WIKI 的招式 `desc` 展示的是**初始数值**，满级数值在成长表每 rank 行内的 `<span data-type="详情">` 上。抓取器改为：核心技正文取**最后一级（F）详情 span = 满级正文**，「额外能力/额外被动」从 desc 切出**单独成一条 move**（无 `growth`），标题归一为「核心技：XXX」。**61 页全部重抓**，核心技从 1 条变 2 条（洛克茜原为唯一样板） |
| 希希芙额外能力 | `strategy/cissia/data/cissia.json` 补回「额外能力：毒素发酵」全文（原文：队伍中存在[击破]或与自身属性相同的角色时触发；拥有[毒素]时，使全队角色暴击伤害提高40%，自身额外提高10%，持续至[毒素]耗尽后30秒） |
| 满级数值修正 | 洛克茜核心技 480/40/22%/10% → **960/76.8/40%/20%**；希希芙无视防御 3% → **6%**；般岳贯穿力 150 → **300 点**；赛斯护盾 50% → **80% 初始攻击力** |
| 剩余初始标注 | 20 处非核心技/额外能力段的「此处数据为初始数据」**保留原样**（WIKI 未提供该招式的满级值，不做无依据替换），由 `tools/agent_audit.py` 逐条列出 |
| 新增 skill | `.github/skills/get-agent-strategy/` —— **代理人攻略一站式入口**（新增 / 修正两种模式、六阶段、按职业分组的参考页表、待确认清单） |
| 共享 references | 新增 `.github/skills/_shared/`（不是 skill）：`naming.md`（slug 唯一性 + 属性/职业/评级 → 图标 slug + 图片命名）、`editorial-fields.md`（信息采集矩阵：应该寻找的点 → 修改的文件）、`deploy-checklist.md`（阶段闸门 + 抓取口径 R1–R6 + 已知坑）。`agent-strategy` / `fix-agent` 里重复的映射表已改为链接 |
| 既有 skill 改造 | 8 个 skill 统一加「由 `get-agent-strategy` 编排」横幅；`agent-strategy` / `fix-agent` 的属性·职业表去重；`agent-background` 补 Nanoka 角色框头像 |
| 新增脚本 | `tools/agent_deploy.py`（一站式编排：身份→预设→抓取→图片→编辑骨架→面板→登记表→闸门，编辑内容只出骨架与待确认清单）、`tools/agent_audit.py`（14 项体检：slug 一致、图标一致、引用不断链、图片齐备、面板形状、驱动盘方案、队伍、命座、加点链、文字攻略、**核心技额外能力完整性**、机制归属抽查、占位残留、生成物新鲜度） |
| 顺带修的数据问题 | 南宫羽职业图标由 `anomaly` 修正为 `stun`（旧数据与预设的「击破」矛盾）；burnice / jane 的 `subPriority` 链尾悬空 `=` 修正为「攻击力 = 穿透值」；菲欧妮称号「坎卜斯黑枝」被 WIKI 清空，抓取器改为**保留旧值**不再抹掉 |
| 希希芙攻略内容 | 拆开「核心被动的电属性条件」与「额外能力（击破/同属性）触发 + 全队暴伤 +40%、自身 +10%」；队伍 note 补触发条件；暴击/爆伤口径计入额外能力增益；`driveBuilds[].set4` 由数组改为对象；补「关键命座推荐」——`cinemaPriority` 取 1 / 2 / 6 影画（1 减穿 + 全队无视 5% 电抗、2 蛇吻 +35% 且失衡补毒、6 蚀骨印记联动脉冲） |
| 希希芙配装重置 | 按需求方口径重置：闪避降到 **7 级**；音擎只留专武 + **限定下位**（机巧心种）+ **非限定下位**（硫磺石、旋钻机-赤轴）；驱动盘改两套——**单强攻** 4 拂晓生花 + 2 摇摆爵士（回能，备选啄木鸟电音 / 折枝剑歌），4 号暴击率、5 号电属性伤害、6 号回能；**双强攻** 4 静听嘉音 + 2 摇摆爵士，4 号暴击率、5 号攻击力、6 号回能；副词条统一「暴击率 > 攻击力% > 暴击伤害 = 攻击力 > 穿透值」。毕业面板按新配装实算：满配 **2,835.5 / 62.6% / 126.8% / 穿透值 36**（暴击率 14 条副词条补回 2 件套让出的 8%，局内 62.6% + 专武 20% + 蚀骨 3 层 18% 正好满暴），30 词条档 **2,401.2 / 50.6% / 93.2% / 穿透值 18**；双 C 队（席希耀）里的希希芙改挂静听嘉音，与双强攻方案对齐 |

验证：`tools/agent_audit.py --all` **0 ERROR**（28 WARN 均为「WIKI 未提供满级值」与「set4 数组写法」两类已知情况，5 INFO 为 severian 未公开 + 两名缺影画图）；`normalize_strategy.py --check`、`seed_main_stat_notes.py --check`、`gen_strategy_guides.py --check`、`calc_graduation_panel.py --check-all`、`sync_presets.py --to-legacy --check`、`bundle_worker_data.py --check` 全过；后端 `pytest` 315 passed、前端 `npm run test` 131 passed、`npm run typecheck`、`npm run build` 通过。

---

---

## 2026-10-20 · 全站图片统一 webp + 角色框头像补齐

| 变更 | 说明 |
| --- | --- |
| 角色框头像 | 新增 `tools/fetch_agent_films.py`，从 Nanoka（`zzz.nanoka.cc`）静态数据接口取 `IconRolePiece<编号>.webp`，为**全部 61 位代理人**补齐 `frontend/public/images/strategy/<slug>/film.webp`（约 11 KB/张，源图 156×156 RGBA）。编号取自详情 JSON 的 `icon`（安比 01 / 可琳 09 / 11号 05 保留前导零），个别代理人（克拉蕾）回退 `partner_info.inter_knot_icon` 的编号 69 |
| 图片统一 webp | `frontend/public/images/` 下 **464 张 PNG 全部转成 webp**（`tools/images_to_webp.py`，有损 q90；已是 webp 载荷的立绘背景原样透传）。体积 **249.89 MB → 39.90 MB（省 84%）**，加上新增头像后共 **522 张 / 40.51 MB**。单张最大收益：影画立绘 2.9 MB → 289 KB |
| 引用同步改写 | 同步改写 **134 个文件、3245 处** `/images/…png` → `.webp`：61 份 `*.strategy.json`、61 份抓取产物 `*.json`、`data/catalog/drive-discs.json`、`frontend/src/constants/strategyGuides.ts`（重新生成）、`renderStrategy.ts` / `useCascaderIcons.ts` / 计算器组件、`backend/tests/test_strategy_data.py`、前端测试、文档与 skills。**远程兜底 URL（`*Remote` 的 mihoyo CDN 地址）保持原样** |
| 抓取脚本跟进 | `scrape_agent_guide.py` 下载时直接转码为 webp（无 Pillow 时原样透传，浏览器按内容嗅探渲染），落盘名改为 `.webp`；`fetch_agent_backgrounds.py` 改存 `background.webp` |
| 文档同步 | `docs/overview/directory-layout.md`、`frontend/src/README.md` 的图片清单与张数改为实测值（61 代理人 + 101 音擎 + 7 图标 + 30 驱动盘 + 6 技能 + 10 属性 + 2 等级 + 305 攻略独有 = 522 张 webp）；skills 文档的图片文件名规范改为 `.webp` |
| 回归守护 | `frontend/tests/strategy-background.spec.ts` 增加「每位代理人都有 `film.webp`」断言 |

验证：`tools/images_to_webp.py` 自校验「无残留 `.png` 引用 + 所有本地图片引用均存在」通过；`normalize_strategy.py --check`、`gen_strategy_guides.py --check`、`seed_main_stat_notes.py --check`、`check_docs.py` 全过；后端 `pytest` 315 passed、前端 `npm run test` 131 passed、`npm run typecheck`、`npm run build` 通过；`dist/images` 同步为 522 张 webp / 40.51 MB。

---

---

## 2026-10-20 · 代理人攻略页立绘背景补齐

| 变更 | 说明 |
| --- | --- |
| 背景补齐 | 此前只有 `roxy`、`phoenix` 两页有立绘背景，本次为**全部 61 位代理人**补齐：`frontend/public/images/strategy/<slug>/background.webp`（共 59 张新图，均为 Gachabase 的立绘 `splash_art`，webp 载荷，约 +9 MB） |
| 数据字段 | 每份 `strategy/<slug>/data/<slug>.strategy.json` **顶层**新增 `"background": "/images/strategy/<slug>/background.webp"`（与 `phoenix`/`roxy` 既有写法一致），共享渲染器 `renderStrategy.ts` 据此输出 `.page-bg` 背景层，无需改任何 HTML/CSS |
| 抓取工具 | 新增 `tools/fetch_agent_backgrounds.py`：从 Gachabase（`zzz.gachabase.net` beta 分支）的 SvelteKit `__data.json` 接口取数——列表接口拿代理人 id/slug，详情接口取 `entity.assets.splash_art_path_hash` → `variants[hash].webp`。支持 `--dry-run` 预览、`--skip` 黑名单，已有的背景自动跳过 |
| 换装记录去重 | Gachabase 里 `aria`(1502)、`remielle`(1582) 各有一条换装记录，其 `splash_art_path_hash` 会串到别的代理人（青衣/露西）身上；脚本按 id 取最小的一条（本体），避免下错图 |
| 回归守护 | 新增 `frontend/tests/strategy-background.spec.ts`：断言登记表里每位代理人的 `background` 字段与背景图文件都存在，且攻略页确实渲染出 `.page-bg` 层 |

验证：`npm run test` 130 passed（新增 2 项）、`npm run typecheck`、`npm run build` 通过；`normalize_strategy.py --check`、`gen_strategy_guides.py --check`、`seed_main_stat_notes.py --check`、`check_docs.py` 均通过；后端 `pytest` 315 passed。抓取结果逐张目测抽检（星见雅、蕾米埃尔、雅、火波）均为正确的竖版立绘。

---

---

## 2026-10-20 · 星见雅驱动盘与毕业面板修正

| 变更 | 说明 |
| --- | --- |
| 驱动盘分两套 | `strategy/miyabi/` 的 `driveBuilds` 由 1 套改 2 套（4 件套不同，按约定分页）：**直伤流** 4 折枝剑歌 `ep-1000` + 2 河豚电音 `ep-193`（备选静听嘉音 `ep-1001`）、**精通流** 4 自由蓝调 `ep-191` + 2 法厄同之歌 `ep-1194`（备选谶羽之誓 `ep-2116` / 混沌爵士 `ep-800`，同为异常精通+30） |
| 主词条 | 直伤流 4 号爆伤+48%（备选暴击率+24%）/ 5 号穿透率+24%（备选攻击力+30%）/ 6 号攻击力+30%（备选异常掌控+30%）；精通流 4 号异常精通+92（备选暴击率+24%）/ 5 号穿透率+24%（备选攻击力+30%）/ 6 号异常掌控+30%（备选无） |
| 副词条优先级 | 直伤流：**暴击率 > 攻击力% = 暴击伤害 > 异常精通 > 攻击力 = 穿透值**；精通流：**暴击率 = 异常精通 > 攻击力% > 暴击伤害 > 攻击力 = 穿透值** |
| 展示行 | 毕业面板展示行由 `atk,cr,cd,dmg` 改为 `atk,cr,cd,am`（攻击力 / 暴击率 / 暴击伤害 / 异常精通），两件套由「啄木鸟电音」换成「河豚电音」（穿透率+8%） |
| 满配面板 | 按直伤流 4 折枝 2 河豚实算：攻击力 **3,010.2** / 暴击率 **81.8%** / 暴击伤害 **133.2%** / 异常精通 **382**（54 词条 = 暴击率×22 + 暴击伤害×4 + 攻击力%×12 + 异常精通×16；暴击率堆到 80%、攻击力堆到 3000 即止，爆伤 130 为目标）。换装后暴击率只能靠副词条顶——基础暴击率仅 5%，旧方案的「啄木鸟电音 2 件 +8%」与「4 号位暴击率 +24%」两条来源都换成了爆伤/穿透/攻击 |
| 非满配面板 | 同配置、30 词条（暴击率×20 + 暴击伤害×2 + 攻击力%×8）：攻击力 **2,815.4** / 暴击率 **77%** / 暴击伤害 **123.6%** / 异常精通 **238**（攻击力门槛降到 2800、爆伤降到 120；词条池只有暴击率/暴击伤害/攻击力%，余量全给暴击率） |
| 新增队伍 | 新增「雅维蕾」：星见 雅 `ep-996` 自由蓝调 / 维琳娜 `ep-1960` 呼啸沙龙 / 蕾米埃尔 `ep-2076` 谶羽之誓——三异常互相结算紊乱刷[落霜]，蕾米埃尔流明复制右侧属性即转烈霜异常，[幻色]给全队异常积蓄效率 +15%，队中 3 异常吃满额外能力 40% 加攻档 |
| 文案修正 | 文字攻略中与新面板冲突的旧数据一并改正：「核心暴击率+14.4%」→「基础暴击率只有 5%」、「专武残心青囊」→ 霰落星殿、「四号位暴击率+24%」→ 新直伤流 4 号位为暴击伤害、已换掉的「啄木鸟电音」→ 河豚电音，并补两套驱动盘与「雅维蕾」的说明 |

验证：`calc_graduation_panel.py --check`（单文件实算比对）退出 0、`--check-all` 61 份攻略面板结构校验通过；`seed_main_stat_notes.py --check`（192 条主词条备注齐全）、`normalize_strategy.py --check`、`gen_strategy_guides.py --check`、`check_docs.py` 均通过；后端 `pytest` 315 passed、前端 `npm run test` 128 passed、`npm run typecheck`、`npm run build` 通过。

---

---

## 2026-10-19 · 「保存攻略」改为 JSON 驱动的攻略缩略图

| 变更 | 说明 |
| --- | --- |
| 保存攻略 | 不再截取 hero + 攻略区块，改为按 `strategy/<slug>/data/*.json` 生成 1360px 白底攻略卡片，导出 PNG |
| 卡片内容 | 左侧使用攻略 `background` 立绘；右侧六条分支：技能加点 / 命座（01–06 关键命座高亮）/ 武器 / 驱动盘 / 队伍 / 毕业面板（满配 + 非满配） |
| 可读性 | 正文、标签与连接线统一改为深色；技能、武器、驱动盘、队伍等条目使用白色不透明单元背景，避免透出立绘 |
| 词条展示 | 毕业面板按「大词条 + 小词条」展示：计算仍用完整 54 条实算，展示改成如洛茜 `47+7 词条`、莱特 `47+7`、克拉蕾 `37+17`、叶瞬光 `45+9`；小词条（小攻击/小防御/小生命、穿透值、无效词条）只计数不展开 |
| 驱动盘卡片 | 导出图的驱动盘推荐改为「配装行 + 4/5/6 号位三个主词条小框」，首选与备选同框、只显示词条名并隐藏 `+数值`（如 `异常精通 +92` → `异常精通`），详情页保留完整数值；无备选时自动隐藏；主词条按方案分组：共用则一行，不同则各自成组（行首为方案名） |
| 样式隔离 | 导出卡片增加 `strategy-card--export` 修饰类，覆盖启动页代理人卡片同名的 `.strategy-card` / `.strategy-card__tachie` 规则，避免立绘绝对定位后铺满整张导出图 |
| 导出布局 | 导出卡片内部布局全部改为 flex（html2canvas 不支持 grid），并显式重置启动页卡片继承来的 `flex-direction: column` / `align-items: center`，修复导出图里立绘与内容上下堆叠的问题；立绘改用 `max-width/max-height` 而非 `object-fit` |
| 备选对齐 | 主词条框改为「号位徽标 + 文字列」，首选与备选同处一列，备选文字与主词条名左对齐 |
| 保存一图流 | 保持原有整页截图逻辑不变 |
| 测试 | 新增 `tests/strategy-card.spec.ts` 与 `tests/substats.spec.ts`，覆盖卡片字段映射、词条 47+7 拆分与登记表内全部代理人 |

验证：`npm run typecheck`、`npm test`（128 passed）、`npm run build` 通过；Chrome + html2canvas 实测复核洛茜导出图（立绘在左、六条分支在右、4/5/6 号位三个框且备选与主词条对齐）。

---

---

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
| 修复计划 | 新增 `docs/completeds/repair-plan.md`（三阶段修复计划，含 P0/P1/P2 共 36 项发现） |

验证：`pytest` 310 passed；`npm run typecheck` / `npm run test` 118 passed；`normalize_strategy.py --check`、`gen_strategy_guides.py --check`、`seed_main_stat_notes.py --check`、`calc_graduation_panel.py --check-all` 均通过。`calc_graduation_panel.py --check`（单文件实算比对）仍需按代理人传完整参数方可复现，结构化 `--check-all` 已覆盖全部文件。

---

---

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

---

---

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

---

---

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

---

---

## 2026-10-18 · 攻略数据归一、UTF-8 修复与图标命名统一

| 变更 | 说明 |
| --- | --- |
| 数据命名归一 | 29 个攻略目录的数据文件改为 `<slug>.json` / `<slug>.strategy.json`；`app.js`、JSON、`strategyGuides.ts` 引用同步 |
| 清理遗留目录 | 删除重复的 `strategy/ye-shun-guang/`，规范目录为 `strategy/ye-shunguang/` |
| 修复坏 JSON | 21 份非 UTF-8 的抓取产物按 `entryPageId` 从官方 Wiki 重新抓取，补齐本地图标 / 立绘 / 影画路径 |
| 图片命名统一 | 属性 / 职业图标统一为小写 ASCII slug（`honed-edge.webp`、`attack.webp` 等），数据、Skill 与文档同步 |
| 回归守卫 | 新增目录 / 数据文件名 / UTF-8 / 图片引用 / 登记表一致性测试；音擎计数改为从数据文件动态读取 |
| 新增工具 | `tools/normalize_strategy.py`：`--check`、`--rescrape-invalid`、`--remove-legacy` |

验证：`pytest` 307 passed；`npm run test` 108 passed；`npm run typecheck`、`npm run build` 通过。

---

---

## 历史归档

更早的变更记录按月归档：

- [changelog/2026-10-archive.md](changelog/2026-10-archive.md)
