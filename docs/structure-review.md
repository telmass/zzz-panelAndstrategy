# 结构审查：问题与解决方案

审查时间：2026-10-18。范围：仓库目录结构、数据命名与编码、攻略页模板、文档体系、测试护栏。
本文**只记录问题与建议**，不表示修复已完成；每项给出证据、影响、解决方案与验收标准。

优先级：P0 = 已导致测试红灯或线上数据错误；P1 = 高概率产生漂移或维护成本失控；
P2 = 整洁度与长期演进问题。

## 修复状态（2026-10-18）

| 项 | 状态 | 说明 |
| --- | --- | --- |
| P0-1 数据命名 | **已修复** | 29 个目录的数据文件已改为 `<slug>.json` / `<slug>.strategy.json`；删除遗留 `strategy/ye-shun-guang/`；JSON 引用同步 |
| P0-2 UTF-8 | **已修复** | 21 份坏 JSON 已从官方 Wiki 重新抓取；全仓库攻略 JSON 可用 UTF-8 读取 |
| P0-3 测试红灯 | **已修复** | 后端 306 项全绿、前端 112 项全绿；音擎计数改为从 `data/*.json` 动态读取 |
| P1-1 身份数据副本 | **已修复** | `strategyGuides.ts` 改由 `tools/gen_strategy_guides.py` 从 mapping + 攻略数据生成；新增 `--check` 与一致性测试 |
| P1-2 模板重复 | **已修复** | 删除 177 份 per-page `index.html/app.js/styles.css`；攻略页迁入 Vue 路由 + `strategy/renderStrategy.ts` + 单一 `strategy.css`，去掉 iframe |
| P1-3 图片命名 | **已修复** | 属性 / 职业图标统一为小写 ASCII slug，数据、登记表、Skill 与文档同步 |
| P1-4 文档漂移 | **已修复** | 新增集成总览与结构审查，重写索引，校准数量与路径 |
| P2 整洁度 | **部分处理** | 已删除遗留攻略目录、58 份 `requirements.txt` 与空资源目录；`.kilo/worktrees` 清理仍待做 |

---

## P0-1. 攻略数据命名与规范 slug 不一致（29 个目录）

### 现状

`data/agent-name-mapping.json` 是规范 slug 的唯一来源，`strategyGuides.ts` 的 59 条
登记项全部与 mapping 一致。但 `strategy/<slug>/data/` 下仍有 29 个目录沿用旧拼音 /
旧 slug 文件名：

| 目录 | 实际数据文件 | 规范文件 |
| --- | --- | --- |
| `anby` | `an-bi.json` / `an-bi.strategy.json` | `anby.*` |
| `anton` | `an-dong.*` | `anton.*` |
| `astra-yao` | `yao-jia-yin.*` | `astra-yao.*` |
| `billy` | `bi-li.*` | `billy.*` |
| `burnice` | `berise.*` | `burnice.*` |
| `corin` | `ke-lin.*` | `corin.*` |
| `ellen` | `ai-lian.*` | `ellen.*` |
| `evelyn` | `yi-a-lin.*` | `evelyn.*` |
| `grace` | `ge-li-si.*` | `grace.*` |
| `harumasa` | `you-zhen.*` | `harumasa.*` |
| `jane` | `jane-doe.*` | `jane.*` |
| `koleda` | `ke-lei-da.*` | `koleda.*` |
| `lighter` | `laite.*` | `lighter.*` |
| `lucy` | `lu-xi.*` | `lucy.*` |
| `lycaon` | `le-ka-en.*` | `lycaon.*` |
| `manato` | `zhen-dou.*` | `manato.*` |
| `miyabi` | `xing-ji-ya.*` | `miyabi.*` |
| `nekomata` | `mao-you.*` | `nekomata.*` |
| `nicole` | `ni-ke.*` | `nicole.*` |
| `pan-yinhu` | `pan-yin-hu.*` | `pan-yinhu.*` |
| `piper` | `pai-pai.*` | `piper.*` |
| `pulchra` | `bo-ke-na.*` | `pulchra.*` |
| `rina` | `li-na.*` | `rina.*` |
| `seth` | `sai-si.*` | `seth.*` |
| `soldier-11` | `shi-yi-hao.*` | `soldier-11.*` |
| `soukaku` | `cang-jiao.*` | `soukaku.*` |
| `yanagi` | `yue-cheng-liu.*` | `yanagi.*` |
| `ye-shunguang` | `ye-shun-guang.*` | `ye-shunguang.*` |
| `ye-shun-guang`（遗留目录） | `ye-shun-guang.json`（无 strategy 文件） | 应删除 |

