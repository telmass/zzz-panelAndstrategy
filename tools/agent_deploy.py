"""新代理人一键部署 / 已有代理人修正的编排入口。

阶段：
    identity  解析身份（中文名 → slug / WIKI 条目 id / 属性 / 职业 / 评级 / 面板模式）
    presets   预设层：mapping 补录 → agent-presets → weapon-presets → drive-disc-presets
    scrape    抓 WIKI 产物（.json）
    images    立绘背景（Gachabase）+ 角色框头像（Nanoka）
    editorial 从**同职业**参考页克隆结构、值置占位，输出待确认清单（不猜内容）
    panel     算毕业面板（calc_graduation_panel.py）
    register  登记表 + 生成物（gen_strategy_guides / sync_presets / bundle_worker_data）
    verify    全量闸门
    sync      同步收尾：按「改了什么 → 同步哪里」表更新文档/代码，并复核一致性

用法：
    python tools/agent_deploy.py --name 希希芙
    python tools/agent_deploy.py --slug cissia --stages editorial,panel,register,verify
    python tools/agent_deploy.py --name 希希芙 --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

# 管道输出固定 UTF-8：Windows 上管道默认用系统代码页（本机 GBK），
# 父工具按 UTF-8 读会抛 UnicodeDecodeError 或读出乱码。控制台输出保持
# 系统代码页，否则用户在自己的终端里会看到乱码。
if hasattr(sys.stdout, "reconfigure") and not sys.stdout.isatty():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".github" / "skills"
SHARED = SKILLS / "_shared"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_paths import dataset_path  # noqa: E402

#: 数据集路径由 ``data/manifest.json`` 统一登记，此处只取用。
MAPPING = dataset_path("agent-index")
AGENT_PRESETS = dataset_path("agents")

STAGES = ["identity", "presets", "scrape", "images", "editorial", "panel", "register", "verify", "sync"]

#: 参考页排序：同职业优先，规范样板页（ye-shunguang / roxy / miyabi / banyue / claret / cissia）更优先
REFERENCE_PREFERENCE = (
    "ye-shunguang", "roxy", "miyabi", "banyue", "claret", "cissia", "astra-yao", "ben",
)

#: 阶段 G「同步收尾」对照表：改动类型 → 必须同步的地方
SYNC_TARGETS = [
    ("新增 / 删除代理人", [
        "data/catalog/agent-index.json（data/manifest.json 登记）",
        "strategy/<slug>/data/（两份 JSON）",
        "frontend/src/constants/strategyGuides.ts（tools/gen_strategy_guides.py）",
        "docs/overview/project-overview.md「当前规模」表的代理人数 / 命名映射 / 攻略页数",
        "docs/design/data-schema.md 的数据表",
        "docs/overview/requirements.md F3",
    ]),
    ("面板 / 核心 / 音擎 / 驱动盘预设变了", [
        "data/catalog/agents.json | weapons.json | drive-discs.json（data/manifest.json 登记）",
        "backend/src/zzz_panel/_bundled_data.py（tools/bundle_worker_data.py）",
    ]),
    ("攻略编辑内容变了", [
        "frontend/src/constants/strategyGuides.ts（tools/gen_strategy_guides.py）",
        "毕业面板形状（calc_graduation_panel.py --check-all）",
    ]),
    ("新增 / 替换图片", [
        "必须是 webp（tools/images_to_webp.py）",
        "JSON 的 /images/… 引用与磁盘文件名逐字一致",
    ]),
    ("新增 / 改名脚本", [
        "tools/README.md「脚本一览」",
        "docs/guides/development.md 的脚本段",
        "docs/README.md 的索引（面向使用流程时）",
    ]),
    ("改了攻略 JSON 字段契约", [
        "strategy/README.md（契约表）",
        "docs/design/data-schema.md",
        "frontend/src/types/",
    ]),
    ("改了 skill / 流程 / 规则", [
        ".github/skills/_shared/（共享规程的唯一事实源）",
        "相关 .github/skills/*/SKILL.md",
        "docs/README.md 技能表",
        "strategy/README.md 的新增流程",
    ]),
    ("任何数量类事实变了", [
        "docs/overview/project-overview.md「当前规模」表（唯一事实源）",
    ]),
]


def run(command: list[str], cwd: Path = ROOT, check: bool = True) -> int:
    print("  $ " + " ".join(str(part) for part in command), flush=True)
    # errors="replace"：Windows 上子进程的管道输出是 GBK，按 UTF-8 硬解会抛
    # UnicodeDecodeError，把读取线程打死、输出截断。解码失败不该影响判定。
    proc = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if out:
        print("    " + out.replace("\n", "\n    ")[:2000], flush=True)
    if proc.returncode != 0:
        print("    !! " + (err or out)[:1500], file=sys.stderr, flush=True)
        if check:
            raise SystemExit(proc.returncode)
    return proc.returncode


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(text: str | None) -> str:
    return re.sub(r"[\s·・.\-—_&']", "", text or "").lower()


def resolve_identity(name: str, slug: str | None) -> dict:
    """中文名/英文名/slug → 身份信息。"""
    mapping = load_json(MAPPING)
    entry = None
    if slug:
        entry = next((item for item in mapping if item["slug"] == slug), None)
    if entry is None:
        for item in mapping:
            if name and name in (item.get("cn_short"), item.get("cn_full"), item.get("en")):
                entry = item
                break
    if entry is None:
        for item in mapping:
            if normalize(name) and normalize(name) in (normalize(item.get("cn_short")), normalize(item.get("cn_full"))):
                entry = item
                break
    if entry is None:
        raise SystemExit(f"在 data/catalog/agent-index.json 里找不到代理人：{name or slug}")

    slug = entry["slug"]
    scraped_path = ROOT / "strategy" / slug / "data" / f"{slug}.json"
    presets = load_json(AGENT_PRESETS)
    preset = next((p for p in presets if p.get("id") == f"ep-{entry.get('entryPageId', '')}"), None)
    entry_page_id = None
    if scraped_path.is_file():
        entry_page_id = load_json(scraped_path)["meta"].get("entryPageId")
    if entry_page_id is None:
        preset = preset or next(
            (p for p in presets if p.get("name") in (entry.get("cn_short"), entry.get("cn_full"))), None
        )
        if preset:
            source = preset.get("source", "")
            match = re.search(r"/content/(\d+)/", source)
            entry_page_id = int(match.group(1)) if match else None
    return {
        "slug": slug,
        "name": entry.get("cn_full") or entry.get("cn_short"),
        "entry_page_id": entry_page_id,
        "exists": (ROOT / "strategy" / slug / "data" / f"{slug}.strategy.json").is_file(),
    }


def profession_index() -> dict[str, list[str]]:
    """职业 → 已有攻略页 slug 列表（按 WIKI 条目 id 升序，便于挑同代页面）。"""
    index: dict[str, list[str]] = {}
    for path in sorted((ROOT / "strategy").glob("*/data/*.json")):
        if path.name.endswith(".strategy.json"):
            continue
        try:
            data = load_json(path)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        role = (data.get("profile") or {}).get("roleTag") or ""
        index.setdefault(role, []).append(path.parent.parent.name)
    return index


def pick_reference(profession: str) -> str | None:
    """同职业参考页；同职业没有时用规范样板页。"""
    index = profession_index()
    candidates = index.get(profession, [])
    ordered = [slug for slug in REFERENCE_PREFERENCE if slug in candidates]
    ordered += [slug for slug in candidates if slug not in ordered]
    if ordered:
        return ordered[0]
    for slug in REFERENCE_PREFERENCE:
        if (ROOT / "strategy" / slug / "data" / f"{slug}.strategy.json").is_file():
            return slug
    return None


def skeleton_from(reference_slug: str, identity: dict) -> dict:
    """从参考页克隆**结构**，把具体内容重置为占位。"""
    path = ROOT / "strategy" / reference_slug / "data" / f"{reference_slug}.strategy.json"
    data = deepcopy(load_json(path))
    for key in ("graduationPanel", "graduationPanelAlt", "cinemaPriority", "background", "_meta"):
        data.pop(key, None)

    meta = {
        "agentId": f"ep-{identity['entry_page_id']}" if identity.get("entry_page_id") else "TODO",
        "name": identity["name"],
        "note": "TODO：本文件是该代理人的攻略编辑内容（加点/推荐/队伍/文字攻略），与抓取产物分开维护；graduationPanel 由 calc_graduation_panel.py 实算后写入。",
        "editorialSources": [
            "技能机制：抓取自米游社 WIKI 代理人页的技能与影画文本（strategy/<slug>/data/<slug>.json）",
            "配装口径：仓库计算器选项表（data/rules/calculator-rules.json）、音擎预设（data/catalog/weapons.json）与驱动盘预设（data/catalog/drive-discs.json）",
            "推荐档位与队伍：TODO（需求方确认 + 社区攻略档位作为参考）",
        ],
        "officialGuide": (
            f"https://baike.mihoyo.com/zzz/wiki/content/{identity['entry_page_id']}/detail"
            if identity.get("entry_page_id")
            else "TODO"
        ),
    }
    data["_meta"] = meta

    for item in data.get("skillPriority") or []:
        item["level"] = "TODO"
        item["maxLevel"] = "TODO"
    for tier in data.get("weapons") or []:
        tier["note"] = "TODO"
        for item in tier.get("items") or []:
            item["name"] = "TODO"
            item["stats"] = "TODO"
            item["icon"] = "TODO"
    for build in data.get("driveBuilds") or []:
        build["name"] = "TODO"
        set4 = build.get("set4")
        entries = set4 if isinstance(set4, list) else [set4]
        for entry in entries:
            if isinstance(entry, dict):
                entry["name"] = "TODO"
                entry["label"] = "TODO"
                entry["effect4"] = "TODO"
                entry["icon"] = "TODO"
        set2 = build.get("set2") or {}
        for group in ("main", "alt"):
            items = set2.get(group) or []
            if isinstance(items, dict):
                items = [items]
            for item in items:
                item["name"] = "TODO"
                item["label"] = "TODO"
                item["icon"] = "TODO"
        for stat in build.get("mainStats") or []:
            stat["main"] = "TODO"
            stat["alt"] = "TODO"
        for item in build.get("subPriority") or []:
            item["label"] = "TODO"
    for team in data.get("teams") or []:
        team["name"] = "TODO"
        for member in team.get("members") or []:
            member["agentId"] = "TODO"
            member["name"] = "TODO"
            member["role"] = "TODO"
            member["avatar"] = "TODO"
            member["note"] = "TODO"
            for entry in member.get("set4") or []:
                entry["name"] = "TODO"
                entry["icon"] = "TODO"
    for guide in data.get("textGuide") or []:
        guide["title"] = "TODO"
        guide["lines"] = ["TODO"]
    return data


def checklist(slug: str) -> str:
    text = (SHARED / "editorial-fields.md").read_text(encoding="utf-8")
    rows = [line for line in text.splitlines() if line.startswith("|") and "---" not in line]
    lines = [
        f"  {row.strip()}"
        for row in rows[2:]
        if "来源" not in row and not row.strip().startswith("| 要找的点")
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="", help="中文名/英文名")
    parser.add_argument("--slug", default="", help="规范 slug（已知时更稳）")
    parser.add_argument("--stages", default="all", help=f"逗号分隔的阶段，可选 {','.join(STAGES)}（默认 all）")
    parser.add_argument("--dry-run", action="store_true", help="只打印将要做什么")
    parser.add_argument("--skip-refresh", action="store_true", help="预设阶段不跑全量刷新脚本")
    args = parser.parse_args()

    stages = STAGES if args.stages == "all" else [s.strip() for s in args.stages.split(",") if s.strip()]
    for stage in stages:
        if stage not in STAGES:
            raise SystemExit(f"未知阶段：{stage}（可选 {','.join(STAGES)}）")

    identity = resolve_identity(args.name, args.slug)
    slug = identity["slug"]
    print(f"== 代理人：{identity['name']}（slug={slug}，WIKI 条目 {identity['entry_page_id']}，"
          f"{'已存在' if identity['exists'] else '未部署'}）")

    if "identity" in stages:
        print("  身份解析完成")

    if "presets" in stages:
        print("== 阶段 B：预设层")
        if not args.skip_refresh and not args.dry_run:
            run(["uv", "run", "python", str(SKILLS / "read-zzz-agent-stats/scripts/refresh_agent_presets.py")])
            run(["uv", "run", "python", str(SKILLS / "read-zzz-engine-stats/scripts/refresh_weapon_presets.py")])
            run(["uv", "run", "python", str(SKILLS / "read-zzz-drive-disc/scripts/refresh_disc_presets.py")])
        else:
            print("  （跳过全量刷新；预设刷新是全量扫描，与新增单个代理人不匹配）")

    if "scrape" in stages and identity.get("entry_page_id"):
        print("== 阶段 C：抓取")
        target = ROOT / "strategy" / slug / "data" / f"{slug}.json"
        if args.dry_run:
            print(f"  将抓取 {target}")
        else:
            run([
                "uv", "run", "python", str(SKILLS / "agent-strategy/scripts/scrape_agent_guide.py"),
                "--entry-page-id", str(identity["entry_page_id"]),
                "--slug", slug,
                "--output", str(target),
            ])

    if "images" in stages:
        print("== 阶段 C：图片")
        if args.dry_run:
            print("  将抓取 background.webp（Gachabase）与 film.webp（Nanoka）")
        else:
            run(["uv", "run", "python", str(ROOT / "tools/fetch_agent_backgrounds.py")])
            run(["uv", "run", "python", str(ROOT / "tools/fetch_agent_films.py")])

    if "editorial" in stages:
        print("== 阶段 D：编辑内容骨架")
        profession = ""
        scraped_path = ROOT / "strategy" / slug / "data" / f"{slug}.json"
        if scraped_path.is_file():
            profession = (load_json(scraped_path).get("profile") or {}).get("roleTag") or ""
        reference = pick_reference(profession)
        print(f"  同职业参考页：{reference or '（无可用参考页）'}")
        target = ROOT / "strategy" / slug / "data" / f"{slug}.strategy.json"
        if reference and (args.dry_run or not target.is_file()):
            skeleton = skeleton_from(reference, identity)
            if args.dry_run:
                print("  将写入骨架（值全部置为 TODO）：", target)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(skeleton, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="")
                print(f"  已写入骨架：{target.relative_to(ROOT)}")
        elif target.is_file():
            print("  攻略文件已存在，保留原内容（修正模式）")
        print("\n  待确认清单（逐项与用户确认后写入，脚本不猜内容）：")
        print(checklist(slug))

    if "panel" in stages:
        print("== 阶段 E：毕业面板")
        target = ROOT / "strategy" / slug / "data" / f"{slug}.strategy.json"
        if args.dry_run:
            print("  将用 calc_graduation_panel.py 实算 graduationPanel / graduationPanelAlt")
        else:
            run([
                "uv", "run", "python", str(SKILLS / "agent-strategy/scripts/calc_graduation_panel.py"),
                "--strategy", str(target),
            ], check=False)

    if "register" in stages:
        print("== 阶段 E：登记表与生成物")
        if args.dry_run:
            print("  将跑 gen_strategy_guides.py / sync_manifest / bundle_worker_data.py")
        else:
            run(["uv", "run", "python", str(ROOT / "tools/gen_strategy_guides.py")])
            run(["uv", "run", "python", str(ROOT / "tools/sync_manifest.py")])
            run(["uv", "run", "python", str(ROOT / "tools/bundle_worker_data.py")])

    if "verify" in stages:
        print("== 阶段 F：闸门")
        gates = [
            ("uv", "run", "python", str(ROOT / "tools/normalize_strategy.py"), "--check"),
            ("uv", "run", "python", str(ROOT / "tools/seed_main_stat_notes.py"), "--check"),
            ("uv", "run", "python", str(ROOT / "tools/gen_strategy_guides.py"), "--check"),
            ("uv", "run", "python", str(SKILLS / "agent-strategy/scripts/calc_graduation_panel.py"), "--check-all"),
            ("uv", "run", "python", str(ROOT / "tools/sync_manifest.py"), "--check"),
            ("uv", "run", "python", str(ROOT / "tools/bundle_worker_data.py"), "--check"),
            ("uv", "run", "python", str(ROOT / "tools/agent_audit.py")),
        ]
        if args.dry_run:
            for gate in gates:
                print("  $ " + " ".join(gate[2:]))
        else:
            for gate in gates:
                run(list(gate), check=False)

    if "sync" in stages:
        print("== 阶段 G：同步收尾")
        print("  按「改了什么 → 必须同步哪里」逐条核对（完整表见 .github/skills/_shared/deploy-checklist.md）：")
        for change, targets in SYNC_TARGETS:
            print(f"    · {change}")
            for target in targets:
                print(f"        - {target}")
        if args.dry_run:
            print("  将跑 gen_strategy_guides.py / sync_manifest.py / bundle_worker_data.py / check_docs.py")
        else:
            run(["uv", "run", "python", str(ROOT / "tools/gen_strategy_guides.py")])
            run(["uv", "run", "python", str(ROOT / "tools/sync_manifest.py")])
            run(["uv", "run", "python", str(ROOT / "tools/bundle_worker_data.py")])
            run(["uv", "run", "python", str(ROOT / "tools/check_docs.py")], check=False)
            run(["uv", "run", "python", str(ROOT / "tools/agent_audit.py")], check=False)

    print("\n== 完成。改了哪些文件请用 git status 查看；数据来源与待确认项见上面的清单。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
