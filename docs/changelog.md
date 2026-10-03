# 变更记录

记录影响使用方式或正确性的变更。纯内部重构不逐条记录，见
[git 历史](https://github.com)。

版本号见 `pyproject.toml` 与 `frontend/package.json`，当前均为 `0.1.0`。

## 2026-10-03 · Vue3 迁移收尾（第 5 步）

### 删除

| 变更 | 说明 |
| --- | --- |
| **删除「标准版示例」页** | 原 `/example` 路由与其视图整体移除。该页复制了一整套计算逻辑与预设值，与统一计算器完全重复。启动页入口卡片、路由、`ResultPanel` 中仅供它使用的插槽一并删除 |
| **删除 `frontend/legacy/`** | 迁移前的原生 HTML 实现。`index.html`、`guide.html`、`example-template.html`、`redirect-*.html` 均已分别被 Vue3 页面或路由 query 取代 |
| **删除仓库根目录 6 个中文重定向页** | 纯 `meta refresh` 兼容桩，现直接访问 `/` |

> ⚠️ **`data/agent-presets.js` 与 `data/weapon-presets.js` 仍然保留**，
> 但已移到 `frontend/tests/fixtures/legacy-calculator/data/`，
> 身份从「legacy 页面的数据」变为「只读对拍夹具」。删掉它三方对拍就跑不起来。

### 保留护栏

| 变更 | 说明 |
| --- | --- |
| 计算部分改为只读夹具 | 用 `git mv` 把对拍真正需要的 6 个文件移到 `frontend/tests/fixtures/legacy-calculator/`，保留 `pages/ data/ scripts/ styles/` 结构。新增该目录的 README 写明「禁止修改」 |
| 5 处消费者改路径 | `legacy-parity.spec.ts`、两个诊断脚本、`sync_presets.py`、`refresh_agent_presets.py` 的 `--config` 默认值 |
| **修掉一处假绿灯** | `test_fmt_parity.py` 原在 Node 退出码非 0 时 `pytest.skip`。基准文件缺失会命中这条路径——测试不报错但检查已失效。现改为只有 Node 不可用才 skip |

### 新增

- `/guide` 学习指南页（吸收旧 `guide.html` 全文），配套 4 个展示组件
- `docs/completeds/` 归档目录

### 文档

`docs/` 从 7 篇扩为 9 篇 + 2 篇归档。新增需求说明、接口文档、开发指南、
测试策略、部署指南、变更记录；修正 `data-schema.md` 中与实现不符的接口章节。

## 2026-10-03 · 预设数据改造为 JSON（第 4 步）

| 变更 | 说明 |
| --- | --- |
| 预设改走 `GET /api/presets/*` | 前端不再持有 160 条预设副本，构建产物从 182.90 kB 降到 128.97 kB |
| 新增 `data/agent-presets.json`（60 条）<br>`data/weapon-presets.json`（100 条） | 由 Skill 抓取脚本生成，是唯一真实源 |
| 配装规则表改为 `data/options.json` | 由 `core/options.py` 单向生成。前端经 `@data` 别名直接 import，下拉框无需等 HTTP |
| **选项从数组下标改为稳定 id** | 预存在后端、选项表在前端，两者不再需要共享同一份数组顺序 |
| 新增 `tools/sync_presets.py` | `--from-legacy` / `--to-legacy` / `--options` / `--check` 四模式，往返字节一致 |
| 后端新增 `presets/` | `loader.py` 按 mtime 缓存；`validate.py` 全量语义校验，失败整份拒绝 |
| 前端删除 `src/data/*.ts` | 数据不再有前端副本 |

> 预设走接口、规则表走本地是**故意不对称**：前者数据量大且需刷新，
> 后者要瞬时可用。理由与论证见 [architecture.md](architecture.md)。

## 2026-10-02 · 计算下沉到 Python（第 3 步）

**这是本项目唯一一次会改变数值正确性的变更。**

| 变更 | 说明 |
| --- | --- |
| 计算全部移到 `backend/src/zzz_panel/core/` | 前端不再做任何算术，只传「选了什么」 |
| 新增 `POST /api/panel/calc` | 请求只含选择项，响应含 12 行 `totals` 与结构化 `breakdown` |
| 明细改为结构化片段 | 后端不输出中文文案，格式化与换行留在前端 |
| 新增 `services/panel_service.py` | 网页与命令行共用同一份规则 |
| 新增三方对拍 | 旧 JS ≡ Vue3 页面 ≡ Python 后端，逐字符比对 |

## 2026-10-02 · 前端搭建（第 0～2 步）

- 第 0 步：Vite + Vue3 + TS 工程骨架，业务逻辑仍在前端计算
- 第 1 步：静态结构（无计算），`?mode=` 提升为路由 query，命破/锋御从独立页合为统一计算器
- 第 2 步：交互逻辑迁移到 Pinia store 与 composable

## 后续计划

见 [requirements.md](requirements.md) 第 7 节「已知限制」——
那里列出的死代码与不一致项都是可清理的重构候选。

## 相关文档

- [requirements.md](requirements.md) —— 项目范围与已知限制
- [architecture.md](architecture.md) —— 架构与设计决策
- [completeds/migration-vue3.md](completeds/migration-vue3.md) —— 迁移全过程记录