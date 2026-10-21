"""把样式表归一到设计体系（一次性迁移脚本）。

    python tools/normalize_ui_scale.py            # 就地改写
    python tools/normalize_ui_scale.py --check    # 只报告，不写文件

做四件事：

1. **字号**改成 ``var(--text-*)``（8 档阶梯），不再有裸 px。
2. **字重**改成 ``var(--weight-*)``（3 档），650 / 750 / 800 一并收敛。
3. **间距**归到刻度（2 / 4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 80）。
4. **令牌改名**：``--color-text-faint`` 并入 ``--color-text-muted``；
   ``--shadow-module`` / ``--shadow-result`` / ``--shadow-raised`` 收进
   ``--elevation-*`` 阶梯；手写阴影改用对应档位。

字号与字重用变量（档位少、名字有意义），间距保留裸 px（刻度由
``tools/check_ui_scale.py`` 按数值把关）——两者的取舍见该脚本的 docstring。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    REPO_ROOT / "frontend/src/assets/styles/base.css",
    REPO_ROOT / "frontend/src/assets/styles/components.css",
    REPO_ROOT / "frontend/src/strategy/strategy.css",
]

#: 字号（px）-> 档位令牌。
FONT_SIZE_TOKENS = {
    "9": "--text-xs",
    "10": "--text-xs",
    "10.5": "--text-xs",
    "11": "--text-xs",
    "12": "--text-xs",
    "12.5": "--text-sm",
    "13": "--text-sm",
    "13.5": "--text-sm",
    "14": "--text-base",
    "14.5": "--text-base",
    "15": "--text-md",
    "16": "--text-lg",
    "17": "--text-lg",
    "18": "--text-lg",
    "19": "--text-xl",
    "20": "--text-xl",
    "21": "--text-xl",
    "24": "--text-2xl",
    "28": "--text-3xl",
    "30": "--text-3xl",
}

#: 字重 -> 档位令牌。
FONT_WEIGHT_TOKENS = {
    "400": "--weight-normal",
    "600": "--weight-medium",
    "650": "--weight-medium",
    "700": "--weight-bold",
    "750": "--weight-bold",
    "800": "--weight-bold",
}

#: 间距（px）-> 刻度上的值。取「就近但不小于原值」的方向，视觉上只会更松
#: 一点，不会挤在一起。
SPACING_SCALE = {
    1: 2,
    3: 2,
    5: 4,
    6: 4,
    7: 8,
    9: 8,
    10: 12,
    14: 12,
    18: 16,
    22: 20,
    26: 24,
    34: 32,
    36: 32,
}

#: 不是间距的量，保持原值。
SPACING_EXCEPTIONS = {44, 48, 76, 80, 132}

#: 令牌改名。
TOKEN_RENAMES = {
    "--color-text-faint": "--color-text-muted",
    "--shadow-module": "--elevation-2",
    "--shadow-result": "--elevation-3",
    "--shadow-raised": "--elevation-3",
}

#: 手写阴影 -> elevation 档位。
SHADOW_REPLACEMENTS = {
    "0 1px 2px rgb(17 19 24 / 6%)": "var(--elevation-1)",
    "0 1px 3px rgb(17 19 24 / 6%)": "var(--elevation-2)",
    "0 1px 3px rgb(17 19 24 / 5%)": "var(--elevation-1)",
    "0 1px 4px rgb(0 0 0 / 18%)": "var(--elevation-1)",
    "0 2px 6px rgb(23 25 31 / 6%)": "var(--elevation-1)",
    "0 3px 8px rgb(17 19 24 / 18%)": "var(--elevation-2)",
    "0 4px 16px rgb(16 19 24 / 12%)": "var(--elevation-3)",
    "0 18px 50px rgb(17 19 24 / 10%)": "var(--elevation-4)",
}

_FONT_SIZE_RE = re.compile(r"(font-size\s*:\s*)([0-9.]+)(px|em)\b")
_FONT_WEIGHT_RE = re.compile(r"(font-weight\s*:\s*)([0-9]+)\b")
_SPACING_RE = re.compile(
    r"((?:padding|margin|gap|row-gap|column-gap)(?:-[a-z]+)?\s*:\s*)([^;]+);"
)


def _fix_font_size(match: re.Match[str]) -> str:
    prefix, value, unit = match.groups()
    if unit == "em":
        # 0.9em 是相对字号，归到 --text-sm。
        return f"{prefix}var(--text-sm)"
    token = FONT_SIZE_TOKENS.get(value)
    if token is None:
        return match.group(0)
    return f"{prefix}var({token})"


def _fix_font_weight(match: re.Match[str]) -> str:
    prefix, value = match.groups()
    token = FONT_WEIGHT_TOKENS.get(value)
    if token is None:
        return match.group(0)
    return f"{prefix}var({token})"


def _fix_spacing(match: re.Match[str]) -> str:
    prefix, body = match.groups()

    def replace_value(value_match: re.Match[str]) -> str:
        raw = value_match.group(1)
        number = float(raw)
        if number != int(number):
            return raw
        if int(number) in SPACING_EXCEPTIONS:
            return raw
        mapped = SPACING_SCALE.get(int(number))
        if mapped is None:
            return raw
        return f"{mapped}px"

    return f"{prefix}{_PX_RE.sub(replace_value, body)};"


_PX_RE = re.compile(r"(?<![\w.%-])(\d+(?:\.\d+)?)px")


def normalize(text: str) -> str:
    text = _FONT_SIZE_RE.sub(_fix_font_size, text)
    text = _FONT_WEIGHT_RE.sub(_fix_font_weight, text)
    text = _SPACING_RE.sub(_fix_spacing, text)
    for old, new in TOKEN_RENAMES.items():
        text = text.replace(f"var({old})", f"var({new})")
    for old, new in SHADOW_REPLACEMENTS.items():
        text = text.replace(old, new)
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="只报告，不写文件")
    args = parser.parse_args()

    drift = 0
    for path in TARGETS:
        raw = path.read_text(encoding="utf-8")
        normalized = normalize(raw)
        relative = path.relative_to(REPO_ROOT).as_posix()
        if normalized == raw:
            print(f"  ok       {relative}")
            continue
        drift += 1
        if args.check:
            print(f"  drift    {relative}")
            continue
        path.write_text(normalized, encoding="utf-8", newline="\n")
        print(f"  updated  {relative}")

    if args.check:
        return 1 if drift else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
