"""把攻略页目录、数据文件名、图片路径统一到规范 slug。

背景：历史攻略页先用拼音 / 旧 slug 命名文件和图片，后来目录改名但数据文件没跟着改，
导致 ``strategy/<slug>/data/<slug>.json`` 约定被破坏、后端测试按规范名读取时失败。

本脚本做四件事（默认只做前两件）：

1. 把 ``data/*.json`` 重命名为 ``<slug>.json`` / ``<slug>.strategy.json``；
2. 把 JSON / JS / HTML 里指向旧 slug 的 ``/images/strategy/<old>/``、``data/<old>.json``
   等引用改成当前目录的 slug；
3. ``--rescrape-invalid``：对不是合法 UTF-8 的抓取产物，按 ``meta.entryPageId`` 重新抓取；
4. ``--remove-legacy``：删除不在 ``data/agent-name-mapping.json`` 里的攻略目录。

用法（仓库根）::

    python tools/normalize_strategy.py --check
    python tools/normalize_strategy.py --rescrape-invalid --remove-legacy

``--check`` 只报告，不写文件；有漂移时退出码 1，可接进 CI。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STRATEGY_ROOT = REPO_ROOT / "strategy"
SCRAPER = REPO_ROOT / ".github" / "skills" / "agent-strategy" / "scripts" / "scrape_agent_guide.py"
MAPPING_PATH = REPO_ROOT / "data" / "agent-name-mapping.json"

IMAGE_PREFIX_RE = re.compile(r"/images/strategy/([^/\"']+)/")
ENTRY_PAGE_RE = re.compile(rb'"entryPageId"\s*:\s*(\d+)')
APP_DATA_URL_RE = re.compile(r"(const DATA_URL = ')[^']+(';)")
APP_STRATEGY_URL_RE = re.compile(r"(const STRATEGY_URL = ')[^']+(';)")
APP_REF_RE = re.compile(r"data/([^/\"']+?)(?:\.strategy)?\.json")


def load_mapping() -> tuple[dict[str, dict], set[str]]:
    mapping = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    by_slug = {item["slug"]: item for item in mapping}
    return by_slug, set(by_slug)


def is_utf8(path: Path) -> bool:
    try:
        path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    return True


def entry_page_id(path: Path) -> int | None:
    match = ENTRY_PAGE_RE.search(path.read_bytes())
    return int(match.group(1)) if match else None


def image_slugs(text: str) -> set[str]:
    return {match for match in IMAGE_PREFIX_RE.findall(text) if match}


def rewrite_references(text: str, slug: str, old_stems: set[str]) -> str:
    """把旧 slug 的图片 / 数据引用改成当前 slug；不碰 ``data/options.json`` 等共享文件。"""
    text = IMAGE_PREFIX_RE.sub(f"/images/strategy/{slug}/", text)
    for old in sorted(old_stems - {slug}):
        text = text.replace(f"strategy/{old}/data/{old}.strategy.json", f"strategy/{slug}/data/{slug}.strategy.json")
        text = text.replace(f"strategy/{old}/data/{old}.json", f"strategy/{slug}/data/{slug}.json")
        text = text.replace(f"data/{old}.strategy.json", f"data/{slug}.strategy.json")
        text = text.replace(f"data/{old}.json", f"data/{slug}.json")
    return text


def rewrite_app_urls(text: str, slug: str) -> str:
    text = APP_DATA_URL_RE.sub(rf"\g<1>data/{slug}.json\g<2>", text)
    return APP_STRATEGY_URL_RE.sub(rf"\g<1>data/{slug}.strategy.json\g<2>", text)


def rename_data_files(slug: str, data_dir: Path, apply: bool) -> tuple[list[Path], list[str], set[str]]:
    """返回 (规范文件, 问题列表, 旧 slug 集合)。"""
    issues: list[str] = []
    old_stems: set[str] = set()
    scraped = data_dir / f"{slug}.json"
    strategy = data_dir / f"{slug}.strategy.json"

    for target, suffix in ((scraped, ".json"), (strategy, ".strategy.json")):
        if target.exists():
            continue
        if suffix == ".strategy.json":
            candidates = sorted(data_dir.glob("*.strategy.json"))
        else:
            candidates = sorted(
                p for p in data_dir.glob("*.json")
                if not p.name.endswith(".strategy.json")
            )
        if len(candidates) == 1:
            old = candidates[0]
            old_stem = old.name[: -len(suffix)]
            old_stems.add(old_stem)
            issues.append(f"{old.relative_to(REPO_ROOT)} -> {target.relative_to(REPO_ROOT)}")
            if apply:
                old.rename(target)
        elif len(candidates) > 1:
            issues.append(f"{data_dir.relative_to(REPO_ROOT)} 有多个候选 {suffix}: {[p.name for p in candidates]}")
        elif not target.exists():
            issues.append(f"{target.relative_to(REPO_ROOT)} 缺失")
    return [scraped, strategy], issues, old_stems


def normalize_text_file(
    path: Path,
    slug: str,
    old_stems: set[str],
    apply: bool,
    *,
    is_app: bool = False,
) -> list[str]:
    if not path.exists() or not is_utf8(path):
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        text = handle.read()
    stems = old_stems | image_slugs(text)
    if is_app:
        stems |= {match.group(1) for match in APP_REF_RE.finditer(text)}
        text = rewrite_app_urls(text, slug)
    fixed = rewrite_references(text, slug, stems)
    if fixed != text:
        if apply:
            with path.open("w", encoding="utf-8", newline="") as handle:
                handle.write(fixed)
        return [f"引用已更新: {path.relative_to(REPO_ROOT)}"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="只报告，不写文件")
    parser.add_argument("--rescrape-invalid", action="store_true", help="重新抓取不是合法 UTF-8 的抓取产物")
    parser.add_argument("--remove-legacy", action="store_true", help="删除不在 mapping 中的攻略目录")
    args = parser.parse_args()
    apply = not args.check

    by_slug, canonical_slugs = load_mapping()
    problems: list[str] = []

    for entry in sorted(STRATEGY_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        slug = entry.name
        if slug not in canonical_slugs:
            problems.append(f"非规范目录: {entry.relative_to(REPO_ROOT)}")
            if apply and args.remove_legacy:
                shutil.rmtree(entry)
                print(f"已删除 {entry.relative_to(REPO_ROOT)}")
            continue

        data_dir = entry / "data"
        if not data_dir.is_dir():
            problems.append(f"缺少 data/: {entry.relative_to(REPO_ROOT)}")
            continue

        files, issues, old_stems = rename_data_files(slug, data_dir, apply)
        problems.extend(issues)
        scraped, strategy = files

        if scraped.exists() and not is_utf8(scraped):
            page_id = entry_page_id(scraped)
            problems.append(f"非 UTF-8 抓取产物: {scraped.relative_to(REPO_ROOT)}")
            if apply and args.rescrape_invalid:
                if page_id is None:
                    problems.append(f"无法从 {scraped.name} 解析 entryPageId")
                else:
                    cmd = [
                        sys.executable,
                        str(SCRAPER),
                        "--entry-page-id",
                        str(page_id),
                        "--slug",
                        slug,
                        "--output",
                        str(scraped),
                        "--no-images",
                    ]
                    result = subprocess.run(cmd, cwd=REPO_ROOT)
                    if result.returncode != 0:
                        problems.append(f"重新抓取失败: {scraped.relative_to(REPO_ROOT)}")
                    else:
                        print(f"已重新抓取 {scraped.relative_to(REPO_ROOT)} (entry {page_id})")

        for path in (scraped, strategy):
            problems.extend(normalize_text_file(path, slug, old_stems, apply))

        for name in ("app.js", "index.html"):
            path = entry / name
            problems.extend(
                normalize_text_file(
                    path,
                    slug,
                    old_stems,
                    apply,
                    is_app=name == "app.js",
                )
            )

    # Skill 文档里的示例路径也必须指向真实目录；历史实例曾大量引用旧拼音 slug。
    for skill_doc in sorted((REPO_ROOT / ".github" / "skills").rglob("SKILL.md")):
        text = skill_doc.read_text(encoding="utf-8")
        for ref in sorted(set(re.findall(r"strategy/([a-z0-9-]+)/", text))):
            if ref not in canonical_slugs and ref not in {"scripts"}:
                problems.append(f"Skill 文档引用不存在的目录: {skill_doc.relative_to(REPO_ROOT)} -> strategy/{ref}/")

    if args.check:
        for item in problems:
            print(item)
        print(f"共 {len(problems)} 项需要处理")
        return 1 if problems else 0

    print(f"完成；处理/发现问题 {len(problems)} 项")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
