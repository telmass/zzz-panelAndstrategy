"""代理人攻略页体检：一致性、引用完整性、技能文本完整性、占位残留、生成物新鲜度。

用法：
    python tools/agent_audit.py                # 全量体检
    python tools/agent_audit.py --slug miyabi  # 只查一位
    python tools/agent_audit.py --json         # 机器可读输出
    python tools/agent_audit.py --strict       # WARN 也算失败

退出码：存在 ERROR 时为 1（--strict 时 WARN 也算）。
本脚本**只报告不改数据**；`--fix-safe` 仅做安全项（补 `mainStats[].note: ""`、重生成登记表）。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

# 管道输出固定 UTF-8：Windows 上管道默认用系统代码页（本机 GBK），
# 父工具按 UTF-8 读会抛 UnicodeDecodeError 或读出乱码。控制台输出保持
# 系统代码页，否则用户在自己的终端里会看到乱码。
if hasattr(sys.stdout, "reconfigure") and not sys.stdout.isatty():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STRATEGY = ROOT / "strategy"
IMAGES = ROOT / "frontend" / "public" / "images"
REGISTRY = ROOT / "frontend" / "src" / "constants" / "strategyGuides.ts"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_paths import dataset_path  # noqa: E402

#: 数据集路径由 ``data/manifest.json`` 统一登记，此处只取用。
MAPPING = dataset_path("agent-index")
AGENT_PRESETS = dataset_path("agents")
DISC_PRESETS = dataset_path("drive-discs")

ATTRIBUTE_SLUGS = {
    "lumiflux", "auric-ink", "honed-edge", "frost", "wind", "fire", "ice", "ether", "physical", "electric",
}
ROLE_SLUGS = {"attack", "stun", "anomaly", "support", "defense", "rupture", "armorer"}
GRADE_SLUGS = {"s", "a"}

IMAGE_REF_RE = re.compile(r"/images/[^\s\"'`()\[\]<>,;]+")
PLACEHOLDER_RE = re.compile(r"TODO|待确认|待补|FIXME|xxx|XXX", re.IGNORECASE)
EXTRA_ABILITY_RE = re.compile(r"额外(?:能力|被动)\s*[:：]")
#: 优先级链的连接符：> 优先、= 同级、≈ 近似同级
CHAIN_SEPARATORS = (">", "=", "≈")

ERROR, WARN, INFO = "ERROR", "WARN", "INFO"


@dataclass
class Issue:
    level: str
    slug: str
    file: str
    message: str


@dataclass
class Report:
    issues: list[Issue] = field(default_factory=list)

    def add(self, level: str, slug: str, file: str, message: str) -> None:
        self.issues.append(Issue(level, slug, file, message))

    def by_level(self, level: str) -> list[Issue]:
        return [i for i in self.issues if i.level == level]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def image_exists(url: str) -> bool:
    if not url.startswith("/images/"):
        return True
    return (ROOT / "frontend" / "public" / url.lstrip("/")).is_file()


def check_slug_consistency(report: Report, mapping: dict[str, str], registry: set[str]) -> None:
    for slug in sorted(mapping):
        folder = STRATEGY / slug
        if not folder.is_dir():
            report.add(INFO, slug, "data/catalog/agent-index.json", "mapping 里有该代理人，但没有攻略目录（未公开/未部署）")
            continue
        data_dir = folder / "data"
        for name in (f"{slug}.json", f"{slug}.strategy.json"):
            if not (data_dir / name).is_file():
                report.add(ERROR, slug, f"strategy/{slug}/data/{name}", "数据文件名与 mapping 的 slug 不一致或缺失")
        if slug not in registry:
            report.add(ERROR, slug, "frontend/src/constants/strategyGuides.ts", "登记表里没有该 slug（跑 tools/gen_strategy_guides.py）")
        image_dir = IMAGES / "strategy" / slug
        if not image_dir.is_dir():
            report.add(ERROR, slug, f"frontend/public/images/strategy/{slug}/", "缺少该代理人的图片目录")


def check_scraped(report: Report, slug: str, scraped: dict, preset: dict | None) -> None:
    profile = scraped.get("profile") or {}
    if not preset:
        report.add(WARN, slug, "data/catalog/agents.json", "该代理人没有计算器预设")
    else:
        for field_name in ("attribute", "roleTag", "grade"):
            got, want = profile.get(field_name), preset.get(field_name)
            if want and got and got != want:
                report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.json", f"profile.{field_name}={got!r} 与预设 {want!r} 不一致")
    icons = profile.get("icons") or {}
    attribute_icon = str(icons.get("attribute") or "")
    if attribute_icon:
        slug_name = attribute_icon.rsplit("/", 1)[-1].removesuffix(".webp")
        if slug_name not in ATTRIBUTE_SLUGS:
            report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.json", f"属性图标 slug 非法：{slug_name!r}")
    profession_icon = str(icons.get("profession") or "")
    if profession_icon:
        slug_name = profession_icon.rsplit("/", 1)[-1].removesuffix(".webp")
        if slug_name not in ROLE_SLUGS:
            report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.json", f"职业图标 slug 非法：{slug_name!r}")
    grade_icon = str(icons.get("grade") or "")
    if grade_icon:
        slug_name = grade_icon.rsplit("/", 1)[-1].removesuffix(".webp")
        if slug_name not in GRADE_SLUGS:
            report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.json", f"等级图标 slug 非法：{slug_name!r}")
    for key, url in icons.items():
        if url and not image_exists(url):
            report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.json", f"图标 {key} 指向不存在的文件：{url}")


def check_image_refs(report: Report, slug: str, file_label: str, data: dict) -> None:
    text = json.dumps(data, ensure_ascii=False)
    for url in sorted(set(IMAGE_REF_RE.findall(text))):
        if not image_exists(url):
            report.add(ERROR, slug, file_label, f"图片引用不存在：{url}")


def check_images_present(report: Report, slug: str) -> None:
    folder = IMAGES / "strategy" / slug
    for name, required in (("tachie.webp", True), ("background.webp", True), ("film.webp", True),
                           ("cinema-2.webp", False), ("cinema-3.webp", False)):
        path = folder / name
        if path.is_file():
            continue
        if required:
            report.add(WARN, slug, f"frontend/public/images/strategy/{slug}/{name}", "缺少该图片")
        else:
            report.add(INFO, slug, f"frontend/public/images/strategy/{slug}/{name}", "缺少该图片（WIKI 未提供时正常）")


def check_panels(report: Report, slug: str, data: dict) -> None:
    for key in ("graduationPanel", "graduationPanelAlt"):
        panel = data.get(key)
        if not panel:
            if key == "graduationPanel":
                report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", "缺少 graduationPanel")
            continue
        for field_name in ("build", "totals", "note", "computedAt"):
            if not panel.get(field_name):
                report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"{key}.{field_name} 缺失")
        totals = panel.get("totals") or []
        for item in totals:
            if not item.get("label") or item.get("value") is None:
                report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"{key}.totals 里有缺 label/value 的行")


def check_drive_builds(report: Report, slug: str, data: dict, disc_names: set[str]) -> None:
    builds = data.get("driveBuilds") or []
    if not builds:
        report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", "缺少 driveBuilds")
        return
    seen_sets: list[str] = []
    for index, build in enumerate(builds):
        label = f"driveBuilds[{index}]"
        # 2 件套**组**：并列，都要装。2+2+2 就是三组。
        # 组内的 main / alt 是**候选**（二选一），可以各是「多套同效果的候选」数组。
        set2_groups = [build.get(key) for key in ("set2", "set2b", "set2c")]
        present_groups = [group for group in set2_groups if group]
        if len(present_groups) > 3:
            report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json",
                       f"{label} 有 {len(present_groups)} 组 2 件套，6 个槽位最多三组")

        set4 = build.get("set4")
        if isinstance(set4, list):
            if len(set4) > 1:
                report.add(WARN, slug, f"strategy/{slug}/data/{slug}.strategy.json",
                           f"{label} 把 {len(set4)} 个 4 件套写进同一方案（契约要求拆成独立方案分页；"
                           "现有数据用 scene 标注场景，后端测试也允许该写法）")
            else:
                report.add(WARN, slug, f"strategy/{slug}/data/{slug}.strategy.json",
                           f"{label}.set4 只有一个 4 件套时应写成对象而非数组")
            set4_entries = set4
        elif isinstance(set4, dict):
            set4_entries = [set4]
        elif set4 is None and present_groups:
            # 2+2+2 没有 4 件套组——合法（4 件套组必然带来自己的 2 件套效果，
            # 而 4+2+2 装不下：8 片 > 6 槽）。
            set4_entries = []
        else:
            report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"{label}.set4 缺失")
            set4_entries = []
        for entry in set4_entries:
            name = entry.get("name") or ""
            if name in seen_sets:
                report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"4 件套「{name}」出现在多个方案里")
            seen_sets.append(name)
            if name and disc_names and name not in disc_names:
                report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"4 件套「{name}」不在驱动盘预设里")
        for group_index, set2 in enumerate(present_groups):
            for group in ("main", "alt"):
                entries = set2.get(group) or []
                if isinstance(entries, dict):
                    entries = [entries]
                for entry in entries:
                    name = entry.get("name") or ""
                    if name and disc_names and name not in disc_names:
                        report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"2 件套「{name}」不在驱动盘预设里")
        for stat in build.get("mainStats") or []:
            if not stat.get("alt"):
                report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json",
                           f"{label}.mainStats「{stat.get('slot')}」没有备选（没有时写「无」）")
        priority = build.get("subPriority") or []
        for position, item in enumerate(priority):
            nxt = item.get("next")
            if position < len(priority) - 1 and nxt not in CHAIN_SEPARATORS:
                report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"{label}.subPriority 链在「{item.get('label')}」处断开")
            if position == len(priority) - 1 and nxt:
                report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"{label}.subPriority 链尾的 next 应为空")
        if priority and not priority[-1].get("label"):
            report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"{label}.subPriority 最后一项缺 label")


def check_teams(report: Report, slug: str, data: dict, preset_ids: set[str], disc_names: set[str]) -> None:
    for index, team in enumerate(data.get("teams") or []):
        if not team.get("name"):
            report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"teams[{index}] 缺 name")
        for member in team.get("members") or []:
            agent_id = member.get("agentId") or ""
            if agent_id and agent_id not in preset_ids:
                report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json",
                           f"teams[{index}] 成员 {member.get('name')}（{agent_id}）不在预设里")
            avatar = member.get("avatar") or ""
            if avatar and not image_exists(avatar):
                report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"teams[{index}] 头像不存在：{avatar}")
            for entry in member.get("set4") or []:
                name = entry.get("name") or ""
                if name and disc_names and name not in disc_names:
                    report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"teams[{index}] 套装「{name}」不在驱动盘预设里")


def check_cinema_priority(report: Report, slug: str, data: dict) -> None:
    cinema = data.get("cinemaPriority")
    if not cinema:
        return
    image = cinema.get("image") or ""
    if not image:
        report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", "cinemaPriority.image 缺失")
    elif not image_exists(image):
        report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"cinemaPriority.image 不存在：{image}")
    levels = cinema.get("keyLevels") or []
    if not levels:
        report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", "cinemaPriority.keyLevels 为空")
    for level in levels:
        if level not in range(1, 7):
            report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"cinemaPriority.keyLevels 含非法影画编号：{level}")
    if not cinema.get("note"):
        report.add(WARN, slug, f"strategy/{slug}/data/{slug}.strategy.json", "cinemaPriority.note 为空")


def check_skill_priority(report: Report, slug: str, data: dict) -> None:
    priority = data.get("skillPriority") or []
    if not priority:
        report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", "缺少 skillPriority")
        return
    for position, item in enumerate(priority):
        nxt = item.get("next")
        if position < len(priority) - 1 and nxt not in CHAIN_SEPARATORS:
            report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"skillPriority 链在「{item.get('label')}」处断开")
        if position == len(priority) - 1 and nxt:
            report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", "skillPriority 链尾的 next 应为空")
        icon = item.get("icon") or ""
        if icon and not image_exists(icon):
            report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"skillPriority 图标不存在：{icon}")
        if not item.get("label"):
            report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", "skillPriority 里有缺 label 的项")


def check_text_guide(report: Report, slug: str, data: dict) -> None:
    guides = data.get("textGuide") or []
    if not guides:
        report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", "缺少 textGuide")
        return
    for index, guide in enumerate(guides):
        if not guide.get("title"):
            report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"textGuide[{index}] 缺 title")
        if not guide.get("lines"):
            report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"textGuide[{index}] 缺 lines")


def check_skill_text(report: Report, slug: str, scraped: dict, data: dict) -> None:
    """技能文本完整性：额外能力必须在、初始数据标记必须不在。"""
    skills = {s.get("key"): s for s in scraped.get("skills") or []}
    core = skills.get("core") or {"moves": []}
    moves = core.get("moves") or []
    if not any(EXTRA_ABILITY_RE.match(m.get("title") or "") for m in moves):
        report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.json", "核心技缺少「额外能力 / 额外被动」条目")
    for skill in scraped.get("skills") or []:
        for move in skill.get("moves") or []:
            if "此处数据为初始数据" in (move.get("text") or ""):
                report.add(WARN, slug, f"strategy/{slug}/data/{slug}.json",
                           f"{skill.get('name')}「{move.get('title')}」仍标注「初始数据」（WIKI 未提供该招式的满级值）")
    # 文字攻略提到的「额外能力/额外被动」必须能在抓取产物里找到同名条目
    known = {m.get("title") or "" for m in moves}
    guide_text = json.dumps(data.get("textGuide") or [], ensure_ascii=False)
    mentioned = set(re.findall(r"额外(?:能力|被动)\s*[:：]\s*([^\]，。；、\n]{1,20})", guide_text))
    for name in mentioned:
        if not any(title.startswith(f"额外能力：{name}") or title.startswith(f"额外被动：{name}") for title in known):
            report.add(ERROR, slug, f"strategy/{slug}/data/{slug}.strategy.json",
                       f"文字攻略提到「{name}」，但抓取产物的核心技里没有同名条目（机制归属可能写错）")


def check_placeholders(report: Report, slug: str, data: dict) -> None:
    text = json.dumps(data, ensure_ascii=False)
    for match in set(PLACEHOLDER_RE.findall(text)):
        report.add(WARN, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"残留占位标记：{match!r}")
    for build in data.get("driveBuilds") or []:
        if not build.get("mainStats"):
            report.add(WARN, slug, f"strategy/{slug}/data/{slug}.strategy.json", "driveBuilds 缺 mainStats")
    for team in data.get("teams") or []:
        for member in team.get("members") or []:
            if not member.get("note"):
                report.add(WARN, slug, f"strategy/{slug}/data/{slug}.strategy.json", f"队伍「{team.get('name')}」的 {member.get('name')} 没有 note")


def _backend_python() -> str:
    """跑需要后端依赖的脚本时用的解释器。

    系统的 ``python`` 里没有 pydantic；用它跑 ``calc_graduation_panel.py``
    会 ModuleNotFoundError，看起来像「实算不一致」，实则根本没跑起来。
    """
    for candidate in (
        ROOT / ".venv" / "Scripts" / "python.exe",
        ROOT / ".venv" / "bin" / "python",
        ROOT / "backend" / ".venv" / "Scripts" / "python.exe",
        ROOT / "backend" / ".venv" / "bin" / "python",
    ):
        if candidate.is_file():
            return str(candidate)
    return "python"


def check_generated_freshness(report: Report) -> None:
    commands = [
        ("python tools/gen_strategy_guides.py --check", "登记表"),
        ("python tools/sync_manifest.py --check", "数据集登记表"),
        ("python tools/bundle_worker_data.py --check", "Worker 产物"),
        # 参考实例**实算**比对：--check-all 只验形状，实算才验数值。
        # 没有这条，脚本与预设数据脱节（比如预设改形状后脚本读错字段）会一直
        # 静默到有人手动跑才炸。
        #
        # 这条要带后端依赖（pydantic），必须用装了依赖的解释器——用系统的
        # `python` 会 ModuleNotFoundError，看起来像「实算不一致」，实则是
        # 根本没跑起来。
        (
            f"{_backend_python()} .github/skills/agent-strategy/scripts/"
            "calc_graduation_panel.py --check",
            "毕业面板实算",
        ),
    ]
    for command, label in commands:
        try:
            # errors="replace"：Windows 上子进程的管道输出是 GBK，按 UTF-8 硬解会抛
            # UnicodeDecodeError，把读取线程打死、输出截断。解码失败不该影响判定。
            proc = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=True,
            )
        except OSError:
            continue
        if proc.returncode != 0:
            report.add(ERROR, "-", label, f"{label}已过期（{command} 退出码 {proc.returncode}）")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", default="", help="只查一位代理人")
    parser.add_argument("--all", action="store_true", help="查全部代理人（默认行为）")
    parser.add_argument("--json", action="store_true", help="机器可读输出")
    parser.add_argument("--strict", action="store_true", help="WARN 也算失败")
    args = parser.parse_args()

    mapping_items = load_json(MAPPING)
    mapping = {item["slug"]: item.get("cn_full") or item.get("cn_short") or "" for item in mapping_items}
    presets_raw = load_json(AGENT_PRESETS)
    preset_items = presets_raw if isinstance(presets_raw, list) else list(presets_raw.get("agents", {}).values())
    # 预设 id 形如 ep-<WIKI 条目 id>，与抓取产物的 meta.entryPageId 对应
    presets_by_entry = {
        int(item["id"].replace("ep-", "")): item
        for item in preset_items
        if str(item.get("id", "")).startswith("ep-")
    }
    preset_ids = {item["id"] for item in preset_items if item.get("id")}
    disc_raw = load_json(DISC_PRESETS)
    disc_items = disc_raw if isinstance(disc_raw, list) else list(disc_raw.get("discs", {}).values())
    disc_names = {item.get("name") for item in disc_items if item.get("name")}

    registry_text = REGISTRY.read_text(encoding="utf-8") if REGISTRY.is_file() else ""
    registry = set(re.findall(r"slug:\s*'([^']+)'", registry_text))

    report = Report()
    check_slug_consistency(report, mapping, registry)
    slugs = [] if (args.all or not args.slug) else [args.slug]
    if not slugs:
        slugs = sorted(mapping)
    for slug in slugs:
        scraped_path = STRATEGY / slug / "data" / f"{slug}.json"
        strategy_path = STRATEGY / slug / "data" / f"{slug}.strategy.json"
        if not scraped_path.is_file() or not strategy_path.is_file():
            continue
        try:
            scraped = load_json(scraped_path)
            data = load_json(strategy_path)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            report.add(ERROR, slug, f"strategy/{slug}/data/", f"JSON 解析失败：{error}")
            continue
        check_scraped(report, slug, scraped, presets_by_entry.get((scraped.get("meta") or {}).get("entryPageId")))
        check_image_refs(report, slug, f"strategy/{slug}/data/{slug}.json", scraped)
        check_image_refs(report, slug, f"strategy/{slug}/data/{slug}.strategy.json", data)
        check_images_present(report, slug)
        check_panels(report, slug, data)
        check_drive_builds(report, slug, data, disc_names)
        check_teams(report, slug, data, preset_ids, disc_names)
        check_cinema_priority(report, slug, data)
        check_skill_priority(report, slug, data)
        check_text_guide(report, slug, data)
        check_skill_text(report, slug, scraped, data)
        check_placeholders(report, slug, data)
    check_generated_freshness(report)

    if args.json:
        print(json.dumps([issue.__dict__ for issue in report.issues], ensure_ascii=False, indent=2))
    else:
        for level in (ERROR, WARN, INFO):
            items = report.by_level(level)
            if not items:
                continue
            print(f"\n=== {level}（{len(items)}）===")
            for issue in items:
                print(f"  [{issue.slug}] {issue.file}\n      {issue.message}")
        errors = len(report.by_level(ERROR))
        warns = len(report.by_level(WARN))
        infos = len(report.by_level(INFO))
        print(f"\n体检结果：{errors} ERROR / {warns} WARN / {infos} INFO")
    return 1 if report.by_level(ERROR) or (args.strict and report.by_level(WARN)) else 0


if __name__ == "__main__":
    sys.exit(main())
