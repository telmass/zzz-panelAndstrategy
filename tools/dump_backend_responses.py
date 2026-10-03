"""导出后端 /api/panel/calc 的响应，供前端对拍诊断脚本比对。

场景定义与 backend/tests/legacy_cases.json 一致（默认空配置 / 满配 / 命破 / 锋御），
这样能与 tools/dump_legacy_cases.mjs 的产物直接对齐。

用法：uv run python tools/dump_backend_responses.py <输出路径>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend" / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from zzz_panel.api.app import app  # noqa: E402

# ep-211 防暴者Ⅵ型：S 级强攻，基础攻击 713 + 暴击伤害 48%
EP211_SUB = {"target": "cd", "value": 48, "kind": "pct", "label": "暴击伤害"}

FULL = {
    "mode": "standard",
    "base": {
        "hp": 8000, "atk": 1000, "def": 600, "impact": 90,
        "cr": 5, "cd": 50, "ac": 100, "am": 100, "pr": 0, "er": 1.2,
    },
    "weapon": {"baseKind": "atk", "baseValue": 713, "substat": EP211_SUB},
    "core": {"core1": "cr", "core2": "cd"},
    "discMain": {"disc4": "atk_pct_30", "disc5": "dmg_30", "disc6": "impact_pct_24"},
    "subStats": {"hp_flat": 12, "atk_pct": 7, "def_flat": 5, "cr": 9, "cd": 4, "pen_val": 6, "am": 11},
    "sets": {"set0": "atk_pct_10", "set1": "cd_16", "set2": "er_pct_20"},
}

EP1299 = {
    "mode": "rupture",
    "base": {
        "hp": 7953, "atk": 872, "def": 441, "impact": 93,
        "cr": 5, "cd": 50, "ac": 92, "am": 90, "pr": 0, "er": 0,
    },
    "weapon": {"baseKind": "atk", "baseValue": 0, "substat": None},
    "core": {"core1": "cr", "core2": "hp_base"},
    "discMain": {"disc4": "", "disc5": "", "disc6": ""},
    "subStats": {},
    "sets": {"set0": "", "set1": "", "set2": ""},
}

EP2145 = {
    "mode": "fengyu",
    "base": {
        "hp": 5651, "atk": 626, "def": 441, "impact": 93,
        "cr": 22.5, "cd": 50, "ac": 80, "am": 79, "pr": 0, "er": 1.5,
    },
    "weapon": {"baseKind": "atk", "baseValue": 0, "substat": None},
    "core": {"core1": "cr", "core2": "cr"},
    "discMain": {"disc4": "", "disc5": "", "disc6": ""},
    "subStats": {},
    "sets": {"set0": "", "set1": "", "set2": ""},
}

CASES = {
    "empty": {"mode": "standard"},
    "full": FULL,
    "ep-1299": EP1299,
    "ep-2145": EP2145,
}


def main() -> None:
    out_path = Path(sys.argv[1])
    client = TestClient(app)
    payload = {name: client.post("/api/panel/calc", json=body).json() for name, body in CASES.items()}
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("scenarios:", ", ".join(payload))


if __name__ == "__main__":
    main()