# 部署指南

本项目是**单机个人工具**：无账号、无数据库、无外部服务依赖。

**线上站点是 <https://zzzstrategy.cc.cd>，形态 D（Cloudflare Workers），公开访问。**
下面四种形态里，A/B 是自建服务器的替代方案，C 是不部署，D 是当前生产形态。

## 1. 部署形态选型

后端**不托管**前端静态文件（`backend/src/zzz_panel/api/app.py` 里没有任何
`StaticFiles` / `mount`），因此有四种可选形态：

| 形态 | 适用 | 代价 |
| --- | --- | --- |
| A. 同域反代 | 已有服务器、不想引入 Cloudflare | 需要一个反向代理（Nginx / Caddy） |
| B. 双域分离 | 前端部署在 CDN | 前端构建产物需写绝对 API 地址，且要放开后端 CORS |
| C. 仅本地 | 自用，不上线 | 无 |
| **D. Cloudflare Workers（线上在用）** | 想要一个公网直开的网址，又不维护服务器 | Python 只能装纯包与 PyEmscripten wheel；免费额度有请求上限 |

### 形态 C：仅本地

不部署，只在本机跑：`pwsh tools/dev.ps1`（Vite 5173 + uvicorn 8000）。
`/api` 由 Vite 代理同源转发，因此连 CORS 都不涉及——见第 3 节末尾的说明。

### 为什么默认走同域

开发期前端用相对路径 `/api`，由 Vite 代理到后端，因此**开发期完全不涉及 CORS**。
生产期沿用这个思路：让页面与 API 同域，相对路径继续有效，浏览器同源策略直接放行，
CORS 配置就变成兜底而非必需。形态 D 用 `run_worker_first` 天然满足这一点。

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

`[tool.hatch.build.targets.wheel]` 已指向 `backend/src/zzz_panel`。
wheel 里**不含 `data/` 目录**——本地与自建部署在运行时从仓库根读取（见第 6 节）；
形态 D 则改读编译进包的 `zzz_panel/_bundled_data.py`（见 5.3）。

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

线上地址：**<https://zzzstrategy.cc.cd>**（另有一个 `workers.dev` 备用地址）。

| 项 | 值 |
| --- | --- |
| 入口 | `backend/src/worker.py` |
| 配置 | `wrangler.jsonc` |
| 运行时 | Python Workers（CPython 编译到 WebAssembly 的 Pyodide） |
| 费用 | 免费额度可用。不需要 Docker，也不需要服务器 |
| 站点可用性 | 与任何一台自有服务器无关。部署完即可关机关机 |

### 5.1 路由分工

| 路径 | 由谁处理 |
| --- | --- |
| `/api/*` | Worker 里的 FastAPI |
| `/docs`、`/openapi.json` | 同上，FastAPI 自带的接口文档 |
| `/`、`/assets/*` | Workers 静态资源层，不进 Worker（不计 CPU） |
| `/calculator`、`/guide` | 静态资源层未命中 → 按 `not_found_handling` 回落 `index.html` |

最后一行就是第 3 节 `try_files $uri $uri/ /index.html` 的等价物。

### 5.2 部署步骤

前置条件（三条都是实测踩到的）：

- **`uv` >= 0.12.3**。`pywrangler sync` 会自己检查并直接报错退出。版本过低时
  报 `ERROR uv version at least 0.12.3 required`，升级：`uv self update`
- **`wrangler.jsonc` 必须是纯 ASCII**。pywrangler 用 Python 的**本地编码**
  解析这个文件，中文 Windows（GBK）下任何非 ASCII 字节都会让部署在解析阶段
  就失败（`'gbk' codec can't decode byte ...`）。所以该文件的注释是英文的，
  说明文字一律放本文档。
- **本机要有可用的 HTTP 代理**（中国大陆部署机基本都必需）。wrangler 是 Node
  程序，不读 Windows 系统代理，直连 `api.cloudflare.com` 会超时。写法见 5.8，
  建议直接写进部署脚本，别每次手敲。

```powershell
# 0. 一次性：装 Wrangler，并在浏览器里授权 Cloudflare 账号
npx wrangler login

# 0.5 每次都带上：wrangler 是 Node 程序，不读 Windows 系统代理
$env:NODE_USE_ENV_PROXY = "1"
$env:HTTPS_PROXY = "http://127.0.0.1:7892"   # 换成你自己的端口
$env:HTTP_PROXY  = "http://127.0.0.1:7892"

cd frontend
npm ci
npm run build        # 产物 frontend/dist/，wrangler.jsonc 的 assets.directory 指向它
cd ..

# 1. 生成预设数据的包内镜像（原因见 5.3）
uv run python tools/bundle_worker_data.py

# 2. 部署（首次会下载 Pyodide 解释器，较慢）
uv run --group worker pywrangler deploy
```

部署成功后，Worker 上会有两个可达地址：

