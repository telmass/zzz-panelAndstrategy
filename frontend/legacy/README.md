# frontend/legacy — 过渡期原生实现

重构前的原生 HTML 版本，**Vue3 迁移完成前是用户实际使用的版本**。

- 直接打开 `pages/index.html` 即可使用（无需构建、无需起服务）
- 或经 Vite dev server 访问 `/legacy/pages/index.html`
- **不参与 `npm run build`**，不会进入 `dist/`

文件对照、已知特性与删除时机见 [../../../docs/legacy-pages.md](../../../docs/legacy-pages.md)。

## 维护约束

- `data/agent-presets.js`、`data/weapon-presets.js` 是 Skill 脚本的**生成物，勿手改**
- `scripts/calculator-config.js` 是抓取脚本的**正则解析源**，格式不可随意改动
- `pages/calculator.html` 中 `data/*.js` 必须先于 `scripts/calculator.js` 加载
