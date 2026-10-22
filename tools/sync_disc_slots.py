"""从官方 HoYoLAB Wiki 抓取**驱动盘主词条与副词条池**，生成可校验的数据集。

为什么要有这个
--------------
驱动盘 1/2/3/4/5/6 号位的主词条数值、以及副词条池，此前**只存在于**
``backend/src/zzz_panel/core/options.py`` 的手写规则表里——**没有任何东西
校验它**。规则表写错一次，规则验证全绿，面板静默地算错。

（真实发生过：6 号位「冲击力」被写成 24%，官方是 **18%**；5 号位第 5 项被写成
通用「增伤」，官方是**属性伤害**。两次都是靠人工比对 Wiki 才发现的。）

这份数据集把官方口径**独立地**存一份，让
``backend/tests/test_options_json.py`` 能断言「规则表里的每个数值都能在官方
数据里找到对应」——下次写错，CI 会拦下。

数据从哪来
----------
同一个 WIKI 内容接口（``.github/skills/read-zzz-drive-disc/SKILL.md`` 同一通道）：

- ``driver_disk`` 组件的 ``disks_name`` / ``disks_desc``：6 个槽位，每个槽位是
  「选项名 + S/A/B 三档表」；
- ``rich_row_base_info`` 组件的 ``rich_text``：**副词条池**（10 项）。

**副词条的每档数值**（生命 112 / 攻击 19 / …）Wiki 上没有——它只给池子。
所以本数据集只固化**池子**，每档数值仍以规则表为准（并在文件里写明这一点）。

用法::

    python tools/sync_disc_slots.py            # 抓取并写回
    python tools/sync_disc_slots.py --check    # 只校验，不写
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "catalog" / "drive-disc-slots.json"

#: 驱动盘 Wiki 目录页（套装的分类入口）。
INDEX_URL = "https://baike.mihoyo.com/zzz/wiki/channel/map/2/46"

#: 内容接口的取数模板（entry_page_id 来自详情页 URL）。
API_URL = "https://act-api-takumi.mihoyo.com/hoyowiki/zzz/wapi/entry_page_v2?entry_page_id={id}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://baike.mihoyo.com/",
    "x-rpc-wiki_app": "zzz",
}

#: 抽样抓取的几个套装详情页——用来确认「槽位表在所有套装上完全一致」。
SAMPLE_ENTRY_IDS = (104, 151, 152, 153, 189)

#: ``<strong>选项名</strong>`` 紧跟一张 ``<table>``，表里是 S/A/B 三档。
OPTION_RE = re.compile(
    r"<strong>(?P<name>.*?)</strong>.*?<table.*?</table>", re.S
)
CELL_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
GRADE_RE = re.compile(r"([SAB])\s*级\s*[：:]\s*([\d.]+)\s*(%?)")
TAG_RE = re.compile(r"<[^>]+>")

#: 槽位名 -> 槽位号。
SLOT_RE = re.compile(r"([1-6])\s*号位")

#: Wiki 在槽位段首写的说明后缀（「「异常精通」为固定值数据」）。
NOTE_SUFFIX = "为固定值数据"

#: Wiki 的用词不统一：同一个属性在不同套装页上分别写作「异常掌控」与
#: 「异常掌握」。游戏内的规范名是**异常掌控**，这里统一到它，
#: 否则「槽位表在所有套装上一致」的校验会被用词差异误伤。
NAME_ALIASES = {
    "异常掌握": "异常掌控",
    "属性伤害加成": "属性伤害",
    "能量自动回复": "能量回复",
}


def fetch(entry_page_id: int) -> dict:
    request = urllib.request.Request(API_URL.format(id=entry_page_id), headers=HEADERS)
    with urllib.request.urlopen(request, timeout=40) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("retcode") != 0:
        raise ValueError(f"entry_page_id={entry_page_id} 返回 retcode={payload.get('retcode')}")
    return payload


def components(page: dict) -> list[dict]:
    """页面里的全部组件（``data`` 是**双重编码**的 JSON 字符串）。"""
    out: list[dict] = []
    for module in page.get("modules") or []:
        for component in module.get("components") or []:
            if not component.get("data"):
                continue
            try:
                out.append(
                    {
                        "component_id": component.get("component_id"),
                        "data": json.loads(component["data"]),
                    }
                )
            except (ValueError, TypeError):
                continue
    return out


def plain(text: str) -> str:
    return TAG_RE.sub("", text or "").strip()


def _normalize_name(name: str) -> str:
    """Wiki 的选项名 -> 规则表用的规范名。

    Wiki 与规则表的用词有三处差异：

    - 第一个选项带注记「（均为满级数据）」；
    - 百分比项写作「百分比攻击力」，规则表写作「攻击力」；
    - 「属性伤害加成（风、冰、火、电、物理、以太）」/「异常掌握」/「能量自动回复」
      在规则表里分别是「属性伤害」/「异常掌控」/「能量回复」。

    归一后两边同名，CI 才能直接对照。
    """
    name = re.sub(r"（[^）]*）|\([^)]*\)", "", name).strip()
    name = name.removeprefix("百分比")
    return NAME_ALIASES.get(name, name)


def parse_options(html_blob: str) -> list[dict]:
    """一段槽位 HTML -> 选项列表。

    Wiki 的槽位段落是「`<strong>选项名</strong>` + 一张 S/A/B 表」逐项排列。
    """
    options: list[dict] = []
    for match in OPTION_RE.finditer(html_blob):
        name = _normalize_name(plain(match.group("name")))
        if not name:
            continue
        values: dict[str, float] = {}
        percent = False
        for cell in CELL_RE.findall(match.group(0)):
            cell_match = GRADE_RE.search(plain(cell))
            if not cell_match:
                continue
            grade, number, unit = cell_match.groups()
            values[grade] = float(number)
            percent = percent or unit == "%"
        if not values:
            continue
        options.append(
            {
                "name": name,
                "kind": "pct" if percent else "flat",
                "values": values,
            }
        )
    return options


def parse_sub_stats(components_: list[dict]) -> list[str]:
    """副词条池（``rich_row_base_info`` 的 rich_text）。

    原文按 ``<p>`` 分行：

    ```
    副词条
    生命值 攻击力 防御力
    生命值百分比 攻击力百分比 防御力百分比
    穿透值 暴击率 暴击伤害 异常精通
    ```
    """
    for component in components_:
        if component["component_id"] != "rich_row_base_info":
            continue
        data = component["data"]
        if isinstance(data, str):
            data = json.loads(data)
        text = str(data.get("rich_text") or "")
        names: list[str] = []
        for line in re.findall(r"<p[^>]*>(.*?)</p>", text, re.S):
            line = plain(line).strip()
            if not line or line == "副词条":
                continue
            for token in re.split(r"\s+", line):
                token = token.strip()
                if token and token not in names:
                    names.append(token)
        return names
    return []


def build() -> dict[str, Any]:
    """抓取并汇总成数据集。"""
    per_set: dict[str, dict[str, Any]] = {}
    sub_stats: list[str] = []
    for entry_page_id in SAMPLE_ENTRY_IDS:
        page = fetch(entry_page_id)["data"]["page"]
        comps = components(page)
        driver = next((c for c in comps if c["component_id"] == "driver_disk"), None)
        if driver is None:
            continue
        data = driver["data"]
        if isinstance(data, str):
            data = json.loads(data)
        names = data.get("disks_name") or []
        descs = data.get("disks_desc") or []
        slots: dict[str, Any] = {}
        for slot_name, blob in zip(names, descs):
            slot_match = SLOT_RE.search(plain(slot_name))
            if not slot_match:
                continue
            slot = slot_match.group(1)
            slots[slot] = {"name": plain(slot_name), "options": parse_options(blob)}
        per_set[str(entry_page_id)] = {"name": page.get("name"), "slots": slots}
        if not sub_stats:
            sub_stats = parse_sub_stats(comps)

    # 槽位表应当在所有套装上完全一致——不一致就不敢把它当通用真源。
    reference = None
    for entry_page_id, entry in per_set.items():
        if reference is None:
            reference = entry
            continue
        if entry["slots"] != reference["slots"]:
            raise SystemExit(
                f"套装 {entry_page_id}（{entry['name']}）的槽位表与 {reference['name']} 不一致，"
                "先人工核对再生成"
            )

    payload = {
        "_generated": (
            "由 tools/sync_disc_slots.py 从官方 HoYoLAB Wiki 抓取生成，勿手改；"
            "规则表的真实源仍是 core/options.py，本数据集是它的**独立对照**。"
        ),
        "source": INDEX_URL,
        "api": "https://act-api-takumi.mihoyo.com/hoyowiki/zzz/wapi/entry_page_v2",
        "fetchedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "sampleEntryIds": list(SAMPLE_ENTRY_IDS),
        "slots": (reference or {}).get("slots", {}),
        "subStats": sub_stats,
        "notes": [
            "**副词条的每档数值（生命 112 / 攻击 19 / …）Wiki 上没有**——驱动盘页只给池子。"
            "本数据集固化的只是**池子**（10 项），每档数值仍以规则表为准。",
            "槽位表在抽样套装上逐字一致（脚本会校验，不一致直接报错）。",
        ],
    }
    return payload


def dump(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="只报告漂移，不写文件")
    args = parser.parse_args()

    payload = build()
    text = dump(payload)
    current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else None
    if current == text:
        print(f"  ok       {OUTPUT.name}")
        return 0
    if args.check:
        # 抓取时间戳每次都变，比对时不算它——它只是「什么时候抓的」，
        # 不影响内容是否漂移。
        if current is not None:
            old = json.loads(current)
            old.pop("fetchedAt", None)
            fresh = dict(payload)
            fresh.pop("fetchedAt", None)
            if old == fresh:
                print(f"  ok       {OUTPUT.name}（仅 fetchedAt 不同）")
                return 0
        print(f"  drift    {OUTPUT.name}")
        return 1
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"  updated  {OUTPUT.name}")
    print("next: python tools/sync_manifest.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
