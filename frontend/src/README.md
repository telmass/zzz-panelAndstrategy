# frontend/src — Vue3 源码

迁移目标目录。**当前为空骨架**，尚未初始化 Vite 工程。

## 目录职责

| 目录 | 职责 |
| --- | --- |
| `assets/` | 经 Vite 处理的资源：`images/`（可 import）、`fonts/`、`styles/`（全局样式） |
| `components/layout/` | 页面骨架，与业务无关 |
| `components/common/` | 通用件：BaseSelect / NumberField / StatRow |
| `components/calculator/` | 业务组件，按 legacy 页面的 `.module` 切分 |
| `views/` | 路由级页面，一一对应现有 6 个 HTML |
| `router/` | 路由表 + 守卫 |
| `stores/` | Pinia：panelStore / presetStore / uiStore |
| `composables/` | 跨组件复用的行为 |
| `api/` | **唯一**网络出口，禁止在组件内直接 `fetch` |
| `types/` | TS 类型，与 `backend/src/zzz_panel/schemas/` 一一对应 |
| `constants/` | 枚举与常量 |
| `utils/` | 纯函数：`fmt` / `clamp` |
| `data/` | 后端不可用时的静态兜底数据 |

详见 [../../../docs/directory-layout.md](../../../docs/directory-layout.md)。

## 资源放置规则（易错）

- 放 **`public/`**（即 `frontend/public/`）：运行时按 URL 取的资源。当前 160 张
  代理人/音擎 PNG 在此。**不能被 `import`**，只能按路径引用。
- 放 **`src/assets/`**：会被 `import`、生成带 hash 的 URL、可被 CSS `url()` 引用。
  **未被 import 的文件不会进入构建产物**——这是 160 张 PNG 不放在这里的原因。

## 迁移进度

见 [../../../docs/migration-vue3.md](../../../docs/migration-vue3.md)。
