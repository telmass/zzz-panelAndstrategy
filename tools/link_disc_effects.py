"""给驱动盘套装数据补 ``effect2``（2 件套效果 -> 规则表 setOptions 的 id）。

    python tools/link_disc_effects.py            # 就地改写
    python tools/link_disc_effects.py --check    # 只报告

为什么需要这一列
----------------
计算器的「二件套效果」下拉列的是**效果**（12 项 ``setOptions``），不是**套装**。
要知道某套装的 2 件套效果对应哪个可选项，就得有一张映射——``effect2`` 就是它。

映射不了的两类
--------------
30 套里有 **12 套的 2 件套效果不在可算范围**：

- **属性伤害**（8 套）：以太 / 冰 / 火 / 电 / 风 属性伤害 +10%。面板**没有
  「属性伤害」这一行**——加一行会破坏三方对拍（参照实现的行集是固定的）。
- **条件触发**（4 套）：如「[普通攻击]造成的伤害提升15%」「攻击造成的失衡值提升6%」
  「施加的护盾值+15%」——它们不是固定面板值。

这两类写 ``effect2: null`` 并用 ``effect2Note`` 说明原因，UI 据此说明
「该套装的 2 件套效果不计入面板」，而不是让用户选完发现数字没变。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_paths import dataset_path  # noqa: E402

#: 2 件套效果文本 -> 规则表 setOptions 的 id。文本已归一（去句号、全角加号转半角）。
EFFECT_TO_OPTION = {
    "物理伤害+10%": "dmg_10",
    "攻击力+10%": "atk_pct_10",
    "防御力+16%": "def_pct_16",
    "暴击率+8%": "cr_8",
    "暴击伤害+16%": "cd_16",
    "冲击力+6%": "impact_pct_6",
    "异常掌控+8%": "ac_pct_8",
    "能量自动回复+20%": "er_pct_20",
    "异常精通+30点": "am_30",
    "生命值+10%": "hp_pct_10",
    "穿透率+8%": "pr_8",
}

#: 算不出来的 2 件套效果 -> 原因。
UNMAPPED_REASON = {
    "以太伤害+10%": "属性伤害",
    "冰属性伤害+10%": "属性伤害",
    "火属性伤害+10%": "属性伤害",
    "电属性伤害+10%": "属性伤害",
    "风属性伤害+10%": "属性伤害",
    "[普通攻击]造成的伤害提升15%": "条件触发",
    "[追加攻击]和[冲刺攻击]造成的伤害提升15%": "条件触发",
    "攻击造成的失衡值提升6%": "条件触发",
    "施加的护盾值+15%": "条件触发",
}


def normalize(text: str) -> str:
    """归一 2 件套效果文本：去句号、全角加号转半角、去掉空白。"""
    return (
        text.replace("＋", "+")
        .replace("。", "")
        .replace(" ", "")
        .replace("　", "")
        .strip()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="只报告，不写文件")
    args = parser.parse_args()

    path = dataset_path("drive-discs")
    items = json.loads(path.read_text(encoding="utf-8"))

    unknown: list[str] = []
    changed = 0
    for item in items:
        text = normalize(item["setEffect2"])
        if text in EFFECT_TO_OPTION:
            new = {"effect2": EFFECT_TO_OPTION[text]}
        elif text in UNMAPPED_REASON:
            new = {"effect2": None, "effect2Note": UNMAPPED_REASON[text]}
        else:
            unknown.append(f"{item['name']}：{item['setEffect2']}")
            continue
        if item.get("effect2") != new["effect2"] or item.get("effect2Note") != new.get("effect2Note"):
            changed += 1
        # 键序：effect2 / effect2Note 放在 image 之后。
        item.pop("effect2", None)
        item.pop("effect2Note", None)
        item.update(new)

    if unknown:
        print("无法归类的 2 件套效果（请补表）：", file=sys.stderr)
        for line in unknown:
            print(f"  {line}", file=sys.stderr)
        return 2

    if args.check:
        print(f"  drift    {changed} 套待补 effect2" if changed else "  ok       effect2 已齐全")
        return 1 if changed else 0

    ordered = []
    for item in items:
        row = {}
        for key in ("id", "name", "source", "setEffect2", "setEffect4", "image", "effect2", "effect2Note"):
            if key in item:
                row[key] = item[key]
        ordered.append(row)

    path.write_text(
        json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    mappable = sum(1 for item in ordered if item.get("effect2"))
    print(
        f"  updated  {path.name}（{len(ordered)} 套：{mappable} 套可算，"
        f"{len(ordered) - mappable} 套不可算）"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
