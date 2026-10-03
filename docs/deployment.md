# 部署指南

本项目是**单机个人工具**：无账号、无数据库、无外部服务依赖。
部署的实质就是「把 `frontend/dist/` 交给静态服务器，把 FastAPI 挂起来，
让两者能互相找到」。

## 1. 部署形态选型

后端**不托管**前端静态文件（`backend/src/zzz_panel/api/app.py` 里没有任何
`StaticFiles` / `mount`），因此有三种可选形态：

| 形态 | 适用| 代价 |
| --- | --- | --- |
| **A. 同域反代**（推荐） | 任何长期使用 | 需要一个反向代理（Nginx / Caddy） |
| B. 双域分离 | 前端部署在 CDN | 前端构建产物需写绝对 API 地址，且要放开后端 CORS |
| C. 仅本地 | 自用 | 后端加 CORS 白名单，前端跑 `vite preview` |

### 为什么默认走同域

开发期前端用相对路径 `/api`，由 Vite 代理到后端，因此**开发期完全不涉及 CORS**。
生产期沿用这个思路：让页面与 API 同域，相对路径继续有效，浏览器同源策略直接放行，
CORS 配置就变成兜底而非必需。

## 2. 构建

### 前端

```powershell
cd frontend
npm ci                  # 或 npm install
npm run build           # = vue-tsc --noEmit && vite build
```

产物在 `frontend/dist/`：

```
dist/
├── index.html
└── assets/
    ├── index-<hash>.js
    └── index-<hash>.css
```

`emptyOutDir: true`，每次构建前会清空，不会残留旧hash 文件。

### 后端

后端是纯 Python 包，**没有构建步骤**。`uv sync` 即可。
若需要打包成 wheel：

```powershell
uv build               # hatchling，产出 dist/*.whl
```

`[tool.hatch.build.targets.wheel]` 已指向 `backend/src/zzz_panel`，
包内不含 `data/`——预设数据在运行时从仓库根读取，见第 5 节。

## 3. 形态 A：同域反向代理（推荐）

### 启动后端

```powershell
uv run uvicorn zzz_panel.api.app:app --host 127.0.0.1 --port 8000
```

生产建议加 `--workers N`（纯函数计算，无状态，多进程安全），
或用进程管理器（systemd / Windows 服务 / Docker）。

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name zzz-panel.example.com;

    # 静态产物
    root /srv/zzz-panel/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;   # SPA history fallback
    }

    # 静态资源带 hash，可长缓存
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API 反代到后端
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**`try_files ... /index.html` 不能省。** 前端用 history 模式路由，
直接访问 `/calculator` 或 `/guide` 时服务器上并不存在对应文件，
不回落到 `index.html` 会得到 404。

前端代码里全部使用相对路径 `/api`，因此**不需要重新构建**即可在这种部署下工作。

### Nginx 未配置时的替代方案

把 `dist/` 交给任何静态服务器（Caddy、`http-server`、`npx serve`），
再把 `/api` 反代到后端，效果相同。

## 4. 形态 B：前后端分域

需要在**构建时**注入后端绝对地址：

```powershell
# frontend/.env.production
VITE_API_BASE_URL=https://api.example.com/api
```

```powershell
cd frontend
npm run build
```

> ⚠️ `VITE_API_BASE_URL` 是 **Vite 构建期变量**，会被内联进产物。
> 运行时改环境变量**无效**，必须重新构建。

同时必须放开后端 CORS。当前白名单只有开发用的两个源
（`api/app.py`）：

```python
allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
```

跨域部署需在 `app.py` 追加你的前端域名。注意：

- `allow_credentials=False`，因此不能用 `*` 之外再叠加凭证的模式；
  若将来开启 cookie 凭证，`allow_origins` **不能**是 `*`。
- `allow_methods=["GET", "POST", "OPTIONS"]` 覆盖了全部需求。

## 5. 预设数据的部署位置

后端启动时按以下顺序定位 `data/`：

