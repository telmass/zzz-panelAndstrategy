# 结构审查（历史归档）

> **状态：已归档（2026-10-18）**
> 本文档是 2026-10-13 至 2026-10-17 期间的结构审查记录。所列问题均已修复或
> 转入 `docs/repair-plan.md`。当前技术债以 repair-plan 为准。

## 归档原因

原文档混合了「当前问题描述」与「修复后状态」，随着修复推进，内容自相矛盾
（标题说"已修复"但正文还在描述旧状态）。为避免误导，改为纯历史记录。

## 当时发现并已修复的核心问题

| 问题 | 修复方式 | 完成时间 |
| --- | --- | --- |
| P0-1 数据命名 | 29 个目录的数据文件改为 `<slug>.json` / `<slug>.strategy.json`；删除遗留 `~~strategy/ye-shun-guang/~~ (now ye-shunguang)` | 2026-10-13 |
| P1-1 身份数据三处重复 | `strategyGuides.ts` 由生成器统一维护 | 2026-10-14 |
| P1-2 模板重复 | 删除 177 份 per-page `index.html/app.js/styles.css`；攻略页迁入 Vue 路由 | 2026-10-15 |
| P1-3 图片散布 | 全部归位 `frontend/public/images/`，JSON 引用统一 `/images/…` | 2026-10-13 |
| P1-4 文档漂移 | 数量/路径以 `project-overview.md` 当前规模表为准；后续由 `docs/repair-plan.md` 跟踪 | 2026-10-14 |
| P2-1 worktrees 累积 | `.kilo/worktrees` 已清空（本地操作） | 2026-10-15 |
| P2-2 guide 硬编码 | GuideView.vue 保留（内容抽取列入 repair-plan P2-19） | — |
| P2-3 根目录杂物 | `utf8_report.json` 已在 repair-plan P2-9 中处理 | — |

## 遗留（已转入 repair-plan）

- 毕业面板不可复现 → repair-plan P0-3
- CLI 格式化不走 core → repair-plan P2-10
- renderStrategy.ts 单体 → repair-plan P2-13
- GuideView 内容硬编码 → repair-plan P2-19
- 图片未压缩 → repair-plan P2-18

## 历史上下文

<details>
<summary>展开原始审查描述（已过时，仅供追溯）</summary>

当时 `strategy/` 目录下有 29 个代理人各有一套 `index.html / app.js / styles.css`，
加上共享的 `strategy/_shared/` 目录。图片散布在多个 `assets/` 子目录中，
JSON 引用使用页相对路径而非 `/images/…` URL。

这些结构已在 Vue 迁移（2026-10-15）中彻底移除。

</details>
