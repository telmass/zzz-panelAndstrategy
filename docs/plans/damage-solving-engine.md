# 伤害求解层落地计划：白板口径、局内效果、词条优化与相对值

状态：**待执行**
制定日期：2026-10-23
上一阶段：[damage-engine-phase2.md](damage-engine-phase2.md)（职业口径 + 参数数据集）
设计指南：[../design/damage-mechanism-guide.md](../design/damage-mechanism-guide.md) §17–§28
规格真源：[../design/damage-formulas.md](../design/damage-formulas.md)（含 §3.6.1 紊乱倍率）

> **约定**：本计划里带反引号的路径是**已存在**文件；带「拟新增」前缀的是**尚未落地**的
> 文件，不加反引号，避免 `tools/check_docs.py` 把规划路径当成断链。

---

## 0. 这份计划是什么

把设计指南 B 部分（§17–§28）从「口径与算法」落成**可运行的代码、数据、工具与页面**：

```text
白板目标 → 局内效果层 → 代理人档案 → 理论循环 → 词条优化 → 驱动盘评分 → 相对值报告 → 策略页
```

**本期做**：

- 白板目标 `whiteboard-boss-60` 与敏感性目标；
- `Effect` 层（音擎被动 / 4 件套 / 影画 / 条件 / 层数 / 覆盖率 / 快照）；
- 每代理人 `strategy/<slug>/calculator/calculator.json` + 生成物 `report.json`；
- 技能倍率解析、直伤 / 属性异常循环、紊乱倍率纯函数（引擎路径后续）；
- 副词条最优分配（含每盘可行性）、驱动盘评分；
- 影画 / 音擎相对值表、非满配曲线；
- 策略页「数值口径（白板）」模块。

**本期不做**（明确登记）：

- 完整战斗模拟、时间轴、能量循环、队伍 Buff / 队友快照；
- 风属性 / 耀变 / 异放 / 紊乱的**引擎结算路径**（紊乱只做倍率纯函数与文档）；
- 逐角色自定义代码（只做数据档案 + 窄接口例外）；
- 主词条全组合搜索（`main+sub` 作为可选模式，默认固定）。

**完成定义（v1）**：

- 36 名伤害向代理人（强攻 / 异常 / 命破 / 锋御）有 `modeled` 或 `partial` 报告；
- 13 名支援 / 防护有 `personal-only` 报告，并明确「团队贡献未建模」；
- 12 名击破有 `personal-only` 报告，并明确「白板不评价冲击」；
- 风 / 流明等特殊机制至少登记 `descriptive`，不静默为 0；
- 每个 `report.json` 可通过 `--check` 复算，策略页可渲染，CI 全绿。

> 「61 个全部 modeled」不是 v1 目标；**每个代理人都有明确状态**才是。

---

## 1. 起点与阻断（可核对）

| 能力 | 现状 | 缺口 / 阻断 |
| --- | --- | --- |
| 面板 | `core/panel.py`，三方对拍锁定 | — |
| 伤害乘区 | `core/damage/zones.py` + `engine.py`，常规/异常/贯穿/锋御路径 | 无 Effect 层、无事件/循环、无 4 件套/影画/音擎被动 |
| 目标函数 | `services/damage_service.py` | `multiplier=1`；无 rotation；无目标选择 |
| 对比 / 边际 | `services/compare_service.py` / `benefit_service.py` | **`compare_service` 导入即 `AttributeError`**：`options.MAIN_STAT_EXCLUDES` 不存在 |
| 毕业面板 | `strategy/*/data/*.strategy.json` 的 `graduationPanel` | **61 份里 0 份有 `buildSpec`**；`calc_graduation_panel.py` 里 `args_from_build_spec` 已丢失，`migrate_build_spec` / `build_compare` / `substat_benefit` / `derive_panel` 调用即 `AttributeError` |
| 音擎 | `data/catalog/weapons.json` 101 条 | 只有 `base` + `substat`；**没有 `[局内生效]` 被动与精炼数组** |
| 4 件套 | `data/catalog/drive-discs.json` 有 `setEffect4` 文本 | 计算器只建模 2 件套 |
| 影画 | `<slug>.json` 只有文本 | 没有结构化 `modifiers` / `rotationPatches` |
| 技能倍率 | `<slug>.json` 有 1–16 级文本 | 没有解析成数值表；`score_build` 固定 1 |
| 词条优化 | `calc_graduation_panel.py` 手工传 `--sub-stats` | 没有搜索算法；没有每盘可行性 |
| 驱动盘评分 | `benefit_service.one_roll_values` | 没有单盘分、没有主词条分、没有锚点 |
| 报告 / UI | 无 | 没有 `calculator/report.json`；策略页没有数值表 |
| 命名 | 工作区 `core/modes.py` 用 `fengyu`，`engine.py` / 预设用 `armorer` | 一半一半，必须统一 |
| 6 号位冲击力 | `options.py` 仍 24% | 官方 / 参考实现 18%，数据债 |

