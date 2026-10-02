# Vue3 迁移指南

原方案：`.kilo/plans/1790874878566-frontend-backend-directory-refactor.md`

每一步都保持 `frontend/legacy/` 可用，随时可回退。

## 进度

| 步骤 | 内容 | 状态 |
| --- | --- | --- |
| 目录重构 | 建立 frontend/ backend/ 骨架，legacy 下沉 | ✅ 已完成 |
| 第 0 步 | 搭壳（Vite + Vue3 + TS，不迁业务） | ✅ 已完成（2026-10-02） |
| 第 1 步 | 静态结构（无计算） | ✅ 已完成（2026-10-02） |
| 第 2 步 | 交互逻辑（仍在前端算） | ✅ 已完成（2026-10-02） |
| 第 3 步 | 计算下沉到 Python | ⬜ 未开始 |
| 第 4 步 | 预设数据改造为 JSON | ⬜ 未开始 |
| 第 5 步 | 收尾，删除 legacy 与重定向页 | ⬜ 未开始 |

## 第 0 步 · 搭壳（已完成 2026-10-02）

产出文件：

```
frontend/
├── index.html            Vite 入口
├── package.json          name: zzz-panel-frontend
├── tsconfig.json         strict，exclude legacy
├── vite.config.ts        @ 别名 + /api 代理 + vitest 配置
├── .env.example          VITE_API_BASE_URL
└── src/
    ├── main.ts           createApp(App).use(pinia).use(router).mount('#app')
    ├── App.vue           仅 <router-view />
    ├── router/index.ts   Launcher / Calculator / Guide 三条路由
    ├── stores/panelStore.ts
    └── views/            LauncherView / CalculatorView / GuideView（占位）
```

注意 `legacy/` 与 `public/` 已存在，**不要用脚手架覆盖**，`package.json` 等配置为手工创建。

`vite.config.ts` 的 `defineConfig` 从 `vitest/config` 导入而非 `vite`——只有前者带
`test` 字段的类型定义。

已验证：`npm run typecheck` 通过；`npm run build` 产出 `dist/`（含 `public/` 的 160 张图片，
不含 `legacy/`）；`/legacy/pages/calculator.html` 在 dev server 下正常访问。

## 第 1 步 · 静态结构

5. 把 `legacy/styles/calculator.css` 拆进 `src/assets/styles/`：
   `tokens.css`（提取颜色/间距变量）+ `base.css` + `components.css`。
6. 按 `.module` 边界把 `calculator.html` 的 DOM 拆成 `src/components/calculator/*`，
   全部 `v-model` 双向绑定到 `panelStore`，**计算结果先写死**。
7. `src/views/LauncherView.vue` 复刻启动界面卡片。
8. **验收**：新页面渲染与 legacy 一致，切换所有下拉无报错。

## 第 1 步 · 静态结构（已完成 2026-10-02）

只搭骨架，不含业务逻辑、数据请求与事件绑定。legacy 保持可用且未改动。

```
src/
├── assets/styles/       index.css 为入口，按 tokens → base → components 顺序引入
├── components/
│   ├── common/          PanelModule / NumberField / TextField / SelectField / StepperInput
│   ├── calculator/      六大模块 + ResultPanel，经 index.ts 统一导出
│   └── layout/
├── constants/           选项表，第 2 步起由 placeholderOptions.ts 改为 calculatorOptions.ts
└── types/panel.ts       类型契约，键名对齐 legacy 的 DOM id
```

`calculator.css` 拆为三层时做了两处取舍：

- legacy 的 `.grid3` 未被任何页面引用，未迁入。
- `TextField` 与 `NumberField` 分开：音擎的「固定副词条属性」需承载 `—`，
  数字输入框无法表示，沿用 legacy 的 `type="text"`。

通用组件最终落在 `components/common/` 而非 `components/ui/`——按
`docs/directory-layout.md` 的规范分层，并去掉了多余的 `ui/` 嵌套。
`constants/placeholderOptions.ts` 是第 1 步的占位选项，第 2 步接入真实数据后
已替换为 `constants/calculatorOptions.ts`。

