"""面板口径「专武」的守护测试。

面板口径固定为 **0 影画 + 专武**（见 ``docs/design/calculation-rules.md`` §0）。
「专武」在数据里靠音擎的两列 Wiki 直读字段认：

- ``limited`` —— 「获取途径 = 限定调频」，即该音擎是某位代理人的专属音擎；
- ``recommendedAgents`` —— Wiki 音擎页「推荐代理人」列。

**只看推荐列表是不够的**：常驻音擎也会被推荐给若干代理人（那是推荐搭配，
不是专武）。所以判定必须两者取交集。

这里守三件事：
1. 限定音擎的推荐列表非空，且推荐的人都是真实代理人；
2. 每位已收录的代理人至少有一把 Wiki 推荐音擎（面板的兜底口径可用）；
3. 专武候选是推荐列表的**子集**（限定 ⊆ 推荐）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend" / "src"))

from zzz_panel.presets.loader import (  # noqa: E402
    load_agents,
    load_weapons,
    recommended_weapon_ids,
    signature_weapon_ids,
)


@pytest.fixture(scope="module")
def weapons():
    return load_weapons()


@pytest.fixture(scope="module")
def agent_ids() -> set[str]:
    return {agent.id for agent in load_agents()}


def test_limited_engines_have_recommended_agents(weapons) -> None:
    limited = [weapon for weapon in weapons if weapon.limited]
    assert limited, "没有任何限定调频音擎——抓取脚本的 limited 判据可能坏了"
    for weapon in limited:
        assert weapon.recommended_agents, f"{weapon.name} 标为限定，却没有推荐代理人"


def test_recommended_agents_resolve_to_real_agents(weapons, agent_ids: set[str]) -> None:
    """推荐列里的条目必须能解析成真实代理人。

    允许「旧条目 id + 正确中文名」的情况（伊芙琳在 Wiki 推荐列里是
    ``ep-1124``，规范条目是 ``ep-1158``）——解析器按 id 优先、名字兜底。
    """
    from zzz_panel.presets.loader import _agent_resolver, _resolve_agent

    resolver = _agent_resolver()
    for weapon in weapons:
        for agent in weapon.recommended_agents:
            resolved = _resolve_agent(agent.id, agent.name, resolver)
            assert resolved in agent_ids, (
                f"{weapon.name} 推荐了 {agent.name}（{agent.id}），"
                "它既不在 data/catalog/agents.json 里，也匹配不上任何已知中文名"
            )


def test_every_agent_has_a_recommended_weapon(agent_ids: set[str]) -> None:
    missing = [
        agent_id
        for agent_id in sorted(agent_ids)
        if not recommended_weapon_ids(agent_id)
    ]
    assert not missing, f"这些代理人没有任何 Wiki 推荐音擎：{missing}"


def test_signature_is_a_subset_of_recommended(agent_ids: set[str]) -> None:
    for agent_id in sorted(agent_ids):
        signature = set(signature_weapon_ids(agent_id))
        recommended = set(recommended_weapon_ids(agent_id))
        assert signature <= recommended, (
            f"{agent_id} 的专属音擎 {sorted(signature)} 不在推荐列表 {sorted(recommended)} 内"
        )


def test_limited_flag_matches_acquisition_source() -> None:
    """``limited`` 必须真的来自「获取途径 = 限定调频」，不能是手填的。

    抽查几件音擎的 Wiki 页面原文：限定的那几把写着「获取途径：限定调频」，
    常驻的那几把写着「获取途径：常驻调频」。
    """
    raw = (REPO_ROOT / "data" / "catalog" / "weapons.json").read_text(encoding="utf-8")
    payload = json.loads(raw)
    by_id = {item["id"]: item for item in payload}
    assert by_id["ep-1751"]["limited"] is True, "云霓孤光是叶瞬光的限定音擎"
    assert by_id["ep-219"]["limited"] is False, "拘缚者是常驻调频，不是专武"
    assert by_id["ep-1463"]["limited"] is True, "狸法七变化是限定音擎"
