"""Cloudflare Worker 部署形态的测试。

两件互相独立、但缺一不可的事：

1. ``tools/bundle_worker_data.py`` 把 ``data/*.json`` **逐字节**编译进
   ``zzz_panel/_bundled_data.py``。这是 Worker 唯一能带上的数据形式——
   ``pywrangler`` 只上传 ``.py``，包里的 ``.json`` 会被静默丢弃。
2. ``presets/loader.py`` 在磁盘上没有 ``data/`` 时回退到该模块。

漂移的后果很隐蔽：页面能开、``/api/panel/calc`` 返回 200，但两个级联选择器
全空、``/api/presets/*`` 是 503。因此「编译产物与真实源逐字节一致」必须钉死。

两条都不需要真的构建或部署 Worker，也没有依赖本机是否生成过产物
（生成模块通过 :func:`fake_bundled` 现场伪造），因此没有 skip。
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

from zzz_panel.presets import loader

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))
bundle_worker_data = importlib.import_module("bundle_worker_data")

#: 生成模块里的常量名 -> 真实源文件名。
CONSTANTS = {value: key for key, value in bundle_worker_data.SOURCES.items()}


def compile_module(dest: Path, check: bool = False) -> int:
    return bundle_worker_data.sync(REPO_ROOT / "data", dest, check)


def load_generated(dest: Path) -> types.ModuleType:
    """把生成的 .py 当模块执行，拿到其中的常量。"""
    spec = importlib.util.spec_from_file_location("bundled_probe", dest)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------
# 编译脚本
# --------------------------------------------------------------------------


def test_generated_module_round_trips_source_bytes(tmp_path: Path) -> None:
    """逐字节一致：字面量拼接必须精确还原源文件，含末尾换行。"""
    dest = tmp_path / "_bundled_data.py"
    assert compile_module(dest) == 0

    module = load_generated(dest)
    for attr, name in CONSTANTS.items():
        source = (REPO_ROOT / "data" / name).read_bytes()
        assert getattr(module, attr).encode("utf-8") == source, name


def test_generated_module_is_valid_python(tmp_path: Path) -> None:
    """生成物要能通过编译检查——它会被当作普通模块被 Worker 导入。"""
    dest = tmp_path / "_bundled_data.py"
    compile_module(dest)
    compile(dest.read_text(encoding="utf-8"), str(dest), "exec")


def test_generation_is_idempotent(tmp_path: Path) -> None:
    dest = tmp_path / "_bundled_data.py"
    assert compile_module(dest) == 0
    first = dest.read_text(encoding="utf-8")

    assert compile_module(dest) == 0
    assert dest.read_text(encoding="utf-8") == first


def test_check_mode_flags_drift_without_writing(tmp_path: Path) -> None:
    dest = tmp_path / "_bundled_data.py"
    assert compile_module(dest) == 0
    assert compile_module(dest, check=True) == 0

    dest.write_text("# 过时了\n", encoding="utf-8")
    assert compile_module(dest, check=True) == 1
    # check 模式只报告，不修复。
    assert dest.read_text(encoding="utf-8") == "# 过时了\n"


def test_options_json_is_not_compiled(tmp_path: Path) -> None:
    """``options.json`` 由前端在构建期经 Vite 别名读真实源，不走后端，不该进产物。"""
    dest = tmp_path / "_bundled_data.py"
    compile_module(dest)
    text = dest.read_text(encoding="utf-8")

    assert "options.json" not in text
    assert set(CONSTANTS) == {"AGENTS_JSON", "WEAPONS_JSON"}


def test_default_module_name_matches_generator_output() -> None:
    """loader 里写死的那句 import 必须正好指向生成脚本的落点。

    这条曾真的错过一次：``__package__`` 在 ``presets/loader.py`` 里是
    ``zzz_panel.presets``，拼出来成了 ``zzz_panel.presets._bundled_data``，
    而文件在 ``zzz_panel/_bundled_data.py``。线上表现为 ``/api/presets/*``
    503，detail 里写着「找不到编译产物」——文件其实就在包里。
    """
    assert loader._DEFAULT_EMBEDDED_MODULE == "zzz_panel._bundled_data"
    assert bundle_worker_data.BUNDLED_MODULE == (
        REPO_ROOT / "backend" / "src" / "zzz_panel" / "_bundled_data.py"
    )
    assert (
        bundle_worker_data.BUNDLED_MODULE.stem
        == loader._DEFAULT_EMBEDDED_MODULE.rsplit(".", 1)[1]
    )


def test_missing_source_is_an_error(tmp_path: Path) -> None:
    empty = tmp_path / "data"
    empty.mkdir()
    assert bundle_worker_data.sync(empty, tmp_path / "out.py", check=False) == 1


# --------------------------------------------------------------------------
# loader 的编译产物回退分支
# --------------------------------------------------------------------------


def fake_bundled(
    monkeypatch: pytest.MonkeyPatch, agents: str = "[]", weapons: str = "[]"
) -> str:
    """现场伪造一个生成模块，并让 loader 指向它。

    不依赖本机是否真的跑过 ``bundle_worker_data.py``——否则「本地生成过」
    就会让本组用例在别人的机器上走出不同结果。
    """
    name = "zzz_panel_test_bundled"
    module = types.ModuleType(name)
    module.AGENTS_JSON = agents  # type: ignore[attr-defined]
    module.WEAPONS_JSON = weapons  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.setattr(loader, "_EMBEDDED_MODULE", name)
    monkeypatch.setattr(loader, "_EMBEDDED", {})
    return name


@pytest.fixture
def no_disk_data(monkeypatch: pytest.MonkeyPatch) -> None:
    """让磁盘这条路彻底走不通：既没有环境变量，也找不到仓库根。"""
    monkeypatch.delenv("ZZZ_PANEL_DATA_DIR", raising=False)
    monkeypatch.setattr(loader, "_REPO_MARKER", "no-such-marker.toml")
    monkeypatch.setattr(loader, "_data_dir", None)


def agent_item(name: str = "示例代理人") -> str:
    """一条**真实**预设（改个名字便于断言）。

    不手搓预设对象：校验规则有十几条（核心槽位恒为 2、每级数值一致、
    缺失的基础面板必须声明 unavailable……），手搓的样本极易过期。
    借用真源第一条，规则变化时本用例自动跟随。
    """
    items = json.loads(
        (REPO_ROOT / "data" / "agent-presets.json").read_text(encoding="utf-8")
    )
    item = dict(items[0])
    item["name"] = name
    return json.dumps([item], ensure_ascii=False)


def test_falls_back_to_compiled_module(
    no_disk_data: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_bundled(monkeypatch, agents=agent_item())
    assert [agent.name for agent in loader.load_agents()] == ["示例代理人"]


def test_compiled_module_data_is_validated_too(
    no_disk_data: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """编译产物走的是同一条校验链路，不是「反序列化完就直接返回」。"""
    fake_bundled(monkeypatch, agents=json.dumps([{"id": "ep-0001"}]))
    with pytest.raises(loader.PresetLoadError):
        loader.load_agents()


def test_compiled_module_survives_repeated_calls(
    no_disk_data: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_bundled(monkeypatch, agents=agent_item())
    assert loader.load_agents() == loader.load_agents()


def test_missing_module_names_the_generate_command(
    no_disk_data: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(loader, "_EMBEDDED_MODULE", "zzz_panel._no_such_module")
    monkeypatch.setattr(loader, "_EMBEDDED", {})
    with pytest.raises(loader.PresetLoadError) as error:
        loader.load_agents()
    assert "bundle_worker_data.py" in str(error.value)


def test_missing_constant_asks_for_regeneration(
    no_disk_data: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    name = fake_bundled(monkeypatch)
    delattr(sys.modules[name], "AGENTS_JSON")
    with pytest.raises(loader.PresetLoadError) as error:
        loader.load_agents()
    assert "AGENTS_JSON" in str(error.value)


def test_env_override_still_wins_over_compiled_module(
    no_disk_data: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """环境变量优先级最高：编译产物只是兜底，不能反过来盖掉显式配置。"""
    fake_bundled(monkeypatch, agents=agent_item("编译产物里的"))
    explicit = tmp_path / "explicit"
    explicit.mkdir()
    (explicit / "agent-presets.json").write_text(
        agent_item("磁盘上的"), encoding="utf-8"
    )
    (explicit / "weapon-presets.json").write_text("[]", encoding="utf-8")
    monkeypatch.setenv("ZZZ_PANEL_DATA_DIR", str(explicit))
    monkeypatch.setattr(loader, "_data_dir", None)

    assert [agent.name for agent in loader.load_agents()] == ["磁盘上的"]


def test_repo_data_wins_over_compiled_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """仓库根的 ``data/`` 是唯一真实源。编译产物排在它后面正是为了不遮住它。"""
    fake_bundled(monkeypatch, agents=agent_item("编译产物里的"))
    monkeypatch.setattr(loader, "_REPO_MARKER", "pyproject.toml")
    monkeypatch.delenv("ZZZ_PANEL_DATA_DIR", raising=False)
    monkeypatch.setattr(loader, "_data_dir", None)

    assert len(loader.load_agents()) == 60
    assert len(loader.load_weapons()) == 100


def test_compiled_module_matches_repo_data_when_present(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """真去编译一份再导入，条数与姓名必须与磁盘真源一致。

    这是唯一能证明「部署上去的那份」与「仓库里的真源」没跑偏的用例；
    上面几条用的是伪造模块，只验证接线。
    """
    dest = tmp_path / "_bundled_data.py"
    assert compile_module(dest) == 0

    name = "zzz_panel_test_real"
    spec = importlib.util.spec_from_file_location(name, dest)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

    monkeypatch.setattr(loader, "_EMBEDDED_MODULE", name)
    monkeypatch.setattr(loader, "_EMBEDDED", {})
    monkeypatch.setattr(loader, "_REPO_MARKER", "no-such-marker.toml")
    monkeypatch.delenv("ZZZ_PANEL_DATA_DIR", raising=False)

    from_compiled: list[tuple[str, str]] = []
    for loader_call in (loader.load_agents, loader.load_weapons):
        monkeypatch.setattr(loader, "_data_dir", None)
        monkeypatch.setattr(loader, "_EMBEDDED", {})
        compiled = loader_call()
        monkeypatch.setattr(loader, "_EMBEDDED", {})

        monkeypatch.setattr(loader, "_REPO_MARKER", "pyproject.toml")
        monkeypatch.setattr(loader, "_data_dir", None)
        on_disk = loader_call()
        from_compiled.append(
            ([item.name for item in compiled], [item.name for item in on_disk])
        )

    for compiled_names, disk_names in from_compiled:
        assert compiled_names == disk_names
