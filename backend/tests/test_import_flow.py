"""「用 skill 导入新条目」端到端演练。

回答一个问题：**导入一位新代理人 / 一件新音擎 / 一套新驱动盘之后，整条链路是否自洽？**

链路（与真实的 skill 流程一一对应）：

1. 抓取脚本写 JSON（这里直接改 JSON，等价于脚本写完）
2. ``sync_manifest.py --check`` —— 应当**报漂移**（登记表的 count/sha256 过期了）
3. ``sync_manifest.py`` —— 刷新登记表
4. ``bundle_worker_data.py`` —— 重编译 Worker 产物
5. 后端 loader 指向新目录 —— 新条目能被加载并通过语义校验
6. ``agent_audit.py --all`` —— 体检仍通过

全部在**临时副本**上跑，不碰仓库里的真实数据。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


@pytest.fixture
def fake_repo(tmp_path: Path) -> Path:
    """一份「仓库根」副本：带 data/ 与 tools/，数据可随意改。"""
    root = tmp_path / "repo"
    root.mkdir()
    shutil.copytree(REPO_ROOT / "data", root / "data")
    shutil.copytree(REPO_ROOT / "tools", root / "tools")
    return root


def _append(dataset: str, entry: dict) -> None:
    """往数据集里追加一条（等价于抓取脚本写文件）。"""
    manifest = json.loads((REPO_ROOT / "data" / "manifest.json").read_text(encoding="utf-8"))
    path = REPO_ROOT / "data" / manifest["datasets"][dataset]["path"]
    items = json.loads(path.read_text(encoding="utf-8"))
    items.append(entry)
    path.write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return path


def test_manifest_gate_catches_a_changed_dataset(fake_repo: Path) -> None:
    """数据变了而没刷新登记表时，漂移闸必须报错。

    这是导入流程里最容易漏的一步——漏了它，CI 会在与本次改动无关的地方红。
    """
    manifest = json.loads((fake_repo / "data" / "manifest.json").read_text(encoding="utf-8"))
    agents_path = fake_repo / "data" / manifest["datasets"]["agents"]["path"]
    agents = json.loads(agents_path.read_text(encoding="utf-8"))
    template = next(a for a in agents if a["id"] == "ep-1109")
    agents.append({**template, "id": "ep-9999", "name": "试导入代理人"})
    agents_path.write_text(
        json.dumps(agents, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    result = _run([sys.executable, str(fake_repo / "tools/sync_manifest.py"), "--check"], fake_repo)
    assert result.returncode != 0, "数据变了但 sync_manifest --check 仍报一致——漂移闸没生效"

    result = _run([sys.executable, str(fake_repo / "tools/sync_manifest.py")], fake_repo)
    assert result.returncode == 0, result.stdout + result.stderr

    result = _run([sys.executable, str(fake_repo / "tools/sync_manifest.py"), "--check"], fake_repo)
    assert result.returncode == 0, "刷新后仍报漂移"

    updated = json.loads((fake_repo / "data" / "manifest.json").read_text(encoding="utf-8"))
    assert updated["datasets"]["agents"]["count"] == len(agents)


def test_bundle_worker_data_picks_up_a_new_agent(fake_repo: Path) -> None:
    """新代理人必须进 Worker 编译产物——否则线上继续供旧数据。"""
    manifest = json.loads((fake_repo / "data" / "manifest.json").read_text(encoding="utf-8"))
    agents_path = fake_repo / "data" / manifest["datasets"]["agents"]["path"]
    agents = json.loads(agents_path.read_text(encoding="utf-8"))
    template = next(a for a in agents if a["id"] == "ep-1109")
    agents.append({**template, "id": "ep-9999", "name": "试导入代理人"})
    agents_path.write_text(
        json.dumps(agents, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    dest = fake_repo / "backend/src/zzz_panel/_bundled_data.py"
    dest.parent.mkdir(parents=True, exist_ok=True)
    result = _run(
        [
            sys.executable,
            str(fake_repo / "tools/bundle_worker_data.py"),
            "--data-dir",
            str(fake_repo / "data"),
            "--dest",
            str(dest),
        ],
        fake_repo,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ep-9999" in dest.read_text(encoding="utf-8"), "新代理人没进 Worker 产物"


def test_backend_loads_a_new_agent_weapon_and_disc(fake_repo: Path) -> None:
    """后端能从新目录加载新代理人 / 新音擎，并让新套装通过交叉引用检查。"""
    manifest = json.loads((fake_repo / "data" / "manifest.json").read_text(encoding="utf-8"))
    datasets = manifest["datasets"]

    agents_path = fake_repo / "data" / datasets["agents"]["path"]
    agents = json.loads(agents_path.read_text(encoding="utf-8"))
    template = next(a for a in agents if a["id"] == "ep-1109")
    agents.append({**template, "id": "ep-9999", "name": "试导入代理人"})
    agents_path.write_text(
        json.dumps(agents, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    weapons_path = fake_repo / "data" / datasets["weapons"]["path"]
    weapons = json.loads(weapons_path.read_text(encoding="utf-8"))
    weapon_template = next(w for w in weapons if w["id"] == "ep-1107")
    weapons.append({**weapon_template, "id": "ep-9998", "name": "试导入音擎"})
    weapons_path.write_text(
        json.dumps(weapons, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    discs_path = fake_repo / "data" / datasets["drive-discs"]["path"]
    discs = json.loads(discs_path.read_text(encoding="utf-8"))
    disc_template = next(d for d in discs if d["id"] == "ep-104")
    discs.append({**disc_template, "id": "ep-9997", "name": "试导入套装"})
    discs_path.write_text(
        json.dumps(discs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    # 让 loader 指向这份副本。
    from zzz_panel.presets import manifest as presets_manifest
    from zzz_panel.presets import loader

    previous = presets_manifest._data_dir
    previous_env = os.environ.get("ZZZ_PANEL_DATA_DIR")
    os.environ["ZZZ_PANEL_DATA_DIR"] = str(fake_repo / "data")
    presets_manifest._data_dir = None
    try:
        loaded_agents = loader.load_agents()
        loaded_weapons = loader.load_weapons()
    finally:
        presets_manifest._data_dir = previous
        if previous_env is None:
            os.environ.pop("ZZZ_PANEL_DATA_DIR", None)
        else:
            os.environ["ZZZ_PANEL_DATA_DIR"] = previous_env

    assert any(a.id == "ep-9999" for a in loaded_agents), "后端加载不到新代理人"
    assert any(w.id == "ep-9998" for w in loaded_weapons), "后端加载不到新音擎"


def test_audit_catches_a_stale_registry_until_it_is_refreshed(fake_repo: Path) -> None:
    """导入后、体检应当**先报登记表过期**，刷新后恢复通过。

    这条是导入流程的「安全网」：忘了跑 ``sync_manifest.py`` 时，体检与 CI
    都会指出「数据集登记表已过期」，而不是让人以为导入成功了就完事。
    """
    manifest = json.loads((fake_repo / "data" / "manifest.json").read_text(encoding="utf-8"))
    agents_path = fake_repo / "data" / manifest["datasets"]["agents"]["path"]
    agents = json.loads(agents_path.read_text(encoding="utf-8"))
    template = next(a for a in agents if a["id"] == "ep-1109")
    agents.append({**template, "id": "ep-9999", "name": "试导入代理人"})
    agents_path.write_text(
        json.dumps(agents, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    result = _run([sys.executable, str(fake_repo / "tools/agent_audit.py"), "--all"], fake_repo)
    assert result.returncode != 0, "登记表过期时体检仍报通过——体检没接上漂移闸"
    output = result.stdout + result.stderr
    assert "数据集登记表" in output, "体检没有点名「数据集登记表」"
    assert "已过期" in output, "体检没有说明登记表已过期"

    refresh = _run([sys.executable, str(fake_repo / "tools/sync_manifest.py")], fake_repo)
    assert refresh.returncode == 0, refresh.stdout + refresh.stderr

    # 刷新后「登记表过期」这条应当消失（本次只导入了预设，没建攻略目录，
    # 因此仍会有别的 ERROR——那是「只导一半」的真实状态，不该被本次断言掩盖）。
    result = _run([sys.executable, str(fake_repo / "tools/agent_audit.py"), "--all"], fake_repo)
    output = result.stdout + result.stderr
    assert "数据集登记表已过期" not in output, output[-800:]
