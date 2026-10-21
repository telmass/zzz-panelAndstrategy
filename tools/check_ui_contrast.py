"""对比度闸门：检查设计令牌之间的实际对比度。

    python tools/check_ui_contrast.py --check     # 只校验，有不合格项则退出码 1
    python tools/check_ui_contrast.py --list      # 列出全部配对及其实测值

为什么要有这道闸
----------------
本仓库的浅色面上有五个文字灰、七个标签色、六个模块色、两条结果渐变，加起来
二十多个颜色值。**没有闸门时它们从未被对比度校验过**，于是：

- ``--color-text-faint``（所有说明性文字的颜色）在白底上只有 **2.54:1**，
  远低于 WCAG AA 的 4.5:1——用户在计算器页读不到任何一条操作说明；
- 表单控件的边框只有 **1.47:1**，低于 WCAG 1.4.11 要求的 3:1；
- 六个模块序号徽标的白字压在各自强调色上，**6/6 全部不合格**。

这类问题不会自己暴露：页面「看起来还行」，只是难读。闸门把「看起来还行」
换成一条可以失败的断言。

配对表
------
``PAIRS`` 列出系统**实际会用到的**前景/背景组合，而不是理论上的笛卡尔积。
阈值按 WCAG 2.1：正文 4.5:1，大字（≥18.66px 粗体或 ≥24px）与非文字元素
（控件边界、图形）3:1。

令牌从 ``frontend/src/assets/styles/tokens.css`` 读取——闸门不重复一份颜色值，
令牌改了这里立刻反映。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOKENS_CSS = REPO_ROOT / "frontend/src/assets/styles/tokens.css"

#: 正文所需的最低对比度（WCAG 2.1 AA）。
AA_TEXT = 4.5

#: 大字与非文字元素（控件边界、图形）所需的最低对比度。
AA_LARGE = 3.0

#: 前景令牌 / 背景令牌 / 最低对比度 / 说明。
#:
#: 用 ``#`` 开头的是字面色值（用于「白字压模块色」这类组合），其余是
#: ``tokens.css`` 里的令牌名。
PAIRS: tuple[tuple[str, str, float, str], ...] = (
    # ---- 浅色面：正文与次要文字 ----
    ("--color-text", "--color-surface", AA_TEXT, "正文"),
    ("--color-text", "--color-page-bg", AA_TEXT, "正文落在页面底色上"),
    ("--color-text-strong", "--color-surface", AA_TEXT, "标题与数值"),
    ("--color-text-strong", "--color-page-bg", AA_TEXT, "标题落在页面底色上"),
    ("--color-text-muted", "--color-surface", AA_TEXT, "次要文字（标签、说明）"),
    ("--color-text-muted", "--color-page-bg", AA_TEXT, "次要文字落在页面底色上"),
    ("--color-input-readonly-text", "--color-input-readonly-bg", AA_TEXT, "只读回填区"),
    # ---- 浅色面：品牌与状态 ----
    ("--color-accent", "--color-surface", AA_TEXT, "眉标（12px 粗体）"),
    ("--color-accent-text", "--color-accent-soft", AA_TEXT, "强调底色上的文字"),
    ("--color-danger", "--color-surface", AA_TEXT, "错误提示"),
    ("--color-success", "--color-fixed-stat-bg", AA_TEXT, "固定词条数值"),
    # ---- 浅色面：描边 ----
    # 装饰性描边（卡片边框、分隔线）不列入配对：WCAG 1.4.11 管的是「识别控件
    # 所需的视觉信息」，装饰性分隔线不在其列。**控件**边界用
    # ``--color-border-strong``，见下。
    ("--color-border-strong", "--color-surface", AA_LARGE, "表单控件边界（WCAG 1.4.11）"),
    ("--color-border-strong", "--color-input-readonly-bg", AA_LARGE, "只读控件边界"),
    # ---- 浅色面：模块标签（12.5px 粗体压浅底） ----
    ("--tag-base-text", "--tag-base-bg", AA_TEXT, "模块 1 标签"),
    ("--tag-weapon-text", "--tag-weapon-bg", AA_TEXT, "模块 2 标签"),
    ("--tag-core-text", "--tag-core-bg", AA_TEXT, "模块 3 标签"),
    ("--tag-disc-text", "--tag-disc-bg", AA_TEXT, "模块 4 标签"),
    ("--tag-sub-text", "--tag-sub-bg", AA_TEXT, "模块 5 标签"),
    ("--tag-set-text", "--tag-set-bg", AA_TEXT, "模块 6 标签"),
    ("--tag-armorer-text", "--tag-armorer-bg", AA_TEXT, "锋御标签"),
    # ---- 浅色面：模块色条（非文字，3:1） ----
    ("--module-base-accent", "--color-surface", AA_LARGE, "模块 1 色条"),
    ("--module-weapon-accent", "--color-surface", AA_LARGE, "模块 2 色条"),
    ("--module-core-accent", "--color-surface", AA_LARGE, "模块 3 色条"),
    ("--module-disc-accent", "--color-surface", AA_LARGE, "模块 4 色条"),
    ("--module-sub-accent", "--color-surface", AA_LARGE, "模块 5 色条"),
    ("--module-set-accent", "--color-surface", AA_LARGE, "模块 6 色条"),
    # ---- 模块序号徽标：白字压中性深底 ----
    ("--color-surface", "--color-text-strong", AA_TEXT, "01–06 序号徽标"),
    # ---- 结果区：深色渐变上的文字 ----
    ("--result-text", "--result-gradient-from", AA_TEXT, "结果区正文"),
    ("--result-text", "--result-gradient-to", AA_TEXT, "结果区正文（渐变亮端）"),
    ("--result-label", "--result-gradient-from", AA_TEXT, "结果区标签"),
    ("--result-label", "--result-gradient-to", AA_TEXT, "结果区标签（渐变亮端）"),
    ("--result-value", "--result-gradient-from", AA_TEXT, "结果数值"),
    ("--result-value", "--result-gradient-to", AA_TEXT, "结果数值（渐变亮端）"),
    ("--result-value-main", "--result-gradient-from", AA_TEXT, "主结果数值"),
    ("--result-value-main", "--result-gradient-to", AA_TEXT, "主结果数值（渐变亮端）"),
    ("--result-breakdown", "--result-gradient-from", AA_TEXT, "明细文字"),
    ("--result-breakdown", "--result-gradient-to", AA_TEXT, "明细文字（渐变亮端）"),
)

_TOKEN_RE = re.compile(r"^\s*(--[a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{3,8})\s*;", re.MULTILINE)


def load_tokens() -> dict[str, str]:
    """从 ``tokens.css`` 读出全部颜色令牌。"""
    text = TOKENS_CSS.read_text(encoding="utf-8")
    return {name: value.lower() for name, value in _TOKEN_RE.findall(text)}


def _expand_hex(value: str) -> str:
    """把 ``#abc`` 展开成 ``#aabbcc``，方便统一计算。"""
    if len(value) == 4:
        return "#" + "".join(ch * 2 for ch in value[1:])
    return value


