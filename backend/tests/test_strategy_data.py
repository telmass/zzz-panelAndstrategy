"""攻略抓取产物与「基础面板 = 60 级口径」的守护测试。

背景（柚叶踩过）：晋升需求滑块里，初始行给全量字段、满级行只给随晋升变化的
生命 / 攻击 / 防御，而满级行的字段名是**短名**（生命 / 攻击 / 防御，缺
「值 / 力」后缀）。抓取脚本按标签文本做键合并，短名覆盖不了长名，于是
基础面板同时列出初始行与满级行的生命 / 攻击 / 防御，页面显示 13 项。

这里守两层：
- 抓取函数：短名必须归一后覆盖（合成 page，不联网）
- 已提交数据：六个攻略页的 basePanel 不得出现重复口径，且与
  ``data/catalog/agents.json`` 的同名字段同值（面板口径唯一真源）
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
def test_drive_builds_have_distinct_four_piece_sets(slug: str) -> None:
    """多个驱动盘方案只要 4 件套不同，就写成独立方案（分页），不合并。

    roxy 的参考实现：非锋御队 4 山大王 + 2 回能与锋御队 4 静听嘉音 + 2 回能
    共用同一份 2 件套 / 主词条 / 副词条，但因为 4 件套不同而写成两个方案——
    每个方案的名字以使用场景开头（"非锋御队：" / "锋御队："）。

    同一个 4 件套出现在多个方案中才是数据错误（重复方案）。
    """
    data = json.loads((REPO_ROOT / "strategy" / slug / "data" / f"{slug}.strategy.json").read_text(encoding="utf-8"))
    seen: dict[tuple, int] = {}
    for index, build in enumerate(_drive_builds(data)):
        signature = _set4_names(build)
        if not signature:
            continue
        assert signature not in seen, (
            f"{slug} 的 4 件套 {signature} 被重复列出："
            f"方案 {seen.get(signature)} 与方案 {index}——"
            "同一个 4 件套不应出现在多个方案中；不同 4 件套应写成独立方案"
        )
        seen[signature] = index


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
def test_strategy_json_does_not_carry_its_own_base_panel(slug: str) -> None:
    """攻略 JSON 不再自带基础面板——那份数据的唯一真实源是代理人预设。

    同一批数字曾在 61 份攻略 JSON 与预设数据里各存一份，已经发生过漂移
    （三名代理人的属性名口径在两处不一致）。基础面板现由前端从预设派生
    （``frontend/src/strategy/basePanel.ts``），这里守住「不再各存一份」。
    """
    path = REPO_ROOT / "strategy" / slug / "data" / f"{slug}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "basePanel" not in data, (
        f"{slug} 的攻略 JSON 仍带 basePanel——基础面板应从代理人预设派生"
    )


@pytest.mark.parametrize(
    "slug",
    sorted(p.name for p in (REPO_ROOT / "strategy").iterdir() if p.is_dir()),
)
def test_strategy_agent_id_resolves_to_a_published_preset(slug: str) -> None:
    """攻略页的 agentId 必须对应一个已发布的预设。

    攻略页的基础面板从预设派生，因此这条关联是硬依赖——没有预设就没有面板。
    """
    path = REPO_ROOT / "strategy" / slug / "data" / f"{slug}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    presets = {
        preset["id"]: preset
        for preset in json.loads(
            (REPO_ROOT / "data" / "catalog" / "agents.json").read_text(encoding="utf-8")
        )
    }
    agent_id = (data.get("meta") or {}).get("agentId")
    assert agent_id in presets, (
        f"{slug}（agentId={agent_id}）不在 agents.json 中——"
        "每个攻略页的 agentId 都必须对应一个已发布的预设；"
        "未发布代理人不应有攻略页目录"
    )


def _strategy_dirs() -> list[str]:
    return sorted(p.name for p in (REPO_ROOT / "strategy").iterdir() if p.is_dir())


def _mapping_slugs() -> set[str]:
    mapping = json.loads((REPO_ROOT / "data" / "catalog" / "agent-index.json").read_text(encoding="utf-8"))
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
        for ref in re.findall(r"/images/(?:attributes|icons)/[a-z0-9-]+\.webp", text):
            if not (public / ref.lstrip("/")).exists():
                missing.append(f"{path.relative_to(REPO_ROOT)} -> {ref}")
    # 渲染器的 roleTag 回退路径（profile.icons.profession 为空时使用）
    for slug in ("attack", "stun", "anomaly", "support", "defense", "rupture", "armorer"):
        ref = f"/images/icons/{slug}.webp"
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
        for ref in re.findall(r"/images/[A-Za-z0-9_./-]+\.webp", text):
            if not (public / ref.lstrip("/")).exists():
                missing.append(f"{path.relative_to(REPO_ROOT)} -> {ref}")
    assert not missing, "\n".join(missing)


def test_every_main_stat_has_a_string_note_field() -> None:
    """主词条表第四列备注依赖 ``mainStats[].note``；每条都必须预留字符串位置。"""
    problems: list[str] = []
    for path in sorted((REPO_ROOT / "strategy").glob("*/data/*.strategy.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for build_index, build in enumerate(data.get("driveBuilds") or []):
            for stat_index, stat in enumerate(build.get("mainStats") or []):
                if not isinstance(stat.get("note"), str):
                    problems.append(
                        f"{path.relative_to(REPO_ROOT)} driveBuilds[{build_index}].mainStats[{stat_index}] 缺 note 字符串"
                    )
    assert not problems, "\n".join(problems)


def test_drive_build_set_groups_are_well_formed() -> None:
    """驱动盘套装组的形状必须合法。

    **驱动盘不一定只有「4+2」。** 6 个槽位也可以是 2+2+2（三组 2 件套）。
    契约分**两条轴**，不能混：

    - **组**（并列，都要装）：``set2`` / ``set2b`` / ``set2c``——第 1/2/3 组
      2 件套，每组是 ``{main, alt}``。最多三组（6 个槽位最多三组 2 件套）。
    - **候选**（二选一）：组内的 ``main`` / ``alt``，各自可以是单个套装对象，
      也可以是**多个同效果的候选套装**（如「物理伤害 +10%」有獠牙重金属与
      沧浪行歌两套）。

    ``set4`` 是另一条轴：4 件套的**候选**列表（三选一，各带 ``scene``
    说明什么场景用哪个），**不是**「同时生效多个 4 件套」——一个代理人最多
    生效一个 4 件套，4+4 也装不下（8 片 > 6 槽）。

    形状写错时页面会静默少渲染一栏——所以在这里拦住。
    """
    problems: list[str] = []

    def check_set_pick(name: str, value: object, where: str) -> None:
        """一个「首选 / 备选」：套装对象或候选套装数组，元素要有 name。"""
        if value is None:
            return
        items = value if isinstance(value, list) else [value]
        if not items:
            problems.append(f"{where}.{name} 是空数组")
        for index, item in enumerate(items):
            if not isinstance(item, dict) or not item.get("name"):
                problems.append(f"{where}.{name}[{index}] 缺 name")

    def check_set4(value: object, where: str) -> None:
        """4 件套候选：对象或数组，元素要有 name。"""
        if value is None:
            return
        items = value if isinstance(value, list) else [value]
        for index, item in enumerate(items):
            if not isinstance(item, dict) or not item.get("name"):
                problems.append(f"{where}.set4[{index}] 缺 name")

    def check_set2_group(group: object, where: str) -> None:
        if not isinstance(group, dict):
            problems.append(f"{where} 的 2 件套组不是对象")
            return
        if "main" not in group:
            problems.append(f"{where} 的 2 件套组缺 main")
        check_set_pick("main", group.get("main"), where)
        check_set_pick("alt", group.get("alt"), where)

    for path in sorted((REPO_ROOT / "strategy").glob("*/data/*.strategy.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for build_index, build in enumerate(data.get("driveBuilds") or []):
            where = f"{path.relative_to(REPO_ROOT)} driveBuilds[{build_index}]"
            check_set4(build.get("set4"), where)
            groups = 0
            for key in ("set2", "set2b", "set2c"):
                group = build.get(key)
                if group is None:
                    continue
                groups += 1
                # 「组」是一个对象——不是数组。写成数组是把它当成了「候选」，
                # 那是 main / alt 内部的维度，两条轴不能混。
                if isinstance(group, list):
                    problems.append(f"{where}.{key} 写成了数组：组是一个对象，候选在 main / alt 里")
                    continue
                check_set2_group(group, f"{where}.{key}")
            if groups > 3:
                problems.append(f"{where} 有 {groups} 组 2 件套，6 个槽位最多三组")
            # 4 件套组必然带来它自己的 2 件套效果，而 4+2+2 是 8 片 > 6 槽——
            # 有 4 件套组时就只能再有一组 2 件套。
            if build.get("set4") is not None and groups > 1:
                problems.append(
                    f"{where} 同时有 4 件套组与 {groups} 组 2 件套："
                    "4+2+2 需要 8 片，6 个槽位装不下"
                )

    assert not problems, "\n".join(problems)

#: 修正量 -> 展示标签。只列**毕业面板可能展示的行**（``TOTAL_LABELS`` 的口径）。
#:
#: 用来判断「某个 2 件套效果被多算一次时，会不会落到展示行上」。
MODIFIER_TO_LABEL = {
    "hp_pct": "生命值",
    "hp_flat": "生命值",
    "hp_base": "生命值",
    "atk_pct": "攻击力",
    "atk_flat": "攻击力",
    "atk_base": "攻击力",
    "def_pct": "防御力",
    "def_flat": "防御力",
    "cr": "暴击率",
    "cd": "暴击伤害",
    "impact_pct": "冲击力",
    "ac_pct": "异常掌控",
    "dmg": "增伤",
    "pr": "穿透率",
    "pen_val": "穿透值",
    "am": "异常精通",
    "er_pct": "能量回复",
    "er_flat": "能量回复",
}


def test_graduation_build_never_double_counts_one_set() -> None:
    """4 件套与 2 件套同套时，多算的那份 2 件套效果不许落在展示行上。

    **6 件全来自同一套**（4 件套组 + 同一套的 2 件套组）是合法配装，但此时
    实际生效的是**一组 2 件套效果 + 一个 4 件套效果**——同一套的 2 件套效果
    不会因为多穿两件而叠加。

    ``calc_graduation_panel.py`` 遇到这种配装会**把重复的 2 件套组并掉**
    （不额外占槽位），所以算出来的面板是对的。这条守的是**已发布的面板**：
    如果多算的那份 2 件套效果会落在某个展示行上，那一行的数值就偏大了。

    判据：从规则表取该套装的 ``effect2`` -> 它的 ``to``（修正量）-> 展示标签；
    那个标签**不能**出现在面板的展示行里。
    """
    rules = json.loads(
        (REPO_ROOT / "data" / "rules" / "calculator-rules.json").read_text(encoding="utf-8")
    )
    set_targets = {option["id"]: option["to"] for option in rules["setOptions"]}
    discs = {
        item["name"]: item
        for item in json.loads(
            (REPO_ROOT / "data" / "catalog" / "drive-discs.json").read_text(encoding="utf-8")
        )
    }

    problems: list[str] = []
    for path in sorted((REPO_ROOT / "strategy").glob("*/data/*.strategy.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for key in ("graduationPanel", "graduationPanelAlt"):
            panel = data.get(key)
            if not panel:
                continue
            build = panel.get("build") or {}
            four = build.get("set4")
            two = build.get("set2")
            twos = two if isinstance(two, list) else ([two] if two else [])
            if not four or four not in twos:
                continue
            # 同套：4 件套组带来的 2 件套效果 + 2 件套组带来的 2 件套效果
            # 本来就是同一个，只算一次。面板的展示行里不能有受它影响的行。
            effect2 = discs.get(four, {}).get("effect2")
            if not effect2:
                continue
            target = set_targets.get(effect2)
            if target is None:
                continue
            label = MODIFIER_TO_LABEL.get(target)
            if label is None:
                continue
            shown = {field.get("label") for field in panel.get("totals") or []}
            if label in shown:
                problems.append(
                    f"{path.relative_to(REPO_ROOT)} {key}：4 件套 {four} 与 2 件套同套，"
                    f"「{label}」被多算了一次"
                )
    assert not problems, "\n".join(problems)


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


def test_strategy_cross_references_resolve() -> None:
    """攻略 JSON 的交叉引用完整性：武器名/图标、队伍 agentId、驱动盘名/图标。"""
    agents = json.loads((REPO_ROOT / "data" / "catalog" / "agents.json").read_text(encoding="utf-8"))
    weapons = json.loads((REPO_ROOT / "data" / "catalog" / "weapons.json").read_text(encoding="utf-8"))
    discs = json.loads((REPO_ROOT / "data" / "catalog" / "drive-discs.json").read_text(encoding="utf-8"))
    by_agent_id = {a["id"]: a for a in agents}
    by_weapon_name = {w["name"]: w for w in weapons}
    by_disc_name = {d["name"]: d for d in discs}
    problems: list[str] = []

    for slug in _strategy_dirs():
        path = REPO_ROOT / "strategy" / slug / "data" / f"{slug}.strategy.json"
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))

        # 音擎推荐：名称必须在 weapon-presets 中；有图标时 id 要对应
        for tier in data.get("weapons") or []:
            for item in tier.get("items") or []:
                name = item.get("name", "")
                weapon = by_weapon_name.get(name)
                if weapon is None:
                    problems.append(f"{slug}: 音擎「{name}」不在 weapons.json 中")
                elif item.get("icon") and item["icon"] != f"/images/weapons/{weapon['id']}.webp":
                    problems.append(f"{slug}: 音擎「{name}」图标 id 不匹配")

        # 队伍成员：agentId 必须在 agent-presets 中；avatar 有值时要对应
        for team in data.get("teams") or []:
            for member in team.get("members") or []:
                aid = member.get("agentId", "")
                if aid not in by_agent_id:
                    problems.append(f"{slug}: 队伍成员 agentId={aid} 不在 agents.json 中")
                avatar = member.get("avatar", "")
                if avatar and avatar != f"/images/agents/{aid}.webp":
                    problems.append(f"{slug}: 队伍成员 {aid} avatar 路径不匹配")

        # 驱动盘方案：set4/set2 名称必须在 drive-disc-presets 中
        for build in data.get("driveBuilds") or []:
            set4 = build.get("set4") or {}
            if isinstance(set4, list):
                for s in set4:
                    name = (s or {}).get("name", "")
                    if name and name not in by_disc_name:
                        problems.append(f"{slug}: 4 件套「{name}」不在 drive-discs.json 中")
            else:
                name = (set4 or {}).get("name", "")
                if name and name not in by_disc_name:
                    problems.append(f"{slug}: 4 件套「{name}」不在 drive-discs.json 中")
            set2 = build.get("set2") or {}
            if isinstance(set2, dict):
                for key in ("main", "alt"):
                    sub = set2.get(key)
                    if isinstance(sub, dict) and sub.get("name") and sub["name"] not in by_disc_name:
                        problems.append(f"{slug}: 2 件套「{sub['name']}」不在 drive-discs.json 中")

    assert not problems, "\n".join(sorted(set(problems)))


def test_no_placeholder_text_in_strategy_data() -> None:
    """攻略数据不应残留占位文本（待确认 / TODO / TBD）。"""
    pattern = re.compile(r"待确认|TODO|TBD|FIXME|placeholder|占位")
    problems: list[str] = []
    for slug in _strategy_dirs():
        for suffix in ("json", "strategy.json"):
            path = REPO_ROOT / "strategy" / slug / "data" / f"{slug}.{suffix}"
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for match in pattern.finditer(text):
                context = text[max(0, match.start() - 30) : match.end() + 30]
                problems.append(f"{path.relative_to(REPO_ROOT)}: …{context}…")
    assert not problems, "\n".join(problems)
