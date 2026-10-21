"""预设数据的规范化序列化与规则表生成。

    python tools/sync_presets.py --options       # core/*.py → data/rules/calculator-rules.json（单向）
    python tools/sync_presets.py --check         # 只比对，不写文件；有漂移则退出码 1

本模块有两个职责：

1. **规范化序列化**（:func:`order_preset` / :func:`dump_json`）：把预设数据
   整理到本模块定义的键序后再写出。三个 Skill 抓取脚本都复用这里的实现，
   因此重新抓取产出的文件是**字节幂等**的——这是 ``backend/tests/test_presets.py``
   里「抓取脚本须能逐字节重现已提交文件」那条断言的前提。各写一套序列化
   会让漂移永远无法定位。

2. **规则表生成**（:func:`build_options`）：``data/rules/calculator-rules.json``
   是 ``core/options.py`` 与 ``core/constants.py`` 的派生产物。前端
   ``src/constants/calculatorOptions.ts`` 不再持有副本，从该 JSON 读取，
   故下拉框无需等一次 HTTP 往返即可渲染。

关于参照实现夹具
----------------
``frontend/tests/fixtures/legacy-calculator/`` 里的 ``data/*.js`` 曾由本脚本
的 ``--to-legacy`` 模式生成。它是**三方对拍的参照实现**，其输入应当是一个
**不动点**——参照实现的价值在于它是过去某个确定时刻的正确实现，若它的输入
跟着当前数据一起变，就再也说明不了「旧实现算得对」。

因此该夹具已于数据形状重构前**冻结为快照**，不再由本脚本生成。对应的守门
换成 ``backend/tests/test_legacy_fixture_snapshot.py``：它断言夹具里用到的
那几名代理人与当前数据集在**语义上等值**（基础面板逐项、核心加成的选项
与每级数值、面板模式），守的是真正关心的不变量——数值等价，而不是
「转换无损」。
"""

from __future__ import annotations

import argparse
import json
import sys

# 管道输出固定 UTF-8：Windows 上管道默认用系统代码页（本机 GBK），
# 父工具按 UTF-8 读会抛 UnicodeDecodeError 或读出乱码。控制台输出保持
# 系统代码页，否则用户在自己的终端里会看到乱码。
if hasattr(sys.stdout, "reconfigure") and not sys.stdout.isatty():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_SRC = REPO_ROOT / "backend" / "src"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_paths import dataset_path  # noqa: E402

#: 规则表数据集在 ``data/manifest.json`` 里的 id。
RULES_DATASET = "calculator-rules"

#: 规则表 JSON 的绝对路径。测试会 monkeypatch 这个常量指向临时目录。
OPTIONS_JSON = dataset_path(RULES_DATASET)

#: ``data/rules/calculator-rules.json`` 里的表 -> ``core`` 模块里的变量名。
#: 键同时是 JSON 的键名，改这里等于改前端取数的字段名。
OPTION_TABLES = (
    ("coreOptions", "options", "CORE_OPTIONS"),
    ("disc4Options", "options", "DISC4_OPTIONS"),
    ("disc5Options", "options", "DISC5_OPTIONS"),
    ("disc6Options", "options", "DISC6_OPTIONS"),
    ("setOptions", "options", "SET_OPTIONS"),
    ("subStats", "options", "SUB_STATS"),
)

OPTIONS_NOTICE = (
    "由 tools/sync_presets.py --options 从 backend/src/zzz_panel/core/ 生成，勿手改；"
    "规则表的唯一真实源是 core/options.py 与 core/constants.py。"
)

#: 规则表 JSON 的版本号。形状演进时递增，前端按版本判断字段含义。
OPTIONS_SCHEMA_VERSION = 2

#: ``attribute`` / ``grade`` 是「这是谁」的分类信息，紧跟 name，
#: 与 ``WEAPON_KEY_ORDER`` 把 ``grade`` 放在 name 之后的约定一致；
#: ``roleTag`` / ``panelMode`` 随后才是分组与计算维度。
AGENT_KEY_ORDER = (
    "id", "name", "attribute", "grade", "roleTag", "panelMode", "source",
    "base", "baseExtra", "baseUnmodeled", "core",
)
BASE_KEY_ORDER = ("hp", "atk", "def", "impact", "cr", "cd", "ac", "am", "pr", "er")
BASE_EXTRA_KEY_ORDER = ("penforce", "energyAccumulation")
CORE_KEY_ORDER = ("optionId", "optionCount", "ranks", "label", "perRank")
WEAPON_KEY_ORDER = (
    "id", "name", "grade", "roleTag", "source", "base", "substat",
)
BASE_KIND_ORDER = ("kind", "value")
SUBSTAT_KEY_ORDER = ("label", "value", "kind", "to")

