"""攻略抓取产物与「基础面板 = 60 级口径」的守护测试。

背景（柚叶踩过）：晋升需求滑块里，初始行给全量字段、满级行只给随晋升变化的
生命 / 攻击 / 防御，而满级行的字段名是**短名**（生命 / 攻击 / 防御，缺
「值 / 力」后缀）。抓取脚本按标签文本做键合并，短名覆盖不了长名，于是
基础面板同时列出初始行与满级行的生命 / 攻击 / 防御，页面显示 13 项。

这里守两层：
- 抓取函数：短名必须归一后覆盖（合成 page，不联网）
- 已提交数据：六个攻略页的 basePanel 不得出现重复口径，且与
  ``data/agent-presets.json`` 的同名字段同值（面板口径唯一真源）
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

#: 攻略页基础面板字段 -> agent-presets.base 的键。只列两处同名的字段：
#: 命破 / 锋御的专属字段（贯穿力 / 锐暴伤害 …）不进 preset 的 base，跳过。
PANEL_TO_BASE = {
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
}

#: 满级行的短字段名 -> 规范字段名。抓取脚本里的别名表，测试与之保持一致。
SHORT_LABELS = {"生命": "生命值", "攻击": "攻击力", "防御": "防御力"}

SCRAPER = REPO_ROOT / ".github/skills/agent-strategy/scripts/scrape_agent_guide.py"


def _load_scraper():
    """导入抓取脚本（有 ``__main__`` 保护，导入即安全）。"""
    spec = importlib.util.spec_from_file_location(SCRAPER.stem, SCRAPER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[SCRAPER.stem] = module
    spec.loader.exec_module(module)
    return module


def _slider_page(*rows: list[list[str]]) -> dict:
    """合成「晋升需求滑块」page。

    形状对齐真实抓取产物：``modules -> components -> data`` 三层，
    role_talent 的 ``data.list[].children[]`` 里放滑块，滑块 ``growth``
    的「初始 / 满级」两项各带一行 HTML 单元格。
    ``rows`` 按「初始 / 满级」顺序给出，每个 row 是 ``[单元格文本, ...]``。
    """
    growth = []
    for name, row in zip(("初始", "满级"), rows):
        growth.append(
            {
                "name": name,
                "children": [{"row": [[f"<p>{cell}</p>" for cell in row]]}],
            }
        )
    slider = {"list": [{"children": [{"desc": "晋升需求滑块", "growth": growth}]}]}
    return {"modules": [{"components": [{"component_id": "role_talent", "data": slider}]}]}


def test_parse_base_panel_merges_short_label_max_row() -> None:
    """满级行用短名时，必须归一成规范字段并覆盖初始值。"""
    scraper = _load_scraper()
    page = _slider_page(
        ["生命值：710", "攻击力：109", "防御力：49", "冲击力：86"],
        ["生命：8829", "攻击：683", "防御：612"],
    )
    panel = scraper.parse_base_panel(page)

    labels = [field["label"] for field in panel]
    # 短名不得作为独立字段残留
    assert not (set(labels) & set(SHORT_LABELS))
    # 生命 / 攻击 / 防御各只出现一次，且取的是满级值
    by_label = {field["label"]: field["value"] for field in panel}
    assert by_label["生命值"] == 8829
    assert by_label["攻击力"] == 683
    assert by_label["防御力"] == 612
    assert labels.count("生命值") == 1
    assert labels.count("攻击力") == 1
    assert labels.count("防御力") == 1


def test_parse_base_panel_same_label_max_row_still_wins() -> None:
    """满级行与初始行同名时，行为不变（其余代理人口径）。"""
    scraper = _load_scraper()
    page = _slider_page(
        ["生命值：710", "攻击力：109", "冲击力：86"],
        ["生命值：8829", "攻击力：683"],
    )
    panel = scraper.parse_base_panel(page)

    by_label = {field["label"]: field["value"] for field in panel}
    assert by_label == {"生命值": 8829, "攻击力": 683, "冲击力": 86}
    # 顺序仍按 BASE_PANEL_FIELDS，不因合并而乱序
    assert [field["label"] for field in panel] == ["生命值", "攻击力", "冲击力"]


def _drive_builds(data: dict) -> list[dict]:
    """取驱动盘推荐方案数组，兼容旧的单个 ``drives`` 对象。"""
    if isinstance(data.get("driveBuilds"), list):
        return data["driveBuilds"]
    return [data["drives"]] if data.get("drives") else []


def _set2_signature(build: dict) -> tuple:
    """2 件套签名：main/alt 的套装名序列（顺序敏感）。"""
    set2 = build.get("set2") or {}
    names = []
    for key in ("main", "alt"):
        value = set2.get(key)
        items = value if isinstance(value, list) else value and [value] or []
        for item in items:
            if isinstance(item, dict) and item.get("name"):
                names.append(f"{key}:{item['name']}")
    return tuple(names)


def _set4_names(build: dict) -> tuple:
    """4 件套名称序列；单对象与数组合一处理。"""
    set4 = build.get("set4")
    items = set4 if isinstance(set4, list) else set4 and [set4] or []
    return tuple(item["name"] for item in items if isinstance(item, dict) and item.get("name"))


@pytest.mark.parametrize(
    "slug",
    sorted(p.name for p in (REPO_ROOT / "strategy").iterdir() if p.is_dir()),
)
def test_drive_builds_do_not_repeat_the_same_two_piece(slug: str) -> None:
    """同一个 2 件套被多个方案重复列出时，必须合并成一个方案。

    柚叶曾把「月光骑士颂 / 静听嘉音 / 自由蓝调 + 法厄同之歌」写成三个完整方案，
    主词条表与副词条链整段重复三遍。合并后 4 件套收进一个 ``set4`` 数组、
    每项带 ``scene`` 使用场景备注，共用同一份 2 件套 / 主词条 / 副词条。
    """
    data = json.loads((REPO_ROOT / "strategy" / slug / "data" / f"{slug}.strategy.json").read_text(encoding="utf-8"))
    seen: dict[tuple, tuple] = {}
    for build in _drive_builds(data):
        signature = _set2_signature(build)
        if not signature:
            continue
        assert signature not in seen, (
            f"{slug} 的 2 件套 {signature} 被重复列出："
            f"{seen.get(signature)} 与 {_set4_names(build)}，应合并为一个方案"
        )
        seen[signature] = _set4_names(build)


@pytest.mark.parametrize(
    "slug",
    sorted(p.name for p in (REPO_ROOT / "strategy").iterdir() if p.is_dir()),
)
def test_merged_set4_array_entries_carry_a_scene(slug: str) -> None:
    """``set4`` 为数组（多 4 件套合并）时，每一项都要有 ``scene`` 使用场景备注。

    没有场景备注的话，读者无法判断该选哪一个，合并就失去了意义。
    """
    data = json.loads((REPO_ROOT / "strategy" / slug / "data" / f"{slug}.strategy.json").read_text(encoding="utf-8"))
    for build in _drive_builds(data):
        set4 = build.get("set4")
        if not isinstance(set4, list) or len(set4) < 2:
            continue
        for entry in set4:
            assert entry.get("scene", "").strip(), f"{slug} 的 4 件套 {entry.get('name')} 缺 scene 使用场景备注"


@pytest.mark.parametrize(
    "slug",
    sorted(p.name for p in (REPO_ROOT / "strategy").iterdir() if p.is_dir()),
)
def test_base_panel_matches_agent_presets(slug: str) -> None:
    """攻略页 basePanel 必须是 60 级口径，且与 preset 同值。

    这条断言会在两种坏味道上报警：字段重复列出（柚叶的 13 项），以及
    攻略页与计算器预设口径不一致。
    """
    data = json.loads((REPO_ROOT / "strategy" / slug / "data" / f"{slug}.json").read_text(encoding="utf-8"))
    presets = {
        preset["id"]: preset
        for preset in json.loads((REPO_ROOT / "data" / "agent-presets.json").read_text(encoding="utf-8"))
    }
    panel = data.get("basePanel")
    assert panel, f"{slug} 缺 basePanel（抓取产物结构可能已改版）"

    labels = [field["label"] for field in panel]
    assert len(labels) == len(set(labels)), f"{slug} 基础面板字段重复：{labels}"
    assert not (set(labels) & set(SHORT_LABELS)), f"{slug} 残留满级行短字段名：{labels}"

    agent_id = (data.get("meta") or {}).get("agentId")
    preset = presets.get(agent_id)
    if preset is None:
        pytest.skip(f"{slug}（{agent_id}）不在 agent-presets.json 中")
    base = preset["base"]
    for field in panel:
        key = PANEL_TO_BASE.get(field["label"])
        if key is None or key not in base:
            continue  # 专属字段（贯穿力 / 锐暴伤害 …）不参与比对
        assert field["value"] == base[key], f"{slug}.{field['label']} 与 preset.base.{key} 不一致"


def _strategy_dirs() -> list[str]:
    return sorted(p.name for p in (REPO_ROOT / "strategy").iterdir() if p.is_dir())


def _mapping_slugs() -> set[str]:
    mapping = json.loads((REPO_ROOT / "data" / "agent-name-mapping.json").read_text(encoding="utf-8"))
    return {item["slug"] for item in mapping}


def _registry_slugs() -> set[str]:
    text = (REPO_ROOT / "frontend" / "src" / "constants" / "strategyGuides.ts").read_text(encoding="utf-8")
    return set(re.findall(r"slug:\s*'([^']+)'", text))


def test_strategy_dirs_use_canonical_slugs() -> None:
    """目录名必须是 mapping 里的规范 slug，且每个目录都已登记。"""
    dirs = set(_strategy_dirs())
    mapping = _mapping_slugs()
    registry = _registry_slugs()
    assert dirs == registry, f"目录与登记表不一致：仅目录 {sorted(dirs - registry)}；仅登记 {sorted(registry - dirs)}"
    assert dirs <= mapping, f"非规范目录：{sorted(dirs - mapping)}"


def test_strategy_data_files_are_canonical_utf8_and_self_consistent() -> None:
    """每个攻略页必须有规范命名的两份 JSON，且引用只指向自己的 slug。"""
    problems: list[str] = []
    for slug in _strategy_dirs():
        data_dir = REPO_ROOT / "strategy" / slug / "data"
        scraped = data_dir / f"{slug}.json"
        strategy = data_dir / f"{slug}.strategy.json"
        for path in (scraped, strategy):
            if not path.exists():
                problems.append(f"{path.relative_to(REPO_ROOT)} 缺失")
                continue
            try:
                text = path.read_text(encoding="utf-8")
                json.loads(text)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                problems.append(f"{path.relative_to(REPO_ROOT)} 无法读取：{exc}")
                continue
            for other in re.findall(r"/images/strategy/([^/\"']+)/", text):
                if other != slug:
                    problems.append(f"{path.relative_to(REPO_ROOT)} 引用旧图片目录 {other}")
        app_js = REPO_ROOT / "strategy" / slug / "app.js"
        if app_js.exists():
            text = app_js.read_text(encoding="utf-8")
            if f"data/{slug}.json" not in text or f"data/{slug}.strategy.json" not in text:
                problems.append(f"{app_js.relative_to(REPO_ROOT)} 的 DATA_URL/STRATEGY_URL 未指向 {slug}")
    assert not problems, "\n".join(problems)


def test_icon_references_point_to_existing_lowercase_files() -> None:
    """属性 / 职业图标必须存在，且统一为小写 ASCII slug。"""
    public = REPO_ROOT / "frontend" / "public"
    files = [
        REPO_ROOT / "frontend" / "src" / "constants" / "strategyGuides.ts",
        *sorted((REPO_ROOT / "strategy").glob("*/data/*.json")),
    ]
    missing: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for ref in re.findall(r"/images/(?:attributes|icons)/[a-z0-9-]+\.png", text):
            if not (public / ref.lstrip("/")).exists():
                missing.append(f"{path.relative_to(REPO_ROOT)} -> {ref}")
    # 渲染器的 roleTag 回退路径（profile.icons.profession 为空时使用）
    for slug in ("attack", "stun", "anomaly", "support", "defense", "rupture", "armorer"):
        ref = f"/images/icons/{slug}.png"
        if not (public / ref.lstrip("/")).exists():
            missing.append(f"渲染器回退 -> {ref}")
    assert not missing, "\n".join(missing)


def test_all_strategy_image_references_exist() -> None:
    """攻略 JSON 与登记表里的每个具体 /images/…png 都必须有对应文件。"""
    public = REPO_ROOT / "frontend" / "public"
    files = [
        REPO_ROOT / "frontend" / "src" / "constants" / "strategyGuides.ts",
        *sorted((REPO_ROOT / "strategy").glob("*/data/*.json")),
    ]
    missing: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for ref in re.findall(r"/images/[A-Za-z0-9_./-]+\.png", text):
            if not (public / ref.lstrip("/")).exists():
                missing.append(f"{path.relative_to(REPO_ROOT)} -> {ref}")
    assert not missing, "\n".join(missing)


def test_skill_doc_strategy_paths_exist() -> None:
    """Skill 文档里的 ``strategy/<slug>/`` 示例必须指向真实目录。"""
    actual = set(_strategy_dirs())
    ignored = {"scripts"}
    missing: list[str] = []
    for path in sorted((REPO_ROOT / ".github" / "skills").rglob("SKILL.md")):
        text = path.read_text(encoding="utf-8")
        for ref in sorted(set(re.findall(r"strategy/([a-z0-9-]+)/", text))):
            if ref not in actual and ref not in ignored:
                missing.append(f"{path.relative_to(REPO_ROOT)} -> strategy/{ref}/")
    assert not missing, "\n".join(missing)
