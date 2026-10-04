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
| **D. Cloudflare Workers** | 想要一个公网直开的网址，又不维护服务器 | Python 只能装纯包与 PyEmscripten wheel；免费额度有请求上限 |

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
包内不含 `data/`——预设数据在运行时从仓库根读取，见第 6 节。

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
    server_name zzz-panel-and-strategy.example.com;

    # 静态产物
    root /srv/zzz-panel-and-strategy/dist;
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

## 5. 形态 D：Cloudflare Workers（一个 Worker 同源）

面向「想有个公网直开的网址、又不想维护服务器」的场景：**FastAPI 与前端静态产物
由同一个 Worker 提供**，页面与 API 同域，因此 `VITE_API_BASE_URL` 不用改、
后端 CORS 也不用放开。它就是第 3 节那套 Nginx 配置的反代，只是把反代换成了
Wrangler 的 assets 路由。

| 项 | 值 |
| --- | --- |
| 入口 | `backend/src/worker.py` |
| 配置 | `wrangler.jsonc` |
| 运行时 | Python Workers（CPython 编译到 WebAssembly 的 Pyodide） |
| 费用 | 免费额度可用。不需要 Docker，也不需要服务器 |

### 5.1 路由分工

| 路径 | 由谁处理 |
| --- | --- |
| `/api/*` | Worker 里的 FastAPI |
| `/docs`、`/openapi.json` | 同上，FastAPI 自带的接口文档 |
| `/`、`/assets/*` | Workers 静态资源层，不进 Worker（不计 CPU） |
| `/calculator`、`/guide` | 静态资源层未命中 → 按 `not_found_handling` 回落 `index.html` |

最后一行就是第 3 节 `try_files $uri $uri/ /index.html` 的等价物。

### 5.2 部署步骤

前置条件（两条都是实测踩到的）：

- **`uv` >= 0.12.3**。`pywrangler sync` 会自己检查并直接报错退出。版本过低时
  报 `ERROR uv version at least 0.12.3 required`，升级：`uv self update`
- **`wrangler.jsonc` 必须是纯 ASCII**。pywrangler 用 Python 的**本地编码**
  解析这个文件，中文 Windows（GBK）下任何非 ASCII 字节都会让部署在解析阶段
  就失败（`'gbk' codec can't decode byte ...`）。所以该文件的注释是英文的，
  说明文字一律放本文档。

```powershell
# 0. 一次性：装 Wrangler，并在浏览器里授权 Cloudflare 账号
npx wrangler login

cd frontend
npm ci
npm run build        # 产物 frontend/dist/，wrangler.jsonc 的 assets.directory 指向它
cd ..

# 1. 生成预设数据的包内镜像（原因见 5.3）
uv run python tools/bundle_worker_data.py

# 2. 部署（首次会下载 Pyodide 解释器，较慢）
uv run --group worker pywrangler deploy
```

成功后拿到 `https://zzz-panel-and-strategy.<你的子域>.workers.dev`。
想用自己的域名，在 Cloudflare 控制台给该 Worker 加一条 Custom Domain 即可
（域名需托管在 Cloudflare DNS）。

`pywrangler sync` 会生成 `pylock.toml`（PEP 751，Worker 环境的锁文件）。
**这个文件要提交**：它固定了 Pyodide 里每个依赖的版本，不提交的话同一份代码在
不同机器上会部署出不同的 Worker。`uv.lock` 管本地，两者都要。

### 5.3 为什么需要 tools/bundle_worker_data.py

**`pywrangler` 只上传 `.py` 文件。** 入口目录下的 `.json`、`.html` 一类资源会被
**静默**丢弃——不报错、不警告，只是线上读不到。仓库根的 `data/` 因此永远上不去，
而 `presets/loader.py` 原本靠「从 `__file__` 向上找同时含 `pyproject.toml` 与
`data/` 的祖先目录」定位数据，在 Worker 里必然失败。

所以数据必须编译成一个 **Python 模块** `zzz_panel/_bundled_data.py`，由

```powershell
uv run python tools/bundle_worker_data.py
```

生成。它把 `data/agent-presets.json` 与 `data/weapon-presets.json` 的原文按
「每行一个相邻字符串字面量」存进两个常量，因此：

- 与源文件**逐字节**一致，可被 `--check` 校验，也不需要 `importlib.resources`
- 不依赖 Worker 虚拟文件系统的任何行为
- **唯一真实源仍是 `data/`**，生成物不提交（见 `.gitignore`）

`options.json` **不**编译进去：它由前端在构建期经 Vite 别名 `@data` 读真实源，
根本不经过后端。

### 怎么确认生成物真的进了包

用干跑把产物 dump 出来看，别只看命令输出：

```powershell
uv run --group worker pywrangler deploy --dry-run --outdir .wrangler-dry
Get-ChildItem .wrangler-dry\zzz_panel -Recurse -File | Measure-Object
```

产物里的 `zzz_panel/` 应包含 `_bundled_data.py`。看不到就是没生成或没上传。

**忘了这一步的症状**：页面能开、`/api/panel/calc` 返回 200，但两个级联选择器
只有职业分组、没有具体条目，`/api/presets/*` 返回 503。

