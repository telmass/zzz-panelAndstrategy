"""为缺少立绘背景的代理人攻略页补齐背景图。

数据来源：Gachabase（Zenless Zone Zero，beta 分支）的 SvelteKit `__data.json`
接口。响应是 devalue 扁平格式，且被拆成两行——第 1 行是导航壳，第 2 行是
`{"type":"chunk","id":1,"data":[...]}` 的真数据。

立绘字段为 `entity.assets.splash_art_path_hash`，经 `variants[hash].webp`
可得到 Gachabase CDN 上的 webp 地址，直接存成 `background.webp`
（Gachabase 只提供 webp 变体，省掉二次转码）。

用法：
    uv run python tools/fetch_agent_backgrounds.py            # 补齐缺失的背景图
    uv run python tools/fetch_agent_backgrounds.py --dry-run  # 只报告，不落盘
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from difflib import get_close_matches
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPPING_PATH = os.path.join(ROOT, "data", "catalog", "agent-index.json")
IMAGE_DIR = os.path.join(ROOT, "frontend", "public", "images", "strategy")
LIST_URL = "https://zzz.gachabase.net/agents/beta/__data.json?lang=chs"
DETAIL_URL = "https://zzz.gachabase.net/agents/{id}/{slug}/beta/__data.json?lang=chs"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "*/*"}


def fetch(url: str, binary: bool = False, retries: int = 3) -> Any:
    """带重试的 GET。"""
    last: Exception | None = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=90) as response:
                payload = response.read()
            return payload if binary else payload.decode("utf-8")
        except Exception as error:  # noqa: BLE001 - 网络层异常统一重试
            last = error
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"请求失败 {url}: {last}")


def unflatten(values: list) -> Any:
    """还原 devalue 的扁平数组格式。"""

    cache: dict[int, Any] = {}

    def hydrate(index: int) -> Any:
        if index == -1:
            return None
        if index == -2:
            return float("nan")
        if index == -3:
            return float("inf")
        if index == -4:
            return float("-inf")
        if index in cache:
            return cache[index]
        value = values[index]
        if value is None or isinstance(value, (str, int, float, bool)):
            cache[index] = value
            return value
        if isinstance(value, list):
            items: list[Any] = []
            cache[index] = items
            for item in value:
                items.append(hydrate(item))
            return items
        record: dict[str, Any] = {}
        cache[index] = record
        for key, ref in value.items():
            record[key] = hydrate(ref)
        return record

    return hydrate(0)


def chunk_data(text: str) -> dict:
    """取出 SvelteKit 响应里 chunk 的数据体。"""
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get("type") == "chunk":
            return unflatten(payload["data"])["data"]
    raise RuntimeError("响应里没有 chunk 数据")


def normalize(text: str | None) -> str:
    """中文/英文名归一化：去掉空格、间隔号、连字符等噪音。"""
    return re.sub(r"[\s·・.\-—_&']", "", text or "").lower()


def webp_size(data: bytes) -> tuple[int, int] | None:
    """解析 webp 的画布尺寸（VP8X / VP8 两种容器）。"""
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    chunk = data[12:16]
    if chunk == b"VP8X":
        width = int.from_bytes(data[24:27], "little") + 1
        height = int.from_bytes(data[27:30], "little") + 1
        return width, height
    if chunk == b"VP8 ":
        width = int.from_bytes(data[26:28], "little") & 0x3FFF
        height = int.from_bytes(data[28:30], "little") & 0x3FFF
        return width, height
    return None


def match_slug(entry: dict, by_cn: dict[str, str], by_en: dict[str, str], repo_slugs: set[str]) -> str | None:
    """优先用 gachabase 的 slug 直配，其次中文名（短名/全名），英文名做兜底。"""
    if entry.get("slug") in repo_slugs:
        return entry["slug"]
    names = [entry.get("name", {}).get("text"), entry.get("full_name", {}).get("text")]
    for name in names:
        slug = by_cn.get(normalize(name))
        if slug:
            return slug
    candidates = get_close_matches(normalize(entry.get("internal_name", "")), list(by_en), 1, 0.72)
    return by_en[candidates[0]] if candidates else None


def strategy_path(slug: str) -> str:
    return os.path.join(ROOT, "strategy", slug, "data", f"{slug}.strategy.json")


def has_background(slug: str) -> bool:
    path = strategy_path(slug)
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8") as handle:
        return "background" in json.load(handle)


def write_background_field(slug: str) -> None:
    """在攻略 JSON 顶层插入 background 字段（保持其余内容逐字节不变）。"""
    path = strategy_path(slug)
    with open(path, encoding="utf-8") as handle:
        raw = handle.read()
    if '"background"' in raw:
        return
    newline = "\r\n" if "\r\n" in raw else "\n"
    line = f'  "background": "/images/strategy/{slug}/background.webp",{newline}'
    prefix = "{" + newline
    if raw.startswith(prefix):
        raw = prefix + line + raw[len(prefix):]
    elif raw.startswith("{\n"):
        raw = "{\n" + line + raw[2:]
    else:
        raise RuntimeError(f"{path} 不是预期的 JSON 结构")
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不下载/写文件")
    parser.add_argument("--delay", type=float, default=0.4, help="每次请求之间的间隔秒数")
    parser.add_argument("--skip", default="", help="逗号分隔的 slug 黑名单")
    args = parser.parse_args()

    skip = {item.strip() for item in args.skip.split(",") if item.strip()}

    with open(MAPPING_PATH, encoding="utf-8") as handle:
        mapping = json.load(handle)
    by_cn: dict[str, str] = {}
    by_en: dict[str, str] = {}
    for item in mapping:
        for key in (item.get("cn_short"), item.get("cn_full")):
            if key:
                by_cn.setdefault(normalize(key), item["slug"])
        if item.get("en"):
            by_en.setdefault(normalize(item["en"]), item["slug"])

    listing = chunk_data(fetch(LIST_URL))
    entries = listing["entries"]
    print(f"Gachabase 代理人条目：{len(entries)}")

    repo_slugs = {item["slug"] for item in mapping}
    pairs: list[tuple[str, dict]] = []
    unresolved: list[str] = []
    seen: dict[str, list[dict]] = {}
    for entry in entries:
        slug = match_slug(entry, by_cn, by_en, repo_slugs)
        if slug:
            seen.setdefault(slug, []).append(entry)
        else:
            unresolved.append(f'{entry["id"]} {entry.get("name", {}).get("text")} / {entry.get("internal_name")}')
    if unresolved:
        print("未能匹配仓库 slug：")
        for item in unresolved:
            print("  -", item)

    # gachabase 里同一位代理人可能有多条记录（本体 + 换装），换装记录的
    # splash_art_path_hash 会串到别的代理人身上，因此只保留 id 最小的那条（本体）。
    for slug, sources in seen.items():
        if len(sources) > 1:
            dropped = ", ".join(f'{item["id"]}/{item["slug"]}' for item in sources[1:])
            print(f"[重复记录] {slug} 保留 {sources[0]['id']}，忽略 {dropped}")
            pairs.append((slug, sources[0]))
        else:
            pairs.append((slug, sources[0]))

    covered = {slug for slug, _ in pairs if os.path.exists(strategy_path(slug))}
    missing = sorted(repo_slugs - covered)
    print(f"仓库 slug 覆盖：{len(covered)}/{len(repo_slugs)}，未覆盖：{missing}")

    done = skipped = failed = 0
    for slug, entry in pairs:
        if slug in skip:
            continue
        if not os.path.exists(strategy_path(slug)):
            continue
        if has_background(slug):
            skipped += 1
            continue
        try:
            detail = chunk_data(fetch(DETAIL_URL.format(id=entry["id"], slug=entry["slug"])))
            assets = detail["entity"].get("assets", {})
            splash_hash = assets.get("splash_art_path_hash")
            if not splash_hash:
                print(f"[skip] {slug}: 没有 splash_art_path_hash")
                skipped += 1
                continue
            variant = detail.get("variants", {}).get(splash_hash, {})
            url = variant.get("webp")
            if not url:
                ref = detail.get("refs", {}).get(splash_hash, {})
                url = ref.get("url")
            if not url:
                print(f"[skip] {slug}: 找不到可用的图片地址")
                skipped += 1
                continue
            if args.dry_run:
                print(f"[plan] {slug:16s} {url}")
                continue
            target_dir = os.path.join(IMAGE_DIR, slug)
            os.makedirs(target_dir, exist_ok=True)
            data = fetch(url, binary=True)
            size = webp_size(data)
            if size is None:
                print(f"[warn] {slug}: 不是可识别的 webp，前 16 字节 {data[:16]!r}")
            elif size[1] <= size[0]:
                print(f"[warn] {slug}: 尺寸 {size[0]}x{size[1]} 不是竖版立绘")
            with open(os.path.join(target_dir, "background.webp"), "wb") as handle:
                handle.write(data)
            write_background_field(slug)
            dimension = f"{size[0]}x{size[1]}" if size else "?"
            print(f"[ok] {slug:16s} {len(data) / 1024:8.1f} KB  {dimension}")
            done += 1
        except (urllib.error.URLError, RuntimeError, KeyError, IndexError) as error:
            print(f"[fail] {slug}: {error}")
            failed += 1
        time.sleep(args.delay)

    print(f"完成：新增 {done}，跳过 {skipped}，失败 {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
