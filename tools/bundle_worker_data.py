"""把 ``data/`` 下的预设数据编译进一个 Python 模块，供 Cloudflare Worker 部署。

    python tools/bundle_worker_data.py            # 生成/刷新
    python tools/bundle_worker_data.py --check     # 只比对，有漂移则退出码 1

为什么不能直接复制一份 .json
---------------------------
``pywrangler`` 部署时**只上传 ``.py`` 文件**。入口目录下的 ``.json``、``.html``
一类资源会被静默丢弃——不报错，只是线上读不到。

实测方式：``wrangler deploy --dry-run --outdir .wrangler-dry``，产出的
``zzz_panel/`` 目录里只有 27 个 ``.py``，镜像进去的 JSON 不在其中，症状是
``/api/presets/*`` 返回 503（与「忘记生成镜像」完全一样，因此必须靠
``--dry-run`` 之外的手段排查）。

所以 Worker 里唯一能带上的数据形式就是 Python 模块。模块以「每行一个相邻
字符串字面量」保存原文，好处是：

- 与源文件**逐字节**一致，可被 ``--check`` 校验
- 不依赖虚拟文件系统的任何行为，也不需要 ``importlib.resources``
- 生成物不提交，唯一真实源永远是仓库根的 ``data/``

收哪些数据集由 ``data/manifest.json`` 的 ``worker`` 字段决定（目前是代理人
与音擎预设——这两个是后端 ``presets/loader.py`` 运行时读的）。规则表
``calculator-rules`` 不收：它由前端在**构建期**经 Vite 别名 ``@data`` 读真实源，
根本不经过后端。

常量名由数据集 id 推导（``agents`` → ``AGENTS_JSON``），打包脚本与后端
loader 用同一条规则；两侧是否一致由 ``backend/tests/test_worker_bundle.py``
断言，改名漏改一侧会在 CI 就失败，而不是上线后才 503。
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

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_paths import dataset_path, load_manifest, worker_constant  # noqa: E402

#: 生成目标。**必须是 .py**——只有 .py 会被上传（见模块 docstring）。
#: 放在 ``backend/src/`` 之下才会被 pywrangler 附加：它只附加 Worker 入口
#: ``backend/src/worker.py`` 所在目录的整棵树。
BUNDLED_MODULE = REPO_ROOT / "backend" / "src" / "zzz_panel" / "_bundled_data.py"


def _worker_sources() -> dict[str, str]:
    """真实源相对路径 -> 生成模块里的常量名。取自 ``data/manifest.json``。"""
    manifest = load_manifest()
    sources: dict[str, str] = {}
    for name, entry in manifest["datasets"].items():
        if entry.get("worker"):
            sources[entry["path"]] = worker_constant(name)
    return sources


#: 源文件相对路径 -> 生成模块里的常量名。
SOURCES = _worker_sources()

_HEADER_LINES = (
    '"""预设数据的 Worker 编译产物，**生成物，勿手工编辑**。',
    "",
    "由 ``python tools/bundle_worker_data.py`` 从仓库根 ``data/`` 生成。",
    "唯一真实源是 ``data/``；本文件不提交（见 ``.gitignore``）。",
    "",
    "原文按「每行一个相邻字符串字面量」保存，因此与源文件逐字节一致，",
    "且不依赖 Worker 虚拟文件系统的任何行为。",
    '"""',
    "",
)


def render_module(payloads: dict[str, str]) -> str:
    """把若干个 JSON 原文渲染成 Python 模块文本。"""
    chunks = ["\n".join(_HEADER_LINES)]
    for name in SOURCES:
        constant = SOURCES[name]
        lines = payloads[name].splitlines(keepends=True)
        chunks.append(f"\n{constant} = (\n")
        for line in lines:
            # json.dumps 产出的字符串字面量在 Python 里同样合法：
            # 双引号、反斜杠、换行转义与 Python 一致。
            chunks.append(f"    {json.dumps(line, ensure_ascii=False)}\n")
        chunks.append(")\n")
    return "".join(chunks)


def _display(path: Path) -> str:
    """给人看的路径。``--dest`` 可能指向仓库外（测试就 tmp_path），别因此崩掉。"""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def sync(data_dir: Path, dest: Path, check: bool) -> int:
    """重新生成模块。

    返回 0 表示已生成且与真实源一致；返回 1 表示「check 模式下查出漂移」
    或「源文件缺失」。
    """
    payloads: dict[str, str] = {}
    for name in SOURCES:
        source = data_dir / name
        if not source.is_file():
            print(f"缺少真实源 {source}，无法生成。", file=sys.stderr)
            return 1
        payloads[name] = source.read_text(encoding="utf-8")

    rendered = render_module(payloads)

    if dest.is_file() and dest.read_text(encoding="utf-8") == rendered:
        print(f"已是最新：{len(payloads)} 份数据 -> {_display(dest)}")
        return 0

    if check:
        print(f"有漂移：{_display(dest)} 与 data/ 不一致", file=sys.stderr)
        print("运行 `python tools/bundle_worker_data.py` 重新生成。", file=sys.stderr)
        return 1

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(rendered, encoding="utf-8")
    print(
        f"已生成：{_display(dest)}"
        f"（{len(payloads)} 份数据，{len(rendered.encode('utf-8')) // 1024} KiB）"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="只比对不写文件；生成物与 data/ 不一致时退出码 1",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DATA_DIR,
        help=f"真实源目录，默认 {DATA_DIR}",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=BUNDLED_MODULE,
        help=f"生成目标 .py，默认 {BUNDLED_MODULE}",
    )
    args = parser.parse_args()

    return sync(args.data_dir, args.dest, args.check)


if __name__ == "__main__":
    raise SystemExit(main())
