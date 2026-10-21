"""从 canonical 数据生成 frontend/src/constants/strategyGuides.ts。

数据源（按优先级）：
- ``data/catalog/agent-index.json``：slug / 英文名 / 中文名与顺序；
- ``strategy/<slug>/data/<slug>.json``：姓名、agentId、评级/属性/职业图标、立绘；
- ``data/catalog/agents.json``：抓取产物缺少字段时的兜底。

生成顺序为 mapping 的**逆序**（最新代理人优先），与选择页当前展示顺序一致。
新增代理人只需补 mapping + strategy 数据，然后运行本脚本；``--check`` 供 CI 使用。
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
OUTPUT_PATH = REPO_ROOT / "frontend" / "src" / "constants" / "strategyGuides.ts"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_paths import dataset_path  # noqa: E402

#: 数据集路径由 ``data/manifest.json`` 统一登记，此处只取用。
MAPPING_PATH = dataset_path("agent-index")
PRESETS_PATH = dataset_path("agents")

#: 属性/职业/评级 → 图标 slug 映射。与 agent-background Skill 和共享渲染器
#: (renderStrategy.ts) 中的同名表保持一致；这里是生成器侧的唯一真实源。
ATTRIBUTE_SLUGS = {
    "火": "fire", "冰": "ice", "电": "electric", "以太": "ether",
    "物理": "physical", "烈霜": "frost", "玄墨": "auric-ink",
    "凛刃": "honed-edge", "风": "wind", "流明": "lumiflux",
}
ROLE_SLUGS = {
    "强攻": "attack", "击破": "stun", "异常": "anomaly", "支援": "support",
    "防护": "defense", "命破": "rupture", "锋御": "armorer",
}
GRADE_SLUGS = {"S": "s", "A": "a"}


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
        short_name = item.get("cn_short") or name
        entry = {
            "slug": slug,
            "name": name,
            "shortName": short_name,
            "en": item.get("en") or "",
            "agentId": agent_id,
        }
        if assets.get("tachie"):
            entry["tachie"] = assets["tachie"]
        # 图标解析：优先取抓取产物的 profile.icons，缺失时从预设数据
        # (attribute/roleTag/grade) 推导，保证字段永不缺位。
        attr_label = profile.get("attribute") or preset.get("attribute") or ""
        role_label = profile.get("roleTag") or preset.get("roleTag") or ""
        grade_label = profile.get("grade") or preset.get("grade") or ""

        grade_icon = icons.get("grade") or (
            f"/images/grades/{GRADE_SLUGS[grade_label]}.webp" if grade_label in GRADE_SLUGS else ""
        )
        attribute_icon = icons.get("attribute") or (
            f"/images/attributes/{ATTRIBUTE_SLUGS[attr_label]}.webp" if attr_label in ATTRIBUTE_SLUGS else ""
        )
        role_icon = icons.get("profession") or (
            f"/images/icons/{ROLE_SLUGS[role_label]}.webp" if role_label in ROLE_SLUGS else ""
        )
        if grade_icon:
            entry["gradeIcon"] = grade_icon
        if attribute_icon:
            entry["attributeIcon"] = attribute_icon
        if role_icon:
            entry["roleIcon"] = role_icon
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
        "  shortName: string;",
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
        for key in ("slug", "name", "shortName", "en", "agentId", "tachie", "gradeIcon", "attributeIcon", "roleIcon"):
            if key in entry:
                lines.append(f"    {key}: {ts(entry[key])},")
        lines.append("  },")
    lines.extend(
        [
            "];",
            "",
            "export function agentPortraitUrl(agentId: string): string {",
            "  return `/images/agents/${agentId}.webp`;",
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
