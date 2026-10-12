"""Refresh data/drive-disc-presets.json from the official HoYoLAB ZZZ Wiki.

Scans the wiki entry_page_id space through the public content API, keeps every
page that carries a ``driver_disk`` component (驱动盘 page signature), and
writes only the 2-piece / 4-piece set effects. Each set's icon is downloaded
to ``frontend/public/images/discs/ep-<entry_page_id>.png``, matching the
``ep-<entry_page_id>`` naming that ``images/agents`` and ``images/weapons``
already use; the JSON ``image`` field records the served URL
``/images/discs/ep-<entry_page_id>.png``（唯一图片根约定，见
``frontend/public/images/``）。

主词条表、副词条表、推荐角色等栏目一概不写——本文件只回答「这套驱动盘的
2 件套与 4 件套效果是什么」。

驱动盘页的判定与取值：

- 一页是驱动盘页，当且仅当它带 ``driver_disk`` 组件（六号位盘名、
  各号位满级主词条表、盘面图标都在里面）。代理人页与音擎页都没有该组件。
- 2/4 件套效果在**第一个**表头含「二件套」的 ``double_col_table`` 里：
  行内两列依次是 2 件套、4 件套，取纯文本（剥 HTML、折叠空白）。
  同一页上还有一个「推荐角色」表的表头不同，不会误取。
- 套装图标取 ``material_base_info.img``（详情页头部大图），缺失时回退
  页面 ``icon_url``（频道列表小图）。两者内容同一张图（同一内容哈希），
  只是 URL 后缀的尺寸参数不同。
- 效果文本保持 Wiki 原文，不做任何数值化。Wiki 自身的全角「＋」
  （混沌爵士的「异常精通＋30点。」）也照抄——数据源不做静默改写。

``data/drive-disc-presets.json`` 是驱动盘套装效果的唯一真实源，由本脚本
整体覆盖生成，不要手工编辑。默认路径相对仓库根，请从仓库根运行：

    python .github/skills/read-zzz-drive-disc/scripts/refresh_disc_presets.py
    python .github/skills/read-zzz-drive-disc/scripts/refresh_disc_presets.py --max-id 2600
"""

import argparse
import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

API = "https://act-api-takumi.mihoyo.com/hoyowiki/zzz/wapi/entry_page_v2?entry_page_id={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://baike.mihoyo.com/",
    "x-rpc-wiki_app": "zzz",
}
#: 默认输出。仓库根 ``data/`` 是唯一真实源。
OUTPUT = "data/drive-disc-presets.json"
#: 套装图标落地目录，与 ``images/agents`` ``images/weapons`` 平级。
IMAGES_DIR = "frontend/public/images/discs"

#: 仓库根。本脚本从 ``.github/skills/<skill>/scripts/`` 上溯四层到达。
REPO_ROOT = Path(__file__).resolve().parents[4]

#: 块级闭合标签与 ``<br>`` 先换成空格，否则相邻两段的文字会粘在一起。
_BLOCK_TAG = re.compile(r"(?i)</\s*(?:p|div|li|tr|table|h[1-6])\s*>|<br\s*/?>")
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def load_sync_presets():
    """导入 ``tools/sync_presets.py`` 以复用其 JSON 序列化与 id 校验。

    预设 JSON 的键序与缩进由该脚本单一定义，这里不另写一套。
    """
    if str(REPO_ROOT / "tools") not in sys.path:
        sys.path.insert(0, str(REPO_ROOT / "tools"))
    import sync_presets

    return sync_presets