**结论**：先做 P0 阻断，否则后面的相对值表建在坏地基上。

---

## 2. 范围与裁决（Phase 0）

采用设计指南 §28.8.3 的裁决 D1–D18，不在这里重复；补充三条执行裁决：

| # | 执行裁决 | 说明 |
| --- | --- | --- |
| E1 | 基准 = `C0R1` + 54 条**最优**副词条 | 报告同时给 `samePanel` / `optimalPanel` |
| E2 | 报告走**静态文件**，不新增 FastAPI 路由 | `/strategy/<slug>/calculator/report.json`，Vite 插件复制 |
| E3 | 每盘可行性是**硬约束** | 不可行解不进入 Top-K，不接受「近似 4.5 档/盘」 |

### 2.1 按定位的计算器范围

| 范围 | 人数 | 计算器类型 | v1 输出 |
| --- | ---: | --- | --- |
| 强攻 / 异常 / 命破 / 锋御 | 36 | `personal` | 完整个体伤害 + 武器/影画相对值 |
| 支援 / 防护 | 13 | `personal-only` | 个人伤害；团队增益 `descriptive` |
| 击破 | 12 | `stun` | 个人伤害；冲击/失衡「白板不评价」 |
| 风 / 流明等特殊 | 含在上面的角色里 | `personal` / `descriptive` | 先登记机制，不强行算 |

> 人数来自 `data/catalog/agents.json` 当前 61 条：强攻 17 / 异常 13 / 击破 12 /
> 支援 8 / 命破 5 / 防护 5 / 锋御 1。

### 2.2 试点

| 试点 | 用途 | 关键验证 |
| --- | --- | --- |
| 叶瞬光（直伤） | P1 第一个 `personal` | 音擎局内暴击、影画技能等级、直伤循环 |
| 菲欧妮（异常） | P1 异常 + 音擎层数 | 异常精通、双生层数、灼蚀条件、C2/C6 |
| 克拉蕾（锋御） | P1 锐化 | 防御力基础、锐暴平方项、转模 |
| 般岳（命破） | P2 贯穿 | 贯穿力、生命值转模、防御区恒 1 |

---

## 3. 工作分解（P0–P7）

> 估算为**单人**人日（含实现 + 单测 + 自测），不含等待评审。可并行时在 §4 标注。

### P0 · 阻断与契约（约 5 人日）

