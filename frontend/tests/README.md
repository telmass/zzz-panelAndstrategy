# frontend/tests — 前端测试

Vitest 单元测试。优先覆盖：

- `src/utils/fmt` — 须与后端 `_fmt` 及 legacy `calculator.js` 的取整/千分位规则一致
- `src/composables/useSubStatLimit` — 副词条总条数 ≤54 的钳制行为
- `src/composables/usePanelMode` — standard / rupture / fengyu 的字段显隐与文案替换

集成测试（组件渲染、后端联调）在 Vue3 迁移第 2 步之后补充。