def fetch(entry_page_id):
    for attempt in range(3):
        try:
            req = urllib.request.Request(API.format(entry_page_id), headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            time.sleep(0.6 * (attempt + 1))
    return None


def components(page):
    out = {}
    for module in page.get("modules") or []:
        for comp in module.get("components") or []:
            cid, data = comp.get("component_id"), comp.get("data")
            if not cid or not data:
                continue
            try:
                out.setdefault(cid, []).append(json.loads(data))
            except ValueError:
                pass
    return out


def plain(text):
    """剥 HTML、折叠空白。多段落在边界处留一个空格。"""
    text = _BLOCK_TAG.sub(" ", text or "")
    text = _TAG.sub("", text)
    return _WS.sub(" ", text).strip()


def is_disc(comps):
    return bool(comps.get("driver_disk"))


def set_effects(comps):
    """返回 ``(二件套, 四件套)`` 纯文本；找不到返回 ``None``。

    只认表头含「二件套」的表：同一页的「推荐角色」表表头不同，
    不会误取。取到的两列必须都非空，否则宁可跳过也不写半条数据。
    """
    for table in comps.get("double_col_table") or []:
        for block in table.get("tables") or []:
            if "二件套" not in (block.get("header") or []):
                continue
            for row in block.get("row") or []:
                if len(row) < 2:
                    continue
                two, four = plain(row[0]), plain(row[1])
                if two and four:
                    return two, four
    return None


def set_image(page, comps):
    """套装图标 URL：详情页头部图优先，回退频道列表图标。"""
    for info in comps.get("material_base_info") or []:
        if info.get("img"):
            return info["img"]
    return page.get("icon_url")


def parse(page):
    comps = components(page)
    if not is_disc(comps):
        return None
    effects = set_effects(comps)
    if not effects:
        return None
    entry_id = int(page.get("id"))
    return {
        "id": "ep-{}".format(entry_id),
        "name": page.get("name"),
        "source": "https://baike.mihoyo.com/zzz/wiki/content/{}/detail?mhy_presentation_style=fullscreen".format(entry_id),
        "setEffect2": effects[0],
        "setEffect4": effects[1],
        "image": "/images/discs/ep-{}.png".format(entry_id),
        "_image_path": "{}/ep-{}.png".format(IMAGES_DIR, entry_id),
        "_image_url": set_image(page, comps),
    }


def scan(max_id, workers):
    records, seen = [], 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for resp in pool.map(fetch, range(1, max_id + 1)):
            seen += 1
            if not resp or resp.get("retcode") != 0:
                continue
            page = (resp.get("data") or {}).get("page") or {}
            record = parse(page)
            if record:
                records.append(record)
            if seen % 250 == 0:
                print("scanned {} ids, {} sets".format(seen, len(records)), flush=True)
    records.sort(key=lambda item: int(item["id"][3:]))
    return records


def download_image(url, destination):
    """抓图并落盘；内容有变才写，返回是否发生了写入。"""
    if not url:
        return False
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = resp.read()
    except Exception as error:
        print("  image failed {}: {}".format(destination, error))
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.read_bytes() == payload:
        return False
    destination.write_bytes(payload)
    return True


def render(records):
    """序列化为规范化 JSON，并同步下载套装图标。"""
    sync_presets = load_sync_presets()
    presets = []
    for item in records:
        preset = {key: value for key, value in item.items() if not key.startswith("_")}
        # 下载落盘用仓库相对路径 _image_path；JSON 里的 image 是 /images/… URL，
        # 不能拿它拼落盘路径（pathlib 的绝对路径会吞掉前段的 REPO_ROOT）。
        downloaded = download_image(item["_image_url"], REPO_ROOT / item["_image_path"])
        preset["_downloaded"] = downloaded
        presets.append(preset)
    sync_presets.check_ids(presets, OUTPUT)
    downloaded = sum(1 for preset in presets if preset.pop("_downloaded"))
    return sync_presets.dump_json(presets), downloaded


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-id", type=int, default=2600)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--out", default=OUTPUT)
    args = parser.parse_args()

    records = scan(args.max_id, args.workers)
    content, downloaded = render(records)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8", newline="\n")
    print("sets found: {}".format(len(records)))
    print("images downloaded/updated: {}".format(downloaded))
    print("presets written: {} -> {}".format(len(records), args.out))


if __name__ == "__main__":
    main()
