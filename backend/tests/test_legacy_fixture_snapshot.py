"""参照实现夹具与当前数据集的**语义等价**测试。

背景
----
``frontend/tests/fixtures/legacy-calculator/`` 是三方对拍（legacy ≡ Vue3 ≡
Python）的参照实现。参照实现的输入必须是一个**不动点**——它证明的是「旧实现
在某个确定时刻算得对」。若它的输入跟着当前数据一起变，就再也说明不了这一点。

因此该夹具的 ``data/*.js`` 已在数据形状重构前**冻结为快照**，不再由
``tools/sync_presets.py`` 生成（原 ``--to-legacy`` / ``--from-legacy`` 模式已
移除）。

冻结之后，守门从「转换无损」换成**语义等价**：夹具里那几名代理人与音擎，
必须与当前数据集在**数值与结构上等值**。这才是真正关心的不变量——数值等价，
而不是「某个脚本能无损地来回转」。

若将来确实要更新夹具（例如为了覆盖新形态的代理人），应当**重跑一次三方对拍
并人工确认数值一致**后，再更新本文件里的期望；不要把「夹具与数据不同步」
当成可以放宽的理由。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DATA = REPO_ROOT / "frontend/tests/fixtures/legacy-calculator/data"

#: 三方对拍用到的代理人。夹具里必须恰好有这几条。
PARITY_AGENT_IDS = ("ep-1299", "ep-2145")

#: 三方对拍用到的音擎（满配场景选 S 级强攻的首选）。
PARITY_WEAPON_ID = "ep-1751"


# --------------------------------------------------------------------------
# 极简 JS 字面量解析
# --------------------------------------------------------------------------


class _JsLiteralParser:
    """解析 legacy 夹具里那种「对象 + 数组 + 单引号字符串」的 JS 字面量。

    夹具是**冻结的**快照，格式固定，因此不需要完整的 JS 解析器：只需认得
    对象、数组、数字、单引号字符串与三个字面量关键字。真正的 JS 语法
    （函数、模板串、运算）一律不支持——遇到即报错，避免「悄悄解析错了」。
    """

    _TOKEN = re.compile(
        r"""
        (?P<string>'(?:\\.|[^'\\])*')
        | (?P<number>-?\d+(?:\.\d+)?)
        | (?P<punct>[{}\[\],:])
        | (?P<word>[A-Za-z_][A-Za-z0-9_]*)
        | (?P<space>\s+)
        """,
        re.VERBOSE,
    )

    def __init__(self, text: str) -> None:
        self._tokens = [
            (match.lastgroup, match.group())
            for match in self._TOKEN.finditer(text)
            if match.lastgroup != "space"
        ]
        self._pos = 0

    def parse(self) -> Any:
        value = self._value()
        if self._pos != len(self._tokens):
            raise ValueError("JS 字面量尾部有多余内容")
        return value

    def _peek(self) -> tuple[str, str] | None:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _next(self) -> tuple[str, str]:
        token = self._peek()
        if token is None:
            raise ValueError("JS 字面量意外结束")
        self._pos += 1
        return token

    def _expect(self, punct: str) -> None:
        kind, text = self._next()
        if kind != "punct" or text != punct:
            raise ValueError(f"期望 {punct!r}，实际是 {text!r}")

    def _value(self) -> Any:
        kind, text = self._next()
        if kind == "string":
            return text[1:-1].replace("\\'", "'").replace("\\\\", "\\")
        if kind == "number":
            return float(text) if "." in text else int(text)
        if kind == "word":
            if text == "true":
                return True
            if text == "false":
                return False
            if text == "null":
                return None
            raise ValueError(f"不支持的 JS 关键字 {text!r}")
        if kind == "punct" and text == "[":
            items = []
            if self._peek() == ("punct", "]"):
                self._next()
                return items
            while True:
                items.append(self._value())
                kind, text = self._next()
                if text == "]":
                    return items
                if text != ",":
                    raise ValueError(f"数组里期望 , 或 ]，实际是 {text!r}")
                # 允许尾逗号：夹具里对象/数组都带尾逗号（JS 合法）。
                if self._peek() == ("punct", "]"):
                    self._next()
                    return items
        if kind == "punct" and text == "{":
            obj: dict[str, Any] = {}
            if self._peek() == ("punct", "}"):
                self._next()
                return obj
            while True:
                key_kind, key_text = self._next()
                if key_kind == "string":
                    key = key_text[1:-1]
                elif key_kind == "word":
                    key = key_text
                else:
                    raise ValueError(f"对象键必须是标识符或字符串，实际是 {key_text!r}")
                self._expect(":")
                obj[key] = self._value()
                kind, text = self._next()
                if text == "}":
                    return obj
                if text != ",":
                    raise ValueError(f"对象里期望 , 或 }}，实际是 {text!r}")
                if self._peek() == ("punct", "}"):
                    self._next()
                    return obj
        raise ValueError(f"无法解析的记号 {text!r}")


def _load_fixture_array(path: Path, global_name: str) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    prefix = f"window.{global_name} = "
    start = text.index(prefix) + len(prefix)
    end = text.rindex(";")
    return _JsLiteralParser(text[start:end]).parse()


@pytest.fixture(scope="module")
def fixture_agents() -> list[dict[str, Any]]:
    return _load_fixture_array(FIXTURE_DATA / "agent-presets.js", "AGENT_PRESETS")


@pytest.fixture(scope="module")
def fixture_weapons() -> list[dict[str, Any]]:
    return _load_fixture_array(FIXTURE_DATA / "weapon-presets.js", "WEAPON_PRESETS")


@pytest.fixture(scope="module")
def current_agents() -> list[dict[str, Any]]:
    return json.loads((REPO_ROOT / "data/catalog/agents.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def current_weapons() -> list[dict[str, Any]]:
    return json.loads((REPO_ROOT / "data/catalog/weapons.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# 语义等价
# --------------------------------------------------------------------------


def test_fixture_is_frozen_and_not_regenerated() -> None:
    """夹具不再由脚本生成——「参照实现」必须是不动点。

    断言方式是「生成脚本里没有反向生成夹具的入口」：一旦有人把
    ``--to-legacy`` 加回来，夹具就会跟着当前数据漂移，这条测试先失败。
    """
    source = (REPO_ROOT / "tools/sync_presets.py").read_text(encoding="utf-8")
    assert '"--to-legacy"' not in source
    assert '"--from-legacy"' not in source
    assert "def dump_js(" not in source
    assert "def load_js(" not in source
    assert "def _JsParser" not in source


@pytest.mark.parametrize("agent_id", PARITY_AGENT_IDS)
def test_parity_agents_are_semantically_equal(
    agent_id: str,
    fixture_agents: list[dict[str, Any]],
    current_agents: list[dict[str, Any]],
) -> None:
    """三方对拍用到的代理人：夹具与当前数据在数值与结构上等值。

    比的是**语义**而非 JSON 形状：夹具是 v1 形状（``coreBonuses`` /
    ``perRankValue``），当前数据是 v2 形状（``core`` / ``perRank``）。形状
    变了，值不能变。
    """
    old = next((item for item in fixture_agents if item["id"] == agent_id), None)
    new = next((item for item in current_agents if item["id"] == agent_id), None)
    assert old is not None, f"夹具里没有 {agent_id}"
    assert new is not None, f"当前数据里没有 {agent_id}"

    for field in ("id", "name", "attribute", "grade", "roleTag", "panelMode"):
        assert old[field] == new[field], f"{agent_id}.{field} 不一致"

    # 基础面板：键集与数值都要一致（夹具里缺键即官方未提供）。
    assert set(old["base"]) == set(new["base"]), f"{agent_id} 的基础面板键集不一致"
    for key, value in old["base"].items():
        assert value == new["base"][key], f"{agent_id}.base.{key} 不一致"

    # 命破专属的额外基础属性。
    old_extra = old.get("additionalBaseStats") or {}
    new_extra = new.get("baseExtra") or {}
    assert old_extra == new_extra, f"{agent_id} 的额外基础属性不一致"

    # 核心加成：选项、位次、每级数值、合计都要一致。
    old_core = old["coreBonuses"]
    new_core = new["core"]
    assert len(old_core) == len(new_core), f"{agent_id} 的核心加成条数不一致"
    for old_bonus, new_bonus in zip(old_core, new_core):
        assert old_bonus["optionId"] == new_bonus["optionId"]
        assert old_bonus["ranks"] == new_bonus["ranks"]
        assert old_bonus["label"] == new_bonus["label"]
        assert old_bonus["perRankValue"] == new_bonus["perRank"]
        assert old_bonus["totalValue"] == new_bonus["totalValue"]
        assert old_bonus.get("optionCount") == new_bonus.get("optionCount")


def test_parity_weapon_is_semantically_equal(
    fixture_weapons: list[dict[str, Any]],
    current_weapons: list[dict[str, Any]],
) -> None:
    """三方对拍用到的音擎同样要等值。"""
    old = next(
        (item for item in fixture_weapons if item["id"] == PARITY_WEAPON_ID), None
    )
    new = next(
        (item for item in current_weapons if item["id"] == PARITY_WEAPON_ID), None
    )
    assert old is not None, f"夹具里没有音擎 {PARITY_WEAPON_ID}"
    assert new is not None, f"当前数据里没有音擎 {PARITY_WEAPON_ID}"

    for field in ("id", "name", "grade", "roleTag"):
        assert old[field] == new[field], f"音擎 {PARITY_WEAPON_ID}.{field} 不一致"

    old_base = old["baseAttack"] if old["baseKind"] == "atk" else old["baseDefense"]
    assert old_base == new["base"]["value"], "音擎基础值不一致"
    assert old["baseKind"] == new["base"]["kind"], "音擎基础值类型不一致"
    assert old["substat"] == new["substat"], "音擎固定副词条不一致"


def test_fixture_covers_every_parity_case() -> None:
    """夹具里必须有对拍用到的全部代理人与音擎，否则对拍是拿不同的输入在比。"""
    agents = _load_fixture_array(FIXTURE_DATA / "agent-presets.js", "AGENT_PRESETS")
    weapons = _load_fixture_array(FIXTURE_DATA / "weapon-presets.js", "WEAPON_PRESETS")
    agent_ids = {item["id"] for item in agents}
    weapon_ids = {item["id"] for item in weapons}
    for agent_id in PARITY_AGENT_IDS:
        assert agent_id in agent_ids, f"夹具缺少代理人 {agent_id}"
    assert PARITY_WEAPON_ID in weapon_ids, f"夹具缺少音擎 {PARITY_WEAPON_ID}"
