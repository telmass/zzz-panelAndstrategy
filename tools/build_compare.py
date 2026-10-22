"""配装对比报告：音擎 / 主词条 / 两档门槛。

用法::

    python tools/build_compare.py                 # 全部攻略页
    python tools/build_compare.py roxy caesar     # 只算这几份
    python tools/build_compare.py --out data/reports/build-compare.json

产出三样（口径见 ``docs/design/damage-formulas.md``）：

1. **音擎对比**（D1-Wpn）：该页推荐的每把音擎各算一次伤害，看差多少。
2. **主词条取舍**（D1-Main）：4/5/6 号位各选项的伤害排序——**含副词条联动重排**
   （选了某个主词条，那一盘就不能再出同名的副词条）。
3. **两档门槛**（D1-Tier）：从满配逐步减条数，得到「多少条 = 多少伤害」。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_SCRIPT = (
    ROOT / ".github" / "skills" / "agent-strategy" / "scripts" / "calc_graduation_panel.py"
)
STRATEGY_DIR = ROOT / "strategy"
CATALOG = ROOT / "data" / "catalog"
DEFAULT_OUT = ROOT / "data" / "reports" / "build-compare.json"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CALC = _load("calc_graduation_panel", SKILL_SCRIPT)


def _service():
    backend_src = ROOT / "backend" / "src"
    if str(backend_src) not in sys.path:
        sys.path.insert(0, str(backend_src))
    from zzz_panel.services import compare_service

    return compare_service


compare = _service()


def _agent_preset(agent_id: str, agents: list[dict]) -> dict | None:
    """按 id 取代理人预设（面板模式 + 定位 + 基础面板）。"""
    for agent in agents:
        if agent.get("id") == agent_id:
            return agent
    return None


def _weapon_candidates(page: dict, weapons_by_name: dict) -> list[dict]:
    """该页推荐的音擎 -> 音擎条目（按名字查目录）。"""
    names: list[str] = []
    for entry in page.get("weapons") or []:
        for item in entry.get("items") or []:
            name = item.get("name")
            if name and name not in names:
                names.append(name)
    candidates = []
    for name in names:
        weapon = weapons_by_name.get(name)
        if weapon:
            candidates.append(weapon)
    return candidates


def build_report(slugs: list[str] | None) -> dict:
    agents = json.loads((CATALOG / "agents.json").read_text(encoding="utf-8"))
    weapons = json.loads((CATALOG / "weapons.json").read_text(encoding="utf-8"))
    weapons_by_name = {item["name"]: item for item in weapons}

    report: dict[str, dict] = {}
    for path in sorted(STRATEGY_DIR.glob("*/data/*.strategy.json")):
        slug = path.parent.parent.name
        if slugs and slug not in slugs:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        panel = data.get("graduationPanel") or {}
        spec = panel.get("buildSpec")
        if not spec:
            report[slug] = {"status": "no-buildSpec"}
            continue
        args = CALC.args_from_build_spec(spec)
        request, _ = CALC.build_request(args)
        agent = _agent_preset(spec.get("agentId"), agents)
        # 路径由**面板模式 + 定位**决定（命破 → 贯穿、锋御 → 锐化、异常定位 → 异常）
        from zzz_panel.services.damage_service import path_for_agent

        damage_path = path_for_agent(
            (agent or {}).get("panelMode", "") if isinstance(agent, dict) else "",
            (agent or {}).get("roleTag", "") if isinstance(agent, dict) else "",
        )

        weapons_cmp = compare.compare_weapons(
            request,
            _weapon_candidates(data, weapons_by_name),
            path=damage_path,
            agent=agent,
        )
        main_stats = {
            slot: compare.compare_main_stats(
                request, slot=slot, path=damage_path, agent=agent
            )
            for slot in ("disc4", "disc5", "disc6")
        }
        tier = compare.tier_curve(request, path=damage_path, agent=agent)
        report[slug] = {
            "status": "ok",
            "agent": panel.get("build", {}).get("agent"),
            "path": damage_path,
            "weapons": weapons_cmp,
            "mainStats": main_stats,
            "tier": tier,
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("slugs", nargs="*", help="只算这些 slug（默认全部）")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="报告输出路径")
    args = parser.parse_args()

    report = build_report(args.slugs or None)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    ok = [slug for slug, item in report.items() if item.get("status") == "ok"]
    print(f"已算 {len(ok)} 份，跳过 {len(report) - len(ok)} 份（没有 buildSpec）")
    for slug in ok[:5]:
        item = report[slug]
        best = item["weapons"][0] if item["weapons"] else None
        if best:
            print(f"  {slug}：音擎最优 {best['name']}（{best['damage']:.0f}）")
    print(f"报告：{out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
