# backend/tests — Python 测试

pytest 回归测试，**87 项**。运行：

```powershell
uv run pytest
```

配置在 `pyproject.toml` 的 `[tool.pytest.ini_options]`（`pythonpath = ["backend/src"]`）。

> **必须 0 skip。** 任何 skip 都意味着某道护栏没真正执行，`test_fmt_parity.py` 尤其如此。
> 各文件的覆盖范围另见 [../../docs/directory-layout.md](../../docs/directory-layout.md) 第 3 节。

## 6 个测试模块

| 文件 | 项数 | 覆盖内容 |
| --- | --- | --- |
| `test_panel.py` | 28 | `core/panel.py` 及模式专属计算。以重构前 `main.py` 的 `EXAMPLE` 为锚点锁定 12 项数值，另覆盖基础公式、武器副词条、命破贯穿力、锋御实际暴击率与固定锐暴伤害 |
| `test_presets.py` | 25 | `presets/` 的加载与结构校验：真实数据可通过、重复 id / 未知 roleTag / 未知 panelMode / 无法表示的核心加成 / 每级数值不一致 / 核心槽位数不等于 2 一律被拒。另含**防漂移**：抓取脚本须能逐字节重现已提交的 `data/*.json`，且复用 `sync_presets.py` 的序列化器 |
| `test_api.py` | 13 | FastAPI 路由契约：`/api/health`、空请求返回 12 行、命破/锋御专属行、非法 mode 被拒、明细片段可渲染、副词条钳制落在 core 层、CORS 白名单、预设损坏返回 503 而非 500、路由已注册进 OpenAPI |
| `test_options_json.py` | 11 | `data/options.json` 的**防漂移**：规则表真源是 `core/options.py` 与 `core/constants.py`，改了 Python 侧却忘了跑 `python tools/sync_presets.py --options` 时本测试失败 |
| `test_legacy_parity.py` | 8 | Python 与**未经改动的 legacy 页面**抽样用例对拍。期望值由 `frontend/tools/dump_legacy_cases.mjs` 从 legacy 夹具导出；四组场景与 `frontend/tests/legacy-parity.spec.ts` 一一对应 |
| `test_fmt_parity.py` | 2 | 前后端 `fmt` 一致性：同一组输入下 Node 前端与 Python 输出逐字符相同（跨语言对拍的失效方式）。把该栏换成假绿灯，是比信息更糟的失败 |

## 夹具与辅助文件

| 文件 | 作用 |
| --- | --- |
| `legacy_cases.json` | `dump_legacy_cases.mjs` 导出的 legacy 期望值。**重新生成**见 `test_legacy_parity.py` 的模块 docstring，不要手工编辑 |
| `_fmt_driver.cjs` | `test_fmt_parity.py` 调用的 Node 驱动，用同一组输入跑前端 `fmt` 与 Python `fmt` 并比对 |

## 与前端对拍的关系

前端 `frontend/tests/legacy-parity.spec.ts` 做的是**三方对拍**：legacy 夹具 ≡ Vue3 页面 ≡ Python 后端。
本目录的 `test_legacy_parity.py` 只覆盖其中「Python ≡ legacy」这一段，且用的是**抽样**用例。