| 地址 | 说明 |
| --- | --- |
| `https://zzzstrategy.cc.cd` | **正式地址**。自定义域名，NS 已委派到 Cloudflare（`tara` / `brett`），A 记录为 Cloudflare 任播 IP 且开启代理 |
| `https://zzz-panel-and-strategy.<你的子域>.workers.dev` | Cloudflare 自动分配，作为备用入口 |

绑定自定义域名的位置：Cloudflare 控制台 → `Workers & Pages` →
`zzz-panel-and-strategy` → `Settings` → `Domains & Routes` → `Add` →
`Custom domain`。域名必须已托管在 Cloudflare DNS。

> **国内网络直连这两个地址都会被重置**（按 SNI 阻断，TCP 443 能连通但握手阶段
> 被 RST）。这是本地网络环境问题，**不是站点故障**——境外网络与 Cloudflare 边缘
> 正常。用代理访问即可。

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

### 5.4 怎么确认生成物真的进了包

用干跑把产物 dump 出来看，别只看命令输出：

```powershell
uv run --group worker pywrangler deploy --dry-run --outdir .wrangler-dry
Get-ChildItem .wrangler-dry\zzz_panel -Recurse -File | Measure-Object
```

产物里的 `zzz_panel/` 应包含 `_bundled_data.py`。看不到就是没生成或没上传。

**忘了这一步的症状**：页面能开、`/api/panel/calc` 返回 200，但两个级联选择器
只有职业分组、没有具体条目，`/api/presets/*` 返回 503。

### 5.5 本地预览

```powershell
uv run python tools/bundle_worker_data.py
cd frontend; npm run build; cd ..
uv run --group worker pywrangler dev
```

`pywrangler dev` 跑的是 workerd + Pyodide，本地就能看到 Worker 的真实行为，
比先部署再试错快。首次运行要下载 Pyodide 解释器，较慢。

### 5.6 已知约束

| 约束 | 说明 |
| --- | --- |
| 只能装纯 Python 与带 PyEmscripten wheel 的包 | 因此 `[project.dependencies]` 里不能有 `uvicorn[standard]` 这类带 C/Rust 扩展的包，否则 `pywrangler sync` 直接失败。这也是把 uvicorn 移进 dev 组、把 Worker 工具链单列为 `worker` 组的原因 |
| **只上传 `.py`** | 包里的 `.json` / `.html` 会被静默丢弃，见 5.3 |
| **不读系统代理** | wrangler 是 Node 程序，不走 WinINET 系统代理。直连 Cloudflare 超时时要显式给环境变量（见 5.8） |
| 请求额度 | 免费版有每日请求上限。计算是纯函数、毫秒级，CPU 时间不是瓶颈 |
| 冷启动 | Pyodide 快照在**部署时**生成，运行时不必重跑依赖初始化。实测启动约 2.3 s |
| 内存文件系统 | 不能写盘。本项目只读不写，无需持久化 |
| 无鉴权 | 刻意如此，依据与残留风险见 [5.9](#59-访问控制当前是公开的) |

### 5.7 出问题先查这两处

- **503 + 选择器空** → 生成物缺失或过期，见 5.3；先看 503 的 `detail`
- **`/api` 404、但页面正常** → `run_worker_first` 与实际请求路径不匹配；
  前端打的是 `/api/*`（见 `frontend/src/api/panel.ts`）
- **`The request to Cloudflare's API timed out`** → 见 5.8

### 5.8 需要代理时

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

### 5.9 访问控制：当前是公开的

**本项目刻意公开。** 任何人都能打开 <https://zzzstrategy.cc.cd> 直接用，无需登录、
无需凭据。没有配置 Cloudflare Access，也没有在 Worker 里写鉴权。

自测是否被 Access 挡着（被挡住时长这样）：

```powershell
$url = "https://zzzstrategy.cc.cd/"
try { Invoke-WebRequest -Uri $url -MaximumRedirection 0 -ErrorAction Stop | Out-Null; "公开" }
catch { "被 Access 挡住 -> " + $_.Exception.Response.Headers["Location"] }
```

响应头里出现 `cf-access-*` 或 `Set-Cookie: CF_Authorization` 也说明 Access 生效了。

#### 公开的依据

| 接口 | 为什么可以公开 |
| --- | --- |
| `POST /api/panel/calc` | 纯函数计算，不写任何状态、不落盘、不读用户数据 |
| `GET /api/presets/*` | 只读公开的游戏数据（代理人、音擎、选项表） |
| `GET /api/health` | 只回一个固定字符串 |

全站没有账号、没有个人信息、没有可写的数据面。

#### 两点残留风险

| 风险 | 说明与对策 |
| --- | --- |
| 免费额度被消耗 | Workers 免费版有每日请求上限，别人刷流量会吃掉你的额度。计算是毫秒级的纯函数，CPU 不是瓶颈，瓶颈是请求数。真被刷了再上 WAF 限速（`Cloudflare → 你的域 → Security → WAF → Rate limiting rules`），不必提前加 |
| 503 的 `detail` 会回显路径 | 预设加载失败时，响应里带文件路径。现在只是包内生成物的模块名，不会泄露你的本机目录；但**不要把用户目录写进任何错误信息**（见 [api-reference.md](api-reference.md)） |

#### 如果哪天想改成私有

用 **Cloudflare Access**，零代码：

1. 控制台完成一次 Zero Trust 初始化（生成 `<团队名>.cloudflareaccess.com`）
2. `Workers & Pages` → `zzz-panel-and-strategy` → `Settings` → `Domains & Routes`
3. `workers.dev` 那一行点 **Enable Cloudflare Access**
4. **Manage Cloudflare Access** → 动作 `Allow`，规则选 **Emails** 并填具体邮箱

为什么不用「Worker 内自己加 Basic Auth」：我们的 `run_worker_first` 只放行
`/api/*` 等少数路径，其余静态资源由资源层直接返回、**根本不进 Worker**，
脚本里的鉴权拦不住 `/` 和 `/assets/*`。改 `run_worker_first: true` 能解决，
但每个 `.png`、每个 `.js` 都要过一次 Worker（略增延迟，且静态资源请求开始计入
请求数与 CPU）。Access 挡在 Worker 外面，官方说明它同时保护 Worker 与静态资源。

两个坑：别选 **Email domain** 规则（那会允许整个邮箱域名的人通过）；
别漏 Preview URLs（否则每个版本预览地址都还是公开的）。
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

> 下列命令是 **PowerShell**。不要照抄 `curl -X POST ... -d '{}'`：PowerShell 5.1 里
> `curl` 是 `Invoke-WebRequest` 的别名，不认这些参数。

自建部署（形态 A/B/C，地址按实际改）：

```powershell
# 1. 探活
Invoke-RestMethod http://127.0.0.1:8000/api/health          # 期望 {"status":"ok"}

# 2. 预设可读
(Invoke-RestMethod http://127.0.0.1:8000/api/presets/agents).items.Length   # 期望 60
(Invoke-RestMethod http://127.0.0.1:8000/api/presets/weapons).items.Length  # 期望 100

# 3. 计算可用（空body 即合法请求，应返回 12 个 totals 键）
(Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/panel/calc `
  -ContentType 'application/json' -Body '{}').totals.PSObject.Properties.Name.Count
