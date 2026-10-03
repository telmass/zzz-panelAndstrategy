# 音擎下拉选项图标（roletag + 音擎头像）

## 目标

给音擎 `n-cascader` 的展开态选项加前缀图标：一级显示 roletag 类别图标，二级显示音擎头像。
**不改任何交互逻辑、状态管理、数据结构。**

## 已核实的事实（勿重复调查）

| 事实 | 依据 |
| --- | --- |
| `NCascader` 全项目仅一处：`WeaponModule.vue:57` | `grep n-cascader\|NCascader` |
| `icons/` 目录**未被任何代码引用**（全仓库 grep `icons/` 零命中），且为 untracked | `git status` 显示 `?? frontend/public/images/icons/` |
| 当前**未设** `render-prefix` / `show-checkbox`，故 naive **不渲染任何前缀元素** | `CascaderOption.mjs:197` `if (showCheckbox \|\| renderPrefix)` |
| 唯一叫 "placeholder" 的元素在**后缀**（右侧）且二级为空 | `CascaderOption.mjs:227` `.n-cascader-option-icon-placeholder` |
| `render-prefix` 是 Cascader 合法 prop，经 provide 下达到 `CascaderOption` | `Cascader.mjs:120`、`Cascader.mjs:731` |
| `renderPrefix` 收到的是 `tmNode.rawNode`，即我们传入的原始 option | `CascaderOption.mjs:217` |
| **搜索结果列表无法加图标**：选项被裁成 `{value,label}`，且不传任何 render hook | `CascaderSelectMenu.mjs:78-80`、`:149-162` |
| `index.css` 全局引入（非 scoped），全局类名可命中 Teleport 到 body 的浮层 | `main.ts:8` |
| jsdom 里选项**不渲染**（`virtualScroll` + 零高度），自动化测试只能断 `render-prefix` props，不能断选项 DOM | `CascaderSubmenu.mjs:63`、`setup.ts` 注释 |

> 结论：不存在"图标加载失败"问题（无引用即无请求）。这是**新增**图标渲染，不是修 bug。

## 已锁定决策

1. **文件名沿用仓库已有的官方映射**，取自 HoYoLAB Wiki API 的 profession key
   （`.github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py:39-47`），不新造拼音或英文词。
2. **搜索结果列表保持纯文本**（naive-ui 限制）。树形菜单两级都有图标；输入搜索词后为纯文本列表。
   与目标站行为一致（目标站同用 naive-ui，同样受限）。
3. **naive 右侧 32px 后缀占位保留不动**。传 `render-suffix` 返回 `null` 省不下空间——
   外层 `.n-cascader-option__suffix` 仍有 `min-width: 32px`，只会连一级项的箭头 chevron 一起丢掉。

## 步骤

### 步骤 1 · 重命名 7 张 roletag 图标

映射（`frontend/public/images/icons/`）：

| 原文件名 | roletag | 新文件名 |
| --- | --- | --- |
| `强攻.png` | 强攻 | `strike.png` |
| `击破.png` | 击破 | `pierce.png` |
| `异常.png` | 异常 | `abnormal.png` |
| `支援.png` | 支援 | `support.png` |
| `防护.png` | 防护 | `guard.png` |
| `命破.png` | 命破 | `rupture.png` |
| `锋御.png` | 锋御 | `armero.png` |

均为小写 ASCII，无中文。注意 `armero` 看着奇怪，但它是官方 wiki key，与仓库既有脚本一致。

操作：纯改名（untracked，无需 `git mv`）。

**验证**
- `glob public/images/icons/**` 确认 7 个新名、无中文残留。
- 全仓库 grep `icons/` 与 7 个中文文件名，确认**零引用**——因此无需改任何代码。
  若 grep 出命中，说明有遗漏引用，必须改完再继续。
- `npm run build` 后确认 `dist/images/icons/` 下 7 张齐全。

### 步骤 2 · 在展示层新增图标映射（不改 store）

文件：`frontend/src/components/calculator/WeaponModule.vue`（仅此一处需要，不进 `constants/`）。

- 只读引入 `WEAPON_ROLE_TAGS`（`@/constants/calculatorOptions`）取联合类型
  `(typeof WEAPON_ROLE_TAGS)[number]`。
- 新增模块级 `const ROLE_ICON: Record<WeaponRoleTag, string>`，值为步骤 1 的 slug。
  用 `Record<联合类型, string>` 是为了**编译期穷尽**——将来 `WEAPON_ROLE_TAGS` 加了新
  roletag 而这里漏了，`vue-tsc` 会报错，而不是运行时静默缺图。
- 新增 `optionIconSrc(option): string`：以 `option.children?.length` 判层级
  （一级=roletag 组 → `/images/icons/{slug}.png`；二级=叶子 → `/images/weapons/{option.value}.png`）。
  **映射未命中时返回空串**，调用方据此不渲染 `<img>`，避免出现破图方框。
