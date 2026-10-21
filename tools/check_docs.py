"""Validate documentation: relative links, backtick paths, stale references, and
quantity claims ("数量类事实") against the data they describe.

Checks:
1. All relative Markdown links in docs/ and README.md point to existing files.
2. All backtick-quoted paths (``tools/…``, ``frontend/…``, ``backend/…``, ``data/…``,
   ``strategy/…``, ``docs/…``) in SKILL.md files point to existing files/dirs.
3. No stale ``DATA_URL`` / ``app.js`` / ``styles.css`` references in current-state docs.
4. Quantity claims in current-state docs match the data they point at
   （代理人 / 音擎 / 驱动盘 / 规则表 / 命名映射 / 攻略页 / 图片 / 测试数）。

Usage:
    python tools/check_docs.py          # run all checks
    python tools/check_docs.py --check  # same (CI-friendly exit code)
    python tools/check_docs.py --skip-test-counts   # 不跑测试计数核对（更快）
"""

from __future__ import annotations

import argparse
import json
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
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / ".github" / "skills"
ROOT_DOCS = REPO_ROOT / "docs"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_paths import dataset_path  # noqa: E402

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


def check_html_links() -> list[str]:
    """Verify relative links in HTML files resolve.

    仓库根的 ``index.html`` 是开发者指引页，它链到各文档。文档重组（``docs/``
    下面的文件搬到 ``overview/`` ``design/`` ``guides/``）之后，**Markdown 里的
    链接有闸门守，HTML 里的没有**——于是那几条链接悄悄断了很久。

    所以这里把 HTML 也纳入检查：``href="…"`` 里的相对路径必须存在。
    """
    problems = []
    for html in sorted(REPO_ROOT.rglob("*.html")):
        if any(part in {".git", "node_modules", ".venv", ".venv-workers", "python_modules",
                        ".wrangler", "__pycache__", ".pytest_cache", ".kilo", "dist"} for part in html.parts):
            continue
        try:
            text = html.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for link in re.findall(r'(?:href|src)="([^"]+)"', text):
            if link.startswith(("http://", "https://", "#", "mailto:", "data:", "//")):
                continue
            target = link.split("#", 1)[0].split("?", 1)[0]
            if not target:
                continue
            if target.startswith("/"):
                # 服务器绝对路径（Vite dev server 的 /src/main.ts、/favicon.svg）。
                # 它们由 dev server 解析，不是文件相对路径；静态资源在
                # frontend/public/ 下，源码在 frontend/ 下。
                candidates = [
                    REPO_ROOT / "frontend" / "public" / target.lstrip("/"),
                    REPO_ROOT / "frontend" / target.lstrip("/"),
                ]
                if any(candidate.exists() for candidate in candidates):
                    continue
                problems.append(f"{html.relative_to(REPO_ROOT)}: broken link -> {link}")
                continue
            resolved = (html.parent / target).resolve()
            if not resolved.exists():
                problems.append(f"{html.relative_to(REPO_ROOT)}: broken link -> {link}")
    return problems


def check_backtick_paths() -> list[str]:
    """Verify backtick-quoted repo paths in SKILL.md and current-state docs exist."""
    problems = []
    targets = [SKILL_DIR / name / "SKILL.md" for name in SKILL_DIR.iterdir() if name.is_dir()]
    targets += [path for path in ROOT_DOCS.rglob("*.md") if not is_historical(path)]
    targets += [
        REPO_ROOT / "README.md",
        REPO_ROOT / "data" / "README.md",
        REPO_ROOT / "tools" / "README.md",
        REPO_ROOT / "frontend" / "src" / "README.md",
        REPO_ROOT / "frontend" / "tests" / "README.md",
        REPO_ROOT / "backend" / "tests" / "README.md",
    ]
    seen = set()
    for target in targets:
        if not target.is_file() or target in seen:
            continue
        seen.add(target)
        text = target.read_text(encoding="utf-8")
        for match in re.finditer(r"`((?:tools|frontend|backend|data|strategy|docs)/[\w./_-]+)`", text):
            path_text = match.group(1)
            if "<" in path_text or "*" in path_text:
                continue
            # 去掉行号后缀（docs/xxx.md:116）
            path_text = path_text.split(":")[0]
            if not (REPO_ROOT / path_text.rstrip("/")).exists():
                problems.append(f"{target.relative_to(REPO_ROOT)}: path not found -> {match.group(1)}")
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


