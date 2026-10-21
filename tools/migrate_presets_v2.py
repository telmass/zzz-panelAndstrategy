"""把代理人 / 音擎预设从 v1 形状迁移到 v2 形状。

    python tools/migrate_presets_v2.py            # 就地改写
    python tools/migrate_presets_v2.py --check    # 只报告，不写文件

v1 → v2 的变化
--------------
**代理人**

| v1 | v2 |
| --- | --- |
| ``base``（缺键表示「官方未提供」） | 不变 |
| ``unavailableBaseStats``（同一事实的第二份表达） | 删除——由 ``base`` 的缺键派生 |
| ``additionalBaseStats`` | ``baseExtra`` |
| ``unmodeledBaseStats`` | ``baseUnmodeled`` |
| ``coreBonuses`` | ``core`` |
| ``coreBonuses[].perRankValue`` | ``core[].perRank`` |
| ``coreBonuses[].totalValue`` | 保留（见下） |
| ``coreBonuses[].unit`` | 保留（见下） |

**音擎**

| v1 | v2 |
| --- | --- |
| ``baseKind`` + ``baseAttack`` + ``baseDefense`` | ``base: {kind, value}`` |

关于 ``totalValue`` 与 ``unit``
------------------------------
它们确实可由规则表推出（``totalValue = 选项值 × 槽位数``、``unit`` 由选项
``kind`` 决定），但**保留**在数据里：

接口响应与源 JSON **逐条等价**是本项目的一条硬性质——正因为它，前端才能删掉
自己的数据副本、接口给出的就是源数据。一旦响应改为「源字段 + 运行时派生
字段」，这条性质就破了，代价远大于省下两个字段。

冗余不会悄悄漂移：``presets/validate.py`` 逐条核对
``每级数值 × 位次数 == 合计 == 选项值 × 槽位数``，任何一处对不上即加载失败。


本脚本是**一次性迁移**工具，保留在仓库里是为了让「这份数据是怎么变成现在
这个形状的」有据可查。Skill 抓取脚本已直接产出 v2 形状，重抓不需要再跑它。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_paths import dataset_path  # noqa: E402
import sync_presets  # noqa: E402


def migrate_agent(agent: dict[str, Any]) -> dict[str, Any]:
    """一名代理人，v1 → v2。已是 v2 形状时原样返回（幂等）。"""
    if "core" in agent and "coreBonuses" not in agent:
        return agent

    base = agent.get("base", {})

    core: list[dict[str, Any]] = []
    for bonus in agent.get("coreBonuses", []):
        item = {
            "optionId": bonus["optionId"],
            "ranks": list(bonus["ranks"]),
            "label": bonus["label"],
            "perRank": bonus["perRankValue"],
            "totalValue": bonus["totalValue"],
            "unit": bonus["unit"],
        }
        if bonus.get("optionCount"):
            item["optionCount"] = bonus["optionCount"]
        core.append(item)

    migrated = {
        key: value
        for key, value in agent.items()
        if key not in {"base", "unavailableBaseStats", "additionalBaseStats",
                       "unmodeledBaseStats", "coreBonuses"}
    }
    migrated["base"] = base
    if agent.get("additionalBaseStats"):
        migrated["baseExtra"] = agent["additionalBaseStats"]
    if agent.get("unmodeledBaseStats"):
        migrated["baseUnmodeled"] = agent["unmodeledBaseStats"]
    migrated["core"] = core
    return migrated


def migrate_weapon(weapon: dict[str, Any]) -> dict[str, Any]:
    """一件音擎，v1 → v2。已是 v2 形状时原样返回（幂等）。"""
    if "base" in weapon and "baseKind" not in weapon:
        return weapon

    kind = weapon["baseKind"]
    value = weapon.get("baseAttack") if kind == "atk" else weapon.get("baseDefense")
    migrated = {
        key: value_
        for key, value_ in weapon.items()
        if key not in {"baseKind", "baseAttack", "baseDefense"}
    }
    migrated["base"] = {"kind": kind, "value": value or 0.0}
    return migrated


def _dump(items: list[dict[str, Any]]) -> str:
    return json.dumps(items, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="只报告，不写文件")
    args = parser.parse_args()

    plan = (
        ("agents", dataset_path("agents"), migrate_agent, True),
        ("weapons", dataset_path("weapons"), migrate_weapon, False),
    )

    drift = 0
    for name, path, migrate, is_agent in plan:
        raw = path.read_text(encoding="utf-8")
        items = json.loads(raw)
        migrated = [
            sync_presets.order_preset(migrate(item), agent=is_agent) for item in items
        ]
        text = _dump(migrated)
        if text == raw:
            print(f"  ok       {name}")
            continue
        drift += 1
        if args.check:
            print(f"  drift    {name}（尚未迁移到 v2）")
            continue
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"  updated  {name}（{len(migrated)} 条）")

    if args.check:
        return 1 if drift else 0
    print("迁移完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
