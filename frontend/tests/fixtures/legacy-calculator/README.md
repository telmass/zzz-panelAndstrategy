# legacy-calculator · 参照实现夹具

Vue3 迁移前的原生 HTML 实现（`frontend/legacy/`）在第 5 步已整体删除，
但**计算部分被原样保留在这里**，作为三方对拍与格式化对拍的基准。

## 为什么留下

| 消费者 | 断言什么 |
| --- | --- |
| `frontend/tests/legacy-parity.spec.ts` | 旧 JS 实算结果与 Vue3 页面经 HTTP 取回的结果**逐字符相同** |
| `backend/tests/test_fmt_parity.py` | Python 的 `core.fmt.fmt` 与 legacy 的 `fmt` 对同一组数值产出相同字符串 |
| `frontend/tools/diff_breakdown.mjs` | 排查对拍差异时，按 DOM 层级归类逐行 diff |
| `frontend/tools/dump_legacy_cases.mjs` | 导出抽样用例为 `backend/tests/legacy_cases.json` |
| `tools/sync_presets.py --to-legacy` | 由 `data/*.json` 反向生成本目录的 `data/*.js` |

删掉它等于删掉项目最强的一道正确性护栏，且 `test_fmt_parity.py` 会因
`pytest.skip` 变成**假绿灯**——不报错，但检查已失效。

## 目录结构必须保持

`pages/calculator.html` 用 `../styles`、`../data`、`../scripts` 相对引用，
因此四个子目录的位置不能动。

## 维护约束

- **禁止修改任何文件。** 一旦修改，参照基准就变成了新实现本身，
  三方对拍退化为「自己和自己比」，永远不会失败，也就失去了意义。
- **禁止给legacy 补功能。** 新需求一律实现在 Vue3 侧。
- `data/agent-presets.js`、`data/weapon-presets.js` 由
  `python tools/sync_presets.py --to-legacy` 从 `data/*.json` 生成，勿手工编辑；
  改动预设后跑 `--to-legacy --check`，退出码非 0 即表示两侧漂移。
- `scripts/calculator-config.js` 是 Skill 抓取脚本的**正则解析源**，格式不可随意改动。

## 已删除的 legacy 页面

以下页面在本目录之外，已随迁移删除，无需保留：

| 原路径 | 去向 |
| --- | --- |
| `pages/index.html` | `src/views/LauncherView.vue` |
| `pages/guide.html` | `src/views/GuideView.vue` |
| `pages/example-template.html` | 不吸收（计算逻辑与统一计算器重复） |
| `pages/redirect-rupture.html`、`pages/redirect-fengyu.html` | `?mode=` 路由 query |