| ID | 任务 | 落点 | 验收 | 依赖 |
| --- | --- | --- | --- | --- |
| P0-1 | 修 `compare_service` 的 `MAIN_STAT_EXCLUDES` | `core/options.py` 补映射，或改为引用 `core/panel_rows.py` 的单一真源 | `from zzz_panel.services import compare_service` 成功；`pytest` 绿 | — |
| P0-2 | 统一 `armorer` / `fengyu` | `core/modes.py`、`core/panel.py`；默认统一回最后一次提交的 `armorer`；若 `fengyu` 是有意改名，则全链路统一到 `fengyu`，先与用户确认 | `pytest` + 三方对拍绿；无另一种拼写残留 | — |
| P0-3 | `TargetPreset` 补 `fixed_defense` / `distance_falloff` / `stunned_default` | `core/damage/targets.py`、`engine.py`；`target_defense()` 使用 `fixed_defense` | 白板常量测试 W1；`fixed_defense=0` 时与旧结果逐值一致 | — |
| P0-4 | 白板目标 + 敏感性目标 | `core/damage/targets.py` | `WHITEBOARD_TARGET` 的防御区 `0.454545…`、失衡区 2.5、抗性区 1.0 | P0-3 |
| P0-5 | 新增 schema：`schemas/calculator.py` / `schemas/effects.py` | 拟新增 backend/src/zzz_panel/schemas/calculator.py、backend/src/zzz_panel/schemas/effects.py | 严格校验：未知字段 / 未知 target / 未知 condition 拒绝 | — |
| P0-6 | 报告静态路径 + Vite 插件契约 | 拟新增 backend/src/zzz_panel/services/calculator_service.py；`frontend/vite.config.ts` | dev 可访问 `/strategy/<slug>/calculator/report.json`；构建产物含该文件；404 不抛错 | — |
| P0-7 | `buildSpec` 重建方案落地 | 先恢复 `calc_graduation_panel.py` 的 `args_from_build_spec`（或抽到共享模块）；再跑 `migrate_build_spec.py`；把 `--check-all` 改成按 `buildSpec` 实算 | 61 份 `buildSpec` 可从 calculator/profile 复算；`--check-all` 实算通过；迁移失败的原样保留并点名 | P0-5 |
| P0-8 | CI 基线 | `.github/workflows/ci.yml` | 现有 `pytest` / `npm test` / `check_docs` / `sync_manifest`；先修复或记录 4 处图片计数与测试计数漂移；**新增内容不得增加问题** | P0-1..P0-3 |

**P0 完成标志**：现有工具能跑、命名一致、白板目标可加载、schema 能拒绝坏数据。

### P1 · 目标 / 效果层 / 音擎（约 12 人日）

| ID | 任务 | 落点 | 验收 | 依赖 |
| --- | --- | --- | --- | --- |
| P1-1 | `Effect` 数据模型 + 目标注册表 | 拟新增 backend/src/zzz_panel/core/damage/effects.py | §28.3.1 白名单；未知 target 拒绝 | P0-5 |
| P1-2 | 条件 DSL + 求值上下文 | 同上 | §28.3.3 条件全部有单测；未知 condition 报错 | P1-1 |
| P1-3 | 层数 / 覆盖率 / 叠加 / 顺序 | 同上 | `effective = base × stacks × uptime`；条件假 = 0；同区加算、独立乘区相乘 | P1-1 |
| P1-4 | 快照 / 实时拆分 | `effects.py` + `engine.py` | 直伤实时、异常积蓄时；无视抗性不进加权（W7） | P1-3 |
| P1-5 | 音擎 effect 抓取 + schema | `refresh_weapon_presets.py`、`schemas/presets.py`、`data/catalog/weapons.json` | 涅槃/双生/壳中/嵌合 4 条 `raw` + 精炼数组；`perRefinement` 长度 5 | P0-5 |
| P1-6 | 4 件套 + 属性伤害 2 件套 | `data/catalog/drive-discs.json`、`link_disc_effects.py`、`calculator.effects` | 试点角色 4 件套至少 1 套 `modeled`；属性伤害 2 件套按元素进 `effects`，不匹配 `not_applicable` | P1-1 |
| P1-7 | 三个试点接入 | `strategy/<slug>/calculator/` | 每个试点 `report.json` 生成；武器/影画表可复算 | P1-1..P1-6 |
| P1-8 | 验收：W5 / W6 / W7 | 拟新增 backend/tests/test_damage_effects.py | 局内不改面板；火伤只打火事件；快照/实时分表 | P1-1..P1-4 |
| P1-9 | 逐角色机制常数 | 拟新增 data/catalog/agent-mechanics.json（登记到 `data/manifest.json`）；`core/modes.py` 读 `armorerCritFromCd` / `armorerBlastDamage` | 克拉蕾 0.35 / 150 与硬编码值一致；其它角色默认值不漂移；`sync_manifest.py --check` 绿 | P0-3 |

**P1 完成标志**：音擎被动从「武器库缺字段」变成 `Effect`；试点能算出「带专武 vs 下位」的差异。

