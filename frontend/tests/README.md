# frontend/tests — 前端测试

Vitest + jsdom，共 **64 项**。

```powershell
npm run test          # 一次性
npm run test:watch    # 监听
```

> ⚠️ Vitest 配置在 `vite.config.ts` 的 `test` 块中，**没有独立的
> `vitest.config.ts`**。找不到时别去找不存在的文件。

策略、覆盖范围与设计理由见 [docs/testing.md](../../docs/testing.md)。

## 三个 spec

| 文件 | 项数 | 覆盖 |
| --- | --- | --- |
| `calculator-view.spec.ts` | 27 | 计算器骨架、启动页、子页返回导航、指南页 |
| `panel-interactions.spec.ts` | 33 | 音擎三级联动、副词条钳制、模式与锋御文案、代理人预设载入、后端对接 |
| `legacy-parity.spec.ts` | 4 | **三方对拍**：旧 JS ≡ Vue3 页面 ≡ Python 后端 |

## support/ — 夹具层

| 文件 | 作用 |
| --- | --- |
| `setup.ts` | 全局 stub `RouterLink` |
| `router.ts` | `RouterLinkStub`，把 `to` 渲染成 `href` |
| `api.ts` | 假后端。**读真实的 `data/*.json`**，因此下拉框项数断言能发现数据漂移 |
| `backend.ts` | 拉起真实 uvicorn（端口 0 自动分配），仅供三方对拍使用 |
| `flush.ts` | 等待 260 ms（越过 200 ms 防抖）+ 微任务 + 两个宏任务 |

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
`usePanelStore()`，不自动卸载会造成实例残留。

## 相关文档

- [docs/testing.md](../../docs/testing.md) —— 测试策略与三方对拍
- [docs/development.md](../../docs/development.md) —— 测试命令与常见坑
- [docs/requirements.md](../../docs/requirements.md) —— 验收标准