另有 8 个文件内的 `/images/strategy/<old>/` 仍指向旧目录名：
`astra-yao`、`lucy`、`manato`、`nicole`、`rina`、`soukaku`、`sunna`（`qian-xia`）、
`ye-shunguang`（`ye-shun-guang`）。

### 影响

- `backend/tests/test_strategy_data.py` 按 `<slug>/data/<slug>.json` 读取，29 个目录直接
  `FileNotFoundError`；这是当前 60 个后端失败中的绝大多数。
- `agent-strategy` / `fix-agent` Skill 都声明「规范 slug 优先」，但实际数据违反契约，
  新人照文档操作会继续制造同类错误。
- 旧图片目录名不存在时，攻略页 hero / 立绘会静默缺图。
- `strategy/ye-shun-guang/` 是重复且内容不同的遗留目录（209,628 B vs 规范目录 209,683 B），
  会让测试参数化多跑一遍并持续报错。

### 解决方案

1. **建立迁移脚本**（建议 `tools/normalize_strategy.py`，只做机械重命名）：
   - 读取 `data/agent-name-mapping.json` → `slug`；
   - 对每个 `strategy/<dir>/data/*.json`，把旧文件名重命名为 `<slug>.json` / `<slug>.strategy.json`；
   - 把两个 JSON 内所有 `/images/strategy/<old>/` 替换为 `/images/strategy/<slug>/`；
   - 同步改写 `app.js` 的 `DATA_URL` / `STRATEGY_URL`；
   - 删除遗留 `strategy/ye-shun-guang/`（先比对并确认其内容已被规范目录覆盖）。
2. **一次性全量执行**后跑：
   ```powershell
   .venv\Scripts\python.exe -m pytest backend/tests/test_strategy_data.py -q
   cd frontend; npm run test; cd ..
   ```
3. **加护栏**（防止再次漂移）：新增一个轻量 pytest（或 CI 脚本），断言：
   - 每个 `strategy/<slug>/` 的目录名在 `agent-name-mapping.json` 中；
   - `data/` 恰好有 `<slug>.json` 与 `<slug>.strategy.json`；
   - 两个 JSON 内 `/images/strategy/` 前缀只能是 `<slug>`；
   - `strategyGuides.ts` 的 slug 集合 = 目录集合。
4. **验收**：`test_strategy_data.py` 0 失败；无 `ye-shun-guang` 目录；`strategyGuides.ts`、
   mapping、目录、数据文件名四者完全一致。

---

## P0-2. 21 份攻略抓取 JSON 不是合法 UTF-8

### 现状

以下文件用 `utf-8` 读取即失败（`invalid continuation byte`）：

`anby`、`anton`、`billy`、`burnice`、`corin`、`ellen`、`evelyn`、`grace`、`harumasa`、
`jane`、`koleda`、`lighter`、`lycaon`、`miyabi`、`nekomata`、`pan-yinhu`、`piper`、
`pulchra`、`seth`、`soldier-11`、`yanagi` 的抓取 JSON。

典型坏点位于 `profile.name` 附近（如 `安比·德玛?` 缺字），说明文本在写入链路中丢过字节，
不是合法的 GBK/GB18030 文件，无法靠换编码完整还原。

### 影响

- Python 测试无法读取；浏览器 `response.json()` 会以替换字符（U+FFFD）解码，页面出现错字，
  但不会抛错——属于**静默数据损坏**。
- 攻略页中的姓名、称号、技能文本可能永久缺字。
- 后续自动重命名 / 批量替换脚本若按 UTF-8 处理会再次破坏文件。

### 解决方案

1. **以抓取脚本重新生成**这 21 份 `<slug>.json`（联网读官方 Wiki），不要尝试手工修字节；
   重抓前先完成 P0-1 的规范命名。
2. 抓取脚本写文件时显式 `encoding="utf-8"`、`ensure_ascii=False`，并在写完后立刻
   `json.loads(path.read_text(encoding="utf-8"))` 自检。
3. 在 `test_strategy_data.py` 增加一条参数化断言：所有 `strategy/**/data/*.json` 必须是
   合法 UTF-8 且可 `json.loads`。
