"""从 canonical 数据生成 frontend/src/constants/strategyGuides.ts。

数据源（按优先级）：
- ``data/agent-name-mapping.json``：slug / 英文名 / 中文名与顺序；
- ``strategy/<slug>/data/<slug>.json``：姓名、agentId、评级/属性/职业图标、立绘；
- ``data/agent-presets.json``：抓取产物缺少字段时的兜底。

生成顺序为 mapping 的**逆序**（最新代理人优先），与选择页当前展示顺序一致。
新增代理人只需补 mapping + strategy 数据，然后运行本脚本；``--check`` 供 CI 使用。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MAPPING_PATH = REPO_ROOT / "data" / "agent-name-mapping.json"
PRESETS_PATH = REPO_ROOT / "data" / "agent-presets.json"
OUTPUT_PATH = REPO_ROOT / "frontend" / "src" / "constants" / "strategyGuides.ts"


def ts(value: str) -> str:
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def build_entries() -> list[dict[str, str]]:
    mapping = load_json(MAPPING_PATH)
    presets = load_json(PRESETS_PATH)
    by_name: dict[str, dict] = {}
    for preset in presets:
        by_name[preset["name"]] = preset

    entries: list[dict[str, str]] = []
    for item in reversed(mapping):
        slug = item["slug"]
        data_path = REPO_ROOT / "strategy" / slug / "data" / f"{slug}.json"
        if not data_path.exists():
            continue
        data = load_json(data_path)
        profile = data.get("profile") or {}
        assets = data.get("assets") or {}
        icons = profile.get("icons") or {}
        meta = data.get("meta") or {}
        preset = by_name.get(item.get("cn_full")) or by_name.get(item.get("cn_short")) or {}

        agent_id = meta.get("agentId") or preset.get("id") or ""
        name = profile.get("name") or item.get("cn_full") or item.get("cn_short") or slug
        entry = {
            "slug": slug,
            "name": name,
            "en": item.get("en") or "",
            "agentId": agent_id,
        }
        if assets.get("tachie"):
            entry["tachie"] = assets["tachie"]
        if icons.get("grade"):
            entry["gradeIcon"] = icons["grade"]
        if icons.get("attribute"):
            entry["attributeIcon"] = icons["attribute"]
        if icons.get("profession"):
            entry["roleIcon"] = icons["profession"]
        entries.append(entry)
    return entries


def render(entries: list[dict[str, str]]) -> str:
    lines = [
        "/**",
        " * 攻略板块登记表：由 `tools/gen_strategy_guides.py` 从 mapping 与 strategy 数据生成。",
        " * 不要手工编辑；新增代理人后运行 `python tools/gen_strategy_guides.py`。",
        " * 顺序为 mapping 逆序（最新代理人优先），同时决定 `/strategy` 选择页的卡片顺序。",
        " */",
        "export interface StrategyGuide {",
        "  slug: string;",
        "  name: string;",
        "  en: string;",
        "  agentId: string;",
        "  tachie?: string;",
        "  gradeIcon?: string;",
        "  attributeIcon?: string;",
        "  roleIcon?: string;",
        "}",
        "",
        "export const strategyGuides: StrategyGuide[] = [",
    ]
    for entry in entries:
        lines.append("  {")
        for key in ("slug", "name", "en", "agentId", "tachie", "gradeIcon", "attributeIcon", "roleIcon"):
            if key in entry:
                lines.append(f"    {key}: {ts(entry[key])},")
        lines.append("  },")
    lines.extend(
        [
            "];",
            "",
            "export function agentPortraitUrl(agentId: string): string {",
            "  return `/images/agents/${agentId}.png`;",
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="只检查，不写文件")
    args = parser.parse_args()

    entries = build_entries()
    content = render(entries)
    current = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""

    if args.check:
        if current != content:
            print(f"{OUTPUT_PATH.relative_to(REPO_ROOT)} 已漂移；运行 python tools/gen_strategy_guides.py 重新生成")
            return 1
        print(f"{OUTPUT_PATH.relative_to(REPO_ROOT)} 与数据一致（{len(entries)} 条）")
        return 0

    OUTPUT_PATH.write_text(content, encoding="utf-8", newline="\n")
    print(f"写入 {OUTPUT_PATH.relative_to(REPO_ROOT)}（{len(entries)} 条）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
