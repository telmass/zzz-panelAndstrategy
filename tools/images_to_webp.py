"""把 `frontend/public/images` 下的 PNG 统一转成 webp，并同步改写全仓引用。

背景：仓库图片全是 PNG（464 张 / 约 250 MB），其中影画立绘单张接近 3 MB。
webp 在同等观感下能压到 10% 上下，整包体积可降到 ~25 MB。

用法：
    uv run --with pillow python tools/images_to_webp.py --dry-run   # 预览收益
    uv run --with pillow python tools/images_to_webp.py             # 实际迁移

注意：
- 只改写**本地** `/images/…` 引用；`https://…png` 这类远程地址原样保留。
- 转换在字节层面完成，保留原文件的换行符，避免整文件 diff。
- 迁移后 `frontend/src/constants/strategyGuides.ts` 需要重新生成。
"""

from __future__ import annotations

import argparse
import io
import os
import re
import sys
import time
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover - 依赖缺失时给出明确提示
    print("缺少 Pillow，请用 `uv run --with pillow python tools/images_to_webp.py` 运行")
    raise

ROOT = Path(__file__).resolve().parent.parent
IMAGE_ROOT = ROOT / "frontend" / "public" / "images"

# 只扫这些后缀的文本文件
TEXT_SUFFIXES = {".py", ".ts", ".tsx", ".vue", ".css", ".json", ".md", ".html", ".js", ".yml", ".yaml"}
# 这些目录跳过：其它 worktree、虚拟环境、构建产物、历史计划稿
SKIP_DIRS = {
    ".git",
    ".kilo",
    ".venv",
    ".venv-workers",
    "node_modules",
    "dist",
    "coverage",
    "__pycache__",
    "python_modules",
    ".pytest_cache",
    ".ruff_cache",
}

# 本地图片引用：`/images/…` 开头的路径（含模板串里的 ${…}）
IMAGE_REF_RE = re.compile(r"(?P<p>/images/[^\s\"'`()\[\]<>,;]*?)\.png")


def encode(src: Path, quality: int, lossless: bool) -> bytes:
    """把一张图编码成 webp 字节。

    已经是 webp 载荷的（历史上用 .png 名保存的立绘背景）直接透传，
    避免二次有损压缩反而变大。
    """
    raw = src.read_bytes()
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return raw
    image = Image.open(src)
    image.load()
    if image.mode not in ("RGBA", "RGB"):
        image = image.convert("RGBA")
    buffer = io.BytesIO()
    if lossless:
        image.save(buffer, "WEBP", lossless=True, quality=100, method=6)
    else:
        image.save(buffer, "WEBP", quality=quality, method=6)
    return buffer.getvalue()


def iter_text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        files.append(path)
    return files


def write_bytes_safe(path: Path, payload: bytes, retries: int = 6) -> None:
    """写文件；被编辑器/文件监听器占用时重试。"""
    last: Exception | None = None
    for attempt in range(retries):
        try:
            path.write_bytes(payload)
            return
        except OSError as error:  # noqa: PERF203 - 需要逐次重试
            last = error
            time.sleep(0.4 * (attempt + 1))
    raise RuntimeError(f"写入失败 {path}: {last}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quality", type=int, default=90, help="webp 有损质量（默认 90）")
    parser.add_argument("--lossless", action="store_true", help="改用无损 webp")
    parser.add_argument("--dry-run", action="store_true", help="只统计不落盘")
    args = parser.parse_args()

    pngs = sorted(IMAGE_ROOT.rglob("*.png"))
    print(f"待转换 PNG：{len(pngs)} 张")

    total_before = total_after = 0
    converted = 0
    for index, src in enumerate(pngs, start=1):
        dst = src.with_suffix(".webp")
        try:
            payload = encode(src, args.quality, args.lossless)
        except Exception as error:  # noqa: BLE001
            print(f"[fail] {src.relative_to(ROOT)}: {error}", flush=True)
            continue
        total_before += src.stat().st_size
        total_after += len(payload)
        converted += 1
        if not args.dry_run:
            dst.write_bytes(payload)
            src.unlink()
        if index % 25 == 0 or index == len(pngs):
            print(
                f"  进度 {index}/{len(pngs)}  "
                f"{total_before / 1024 / 1024:.1f} MB -> {total_after / 1024 / 1024:.1f} MB",
                flush=True,
            )
    print(
        f"体积：{total_before / 1024 / 1024:.2f} MB -> {total_after / 1024 / 1024:.2f} MB "
        f"（省 {(1 - total_after / max(total_before, 1)) * 100:.1f}%，共 {converted} 张）"
    )

    refs = []
    for path in iter_text_files():
        try:
            raw = path.read_bytes()
        except Exception:  # noqa: BLE001
            continue
        text = raw.decode("utf-8")
        new_text, count = IMAGE_REF_RE.subn(lambda m: m.group("p") + ".webp", text)
        if count:
            refs.append((path, count, text, new_text))
    print(f"待改写引用：{len(refs)} 个文件，共 {sum(c for _, c, _, _ in refs)} 处")

    if args.dry_run:
        print("\n--- 干跑，未写入任何文件 ---")
        for path, count, _, _ in refs[:20]:
            print(f"  {path.relative_to(ROOT)}: {count} 处")
        if len(refs) > 20:
            print(f"  … 另有 {len(refs) - 20} 个文件")
        return 0

    for path, count, text, new_text in refs:
        write_bytes_safe(path, new_text.encode("utf-8"))
    print(f"已改写 {len(refs)} 个文件的引用")

    # 校验：仓库里不应再残留指向本地图片的 .png 引用
    leftover = []
    for path in iter_text_files():
        try:
            text = path.read_bytes().decode("utf-8")
        except Exception:  # noqa: BLE001
            continue
        for match in IMAGE_REF_RE.finditer(text):
            leftover.append(f"{path.relative_to(ROOT)} -> {match.group(0)}")
    if leftover:
        print("仍有 .png 引用：")
        for item in leftover[:20]:
            print("  ", item)
        return 1

    # 校验：每个本地图片引用都要有对应文件
    missing = []
    for path in iter_text_files():
        try:
            text = path.read_bytes().decode("utf-8")
        except Exception:  # noqa: BLE001
            continue
        for match in IMAGE_REF_RE.finditer(text):
            ref = match.group(0).lstrip("/")
            if not (ROOT / "frontend" / "public" / ref).exists():
                missing.append(f"{path.relative_to(ROOT)} -> {match.group(0)}")
    if missing:
        print("引用了不存在的图片：")
        for item in missing[:20]:
            print("  ", item)
        return 1

    print("校验通过：无残留 .png 引用，所有本地图片引用均存在")
    return 0


if __name__ == "__main__":
    sys.exit(main())
