"""为攻略编辑数据的每条主词条预留备注字段。

用法（仓库根）::

    python tools/seed_main_stat_notes.py
    python tools/seed_main_stat_notes.py --check

只处理 ``strategy/*/data/*.strategy.json`` 中的 ``driveBuilds[].mainStats[]``：

- 缺少 ``note`` 时补 ``""``；
- 已有非空 ``note`` 不覆盖；
- 不新增/删除其它字段，不改动 mainStats 的顺序。

``--check`` 只报告，不做写入；有缺失时退出码 1，可接进 CI。
"""

from __future__ import annotations

import argparse
import json
import sys

# 管道输出固定 UTF-8：Windows 上管道默认用系统代码页（本机 GBK），
# 父工具按 UTF-8 读会抛 UnicodeDecodeError 或读出乱码。控制台输出保持
# 系统代码页，否则用户在自己的终端里会看到乱码。
if hasattr(sys.stdout, "reconfigure") and not sys.stdout.isatty():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = REPO_ROOT / "strategy"


def strategy_files() -> list[Path]:
    return sorted(STRATEGY_ROOT.glob("*/data/*.strategy.json"))


def seed(path: Path) -> tuple[dict, int, int, list[str]]:
    """返回 (数据, 条目数, 新增 note 数, 问题列表)。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    builds = data.get("driveBuilds") if isinstance(data, dict) else None
    if not isinstance(builds, list):
        return data, 0, 0, []

    total = 0
    added = 0
    problems: list[str] = []
    for build_index, build in enumerate(builds):
        if not isinstance(build, dict):
            continue
        stats = build.get("mainStats")
        if not isinstance(stats, list):
            continue
        for stat_index, stat in enumerate(stats):
            if not isinstance(stat, dict):
                problems.append(
                    f"{path.relative_to(REPO_ROOT)} driveBuilds[{build_index}].mainStats[{stat_index}] 不是对象"
                )
                continue
            total += 1
            if "note" not in stat:
                stat["note"] = ""
                added += 1
            elif not isinstance(stat["note"], str):
                problems.append(
                    f"{path.relative_to(REPO_ROOT)} driveBuilds[{build_index}].mainStats[{stat_index}].note 不是字符串"
                )
    return data, total, added, problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="只检查，不写文件")
    args = parser.parse_args()

    total_entries = 0
    total_added = 0
    problems: list[str] = []

    for path in strategy_files():
        data, entries, added, issues = seed(path)
        total_entries += entries
        total_added += added
        problems.extend(issues)
        if added and not args.check:
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            print(f"已补 note: {path.relative_to(REPO_ROOT)} (+{added})")

    if problems:
        print("\n".join(problems))
        return 1

    if args.check:
        missing = total_added
        if missing:
            print(f"{missing} 条 mainStats 缺少 note；运行 python tools/seed_main_stat_notes.py")
            return 1
        print(f"mainStats note 字段完整（{total_entries} 条）")
        return 0

    print(f"完成：{len(strategy_files())} 个文件，{total_entries} 条 mainStats，新增 note {total_added} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
