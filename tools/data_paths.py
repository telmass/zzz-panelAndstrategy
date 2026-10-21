"""数据集路径解析——``data/manifest.json`` 的唯一读取入口。

为什么需要这一层
----------------
仓库根 ``data/`` 下的数据集被 **后端运行时**、**前端构建期**、**开发工具** 与
**Skill 抓取脚本** 四类消费者读取。路径若各写各的，改一次要动十几个文件，且
漏改的那个只会静默读到旧路径或直接 404。

因此把「数据集在哪」收敛到 ``data/manifest.json`` 一处声明，各消费者从这里取。
本模块**零第三方依赖**，以便 Skill 抓取脚本用系统 ``python`` 直接跑。

两种消费方式
------------
- **Python（后端与工具）**：运行时读 manifest，路径永远同步。
- **TypeScript（前端）**：静态 ``import`` 读数据文件本身（Vite 需要可静态分析
  的导入路径），manifest 仅作为**漂移参照**——``backend/tests/test_data_manifest.py``
  会断言静态导入的文件与 manifest 登记的一致，漏改时指名道姓地失败。

刻意**不**在前端用 ``import(\\`@data/${path}\\`)` 动态拼路径：Vite 的动态导入
要求可静态分析的 glob，别名 + JSON 的组合不可靠。静态导入 + 漂移测试是更稳的
等价物。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

#: 仓库根。本文件位于 ``tools/`` 下，故上溯一层。
REPO_ROOT = Path(__file__).resolve().parent.parent

#: 数据根目录。所有数据集路径都相对它。
DATA_DIR = REPO_ROOT / "data"

#: 登记表本体。
MANIFEST_PATH = DATA_DIR / "manifest.json"

#: 攻略数据树根（每个 slug 一个目录，内含 ``data/``）。
STRATEGY_ROOT = REPO_ROOT / "strategy"


class ManifestError(RuntimeError):
    """manifest 缺失、格式非法，或请求了未登记的数据集。"""


def load_manifest() -> dict[str, Any]:
    """读取并返回 manifest 原文。"""
    if not MANIFEST_PATH.is_file():
        raise ManifestError(
            f"缺少数据集登记表 {MANIFEST_PATH}。仓库根 data/ 下的数据集必须在此登记。"
        )
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ManifestError(f"{MANIFEST_PATH} 不是合法 JSON：{error}") from error
    if not isinstance(data, dict) or "datasets" not in data:
        raise ManifestError(f"{MANIFEST_PATH} 缺少 datasets 字段")
    return data


def dataset_ids() -> list[str]:
    """已登记的数据集 id 列表。"""
    return sorted(load_manifest()["datasets"])


def dataset_entry(name: str) -> dict[str, Any]:
    """单个数据集的登记条目。"""
    datasets = load_manifest()["datasets"]
    if name not in datasets:
        raise ManifestError(
            f"数据集 {name!r} 未在 {MANIFEST_PATH.name} 中登记。"
            f"已登记：{sorted(datasets)}"
        )
    return datasets[name]


def dataset_path(name: str) -> Path:
    """数据集文件的绝对路径。"""
    entry = dataset_entry(name)
    return DATA_DIR / entry["path"]


def dataset_rel_path(name: str) -> str:
    """数据集文件相对仓库根的路径，用于日志与报错信息。"""
    return dataset_path(name).relative_to(REPO_ROOT).as_posix()


def strategy_dir(slug: str) -> Path:
    """某个代理人的攻略数据目录。"""
    return STRATEGY_ROOT / slug / "data"


def strategy_slugs() -> list[str]:
    """攻略数据树里登记在册的 slug（读 ``agent-index``）。"""
    index = json.loads(dataset_path("agent-index").read_text(encoding="utf-8"))
    return [item["slug"] for item in index]


def worker_constant(name: str) -> str:
    """数据集在 Worker 编译产物里的常量名。

    由 id 推导（``agents`` → ``AGENTS_JSON``），**不另存一份映射**——打包脚本
    与后端 loader 用同一条推导规则。后端那条在
    ``zzz_panel.presets.manifest.worker_constant``，两侧是否一致由
    ``backend/tests/test_worker_bundle.py`` 断言。
    """
    return f"{name.upper()}_JSON"


__all__ = [
    "DATA_DIR",
    "MANIFEST_PATH",
    "REPO_ROOT",
    "STRATEGY_ROOT",
    "ManifestError",
    "dataset_entry",
    "dataset_ids",
    "dataset_path",
    "dataset_rel_path",
    "load_manifest",
    "strategy_dir",
    "strategy_slugs",
    "worker_constant",
]