- 全用 `/images/...` 相对路径，禁止绝对磁盘路径与外链。

**验证**
- `npm run typecheck`（`vue-tsc --noEmit`）通过。
- 临时把某个 slug 改成不存在的名字，确认**编译期**报错（证明 `Record` 穷尽生效），随后还原。

### 步骤 3 · 接上 `render-prefix`

文件：`frontend/src/components/calculator/WeaponModule.vue`

- 模板给 `<n-cascader>` 加 `:render-prefix="renderOptionPrefix"`。
- `renderOptionPrefix({ option })` 返回 `h('img', {...})`：
  - `class: 'weapon-option-icon'`、`src`、`alt: ''`（装饰性图标）、`loading: 'lazy'`
  - `onError` 把 `img.style.display = 'none'`——缺图时**不显示方框**，与步骤 2 的空串兜底双保险。
  - `src` 为空串时返回 `null`，不渲染元素。
- 保持 `filterable` / `clearable` / `placeholder` / `:options` / `:value` / `@update:value`
  **一律不动**。不碰 `onSelect`、`panelStore`、任何类型定义。

文件：`frontend/src/assets/styles/components.css`（追加到既有"音擎选择器与头像卡片"区块）

```css
/* naive 的 .n-cascader-option__prefix 已是 32px 宽的 flex 居中容器，
   这里只需定尺寸。类名必须全局——浮层 Teleport 到 body，
   写成 .weapon-picker 后代选择器会失效。 */
.weapon-option-icon {
  width: 20px;
  height: 20px;
  border-radius: var(--radius-sm);
  object-fit: cover;
}
```

**验证（浏览器，唯一能真正看到图标的途径）**

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\dev.ps1 start
```

打开 `http://localhost:5173/calculator`，展开音擎下拉：

1. 一级 7 项：左侧各有对应 roletag 图标，右侧仍有 chevron。
2. 点开某一级：二级各项左侧显示对应音擎头像。
3. DevTools Network：过滤 `icons` 与 `weapons`，应见 `/images/icons/strike.png` 等
   **200**；**无 404**（图标缺失时 `onError` 会隐藏，Network 仍会显示 404，据此确认是"资源真缺"而非"渲染失败"）。
4. Console 无报错。
5. 在搜索框输入「云」：结果为**纯文本**（预期行为，见决策 2），图标不出现且无报错。

### 步骤 4 · 回归验证

```powershell
cd frontend; npm run typecheck
cd frontend; npm test
```

预期 **71 项全绿**（`calculator-view` 30 / `panel-interactions` 37 / `legacy-parity` 4）。

补充断言（可选但推荐，jsdom 内可行）：`panel-interactions.spec.ts` 取
`findComponent(NCascader).props('renderPrefix')`，直接以假 option 调用并断言返回 vnode 的
`src`——一级得 `/images/icons/strike.png`、二级得 `/images/weapons/ep-xxx.png`、
未知 roletag 返回 `null`。**不要**断言 `.n-cascader-option` DOM（虚拟列表在 jsdom 渲染不出来）。
新增后测试数变为 72，需同步 `docs/testing.md` 与 `frontend/tests/README.md` 两处计数。

### 步骤 5 · 文档同步（推荐，成本极低）

仓库有多处文档逐一列举 `public/images/` 内容与 PNG 冗余，加了 `icons/` 需跟上：
- `frontend/public/README.md` —— 图片目录表加一行 `images/icons/`（7 张 roletag 图标，已接入）。
- `docs/directory-layout.md:25` 与 `:67-69` —— 更新 160 张的构成说明（新增 7 张 roletag 图标，且**已接入**）。
- `docs/requirements.md:112` —— 「60 张代理人 PNG 无引用」保持不变（`agents/` 仍未接入），无需改。
- `docs/changelog.md` —— 加一条：音擎 cascader 选项新增 roletag 图标与音擎头像前缀。

## 风险

| 风险 | 处置 |
| --- | --- |
| 一级 rletag 拼错导致图标 404 | 名称直接取自既有官方脚本 `refresh_agent_presets.py`，非手写 |
| 未来 `WEAPON_ROLE_TAGS` 扩容漏配图标 | `Record<联合类型,string>` 编译期报错 + 未命中返回空串不渲染 |
| 误以为选项 DOM 可断 | jsdom 虚拟列表渲染不出选项，只能断 props |
| CSS 写成 `.weapon-picker .weapon-option-icon` | 浮层在 body 里，选择器失效。必须全局类名 |

## 明确不做

- 不改 `panelStore`、`weaponPresetGroups`、`selectWeaponPreset`、`WeaponCascaderOption` 等任何类型或数据结构。
- 不改 `onSelect`、`filterable`、`clearable` 及任何事件处理。
- 不给搜索结果列表加图标（naive-ui 不支持，见决策 2）。
- 不动 `agents/` 的 60 张图（仍无引用，属另一笔已记录的债务）。
- 不碰右侧后缀占位与 chevron。