1. 模块内缓存
2. 环境变量 **`ZZZ_PANEL_DATA_DIR`**
3. 从 `__file__` 向上找同时含 `pyproject.toml` 与 `data/` 的祖先目录
4. 都没有 → `PresetLoadError`，`/api/presets/*` 返回 **503**

因此两种部署方式：

| 方式 | 做法 |
| --- | --- |
| 跑在仓库里 | 无需配置，第3 条规则会找到仓库根 |
| 只装了 wheel | **必须**设 `ZZZ_PANEL_DATA_DIR` 指向含 `agent-presets.json` / `weapon-presets.json` 的目录 |

```powershell
$env:ZZZ_PANEL_DATA_DIR = "C:\srv\zzz-panel\data"
uv run uvicorn zzz_panel.api.app:app --port 8000
```

**忘了这一步的症状**：页面能开，但代理人/音擎下拉框为空，控制台报
`预设数据加载失败`，`/api/presets/agents` 返回 503 且 `detail` 说明找不到目录。

## 6. 部署自检清单

```powershell
# 1. 探活
curl http://127.0.0.1:8000/api/health          # 期望 {"status":"ok"}

# 2. 预设可读
curl http://127.0.0.1:8000/api/presets/agents   # 期望 items 长度 60
curl http://127.0.0.1:8000/api/presets/weapons  # 期望 items 长度 100

# 3. 计算可用（空body 即合法请求，应返回 12 个totals 键）
curl -X POST http://127.0.0.1:8000/api/panel/calc `
  -H "Content-Type: application/json" -d '{}'
```

浏览器侧逐项确认：

- [ ] `/` 打开，显示两张入口卡片
- [ ] `/calculator` 直接访问（**刷新 F5**）能正常渲染——验证 history fallback
- [ ] `/guide` 直接访问能正常渲染
- [ ] 计算器选一名代理人 → 载入预设 → 结果区出现数值且明细非空
- [ ] 切换命破/锋御模式 → 专属行出现/消失
- [ ] 浏览器控制台无报错
- [ ] Network 面板无 404 / 5xx

## 7. 更新部署

```powershell
git pull
uv sync
cd frontend; npm ci; npm run build; cd ..
# 重启后端进程
```

若这次更新动了规则表或预设，记得先跑同步：

```powershell
python tools/sync_presets.py --options
python tools/sync_presets.py --to-legacy
```

## 8. 不适用的部署话题

以下是通用运维文档的常见章节，本项目**明确不涉及**，故不写：

| 话题 | 原因 |
| --- | --- |
| 容器编排 / K8s | 单进程个人工具，用不上 |
| 水平扩缩容 | 计算是纯函数、无状态、耗时在毫秒级 |
| 分布式缓存 / 消息队列 | 唯一的缓存是进程内按 mtime 判定的一层 |
| 数据库与迁移 | 无持久化，唯一的「状态」是 `data/` 下的三个 JSON |
| 认证授权 | 见下|
| 监控告警 / 日志聚合 | `/api/health` 足够；生产用 `--log-level info` |
| CI/CD 流水线 | 仓库内没有 CI 配置。需要时按 [development.md](development.md) 第 10 节的检查项组装 |

### 关于认证

**当前无任何鉴权。** `/api/panel/calc` 是纯计算、不写任何状态，
`/api/presets/*` 只读公开的游戏数据，因此公网暴露风险有限。

但若要放到公网，仍建议加一层反向代理 Basic Auth 或 IP 白名单：
无鉴权意味着任何人都能调用接口，也意味着**任何人都能读你的预设数据文件路径**
（503 的 `detail` 会回显文件路径与原因，见 [api-reference.md](api-reference.md)）。

## 9. 相关文档

- [api-reference.md](api-reference.md) —— 接口与状态码
- [development.md](development.md) —— 构建与本地运行
- [architecture.md](architecture.md) —— 分层与依赖方向
- [requirements.md](requirements.md) —— 非目标与已知限制