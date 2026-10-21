# UI 体系

前端视觉体系的说明：令牌、尺度、颜色语义与两道闸门。

**既有系统优先。** 本项目用纯 CSS + CSS 变量（`frontend/src/assets/styles/tokens.css`），
不引入 Tailwind、不换组件库（naive-ui）、不做暗色模式。这套体系是既有的，
本次只是把它补成**有闸门的体系**：之前它有 21 个散落的字号、6 个字重、
29 个颜色值、90 处手写阴影，且**从未被对比度校验过**。

## 两道闸门

```powershell
python tools/check_ui_contrast.py --check   # 颜色对比度（WCAG 2.1）
python tools/check_ui_scale.py --check      # 字号 / 字重 / 间距 / 阴影是否越界
```

两道闸门都在 CI 里（`.github/workflows/ci.yml` 的「UI gates」步）。改配色或
尺度时先改 `tokens.css`，再跑闸门——**不要在组件样式里写死数值**。

| 闸门 | 守什么 | 阈值 |
| --- | --- | --- |
| 对比度 | 令牌两两之间的实际对比度 | 正文 ≥4.5:1；大字与控件边界 ≥3:1 |
| 尺度 | 字号只有 `var(--text-*)`、字重只有 `var(--weight-*)`、间距在刻度上、阴影只用 `--elevation-*` | 越界即失败 |

> 对比度闸门的配对表在 `tools/check_ui_contrast.py` 的 `PAIRS` 里，列出的是
> **实际会用到的**前景/背景组合，不是理论上的笛卡尔积。令牌从 `tokens.css`
> 读取——闸门不重复一份颜色值，令牌改了这里立刻反映。

## 尺度

### 字号：8 档

```
--text-xs 12px  --text-sm 13px  --text-base 14px  --text-md 15px
--text-lg 17px  --text-xl 20px  --text-2xl 24px  --text-3xl 28px
--text-display clamp(26px, 3.2vw, 34px)   # 攻略页 hero 展示级
```

组件样式里**只写** `var(--text-*)`，不写裸 px。档位之间至少 15% 落差，避免
出现「看不出大小差」的两档。

### 字重：3 档

```
--weight-normal 400   --weight-medium 600   --weight-bold 700
```

层级主要靠「两档字重 + 三档文字色」表达，不靠更多字重。原先还有 650 / 750 /
800 三档非标准值——静态字体栈下会被合成，渲染结果不可控。

### 文字色：3 档

```
--color-text-strong #111827   标题与数值
--color-text        #1f2937   正文
--color-text-muted  #5f6b7a   次要说明
```

原先有五档灰，浅色面上最浅的那档只有 **2.54:1**——所有说明性文字（每个模块
下面那行操作说明、帮助文案、副词条累计值）都不可读。现在合并成三档，最浅的
`--color-text-muted` 在白底 **5.43:1**、页面底色 **4.84:1**，两种底色都达标。

### 描边：2 档

```
--color-border        #d1d5db   装饰性分隔线（卡片边框、表格线）
--color-border-strong #7d8794   控件边界（输入框、下拉框），≥3:1
```

两者必须分开：WCAG 1.4.11 要求**识别控件所需的**视觉信息达到 3:1，装饰性
分隔线不在其列；而输入框的描边若只有 1.47:1，控件边界就找不到了。

### 间距：刻度

`4 / 8 / 12 / 16 / 20 / 24 / 32 / 40`（`--space-1` … `--space-10`）。刻度之外的
像素值只允许三个例外，且必须写明理由（`tools/check_ui_scale.py` 的
`ALLOWED_EXCEPTIONS`）：触控目标 44px、sticky 头部偏移 76px / 132px。

**组外空间必须大于组内空间**——六大模块的外距是 24px、内距 20px。原先外距
14px 反而小于内距 18px，六个模块会糊成一片。

### 阴影：5 级 elevation

```
--elevation-0 none
--elevation-1 0 1px 2px rgb(17 19 24 / 6%)     卡片
--elevation-2 0 1px 3px rgb(17 19 24 / 6%)     模块 / 面板
--elevation-3 0 4px 16px rgb(16 19 24 / 12%)  浮层 / 结果区
--elevation-4 0 18px 50px rgb(17 19 24 / 10%) 模态
```

深度只表达「这块东西浮在多高」，不表达强调程度。焦点环（`--shadow-focus` /
`--shadow-focus-strong`）是**状态指示**不是高度，因此不进这个阶梯。

原先有六个手写散落的 `box-shadow`（`0 4px 16px`、`0 1px 4px`、`drop-shadow(…)`
等），现已全部收进阶梯。

## 颜色语义