```

线上 Worker（形态 D）把上面的 `127.0.0.1:8000` 换成 `https://zzzstrategy.cc.cd` 即可，
**并且要带代理**（见 5.8）。

浏览器侧逐项确认：

- [ ] `/` 打开，显示两张入口卡片
- [ ] `/calculator` 直接访问（**刷新 F5**）能正常渲染——验证 history fallback
- [ ] `/guide` 直接访问能正常渲染
- [ ] 计算器在「一、基础面板」里选一名**命破**代理人 → 载入预设 → 结果区出现贯穿力与闪能自动累积行
- [ ] 换选一名**通用**代理人 → 上述两行消失、回到 12 行（模式由预设的 `panelMode` 决定，界面没有独立的模式切换器）
- [ ] 浏览器控制台无报错
- [ ] Network 面板无 404 / 5xx
- [ ] 响应头无 `cf-access-*`、无 `Set-Cookie`（确认仍是公开状态，见 5.9）

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
python tools/bundle_worker_data.py            # 或先跑 --check 确认有没有漂移
cd frontend; npm run build; cd ..
$env:NODE_USE_ENV_PROXY = "1"
$env:HTTPS_PROXY = "http://127.0.0.1:7892"
$env:HTTP_PROXY  = "http://127.0.0.1:7892"
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
| 认证授权 | 全站刻意公开、无鉴权，见 [5.9](#59-访问控制当前是公开的) |
| 监控告警 / 日志聚合 | `/api/health` 足够；Wrangler 自带 `observability`（见 `wrangler.jsonc`） |
| CI/CD 流水线 | 仓库内没有 CI 配置。需要时按 [development.md](development.md) 第 10 节的检查项组装 |

### 关于认证

**形态 D 刻意公开**，依据、残留风险、以及「想改成私有该怎么做」全部集中在
[5.9](#59-访问控制当前是公开的)，本文不重复。

形态 A/B/C 本身也无鉴权：`/api/panel/calc` 是纯计算、不写任何状态，
`/api/presets/*` 只读公开的游戏数据。若放到公网，A/B 形态在反代上加 Basic Auth
或 IP 白名单即可；D 形态用 Cloudflare Access。

无论哪种形态，都请先看 [api-reference.md](api-reference.md) 里 503 响应会回显
文件路径这一点——无鉴权意味着任何人都能读到你的目录结构。

## 10. 相关文档

- [api-reference.md](api-reference.md) —— 接口与状态码
- [development.md](development.md) —— 构建与本地运行
- [architecture.md](architecture.md) —— 分层与依赖方向
- [requirements.md](requirements.md) —— 非目标与已知限制