### P2 · 循环 / 倍率 / 异常（约 10 人日）

| ID | 任务 | 落点 | 验收 | 依赖 |
| --- | --- | --- | --- | --- |
| P2-1 | 技能倍率解析器 | 拟新增 tools/parse_skill_multipliers.py；输出 `strategy/<slug>/calculator/multipliers.json` | 1–16 级、多段、异放/失衡分组；`sourceSha256` 可校验 | P0-5 |
| P2-2 | 事件模型 + 循环校验 | 拟新增 backend/src/zzz_panel/core/damage/rotation.py | §28.4.4 全部检查；id 唯一、路径块匹配、覆盖率 | P0-5 |
| P2-3 | 直伤 / 属性异常事件接入 | `damage_service.py` | 多事件求和；`hits × count` 不重复乘 | P2-2 |
| P2-4 | 紊乱倍率纯函数 | `core/damage/zones.py` | §6.1 五类基底；灼烧 t=2 → 1250%，感电 t=2 → 1450% | — |
| P2-5 | 紊乱 / 异放 / 乱流事件 schema（先不结算） | `rotation.py` | 加载/校验通过；引擎路径标 `not_implemented` | P2-2 |
| P2-6 | 技能等级 + 影画 `rotationPatches` | `rotation.py`、`calculator_service.py` | C3/C5 +2；超 16 级标 `unsupported`；patch 顺序确定 | P2-2 |
| P2-7 | 命破试点般岳 | `strategy/<slug>/calculator/` | 贯穿力基础、防御区恒 1、生命值转模 | P1、P2-3 |

**P2 完成标志**：给定循环能出多事件总伤；倍率不是手填，来自 `<slug>.json`。

### P3 · 优化器 / 可行性（约 14 人日）

| ID | 任务 | 落点 | 验收 | 依赖 |
| --- | --- | --- | --- | --- |
| P3-1 | `cap_i` + 每盘可行性 | 拟新增 backend/src/zzz_panel/services/optimizer_service.py | §28.6.2 五步；`AM 27 + ATK% 27` 判 infeasible | P0-4 |
| P3-2 | 束搜索 + 局部搜索 | 同上 | 参数默认值；确定性；`budgetHit` | P3-1 |
| P3-3 | 独立 oracle | 拟新增 backend/tests/test_optimizer.py | `N ≤ 12` 全枚举一致 | P3-2 |
| P3-4 | 多预算 / 缓存 / 性能 | 同上 | 固定 7 档 `54/45/40/35/30/25/20`；单核 ≤ 8 分钟/角色；重复输入字节一致 | P3-2 |
| P3-5 | CLI：算出最优面板 + 曲线 | 拟新增 tools/build_agent_calculator.py | `--budget 54/30`；`--check`；输出 report 片段 | P3-2 |
| P3-6 | 与旧工具对齐 | `.github/skills/agent-strategy/scripts/calc_graduation_panel.py`、`tools/build_compare.py`、`tools/substat_benefit.py` | 旧的毕业面板可由 `calculator.json` 复算；两个旧工具改为读 calculator 或标 `deprecated`；不破坏现有页面 | P0-7、P3-5 |

**P3 完成标志**：给定 54 条预算，能给出**可刷出**的最优分配与 `D(N)` 曲线。

### P4 · 评分 / 相对值 / 报告（约 8 人日）

| ID | 任务 | 落点 | 验收 | 依赖 |
| --- | --- | --- | --- | --- |
| P4-1 | 单盘评分 | 拟新增 backend/src/zzz_panel/services/disc_score_service.py | `S_disc` / `S_main` / `damageRatio`；`w_i` 在 cap 为 0 | P3-1 |
| P4-2 | 武器 / 影画相对值 | `calculator_service.py` | `samePanel` + `optimalPanel`；C0–C6；R1–R5；矩阵 | P1、P2、P3 |
| P4-3 | 报告 schema + golden | `calculator_service.py`、`strategy/<slug>/calculator/golden.json` | §28.7.5 字段齐全；`calculatorHash`；`stale` 检测 | P4-2 |
| P4-4 | 非满配曲线 | `calculator_service.py` | `optimal` + `drop`；`actual` 有 `graduationPanelAlt` 才算，没有就省略；`A(N)` 定义一致 | P3-5 |
| P4-5 | CLI：单盘评分 | 拟新增 tools/score_disc.py | 输入盘 + 角色 → 分/有效词条/替换建议 | P4-1 |

