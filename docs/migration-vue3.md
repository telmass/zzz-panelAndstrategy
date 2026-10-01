# Vue3 迁移指南

原方案：`.kilo/plans/1790874878566-frontend-backend-directory-refactor.md`

每一步都保持 `frontend/legacy/` 可用，随时可回退。

## 进度

| 步骤 | 内容 | 状态 |
| --- | --- | --- |
| 目录重构 | 建立 frontend/ backend/ 骨架，legacy 下沉 | ✅ 已完成 |
| 第 0 步 | 搭壳（Vite + Vue3 + TS，不迁业务） | ⬜ 未开始 |
| 第 1 步 | 静态结构（无计算） | ⬜ 未开始 |
| 第 2 步 | 交互逻辑（仍在前端算） | ⬜ 未开始 |
| 第 3 步 | 计算下沉到 Python | ⬜ 未开始 |
| 第 4 步 | 预设数据改造为 JSON | ⬜ 未开始 |
| 第 5 步 | 收尾，删除 legacy 与重定向页 | ⬜ 未开始 |

## 第 0 步 · 搭壳

1. 在 `frontend/` 初始化 Vite + Vue3 + TS。注意 `legacy/` 与 `public/` 已存在，
   需选择「忽略现有文件」或手工创建 `package.json` 后再 `npm install`。
2. 配置 `vite.config.ts`：`server.proxy = { '/api': 'http://127.0.0.1:8000' }`、
   别名 `@` → `src`。
3. 建 `src/router/index.ts`（Launcher / Calculator / Guide 三条路由）、
   `src/stores/panelStore.ts`（先空）、`App.vue` 只放 `<router-view/>`。
4. **验收**：`npm run dev` 能打开；`/legacy/pages/calculator.html` 仍可访问；两者互不影响。

## 第 1 步 · 静态结构

5. 把 `legacy/styles/calculator.css` 拆进 `src/assets/styles/`：
   `tokens.css`（提取颜色/间距变量）+ `base.css` + `components.css`。
6. 按 `.module` 边界把 `calculator.html` 的 DOM 拆成 `src/components/calculator/*`，
   全部 `v-model` 双向绑定到 `panelStore`，**计算结果先写死**。
7. `src/views/LauncherView.vue` 复刻启动界面卡片。
8. **验收**：新页面渲染与 legacy 一致，切换所有下拉无报错。

## 第 2 步 · 交互逻辑（仍在前端算）

9. 翻译为 composable / store action：
   - `useSubStatLimit`（总条数 ≤54 钳制）
   - `usePanelMode`（锋御模式文案替换）
   - 音擎三级联动（`calculator.js:80-136`）
   - 代理人标签联动（`calculator.js:183-222`）
10. `applyAgentPreset`（`calculator.js:224-365`）的防御性校验先在前端保留一份
    用于即时反馈，后续与 `backend/src/zzz_panel/presets/validate.py` 对齐。
11. **验收**：同一组输入，新旧页面显示完全相同的 12 项数值与明细文案。

## 第 3 步 · 计算下沉到 Python

12. 落地 `core/modes.py`（贯穿力、实际暴击率）、`core/constants.py`（驱动盘 1/2/3）、
    `core/modifiers.py`（4/5/6 号主词条、副词条换算、二件套）、`core/breakdown.py`（明细）。
13. 落地 `schemas/`、`services/`、`api/`（FastAPI 路由与 CORS）。
14. `src/api/panel.ts` + `usePanelCalc`（防抖 150~300ms）替换前端 `calc()`。
15. `src/utils/fmt` 与后端格式化规则保持一致。
16. **验收**：`backend/tests/test_panel.py` 中 legacy 抽样用例数值全等。

## 第 4 步 · 预设数据改造

17. 写 `tools/sync_presets.py`：把 `legacy/data/*.js` 转为根 `data/*.json`。
    脚本必须可重复执行且字节幂等。
18. `presetStore` 改从 `GET /api/presets/*` 拉取。
19. 抓取脚本（`refresh_*_presets.py`）输出目标改为 `data/*.json`；
    legacy 页面所需的 JS 包装由同步脚本反向生成。

## 第 5 步 · 收尾

20. 吸收 `guide.html`、`example-template.html` 为 `GuideView` / `ExampleView`。
21. `npm run build` 验证产物。
22. **删除 `frontend/legacy/` 与仓库根目录 6 个中文重定向页。**
23. 在本文件更新进度表。

## 回退方式

每步独立提交。若某步出现问题，`git revert` 对应提交即可回到上一步；
`frontend/legacy/` 在整个迁移过程中始终可用，用户侧功能不受影响。
