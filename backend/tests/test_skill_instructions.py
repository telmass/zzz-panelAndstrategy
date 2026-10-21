"""Skill 指令与仓库现状的**漂移闸**。

问题
----
``.github/skills/*/SKILL.md`` 是 agent 执行导入流程时**唯一**的操作说明。
文档里写的命令若与代码对不上，agent 会照着跑，然后卡住——而**没有任何东西
会提醒它**。重构数据管线时踩过一次：``sync_presets.py --to-legacy`` 被移除，
但 6 个 SKILL.md 仍让人跑它，argparse 报「unrecognized arguments」，
导入流程当场断掉。

这个闸门把「文档里的命令」当作**可执行契约**来守：

1. 文档里提到的脚本**必须存在**；
2. 文档里提到的命令**必须真的能跑**（把参数换成 ``--help`` 实际执行一遍，
   捕获「参数不再被接受」这类漂移）；
3. 文档里提到的数据路径**必须与登记表一致**；
4. 抓取脚本的 ``OUTPUT`` 常量**必须与登记表一致**。
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / ".github" / "skills"

#: 参与漂移闸的文档。``_shared/`` 是流程的唯一事实源，必须在内。
DOC_GLOB = "**/*.md"

#: 文档里命令的形态：``python <脚本路径> [参数…]``。
#: 捕获 ``python`` / ``uv run python`` / ``python3``。
COMMAND_RE = re.compile(
    r"(?:uv\s+run\s+)?python3?\s+((?:[\w.\-/]+\.py)(?:\s+[^\n`|>#]*)?)"
)

#: 这些脚本即使存在也**不执行**——它们要么没有 ``--help``，要么会做实际工作。
SKIP_EXECUTION = {
    # 一次性迁移脚本：留着是为了「这份数据是怎么变成现在这个形状的」有据可查，
    # 不是常规流程的一部分。
    "tools/migrate_presets_v2.py",
    "tools/strip_strategy_base_panel.py",
    "tools/normalize_ui_scale.py",
}


def _doc_files() -> list[Path]:
    return sorted(SKILLS_DIR.rglob("*.md"))


def _manifest() -> dict:
    return json.loads((REPO_ROOT / "data" / "manifest.json").read_text(encoding="utf-8"))


def _commands_in(text: str) -> list[str]:
    """抽出文档里的 python 命令行（去重、去掉行尾反引号与续行）。"""
    commands: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith(("python ", "python3 ", "uv run python")):
            continue
        # 去掉 markdown 行尾的 ``` 与表格分隔
        line = line.split("`")[0].split("#")[0].strip().rstrip("|").strip()
        if line and "python" in line:
            commands.append(line)
    return commands


def test_no_skill_doc_mentions_a_removed_command() -> None:
    """已移除的命令不得再出现在 skill 文档里。

    ``--to-legacy`` / ``--from-legacy`` 已随「对拍夹具冻结」移除。
    """
    removed = ("--to-legacy", "--from-legacy")
    offenders: list[str] = []
    for path in _doc_files():
        text = path.read_text(encoding="utf-8")
        for flag in removed:
            if flag in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {flag}")
    assert not offenders, "skill 文档里仍有已移除的命令：\n" + "\n".join(offenders)


def _resolve_script(doc: Path, script: str) -> Path | None:
    """把文档里的脚本路径解析成实际文件。

    文档里的路径有两种写法：仓库相对（``tools/x.py``）与 skill 相对
    （``scripts/x.py``，如 refactoring-ui 的参考文档）。两种都要能解析。
    """
    script = script.replace("\\", "/")
    if not script.endswith(".py"):
        return None
    candidates = [REPO_ROOT / script]
    # skill 相对：文档所在 skill 的目录
    skill_root = doc
    while skill_root != SKILLS_DIR.parent and skill_root.name:
        skill_root = skill_root.parent
        candidates.append(skill_root / script)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def test_every_documented_script_exists() -> None:
    """文档里提到的脚本必须存在。"""
    missing: list[str] = []
    for path in _doc_files():
        text = path.read_text(encoding="utf-8")
        for command in _commands_in(text):
            parts = command.split()
            script = parts[1] if parts[0] != "uv" else parts[3]
            if not script.endswith(".py"):
                continue
            if _resolve_script(path, script) is None:
                missing.append(f"{path.relative_to(REPO_ROOT)}: {script}")
    assert not missing, "skill 文档里提到了不存在的脚本：\n" + "\n".join(missing)


@pytest.mark.parametrize(
    "doc", [p.relative_to(REPO_ROOT).as_posix() for p in _doc_files()], ids=str
)
def test_every_documented_command_still_parses(doc: str) -> None:
    """文档里的命令必须真的能跑——把参数换成 ``--help`` 实际执行一遍。

    这是最关键的一条：``--to-legacy`` 被移除后，argparse 会在**执行期**报
    「unrecognized arguments」，而那时 agent 已经卡在流程里了。这里把它提前
    到 CI。
    """
    path = REPO_ROOT / doc
    text = path.read_text(encoding="utf-8")
    for command in _commands_in(text):
        parts = command.split()
        if parts[0] == "uv":
            parts = parts[2:]  # uv run python ...
        script = parts[1].replace("\\", "/")
        if not script.endswith(".py") or script in SKIP_EXECUTION:
            continue
        target = REPO_ROOT / script
        if not target.is_file():
            continue
        result = subprocess.run(
            [sys.executable, str(target), "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        assert result.returncode == 0, (
            f"{doc}: `{command}` 已无法执行（退出码 {result.returncode}）\n"
            f"{result.stdout[-400:]}{result.stderr[-400:]}"
        )


def test_documented_data_paths_match_the_manifest() -> None:
    """文档里提到的数据路径必须与登记表一致。

    路径改名后文档没跟着改，是与「命令失效」同级的漂移——照样会让 agent
    找不到文件。
    """
    manifest = _manifest()
    registered = {entry["path"] for entry in manifest["datasets"].values()}
    # 登记表本身不是数据集，但它是路径的唯一真源，文档当然会提到它。
    registered.add("manifest.json")
    # 文档里可能写成 ``data/catalog/agents.json`` 或带 data/ 前缀的相对路径。
    mentioned = re.compile(r"data/[\w\-/]+\.json")
    stale: list[str] = []
    for path in _doc_files():
        text = path.read_text(encoding="utf-8")
        for match in set(mentioned.findall(text)):
            relative = match[len("data/") :]
            if relative not in registered:
                stale.append(f"{path.relative_to(REPO_ROOT)}: {match}")
    assert not stale, "skill 文档里的数据路径与登记表对不上：\n" + "\n".join(sorted(stale))


def test_scraper_output_constants_match_the_manifest() -> None:
    """抓取脚本的 ``OUTPUT`` 常量必须指向登记表里登记的那份文件。"""
    manifest = _manifest()
    expected = {
        "refresh_agent_presets.py": manifest["datasets"]["agents"]["path"],
        "refresh_weapon_presets.py": manifest["datasets"]["weapons"]["path"],
        "refresh_disc_presets.py": manifest["datasets"]["drive-discs"]["path"],
    }
    for script_name, registered in expected.items():
        path = next(SKILLS_DIR.rglob(script_name))
        text = path.read_text(encoding="utf-8")
        match = re.search(r'^OUTPUT\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        assert match, f"{script_name} 没有 OUTPUT 常量"
        assert match.group(1) == f"data/{registered}", (
            f"{script_name} 的 OUTPUT 指向 {match.group(1)}，"
            f"登记表里是 data/{registered}"
        )