**P4 完成标志**：菲欧妮示例表能从代码复算；`双生 R5 2 层 = 83.57%` 这类数字有 `report.json` 出处。

### P5 · 前端 / 文档（约 7 人日）

| ID | 任务 | 落点 | 验收 | 依赖 |
| --- | --- | --- | --- | --- |
| P5-1 | Vite 插件支持 `calculator/report.json` | `frontend/vite.config.ts` | dev + build 都能取；目录穿越被拒；404 正常 | P0-6 |
| P5-2 | 前端 API | `frontend/src/api/strategy.ts` | `fetchCalculatorReport()`；404 返回 `null` | P5-1 |
| P5-3 | 策略页数值模块 | `StrategyView.vue`、`renderStrategy.ts`、`strategy.css` | 环境摘要 / 武器表 / 影画表 / 曲线；404 整段隐藏 | P5-2 |
| P5-4 | 前端测试 | 拟新增 frontend/tests/calculator-report.spec.ts | 有报告 / 无报告 / `partial` 标记 / 表格排序 | P5-3 |
| P5-5 | 数据契约文档 | `strategy/README.md`、`docs/design/data-schema.md`、`docs/reference/api-reference.md` | 新字段、路径、404 行为、`calculatorKind` 说明；核对 4+2+2 已从表格删除 | P4-3 |
| P5-6 | 项目文档 | `docs/overview/requirements.md`、`docs/guides/testing.md`、`docs/overview/project-overview.md`、`docs/changelog.md` | 边界与已知限制更新；变更记录 | P5-1..P5-4 |

**P5 完成标志**：现有 61 个策略页不破；有报告的页面多出「数值口径（白板）」。

### P6 · 铺开（约 37 人日）

| ID | 批次 | 数量 | 内容 | 验收 |
| --- | --- | ---: | --- | --- |
| P6-1 | Tier A 伤害向 | 36 | 强攻 / 异常 / 命破 / 锋御 的 calculator.json + report | 每份 `--check` + golden；`modeled` 或明确 `partial` |
| P6-2 | Tier B 支援 / 防护 | 13 | `personal-only`；团队增益 `descriptive` | 顶部 `scopeNote`；不参与跨角色排名 |
| P6-3 | Tier C 击破 | 12 | `stun`；个人伤害 + 冲击不评价 | 顶部 caveat；不拿白板评价击破 |
| P6-4 | 特殊机制 | 风 / 流明等 | `descriptive` 或独立评分 | 不静默为 0；后续独立计划 |
| P6-5 | 新增代理人流程 | — | `tools/agent_deploy.py` 生成 `calculator/calculator.json` 骨架（`status: draft`）+ `golden.json` 占位；`agent_audit.py` 检查 | 新代理人不再漏档案；缺档案时 `agent_audit` 报错 |

**每份 calculator 的 DoD**：

- `calculator.json` 通过严格校验；
- 至少 1 个武器变体 + 1 个影画变体 + 1 个非满配预算；
- `golden.json` 经人工 review；
- `report.json` 的 `status` / `coverage` / `assumptions` 完整；
- 策略页能渲染；`--check` 通过；
- 文档里有「未建模项」清单。

### P7 · 性能 / CI / 收尾（约 5 人日）

| ID | 任务 | 验收 |
| --- | --- | --- |
| P7-1 | 基准与缓存 | 36 份 report 全量生成 ≤ 5 小时（单核）/ ≤ 2 小时（4 路并行）；缓存命中率记录 |
| P7-2 | CI 闸门 | 新测试 / `--check` / `check_docs` / `sync_manifest` / `bundle_worker_data` 全绿 |
| P7-3 | 发布与变更记录 | `docs/changelog.md` 记账；报告版本/引擎版本写明 |
| P7-4 | 复盘与遗留 | 未建模项、D 级裁决、下一阶段（时间轴/队伍/紊乱/风）清单 |