def _relative_luminance(hex_color: str) -> float:
    """WCAG 2.1 相对亮度。"""
    value = _expand_hex(hex_color)
    channels = [int(value[i : i + 2], 16) / 255 for i in (1, 3, 5)]

    def linearize(channel: float) -> float:
        if channel <= 0.03928:
            return channel / 12.92
        return ((channel + 0.055) / 1.055) ** 2.4

    red, green, blue = (linearize(c) for c in channels)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(foreground: str, background: str) -> float:
    """两个色值的对比度（1.0 – 21.0）。"""
    lum_a = _relative_luminance(foreground)
    lum_b = _relative_luminance(background)
    lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


def resolve(tokens: dict[str, str], name: str) -> str | None:
    if name.startswith("#"):
        return name.lower()
    return tokens.get(name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="只校验，不打印全表")
    parser.add_argument("--list", action="store_true", help="打印全部配对与实测值")
    args = parser.parse_args()

    if not TOKENS_CSS.is_file():
        print(f"错误：找不到 {TOKENS_CSS}", file=sys.stderr)
        return 2

    tokens = load_tokens()
    failures: list[str] = []
    missing: list[str] = []

    for fg_name, bg_name, minimum, note in PAIRS:
        fg = resolve(tokens, fg_name)
        bg = resolve(tokens, bg_name)
        if fg is None:
            missing.append(f"{fg_name}（{note}）")
            continue
        if bg is None:
            missing.append(f"{bg_name}（{note}）")
            continue
        ratio = contrast_ratio(fg, bg)
        if args.list:
            status = "OK" if ratio >= minimum else "FAIL"
            print(f"  {status:4} {ratio:6.2f}:1 (需 {minimum}) {fg_name} / {bg_name} — {note}")
        if ratio < minimum:
            failures.append(
                f"{fg_name} / {bg_name} = {ratio:.2f}:1（需 ≥{minimum}）— {note}"
            )

    if missing:
        for name in missing:
            print(f"错误：tokens.css 里没有 {name}", file=sys.stderr)
        return 2

    if failures:
        print(f"对比度不合格 {len(failures)} 项：", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    if not args.list:
        print(f"  ok       对比度 {len(PAIRS)} 组全部达标")
    return 0


if __name__ == "__main__":
    sys.exit(main())
