#!/usr/bin/env python3
"""抓取绝区零官方 WIKI 的代理人攻略数据，输出结构化 JSON + 本地图片资源。

数据来源
--------
米游社绝区零 WIKI 的代理人详情页是 SPA（Nuxt 服务端渲染壳 + 客户端取数），
直接 BeautifulSoup 解析 HTML 只能拿到空壳。真正的内容走公开内容接口：

    https://act-api-takumi.mihoyo.com/hoyowiki/zzz/wapi/entry_page_v2?entry_page_id=<id>

返回体路径 ``data.page.modules[].components[]``，每项的 ``component_id`` 标识
区块类型，``data`` 是 JSON 字符串。本脚本按 component_id 抽取三类区块：

* ``role_base_info``    姓名 / 评级 / 属性 / 职业 / 立绘 / 自定义字段；等级图标从
                         bundle 的 fastcdn 映射下载（属性图标 WIKI 未公开，见
                         profile_icons 注释）
* ``role_talent``       两个组件：技能展示（6 个 tab：普攻/闪避/支援技/特殊技/
                         终结技/核心技，每 tab 含 icon 与招式列表——标题 + HTML
                         描述 + 1-16 级或 A-F 级成长数据）；晋升需求滑块（初始行 +
                         满级行合并出 60 级基础面板）
* ``double_col_table``  影画表（表头「影画名称 / 效果展示」，LEVEL1..6 行）

抽取到的 HTML 描述（内含按钮图标 span、颜色 span、技能名 [括号] 文本）由
BeautifulSoup 清洗为可读纯文本；六大类技能与影画文本写入 JSON。

图片落地遵循仓库唯一约定——**唯一图片根是 `frontend/public/images/`**，
JSON 里一律写 `/images/…` URL（禁止页相对 `assets/…`），详见
``profile_icons`` / ``local_assets`` / ``cinema_backdrops`` 的注释。

用法（仓库根；默认抓叶瞬光写入 strategy/ye-shunguang/）::

    python .github/skills/agent-strategy/scripts/scrape_agent_guide.py
    python .github/skills/agent-strategy/scripts/scrape_agent_guide.py --entry-page-id 1109 \
        --slug <slug> --output strategy/<slug>/data/<slug>.json
    python .github/skills/agent-strategy/scripts/scrape_agent_guide.py --no-images   # 不下载图片

共享图标（技能 / 等级 / 职业 / 属性）直接落 ``frontend/public/images/`` 下对应
子目录并写 ``/images/…`` URL；每代理人独有的立绘 / 称号 / 影画背景落
``--assets-dir``（默认 ``frontend/public/images/strategy/<slug>/``）。
"""

from __future__ import annotations

import argparse
import datetime
import html
import json
import re
import sys

# 管道输出固定 UTF-8：Windows 上管道默认用系统代码页（本机 GBK），
# 父工具按 UTF-8 读会抛 UnicodeDecodeError 或读出乱码。控制台输出保持
# 系统代码页，否则用户在自己的终端里会看到乱码。
if hasattr(sys.stdout, "reconfigure") and not sys.stdout.isatty():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

#: 仓库根 ``tools/`` 在 sys.path 上，才能 import ``data_paths``（数据集路径的
#: 唯一真源是 ``data/manifest.json``）。本脚本从
#: ``.github/skills/agent-strategy/scripts/`` 上溯到仓库根。
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "tools"))

API = "https://act-api-takumi.mihoyo.com/hoyowiki/zzz/wapi/entry_page_v2?entry_page_id={}"
#: 与仓库既有抓取脚本（.github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py）
#: 一致的请求头。缺了 Referer / x-rpc-wiki_app 会返回 403。
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://baike.mihoyo.com/",
    "x-rpc-wiki_app": "zzz",
}

#: ``role_base_info.role_profession`` slug -> 官方职业文案。
PROFESSION_TAGS = {
    "strike": "强攻",
    "pierce": "击破",
    "abnormal": "异常",
    "support": "支援",
    "guard": "防护",
    "rupture": "命破",
    "armero": "锋御",
}

#: ``role_base_info.role_attribute`` slug -> 官方属性文案。electric 官方作「电」，
#: honed_edge 官方作「凛刃」；未登记的 slug 直接报错，不猜。
ATTRIBUTE_LABELS = {
    "electric": "电",
    "ether": "以太",
    "fire": "火",
    "ice": "冰",
    "physical": "物理",
    "frost": "烈霜",
    "auricink": "玄墨",
    "honed_edge": "凛刃",
    "wind": "风",
    "Lumiflux": "流明",
}

#: WIKI 技能 tab -> (本项目的类别 key, 展示名)。
#:
#: 六大类按「普攻/闪避/支援/特殊/连携/核心技」划分；WIKI 把连携技与终结技合并在
#: 同一个「终结技」tab 下（该 tab 的招式同时包含「连携技：…」与「终结技：…」），
#: 因此 tab「终结技」整体映射为类别「连携技」，展示名保持「连携技」。
SKILL_TABS: dict[str, tuple[str, str]] = {
    "普攻": ("basic", "普通攻击"),
    "普通攻击": ("basic", "普通攻击"),
    "闪避": ("dodge", "闪避"),
    "支援技": ("assist", "支援技"),
    "特殊技": ("special", "特殊技"),
    "终结技": ("chain", "连携技"),
    "连携技": ("chain", "连携技"),
    "核心技": ("core", "核心技"),
}