### 3.1 工作量汇总

| 阶段 | 人日（单人） | 可并行 |
| --- | ---: | --- |
| P0 阻断/契约 | 5 | — |
| P1 效果层/音擎 | 12 | 与 P0-5 之后 |
| P2 循环/倍率 | 10 | 与 P3 部分并行 |
| P3 优化器 | 14 | 与 P2 部分并行 |
| P4 评分/报告 | 8 | 依赖 P3 |
| P5 前端/文档 | 7 | 依赖 P4 schema |
| P6 铺开 61 人 | 37 | 依赖 P2/P3，可分批 |
| P7 性能/CI | 5 | 收尾 |
| **合计** | **98** | 2–3 人约 8–12 周；1 人约 5 个月 |

> 估算含实现 + 单测 + 自测，不含评审等待与数据返工；音擎/影画的原文歧义
> 是最大不确定项，按 P1/P6 的 review 流程留缓冲。

---

## 4. 执行顺序与关键路径

```text
P0 阻断/契约
   ↓
P1 目标/效果层/音擎 ──┬── P2 循环/倍率/异常 ── P3 优化器 ── P4 评分/相对值/报告
                       │                                      ↓
                       └────────────── P5 前端/文档 ──────────┘
                                                              ↓
                                                        P6 铺开 61 人
                                                              ↓
                                                        P7 性能/CI/收尾
```

**关键路径**：P0 → P1 → P2 → P3 → P4 → P5 → P6。

可并行：

- P5 的 Vite/API 骨架可在 P4 schema 确定后先做；
- P6 的 Tier A 可在 P2/P3 完成后分批开始，不必等全部 61 份；
- P2-4 的紊乱纯函数与 P3 无依赖，可提前做；
- P4-1 的评分可在 P3-1 可行性完成后先做。

**里程碑**：

| 里程碑 | 完成条件 | 可对外 |
| --- | --- | --- |
| M1 | P0 + P1 + 3 个试点 | 内部：专武 vs 下位能算 |
| M2 | P2 + P3 + 菲欧妮 report | 内部：最优面板 + 曲线 |
| M3 | P4 + P5 | 可发布：策略页数值表 |
| M4 | P6 Tier A | 可发布：36 名伤害角色 |
| M5 | P6 全部 + P7 | v1 完成 |

---

## 5. 数据迁移与兼容

| 项 | 策略 | 回滚 |
| --- | --- | --- |
| 现有 `strategy/*.strategy.json` | **不改**已有字段；只新增 `calculator/` 目录 | 删除目录即回滚 |
| `graduationPanel` | 保持现状；由 `calculator.json` 复算后 `--check` 比对 | 保留旧 JSON |
| `buildSpec` | 从 `calculator.json` + 固定配装重建；不手填 | 旧字段仍在 |
| 报告 404 | 策略页整段隐藏；不影响首屏 | 删除 `report.json` |
| `compare_service` / `substat_benefit` | P0 修复后保留；P3 起逐步改为读 `calculator.json`，避免两套引擎 | 保留旧入口 |
| `impact_pct_24` | 独立数据修正，不混入本计划；按 D-1 数据快照流程 | 规则表回滚 |
| 61 份铺开 | Tier A → B → C → 特殊；每批 `--check` | 按批删除 `calculator/` |
| Worker 数据 | 报告是静态资源，不进 `_bundled_data.py`；`bundle_worker_data.py --check` 不受影响 | 无需改 Worker |

**迁移顺序**：

1. P0-7 先修 1 个试点 `buildSpec`，证明可复算；
2. P1 三个试点生成 report；
3. P6-1 Tier A 36 份；
4. P6-2 / P6-3 支援/防护/击破；
5. P6-4 特殊机制。

---

## 6. 验收与测试

### 6.1 命令

```powershell
uv run pytest backend/tests -q
cd frontend; npm run test; npm run build
python tools/check_docs.py
python tools/sync_manifest.py --check
python tools/bundle_worker_data.py --check
python .github/skills/agent-strategy/scripts/calc_graduation_panel.py --check-all
python tools/agent_audit.py --all
# P3/P4 之后：
python tools/build_agent_calculator.py phoenix --check
python tools/score_disc.py phoenix --check
```

