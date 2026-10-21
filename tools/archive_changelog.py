"""changelog 归档：`docs/changelog.md` 只保留最近若干条，更早的按月归档到 `docs/changelog/`。

规则（与 `docs/README.md`「文档维护约定」一致）：
* `docs/changelog.md` 是**当前**变更记录，按时间倒序，保留最近 `--keep` 条（默认 12）；
* 更早的条目按**条目日期**归入 `docs/changelog/YYYY-MM-archive.md`；
* 归档文件同样按时间倒序：被移走的条目比归档里已有的**更新**，所以插到归档顶部；
* 归档文件保留原有的「后续计划 / 相关文档 / 历史归档」小节，并刷新其归档索引。

用法：
    python tools/archive_changelog.py               # 归档（默认保留 12 条）
    python tools/archive_changelog.py --keep 20     # 保留 20 条
    python tools/archive_changelog.py --dry-run     # 只看会移动哪些条目
    python tools/archive_changelog.py --list        # 列出当前条目与归档归属
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = REPO_ROOT / "docs" / "changelog.md"
ARCHIVE_DIR = REPO_ROOT / "docs" / "changelog"
DEFAULT_KEEP = 12

#: 指针类小节：不是变更条目，单独处理
FOOTER_TITLES = {"历史归档", "相关文档", "后续计划"}

_LINK_RE = re.compile(r"(\[[^\]]*\]\()([^)]+)(\))")


def rebase_links(text: str, old_dir: Path, new_dir: Path) -> str:
    """把条目里的相对链接按新位置重算（条目从 docs/ 移到 docs/changelog/ 时深度 +1）。"""
    if old_dir == new_dir:
        return text

    def replace(match: re.Match) -> str:
        target = match.group(2)
        if target.startswith(("http://", "https://", "#", "mailto:", "data:")):
            return match.group(0)
        clean = target.split("#", 1)[0].split("?", 1)[0]
        if not clean:
            return match.group(0)
        absolute = (old_dir / clean).resolve()
        if not absolute.exists():
            return match.group(0)
        new_rel = os.path.relpath(absolute, new_dir).replace("\\", "/")
        return match.group(1) + new_rel + target[len(clean):] + match.group(3)

    return _LINK_RE.sub(replace, text)


def split_entries(text: str) -> tuple[str, list[str], str]:
    """把 changelog 正文切成 (前言, [条目…], 页脚)。

    页脚是「历史归档 / 相关文档 / 后续计划」这类指针小节（不是变更条目），
    单独拆出来，归档时保留、当前文件里重建。
    """
    parts = re.split(r"(?m)^## ", text)
    if len(parts) < 2:
        return text, [], ""
    preamble = parts[0]
    sections = ["## " + part.rstrip("\n") for part in parts[1:]]
    entries: list[str] = []
    footers: list[str] = []
    for section in sections:
        title = section.splitlines()[0].strip().lstrip("#").strip()
        (footers if title in FOOTER_TITLES else entries).append(section)
    return preamble, entries, "\n---\n\n".join(footers)


def entry_date(entry: str) -> str:
    """条目日期（取标题里的 YYYY-MM-DD）。"""
    match = re.match(r"##\s*(\d{4}-\d{2}-\d{2})", entry)
    return match.group(1) if match else ""


def archive_name(entry: str) -> str:
    """按条目日期归入的归档文件名。"""
    date = entry_date(entry)
    return f"{date[:7]}-archive.md" if date else "unknown-archive.md"


def render(preamble: str, entries: list[str], footer: str) -> str:
    """按既有结构渲染正文：前言 + 条目（倒序）+ 页脚。"""
    body = preamble.rstrip("\n") + "\n"
    for item in entries:
        body += "\n---\n\n" + item.rstrip("\n") + "\n"
    if footer:
        body += "\n---\n\n" + footer.rstrip("\n") + "\n"
    return body.rstrip("\n") + "\n"


def archive_index(prefix: str = "changelog/") -> str:
    """归档索引（页脚里列出的归档文件）。"""
    names = sorted(p.name for p in ARCHIVE_DIR.glob("*-archive.md"))
    return "\n".join(f"- [{prefix}{name}]({prefix}{name})" for name in names)


def refresh_archive_footer(footer: str, prefix: str) -> str:
    """重建页脚里的「历史归档」小节（其它小节原样保留）。"""
    if not footer:
        return footer
    parts = re.split(r"(?m)^## ", footer)
    head = parts[0]
    out = [head]
    for part in parts[1:]:
        section = "## " + part
        title = section.splitlines()[0].strip().lstrip("#").strip()
        if title == "历史归档":
            section = "## 历史归档\n\n更早的变更记录按月归档：\n\n" + archive_index(prefix=prefix)
        out.append(section)
    return "\n---\n\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", type=int, default=DEFAULT_KEEP, help=f"当前文件保留的条目数（默认 {DEFAULT_KEEP}）")
    parser.add_argument("--dry-run", action="store_true", help="只报告，不写文件")
    parser.add_argument("--list", action="store_true", help="列出当前条目与归档归属")
    args = parser.parse_args()

    if not CHANGELOG.is_file():
        print(f"找不到 {CHANGELOG}", file=sys.stderr)
        return 1

    text = CHANGELOG.read_text(encoding="utf-8")
    preamble, entries, _footer = split_entries(text)
    if not entries:
        print("changelog 里没有条目", file=sys.stderr)
        return 1

    if args.list:
        for index, entry in enumerate(entries):
            mark = "保留" if index < args.keep else "→ 归档"
            print(f"{index + 1:3d}. {entry.splitlines()[0]}   [{mark} / {archive_name(entry)}]")
        return 0

    keep = entries[: args.keep]
    move = entries[args.keep :]
    print(f"当前 {len(entries)} 条 → 保留 {len(keep)} 条，归档 {len(move)} 条")
    if not move:
        print("无需归档")
        return 0

    by_archive: dict[str, list[str]] = {}
    for entry in move:
        by_archive.setdefault(archive_name(entry), []).append(
            rebase_links(entry, CHANGELOG.parent, ARCHIVE_DIR)
        )

    for name, batch in by_archive.items():
        target = ARCHIVE_DIR / name
        if target.is_file():
            existing = target.read_text(encoding="utf-8")
            ex_preamble, ex_entries, ex_footer = split_entries(existing)
            # 被移走的条目比归档里已有的更新 → 插到顶部；否则追加到末尾
            newest_existing = entry_date(ex_entries[0]) if ex_entries else ""
            newest_batch = entry_date(batch[0])
            if not ex_entries or newest_batch >= newest_existing:
                merged = batch + ex_entries
            else:
                merged = ex_entries + batch
            footer = refresh_archive_footer(ex_footer, prefix="")
            new_text = render(ex_preamble, merged, footer)
            action = "合并"
        else:
            header = (
                f"# 变更记录归档 · {name.removesuffix('-archive.md')}\n\n"
                "> 早期变更记录按月归档；最新记录见 [../changelog.md](../changelog.md)。\n"
                "> 条目按时间倒序（越新越靠前）。\n"
            )
            new_text = render(header, batch, "")
            action = "新建"
        if args.dry_run:
            print(f"  [dry-run] {action} {target.relative_to(REPO_ROOT)} ← {len(batch)} 条")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(new_text, encoding="utf-8", newline="")
        print(f"  已{action} {target.relative_to(REPO_ROOT)}（+{len(batch)} 条）")

    if args.dry_run:
        return 0

    # 重写当前文件：前言 + 保留的条目 + 重建的「历史归档」指引
    footer = (
        "## 历史归档\n\n"
        "更早的变更记录按月归档：\n\n"
        + archive_index()
    )
    CHANGELOG.write_text(render(preamble, keep, footer), encoding="utf-8", newline="")
    print(f"  已更新 {CHANGELOG.relative_to(REPO_ROOT)}（保留 {len(keep)} 条）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
