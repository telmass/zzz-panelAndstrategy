"""预设数据加载与下发的测试（第 4 步第 18 条）。

分三层：
- ``data/catalog/*.json`` 真实数据必须能通过全部校验（回归守卫）
- ``presets.validate`` 对每条规则都有反例（校验器本身的正确性）
- HTTP 层形状与「数据坏了要报 503 而不是 500」

反例数据写到 pytest 的 ``tmp_path``，用 ``ZZZ_PANEL_DATA_DIR`` 指过去，
因此不会碰到仓库里真实的 ``data/``。临时目录里也要放一份
``manifest.json``——数据集路径由它登记，没有它 loader 无从知道文件在哪。
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from zzz_panel.api.app import app
from zzz_panel.presets import loader
from zzz_panel.presets import manifest as presets_manifest
from zzz_panel.presets.attributes import (
    attribute_counts,
    is_special_attribute,
    special_agent_attributes,
)
from zzz_panel.schemas.presets import AgentPreset

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))
sync_presets = importlib.import_module("sync_presets")

client = TestClient(app)

#: 临时数据目录里用的登记表。只登记本组用例要写的那两个数据集。
TEMP_MANIFEST = {
    "version": 1,
    "datasets": {
        "agents": {"path": "catalog/agents.json"},
        "weapons": {"path": "catalog/weapons.json"},
    },
    "strategy": {"root": "strategy", "dataSubdir": "data", "indexDataset": "agent-index"},
}


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """指向临时数据目录，并清掉按 mtime 缓存的旧值。"""
    (tmp_path / "manifest.json").write_text(
        json.dumps(TEMP_MANIFEST, ensure_ascii=False), encoding="utf-8"
    )
    monkeypatch.setenv("ZZZ_PANEL_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(presets_manifest, "_data_dir", None)
    return tmp_path


def write(directory: Path, name: str, items: object) -> None:
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")


def valid_agent(**overrides: object) -> dict:
    """一条能通过全部校验的代理人预设，逐条覆盖用 overrides 破坏某条规则。"""
    agent = {
        "id": "ep-0001",
        "name": "示例代理人",
        "attribute": "火",
        "grade": "S",
        "roleTag": "强攻",
        "panelMode": "standard",
        "source": "https://example.invalid/1",
        "base": {key: 1 for key in ("hp", "atk", "def", "impact", "cr", "cd", "ac", "am", "pr", "er")},
        "core": [
            {
                "optionId": "cr",
                "ranks": ["A", "C", "E"],
                "label": "暴击率",
                "perRank": 4.8,
                "totalValue": 14.4,
                "unit": "%",
            },
            {
                "optionId": "cd",
                "ranks": ["B", "D", "F"],
                "label": "暴击伤害",
                "perRank": 9.6,
                "totalValue": 28.8,
                "unit": "%",
            },
        ],
    }
    agent.update(overrides)
    return agent


def valid_weapon(**overrides: object) -> dict:
    weapon = {
        "id": "ep-1001",
        "name": "示例音擎",
        "grade": "S",
        "roleTag": "强攻",
        "source": "https://example.invalid/2",
        "base": {"kind": "atk", "value": 713},
        "substat": {"label": "暴击伤害", "value": 48, "kind": "pct", "to": "cd"},
    }
    weapon.update(overrides)
    return weapon


# ------------------------------------------------------------------ 真实数据


def test_real_agent_data_passes_validation() -> None:
    agents = loader.load_agents()
    source = json.loads(presets_manifest.dataset_path("agents").read_text(encoding="utf-8"))
    assert len(agents) == len(source)
    assert len({agent.id for agent in agents}) == len(agents)


def test_real_weapon_data_passes_validation() -> None:
    weapons = loader.load_weapons()
    source = json.loads(presets_manifest.dataset_path("weapons").read_text(encoding="utf-8"))
    assert len(weapons) == len(source)
    assert len({weapon.id for weapon in weapons}) == len(weapons)


def test_response_matches_source_json_byte_for_byte() -> None:
    """响应与源数据逐条等价——后端不得改写或丢字段。

    这是前端能删掉 ``src/data/*.ts`` 副本的前提：接口给出的就是源数据。
    """
    for dataset, url in (
        ("agents", "/api/presets/agents"),
        ("weapons", "/api/presets/weapons"),
    ):
        source = json.loads(presets_manifest.dataset_path(dataset).read_text(encoding="utf-8"))
        resp = client.get(url)
        assert resp.status_code == 200, url
        assert resp.json()["items"] == source, url


# ----------------------------------------------------- 抓取脚本与规范形式


def _load_skill_script(relative: str):
    """按路径导入抓取脚本。两个脚本都有 ``__main__`` 保护，导入即安全。"""
    path = Path(__file__).resolve().parents[2] / relative
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fetch_scripts_default_output_is_data_dir() -> None:
    """抓取脚本必须写 ``data/catalog/*.json``，不能再写 legacy（第 4 步第 19 条）。"""
    agent = _load_skill_script(
        ".github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py"
    )
    weapon = _load_skill_script(
        ".github/skills/read-zzz-engine-stats/scripts/refresh_weapon_presets.py"
    )
    assert agent.OUTPUT == "data/catalog/agents.json"
    assert weapon.OUTPUT == "data/catalog/weapons.json"
    assert agent.REPO_ROOT == REPO_ROOT
    assert weapon.REPO_ROOT == REPO_ROOT


def test_fetch_scripts_reuse_the_shared_serializer() -> None:
    """两个抓取脚本必须复用 sync_presets 的序列化，而不是各写一套。

    各写一套的后果是重新抓取后 ``--check`` 永远报漂移，且原因极难定位。
    """
    for relative in (
        ".github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py",
        ".github/skills/read-zzz-engine-stats/scripts/refresh_weapon_presets.py",
    ):
        module = _load_skill_script(relative)
        assert module.load_sync_presets() is sync_presets


@pytest.mark.parametrize(
    ("dataset", "agent"),
    [("agents", True), ("weapons", False)],
)
def test_presets_json_is_already_in_canonical_form(dataset: str, agent: bool) -> None:
    """``data/catalog/*.json`` 必须已是规范形式。

    抓取脚本复用 sync_presets 的规范化与序列化，因此重新抓取产出的字节
    应与已提交文件完全一致。这条断言保证「``--check`` 报不出漂移」
    不是碰巧成立。
    """
    raw = presets_manifest.dataset_path(dataset).read_text(encoding="utf-8")
    normalized = [sync_presets.order_preset(item, agent) for item in json.loads(raw)]
    assert sync_presets.dump_json(normalized) == raw, dataset


def test_agent_fetch_script_reproduces_committed_json() -> None:
    """代理人脚本的 ``render()`` 喂入已提交数据后必须原样重现该文件。

    这验证了 ``render`` 用的就是规范序列化，且 ``core`` 的 int/float 归一
    （420.0 → 420、0.12 保持 float）没有改变字面量。
    """
    module = _load_skill_script(
        ".github/skills/read-zzz-agent-stats/scripts/refresh_agent_presets.py"
    )
    raw = presets_manifest.dataset_path("agents").read_text(encoding="utf-8")
    assert module.render(json.loads(raw)) == raw


def test_weapon_fetch_script_reproduces_committed_json() -> None:
    """音擎脚本同上。

    ``render`` 吃的是抓取原始记录（``substatLabel`` / ``baseKind`` …）而非
    成品预设，因此这里从已提交的预设反推记录，验证 int/float 归一
    （713.0 → 713、48.0 → 48）与 ``base`` 二元组的拆分。
    """
    module = _load_skill_script(
        ".github/skills/read-zzz-engine-stats/scripts/refresh_weapon_presets.py"
    )
    raw = presets_manifest.dataset_path("weapons").read_text(encoding="utf-8")
    presets = json.loads(raw)

    records = [
        {
            "id": int(item["id"].split("-")[1]),
            "name": item["name"],
            "grade": item["grade"],
            "baseKind": item["base"]["kind"],
            "baseAttack": float(item["base"]["value"]) if item["base"]["kind"] == "atk" else 0,
            "baseDefense": float(item["base"]["value"]) if item["base"]["kind"] == "def" else 0,
            "substatLabel": item["substat"]["label"],
            "substatValue": float(item["substat"]["value"]),
            "substatIsPct": item["substat"]["kind"] == "pct",
            "roleTags": [item["roleTag"]],
        }
        for item in presets
    ]

    content, skipped, written = module.render(records)
    assert content == raw
    assert skipped == []
    assert written == len(presets)


# ------------------------------------------------------------------ 校验规则


def test_duplicate_id_is_rejected(data_dir: Path) -> None:
    write(data_dir, "catalog/agents.json", [valid_agent(), valid_agent(name="另一个")])
    with pytest.raises(loader.PresetLoadError, match="id 重复"):
        loader.load_agents()


def test_unknown_role_tag_is_rejected(data_dir: Path) -> None:
    write(data_dir, "catalog/agents.json", [valid_agent(roleTag="avigator")])
    with pytest.raises(loader.PresetLoadError, match="roleTag"):
        loader.load_agents()


def test_unknown_panel_mode_is_rejected(data_dir: Path) -> None:
    write(data_dir, "catalog/agents.json", [valid_agent(panelMode="mystery")])
    with pytest.raises(loader.PresetLoadError, match="校验失败"):
        loader.load_agents()


def test_unknown_attribute_is_rejected(data_dir: Path) -> None:
    write(data_dir, "catalog/agents.json", [valid_agent(attribute="雷")])
    with pytest.raises(loader.PresetLoadError, match="attribute"):
        loader.load_agents()


def test_unknown_grade_is_rejected(data_dir: Path) -> None:
    write(data_dir, "catalog/agents.json", [valid_agent(grade="SS")])
    with pytest.raises(loader.PresetLoadError, match="grade"):
        loader.load_agents()


def test_missing_attribute_is_rejected(data_dir: Path) -> None:
    agent = valid_agent()
    del agent["attribute"]
    write(data_dir, "catalog/agents.json", [agent])
    with pytest.raises(loader.PresetLoadError, match="校验失败"):
        loader.load_agents()


# ------------------------------------------------------------- 特殊属性判定


def test_real_data_special_attributes_follow_the_count_rule() -> None:
    """真实数据：特殊属性恰为「当前只有一名代理人持有」的那些属性。

    同时反证硬编码名单：风 有两名持有人，按规则**不是**特殊属性，
    即便它同样是官方新出的属性。
    """
    agents = loader.load_agents()
    counts = attribute_counts(agents)

    assert special_agent_attributes(agents) == {
        attribute for attribute, count in counts.items() if count == 1
    }
    assert counts["风"] == 2
    assert "风" not in special_agent_attributes(agents)
    assert is_special_attribute("烈霜", agents)
    assert not is_special_attribute("火", agents)
    assert not is_special_attribute("风", agents)


def test_special_attribute_needs_exactly_one_holder() -> None:
    """规则只看人数：2 人及以上（含恰好 2 人）都不是特殊属性。"""
    agents = [
        AgentPreset.model_validate(valid_agent(name="甲", attribute="玄墨")),
        AgentPreset.model_validate(valid_agent(name="乙", attribute="玄墨")),
        AgentPreset.model_validate(valid_agent(name="丙", attribute="流明")),
    ]

    assert attribute_counts(agents) == {"玄墨": 2, "流明": 1}
    assert special_agent_attributes(agents) == frozenset({"流明"})
    assert is_special_attribute("流明", agents)
    assert not is_special_attribute("玄墨", agents)


def test_special_attributes_are_not_hardcoded() -> None:
    """换一个只有一人的新属性，它同样是特殊属性——证明规则与属性名无关。"""
    agents = [
        AgentPreset.model_validate(valid_agent(name="甲", attribute="玄墨")),
        AgentPreset.model_validate(valid_agent(name="乙", attribute="玄墨")),
        AgentPreset.model_validate(valid_agent(name="丙", attribute="全新属性")),
    ]
    # 正常数据里「全新属性」会被白名单拦下，这里直接检验判定函数本身：
    # 它既不在 AGENT_ATTRIBUTES 里，也不是任何硬编码名单的一员，
    # 却依然按人数被判成特殊属性。
    assert special_agent_attributes(agents) == frozenset({"全新属性"})


def test_attribute_counts_and_special_set_ignore_order() -> None:
    """判定只看人数，不看代理人在列表中的位置。"""
    agents = [
        AgentPreset.model_validate(valid_agent(name="甲", attribute="风")),
        AgentPreset.model_validate(valid_agent(name="乙", attribute="风")),
    ]
    assert attribute_counts(agents) == {"风": 2}
    assert special_agent_attributes(agents) == frozenset()


def test_unrepresentable_core_bonus_is_rejected(data_dir: Path) -> None:
    agent = valid_agent()
    agent["core"][0]["totalValue"] = 15.0
    write(data_dir, "catalog/agents.json", [agent])
    with pytest.raises(loader.PresetLoadError, match="选项值"):
        loader.load_agents()


def test_inconsistent_per_rank_value_is_rejected(data_dir: Path) -> None:
    agent = valid_agent()
    agent["core"][0]["perRank"] = 5.0
    write(data_dir, "catalog/agents.json", [agent])
    with pytest.raises(loader.PresetLoadError, match="与合计"):
        loader.load_agents()


def test_core_bonuses_must_fill_exactly_two_slots(data_dir: Path) -> None:
    agent = valid_agent()
    agent["core"] = agent["core"][:1]
    write(data_dir, "catalog/agents.json", [agent])
    with pytest.raises(loader.PresetLoadError, match="槽位"):
        loader.load_agents()


def test_option_count_two_consumes_both_slots() -> None:
    """``optionCount=2`` 时一条加成即可填满两个槽位。"""
    agent = AgentPreset.model_validate(
        valid_agent(
            core=[
                {
                    "optionId": "cr",
                    "ranks": ["A", "C"],
                    "label": "暴击率",
                    "perRank": 14.4,
                    "totalValue": 28.8,
                    "unit": "%",
                    "optionCount": 2,
                }
            ]
        )
    )
    from zzz_panel.presets.validate import validate_agents

    validate_agents([agent])  # 不应抛错


def test_missing_base_key_is_rejected_outside_rupture_mode(data_dir: Path) -> None:
    """通用模式缺任一项基础属性都是数据损坏。"""
    agent = valid_agent()
    del agent["base"]["pr"]
    write(data_dir, "catalog/agents.json", [agent])
    with pytest.raises(loader.PresetLoadError, match="基础面板"):
        loader.load_agents()


def test_rupture_mode_may_omit_pr_and_er(data_dir: Path) -> None:
    """命破模式缺 pr/er 合法——这两个位置被贯穿力 / 闪能自动累积取代。"""
    agent = valid_agent(panelMode="rupture")
    del agent["base"]["pr"]
    del agent["base"]["er"]
    agent["baseExtra"] = {"penforce": 100, "energyAccumulation": 2}
    write(data_dir, "catalog/agents.json", [agent])
    assert len(loader.load_agents()) == 1


def test_rupture_agent_requires_additional_base_stats(data_dir: Path) -> None:
    write(data_dir, "catalog/agents.json", [valid_agent(panelMode="rupture")])
    with pytest.raises(loader.PresetLoadError, match="额外基础属性"):
        loader.load_agents()


def test_weapon_base_value_must_be_positive(data_dir: Path) -> None:
    write(data_dir, "catalog/weapons.json", [valid_weapon(base={"kind": "atk", "value": 0})])
    with pytest.raises(loader.PresetLoadError, match="基础值"):
        loader.load_weapons()


def test_unmodeled_base_stat_requires_all_three_fields(data_dir: Path) -> None:
    agent = valid_agent(baseUnmodeled=[{"label": "锐暴伤害", "value": 150}])
    write(data_dir, "catalog/agents.json", [agent])
    with pytest.raises(loader.PresetLoadError, match="校验失败"):
        loader.load_agents()


# ------------------------------------------------------------------ 加载与 HTTP


def test_missing_file_reports_how_to_generate(
    data_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """磁盘上没有数据、编译产物也没有时，错误要指向重新生成的命令。"""
    monkeypatch.setattr(loader, "_EMBEDDED_MODULE", "zzz_panel._no_such_module")
    monkeypatch.setattr(loader, "_EMBEDDED", {})
    with pytest.raises(loader.PresetLoadError, match="bundle_worker_data"):
        loader.load_agents()


def test_invalid_json_reports_file_name(data_dir: Path) -> None:
    path = data_dir / "catalog" / "agents.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{ not json", encoding="utf-8")
    with pytest.raises(loader.PresetLoadError, match="不是合法 JSON"):
        loader.load_agents()


def test_broken_data_returns_503_not_500(data_dir: Path) -> None:
    """数据源坏了不是「代码崩了」，前端据此展示「预设不可用」。"""
    write(data_dir, "catalog/agents.json", [valid_agent(roleTag="avigator")])
    resp = client.get("/api/presets/agents")
    assert resp.status_code == 503
    assert "roleTag" in resp.json()["detail"]


def test_endpoints_are_wired_into_openapi() -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/presets/agents" in paths
    assert "/api/presets/weapons" in paths
