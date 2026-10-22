"""维护 ``data/catalog/agent-index.json`` 的顺序：按 agentId 降序。

    python tools/sort_agent_index.py            # 补 agentId 字段 + 重排 + 写回
    python tools/sort_agent_index.py --check    # 只报告，不写文件

为什么要有这个工具
----------------
映射表是**手工维护**的规范 slug 表，新增代理人时要往里加一条。问题在于：
「加到哪里」没有答案——旧文件是任意顺序，追加到末尾也行、插到中间也行，
于是每加一个人顺序就更乱一次。

而选择页的卡片顺序是**有定义**的：先按评级（S 在前、A 在后），再按 agentId
从大到小（``tools/gen_strategy_guides.py`` 排的）。映射表按同一个 **agentId 降序**
维护，新增的人就有明确的位置可插：``agentId`` 大的排前面。

工具做两件事：

1. **补 ``agentId`` 字段**——条目自带排序键，不必再去猜它是哪个代理人
   （值取自攻略数据的 ``meta.agentId``，没有则取代理人预设的 id）；
2. **按 agentId 降序重排**——解析不出 agentId 的条目（还没公开的代理人）
   排在最后，保持它们之间的相对顺序。

``--check`` 供 CI 用：顺序乱了就退出码非 0，并**告诉你是哪一条该放到第几位**。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = REPO_ROOT / "data" / "catalog" / "agent-index.json"
PRESETS_PATH = REPO_ROOT / "data" / "catalog" / "agents.json"
STRATEGY_ROOT = REPO_ROOT / "strategy"

#: 管道输出固定 UTF-8：Windows 上管道默认用系统代码页（本机 GBK），
# 父工具按 UTF-8 读会抛 UnicodeDecodeError 或读出乱码。控制台输出保持
# 系统代码页，否则用户在自己的终端里会看到乱码。
if hasattr(sys.stdout, "reconfigure") and not sys.stdout.isatty():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

#: 条目里除 agentId 之外的字段，保持原顺序输出。
FIELD_ORDER = ("agentId", "slug", "en", "cn_short", "cn_full")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def agent_id_of(entry: dict, by_name: dict[str, dict]) -> str:
    """取一个条目的 agentId：条目自带 > 攻略数据 > 代理人预设。"""
    existing = entry.get("agentId")
    if isinstance(existing, str) and existing:
        return existing

    slug = entry.get("slug", "")
    data_path = STRATEGY_ROOT / slug / "data" / f"{slug}.json"
    if data_path.is_file():
        data = load_json(data_path)
        agent_id = (data.get("meta") or {}).get("agentId")
        if agent_id:
            return str(agent_id)

    for key in ("cn_full", "cn_short"):
        preset = by_name.get(entry.get(key, ""))
        if preset and preset.get("id"):
            return str(preset["id"])
    return ""


def agent_number(agent_id: str) -> int:
    """``ep-2216`` -> 2216；解析不出时按 0（排最后）。"""
    if agent_id.startswith("ep-"):
        tail = agent_id[3:]
        if tail.isdigit():
            return int(tail)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="只报告，不写文件")
    args = parser.parse_args()

    entries = load_json(INDEX_PATH)
    presets = load_json(PRESETS_PATH)
    by_name = {preset["name"]: preset for preset in presets}

    # 1. 补 agentId
    missing = []
    for entry in entries:
        agent_id = agent_id_of(entry, by_name)
        if not agent_id:
            missing.append(entry.get("slug", "?"))
        entry["agentId"] = agent_id

    # 2. 按 agentId **降序**重排；解析不出的排在最后，保持它们之间的相对顺序
    indexed = list(enumerate(entries))
    indexed.sort(key=lambda pair: (-agent_number(pair[1]["agentId"]), pair[0]))
    sorted_entries = [entry for _, entry in indexed]

    # 3. 字段顺序统一
    shaped = []
    for entry in sorted_entries:
        row = {}
        for field in FIELD_ORDER:
            if field == "agentId" and not entry.get(field):
                continue
            if field in entry:
                row[field] = entry[field]
        shaped.append(row)

    text = json.dumps(shaped, ensure_ascii=False, indent=2)
    current = INDEX_PATH.read_text(encoding="utf-8")

    if args.check:
        problems = []
        if current != text:
            problems.append("映射表不是「补 agentId + 按 agentId 降序」的形态")
            numbers = [agent_number(entry["agentId"]) for entry in shaped]
            for position in range(1, len(numbers)):
                if numbers[position] > numbers[position - 1]:
                    problems.append(
                        f"  第 {position} 条 {shaped[position].get('agentId')} "
                        f"（{shaped[position].get('slug')}）应排在 "
                        f"{shaped[position - 1].get('agentId')} 之前"
                    )
        if problems:
            print("agent-index 顺序检查未通过：")
            for problem in problems:
                print(problem)
            print("运行 `python tools/sort_agent_index.py` 修正。")
            return 1
        # 解析不出 agentId 的条目（还没公开的代理人）是**正常状态**，
        # 只提示、不算失败。
        for slug in missing:
            print(f"  note     {slug} 还没有 agentId（还没公开？）——排在最后")
        print(f"  ok       映射表 {len(shaped)} 条，按 agentId 降序")
        return 0

    if current == text:
        print(f"  ok       映射表 {len(shaped)} 条，已是 agentId 降序")
        return 0

    INDEX_PATH.write_text(text, encoding="utf-8", newline="")
    print(f"已重排 {INDEX_PATH.relative_to(REPO_ROOT)}（{len(shaped)} 条，按 agentId 降序）")
    for slug in missing:
        print(f"  注意：{slug} 解析不出 agentId，排在最后")
    return 0


if __name__ == "__main__":
    sys.exit(main())
