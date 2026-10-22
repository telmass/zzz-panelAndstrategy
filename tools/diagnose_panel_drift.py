"""诊断毕业面板的「文案 ↔ 数值」漂移。

背景
----
``tools/migrate_build_spec.py`` 从攻略 JSON 里手写的配装文案反推
``buildSpec``，并要求**重算结果必须等于页面里存的数值**才算通过。
61 份里有 17 份对不上——说明那些已发布页面**和它自己的配装文案不一致**：
要么文案写错了，要么数值算错了。

本脚本对每一份做**单变量穷举**：在反推出的 spec 上只改一个变量
（核心加成 / 套装效果 / 某条副词条的条数），看哪一个能让重算结果
与页面数值完全相等。找到的候选就是**根因**。

用法::

    python tools/diagnose_panel_drift.py            # 全部
    python tools/diagnose_panel_drift.py roxy       # 只看某一份
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


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CALC = _load("calc_graduation_panel", SKILL_SCRIPT)
MIG = _load("migrate_build_spec", ROOT / "tools" / "migrate_build_spec.py")


def _rows(spec: dict) -> dict[str, float]:
    args = CALC.args_from_build_spec(spec)
    request, _ = CALC.build_request(args)
    computed = CALC.compute_panel(args, request, {"agent": "", "weapon": ""})
    mapping = MIG._label_to_key()
    return {
        mapping.get(row["label"], row["label"]): row["value"]
        for row in computed["totals"]
    }


def _stored(panel: dict) -> dict[str, float]:
    mapping = MIG._label_to_key()
    return {
        mapping.get(row["label"], row["label"]): row["value"]
        for row in panel.get("totals") or []
    }


def _variants(spec: dict, rules: dict, discs: dict) -> list[tuple[str, dict]]:
    """单变量变体：核心 / 套装效果 / 副词条条数。"""
    out: list[tuple[str, dict]] = []

    # 核心：换掉两个核心槽里的任意一个
    core_options = [option["id"] for option in rules["coreOptions"]]
    for index in range(len(spec["core"])):
        for ident in core_options:
            variant = json.loads(json.dumps(spec))
            if variant["core"][index] == ident:
                continue
            variant["core"][index] = ident
            out.append((f"core[{index}] {spec['core'][index]} -> {ident}", variant))

    # 套装：换某组的二件套效果
    effect_options = [option["id"] for option in rules["setOptions"]]
    for group_index, group in enumerate(spec["setGroups"]):
        for ident in effect_options:
            variant = json.loads(json.dumps(spec))
            if variant["setGroups"][group_index].get("effectId") == ident:
                continue
            variant["setGroups"][group_index]["effectId"] = ident
            out.append(
                (f"set[{group_index}].effect {group.get('effectId')} -> {ident}", variant)
            )

    # 副词条：某条的条数 ±1..3
    for ident in list(spec["subStats"]):
        for delta in (-3, -2, -1, 1, 2, 3):
            variant = json.loads(json.dumps(spec))
            count = variant["subStats"][ident] + delta
            if count < 0:
                continue
            variant["subStats"][ident] = count
            out.append((f"sub {ident} {spec['subStats'][ident]} -> {count}", variant))

    return out


def diagnose(path: Path, catalogs: dict, rules: dict) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    slug = path.parent.parent.name
    for key in ("graduationPanel", "graduationPanelAlt"):
        panel = data.get(key)
        if not panel:
            continue
        stored = _stored(panel)
        spec = MIG._spec_from_build(
            panel.get("build") or {}, catalogs, rules, panel.get("totals") or []
        )
        if spec is None:
            print(f"{slug}/{key}: 无法从文案反推 buildSpec")
            continue
        base = _rows(spec)
        if base == stored:
            print(f"{slug}/{key}: 一致")
            continue
        diff = {
            label: (base.get(label), stored.get(label))
            for label in sorted(set(base) | set(stored))
            if base.get(label) != stored.get(label)
        }
        print(f"\n{slug}/{key}  差异：{diff}")
        print(f"  反推出的 spec：{json.dumps(spec, ensure_ascii=False)}")
        hits = []
        for label, variant in _variants(spec, rules, catalogs["discs"]):
            try:
                if _rows(variant) == stored:
                    hits.append(label)
            except Exception:  # noqa: BLE001 - 变体可能构造不出合法请求
                continue
        if hits:
            print(f"  ✅ 单变量可对齐的候选（{len(hits)} 个）：")
            for hit in hits[:12]:
                print(f"      · {hit}")
        else:
            print("  ❌ 单变量改不出来——需要多项一起改，或数值来源不在文案里")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("slugs", nargs="*", help="只看这些 slug（默认全部）")
    args = parser.parse_args()

    catalogs = {
        "agents": MIG._catalog_by_name(MIG.CATALOG / "agents.json"),
        "weapons": MIG._catalog_by_name(MIG.CATALOG / "weapons.json"),
        "discs": MIG._catalog_by_id(MIG.CATALOG / "drive-discs.json"),
    }
    rules = json.loads(
        (ROOT / "data" / "rules" / "calculator-rules.json").read_text(encoding="utf-8")
    )

    for path in sorted((ROOT / "strategy").glob("*/data/*.strategy.json")):
        slug = path.parent.parent.name
        if args.slugs and slug not in args.slugs:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        panels = data.get("graduationPanel") or {}
        stored = _stored(panels)
        spec = MIG._spec_from_build(
            panels.get("build") or {}, catalogs, rules, panels.get("totals") or []
        )
        if spec is None:
            continue
        if _rows(spec) == stored:
            continue
        diagnose(path, catalogs, rules)
    return 0


if __name__ == "__main__":
    sys.exit(main())
