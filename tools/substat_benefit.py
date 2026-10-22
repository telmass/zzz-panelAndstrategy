"""副词条边际收益 / 等效换算 / 优先级验证——按攻略页的 buildSpec 逐个算。

用法::

    python tools/substat_benefit.py                      # 全部攻略页，写报告
    python tools/substat_benefit.py roxy caesar          # 只算这几个
    python tools/substat_benefit.py --out data/reports/substat-benefit.json

产出（三样）：

1. **边际收益曲线**：每条副词条加 N 条的伤害增量（面板层 → 伤害层）。
2. **等效换算**：1 条 X ≈ 多少条暴击率。
3. **优先级验证**：把攻略页 ``driveBuilds[].subPriority`` 写的「> / = / ≈」
   逐对拿去比——**不成立的会被点名**。

口径见 ``docs/design/damage-formulas.md``；引擎见
``backend/src/zzz_panel/core/damage/``。
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
DEFAULT_OUT = ROOT / "data" / "reports" / "substat-benefit.json"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CALC = _load("calc_graduation_panel", SKILL_SCRIPT)


def _service():
    """加载后端服务层（需要 pydantic，用仓库的 venv）。"""
    backend_src = ROOT / "backend" / "src"
    if str(backend_src) not in sys.path:
        sys.path.insert(0, str(backend_src))
    from zzz_panel.services import benefit_service

    return benefit_service


benefit = _service()


def _agent_preset(agent_id: str) -> dict | None:
    """代理人的定位（roleTag）——「异常」定位走异常伤害路径。"""
    agents = json.loads(
        (ROOT / "data" / "catalog" / "agents.json").read_text(encoding="utf-8")
    )
    for agent in agents:
        if agent.get("id") == agent_id:
            return agent
    return None


def request_from_spec(spec: dict):
    """``buildSpec`` -> ``PanelRequest``（复用毕业面板脚本的转换）。"""
    args = CALC.args_from_build_spec(spec)
    request, _ = CALC.build_request(args)
    return request


def build_report(slugs: list[str] | None) -> dict:
    benefit = _service()
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
        request = request_from_spec(spec)
        # 路径按代理人的**定位**选：定位「异常」走异常路径，否则异常精通的收益恒为 0
        agent = _agent_preset(spec.get("agentId"))
        # 路径按**面板模式 + 定位**决定（命破 → 贯穿、锋御 → 锐化、异常定位 → 异常）
        path = benefit.path_for_role(
            (agent or {}).get("roleTag", ""), (agent or {}).get("panelMode", "")
        )
        values = benefit.one_roll_values(request, path=path, agent=agent)
        equivalences = benefit.equivalence(request, path=path, agent=agent)
        chains = []
        checks_by_build: dict[str, list] = {}
        for build in data.get("driveBuilds") or []:
            chain = build.get("subPriority") or []
            if not chain:
                continue
            checks = benefit.verify_priority(request, chain, path=path, agent=agent)
            checks_by_build[build.get("name")] = checks
            chains.append(
                {
                    "name": build.get("name"),
                    "checks": checks,
                    "off": [c for c in checks if c["verdict"] == "off"],
                }
            )
        report[slug] = {
            "status": "ok",
            "agent": panel.get("build", {}).get("agent"),
            "path": path,
            "oneRollValues": values,
            "equivalence": equivalences,
            "chains": chains,
            "_checksByBuild": checks_by_build,
        }
    return report


def suggest_symbol(check: dict, tolerance: float = 0.05) -> tuple[str, str]:
    """给一对比较一个**建议符号**与理由。

    自动校正只做**事实性**修正：

    - 「=」/「≈」被实算否定（比值明显偏离 1）→ 改成「>」——编辑声明的是**等价**，
      实算说差得远，这是事实错误，改。
    - 「>」但实算几乎相等 → 改成「≈」——严格优先实为近似，改。
    - 「>」但实算**方向相反** → **不改**，交给人看（链的顺序要整体调整，
      自动重排风险太大）。
    - 「na」（伤害口径评价不了的：生存项 / 异常角色的常规暴击）→ **不改**。
    """
    sign = check.get("sign", "")
    ratio = check.get("ratio")
    if check.get("verdict") == "na" or ratio is None:
        return sign, "伤害口径评价不了，保持原样"
    if sign in ("=", "≈"):
        if ratio > 1.0 + tolerance:
            return ">", "等号被实算否定（比值 {:.3f}），改为严格优先".format(ratio)
        return sign, "等价成立，保持原样"
    if sign == ">":
        if ratio < 1.0 - tolerance:
            return sign, "实算方向相反（比值 {:.3f}），需人工确认顺序".format(ratio)
        if abs(ratio - 1.0) <= tolerance:
            return "≈", "实算几乎相等（比值 {:.3f}），严格优先改为近似".format(ratio)
        return sign, "严格优先成立，保持原样"
    return sign, "保持原样"


def apply_corrections(report: dict) -> list[dict]:
    """按实算结果修正攻略页的 ``subPriority``；返回改动清单。

    两类修正：

    1. **符号**（事实性）：「=」/「≈」被实算否定 → 改成「>」；「>」但实算几乎相等 → 改成「≈」。
    2. **顺序**（相邻交换）：相邻两项的实算价值**明显反序**（后者高 5% 以上且都 > 0）
       → 交换它们。**生存项**（价值 0，伤害口径评价不了）不参与交换，留在原位。

    方向反了但不相邻的情况不处理——那要重排整条链，是编辑判断。
    """
    changes: list[dict] = []
    for path in sorted(STRATEGY_DIR.glob("*/data/*.strategy.json")):
        slug = path.parent.parent.name
        data = json.loads(path.read_text(encoding="utf-8"))
        touched = False
        checks_by_build = report.get(slug, {}).get("_checksByBuild") or {}
        values = report.get(slug, {}).get("oneRollValues") or {}
        # values 以**副词条 id** 为键（oneRollValues 的原样）
        label_value = values
        for build in data.get("driveBuilds") or []:
            chain = build.get("subPriority") or []
            checks = checks_by_build.get(build.get("name")) or []
            # ① 符号修正
            for index, check in enumerate(checks):
                if index >= len(chain) - 1:
                    break
                suggested, reason = suggest_symbol(check)
                if suggested and suggested != chain[index].get("next"):
                    changes.append(
                        {
                            "slug": slug,
                            "build": build.get("name"),
                            "kind": "符号",
                            "pair": "{} {} {}".format(
                                chain[index].get("label"),
                                chain[index].get("next"),
                                chain[index + 1].get("label"),
                            ),
                            "from": chain[index].get("next"),
                            "to": suggested,
                            "ratio": check.get("ratio"),
                            "reason": reason,
                        }
                    )
                    chain[index]["next"] = suggested
                    touched = True
            # ② 相邻反序 -> 交换（只动可评价的项）
            for index in range(len(chain) - 1):
                a_id = benefit.SUBSTAT_BY_LABEL.get(chain[index].get("label"))
                b_id = benefit.SUBSTAT_BY_LABEL.get(chain[index + 1].get("label"))
                if not a_id or not b_id:
                    continue
                a_value = label_value.get(a_id, 0.0)
                b_value = label_value.get(b_id, 0.0)
                if a_value <= 0.0 or b_value <= 0.0:
                    continue  # 生存项留在原位
                if b_value <= a_value * 1.05:
                    continue
                changes.append(
                    {
                        "slug": slug,
                        "build": build.get("name"),
                        "kind": "顺序",
                        "pair": "{} / {}".format(
                            chain[index].get("label"), chain[index + 1].get("label")
                        ),
                        "from": "{} > {}".format(
                            chain[index].get("label"), chain[index + 1].get("label")
                        ),
                        "to": "{} > {}".format(
                            chain[index + 1].get("label"), chain[index].get("label")
                        ),
                        "ratio": (b_value / a_value) if a_value else None,
                        "reason": "相邻两项实算反序",
                    }
                )
                chain[index]["label"], chain[index + 1]["label"] = (
                    chain[index + 1]["label"],
                    chain[index]["label"],
                )
                chain[index]["next"] = ">"
                touched = True
        if touched:
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("slugs", nargs="*", help="只算这些 slug（默认全部）")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="报告输出路径")
    parser.add_argument("--stdout", action="store_true", help="同时打到标准输出")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="按实算结果**修正**攻略页的优先级链（只改事实性错误；方向反的只报告）",
    )
    args = parser.parse_args()

    report = build_report(args.slugs or None)
    if args.apply:
        changes = apply_corrections(report)
        print(f"已修正 {len(changes)} 处优先级链")
        for change in changes[:10]:
            print(
                "  {} · {}：{} → {}（比值 {}）".format(
                    change["slug"],
                    change["build"],
                    change["pair"],
                    change["to"],
                    change["ratio"],
                )
            )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    ok = [slug for slug, item in report.items() if item.get("status") == "ok"]
    skipped = [slug for slug, item in report.items() if item.get("status") != "ok"]
    def _rows(item, verdict):
        return [
            {"build": chain["name"], "pair": f'{c["a"]} {c["sign"]} {c["b"]}', "ratio": c["ratio"]}
            for chain in item["chains"]
            for c in chain["checks"]
            if c["verdict"] == verdict
        ]

    off = {}
    na = {}
    for slug, item in report.items():
        if item.get("status") != "ok":
            continue
        rows = _rows(item, "off")
        if rows:
            off[slug] = rows
        rows = _rows(item, "na")
        if rows:
            na[slug] = rows

    print(f"已算 {len(ok)} 份，跳过 {len(skipped)} 份（没有 buildSpec）")
    if off:
        print(f"优先级链与实算不一致：{len(off)} 份")
        for slug, rows in off.items():
            for row in rows[:3]:
                ratio = row["ratio"]
                text = f"{ratio:.3f}" if isinstance(ratio, float) and ratio != float("inf") else str(ratio)
                print(f"  {slug} · {row['build']}：{row['pair']}（实算比值 {text}）")
    else:
        print("所有优先级链与实算一致")
    if na:
        print(f"伤害口径评价不了的链段（生存项 / 异常角色的常规暴击）：{len(na)} 份")
    print(f"报告：{out}")
    if args.stdout:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