def count_json(path: Path, key: str | None = None) -> int:
    """数据文件的条目数（列表取长度，字典取 key 下的长度）。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return len(data)
    if key and isinstance(data.get(key), (list, dict)):
        return len(data[key])
    return len(data)


def count_images() -> tuple[int, set[str]]:
    """图片总数与出现的格式集合。"""
    root = REPO_ROOT / "frontend" / "public" / "images"
    count = 0
    formats: set[str] = set()
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".png", ".webp", ".jpg", ".jpeg", ".avif", ".gif"}:
            count += 1
            formats.add(path.suffix.lower().lstrip("."))
    return count, formats


def count_option_tables() -> tuple[int, int]:
    """配装规则表：表数与条目总数。

    只数**列表**值——规则表里还有 ``schemaVersion``（整数）与 ``_generated``
    （说明串）这类非表字段。
    """
    options = json.loads(dataset_path("calculator-rules").read_text(encoding="utf-8"))
    tables = {
        key: value
        for key, value in options.items()
        if isinstance(value, list)
    }
    return len(tables), sum(len(value) for value in tables.values())


def _backend_python() -> list[str]:
    """跑后端 pytest 的命令前缀。

    **必须用装了 pytest 的解释器**：`check_docs.py` 常用系统 python 跑（它零第三方
    依赖），而系统 python 里没有 pytest——用 ``sys.executable`` 收集会直接失败，
    于是「后端用例数」这项事实**静默地不再被核对**（返回 None 就跳过）。

    依次尝试：仓库根 / backend 下的 venv → ``uv run`` → 当前解释器。
    """
    for candidate in (
        REPO_ROOT / ".venv" / "Scripts" / "python.exe",
        REPO_ROOT / ".venv" / "bin" / "python",
        REPO_ROOT / "backend" / ".venv" / "Scripts" / "python.exe",
        REPO_ROOT / "backend" / ".venv" / "bin" / "python",
    ):
        if candidate.is_file():
            return [str(candidate)]
    uv = shutil.which("uv")
    if uv:
        return [uv, "run", "--project", str(REPO_ROOT / "backend"), "python"]
    return [sys.executable]


def count_backend_tests() -> int | None:
    """pytest 收集到的用例数（不执行）。"""
    command = _backend_python() + ["-m", "pytest", "--collect-only", "-q"]
    try:
        proc = subprocess.run(
            command,
            cwd=REPO_ROOT / "backend", capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=300,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    output = (proc.stdout or "") + (proc.stderr or "")
    match = re.search(r"(\d+) tests? collected", output)
    if match:
        return int(match.group(1))
    # 收集失败要说清楚为什么，而不是让这项事实悄悄不被核对。
    print(
        f"  warn     后端用例数收集失败（{' '.join(command)}）：\n"
        f"           {output.strip()[-300:]}",
        file=sys.stderr,
    )
    return None


def count_frontend_tests() -> int | None:
    """vitest 收集到的用例数（不执行）。"""
    npx = "npx.cmd" if sys.platform == "win32" else "npx"
    try:
        proc = subprocess.run(
            [npx, "vitest", "list"],
            cwd=REPO_ROOT / "frontend", capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=300,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    lines = [line for line in (proc.stdout or "").splitlines() if " > " in line]
    return len(lines) or None


#: 文档里可核对的「数量类事实」。
#: 每项 = (标签, [行内正则…], 实际值)；正则要带足够上下文，避免同一行里的别的数字被误判。
def scale_facts(skip_test_counts: bool = False) -> list[tuple[str, list[re.Pattern[str]], int]]:
    agents = count_json(dataset_path("agents"))
    weapons = count_json(dataset_path("weapons"))
    discs = count_json(dataset_path("drive-discs"))
    mapping = count_json(dataset_path("agent-index"))
    pages = len(list((REPO_ROOT / "strategy").glob("*/data/*.strategy.json")))
    images, _formats = count_images()
    tables, entries = count_option_tables()
    facts: list[tuple[str, list[re.Pattern[str]], int]] = [
        ("代理人预设", [
            re.compile(r"代理人预设(?:列表)?[（(]\s*(\d+)\s*条"),
            re.compile(r"\|\s*代理人预设\s*\|\s*(\d+)\s*条"),
        ], agents),
        ("代理人数", [re.compile(r"(\d+)\s*名代理人")], agents),
        ("音擎预设", [
            re.compile(r"音擎预设[（(]\s*(\d+)\s*条"),
            re.compile(r"\|\s*音擎预设\s*\|\s*(\d+)\s*条"),
        ], weapons),
        ("驱动盘套装", [
            re.compile(r"驱动盘套装效果[（(]?\s*(\d+)\s*套"),
            re.compile(r"\|\s*驱动盘套装效果[^|]*\|\s*(\d+)\s*条"),
        ], discs),
        ("配装规则表", [
            re.compile(r"配装规则表[（(]?\s*(\d+)\s*张"),
            re.compile(r"\|\s*配装规则表\s*\|\s*(\d+)\s*张"),
        ], tables),
        ("配装规则条目", [re.compile(r"(\d+)\s*个条目")], entries),
        ("命名映射", [
            re.compile(r"代理人命名映射[（(]?\s*(\d+)\s*条"),
            re.compile(r"\|\s*代理人命名映射\s*\|\s*(\d+)\s*条"),
        ], mapping),
        ("未上线代理人数", [re.compile(r"含\s*(\d+)\s*条未上线")], mapping - agents),
        ("攻略页目录", [
            re.compile(r"攻略页目录[（(]?\s*(\d+)\s*个"),
            re.compile(r"\|\s*攻略页目录\s*\|\s*(\d+)\s*个"),
        ], pages),
        ("图片资源", [
            re.compile(r"图片资源[（(]?\s*(\d+)\s*张"),
            re.compile(r"当前\s*(\d+)\s*张\s*(?:PNG|webp)", re.IGNORECASE),
            re.compile(r"原样拷贝[（(]?\s*(\d+)\s*张"),
            re.compile(r"\|\s*图片资源\s*\|\s*(\d+)\s*张"),
        ], images),
    ]
    if not skip_test_counts:
        backend = count_backend_tests()
        frontend = count_frontend_tests()
        if backend is not None:
            facts.append(("后端测试", [
                re.compile(r"后端[^\n|]{0,10}?(\d+)\s*项"),
                re.compile(r"pytest[^\n|]{0,10}?(\d+)\s*项"),
            ], backend))
        if frontend is not None:
            facts.append(("前端测试", [
                re.compile(r"前端[^\n|]{0,10}?(\d+)\s*项"),
                re.compile(r"npm run test[^\n|]{0,10}?(\d+)\s*项"),
            ], frontend))
    return facts


def check_scale_numbers(skip_test_counts: bool = False) -> list[str]:
    """核对文档里的「数量类事实」与数据源是否一致。"""
    problems: list[str] = []
    facts = scale_facts(skip_test_counts)
    for md in sorted(REPO_ROOT.rglob("*.md")):
        if any(part in {".git", "node_modules", ".venv", ".venv-workers", "python_modules",
                        ".wrangler", "__pycache__", ".pytest_cache", ".kilo", "dist"} for part in md.parts):
            continue
        if is_historical(md):
            continue
        try:
            text = md.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for label, patterns, actual in facts:
                if not any(pattern.search(line) for pattern in patterns):
                    continue
                for pattern in patterns:
                    for match in pattern.finditer(line):
                        stated = int(match.group(1))
                        if stated != actual:
                            problems.append(
                                f"{md.relative_to(REPO_ROOT)}:{line_no}: {label} 写了 {stated}，实际 {actual}"
                            )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="CI mode (always exits non-zero on failure)")
    parser.add_argument("--skip-test-counts", action="store_true", help="不核对前后端测试数（更快）")
    args = parser.parse_args()

    all_problems: list[str] = []
    all_problems.extend(check_markdown_links())
    all_problems.extend(check_html_links())
    all_problems.extend(check_backtick_paths())
    all_problems.extend(check_stale_references())
    all_problems.extend(check_scale_numbers(args.skip_test_counts))

    if all_problems:
        print(f"check_docs: {len(all_problems)} problem(s) found:", file=sys.stderr)
        for p in all_problems:
            print(f"  {p}", file=sys.stderr)
        return 1

    print("check_docs: all documentation references valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
