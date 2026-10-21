"""刷新 / 校验数据集登记表 ``data/manifest.json``。

    python tools/sync_manifest.py            # 刷新 count 与 sha256
    python tools/sync_manifest.py --check    # 只校验，有漂移则退出码 1

manifest 里有两类字段
--------------------
- **人工维护**：``id`` / ``path`` / ``role`` / ``maintained`` / ``generator`` /
  ``schema`` / ``distribution``。改路径只动这里。
- **派生**���``count``（条目数）与 ``sha256``（内容摘要）。由本脚本写入与校验。

为什么要派生字段
----------------
``count`` 能在数据被**整体覆盖但写坏**（截断、漏条目）时立刻发现——数据量变了
却没同步 manifest，说明这批数据不是有意改的。``sha256`` 额外记录「这批数据
什么时候变过」，便于排查「线上供的是哪一版」。

因为是派生值，改完数据要重跑一次本脚本（与既有的 ``sync_presets.py --options``
同属数据闸门）。仓库根 ``data/`` 下若出现未登记的 JSON 文件，本脚本报孤儿错误
——这正是「某个工具偷偷写了个文件进 data/」的发现方式。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys

# 管道输出固定 UTF-8：Windows 上管道默认用系统代码页（本机 GBK），
# 父工具按 UTF-8 读会抛 UnicodeDecodeError 或读出乱码。控制台输出保持
# 系统代码页，否则用户在自己的终端里会看到乱码。
if hasattr(sys.stdout, "reconfigure") and not sys.stdout.isatty():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_paths import DATA_DIR, MANIFEST_PATH, dataset_ids  # noqa: E402

#: ``data/`` 下不参与「孤儿文件」判定的固定文件。
_ALLOWED_FILES = {"manifest.json", "README.md"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _count_items(payload: Any) -> int:
    """条目数：顶层是数组就数长度；顶层是对象就数其下所有数组的长度之和。"""
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        return sum(
            len(value) for value in payload.values() if isinstance(value, list)
        )
    return 0


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path.name} 不是合法 JSON：{error}") from error


def _collect_orphans() -> list[str]:
    """``data/`` 下未登记的文件。"""
    registered = set()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for entry in manifest["datasets"].values():
        registered.add(entry["path"])
    orphans = []
    for path in sorted(DATA_DIR.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(DATA_DIR).as_posix()
        if relative in _ALLOWED_FILES or relative in registered:
            continue
        orphans.append(relative)
    return orphans


def refresh(check_only: bool) -> int:
    """刷新或校验 manifest 的派生字段。返回 0 表示一致，1 表示有漂移。"""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    datasets = manifest["datasets"]
    drift = 0
    failures: list[str] = []

    for name in sorted(datasets):
        entry = datasets[name]
        path = DATA_DIR / entry["path"]
        if not path.is_file():
            failures.append(f"{name}：缺少文件 {path}")
            drift += 1
            continue
        try:
            payload = _read_json(path)
        except ValueError as error:
            failures.append(f"{name}：{error}")
            drift += 1
            continue

        count = _count_items(payload)
        digest = _sha256(path)
        if entry.get("count") != count or entry.get("sha256") != digest:
            if check_only:
                drift += 1
                print(f"  drift    {name}（count/sha256 与磁盘不符）")
            else:
                entry["count"] = count
                entry["sha256"] = digest
                print(f"  updated  {name}（{count} 条）")

    orphans = _collect_orphans()
    if orphans:
        failures.append(f"data/ 下有未登记的文件：{orphans}")
        drift += 1

    if check_only:
        if drift:
            print(f"存在漂移：{drift} 项。运行 `python tools/sync_manifest.py` 刷新。")
        else:
            print(f"  ok       {MANIFEST_PATH.name}（{len(datasets)} 个数据集）")
    else:
        MANIFEST_PATH.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"已刷新：{MANIFEST_PATH.name}（{len(datasets)} 个数据集）")

    for message in failures:
        print(f"错误：{message}", file=sys.stderr)
    return 1 if drift else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="只校验不写文件；有漂移或孤儿文件时退出码 1",
    )
    args = parser.parse_args()

    try:
        return refresh(args.check)
    except (OSError, ValueError, KeyError) as error:
        print(f"错误：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
