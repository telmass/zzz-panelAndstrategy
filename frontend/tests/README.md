# frontend/tests — 前端测试

Vitest + jsdom，共 **118 项**。

```powershell
npm run test          # 一次性
npm run test:watch    # 监听
```

> ⚠️ Vitest 配置在 `vite.config.ts` 的 `test` 块中，**没有独立的
> `vitest.config.ts`**。找不到时别去找不存在的文件。

策略、覆盖范围与设计理由见 [docs/testing.md](../../docs/testing.md)。

## 五个 spec

| 文件 | 项数 | 覆盖 |
| --- | --- | --- |
| `calculator-view.spec.ts` | 36 | 计算器骨架、启动页、子页返回导航、指南页、攻略选择页卡片与 `/strategy/:slug` 路由透传/守卫 |
| `strategy-view.spec.ts` | 10 | 共享渲染器渲染、skip link/landmark、技能/驱动盘 tab ARIA 与方向键、音擎两列、驱动盘四列备注表、加载/错误态、背景字段，以及全部代理人的数据渲染 |
| `panel-interactions.spec.ts` | 51 | 代理人与音擎 cascader 分组与回填、选项前缀图标与菜单文案、模式名「通用」的隐藏、副词条钳制、模式与锋御文案、代理人预设载入、后端对接 |
| `strategy-ui.spec.ts` | 17 | 攻略同款排版：侧边目录编号与锚点、目录开关、`useScrollSpy` 可见带 / 区域容器 / 空窗保留 / 触底兜底 / 二级链接整链路、结果区复制/重置、启动页顶部导航与卡片、指南章节序号与 CTA、两页页眉无跳转按钮 |
| `legacy-parity.spec.ts` | 4 | **三方对拍**：旧 JS ≡ Vue3 页面 ≡ Python 后端 |

## support/ — 夹具层

| 文件 | 作用 |
| --- | --- |
| `setup.ts` | 全局 stub `RouterLink`，并补 jsdom 缺失的浏览器 API：`matchMedia`、`ResizeObserver`、`IntersectionObserver`。**刻意不打 `getBoundingClientRect` 的桩**——见下 |
| `router.ts` | `RouterLinkStub`，把 `to` 渲染成 `href` |
| `api.ts` | 假后端。**读真实的 `data/*.json`**，因此下拉框项数断言能发现数据漂移 |
| `backend.ts` | 拉起真实 uvicorn（端口 0 自动分配），仅供三方对拍使用 |
| `flush.ts` | 等待 260 ms（越过 200 ms 防抖）+ 微任务 + 两个宏任务 |

> ⚠️ `getBoundingClientRect` 刻意**不**打桩。jsdom 已实现它且恒返回全 0，而
> naive-ui 的 `n-cascader` 默认 `virtualScroll`，会拿这个 0 高度决定渲染多少
> 选项——浮层确实打开，但选项一项都不渲染。因此测试**不得断言浮层内的选项
> DOM**：「7 个一级项」在 store 层断言，DOM 层只验证浮层已打开。理由与实测
> 数据见 `setup.ts` 末尾的注释。

## fixtures/ — 只读参照实现

`fixtures/legacy-calculator/` 是迁移前的原生 HTML 实现，原样保留作对拍基准。

> ⛔ **禁止修改。** 改了基准，三方对拍就退化成「自己和自己比」，
> 永远不会失败，也就失去了意义。详见该目录下的
> [README.md](fixtures/legacy-calculator/README.md)。

## 两个容易踩的点

### 每个对拍用例都要重建夹具窗口

夹具的 `clearAgentPresetFields` 只重置基础面板、核心与二件套，
**不触碰** 4/5/6 号主词条与副词条。上一个用例遗留的配装会污染下一个。

### `panel-interactions.spec.ts` 必须 `enableAutoUnmount`

因为 `usePanelCalc` 的 watcher 会在 watcher 作用域之外调用
`usePanelStore()`，不自动卸载会造成实例残留。`calculator-view.spec.ts` 也加了
同样的声明——cascader 浮层 Teleport 到 `body`，不卸载会留给后续用例。

### naive-ui 的三条测试约束

见 [docs/testing.md](../../docs/testing.md) 第 5 节：浮层 Teleport 到 `body`、
选项在 `n-virtual-list` 里 jsdom 渲染不出来、placeholder 是覆盖层而非
`<input>` 的属性。

## 相关文档

- [docs/testing.md](../../docs/testing.md) —— 测试策略与三方对拍
- [docs/development.md](../../docs/development.md) —— 测试命令与常见坑
- [docs/requirements.md](../../docs/requirements.md) —— 验收标准