4. **验收**：全仓库 `python -c "…read_text(encoding='utf-8')"` 无异常；浏览器页面无 `�`。

---

## P0-3. 后端测试红灯，文档却宣称全绿（已修复）

### 修复前

```
244 tests collected
184 passed
60 failed
```

失败集中在：

- `test_strategy_data.py`：58 项（29 个旧命名目录 × 2 个参数化用例）；
- `test_worker_bundle.py::test_repo_data_wins_over_compiled_module`：音擎实际 101 条，
  测试与文档仍写 100；
- `test_presets.py`：`assert 101 == 100`。

而 `README.md`、`docs/testing.md`、`backend/tests/README.md` 仍写「136 项 / 0 skip / 全绿」。
当时前端 108 项全绿。

### 影响

- 新成员按文档执行会误以为环境坏了。
- CI / 提交门禁失去可信度；「测试全绿」不再是可用信号。
- 数量变化（101 把音擎）没有被测试与文档同步。

### 解决方案

1. 先完成 P0-1 / P0-2，再修正测试中的硬编码数量：
   - 把 `100` 改为从 `data/weapon-presets.json` 读取长度，或明确更新为 101；
   - 避免在测试与文档中重复写死数据规模。
2. 增加最小 CI（GitHub Actions 或本地 `tools/check.ps1`）：
   `pytest` → 前端 `typecheck` / `test` → 三条漂移闸。
3. 文档只写「命令 + 当前实测数字」，不再写「必然 136 项」；把数量断言集中到
   `docs/project-overview.md` 的「当前规模」表。
4. **验收**：`pytest` 306/306；文档数字与命令输出一致；CI 红灯能阻断合并。

---

## P1-1. 代理人身份数据有四份副本（已修复）

### 修复结果

`strategyGuides.ts` 现在由 `tools/gen_strategy_guides.py` 生成，输入是
`data/agent-name-mapping.json` + `strategy/<slug>/data/<slug>.json`（必要时用 presets 兜底）。
新增 `--check` 与目录 / 数据 / 登记表一致性测试；新增代理人不再手改 TS 数组。

### 修复前

同一名代理人至少在以下位置重复：

1. `data/agent-name-mapping.json`：`slug` / `en` / `cn_short` / `cn_full`；
2. `data/agent-presets.json`：`id` / `name` / `attribute` / `roleTag` / `grade`；
3. `frontend/src/constants/strategyGuides.ts`：`slug` / `name` / `en` / `agentId` / 图标 URL；
4. `strategy/<slug>/index.html` 与 `app.js`：标题、姓名、`DATA_URL`、头像/立绘路径；
5. `strategy/<slug>/data/<slug>.json`：`meta` / `profile` 又有一份。

`strategyGuides.ts` 639 行、每条 8 个字段，新增代理人必须手工同步，已经出现
`ye-shun-guang` / `ye-shunguang`、`qian-xia` / `sunna`、`orphe-magus` / `orphie-magus`
等历史漂移。

### 影响

- 新增 / 改名代理人需要改 4–5 处，漏一处就出现「卡片有、页面 404」或「图标 404」。
- 不同来源对同一代理人的属性/职业/评级可能不一致，且没有编译期检查。

### 解决方案（按成本从低到高）

1. **最低成本：生成 + 校验。** 新增 `tools/gen_strategy_guides.py`：
   - 以 `agent-name-mapping.json` + `agent-presets.json` + `strategy/<slug>/data/<slug>.json`
     为输入，生成 `strategyGuides.ts`（或生成 JSON，再由 TS 读取）；
   - CI 跑 `--check`，登记表与数据不一致即失败。
2. **中等成本：运行时只读数据。** 把登记表改为构建期生成的 `strategy-guides.json`，
   `StrategyPickerView` 直接 import；不再维护手写 TS 数组。
3. **长期：主应用路由数据化。** 让 `/strategy/:slug` 直接读两份 JSON 渲染，取消 iframe
   与每页一份 `app.js`（见 P1-2），登记表可由 `strategy/` 目录自动发现。

**验收**：新增代理人只需「建目录 + 放数据 + 跑生成脚本」，`--check` 为 0；
`strategyGuides.ts` 不再手工编辑。

---

## P1-2. 攻略页模板复制 59 份，修一次要改 59 处（已修复）

