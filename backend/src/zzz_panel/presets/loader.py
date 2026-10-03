"""预设数据加载。

唯一真实源是仓库根 ``data/*.json``（由 ``tools/sync_presets.py`` 维护）。
本模块负责读盘、结构与语义校验、按 mtime 缓存，并把 ``ValidationError``
与 ``PresetValidationError`` 一律转成 ``PresetLoadError``——让路由层只需
处理一种异常。

缓存按 mtime 而非 TTL：开发时改 JSON 立刻生效，同时避免每次请求都读盘解析
160 条预设。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..schemas.presets import AgentPreset, WeaponPreset
from .validate import PresetValidationError, validate_agents, validate_weapons


class PresetLoadError(RuntimeError):
    """预设数据缺失、无法解析或不满足校验规则。"""


#: 仓库根的标记文件。用来区分「源码树内的可编辑安装」与「装进 site-packages
#: 的发行版」——后者按 ``__file__`` 上溯会跑到 site-packages 里找不到数据。
_REPO_MARKER = "pyproject.toml"

_data_dir: Path | None = None


def data_dir() -> Path:
    """返回预设数据目录。

    默认是仓库根下的 ``data/``。允许用环境变量 ``ZZZ_PANEL_DATA_DIR`` 覆盖，
    测试用它指向临时目录。结果缓存，避免每次请求都上溯目录。
    """
    global _data_dir
    if _data_dir is not None:
        return _data_dir

    override = os.environ.get("ZZZ_PANEL_DATA_DIR")
    if override:
        _data_dir = Path(override)
        return _data_dir

    for parent in Path(__file__).resolve().parents:
        if (parent / _REPO_MARKER).is_file() and (parent / "data").is_dir():
            _data_dir = parent / "data"
            return _data_dir

    raise PresetLoadError(
        "找不到预设数据目录。请在仓库根运行，或用 ZZZ_PANEL_DATA_DIR 指定 data/ 路径。"
    )


class _Cache:
    """按 (路径, mtime, 大小) 判定的单文件缓存。"""

    def __init__(self) -> None:
        self._stamp: tuple[int, int] | None = None
        self._value: Any = None

    def get(self, path: Path, build) -> Any:
        try:
            stat = path.stat()
        except FileNotFoundError:
            # 交给 build 抛出带修复指引的 PresetLoadError，而不是裸的
            # FileNotFoundError；此时不写缓存，下次调用会重新尝试。
            self._stamp, self._value = None, None
            return build()
        stamp = (stat.st_mtime_ns, stat.st_size)
        if stamp != self._stamp:
            self._value = build()
            self._stamp = stamp
        return self._value


_AGENTS = _Cache()
_WEAPONS = _Cache()


def _read(path: Path) -> Any:
    if not path.exists():
        raise PresetLoadError(
            f"缺少预设数据文件 {path}。运行 `python tools/sync_presets.py --from-legacy` 生成。"
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise PresetLoadError(f"{path.name} 不是合法 JSON：{error}") from error


def _build_agents(path: Path) -> list[AgentPreset]:
    raw = _read(path)
    if not isinstance(raw, list):
        raise PresetLoadError(f"{path.name} 顶层应为数组，实际为 {type(raw).__name__}")
    try:
        agents = [AgentPreset.model_validate(item) for item in raw]
    except ValidationError as error:
        raise PresetLoadError(f"{path.name} 结构校验失败：{error}") from error
    try:
        validate_agents(agents)
    except PresetValidationError as error:
        raise PresetLoadError(f"{path.name} 语义校验失败：{error}") from error
    return agents


def _build_weapons(path: Path) -> list[WeaponPreset]:
    raw = _read(path)
    if not isinstance(raw, list):
        raise PresetLoadError(f"{path.name} 顶层应为数组，实际为 {type(raw).__name__}")
    try:
        weapons = [WeaponPreset.model_validate(item) for item in raw]
    except ValidationError as error:
        raise PresetLoadError(f"{path.name} 结构校验失败：{error}") from error
    try:
        validate_weapons(weapons)
    except PresetValidationError as error:
        raise PresetLoadError(f"{path.name} 语义校验失败：{error}") from error
    return weapons


def load_agents() -> list[AgentPreset]:
    """全部代理人预设。数据非法时抛 :class:`PresetLoadError`。"""
    path = data_dir() / "agent-presets.json"
    return _AGENTS.get(path, lambda: _build_agents(path))


def load_weapons() -> list[WeaponPreset]:
    """全部音擎预设。数据非法时抛 :class:`PresetLoadError`。"""
    path = data_dir() / "weapon-presets.json"
    return _WEAPONS.get(path, lambda: _build_weapons(path))


__all__ = ["PresetLoadError", "data_dir", "load_agents", "load_weapons"]