已验证：`vue-tsc --noEmit` 通过；`npm run build` 成功；`tests/calculator-view.spec.ts`
13 项渲染断言全绿（模块顺序与色条变体、12 个基础字段与命破专属字段默认隐藏、
音擎三级下拉的 disabled 链、副词条 10 项步进器与初始禁用态、
结果区在 standard/rupture/fengyu 三种模式下的 12/13/14 行显隐）。

## 第 2 步 · 交互逻辑（仍在前端算）

9. 翻译为 composable / store action：
   - `useSubStatLimit`（总条数 ≤54 钳制）
   - `usePanelMode`（锋御模式文案替换）
   - 音擎三级联动（`calculator.js:80-136`）
   - 代理人标签联动（`calculator.js:183-222`）
10. `applyAgentPreset`（`calculator.js:224-365`）的防御性校验先在前端保留一份
    用于即时反馈，后续与 `backend/src/zzz_panel/presets/validate.py` 对齐。
11. **验收**：同一组输入，新旧页面显示完全相同的 12 项数值与明细文案。

## 第 2 步 · 交互逻辑（已完成 2026-10-02）

`frontend/legacy/` 全程零改动，回退路径完好。

```
src/
├── stores/panelStore.ts        表单状态 + 派生 getters + actions
├── composables/
│   ├── usePanelCalc.ts         实算逻辑，替换第 1 步的写死结果
│   ├── useSubStatLimit.ts      总条数 ≤54、单项 ≤36 钳制
│   ├── usePanelMode.ts         命破/锋御字段显隐与能量类文案替换
│   └── useAgentPreset.ts       预设校验、载入与 URL 查询参数初始化
├── utils/                      fmt.ts 对齐 legacy 取整与千分位，clamp.ts
├── data/                       agentPresets.ts / weaponPresets.ts 静态兜底
├── types/                      agentPresets.ts / weaponPresets.ts
├── constants/calculatorOptions.ts
└── components/common/          通用字段组件改为 v-model 契约
```

音擎三级锁定（等级 → 类别 → 名称）与代理人标签过滤实现为 store action；
切换上游时清空下游选择与只读回填区。切换代理人标签会把 `panelMode` 回落到
URL 请求的模式，非法 `mode` 参数回落 `standard`。

### 测试中的两个坑

`tests/legacy-parity.spec.ts` 用 jsdom 加载 legacy 页面联跑，两个细节容易踩：

- 必须 `runScripts: 'dangerously'`：只有该模式会编译 HTML 内联的 `onchange`
  属性，否则 `updateWeaponGrade` / `applyAgentPreset` 等联动根本不触发。
- 多个 legacy `<script>` 必须合并成**一段**内联脚本：真实浏览器中它们共享
  全局词法作用域，而独立 `eval()` 各自成域，`const` 声明的 `CORE_OPTIONS`
  等将不可见。

另外 legacy 的 `clearAgentPresetFields` 只重置基础面板、核心与二件套，
**不触碰 4/5/6 号主词条与副词条**。共用一个 JSDOM 会让上一个用例的驱动盘
配置漏进下一个用例，产生假差异（曾表现为攻击力 1449.6 vs 1136），
因此每个用例都重建 DOM。

### 已验证

`vue-tsc --noEmit` 与 `npm run build` 通过；`npm run test` 42 项全绿：

- `tests/calculator-view.spec.ts` 13 项渲染断言。其中两条随第 2 步的行为更新：
  副词条按钮不再是「全部禁用」，而是条数为 0 时减号禁用、加号可用；
  结果区不再是 `—` 占位而是实算值。
- `tests/legacy-parity.spec.ts` 4 项对拍：默认空配置与满配两档下，
  12~13 行数值及明细文案**逐字符**一致。
- `tests/panel-interactions.spec.ts` 25 项交互行为：音擎三级锁定与下游清空、
  代理人标签过滤、副词条钳制（含负数与小数归一化）、
  锋御文案替换、预设载入的错误路径。

dev server 下 `/`、`/calculator` 与三个 legacy 页面均返回 200。

## 第 3 步 · 计算下沉到 Python

12. `core/modes.py` 已落地贯穿力、实际暴击率与锋御固定锐暴伤害；
    继续实现 `core/constants.py`（驱动盘 1/2/3）、
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