### 6.2 测试矩阵

| 层 | 测试 | 关键断言 |
| --- | --- | --- |
| 目标 | `test_damage_targets.py` | 白板 `0.454545…` / 2.5 / 1.0；`fixed_defense` |
| 效果 | `test_damage_effects.py` | 精炼数组、层数、uptime、条件、属性过滤、快照/实时 |
| 循环 | `test_rotation.py` | 倍率解析、等级、id、路径块、覆盖率 |
| 优化 | `test_optimizer.py` | N≤12 全枚举；可行性；单调；确定性 |
| 评分 | `test_disc_score.py` | 公式、cap、锚点、`damageRatio` |
| 报告 | `test_calculator_report.py` | schema、hash、stale、404 |
| 前端 | `calculator-report.spec.ts` | 表格、partial、404 隐藏 |
| 数据 | `test_presets.py` / `test_strategy_data.py` | effect 形状、影画 hash、manifest |

### 6.3 Golden 文件策略

`strategy/<slug>/calculator/golden.json` 的结构：

```jsonc
{
  "schemaVersion": 1,
  "agentId": "ep-2216",
  "cases": [
    { "id": "C0R1", "mode": "mixed", "relative": 100.0, "tolerance": 0.05, "status": "modeled" },
    { "id": "twin-ep-212-r5-2stacks", "mode": "anomaly-only", "relative": 83.57, "tolerance": 0.05, "status": "partial" }
  ],
  "generatedAt": "…",
  "note": "人工 review 后提交；不要用 --update-golden 直接覆盖。"
}
```

- 每个 agent 保存**已 review** 的用例：`C0R1`、一个下位音擎、一个影画、一个非满配预算；
- `mode` 是测试选择器：`mixed`（默认）/ `anomaly-only` / `direct-only`，用于把同一份
  calculator 的口径拆开验证；生产报告始终用 `mixed`；
- 生成命令 `--update-golden` **不自动提交**；必须人工看 diff；
- CI 用相对值比较，容差 **0.05%**；绝对伤害容差 0.1%；
- 未建模项变化（`status` / `coverage`）也要 diff，不能只看数值。

### 6.4 与参考实现交叉

- 同一简单直伤角色、同一白板目标，与 `ZZZ-HP` / `zzz_calculator` 对比；
- 差异 < 2% 或每个差异有书面解释；
- 锋御锐爆基础（150% vs 参考 1.2）在核对前**不直接对比**。

---

## 7. 风险与对策

| 风险 | 影响 | 对策 |
| --- | --- | --- |
| 效果文本歧义 | 覆盖率/层数拍脑袋 | `condition` + `stacks` + `uptime` 显式；报告展示；敏感性 |
| 循环假设主导 | 换循环排序变 | 循环写进 calculator；`rotation.md`；至少两组循环对照 |
| 束搜索漏解 | 「最优」不是真最优 | 小预算穷举；多起点；局部搜索；报告写 best found |
| 可行性遗漏 | 给出刷不出的分配 | §28.6.2 硬约束；不可行直接丢弃 |
| 面板/局内泄漏 | 三方对拍坏 | `Effect.phase` + W5；面板接口不接受 effect |
| 属性过滤遗漏 | 火伤打物理事件 | `damageType` + W6；逐事件断言 |
| 61 份工作量 | 铺开拖长 | Tier 分批；模板 + 自动校验；支援/防护先 `personal-only` |
| 支援/击破被误读 | 用个人伤害评价角色 | `scopeNote` / caveat；不参与跨角色排名 |
| 数据漂移 | 报告过期 | `calculatorHash` / `sourceSha256` / `sourceTextHash` + `--check` |
| 性能 | 61×多预算太慢 | 缓存、并行、只跑需要的预算、增量 |
| 紊乱/风/耀变未实现 | 相关角色算不全 | 明确 `descriptive` / 独立计划，不静默 0 |

---

## 8. 交付物与 DoD

### 8.1 代码 / 数据

