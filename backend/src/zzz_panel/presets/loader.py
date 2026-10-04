"""预设数据加载。

唯一真实源是仓库根 ``data/*.json``（由 ``tools/sync_presets.py`` 维护）。
本模块负责读盘、结构与语义校验、按 mtime 缓存，并把 ``ValidationError``
与 ``PresetValidationError`` 一律转成 ``PresetLoadError``——让路由层只需
处理一种异常。

缓存按 mtime 而非 TTL：开发时改 JSON 立刻生效，同时避免每次请求都读盘解析
160 条预设。

数据来源有两条，见 :func:`load_agents`：磁盘上的 ``data/``（定位顺序见
:func:`data_dir`），以及包内生成模块 ``zzz_panel/_bundled_data.py``。
后者只服务于 Cloudflare Worker——``pywrangler`` 只上传 ``.py``，磁盘与
``data/`` 都不会跟着上线。
"""

from __future__ import annotations

import importlib
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

_AGENTS_FILE = "agent-presets.json"
_WEAPONS_FILE = "weapon-presets.json"

_data_dir: Path | None = None


def data_dir() -> Path:
    """返回磁盘上预设数据所在的目录。

    依次尝试：

    1. 模块内缓存
    2. 环境变量 ``ZZZ_PANEL_DATA_DIR``
    3. 从 ``__file__`` 向上找同时含 ``pyproject.toml`` 与 ``data/`` 的祖先目录
    4. 都没有 → ``PresetLoadError``

    第 3 条覆盖仓库与普通 wheel 安装。注意本函数**不**返回 Worker 的包内
    编译产物——那不是一个目录，而是 :func:`_embedded_source` 里的模块常量。
    结果缓存，避免每次请求都上溯目录。
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

#: 生成模块的导入名（真值）。测试会把 :data:`_EMBEDDED_MODULE` 指向临时造的
#: 模块，因此默认值另存一份供断言——两侧一旦对不上，线上就是 503。
#:
#: 注意 ``__package__`` 在本模块里是 ``zzz_panel.presets``（本文件所在的包），
#: 不是包根，要往上剥一层。
_DEFAULT_EMBEDDED_MODULE = f"{__package__.rsplit('.', 1)[0]}._bundled_data"

#: 实际使用的导入名。可被测试替换，从而不依赖「本地是否生成过」这一环境状态。
_EMBEDDED_MODULE = _DEFAULT_EMBEDDED_MODULE

#: 源文件名 -> 生成模块里的常量名。
_EMBEDDED_ATTRS = {
    _AGENTS_FILE: "AGENTS_JSON",
    _WEAPONS_FILE: "WEAPONS_JSON",
}

#: 生成模块的解析结果。内容在进程内不变，缓存一次即可。
_EMBEDDED: dict[str, Any] = {}


def _read_text(path: Path) -> str:
    if not path.exists():
        raise PresetLoadError(
            f"缺少预设数据文件 {path}。运行 `python tools/sync_presets.py --from-legacy` 生成。"
        )
    return path.read_text(encoding="utf-8")


def _decode(name: str, text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise PresetLoadError(f"{name} 不是合法 JSON：{error}") from error


def _parse_agents(name: str, text: str) -> list[AgentPreset]:
    raw = _decode(name, text)
    if not isinstance(raw, list):
        raise PresetLoadError(f"{name} 顶层应为数组，实际为 {type(raw).__name__}")
    try:
        agents = [AgentPreset.model_validate(item) for item in raw]
    except ValidationError as error:
        raise PresetLoadError(f"{name} 结构校验失败：{error}") from error
    try:
        validate_agents(agents)
    except PresetValidationError as error:
        raise PresetLoadError(f"{name} 语义校验失败：{error}") from error
    return agents


def _parse_weapons(name: str, text: str) -> list[WeaponPreset]:
    raw = _decode(name, text)
    if not isinstance(raw, list):
        raise PresetLoadError(f"{name} 顶层应为数组，实际为 {type(raw).__name__}")
    try:
        weapons = [WeaponPreset.model_validate(item) for item in raw]
    except ValidationError as error:
        raise PresetLoadError(f"{name} 结构校验失败：{error}") from error
    try:
        validate_weapons(weapons)
    except PresetValidationError as error:
        raise PresetLoadError(f"{name} 语义校验失败：{error}") from error
    return weapons


def _filesystem_source(name: str) -> Path | None:
    """磁盘上的数据文件路径；定位不到目录或文件不存在时返回 ``None``。"""
    try:
        path = data_dir() / name
    except PresetLoadError:
        return None
    return path if path.is_file() else None


def _embedded_source(name: str) -> Any:
    """从生成模块里取预设数据，模块缺失时抛 :class:`PresetLoadError`。

    Cloudflare Worker 只有这一条路：``pywrangler`` 只上传 ``.py``，
    任何放在包里的 ``.json`` 都不会跟着上线。模块由
    ``tools/bundle_worker_data.py`` 从 ``data/`` 生成。
    """
    if name in _EMBEDDED:
        return _EMBEDDED[name]

    attr = _EMBEDDED_ATTRS[name]
    try:
        module = importlib.import_module(_EMBEDDED_MODULE)
    except ImportError as error:
        raise PresetLoadError(
            f"磁盘上没有 {name}，包内也没有编译产物（{_EMBEDDED_MODULE}）。"
            "请确认数据已生成（`python tools/sync_presets.py --from-legacy`）；"
            "部署 Cloudflare Worker 前运行 `python tools/bundle_worker_data.py`；"
            "或用 ZZZ_PANEL_DATA_DIR 指定含 agent-presets.json / weapon-presets.json 的目录。"
        ) from error

    text = getattr(module, attr, None)
    if text is None:
        raise PresetLoadError(f"{_EMBEDDED_MODULE} 缺少常量 {attr}，请重新生成。")

    parse = _parse_agents if name == _AGENTS_FILE else _parse_weapons
    value = parse(name, text)
    _EMBEDDED[name] = value
    return value


def load_agents() -> list[AgentPreset]:
    """全部代理人预设。数据非法时抛 :class:`PresetLoadError`。"""
    path = _filesystem_source(_AGENTS_FILE)
    if path is None:
        return _embedded_source(_AGENTS_FILE)
    return _AGENTS.get(path, lambda: _parse_agents(_AGENTS_FILE, _read_text(path)))


def load_weapons() -> list[WeaponPreset]:
    """全部音擎预设。数据非法时抛 :class:`PresetLoadError`。"""
    path = _filesystem_source(_WEAPONS_FILE)
    if path is None:
        return _embedded_source(_WEAPONS_FILE)
    return _WEAPONS.get(path, lambda: _parse_weapons(_WEAPONS_FILE, _read_text(path)))


__all__ = ["PresetLoadError", "data_dir", "load_agents", "load_weapons"]