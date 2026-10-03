# backend/tests — Python 测试

pytest 回归测试。运行：

```powershell
uv run pytest
```

配置在 `pyproject.toml` 的 `[tool.pytest.ini_options]`（`pythonpath = ["backend/src"]`）。

## 当前已有

| 文件 | 覆盖内容 |
| --- | --- |
| `test_panel.py` | `core/panel.py` 及模式专属计算。以重构前 `main.py` 的 `EXAMPLE` 为锚点锁定 12 项数值，另覆盖基础公式、武器副词条、命破贯穿力、锋御实际暴击率与固定锐暴伤害 |

## 计划补充（随 Vue3 迁移第 3 步）

| 文件 | 覆盖内容 |
| --- | --- |
| `test_breakdown.py` | 计算明细来源与参照实现 `calculator.js:567-583` 一致 |
| `test_presets.py` | 预设加载与结构校验 |
| `test_api.py` | FastAPI 路由（需 `httpx`，已在 dev 依赖组中） |