| 类型 | 交付物 |
| --- | --- |
| 目标 | `WHITEBOARD_TARGET` + 敏感性目标 + `fixed_defense` / `distance_falloff` / `stunned_default` |
| 效果 | 拟新增 backend/src/zzz_panel/core/damage/effects.py（目标注册表、条件、层数、覆盖率、快照） |
| 循环 | 拟新增 backend/src/zzz_panel/core/damage/rotation.py（事件、倍率、校验、patch） |
| 服务 | 拟新增 backend/src/zzz_panel/services/optimizer_service.py、disc_score_service.py、calculator_service.py |
| 工具 | 拟新增 tools/parse_skill_multipliers.py、build_agent_calculator.py、score_disc.py |
| 数据 | `weapons.json` 的 `effect`；`drive-discs.json` 的 `effect4`；拟新增 data/catalog/agent-mechanics.json |
| 档案 | `strategy/<slug>/calculator/calculator.json` + `golden.json` + `report.json` |
| 前端 | `vite.config.ts`、`api/strategy.ts`、`StrategyView.vue`、`renderStrategy.ts`、`strategy.css` |
| 文档 | 设计指南 §28、本计划、`strategy/README.md`、`data-schema.md`、`api-reference.md`、`requirements.md`、`testing.md`、`changelog.md` |
| 测试 | 新增 §6.2 的 8 组测试 |

### 8.2 单代理人 DoD

- [ ] `calculator.json` 严格校验通过；
- [ ] 至少 1 武器 + 1 影画 + 1 非满配；
- [ ] `golden.json` 人工 review；
- [ ] `report.json` 的 `status` / `coverage` / `assumptions` 完整；
- [ ] 策略页可渲染；404 可回退；
- [ ] `--check` 通过；
- [ ] 未建模项写入 `warnings` / `scopeNote`。

### 8.3 项目 DoD

- [ ] 36 名伤害向有 `modeled` / `partial` 报告；
- [ ] 13 支援/防护 + 12 击破有 `personal-only` + caveat；
- [ ] 特殊机制至少 `descriptive`；
- [ ] 全量 CI 绿；
- [ ] `check_docs` 无新增断链；
- [ ] 性能目标达标；
- [ ] 遗留项/下一阶段清单完成。

---

## 9. 附录

### 9.1 菲欧妮示例的定位

设计指南 §23.6 的菲欧妮表是**示例口径**（纯异常、2 层双生、54 条攻略面板），
用于验证方法和「83%」这个经验值。正式 `report.json` 用 `mixed` 循环、实际异常触发次数、
4 件套与音擎层数假设；两者数字会不同，**不要把手算示例当 golden**。

### 9.2 命令速查

| 目的 | 命令 |
| --- | --- |
| 后端测试 | `uv run pytest backend/tests -q` |
| 前端测试 | `cd frontend; npm run test` |
| 前端构建 | `cd frontend; npm run build` |
| 文档闸门 | `python tools/check_docs.py` |
| 数据登记 | `python tools/sync_manifest.py --check` |
| Worker 产物 | `python tools/bundle_worker_data.py --check` |
| 毕业面板 | `python .github/skills/agent-strategy/scripts/calc_graduation_panel.py --check-all` |
| 新：单角色报告 | `python tools/build_agent_calculator.py <slug> --check` |
| 新：单盘评分 | `python tools/score_disc.py <slug> --check` |

### 9.3 仍未定的问题（后续计划）

| 问题 | 现裁决 | 后续 |
| --- | --- | --- |
| 时间轴 / Buff 窗口 | 作者填 uptime | v2 加 `startTime` / `buffWindows` |
| 队伍 Buff / 队友快照 | v1 不做 | 独立计划；冻结快照 |
| 能量循环 | v1 不校验 | 独立计划 |
| 紊乱引擎 | 只做倍率纯函数 | 独立计划（需时间项） |
| 风 / 耀变 / 异放 | schema 预留，不结算 | 独立计划 |
| 支援/防护团队价值 | 只算个人伤害 | 需要队伍模型后另算 |
| 锋御锐爆基础 150% vs 1.2 | 按本项目 150% | 官方原文核对 |
| 6 号位冲击力 24% vs 18% | 数据修正另行处理 | 按 D-1 数据快照流程 |
