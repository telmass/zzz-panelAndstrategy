"""从攻略抓取产物里移除 ``basePanel``。

    python tools/strip_strategy_base_panel.py            # 就地改写
    python tools/strip_strategy_base_panel.py --check    # 只报告

基础面板的**唯一真实源是代理人预设**（``data/catalog/agents.json``）。攻略
JSON 曾各存一份 ``basePanel``，于是 61 份攻略里有了 61 份同样的数字——两份
数据一旦漂移，攻略页显示的面板就会和计算器算出的对不上（这件事已经发生过：
三名代理人的属性名口径在两处不一致）。

本脚本是一次性迁移工具。抓取脚本已改为不再写该字段，重抓不需要再跑它。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = REPO_ROOT / "strategy"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="只报告，不写文件")
    args = parser.parse_args()

    changed = 0
    for path in sorted(STRATEGY_ROOT.glob("*/data/*.json")):
        if path.name.endswith(".strategy.json"):
            continue
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        if "basePanel" not in data:
            continue
        changed += 1
        if args.check:
            print(f"  drift    {path.relative_to(REPO_ROOT)}")
            continue
        del data["basePanel"]
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"  updated  {path.relative_to(REPO_ROOT)}")

    if args.check:
        if changed:
            print(f"仍有 {changed} 份攻略 JSON 带着 basePanel。")
            return 1
        print("攻略 JSON 均已不含 basePanel。")
        return 0
    print(f"处理完成，共 {changed} 份。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
