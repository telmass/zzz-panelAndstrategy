"""API 契约测试（第 3 步验收项 13）。

只测 HTTP 层的形状与校验，数值正确性由 ``test_legacy_parity.py`` 负责。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from zzz_panel.api.app import app

client = TestClient(app)

MINIMAL = {"mode": "standard"}


def test_health() -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_empty_request_returns_twelve_rows() -> None:
    resp = client.post("/api/panel/calc", json=MINIMAL)
    assert resp.status_code == 200
    data = resp.json()

    assert data["mode"] == "standard"
    assert set(data["totals"]) == {
        "hp", "atk", "def", "cr", "cd", "dmg", "pr", "pv", "am", "ac", "imp", "er",
    }
    # 通用模式没有专属字段
    assert data["modeStats"] == {}
    assert data["blastDmg"] is None
    assert "penforce" not in data["breakdown"]
    assert "actual_cr" not in data["breakdown"]
    # 驱动盘 1/2/3 固定主词条恒定生效，因此始终有这三条来源；
    # 副词条与二件套未选时不应有其它来源。
    assert set(data["sources"]) == {"hp_flat", "atk_flat", "def_flat"}


def test_def_alias_is_accepted() -> None:
    """请求里用 JSON 键名 def（Python 侧是 def_ 关键字规避）。"""
    resp = client.post("/api/panel/calc", json={**MINIMAL, "base": {"hp": 1000, "def": 300}})
    assert resp.status_code == 200
    # 300 + 驱动盘 3 号固定防御 184
    assert resp.json()["totals"]["def"] == pytest.approx(484.0)


def test_disc_fixed_stats_are_always_applied() -> None:
    resp = client.post("/api/panel/calc", json=MINIMAL)
    totals = resp.json()["totals"]
    assert totals["hp"] == pytest.approx(8000 + 2200)
    assert totals["atk"] == pytest.approx(1000 + 316)
    assert totals["def"] == pytest.approx(600 + 184)


def test_rupture_mode_adds_penetration_force() -> None:
    resp = client.post("/api/panel/calc", json={**MINIMAL, "mode": "rupture"})
    data = resp.json()
    assert "penforce" in data["modeStats"]
    assert data["breakdown"]["penforce"]
    assert data["blastDmg"] is None


def test_fengyu_mode_adds_actual_crit_and_blast_damage() -> None:
    resp = client.post("/api/panel/calc", json={**MINIMAL, "mode": "fengyu"})
    data = resp.json()
    assert data["blastDmg"] == pytest.approx(150.0)
    assert data["modeStats"]
    # breakdown 的键是结果行键（与前端 ResultRow.key 对齐），保持 snake_case，
    # 不参与响应的 camelCase 转换
    assert data["breakdown"]["blast_dmg"]


def test_unknown_mode_is_rejected() -> None:
    assert client.post("/api/panel/calc", json={**MINIMAL, "mode": "nope"}).status_code == 422


def test_breakdown_segments_are_renderable() -> None:
    """明细片段只允许四种类型，且每行至少一个片段。"""
    resp = client.post(
        "/api/panel/calc",
        json={
            **MINIMAL,
            "core": {"core1": "cr", "core2": "cd"},
            "sub_stats": {"cr": 6},
            "sets": {"set0": "atk_pct_10"},
        },
    )
    data = resp.json()
    allowed = {"text", "kw", "num", "sources"}

    for row, lines in data["breakdown"].items():
        assert lines, f"{row} 明细为空"
        for line in lines:
            assert line["type"] == "line"
            assert line["parts"], f"{row} 存在空片段行"
            for part in line["parts"]:
                assert part["type"] in allowed
                if part["type"] == "sources":
                    assert isinstance(part["items"], list)


def test_negative_sub_stat_count_is_ignored() -> None:
    resp = client.post(
        "/api/panel/calc",
        json={**MINIMAL, "base": {"cr": 0}, "sub_stats": {"cd": -5}},
    )
    assert resp.status_code == 200
    assert "cd" not in resp.json()["sums"]


def test_fractional_sub_stat_count_is_rejected() -> None:
    """前端钳制后只发整数；后端不做 float→int 静默截断，避免掩盖上游 bug。"""
    resp = client.post("/api/panel/calc", json={**MINIMAL, "sub_stats": {"cr": 3.9}})
    assert resp.status_code == 422


def test_sub_stat_count_is_floored_at_core_layer() -> None:
    """向下取整发生在 core 层：前端传小数也不会被静默接受。"""
    from zzz_panel.core.modifiers import PanelSelection, build_modifiers

    modifiers = build_modifiers(PanelSelection(sub_stats={"cr": 3.9}))
    assert modifiers.sums["cr"] == pytest.approx(3 * 2.4)


def test_weapon_base_def_only_affects_def() -> None:
    resp = client.post(
        "/api/panel/calc",
        json={**MINIMAL, "weapon": {"base_kind": "def", "base_value": 500}},
    )
    totals = resp.json()["totals"]
    assert totals["def"] == pytest.approx(600 + 500 + 184)
    assert totals["atk"] == pytest.approx(1000 + 316)


def test_cors_allows_vite_dev_server() -> None:
    resp = client.options(
        "/api/panel/calc",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "http://localhost:5173"
