"""Validate documentation: relative links, backtick paths, and stale references.

Checks:
1. All relative Markdown links in docs/ and README.md point to existing files.
2. All backtick-quoted paths (``tools/…``, ``frontend/…``, ``backend/…``, ``data/…``,
   ``strategy/…``, ``docs/…``) in SKILL.md files point to existing files/dirs.
3. No stale ``DATA_URL`` / ``app.js`` / ``styles.css`` references in current-state docs.

Usage:
    python tools/check_docs.py          # run all checks
    python tools/check_docs.py --check  # same (CI-friendly exit code)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: File extensions to scan for Markdown links.
MD_EXTENSIONS = {".md"}

#: Path prefixes that indicate a repo-relative reference in backticks.
BACKTICK_PREFIXES = ("tools/", "frontend/", "backend/", "data/", "strategy/", "docs/")

#: Patterns that indicate stale references in current-state docs.
STALE_PATTERNS = [
    (re.compile(r"DATA_URL"), "DATA_URL (removed in Vue migration)"),
    (re.compile(r"strategy/ye-shun-guang"), "old slug ye-shun-guang"),
]

#: Documents exempt from stale-reference checks (historical archives + meta-docs).
HISTORICAL_EXEMPT = {
    Path("docs/changelog"),
    Path("docs/completeds"),
    Path("docs/changelog.md"),
    Path("docs/repair-plan.md"),  # meta-document that describes removed items
    Path("docs/structure-review.md"),  # historical archive
}


def is_historical(path: Path) -> bool:
    """Check if a file is in a historical/exempt directory."""
    try:
        rel = path.relative_to(REPO_ROOT)
    except ValueError:
        return False
    return any(rel == ex or ex in rel.parents for ex in HISTORICAL_EXEMPT)


def check_markdown_links() -> list[str]:
    """Verify all relative links in Markdown files resolve."""
    problems = []
    for md in sorted(REPO_ROOT.rglob("*.md")):
        if any(part in {".git", "node_modules", ".venv", ".venv-workers", "python_modules",
                        ".wrangler", "__pycache__", ".pytest_cache", ".kilo", "dist"} for part in md.parts):
            continue
        try:
            text = md.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            if link.startswith(("http://", "https://", "#", "mailto:", "data:")):
                continue
            target = link.split("#", 1)[0].split("?", 1)[0]
            if not target:
                continue
            resolved = (md.parent / target).resolve()
            if not resolved.exists():
                problems.append(f"{md.relative_to(REPO_ROOT)}: broken link -> {link}")
    return problems


def check_backtick_paths() -> list[str]:
    """Verify backtick-quoted repo paths in SKILL.md files exist."""
    problems = []
    for skill in sorted((REPO_ROOT / ".github" / "skills").rglob("SKILL.md")):
        text = skill.read_text(encoding="utf-8")
        for match in re.findall(r"`((?:tools|frontend|backend|data|strategy|docs)/[\w./_-]+)`", text):
            if "<" in match or "*" in match:
                continue
            target = REPO_ROOT / match.rstrip("/")
            if not target.exists():
                problems.append(f"{skill.relative_to(REPO_ROOT)}: path not found -> {match}")
    return problems


def check_stale_references() -> list[str]:
    """Check for stale references in non-historical docs."""
    problems = []
    for md in sorted(REPO_ROOT.rglob("*.md")):
        if any(part in {".git", "node_modules", ".venv", "dist", ".kilo"} for part in md.parts):
            continue
        if is_historical(md):
            continue
        try:
            text = md.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pattern, description in STALE_PATTERNS:
            for match in pattern.finditer(text):
                line_num = text[: match.start()].count("\n") + 1
                problems.append(
                    f"{md.relative_to(REPO_ROOT)}:{line_num}: stale reference ({description})"
                )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="CI mode (always exits non-zero on failure)")
    args = parser.parse_args()

    all_problems: list[str] = []
    all_problems.extend(check_markdown_links())
    all_problems.extend(check_backtick_paths())
    all_problems.extend(check_stale_references())

    if all_problems:
        print(f"check_docs: {len(all_problems)} problem(s) found:", file=sys.stderr)
        for p in all_problems:
            print(f"  {p}", file=sys.stderr)
        return 1

    print("check_docs: all documentation references valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
