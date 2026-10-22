"""生成毕业面板的**推导链**（derivation）——让面板从「结论」变成「可复核的推导」。

面板（``graduationPanel``）现在给的是结论：几个数字 + 一句说明。
读者无法判断「这个 30 条的分配是不是合理」「为什么 5 号位选穿透率」。

本脚本用已经建好的那套工具（伤害目标函数 / 边际收益 / 主词条取舍 / 两档门槛）
把推导链算出来，写进每份攻略页的 ``graduationPanel.derivation``：

```json
"derivation": [
  {"step": "口径", "reason": "…", "evidence": "docs/design/calculation-rules.md §0"},
  {"step": "目标行", "reason": "…", "evidence": "…"},
  {"step": "主词条", "reason": "…", "evidence": "…"},
  {"step": "副词条", "reason": "…", "evidence": "…"},
  {"step": "档位门槛", "reason": "…", "evidence": "…"}
]
```

``evidence`` 一律指向**可重跑的命令或文档**，满足「数字必须可核对」这条纪律。

用法::

    python tools/derive_panel.py              # 全部攻略页
    python tools/derive_panel.py roxy caesar  # 只算这几份
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_SCRIPT = (
    ROOT / ".github" / "skills" / "agent-strategy" / "scripts" / "calc_graduation_panel.py"
)
STRATEGY_DIR = ROOT / "strategy"
CATALOG = ROOT / "data" / "catalog"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CALC = _load("calc_graduation_panel", SKILL_SCRIPT)


def _services():
    backend_src = ROOT / "backend" / "src"
    if str(backend_src) not in sys.path:
        sys.path.insert(0, str(backend_src))
    from zzz_panel.services import benefit_service, compare_service, damage_service

    return benefit_service, compare_service, damage_service


benefit, compare, damage = _services()

from zzz_panel.core.panel_rows import SUB_STAT_MINOR_LABELS  # noqa: E402  （路径已就绪）


def _slot_labels(options, ident: str) -> str:
    """某个主词条选项 id -> 展示名（兼容选项对象与 dict 两种形状）。"""
    for option in options:
        ident_value = getattr(option, "id", None) or (option.get("optionId") if isinstance(option, dict) else None)
        if ident_value == ident:
            return getattr(option, "label", None) or (option.get("label") if isinstance(option, dict) else ident)
    return ident


def build_derivation(spec: dict, panel: dict, request, slug: str, path: str) -> list[dict]:
    """算出一份推导链。"""
    totals = damage.calculate(request).totals
    steps: list[dict] = []

    steps.append(
        {
            "step": "口径",
            "reason": (
                "面板 = **0 影画 + 专武**的局外面板；不含影画、专武局内加成、"
                "4 件套与队伍增益。敌人在伤害对比中取标准目标（60 级以上首领）。"
            ),
            "evidence": "docs/design/calculation-rules.md §0 · docs/design/damage-formulas.md §7",
        }
    )

    rows = " / ".join(
        "{} {}".format(row["label"], row["value"]) for row in (panel.get("totals") or [])
    )
    total_damage = damage.score_build(request, path=path).total
    steps.append(
        {
            "step": "目标行",
            "reason": "{}；对标准目标的单位倍率伤害 {:.0f}".format(rows, total_damage),
            "evidence": "uv run python tools/build_compare.py {}".format(slug),
        }
    )

    # 主词条：每个槽位选了哪个、在这套配装里排第几
    main_bits = []
    for slot, label in (("disc4", "4 号位"), ("disc5", "5 号位"), ("disc6", "6 号位")):
        chosen = spec.get("discMain", {}).get(slot)
        if not chosen:
            continue
        ranking = compare.compare_main_stats(request, slot=slot, path=path)
        labels = {item["optionId"]: item["label"] for item in ranking}
        rank = next((i + 1 for i, item in enumerate(ranking) if item["optionId"] == chosen), None)
        lead = ""
        if rank == 1 and len(ranking) > 1 and ranking[0]["damage"]:
            lead = "（该槽位伤害第 1，领先第 2 名 {:.1%}）".format(
                ranking[0]["damage"] / ranking[1]["damage"] - 1
            )
        main_bits.append(
            "{} {}{}".format(label, labels.get(chosen, chosen), lead)
        )
    steps.append(
        {
            "step": "主词条",
            "reason": "；".join(main_bits),
            "evidence": "uv run python tools/build_compare.py {}".format(slug),
        }
    )

    # 副词条：条数与优先级（按边际收益排序）
    values = benefit.one_roll_values(request, path=path)
    order = sorted(values, key=lambda key: values.get(key, 0.0), reverse=True)
    labels = benefit.SUBSTAT_BY_LABEL
    by_id = {value: key for key, value in labels.items()}
    chain_bits = []
    minor_total = 0
    minor_labels = set(SUB_STAT_MINOR_LABELS)
    for ident in order:
        count = request.sub_stats.get(ident, 0)
        if count <= 0:
            continue
        label = by_id.get(ident, ident)
        if label in minor_labels:
            # 小词条与面板同一口径：**不逐条列**，只报总数（页面上也是 47+7）。
            minor_total += count
            continue
        chain_bits.append(
            "{} ×{}（每条 +{:.0f}）".format(label, count, values.get(ident, 0.0))
        )
    sub_reason = " > ".join(chain_bits)
    if minor_total:
        sub_reason += "（共 {} 条，含 {} 条小词条）".format(
            sum(request.sub_stats.values()), minor_total
        )
    else:
        sub_reason += "（共 {} 条）".format(sum(request.sub_stats.values()))
    steps.append(
        {
            "step": "副词条",
            "reason": "{}（顺序按单条伤害增量排）".format(sub_reason),
            "evidence": "uv run python tools/substat_benefit.py {}".format(slug),
        }
    )

    # 档位门槛：从满配往下拆
    curve = compare.tier_curve(request, path=path, steps=6)
    near = curve[-1] if len(curve) > 1 else None
    tier_text = "满配 {} 条 = 100% 伤害".format(curve[0]["count"] if curve else 0)
    if near:
        tier_text += "；减到 {} 条 = {:.0%} 伤害".format(near["count"], near["ratio"])
    steps.append(
        {
            "step": "档位门槛",
            "reason": tier_text,
            "evidence": "uv run python tools/build_compare.py {}".format(slug),
        }
    )
    return steps


def _write(path: Path, data: dict) -> None:
    """写文件（Windows 上偶发被占用，重试几次）。"""
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    last: OSError | None = None
    for attempt in range(4):
        try:
            path.write_text(payload, encoding="utf-8", newline="\n")
            return
        except OSError as error:
            last = error
            time.sleep(0.4 * (attempt + 1))
    raise last if last else OSError("write failed")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("slugs", nargs="*", help="只算这些 slug（默认全部）")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不写文件")
    args = parser.parse_args()

    agents = json.loads((CATALOG / "agents.json").read_text(encoding="utf-8"))
    role_by_id = {agent.get("id"): agent.get("roleTag") or "" for agent in agents}

    written = skipped = 0
    for path in sorted(STRATEGY_DIR.glob("*/data/*.strategy.json")):
        slug = path.parent.parent.name
        if args.slugs and slug not in args.slugs:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        panel = data.get("graduationPanel") or {}
        spec = panel.get("buildSpec")
        if not spec:
            skipped += 1
            continue
        request, _ = CALC.build_request(CALC.args_from_build_spec(spec))
        path_kind = benefit.path_for_role(role_by_id.get(spec.get("agentId"), ""))
        derivation = build_derivation(spec, panel, request, slug, path_kind)
        if args.dry_run:
            print(f"--- {slug} ---")
            for step in derivation:
                print(f"  {step['step']}：{step['reason']}")
            continue
        panel["derivation"] = derivation
        data["graduationPanel"] = panel
        try:
            _write(path, data)
        except OSError as error:
            # Windows 上偶发：文件被索引器 / 编辑器占用（errno 22）。
            print("  ! 写入失败 {}：{}".format(path.name, error), file=sys.stderr)
            skipped += 1
            continue
        written += 1
    if not args.dry_run:
        print(f"已写入推导链：{written} 份，跳过 {skipped} 份（没有 buildSpec）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
