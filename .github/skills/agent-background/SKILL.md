# Agent Background

> 🧭 本 skill 是 `get-agent-strategy` 的子流程，通常由它编排调用；单独使用同样有效。
> 共享规则见 [`_shared/naming.md`](../_shared/naming.md)。

## Steps

1. 立绘数据来自 Gachabase（`https://zzz.gachabase.net`，beta 分支）：
   - 列表：`GET https://zzz.gachabase.net/agents/beta/__data.json?lang=chs` → 响应第 2 行是
     `{"type":"chunk","id":1,"data":[…]}`，其中 `data[0].data.entries[]` 是代理人列表
     （`id` / `slug` / `name.text`）。
   - 详情：`GET https://zzz.gachabase.net/agents/<id>/<slug>/beta/__data.json?lang=chs` →
     `data[0].data.entity.assets.splash_art_path_hash` 是立绘资源哈希，
     `data[0].data.variants[hash].webp` 是可直接下载的地址
     （形如 `https://i.gachabase.net/<key>/q:50/f:webp/plain/zzz/assets/<hash>.png`）。
   - 注意：同一位代理人可能还有一条换装记录（如 `aria` 1502、`remielle` 1582），其
     `splash_art_path_hash` 会串到别的代理人身上——**取 id 最小的那条（本体）**。

2. 跑仓库里的抓取脚本（已覆盖全部代理人，无需手工找图）：

   ```powershell
   uv run python tools/fetch_agent_backgrounds.py            # 补齐缺失的背景图
   uv run python tools/fetch_agent_backgrounds.py --dry-run  # 只报告，不落盘
   ```

   脚本会把立绘写到 `frontend/public/images/strategy/<slug>/background.webp`（Gachabase
   只提供 webp 变体，直接存即得），并在攻略 JSON **顶层**写入：

   ```json
   {
     "background": "/images/strategy/<slug>/background.webp"
   }
   ```

   已有背景的代理人会自动跳过；`--skip a,b` 可排除指定 slug。

2.1 角色框头像（`film.webp`）用另一个来源——Nanoka（`https://zzz.nanoka.cc`）：

   ```powershell
   uv run python tools/fetch_agent_films.py            # 补齐缺失的角色框头像
   uv run python tools/fetch_agent_films.py --dry-run  # 只报告，不落盘
   ```

   数据取自 `https://static.nanoka.cc/zzz/<ver>/character.json` 与
   `.../<lang>/character/<id>.json`，资产名是 `IconRolePiece<编号>.webp`（编号来自详情
   JSON 的 `icon`，个别代理人回退 `partner_info.inter_knot_icon` 的编号）。产出
   `frontend/public/images/strategy/<slug>/film.webp`，供「关键命座推荐」块使用
   （`cinemaPriority.image`）。

3. 校验：

   ```powershell
   python tools/normalize_strategy.py --check
   cd frontend; npm run test
   ```

   `frontend/tests/strategy-background.spec.ts` 会守住「每位代理人有 background 字段 +
   背景图存在 + 页面渲染 `.page-bg`」这条不变量。

> 仓库图片**统一 webp**（`frontend/public/images/` 下 522 张，约 40 MB）。新增图片请直接存
> `.webp`；批量 PNG → webp 用 `uv run --with pillow python tools/images_to_webp.py`，
> 它会同步改写全仓 `/images/…` 引用并校验无断链。

The shared renderer (`frontend/src/strategy/renderStrategy.ts`) reads this field and
renders a right-aligned, scrollable `.page-bg` layer. Do **not** edit HTML/CSS per page;
there are no per-agent `index.html` / `styles.css` files anymore. The background is
absolute (not fixed) and stays on the right without covering the page.
