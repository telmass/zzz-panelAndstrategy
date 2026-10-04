"""pytest 全局夹具。

目前只有一件事：让「包内编译产物」这条数据回退路径默认失效。

为什么需要
----------
``zzz_panel/_bundled_data.py`` 是 ``tools/bundle_worker_data.py`` 的产物，
``.gitignore`` 掉了，不进版本库。于是同一份代码在两种机器上行为不同：

- 干净 clone（没跑过生成脚本）→ 回退路径不存在
- 跑过一次生成脚本的本地 → 回退路径存在，``load_agents()`` 会返回它

于是 ``test_missing_file_reports_how_to_generate`` 这类「数据不可用」的用例
会在开发者机器上莫名失败、在 CI 上通过。测试的结论不能取决于机器状态，
因此在这里统一切断：需要这条路径的用例自己装，见
``test_worker_bundle.py``。
"""

from __future__ import annotations

import pytest

from zzz_panel.presets import loader

#: 指向一个永不存在的模块，等价于「生成脚本没跑过」。
_NEVER_GENERATED = "zzz_panel._not_generated_in_tests"


@pytest.fixture(autouse=True)
def no_compiled_presets(monkeypatch: pytest.MonkeyPatch) -> None:
    """切断包内编译产物这条回退路径，让预设只从磁盘真源来。"""
    monkeypatch.setattr(loader, "_EMBEDDED_MODULE", _NEVER_GENERATED)
    monkeypatch.setattr(loader, "_EMBEDDED", {})
