"""数据集登记表 ``data/manifest.json`` 的守护测试。

登记表是**数据集路径的唯一真实源**。这份测试守三件事：

1. 登记的每个数据集都真实存在，且条目数与 ``count`` 一致；
2. ``data/`` 下没有未登记的文件——某个工具偷偷往里写文件会在这里被发现；
3. 内容摘要与登记的 ``sha256`` 一致——数据改了但没同步登记表时会被发现。

前端侧的「静态导入 = 登记项」由 ``frontend/tests/data-manifest.spec.ts`` 断言：
后端能读登记表，前端不能（Vite 的静态导入要求路径可静态分析），两边合起来
才覆盖全部消费者。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
MANIFEST_PATH = DATA_DIR / "manifest.json"


@pytest.fixture(scope="module")
def manifest() -> dict:
    assert MANIFEST_PATH.is_file(), (
        f"缺少 {MANIFEST_PATH.name}。仓库根 data/ 下的数据集必须在此登记。"
    )
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _count_items(payload: object) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        return sum(len(value) for value in payload.values() if isinstance(value, list))
    return 0


def test_every_registered_dataset_exists(manifest: dict) -> None:
    for name, entry in manifest["datasets"].items():
        path = DATA_DIR / entry["path"]
        assert path.is_file(), f"数据集 {name} 登记的路径不存在：{path}"


def test_counts_match_the_files(manifest: dict) -> None:
    for name, entry in manifest["datasets"].items():
        payload = json.loads((DATA_DIR / entry["path"]).read_text(encoding="utf-8"))
        assert _count_items(payload) == entry["count"], (
            f"数据集 {name} 的条目数与登记的 count 不一致，"
            "运行 `python tools/sync_manifest.py` 刷新"
        )


def test_digests_match_the_files(manifest: dict) -> None:
    for name, entry in manifest["datasets"].items():
        digest = hashlib.sha256((DATA_DIR / entry["path"]).read_bytes()).hexdigest()
        assert digest == entry["sha256"], (
            f"数据集 {name} 的内容与登记的 sha256 不一致，"
            "运行 `python tools/sync_manifest.py` 刷新"
        )


def test_no_orphan_files_in_data_dir(manifest: dict) -> None:
    """``data/`` 下不该出现未登记的文件。

    白名单只留登记表与说明文档。某个工具把产物直接写进 ``data/`` 而忘了
    登记，会在这里被点名。
    """
    registered = {entry["path"] for entry in manifest["datasets"].values()}
    allowed = {"manifest.json", "README.md"}
    orphans = [
        path.relative_to(DATA_DIR).as_posix()
        for path in sorted(DATA_DIR.rglob("*"))
        if path.is_file()
        and path.relative_to(DATA_DIR).as_posix() not in registered
        and path.relative_to(DATA_DIR).as_posix() not in allowed
    ]
    assert not orphans, f"data/ 下有未登记的文件：{orphans}"


def test_role_and_maintenance_are_declared(manifest: dict) -> None:
    """每个数据集都要说清「是真源还是产物」「谁维护它」。

    ``generator`` 指**产出这个文件的东西**：抓取脚本产出的源数据有
    generator；手写的文件（``maintained: manual``）没有。
    """
    for name, entry in manifest["datasets"].items():
        assert entry["role"] in ("source", "generated"), f"{name} 的 role 非法"
        assert entry["maintained"] in ("skill", "manual", "code"), f"{name} 的 maintained 非法"
        if entry["maintained"] == "manual":
            assert not entry["generator"], f"{name} 是手写的，不该有 generator"
        else:
            assert entry["generator"], f"{name} 必须写明由谁产出"


def test_worker_datasets_have_a_stable_constant_name(manifest: dict) -> None:
    """要编译进 Worker 的数据集，常量名由 id 推导。

    推导规则写在两处（打包脚本与后端 loader），这里钉住它：改了一处忘了
    另一处，线上会 503。
    """
    from zzz_panel.presets.manifest import worker_constant

    for name, entry in manifest["datasets"].items():
        if entry.get("worker"):
            assert worker_constant(name) == f"{name.upper()}_JSON"


def test_strategy_block_points_at_the_index(manifest: dict) -> None:
    """攻略数据树根与索引数据集必须登记。"""
    strategy = manifest["strategy"]
    assert strategy["root"] == "strategy"
    assert strategy["indexDataset"] in manifest["datasets"]
    assert (REPO_ROOT / strategy["root"]).is_dir()