#: 嵌套容器的键序。代理人预设与音擎预设的 ``base`` 含义不同
#: （前者是 10 项面板，后者是 ``{kind, value}``），故分表登记。
AGENT_CONTAINER_ORDERS = {
    "base": BASE_KEY_ORDER,
    "baseExtra": BASE_EXTRA_KEY_ORDER,
    "core": CORE_KEY_ORDER,
}
WEAPON_CONTAINER_ORDERS = {
    "base": BASE_KIND_ORDER,
    "substat": SUBSTAT_KEY_ORDER,
}


def order_keys(
    value: Any,
    order: tuple[str, ...] | None,
    containers: dict[str, tuple[str, ...] | None],
) -> Any:
    """按给定键序递归整理字典。

    未登记的键按原出现顺序追加在后面，不丢弃——本函数只定序，不改内容。
    """
    if isinstance(value, list):
        return [order_keys(item, order, containers) for item in value]
    if not isinstance(value, dict):
        return value
    keys = [k for k in (order or ()) if k in value]
    keys += [k for k in value if k not in keys]
    return {k: order_keys(value[k], containers.get(k), containers) for k in keys}


def order_preset(preset: dict[str, Any], agent: bool) -> dict[str, Any]:
    if agent:
        return order_keys(preset, AGENT_KEY_ORDER, AGENT_CONTAINER_ORDERS)
    return order_keys(preset, WEAPON_KEY_ORDER, WEAPON_CONTAINER_ORDERS)


def check_ids(items: list[dict[str, Any]], origin: str) -> None:
    seen: set[str] = set()
    for index, item in enumerate(items):
        ident = item.get("id")
        if not isinstance(ident, str) or not ident:
            raise ValueError(f"{origin}: 第 {index + 1} 条缺少 id")
        if ident in seen:
            raise ValueError(f"{origin}: id 重复 {ident!r}")
        seen.add(ident)


def dump_json(items: Any) -> str:
    return json.dumps(items, ensure_ascii=False, indent=2) + "\n"


def write_if_changed(path: Path, text: str, check_only: bool) -> str | None:
    """写前比对；返回 None 表示已一致，否则返回动作描述。"""
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current == text:
        return None
    if check_only:
        return "would update" if current is not None else "would create"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return "updated" if current is not None else "created"


def display(path: Path) -> str:
    """仓库内显示相对路径，仓库外（测试的临时目录）退回绝对路径。"""
    try:
        return str(path.name)
    except ValueError:
        return str(path)


def load_core_module(name: str):
    """按路径导入 ``zzz_panel.core`` 下的模块。

    刻意用绝对路径导入而非 ``pip install`` 后的包名：本脚本要能被纯 stdlib 的
    ``python`` 直接跑起来（Skill 抓取脚本就是用系统 python 执行的）。
    ``core`` 层零第三方依赖，因此这样导入不会拉起 fastapi/pydantic。
    """
    if str(BACKEND_SRC) not in sys.path:
        sys.path.insert(0, str(BACKEND_SRC))
    from importlib import import_module

    return import_module(f"zzz_panel.core.{name}")


def build_options() -> dict[str, Any]:
    """从 Python 规则表生成规则表 JSON 的内容。"""
    options = load_core_module("options")
    constants = load_core_module("constants")

    result: dict[str, Any] = {
        "schemaVersion": OPTIONS_SCHEMA_VERSION,
        "_generated": OPTIONS_NOTICE,
    }
    for json_key, module_name, attr in OPTION_TABLES:
        result[json_key] = [
            {
                "id": o.id,
                "name": o.name,
                "label": o.label,
                "value": o.value,
                "kind": o.kind,
                "to": o.to,
            }
            for o in getattr(options, attr)
        ]
    result["discFixedStats"] = [
        {"slot": s.slot, "name": s.name, "label": s.label, "value": s.value, "to": s.to}
        for s in constants.DISC_FIXED_STATS
    ]
    return result


def run_options(check_only: bool) -> int:
    action = write_if_changed(OPTIONS_JSON, dump_json(build_options()), check_only)
    if action is None:
        print(f"  ok       {display(OPTIONS_JSON)}")
        return 0
    verb = "drift" if check_only else action
    print(f"  {verb:9} {display(OPTIONS_JSON)}")
    return 1 if check_only else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--options", action="store_true",
                        help="core/*.py → data/rules/calculator-rules.json（单向）")
    parser.add_argument("--check", action="store_true",
                        help="只报告漂移，不写文件")
    args = parser.parse_args()

    if args.options:
        print("规则表同步（options）" if not args.check else "规则表检查（options）")
        try:
            return run_options(args.check)
        except (ImportError, AttributeError, OSError) as error:
            print(f"错误：{error}", file=sys.stderr)
            return 2

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
