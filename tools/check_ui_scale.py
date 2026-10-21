"""尺度闸门：字号、字重、间距与阴影是否都来自系统。

    python tools/check_ui_scale.py --check      # 只校验，有越界值则退出码 1
    python tools/check_ui_scale.py --list       # 打印实际用到的各项分布

为什么要有这道闸
----------------
``tokens.css`` 起初**根本没有字号令牌**（文件里自述「本项目未抽 font-size
token」），全站散落着 **21 个不同的字号**与 **6 个字重**（含 650 / 750 这类
非标准值——静态字体栈下会被合成，渲染结果不可控）。阴影同理：三个令牌之外
还有六处手写 ``box-shadow``。间距则用了 1px / 3px / 5px / 7px / 9px 这类
阶梯之外的零散值。

这类「每个值单看都合理，合起来没有体系」的状态，唯一的治法是**给体系配一道
闸**：越界即失败。

尺度定义在 ``tokens.css``
------------------------
- **字号**：``--text-xs … --text-3xl`` 共 8 档。CSS 里**只允许**用
  ``var(--text-*)``，不写裸 px——档位少、令牌短，直接用变量比写死数值更清楚。
- **字重**：``--weight-normal / medium / bold`` 三档。
- **间距**：``--space-*`` 之外的像素值必须落在刻度上
  （2 / 4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 80）；少数「不是间距」
  的量（触控目标尺寸、sticky 头部偏移）列在 :data:`ALLOWED_EXCEPTIONS` 里，
  并写明理由——新增例外必须写理由，不能默默放行。
- **阴影**：只允许 ``var(--elevation-*)``，以及两个焦点环（它们不是「高度」，
  是状态指示）。
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STYLES_DIR = REPO_ROOT / "frontend/src/assets/styles"
STRATEGY_CSS = REPO_ROOT / "frontend/src/strategy/strategy.css"
TOKENS_CSS = STYLES_DIR / "tokens.css"

#: 受检的样式文件。
SCANNED = sorted(STYLES_DIR.glob("*.css")) + ([STRATEGY_CSS] if STRATEGY_CSS.is_file() else [])

#: 间距刻度。这些值是「有意的」——中间那档 2px 是发丝级微调。
SPACING_SCALE = frozenset({2, 4, 8, 12, 16, 20, 24, 32, 40, 48, 80})

#: 允许的例外：不是间距的量。每条都要写明理由。
ALLOWED_EXCEPTIONS: dict[int, str] = {
    44: "触控目标最小高度（WCAG 2.5.5）",
    76: "sticky 头部偏移量，随头部高度变化",
    132: "sticky 头部偏移量（多栏布局下）",
}

#: 允许的阴影：焦点环是状态指示，不是高度。
ALLOWED_SHADOWS = frozenset({"var(--shadow-focus)", "var(--shadow-focus-strong)"})

_FONT_SIZE_RE = re.compile(r"font-size\s*:\s*([^;]+);")
_FONT_WEIGHT_RE = re.compile(r"font-weight\s*:\s*([^;]+);")
_SPACING_RE = re.compile(r"(?:padding|margin|gap|row-gap|column-gap)(?:-[a-z]+)?\s*:\s*([^;]+);")
_SHADOW_RE = re.compile(r"box-shadow\s*:\s*([^;]+);")
_PX_RE = re.compile(r"(?<![\w.%-])(\d+(?:\.\d+)?)px")


def _strip_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)


def _allowed_font_sizes(tokens_css: str) -> set[str]:
    """从 ``tokens.css`` 读出固定档位的字号（px 值）。"""
    return set(re.findall(r"(--text-[a-z0-9-]+)\s*:\s*(\d+(?:\.\d+)?px)", tokens_css))


def _allowed_fluid_sizes(tokens_css: str) -> set[str]:
    """流体展示级字号（``clamp()``）。只允许以 ``var()`` 形式引用。"""
    return set(re.findall(r"(--text-[a-z0-9-]+)\s*:\s*clamp\(", tokens_css))


def _allowed_font_weights(tokens_css: str) -> set[str]:
    return set(re.findall(r"(--weight-[a-z0-9-]+)\s*:\s*(\d+)", tokens_css))


def _scan() -> tuple[list[str], Counter, Counter, Counter, Counter]:
    tokens_css = TOKENS_CSS.read_text(encoding="utf-8")
    size_tokens = _allowed_font_sizes(tokens_css)
    fluid_tokens = _allowed_fluid_sizes(tokens_css)
    allowed_sizes = {value for _, value in size_tokens}
    allowed_weights = {value for _, value in _allowed_font_weights(tokens_css)}

    problems: list[str] = []
    sizes: Counter = Counter()
    weights: Counter = Counter()
    spacings: Counter = Counter()
    shadows: Counter = Counter()

    for path in SCANNED:
        text = _strip_comments(path.read_text(encoding="utf-8"))
        relative = path.relative_to(REPO_ROOT).as_posix()

        for match in _FONT_SIZE_RE.finditer(text):
            value = match.group(1).strip()
            sizes[value] += 1
            if value.startswith("var("):
                name = value[4:-1].strip()
                if name not in {token for token, _ in size_tokens} and name not in fluid_tokens:
                    problems.append(f"{relative}: font-size: {value} 不是已登记的字号档位")
                continue
            if value not in allowed_sizes:
                problems.append(f"{relative}: font-size: {value} 不在字号阶梯上")

        for match in _FONT_WEIGHT_RE.finditer(text):
            value = match.group(1).strip()
            weights[value] += 1
            if value.startswith("var("):
                continue
            if value not in allowed_weights:
                problems.append(f"{relative}: font-weight: {value} 不在字重阶梯上")

        for match in _SPACING_RE.finditer(text):
            for raw in _PX_RE.findall(match.group(1)):
                number = float(raw)
                if number != int(number):
                    problems.append(f"{relative}: 间距 {raw}px 不是整数")
                    continue
                spacings[int(number)] += 1
                if int(number) in SPACING_SCALE or int(number) in ALLOWED_EXCEPTIONS:
                    continue
                problems.append(f"{relative}: 间距 {int(number)}px 不在刻度上")

        for match in _SHADOW_RE.finditer(text):
            value = match.group(1).strip()
            shadows[value] += 1
            if value.startswith("var("):
                if value not in ALLOWED_SHADOWS and "--elevation-" not in value:
                    problems.append(f"{relative}: box-shadow: {value} 不在 elevation 阶梯上")
                continue
            problems.append(f"{relative}: box-shadow: {value} 是手写阴影")

    return problems, sizes, weights, spacings, shadows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="只校验，不打印分布")
    parser.add_argument("--list", action="store_true", help="打印实际用到的分布")
    args = parser.parse_args()

    problems, sizes, weights, spacings, shadows = _scan()

    if args.list:
        print("字号：")
        for value, count in sorted(sizes.items(), key=lambda item: str(item[0])):
            print(f"  {value:>16}  x{count}")
        print("字重：")
        for value, count in sorted(weights.items(), key=lambda item: str(item[0])):
            print(f"  {value:>16}  x{count}")
        print("间距：")
        for value, count in sorted(spacings.items()):
            mark = "" if value in SPACING_SCALE else "  ← 例外"
            print(f"  {value:>16}px  x{count}{mark}")
        print("阴影：")
        for value, count in shadows.most_common():
            print(f"  x{count}  {value[:70]}")

    if problems:
        print(f"尺度越界 {len(problems)} 项：", file=sys.stderr)
        for problem in problems[:60]:
            print(f"  - {problem}", file=sys.stderr)
        if len(problems) > 60:
            print(f"  …另有 {len(problems) - 60} 项", file=sys.stderr)
        return 1

    if not args.list:
        print("  ok       字号 / 字重 / 间距 / 阴影均来自系统")
    return 0


if __name__ == "__main__":
    sys.exit(main())