| 用途 | 令牌 | 说明 |
| --- | --- | --- |
| 交互色 | `--color-accent` 一族 | **唯一**的品牌色：按钮、链接、选中态、焦点环 |
| 危险 / 成功 | `--color-danger` / `--color-success` | 错误提示与固定词条数值 |
| 模块分区 | `--module-*-accent`（6 个） | 装饰性色条，六个对白底都 ≥3:1 |
| 标签 | `--tag-*-bg` / `--tag-*-text`（7 组） | **语义色**，计算器模块标签与指南页提示框按内容类型取同一套 |
| 结果区 | `--result-*` | 深色渐变上的浅色，六个都 ≥4.5:1（渐变亮端是最差情况） |

**模块序号徽标（01–06）是中性的**：深底白字 17.7:1。它承载「这是第几块」，
靠数字本身，不靠颜色——颜色留给左侧色条与标题标签，那两处已经在表达模块身份。

**色相不承载唯一信息**（WCAG 1.4.1）：徽标的数字、徽标的形状、标签的文字，
三者叠加，颜色只是第四道冗余信号。

### 「不收敛色相会不会杂乱」

不会立刻杂乱——色条只有 4px，每张卡只有一个色点，且色相目前不承载状态。但
有三项代价在本次修缮后被放大过：语义重载（靛蓝同时是交互色与模块 01）、
维护成本（29 个颜色值 → 约 90 条对比度配对手写维护）、新 UI 无处取色。

最终选择是**分层**而非全面收敛：攻略页的 `--cat-*`（代理人属性色）与指南页的
`guide-*`（提示框类型）**承载信息**，保留；计算器页的装饰色降级——徽标改中性、
标签与色条保留各自身份。详见 [ui-review-log.md](ui-review-log.md) 的先例表。

## 排版约定

- **正文行长上限 40em**（约 40 个汉字 / 80 个拉丁字符）。`.note`、`.card p`、
  `.subtitle` 与攻略页的 `.para` 都加了 `max-width: 40em`——内容列在 1440px
  视口下有 1180px 宽，不限行长的话一段话能拉到 80 多个字一行。
- **行高随行长变化**：窄栏 1.7–1.75，宽栏 1.5。
- **数字用等宽数字**（`font-variant-numeric: tabular-nums`）：结果值、副词条
  步进器、序号徽标、基础面板输入框。位数变化时数字不左右跳。
- **眉标**（`.eyebrow`）用大写 + `letter-spacing: 0.14em`，是全站唯一的全大写
  文字。

## 深度与描边的分工

卡片**靠阴影 + 底色浮起来**，不再叠一圈描边——描边、阴影、底色三件套同时用会
把页面切成一堆小格子。`.card` / `.page-hero` / `.guide-card` 已去掉描边；
表单控件的描边保留（那是控件边界，不是装饰）。

## 响应式

| 宽度 | 变化 |
| --- | --- |
| ≤960px | 结果区移到主列下方（单列） |
| ≤560px | 音擎 2 列；4/5/6 号主词条与二件套 3 列 → 2 列 |
| ≤480px | 副词条步进器 2 列 → 1 列；基础面板与代理人选择器 2 列 → 1 列 |
| ≤420px | 主词条与二件套 2 列 → 1 列 |

每个多列栅格都有自己的折叠点：窄屏不是桌面布局「折叠」来的——三列栅格在
375px 下每格只有约 90px，而「攻击力 30%」这样的选项需要约 105px。

## 截图

```powershell
node frontend/tools/screenshot.mjs --out <目录>          # 全量（30 张）
node frontend/tools/screenshot.mjs --out <目录> --only calculator --width 375
node frontend/tools/screenshot.mjs --out <目录> --viewport-only --click ".agent-picker .n-base-selection"
```

用 **CDP 驱动本机 Chrome**（Node 22 自带全局 `WebSocket`，**不新增依赖**）。

**为什么不用 `chrome --headless --screenshot`**：Chrome 在 Windows 上把
`--window-size` 的**宽度钳到最小 500px**（实测请求 375 → 实际视口 500，
560 → 544，1280 → 1264）。截出来的图按请求宽度**裁切**，但页面是按 500px 渲染的
——图在骗人：看上去「窄屏没折叠」，其实是根本没截到窄屏。CDP 的
`Emulation.setDeviceMetricsOverride` 能设任意宽度，`Page.captureScreenshot`
还能整页截（`captureBeyondViewport`）。

工具还负责两件容易翻车的事：

- **逐段滚到底再回顶**——攻略页的区块靠 IntersectionObserver 淡入
  （`.reveal` → `.reveal.is-visible`，480ms 过渡）。不滚一遍，视口外的区块在
  整页截图里是**全透明**的。
- **`--click` 打开浮层**——cascader 下拉这类状态要看得见才知道图标对不对。

## 验收

机器能判的都由闸门判。剩下的靠人工清单：
[ui-review-checklist.md](ui-review-checklist.md)。清单分三档（A 机器 / B 二值 /
C 锚点二选一），并有配套的先例表 [ui-review-log.md](ui-review-log.md)。