def _find_repo_root() -> Path:
    """Walk up from this file until pyproject.toml is found (robust to nesting)."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise RuntimeError(f"Cannot find pyproject.toml above {current}")
REPO_ROOT = _find_repo_root()
#: 唯一图片根。所有引用（含 data/*.json 与攻略 JSON）一律写成 /images/… URL。
IMAGES_ROOT = REPO_ROOT / "frontend" / "public" / "images"
DEFAULT_SLUG = "ye-shunguang"
DEFAULT_OUTPUT = REPO_ROOT / "strategy" / DEFAULT_SLUG / "data" / f"{DEFAULT_SLUG}.json"

#: WIKI 职业 slug -> 仓库共享图标文件名（小写 ASCII slug，如 strike -> attack.webp）
PROFESSION_ICON_MAP = {
    "strike": "attack",
    "pierce": "stun",
    "abnormal": "anomaly",
    "support": "support",
    "guard": "defense",
    "rupture": "rupture",
    "armero": "armorer",
}

#: WIKI 属性 slug -> 仓库共享图标文件名（小写 ASCII slug，如 physical -> physical.webp）
ATTRIBUTE_ICON_MAP = {
    "electric": "electric",
    "ether": "ether",
    "fire": "fire",
    "ice": "ice",
    "physical": "physical",
    "frost": "frost",
    "auricink": "auric-ink",
    "honed_edge": "honed-edge",
    "wind": "wind",
    "Lumiflux": "lumiflux",
}

#: WIKI 代理人页前端 bundle（/zzz/wiki/_nuxt/c987913.js）中渲染等级图标的
#: vp 映射：{infinite, s, a, b} -> fastcdn.mihoyo.com 静态资源。
GRADE_ICON_URLS = {
    "s": "https://fastcdn.mihoyo.com/static-resource-v2/2024/04/24/4d5953cc9b8c37437d4ecce305f554e0_3293757479950997418.png",
    "a": "https://fastcdn.mihoyo.com/static-resource-v2/2024/04/10/3e564345fb8ee230beabffdc57944873_5552872158323865375.png",
    "b": "https://fastcdn.mihoyo.com/static-resource-v2/2024/04/24/6170b0fced6864c1d019b54c00ac2ed1_5648623008710121650.png",
}


class ScrapeError(RuntimeError):
    """抓取或解析失败，带可操作的错误信息。"""


# ---------------------------------------------------------------- HTTP


def fetch_entry_page(entry_page_id: int, timeout: float, retries: int = 3) -> dict:
    """拉取 entry_page_v2，返回 ``data.page``。失败重试，最终抛 ScrapeError。"""
    url = API.format(entry_page_id)
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=timeout)
            response.raise_for_status()
            payload = response.json()
            page = payload.get("data", {}).get("page")
            if not page:
                raise ScrapeError(f"entry_page_id={entry_page_id} 返回体中没有 page（可能 id 不存在）")
            return page
        except Exception as error:  # noqa: BLE001 - 统一转成 ScrapeError 并重试
            last_error = error
            if attempt < retries:
                time.sleep(0.6 * attempt)
    raise ScrapeError(f"抓取 {url} 失败：{last_error}") from last_error


# ---------------------------------------------------------------- HTML -> text


def html_to_text(html: str) -> str:
    """把 WIKI 的富文本 HTML 清洗为可读纯文本。

    规则：
    * 删除 ``span.custom-image-view``——混在正文里的手柄按键图标，纯装饰；
    * ``<br>`` 与块级元素结尾转为换行，保留原文分段；
    * 其余标签（颜色 span、strong、a 等）只取文本，保留技能名的 [方括号] 内容；
    * 压缩连续空行、去掉行尾空白。
    """
    if not html or not html.strip():
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for icon in soup.select("span.custom-image-view"):
        icon.decompose()
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for block in soup.find_all(["p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"]):
        block.append("\n")
    text = soup.get_text()
    lines = [line.rstrip() for line in text.splitlines()]
    paragraphs: list[str] = []
    blank = 0
    for line in lines:
        if line.strip():
            paragraphs.append(line.strip())
            blank = 0
        else:
            blank += 1
            if blank == 1 and paragraphs:
                paragraphs.append("")
    while paragraphs and not paragraphs[0]:
        paragraphs.pop(0)
    while paragraphs and not paragraphs[-1]:
        paragraphs.pop()
    return "\n".join(paragraphs)


# ---------------------------------------------------------------- components


def iter_components(page: dict):
    """遍历页面全部组件，产出 (component_id, data_dict)。"""
    for module in page.get("modules") or []:
        for component in module.get("components") or []:
            raw = component.get("data")
            if not raw:
                continue
            try:
                data = json.loads(raw) if isinstance(raw, str) else raw
            except (ValueError, TypeError):
                continue
            if isinstance(data, dict):
                yield component.get("component_id"), data


def find_components(page: dict, component_id: str) -> list[dict]:
    """按 component_id 取全部同名组件（技能展示与晋升需求都是 role_talent）。"""
    return [data for cid, data in iter_components(page) if cid == component_id]


def parse_growth(growth: object) -> list[dict]:
    """解析招式的 1-16 级成长数据。

    WIKI 结构：``[{name: '1', children: [{name: '伤害倍率', row: [[html]]}], materials: []}, ...]``。
    输出 ``[{level, groups: [{name, rows: [text, ...]}]}]``；核心技的 level 是 A-F。
    WIKI 对无专有名称的分组统一写「分类N」，这里归一为「效果」。
    成长表格行尾常带 WIKI 内部链接残留 ``[详情]``，一并剥掉。
    """
    if not isinstance(growth, list):
        return []
    levels: list[dict] = []
    for entry in growth:
        if not isinstance(entry, dict):
            continue
        groups: list[dict] = []
        for group in entry.get("children") or []:
            rows: list[str] = []
            for row in group.get("row") or []:
                if not isinstance(row, list):
                    continue
                for cell in row:
                    text = html_to_text(cell) if isinstance(cell, str) else str(cell)
                    text = re.sub(r"\s*\[详情\]", "", text)
                    if text:
                        rows.append(text)
            group_name = html_to_text(group.get("name") or "")
            if re.fullmatch(r"分类\d+", group_name):
                group_name = "效果"
            groups.append({"name": group_name, "rows": rows})
        levels.append({"level": str(entry.get("name") or ""), "groups": groups})
    return levels


#: 匹配「XX提升N点 / N%」中的属性名与数值。属性名不含标点与换行，
#: 保证从「…效果，暴击率提升15%」里取到的是「暴击率」而不是整句。
_STAT_PATTERN = r"([^，。；：、（）\s\[\]]+?)提升([\d.]+)(点|%)"


def core_max_text(text: str, growth: list[dict]) -> str:
    """把核心技描述里的「初始数据」改写为满级（A-F 全满）数值。

    WIKI 的 desc 固定展示 A 级（初始）数值，各级增量写在 growth 里
    （如「暴击率提升4.8%」「基础攻击力提升25点」）。满级数值 = 初值 +
    各级增量之和；初始句中没有、但升级会提升的属性（如基础攻击力）
    补进句中。只在含「此处数据为初始数据」的那一句内改写，句子外的
    数值一概不动；找不到该句式时原样返回，其他代理人改版可安全降级。
    """
    if "此处数据为初始数据" not in text or not isinstance(growth, list):
        return text

    totals: dict[str, list] = {}
    for entry in growth:
        for group in entry.get("groups") or []:
            for row in group.get("rows") or []:
                for line in row.split("\n"):
                    match = re.fullmatch(_STAT_PATTERN, line.strip())
                    if not match:
                        continue
                    stat, value, unit = match.group(1), float(match.group(2)), match.group(3)
                    totals.setdefault(stat, [0.0, unit])[0] += value
    if not totals:
        return text

    def fmt(value: float) -> str:
        return str(int(value)) if float(value).is_integer() else f"{value:g}"

    def bump(match: re.Match) -> str:
        stat, value, unit = match.group(1), match.group(2), match.group(3)
        if stat not in totals:
            return match.group(0)
        return f"{stat}提升{fmt(float(value) + totals[stat][0])}{unit}"

    head, sep, tail = text.partition("（此处数据为初始数据）")
    bumped = re.sub(_STAT_PATTERN, bump, head)
    extras = [
        f"{stat}提升{fmt(total[0])}{total[1]}"
        for stat, total in totals.items()
        if stat not in bumped
    ]
    bumped = bumped.rstrip("。")
    if extras:
        bumped += "，" + "，".join(extras)
    bumped += "。"
    return f"{bumped}{sep.replace('初始数据', '满级数据')}{tail}"


def core_detail_from_growth(growth: object) -> tuple[str, str]:
    """从核心技的成长表里抽取招式描述与标题（WIKI 的另一种结构）。

    部分代理人（如克拉蕾）的核心技 tab 子项只有成长表、没有 title/desc；
    完整描述以 ``<span data-type="详情" data-name="<escaped html>">`` 的形式挂在
    每一 rank 的行上。这里反转义为纯文本，并取**最后一段（F 级，满级）**的数值——
    A-F 各段的加成数值是递增的（如暴击率 17.5% → 30%），取首段会展示成「只升了一级」。
    标题取行内的「核心被动：XXX」。

    返回 ``(title, text)``；取不到时两者均为空串，调用方按原逻辑跳过。
    """
    title, text = "", ""
    for cell_html in _growth_cells(growth):
        match = re.search(r'data-name="([^"]*)"', cell_html)
        if not match:
            continue
        plain = html_to_text(html.unescape(match.group(1)))
        if plain:
            text = plain  # 后写覆盖先写：最终留下最后一段（满级）的数值
            name = re.search(r"核心被动：([^\]\[，。；\s]+)", html_to_text(cell_html))
            title = f"核心被动：{name.group(1)}" if name else title
    return title, text


# ---------------------------------------------------------------- 技能文本口径

#: 成长行里的「标签：数值」（如「失衡值提升：120%」）。
_GROWTH_VALUE_RE = re.compile(r"^([^：:]+)[：:]\s*([\d.]+%?)$")

#: 核心技正文首行的标题（「核心被动：致命私酿」/「核心技：热夜初拥」）。
_CORE_TITLE_RE = re.compile(r"^(核心技|核心被动)\s*[:：]\s*(.+)$")

#: 额外能力 / 额外被动段的开头。
_EXTRA_ABILITY_RE = re.compile(r"^(额外能力|额外被动)\s*[:：]")


def _growth_cells(growth: object) -> list[str]:
    """展开成长表所有行里的 HTML 单元格。"""
    cells: list[str] = []
    if not isinstance(growth, list):
        return cells
    for level in growth:
        if not isinstance(level, dict):
            continue
        for group in level.get("children") or []:
            if not isinstance(group, dict):
                continue
            for row in group.get("row") or []:
                if isinstance(row, list):
                    cells.extend(cell for cell in row if isinstance(cell, str))
    return cells


def growth_detail_text(growth: object) -> str:
    """取成长表**最后一级**的「详情」span 文本 = 该招式的**满级**描述。

    WIKI 的 ``desc`` 固定展示初始数值（核心技 A 级、其余 1 级），完整描述挂在每一
    rank 行内的 ``<span data-type="详情" data-name="…">`` 上；取最后一段即满级正文
    （洛克茜：攻击力最多 960 点 / 暴伤 40%；希希芙：无视防御 6% 而非初始的 3%）。
    """
    text = ""
    for cell_html in _growth_cells(growth):
        match = re.search(r'data-name="([^"]*)"', cell_html)
        if not match:
            continue
        plain = html_to_text(html.unescape(match.group(1)))
        if plain:
            text = plain  # 后写覆盖先写 → 最后一段（满级）
    return text


def growth_last_values(growth: object) -> dict[str, str]:
    """成长表**最后一级**各行的「标签 → 数值」（如 失衡值提升 → 120%）。

    非核心技的描述标注「（此处数据为初始数据）」，其满级数值就在同招式成长表最后
    一级的同名行里。核心技的成长行是核心加成（「暴击率提升4.8%」这类），格式不同，
    不走这条路（核心技用「详情」span）。
    """
    values: dict[str, str] = {}
    for cell_html in _growth_cells(growth):
        plain = html_to_text(cell_html)
        match = _GROWTH_VALUE_RE.match(plain)
        if match:
            values[match.group(1).strip()] = match.group(2)
    return values


def split_extra_ability(text: str) -> tuple[str, str, str]:
    """把「额外能力：」「额外被动：」段从正文里切出来。

    WIKI 的核心技 desc 里，核心被动正文与额外能力段是同一段富文本，段间空行分隔。
    返回 ``(主体正文, 额外能力标题, 额外能力正文)``；没有额外能力段时后两者为空串。
    """
    lines = text.split("\n")
    for index, line in enumerate(lines):
        stripped = line.strip()
        if _EXTRA_ABILITY_RE.match(stripped):
            body = "\n".join(lines[:index]).rstrip()
            rest = "\n".join(lines[index + 1:]).strip()
            return body, stripped, rest
    return text, "", ""


def strip_core_title_line(text: str) -> str:
    """去掉正文首行的「核心被动：XXX」/「核心技：XXX」标题行（已单独进 title）。"""
    lines = text.split("\n")
    if lines and _CORE_TITLE_RE.match(lines[0].strip()):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines)


def normalize_core_title(child_title: str, desc_text: str, detail_text: str) -> str:
    """核心技标题统一成「核心技：<名称>」（与 roxy 页排版一致）。"""
    for source in (desc_text, detail_text):
        first = source.split("\n", 1)[0].strip() if source else ""
        match = _CORE_TITLE_RE.match(first)
        if match:
            return f"核心技：{match.group(2).strip()}"
    if child_title and child_title.strip() not in ("核心技", "核心被动"):
        return child_title.strip()
    return "核心技"


def rewrite_level_values(text: str, values: dict[str, str]) -> tuple[str, bool]:
    """把「（此处数据为初始数据）」句里的数值换成成长表最后一级的满级值。

    只改写显式标注了初始数据的那一句；句外的数值一概不动。数值换不到时原样返回
    （宁可保留 WIKI 的初始标注，也不产出无依据的数字）。
    """
    if "此处数据为初始数据" not in text or not values:
        return text, False
    head, sep, tail = text.partition("（此处数据为初始数据）")
    changed = False
    for label, value in values.items():
        pattern = re.compile(rf"({re.escape(label)}\s*)(\d+(?:\.\d+)?%)")

        def repl(match: re.Match, value: str = value) -> str:
            return match.group(1) + value

        head, count = pattern.subn(repl, head)
        changed = changed or count > 0
    if not changed:
        return text, False
    return f"{head}{sep.replace('初始数据', '满级数据')}{tail}", True


def parse_skills(page: dict) -> list[dict]:
    """解析六大类技能。

    含两个 role_talent 组件：技能展示（6 tab）与晋升需求（1 tab「总计」）。
    按 SKILL_TABS 的 tab 名匹配，缺失任一必备 tab 即报错并列出实际 tab，
    避免官方改版后静默产出半份数据。
    """
    talents = [t for t in find_components(page, "role_talent") if t.get("list")]
    # 官方偶尔在 tab 名里插空格（席德的「闪 避」），匹配前统一去掉空白。
    normalized_tabs = {re.sub(r"\s+", "", tab): (key, name) for tab, (key, name) in SKILL_TABS.items()}
    skill_lists = [t["list"] for t in talents if any(re.sub(r"\s+", "", item.get("tab_name") or "") in normalized_tabs for item in t["list"])]
    if not skill_lists:
        raise ScrapeError("页面中没有技能展示区块（role_talent）")
    skill_list = skill_lists[0]
    found_tabs = [re.sub(r"\s+", "", item.get("tab_name") or "") for item in skill_list]
    # 把实际出现的 tab 映射到 skill key，校验 6 个必需 key（basic/dodge/assist/special/chain/core）
    # 是否齐全，而不逐个要求别名都出现（官方不同代理人页 tab 写法不一，如“普攻”/“普通攻击”）。
    found_keys = {normalized_tabs[tab][0] for tab in found_tabs if tab in normalized_tabs}
    required_keys = {key for key, _ in SKILL_TABS.values()}
    missing_keys = required_keys - found_keys
    if missing_keys:
        missing_tabs = [tab for tab, (key, _) in SKILL_TABS.items() if key in missing_keys]
        raise ScrapeError(f"技能 tab 缺失 {missing_tabs}；实际 tab 为 {found_tabs}")

    skills: list[dict] = []
    for item in skill_list:
        tab = item.get("tab_name")
        key, name = normalized_tabs[re.sub(r"\s+", "", tab)]
        moves: list[dict] = []
        skipped = 0
        is_core = tab == "核心技"
        for child in item.get("children") or []:
            title = (child.get("title") or "").strip()
            desc_text = html_to_text(child.get("desc") or "")
            growth = child.get("growth") or []

            if is_core:
                # 核心技正文取「详情」span（满级）；额外能力从 desc 切出单独成条。
                detail_text = growth_detail_text(growth)
                body = detail_text or desc_text
                if not body:
                    # 变体条目：只有标题、无描述与成长，是页面内跳转锚点（照旧跳过）。
                    skipped += 1
                    continue
                body, extra_title, extra_text = split_extra_ability(body)
                if not extra_title:
                    _, extra_title, extra_text = split_extra_ability(desc_text)
                body = strip_core_title_line(body)
                if detail_text:
                    # 详情就是满级文本，WIKI 自带的「初始数据」标记按满级口径翻正。
                    body = body.replace("（此处数据为初始数据）", "（此处数据为满级数据）")
                else:
                    # 降级路径：desc 只有初始数值，用成长增量改写成满级。
                    body = core_max_text(body, parse_growth(growth))
                move = {
                    "title": normalize_core_title(title, desc_text, detail_text),
                    "text": body,
                }
                parsed_growth = parse_growth(growth)
                if parsed_growth:
                    move["growth"] = parsed_growth
                moves.append(move)
                if extra_title:
                    moves.append({"title": extra_title, "text": extra_text})
                continue

            if not title or not desc_text:
                # 变体条目：只有标题、无描述与成长（照旧跳过）。
                skipped += 1
                continue
            # 非核心技：desc 即全部信息；把标注为初始数据的句子换成满级数值。
            text, _ = rewrite_level_values(desc_text, growth_last_values(growth))
            move = {"title": title, "text": text}
            parsed_growth = parse_growth(growth)
            if parsed_growth:
                move["growth"] = parsed_growth
            moves.append(move)
        skills.append(
            {
                "key": key,
                "name": name,
                "wikiTab": tab,
                "icon": item.get("icon") or "",
                "moves": moves,
                "_skippedVariants": skipped,
            }
        )
    return skills


def parse_cinemas(page: dict) -> list[dict]:
    """解析影画表（double_col_table，表头「影画名称 / 效果展示」）。"""
    rows: list[list[str]] = []
    for table_component in find_components(page, "double_col_table"):
        for table in table_component.get("tables") or []:
            header = table.get("header") or []
            if not any("影画" in str(cell) for cell in header):
                continue
            rows = table.get("row") or []
            break
        if rows:
            break
    cinemas: list[dict] = []
    for row in rows:
        if len(row) < 2:
            continue
        name_text = html_to_text(row[0])
        match = re.search(r"LEVEL\s*(\d+)", name_text, re.IGNORECASE)
        if not match:
            continue  # 末行「特写」等非影画行
        level = int(match.group(1))
        cinema_name = name_text[match.end():].strip()
        effect = html_to_text(row[1])
        if effect:
            cinemas.append({"level": level, "name": cinema_name, "text": effect})
    cinemas.sort(key=lambda cinema: cinema["level"])
    return cinemas


def parse_cinema_showcases(page: dict) -> dict[str, str]:
    """提取「影画展示1/2/3」原图 URL（map_desc 组件，按 tab_name 索引）。"""
    showcases: dict[str, str] = {}
    for component_id, data in iter_components(page):
        if component_id != "map_desc":
            continue
        for item in data.get("list") or []:
            tab = item.get("tab_name") or ""
            image = item.get("image") or ""
            if tab.startswith("影画展示") and image:
                showcases[tab] = image
    return showcases


def cinema_backdrops(page: dict, cinemas: list[dict], args) -> dict:
    """按命数下载影画展示图作卡片背景：1-3 命用「影画展示2」，4-6 命用「影画展示3」。

    每代理人独有的背景图落 ``--assets-dir``，写
    ``/images/strategy/<slug>/cinema-N.webp``。返回 ``{level: {image, imageRemote}}``；
    下载失败的等级只保留远程 URL。
    """
    if not cinemas or args.no_images:
        return {}
    showcases = parse_cinema_showcases(page)
    backdrops: dict[str, dict] = {}
    for cinema in cinemas:
        level = cinema.get("level")
        # 展示图按「影画展示N」的末位数字命名：cinema-2.webp / cinema-3.webp
        tab = "影画展示2" if level <= 3 else "影画展示3"
        url = showcases.get(tab)
        if not url:
            continue
        local_name = f"cinema-{tab[-1]}.webp"
        entry = {"image": "", "imageRemote": url}
        if download_image(url, args.assets_dir / local_name, args.timeout):
            entry["image"] = f"{args.strategy_url}/{local_name}"
        backdrops[str(level)] = entry
    return backdrops


#: 晋升需求滑块里基础字段的展示顺序。表内未出现的字段（如命破代理人的
#: 贯穿力 / 闪能自动累积）按原出现顺序附在后面，不丢弃。
BASE_PANEL_FIELDS = (
    "生命值",
    "攻击力",
    "防御力",
    "冲击力",
    "暴击率",
    "暴击伤害",
    "异常掌控",
    "异常精通",
    "穿透率",
    "能量自动回复",
)

#: 满级行的字段名比初始行短（缺「值 / 力」后缀）。合并是按标签文本做键的，
#: 不先归一成同一键，满级值就覆盖不了初始值，而会被当成额外字段追加下去——
#: 基础面板于是同时列出初始行与满级行的生命 / 攻击 / 防御（柚叶踩过）。
#: 「生命力」是希希芙页面满级行的写法（生命值的另一种标签），同样归一。
BASE_PANEL_ALIASES = {
    "生命": "生命值",
    "生命力": "生命值",
    "攻击": "攻击力",
    "防御": "防御力",
}


def num(value) -> object:
    """整值收敛为 int，避免 JSON 里出现 7673.0 这类字面量。

    注意必须先转 float 再判整：WIKI 有些页面写作「5.0%」而非「5%」，
    直接 ``int("5.0")`` 会抛 ValueError。
    """
    parsed = float(value)
    return int(parsed) if parsed.is_integer() else parsed


def parse_base_panel(page: dict) -> list[dict]:
    """解析晋升需求滑块，产出 60 级（0 突破）基础面板。

    WIKI 把基础数据放在 role_talent（晋升需求）的滑块里：初始行给全量字段，
    满级行只给随晋升变化的生命 / 攻击 / 防御，逐字段用满级覆盖初始即为 60 级
    面板——与仓库 ``data/catalog/agents.json`` 的 ``base`` 同源同值。
    满级行的短字段名先经 ``BASE_PANEL_ALIASES`` 归一，否则覆盖不生效。
    输出 ``[{label, value, unit}]``，``unit`` 为 "%" 或空串。
    """
    stats: dict[str, dict] = {}
    for talent in find_components(page, "role_talent"):
        for item in talent.get("list") or []:
            for child in item.get("children") or []:
                if "滑块" not in (child.get("desc") or ""):
                    continue
                for entry in child.get("growth") or []:
                    if entry.get("name") not in ("初始", "满级"):
                        continue
                    for group in entry.get("children") or []:
                        for row in group.get("row") or []:
                            if not isinstance(row, list):
                                continue
                            for cell in row:
                                for line in html_to_text(cell).split("\n"):
                                    match = re.fullmatch(r"(.+?)[：:]\s*([\d.]+)(%?)", line.strip())
                                    if match:
                                        label = BASE_PANEL_ALIASES.get(match.group(1), match.group(1))
                                        stats[label] = {
                                            "label": label,
                                            "value": num(match.group(2)),
                                            "unit": match.group(3),
                                        }
    if not stats:
        raise ScrapeError("晋升需求滑块中没有基础数据（role_talent 结构可能已改版）")
    ordered = [stats[label] for label in BASE_PANEL_FIELDS if label in stats]
    ordered += [item for label, item in stats.items() if label not in BASE_PANEL_FIELDS]
    return ordered


#: 基础面板的字段名 -> 代理人预设 ``base`` 的键。用于把抓到的面板与预设对照。
_PANEL_LABEL_TO_BASE_KEY = {
    "生命值": "hp",
    "攻击力": "atk",
    "防御力": "def",
    "冲击力": "impact",
    "暴击率": "cr",
    "暴击伤害": "cd",
    "异常掌控": "ac",
    "异常精通": "am",
    "穿透率": "pr",
    "能量自动回复": "er",
    "锐能自动累积": "er",
}


def check_base_panel_against_preset(panel: list[dict], agent_id: str) -> None:
    """把抓到的面板与代理人预设对照，不一致就告警。

    基础面板的**唯一真实源是预设**（``data/catalog/agents.json``），攻略 JSON
    不再存这份数据。但抓取脚本仍然解析滑块——它是独立的数据来源，两边对不上
    就说明 Wiki 变了而预设没跟上（或反过来）。此时告警而不是失败：预设可能
    已经是人工核对过的正确值。
    """
    preset = _find_agent_preset(agent_id)
    if preset is None:
        return
    base = preset.get("base") or {}
    extra = preset.get("baseExtra") or {}
    for field in panel:
        label = field["label"]
        key = _PANEL_LABEL_TO_BASE_KEY.get(label)
        if key is not None:
            expected = base.get(key)
        elif label == "贯穿力":
            expected = extra.get("penforce")
        elif label == "闪能自动累积":
            expected = extra.get("energyAccumulation")
        else:
            continue
        if expected is None or float(expected) != float(field["value"]):
            print(
                f"  ! 基础面板与预设不一致：{label} 抓到 {field['value']}，"
                f"预设 {expected}（{agent_id}）"
            )


def _find_agent_preset(agent_id: str) -> dict | None:
    """按 id 找代理人预设。找不到就返回 None（不阻断抓取）。"""
    try:
        from data_paths import dataset_path
    except ImportError:
        return None
    try:
        presets = json.loads(dataset_path("agents").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for preset in presets:
        if preset.get("id") == agent_id:
            return preset
    return None


def parse_profile(page: dict) -> dict:
    """解析基础信息：姓名 / 属性 / 职业 / 评级 / 称号 / 自定义字段 / 简介。"""
    base = find_components(page, "role_base_info")
    if not base:
        raise ScrapeError("页面中没有 role_base_info（不是代理人详情页？）")
    info = base[0]
    name = (info.get("name") or "").strip()
    if not name:
        raise ScrapeError("role_base_info 缺少姓名")
    attribute = ATTRIBUTE_LABELS.get(info.get("role_attribute"))
    if attribute is None:
        raise ScrapeError(f"未登记的属性 slug：{info.get('role_attribute')!r}（请在 ATTRIBUTE_LABELS 中补充）")
    role_tag = PROFESSION_TAGS.get(info.get("role_profession"), "")
    profile = {
        "name": name,
        "attribute": attribute,
        "roleTag": role_tag,
        "grade": (info.get("grade") or "").strip(),
        "factionTitle": (info.get("addition_text") or "").strip(),
        "customFields": [
            {"key": str(item.get("key") or ""), "value": str(item.get("value") or "")}
            for item in info.get("custom_field") or []
            if isinstance(item, dict)
        ],
        "intro": "",
    }
    for component in find_components(page, "rich_row_base_info"):
        intro = html_to_text(component.get("rich_text") or "")
        if intro:
            profile["intro"] = intro
            break
    return profile


# ---------------------------------------------------------------- assets


def to_webp(payload: bytes) -> bytes:
    """把 PNG/JPEG 载荷转成 webp 字节。

    仓库图片统一 webp（见 ``tools/images_to_webp.py``）。没装 Pillow 时原样透传，
    浏览器会按内容嗅探渲染，只是体积不省。
    """
    try:
        from PIL import Image
    except ImportError:
        return payload
    import io

    image = Image.open(io.BytesIO(payload))
    image.load()
    if image.mode not in ("RGBA", "RGB"):
        image = image.convert("RGBA")
    buffer = io.BytesIO()
    image.save(buffer, "WEBP", quality=90, method=6)
    return buffer.getvalue()


def download_image(url: str, destination: Path, timeout: float, skip_if_exists: bool = False) -> bool:
    """下载单张图片；失败返回 False（调用方保留远程 URL 兜底）。

    ``skip_if_exists=True`` 用于全代理人共享的图标（技能 / 等级）：磁盘上已有
    同路径文件即视为就绪，不再重复请求 CDN。

    目标是 ``.webp`` 时会把下载到的 PNG/JPEG 转码成 webp，保持仓库图片格式统一。
    """
    if not url:
        return False
    if skip_if_exists and destination.is_file():
        return True
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = response.content
        if destination.suffix.lower() == ".webp":
            payload = to_webp(payload)
        destination.write_bytes(payload)
        return True
    except Exception as error:  # noqa: BLE001 - 单张图片失败不阻断整体
        print(f"  ! 图片下载失败，将保留远程 URL：{url}（{error}）", file=sys.stderr)
        return False


def local_assets(profile: dict, skills: list[dict], page: dict, args) -> dict:
    """下载立绘与技能图标，返回本地 URL 与远程兜底 URL。

    - 头像：不再单独下载——仓库 ``images/agents/<agentId>.webp`` 已存在（与主应用
      计算器 cascader 同源），存在才写该 URL；
    - 立绘：每名代理人独有，落 ``--assets-dir``，写
      ``/images/strategy/<slug>/tachie.webp``；
    - 六张技能图标是全代理人共享资产，落 ``images/skills/<key>.webp``，
      已存在则跳过下载。
    本地文件缺失时对应字段留空、保留 ``*Remote`` 远程兜底，行为不变。
    """
    base_info = find_components(page, "role_base_info")[0]
    avatar_url = page.get("icon_url") or ""
    tachie_url = base_info.get("tachie_pc") or ""
    agent_id = f"ep-{args.entry_page_id}"

    assets: dict = {}
    if args.no_images:
        assets["avatarRemote"] = avatar_url
        assets["tachieRemote"] = tachie_url
    else:
        avatar_file = IMAGES_ROOT / "agents" / f"{agent_id}.webp"
        if avatar_file.is_file():
            assets["avatar"] = f"/images/agents/{agent_id}.webp"
        assets["avatarRemote"] = avatar_url
        if download_image(tachie_url, args.assets_dir / "tachie.webp", args.timeout):
            assets["tachie"] = f"{args.strategy_url}/tachie.webp"
        assets["tachieRemote"] = tachie_url

    for skill in skills:
        if args.no_images:
            continue
        icon_url = skill.pop("icon")
        local = f"/images/skills/{skill['key']}.webp"
        if download_image(icon_url, IMAGES_ROOT / "skills" / f"{skill['key']}.webp", args.timeout, skip_if_exists=True):
            skill["icon"] = local
        skill["iconRemote"] = icon_url
    for skill in skills:
        skill.pop("_skippedVariants", None)
    return assets


def profile_icons(profile: dict, page: dict, args) -> dict:
    """生成姓名后的几枚小图标：属性、职业、等级、称号（虚狩专属）。

    - 职业图标：全代理人共享，直接引用仓库职业图标集
      ``images/icons/<role_profession>.webp``，不再逐代理人复制；
    - 等级图标：WIKI 代理人页 bundle 的 vp 映射（fastcdn 静态资源），按 grade 下载到
      ``images/grades/<grade>.webp``（已存在则跳过）；
    - 称号图标（虚狩专属）：role_base_info.addition_img 直接下发，每代理人独有，
      落 ``--assets-dir``，写 ``/images/strategy/<slug>/title.webp``；没有称号的
      代理人该字段为空，自动跳过。
    - 属性图标：WIKI 不下发，检测人工放置的
      ``images/attributes/<slug>.webp``（如 honed-edge），存在才写该
      URL，否则前端以色牌降级。
    """
    base_info = find_components(page, "role_base_info")[0]
    profession_slug = base_info.get("role_profession") or ""
    attribute_slug = base_info.get("role_attribute") or ""
    grade = (profile.get("grade") or "").lower()
    icons: dict = {"profession": "", "grade": "", "attribute": "", "title": ""}

    if not args.no_images:
        # 职业图标：全代理人共享，直接引用仓库图标集（始终写入正确路径）
        if profession_slug and profession_slug in PROFESSION_ICON_MAP:
            icons["profession"] = f"/images/icons/{PROFESSION_ICON_MAP[profession_slug]}.webp"
        # 等级图标：从 WIKI bundle vp 映射下载，已存在则跳过；下载失败留空，由 fix-agent 兜底
        grade_dest = IMAGES_ROOT / "grades" / f"{grade}.webp"
        grade_url = GRADE_ICON_URLS.get(grade)
        if grade_url and download_image(grade_url, grade_dest, args.timeout, skip_if_exists=True):
            icons["grade"] = f"/images/grades/{grade}.webp"
        # 称号图标（虚狩专属）：role_base_info.addition_img 直接下发
        title_img_url = base_info.get("addition_img") or ""
        if title_img_url and download_image(title_img_url, args.assets_dir / "title.webp", args.timeout):
            icons["title"] = f"{args.strategy_url}/title.webp"
        # 属性图标：WIKI 不下发，直接引用仓库图标集（始终写入正确路径）
        if attribute_slug and attribute_slug in ATTRIBUTE_ICON_MAP:
            icons["attribute"] = f"/images/attributes/{ATTRIBUTE_ICON_MAP[attribute_slug]}.webp"
    return icons


# ---------------------------------------------------------------- main


def keep_existing_title(profile: dict, output: Path) -> None:
    """WIKI 偶尔会清空称号字段（菲欧妮 2026-10 起 `addition_text` 为空，
    「坎卜斯黑枝」改成了阵营名）。此时保留旧产物里的称号，避免把已有信息抹掉。"""
    if profile.get("factionTitle") or not output.exists():
        return
    try:
        previous = json.loads(output.read_text(encoding="utf-8"))
        title = (previous.get("profile", {}).get("factionTitle") or "").strip()
    except (OSError, ValueError):
        return
    if title:
        profile["factionTitle"] = title
        print(f"  ! WIKI 未提供称号，保留旧值：{title}")


def build_guide(page: dict, entry_page_id: int, args) -> dict:
    profile = parse_profile(page)
    skills = parse_skills(page)
    cinemas = parse_cinemas(page)
    assets = local_assets(profile, skills, page, args)
    profile["icons"] = profile_icons(profile, page, args)
    keep_existing_title(profile, args.output)

    # 基础面板**不写进攻略 JSON**：唯一真实源是代理人预设
    # （``data/catalog/agents.json``），攻略页从预设派生——同一批数字不必在
    # 61 份攻略 JSON 里各存一份。抓取时仍然解析滑块并与预设对照，两边对不上
    # 就告警（Wiki 变了而预设没跟上，或反过来）。
    check_base_panel_against_preset(parse_base_panel(page), f"ep-{entry_page_id}")

    guide = {
        "meta": {
            "agentId": f"ep-{entry_page_id}",
            "entryPageId": entry_page_id,
            "name": profile["name"],
            "source": f"https://baike.mihoyo.com/zzz/wiki/content/{entry_page_id}/detail",
            "scrapedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        },
        "profile": profile,
        "assets": assets,
        "skills": skills,
        "cinemas": cinemas,
        "cinemaBackdrops": cinema_backdrops(page, cinemas, args),
    }
    return guide


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--entry-page-id", type=int, default=1687, help="WIKI 条目 id，默认 1687（叶瞬光）")
    parser.add_argument(
        "--slug",
        default=DEFAULT_SLUG,
        help=f"代理人 slug（= strategy/ 目录名），默认 {DEFAULT_SLUG}；独有图片 URL 的前缀",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help=f"JSON 输出路径，默认 {DEFAULT_OUTPUT}")
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=None,
        help="每代理人独有图片（立绘/称号/影画背景）输出目录，默认 frontend/public/images/strategy/<slug>/",
    )
    parser.add_argument("--no-images", action="store_true", help="不下载图片，JSON 中只保留远程 URL")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP 超时秒数")
    args = parser.parse_args()
    if args.assets_dir is None:
        args.assets_dir = IMAGES_ROOT / "strategy" / args.slug
    args.strategy_url = f"/images/strategy/{args.slug}"

    try:
        page = fetch_entry_page(args.entry_page_id, args.timeout)
        guide = build_guide(page, args.entry_page_id, args)
    except ScrapeError as error:
        print(f"抓取失败：{error}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(guide, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    move_count = sum(len(skill["moves"]) for skill in guide["skills"])
    size_kib = args.output.stat().st_size / 1024
    print(f"已生成 {args.output}（{size_kib:.1f} KiB）")
    print(f"  {guide['profile']['name']}：{guide['profile']['attribute']} / {guide['profile']['roleTag']} / {guide['profile']['grade']} 级")
    print(f"  技能 {len(guide['skills'])} 类 · 招式 {move_count} 条 · 影画 {len(guide['cinemas'])} 层")
    backdrops = guide.get("cinemaBackdrops") or {}
    print(f"  影画背景图 {len(backdrops)} 层（1-3 命影画展示2，4-6 命影画展示3）")
    for skill in guide["skills"]:
        print(f"    - {skill['name']}（{skill['wikiTab']}）：{len(skill['moves'])} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