### 修复结果

- 删除 59 个目录下的 `index.html / app.js / styles.css`（共 177 个文件）；
- 新增 `frontend/src/strategy/renderStrategy.ts`（唯一渲染器）与
  `frontend/src/strategy/strategy.css`（唯一一份样式，收窄在 `.strategy-detail`）；
- `StrategyView.vue` 直接拉取 `/strategy/<slug>/data/*.json` 并挂载渲染器，去掉 iframe；
- `vite.config.ts` 改为 `strategyDataPlugin`，只服务 / 拷贝两份 JSON；
- 新增 `strategy-view.spec.ts`，逐个渲染登记表内全部 59 名代理人的数据。

> 迁移保留原 DOM 结构与 CSS，只把选择器收窄到 `.strategy-detail`；测试能捕获数据 / 渲染
> 异常，但未做像素级截图对比。若后续要改视觉，建议先补 Playwright 截图基线。

### 修复前

- `strategy/*/app.js` 59 份，每份约 40 KB，**哈希两两不同**，但差异基本只有
  `DATA_URL` / `STRATEGY_URL` 与注释中的 slug；
- `styles.css` 58 份完全相同（约 40 KB），`roxy` 一份不同；
- `index.html` 59 份，每份只差 `<title>` / `<meta description>`；
- 曾有 58 份 `strategy/<slug>/requirements.txt`（内容均为 `requests` + `beautifulsoup4`），
  与页面运行无关；已在本次修复中删除，依赖统一由根 `pyproject.toml` 管理。

粗略重复体积：`59 × 40 KB (JS) + 59 × 40 KB (CSS) ≈ 4.7 MB`，构建时还会整体复制进
`frontend/dist/strategy/` 并上传到 Cloudflare Assets。

### 影响

- 任何页面逻辑 / 样式修复都要同步 59 份，实际已经出现 `roxy` 样式漂移与多份 `app.js`
  仍引用 `ye-shun-guang` 的情况。
- 审核困难：无法判断某份 copy 是「有意定制」还是「忘记同步」。
- 构建产物与部署体积随代理人数线性增长。

### 解决方案

1. **共享模板（改动最小）**：
   - 新增 `strategy/_shared/{app.js,styles.css}`；
   - 每个 `strategy/<slug>/index.html` 只保留
     `<div id="app" data-slug="<slug>"></div>` 并引用 `../_shared/app.js`；
   - `app.js` 从 `document.getElementById('app').dataset.slug` 推导
     `data/<slug>.json` / `data/<slug>.strategy.json`；
   - `vite.config.ts` 的 `strategyPagesPlugin` 额外放行 `/strategy/_shared/*`，构建时只拷一份。
2. **彻底方案**：把攻略页迁进 Vue 路由（`StrategyView` 直接读 JSON 渲染），删除
   `strategy/<slug>/index.html|app.js|styles.css` 与 iframe；静态页仅保留数据与图片。
   这样还能复用主应用的组件、主题与路由，消除 iframe 高度/滚动同步问题。
3. 删除每目录 `requirements.txt`，抓取依赖统一放 `.github/skills/*/requirements.txt`
   或根 `pyproject.toml`。
4. **验收**：`strategy/` 下无重复 `app.js` / `styles.css`；改一次样式所有页面生效；
   `dist/strategy/` 体积显著下降；前端测试覆盖攻略页渲染。

---

## P1-3. 图片命名规范（已修复）

### 修复前

- 属性：`Honed Edge.png`、`Auric Ink.png`、`Wind.png`…（10 张，含空格 / 首字母大写）；
- 职业：`Attack.png`、`Armorer.png`…（7 张，首字母大写）；
- 文档、Skill、数据对同一概念使用不同写法。

### 修复后

- 属性统一为 `honed-edge.png`、`auric-ink.png`、`wind.png`…；
- 职业统一为 `attack.png`、`armorer.png`…；
- `strategyGuides.ts`、全部攻略 JSON、`useCascaderIcons.ts`、Skill 文档与
  `docs/directory-layout.md` 已同步；
- 一致性测试会检查攻略 JSON 中的图片 slug 只能是当前目录，并校验数据文件可读。

### 残留风险

- 抓取脚本的属性图标映射仍需在新增属性时人工补文件；文件名必须保持小写 slug。
- `frontend/public/images/` 中其他目录（agents / weapons / discs）已是 `ep-<id>` 命名，
  不受本次改动影响。