### 5.4 本地预览

```powershell
uv run python tools/bundle_worker_data.py
cd frontend; npm run build; cd ..
uv run --group worker pywrangler dev
```

`pywrangler dev` 跑的是 workerd + Pyodide，本地就能看到 Worker 的真实行为，
比先部署再试错快。首次运行要下载 Pyodide 解释器，较慢。

### 5.5 已知约束

| 约束 | 说明 |
| --- | --- |
| 只能装纯 Python 与带 PyEmscripten wheel 的包 | 因此 `[project.dependencies]` 里不能有 `uvicorn[standard]`、`matplotlib` 这类带 C/Rust 扩展的包，否则 `pywrangler sync` 直接失败。这也是把它们移到 dev 组与可选组的原因 |
| **只上传 `.py`** | 包里的 `.json` / `.html` 会被静默丢弃，见 5.3 |
| **不读系统代理** | wrangler 是 Node 程序，不走 WinINET 系统代理。直连 Cloudflare 超时时要显式给环境变量（见 5.7） |
| 请求额度 | 免费版有每日请求上限。计算是纯函数、毫秒级，CPU 时间不是瓶颈 |
| 冷启动 | Pyodide 快照在**部署时**生成，运行时不必重跑依赖初始化。实测启动约 2.3 s |
| 内存文件系统 | 不能写盘。本项目只读不写，无需持久化 |
| 无鉴权 | 同第 9 节：公网暴露意味着任何人都能调接口 |

### 5.6 出问题先查这两处

- **503 + 选择器空** → 生成物缺失或过期，见 5.3；先看 503 的 `detail`
- **`/api` 404、但页面正常** → `run_worker_first` 与实际请求路径不匹配；
  前端打的是 `/api/*`（见 `frontend/src/api/panel.ts`）
- **`The request to Cloudflare's API timed out`** → 见 5.7

### 5.7 需要代理时

Node 不读 Windows 的系统代理设置。若直连 Cloudflare API 超时而浏览器正常，
把代理显式交给 Node：

```powershell
$env:NODE_USE_ENV_PROXY = "1"
$env:HTTPS_PROXY = "http://127.0.0.1:7892"   # 换成你自己的端口
$env:HTTP_PROXY  = "http://127.0.0.1:7892"
uv run --group worker pywrangler deploy
```

wrangler 启动时若看到 `Proxy environment variables detected` 即表示已生效。
可用 `npx wrangler whoami` 先验证，它会打印当前账号与 Token 权限。

## 6. 预设数据的部署位置

后端启动时按以下顺序定位 `data/`：

1. 模块内缓存
2. 环境变量 **`ZZZ_PANEL_DATA_DIR`**
3. 从 `__file__` 向上找同时含 `pyproject.toml` 与 `data/` 的祖先目录
4. 都没有 → `PresetLoadError`，`/api/presets/*` 返回 **503**

Worker 不在这条链里：它连磁盘都没有，`load_agents()` 会直接改读包内编译产物
`zzz_panel/_bundled_data.py`（见 5.3）。上面第 3 条命中时不看编译产物，
以保证仓库里的 `data/` 始终是唯一真源。

因此三种部署方式：

| 方式 | 做法 |
| --- | --- |
| 跑在仓库里 | 无需配置，第3 条规则会找到仓库根 |
| 只装了 wheel | **必须**设 `ZZZ_PANEL_DATA_DIR` 指向含 `agent-presets.json` / `weapon-presets.json` 的目录 |
| Cloudflare Worker | 磁盘上没有 `data/`，改读包内编译产物 `zzz_panel/_bundled_data.py`。部署前先跑 `python tools/bundle_worker_data.py`，见 5.3 |

```powershell
$env:ZZZ_PANEL_DATA_DIR = "C:\srv\zzz-panel-and-strategy\data"
uv run uvicorn zzz_panel.api.app:app --port 8000
```

**忘了这一步的症状**：页面能开，但代理人与音擎两个级联选择器都只有职业分组、没有具体条目，
控制台报 `预设数据加载失败`，`/api/presets/agents` 返回 503 且 `detail` 说明找不到目录。

## 7. 部署自检清单

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
- [ ] 计算器在「一、基础面板」里选一名**命破**代理人 → 载入预设 → 结果区出现贯穿力与闪能自动累积行
- [ ] 换选一名**通用**代理人 → 上述两行消失、回到 12 行（模式由预设的 `panelMode` 决定，界面没有独立的模式切换器）
- [ ] 浏览器控制台无报错
- [ ] Network 面板无 404 / 5xx

## 8. 更新部署

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

形态 D（Cloudflare Workers）没有「重启」这一步，重新 deploy 即覆盖，
但**编译产物必须一起重新生成**，否则线上读的是旧预设：

```powershell
python tools/bundle_worker_data.py
cd frontend; npm run build; cd ..
uv run --group worker pywrangler deploy
```

## 9. 不适用的部署话题

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

## 10. 相关文档

- [api-reference.md](api-reference.md) —— 接口与状态码
- [development.md](development.md) —— 构建与本地运行
- [architecture.md](architecture.md) —— 分层与依赖方向
- [requirements.md](requirements.md) —— 非目标与已知限制