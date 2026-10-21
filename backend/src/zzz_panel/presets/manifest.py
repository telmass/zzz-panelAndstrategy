"""数据集登记表（``data/manifest.json``）的读取。

登记���是**数据集路径的唯一真实源**。仓库根 ``data/`` 下的每个数据集都在
``manifest.json`` 里声明它的路径、角色（真源还是产物）、维护方式与分发形态；
后端运行时按 id 取路径，不再自己记文件名。

为什么不直接把文件名写成模块常量
--------------------------------
``data/`` 的文件曾散落在后端 loader、Worker 打包脚本、前端 Vite 配置、四个
Skill 抓取脚本等处，共十几处硬编码。改一次路径要动十几处，漏掉的那处只会
静默读到旧路径或 404。现在路径只写一处，其余消费者从 manifest 取。

前端是唯一例外：Vite 的静态导入要求路径可静态分析，故前端仍用字面量
``import`` 读数据文件本身，由 ``backend/tests/test_data_manifest.py`` 断言
「静态导入的文件 = manifest 登记的文件」，漏改时测试会指名道姓地失败。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

#: 仓库根的标记文件。用来区分「源码树内的可编辑安装」与「装进 site-packages
#: 的发行版」——后者按 ``__file__`` 上溯会跑到 site-packages 里找不到数据。
_REPO_MARKER = "pyproject.toml"

#: 登记表文件名，位于数据根目录下。
MANIFEST_FILENAME = "manifest.json"

_data_dir: Path | None = None


class ManifestError(RuntimeError):
    """登记表缺失、格式非法，或请求了未登记的数据集。"""


def data_dir() -> Path:
    """返回磁盘上预设数据所在的目录。

    依次尝试：

    1. 模块内缓存
    2. 环境变量 ``ZZZ_PANEL_DATA_DIR``
    3. 从 ``__file__`` 向上找同时含 ``pyproject.toml`` 与 ``data/manifest.json``
       的祖先目录
    4. 都没有 → :class:`ManifestError`

    第 3 条覆盖仓库与普通 wheel 安装。注意本函数**不**返回 Worker 的包内
    编译产物——那不是一个目录，而是 :func:`zzz_panel.presets.loader._embedded_source`
    里的模块常量。结果缓存，避免每次请求都上溯目录。
    """
    global _data_dir
    if _data_dir is not None:
        return _data_dir

    override = os.environ.get("ZZZ_PANEL_DATA_DIR")
    if override:
        _data_dir = Path(override)
        return _data_dir

    for parent in Path(__file__).resolve().parents:
        if (parent / _REPO_MARKER).is_file() and (
            parent / "data" / MANIFEST_FILENAME
        ).is_file():
            _data_dir = parent / "data"
            return _data_dir

    raise ManifestError(
        "找不到预设数据目录。请在仓库根运行，或用 ZZZ_PANEL_DATA_DIR 指定 data/ 路径。"
    )


def load_manifest() -> dict[str, Any]:
    """读取登记表原文。"""
    path = data_dir() / MANIFEST_FILENAME
    if not path.is_file():
        raise ManifestError(
            f"缺少数据集登记表 {path}。仓库根 data/ 下的数据集必须在此登记。"
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ManifestError(f"{path} 不是合法 JSON：{error}") from error
    if not isinstance(data, dict) or "datasets" not in data:
        raise ManifestError(f"{path} 缺少 datasets 字段")
    return data


def dataset_ids() -> list[str]:
    """已登记的数据集 id 列表。"""
    return sorted(load_manifest()["datasets"])


def dataset_entry(name: str) -> dict[str, Any]:
    """单个数据集的登记条目。"""
    datasets = load_manifest()["datasets"]
    if name not in datasets:
        raise ManifestError(
            f"数据集 {name!r} 未在 {MANIFEST_FILENAME} 中登记。已登记：{sorted(datasets)}"
        )
    return datasets[name]


def dataset_path(name: str) -> Path:
    """数据集文件的绝对路径。"""
    return data_dir() / dataset_entry(name)["path"]


def worker_constant(name: str) -> str:
    """数据集在 Worker 编译产物里的常量名。

    由 id 推导（``agents`` → ``AGENTS_JSON``），**不另存一份映射**——
    打包脚本与 loader 用同一条推导规则，两边不会对不上。
    """
    return f"{name.upper()}_JSON"


__all__ = [
    "MANIFEST_FILENAME",
    "ManifestError",
    "data_dir",
    "dataset_entry",
    "dataset_ids",
    "dataset_path",
    "load_manifest",
    "worker_constant",
]