---

## P1-4. 文档体系重复且与代码漂移

### 现状

- 同一组命令在 `README.md`、`docs/development.md`、`docs/deployment.md`、`tools/README.md`
  各写一遍，且测试数量、音擎数量、攻略页数量互相矛盾；
- `docs/testing.md` 写「121 / 90 / 211」，后文又写「136 / 108」，实际是 244 / 108；
- `docs/directory-layout.md` 仍说「当前只有叶瞬光、般岳两个攻略页」「213 张图片」；
- `docs/requirements.md` 手工验收仍只列 `/strategy/ye-shun-guang`、`/strategy/ban-yue`；
- `strategy/ye-shunguang/README.md` 是「攻略页模板契约」，却把文档放在某一代理人的数据目录里，
  且仍使用旧 slug；
- `docs/README.md` 未收录 `agent-background`、`fix-agent` 两个新 Skill。

### 影响

- 新人无法判断哪份文档是最新；文档承诺与测试现实不符，降低可信度。
- 修改一处事实需要改 4–6 个文件，必然继续漂移。

### 解决方案

1. 以 [project-overview.md](project-overview.md) 为**唯一集成总览**；
   `docs/README.md` 降级为「索引 + 文档维护规则」，不再复制事实。
2. 每个专题只保留一个权威位置：
   - 数量 / 路径 → `project-overview.md`；
   - 命令 → `development.md`；
   - 接口 → `api-reference.md`；
   - 数据字段 → `data-schema.md`；
   - 测试策略 → `testing.md`；
   - 部署 → `deployment.md`；
   - 结构问题 → 本文。
3. 其他文档用链接代替复制；历史数字只保留在 `changelog.md`，并标注「当时状态」。
4. 把 `strategy/ye-shunguang/README.md` 迁为 `strategy/README.md`（模板契约），
   Skill 文档统一引用它；参考实例统一写 `strategy/ye-shunguang/`。
5. **验收**：全文搜索 `136 项`、`213 张`、`ye-shun-guang`、`ban-yue` 不再命中当前状态描述
   （changelog / 归档除外）。

---

## P2-1. 空目录与遗留文件

| 项 | 问题 | 建议 |
| --- | --- | --- |
| `.kilo/worktrees/` | Agent Manager 的本地工作树副本，含旧代码与大目录 | 不提交；定期在 Agent Manager 清理，不要手工编辑 |

> 已处理：删除 `strategy/ye-shun-guang/`、58 份 `strategy/<slug>/requirements.txt`，
> 以及空的 `frontend/src/assets/fonts/`、`frontend/src/assets/images/`。

---

## P2-2. 攻略页与主应用的边界（已修复）

修复前 `/strategy/:slug` 用 iframe 嵌入静态页，导致：

- 主应用与攻略页各自维护导航、主题、滚动与「回到顶部」；
- 无法共享 Vue 组件与类型；
- iframe 高度、深链、打印、无障碍都需要额外处理；
- 静态页模板复制问题（P1-2）无法根治。

**已实施**：攻略页迁入 Vue 路由（`StrategyView.vue` + `strategy/renderStrategy.ts` +
`strategy.css`），`strategy/<slug>/` 只保留数据；59 个代理人共用一套渲染与样式。

---

## 建议的修复顺序

| 阶段 | 动作 | 验收 |
| --- | --- | --- |
| 1 | P0-1 命名归一 + 删除遗留目录 | `test_strategy_data.py` 不再因缺文件失败 |
| 2 | P0-2 重新抓取 21 份坏 JSON + UTF-8 自检 | 全仓库 JSON 可 `utf-8` 读取 |
| 3 | P0-3 修正硬编码 100 → 101 / 动态读取 | `pytest` 306/306，前端 112/112 |
| 4 | P1-1 生成登记表 + `--check` | 新增代理人只改数据 |
| 5 | P1-2 共享攻略模板 / 去 iframe | 模板只保留一份 |
| 6 | P1-3 图片命名统一 + 存在性测试 | 文档/数据/文件一致 |
| 7 | P1-4 文档去重 + CI | 文档数字与命令输出一致 |

阶段 1–7 已完成；CI 见 `.github/workflows/ci.yml`（数据漂移闸 + 后端 / 前端测试 + 构建）。
