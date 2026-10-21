"""为代理人攻略页抓取「角色框头像」（film 图）。

数据来源：Nanoka（https://zzz.nanoka.cc）的静态数据接口。

    清单   https://static.nanoka.cc/zzz/<ver>/character.json
    详情   https://static.nanoka.cc/zzz/<ver>/<lang>/character/<id>.json
    资产   https://static.nanoka.cc/assets/zzz/<文件名>.webp

资产命名：`IconRolePiece<编号>.webp`，编号取自详情 JSON 的 `icon`（如 `IconRole13`
→ 13，保留前导零：安比 01 / 可琳 09 / 11号 05）；个别代理人（如克拉蕾）该编号在 CDN
上不存在，回退到 `partner_info.inter_knot_icon` 的编号（`IconInterKnotRole0069` → 69）。

用法：
    uv run python tools/fetch_agent_films.py            # 抓取缺失的 film 图
    uv run python tools/fetch_agent_films.py --dry-run  # 只报告，不落盘
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Any

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPPING_PATH = os.path.join(ROOT, "data", "catalog", "agent-index.json")
IMAGE_DIR = os.path.join(ROOT, "frontend", "public", "images", "strategy")
STATIC = "https://static.nanoka.cc"
MANIFEST = f"{STATIC}/manifest.json"
DEFAULT_VERSION = "3.3.12+19566749"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "*/*"}


def fetch(url: str, retries: int = 3) -> bytes:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=90) as response:
                return response.read()
        except Exception as error:  # noqa: BLE001
            last = error
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"请求失败 {url}: {last}")


def fetch_json(url: str) -> Any:
    return json.loads(fetch(url).decode("utf-8"))


def resolve_version() -> str:
    """优先用 manifest 里的最新 zzz 版本，取不到就回退到已知可用版本。"""
    try:
        manifest = fetch_json(MANIFEST)
        version = manifest.get("zzz", {}).get("latest")
        if version:
            return version
    except Exception:  # noqa: BLE001
        pass
    return DEFAULT_VERSION


def normalize(text: str | None) -> str:
    return re.sub(r"[\s·・.\-—_&']", "", text or "").lower()


def build_index(mapping: list[dict]) -> tuple[dict[str, str], dict[str, str]]:
    by_cn: dict[str, str] = {}
    by_en: dict[str, str] = {}
    for item in mapping:
        for key in (item.get("cn_short"), item.get("cn_full")):
            if key:
                by_cn.setdefault(normalize(key), item["slug"])
        if item.get("en"):
            by_en.setdefault(normalize(item["en"]), item["slug"])
    return by_cn, by_en


def piece_candidates(detail: dict) -> list[str]:
    """按优先级给出可能的资产文件名（去重、保持顺序）。"""
    names: list[str] = []

    def push(number: str) -> None:
        if not number:
            return
        number = number.replace(".png", "")
        name = f"IconRolePiece{number}.webp"
        if name not in names:
            names.append(name)

    push(detail.get("icon", "").replace("IconRole", ""))
    partner = detail.get("partner_info", {})
    inter_knot = partner.get("inter_knot_icon", "").split("/")[-1]
    # inter-knot 编号是 4 位补零序列（0069），但资产名用的是不补零的形式（69）
    push((inter_knot.replace("IconInterKnotRole", "").lstrip("0")) or "0")
    return names


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不落盘")
    parser.add_argument("--force", action="store_true", help="已存在也重新抓取")
    parser.add_argument("--delay", type=float, default=0.4, help="请求间隔秒数")
    parser.add_argument("--skip", default="", help="逗号分隔的 slug 黑名单")
    args = parser.parse_args()

    skip = {item.strip() for item in args.skip.split(",") if item.strip()}

    with open(MAPPING_PATH, encoding="utf-8") as handle:
        mapping = json.load(handle)
    by_cn, by_en = build_index(mapping)
    repo_slugs = {item["slug"] for item in mapping}

    version = resolve_version()
    base = f"{STATIC}/zzz/{version}"
    print(f"Nanoka 数据版本：{version}")

    characters = fetch_json(f"{base}/character.json")
    print(f"Nanoka 代理人条目：{len(characters)}")

    done = skipped = failed = 0
    digests: dict[str, list[str]] = {}
    for cid, character in characters.items():
        slug = (
            by_cn.get(normalize(character.get("zh")))
            or by_cn.get(normalize(character.get("en")))
            or by_en.get(normalize(character.get("code")))
        )
        if not slug or slug in skip:
            continue
        if slug not in repo_slugs:
            continue
        target_dir = os.path.join(IMAGE_DIR, slug)
        if not os.path.exists(os.path.join(ROOT, "strategy", slug)):
            continue
        target = os.path.join(target_dir, "film.webp")
        if os.path.exists(target) and not args.force:
            skipped += 1
            continue
        try:
            detail = fetch_json(f"{base}/en/character/{cid}.json")
            names = piece_candidates(detail)
            payload = None
            used = ""
            for name in names:
                try:
                    payload = fetch(f"{STATIC}/assets/zzz/{name}")
                    used = name
                    break
                except RuntimeError:
                    continue
            if payload is None:
                print(f"[fail] {slug}: 找不到角色框头像（尝试 {names}）")
                failed += 1
                continue
            digest = hashlib.sha256(payload).hexdigest()
            digests.setdefault(digest, []).append(slug)
            if args.dry_run:
                print(f"[plan] {slug:16s} {len(payload) / 1024:6.1f} KB  {used}")
                continue
            os.makedirs(target_dir, exist_ok=True)
            with open(target, "wb") as handle:
                handle.write(payload)
            print(f"[ok] {slug:16s} {len(payload) / 1024:6.1f} KB  {used}")
            done += 1
        except (urllib.error.URLError, RuntimeError, KeyError) as error:
            print(f"[fail] {slug}: {error}")
            failed += 1
        time.sleep(args.delay)

    duplicates = {digest: slugs for digest, slugs in digests.items() if len(slugs) > 1}
    if duplicates:
        print("注意：以下代理人拿到的是同一张图（需人工复核）：")
        for slugs in duplicates.values():
            print("  -", ", ".join(slugs))
    print(f"完成：新增 {done}，跳过 {skipped}，失败 {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
