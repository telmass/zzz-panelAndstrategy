"""同步预设与规则表数据。

    python tools/sync_presets.py --from-legacy   # 夹具 data/*.js → data/*.json（一次性引导）
    python tools/sync_presets.py --to-legacy     # data/*.json → 夹具 data/*.js（长期方向）
    python tools/sync_presets.py --options       # core/*.py → data/options.json（单向）
    python tools/sync_presets.py --check         # 只比对，不写文件；有漂移则退出码 1

预设的两个方向都做同一件事：把数据规范化到本模块定义的键序后再写出。
因此「夹具 → JSON → 夹具」必定字节一致，可用来验证转换无损；
重复执行也不会产生 diff（写前比对，不一致才落盘）。

规则表只有一个方向：``data/options.json`` 是 ``core/options.py`` 与
``core/constants.py`` 的派生产物。前端 ``src/constants/calculatorOptions.ts``
不再持有副本，从该 JSON 读取，故下拉框无需等一次 HTTP 往返即可渲染。

「legacy」在本脚本中特指**参照实现夹具**
``frontend/tests/fixtures/legacy-calculator/``：第 5 步删除了 ``frontend/legacy/``
的页面，但把三方对拍所需的 ``data/*.js`` 原样留在了夹具里。
它仍读 ``window.AGENT_PRESETS``，故这份 JS 包装必须继续跟着 JSON 走。
文件是 JS 字面量而非 JSON：单引号、无转义、键名不引号，不可手工编辑。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
LEGACY_DIR = REPO_ROOT / "frontend" / "tests" / "fixtures" / "legacy-calculator" / "data"
DATA_DIR = REPO_ROOT / "data"
BACKEND_SRC = REPO_ROOT / "backend" / "src"
OPTIONS_JSON = DATA_DIR / "options.json"

FILES = (
    ("AGENT_PRESETS", LEGACY_DIR / "agent-presets.js", DATA_DIR / "agent-presets.json"),
    ("WEAPON_PRESETS", LEGACY_DIR / "weapon-presets.js", DATA_DIR / "weapon-presets.json"),
)

#: ``data/options.json`` 里的表 -> ``core`` 模块里的变量名。
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

AGENT_KEY_ORDER = (
    "id", "name", "roleTag", "panelMode", "source", "base",
    "unavailableBaseStats", "additionalBaseStats", "unmodeledBaseStats",
    "coreBonuses", "grade",
)
BASE_KEY_ORDER = ("hp", "atk", "def", "impact", "cr", "cd", "ac", "am", "pr", "er")
ADDITIONAL_KEY_ORDER = ("penforce", "energyAccumulation")
CORE_BONUS_KEY_ORDER = (
    "optionId", "optionCount", "ranks", "label", "perRankValue", "totalValue", "unit",
)
WEAPON_KEY_ORDER = (
    "id", "name", "grade", "roleTag", "source", "baseKind",
    "baseAttack", "baseDefense", "substat",
)
SUBSTAT_KEY_ORDER = ("label", "value", "kind", "to")

CONTAINER_KEY_ORDERS = {
    "base": BASE_KEY_ORDER,
    "additionalBaseStats": ADDITIONAL_KEY_ORDER,
    "unmodeledBaseStats": None,
    "coreBonuses": CORE_BONUS_KEY_ORDER,
    "substat": SUBSTAT_KEY_ORDER,
}

_IDENT = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
_NUMBER = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?")
# 字符串必须排在注释之前，否则 URL 里的 `//` 会被当成行注释。
_TOKEN = re.compile(
    r"'(?:[^'\\]|\\.)*'"
    r"|\"(?:[^\"\\]|\\.)*\""
    r"|//[^\n]*"
    r"|/\*.*?\*/",
    re.DOTALL,
)


def _strip_comments(text: str) -> str:
    return _TOKEN.sub(lambda m: m.group() if m.group()[0] in "'\"" else "", text)


class ParseError(ValueError):
    """legacy JS 字面量无法解析。"""


class _JsParser:
    """解析 legacy 预设文件所用的 JS 字面量子集。

    该子集由抓取脚本生成，特征是无转义序列：整个文件不含反斜杠、
    双引号或反引号，字符串一律用单引号包裹。故无需处理转义。
    """

    def __init__(self, text: str, origin: str) -> None:
        self.text = _strip_comments(text)
        self.origin = origin
        self.pos = 0

    def error(self, message: str) -> ParseError:
        line = self.text.count("\n", 0, self.pos) + 1
        return ParseError(f"{self.origin}:{line}: {message}")

    def skip_ws(self) -> None:
        while self.pos < len(self.text) and self.text[self.pos] in " \t\r\n":
            self.pos += 1

    def parse(self) -> Any:
        value = self.parse_value()
        self.skip_ws()
        if self.pos < len(self.text) and self.text[self.pos] == ";":
            self.pos += 1
            self.skip_ws()
        if self.pos != len(self.text):
            raise self.error(f"尾部有多余内容：{self.text[self.pos:self.pos + 20]!r}")
        return value

    def parse_value(self) -> Any:
        self.skip_ws()
        if self.pos >= len(self.text):
            raise self.error("内容意外结束")
        ch = self.text[self.pos]
        if ch == "{":
            return self.parse_object()
        if ch == "[":
            return self.parse_array()
        if ch in "'\"":
            return self.parse_string()
        for literal, value in (("true", True), ("false", False), ("null", None),
                                ("undefined", None)):
            if self.text.startswith(literal, self.pos):
                self.pos += len(literal)
                return value
        match = _NUMBER.match(self.text, self.pos)
        if match:
            self.pos = match.end()
            raw = match.group()
            return float(raw) if any(c in raw for c in ".eE") else int(raw)
        raise self.error(f"无法识别的记号：{self.text[self.pos:self.pos + 20]!r}")

    def parse_string(self) -> str:
        quote = self.text[self.pos]
        end = self.text.find(quote, self.pos + 1)
        if end < 0:
            raise self.error("字符串未闭合")
        if "\\" in self.text[self.pos:end]:
            raise self.error("字符串含转义序列，超出本解析器支持的子集")
        start = self.pos + 1
        self.pos = end + 1
        return self.text[start:end]

    def parse_object(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        self.pos += 1
        self.skip_ws()
        if self.pos < len(self.text) and self.text[self.pos] == "}":
            self.pos += 1
            return result
        while True:
            self.skip_ws()
            ch = self.text[self.pos]
            if ch in "'\"":
                key = self.parse_string()
            else:
                match = _IDENT.match(self.text, self.pos)
                if not match:
                    raise self.error(f"无法识别的键名：{self.text[self.pos:self.pos + 20]!r}")
                key = match.group()
                self.pos = match.end()
            self.skip_ws()
            if self.text[self.pos] != ":":
                raise self.error(f"键 {key!r} 后缺少冒号")
            self.pos += 1
            result[key] = self.parse_value()
            self.skip_ws()
            ch = self.text[self.pos]
            self.pos += 1
            if ch == "}":
                return result
            if ch != ",":
                raise self.error(f"键 {key!r} 的值后缺少分隔符，得到 {ch!r}")
            self.skip_ws()
            if self.text[self.pos] == "}":
                self.pos += 1
                return result

    def parse_array(self) -> list[Any]:
        result: list[Any] = []
        self.pos += 1
        self.skip_ws()
        if self.pos < len(self.text) and self.text[self.pos] == "]":
            self.pos += 1
            return result
        while True:
            result.append(self.parse_value())
            self.skip_ws()
            ch = self.text[self.pos]
            self.pos += 1
            if ch == "]":
                return result
            if ch != ",":
                raise self.error(f"数组元素后缺少分隔符，得到 {ch!r}")
            self.skip_ws()
            if self.text[self.pos] == "]":
                self.pos += 1
                return result


def load_js(path: Path) -> list[dict[str, Any]]:
    """从 legacy .js 读出预设数组。"""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"window\.[A-Za-z_$][A-Za-z0-9_$]*\s*=\s*", text)
    if not match:
        raise ParseError(f"{path.name}: 找不到 window.X = 赋值语句")
    parser = _JsParser(text[match.end():], path.name)
    data = parser.parse()
    if not isinstance(data, list):
        raise ParseError(f"{path.name}: 赋值结果不是数组")
    return data


def order_keys(value: Any, order: tuple[str, ...] | None) -> Any:
    """按给定键序递归整理字典。

    未登记的键按原出现顺序追加在后面，不丢弃——本函数只定序，不改内容。
    """
    if isinstance(value, list):
        return [order_keys(item, order) for item in value]
    if not isinstance(value, dict):
        return value
    keys = [k for k in (order or ()) if k in value]
    keys += [k for k in value if k not in keys]
    return {k: order_keys(value[k], CONTAINER_KEY_ORDERS.get(k)) for k in keys}


def order_preset(preset: dict[str, Any], agent: bool) -> dict[str, Any]:
    return order_keys(preset, AGENT_KEY_ORDER if agent else WEAPON_KEY_ORDER)


def check_ids(items: list[dict[str, Any]], origin: str) -> None:
    seen: set[str] = set()
    for index, item in enumerate(items):
        ident = item.get("id")
        if not isinstance(ident, str) or not ident:
            raise ValueError(f"{origin}: 第 {index + 1} 条缺少 id")
        if ident in seen:
            raise ValueError(f"{origin}: id 重复 {ident!r}")
        seen.add(ident)


def dump_json(items: list[dict[str, Any]]) -> str:
    return json.dumps(items, ensure_ascii=False, indent=2) + "\n"


def fmt_scalar(value: Any) -> str | None:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer() and abs(value) < 1e16:
            return str(int(value))
        return repr(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace("'", "\\'")
        return f"'{escaped}'"
    return None


def inline_text(value: Any) -> str | None:
    """标量，或值全为标量的扁平对象（`{ label: 'x', value: 1 }`）；否则 None。"""
    scalar = fmt_scalar(value)
    if scalar is not None:
        return scalar
    if isinstance(value, dict) and all(fmt_scalar(v) is not None for v in value.values()):
        return "{ " + ", ".join(f"{k}: {fmt_scalar(v)}" for k, v in value.items()) + " }"
    return None


def js_lines(value: Any, indent: int) -> list[str]:
    """把值渲染为 legacy 风格的 JS 字面量行。

    `indent` 是本值首行开括号所在的列缩进；数组项与对象键各内缩 2 空格。
    标量数组（ranks、unavailableBaseStats）与扁平对象数组
    （unmodeledBaseStats）折成一行，与抓取脚本一致。
    行尾不加分隔逗号，由调用方补。
    """
    scalar = fmt_scalar(value)
    if scalar is not None:
        return [scalar]
    pad = " " * indent
    if isinstance(value, list):
        inlined = [inline_text(item) for item in value]
        if all(text is not None for text in inlined):
            if all(fmt_scalar(item) is not None for item in value):
                return ["[" + ", ".join(text for text in inlined if text) + "]"]
            lines = [pad + "["]
            lines += [" " * (indent + 2) + text + "," for text in inlined if text]
            lines.append(pad + "]")
            return lines
        lines = [pad + "["]
        for item in value:
            item_lines = js_lines(item, indent + 2)
            item_lines[-1] += ","
            lines += item_lines
        lines.append(pad + "]")
        return lines
    if isinstance(value, dict):
        lines = [pad + "{"]
        for key, item in value.items():
            rendered = js_lines(item, indent + 2)
            rendered[0] = f"{' ' * (indent + 2)}{key}: {rendered[0].lstrip()}"
            rendered[-1] += ","
            lines += rendered
        lines.append(pad + "}")
        return lines
    raise TypeError(f"无法渲染类型 {type(value).__name__}")


def dump_js(var_name: str, items: list[dict[str, Any]]) -> str:
    lines = [f"window.{var_name} = ["]
    for preset in items:
        lines += js_lines(preset, 2)
        lines[-1] += ","
    lines.append("];")
    return "\n".join(lines) + "\n"


def display(path: Path) -> str:
    """仓库内显示相对路径，仓库外（测试的临时目录）退回绝对路径。"""
    try:
        return str(path.name)
    except ValueError:
        return str(path)


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
    """从 Python 规则表生成 ``data/options.json`` 的内容。"""
    options = load_core_module("options")
    constants = load_core_module("constants")

    result: dict[str, Any] = {"_generated": OPTIONS_NOTICE}
    for json_key, module_name, attr in OPTION_TABLES:
        result[json_key] = [
            {"id": o.id, "label": o.label, "value": o.value, "kind": o.kind, "to": o.to}
            for o in getattr(options, attr)
        ]
    result["discFixedStats"] = [
        {"slot": s.slot, "label": s.label, "value": s.value, "target": s.target}
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


def run(direction: str, check_only: bool) -> int:
    drift = 0
    for var_name, js_path, json_path in FILES:
        agent = var_name == "AGENT_PRESETS"
        if direction == "to-legacy":
            items = json.loads(json_path.read_text(encoding="utf-8"))
            check_ids(items, json_path.name)
            target, text = js_path, dump_js(var_name, items)
        else:
            items = [order_preset(p, agent) for p in load_js(js_path)]
            check_ids(items, js_path.name)
            target, text = json_path, dump_json(items)
        action = write_if_changed(target, text, check_only)
        if action is None:
            print(f"  ok       {display(target)}")
        else:
            drift += 1
            verb = "drift" if check_only else action
            print(f"  {verb:9} {display(target)}")
    if drift:
        print(f"{'存在漂移' if check_only else '已写入'}：{drift} 个文件")
    return 1 if check_only and drift else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--from-legacy", action="store_true",
                       help="legacy/data/*.js → data/*.json")
    group.add_argument("--to-legacy", action="store_true",
                       help="data/*.json → legacy/data/*.js")
    group.add_argument("--options", action="store_true",
                       help="core/*.py → data/options.json（单向）")
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

    direction = "to-legacy" if args.to_legacy else "from-legacy"
    print(f"{'检查' if args.check else '同步'}（{direction}）")
    try:
        return run(direction, args.check)
    except (ParseError, ValueError, OSError, json.JSONDecodeError) as error:
        print(f"错误：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())