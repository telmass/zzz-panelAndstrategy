# 命名与映射规范

## 规范 slug 唯一性

`data/catalog/agent-index.json` 是全仓唯一正确的命名来源，每条含：

```json
{ "slug": "ye-shunguang", "en": "Ye Shunguang", "cn_short": "叶瞬光", "cn_full": "叶瞬光" }
```

- **slug**：`strategy/<slug>/` 目录名、`strategy/<slug>/data/<slug>.json` 与 `<slug>.strategy.json` 的文件名、
  `frontend/public/images/strategy/<slug>/` 目录名、`frontend/src/constants/strategyGuides.ts` 的 `slug` 字段，
  必须与 mapping 的 `slug` **逐字相同**。
- 发现相似但不一致（如 `orphe-magus` vs `orphie-magus`）时，**以 mapping 为准**；不可改 mapping，
  应把其他所有位置统一过来。
- 改名等于四处同改：目录名、两个数据文件名、图片目录名、登记表条目（登记表由
  `python tools/gen_strategy_guides.py` 重新生成，不手改）。

## 属性 / 职业 / 评级 → 图标 slug

| 中文 | 图标 slug | 图片 |
| --- | --- | --- |
| 流明 | `lumiflux` | `/images/attributes/lumiflux.webp` |
| 玄墨 | `auric-ink` | `/images/attributes/auric-ink.webp` |
| 凛刃 | `honed-edge` | `/images/attributes/honed-edge.webp` |
| 烈霜 | `frost` | `/images/attributes/frost.webp` |
| 风 | `wind` | `/images/attributes/wind.webp` |
| 火 | `fire` | `/images/attributes/fire.webp` |
| 冰 | `ice` | `/images/attributes/ice.webp` |
| 以太 | `ether` | `/images/attributes/ether.webp` |
| 物理 | `physical` | `/images/attributes/physical.webp` |
| 电 | `electric` | `/images/attributes/electric.webp` |

| 职业 | 图标 slug | 图片 |
| --- | --- | --- |
| 强攻 | `attack` | `/images/icons/attack.webp` |
| 击破 | `stun` | `/images/icons/stun.webp` |
| 异常 | `anomaly` | `/images/icons/anomaly.webp` |
| 支援 | `support` | `/images/icons/support.webp` |
| 防护 | `defense` | `/images/icons/defense.webp` |
| 命破 | `rupture` | `/images/icons/rupture.webp` |
| 锋御 | `armorer` | `/images/icons/armorer.webp` |

评级图标：`S` → `s.webp`，`A` → `a.webp`（`/images/grades/`）。

> ⚠️ **两套标签不要混用**：`read-zzz-agent-stats` 脚本内部用的 `ATTRIBUTE_LABELS` 键是
> `fire` / `ice` / `auricink` / `honed_edge` / `ether` / `wind` / `physical` / `Lumiflux`
> （来自 WIKI `role_attribute` 原值），而**图标 slug** 是上表的 `auric-ink` / `honed-edge` / `lumiflux`。
> 写页面时一律用图标 slug；读预设时用脚本 label。

## 图片命名与路径

- 所有图片放 `frontend/public/images/`，JSON 里**只写 `/images/…` URL**（禁止页相对 `assets/…`、
  禁止仓库相对 `frontend/public/images/…`）。
- **攻略专属文件名统一小写**：`film.webp`（角色框头像）、`tachie.webp`（立绘）、`background.webp`（右侧全身背景）、
  `cinema-2.webp` / `cinema-3.webp`（影画展示图）、`title.webp`（称号图）。
- 共享图标：`/images/agents/<agentId>.webp`、`/images/weapons/<engineId>.webp`、
  `/images/discs/ep-<entry_page_id>.webp`、`/images/skills/<key>.webp`、`/images/icons/<role>.webp`、
  `/images/attributes/<attribute>.webp`、`/images/grades/<grade>.webp`。
- 仓库图片**统一 webp**（`tools/images_to_webp.py` 批量转换并改写全仓引用）。
  JSON 里的 `/images/…` URL 与磁盘文件名的大小写与扩展名必须完全一致（Cloudflare CDN 区分大小写）。
- 新增图片一律直接存 `.webp`；批量 PNG → webp 用
  `uv run --with pillow python tools/images_to_webp.py`（它会同步改写引用并校验断链）。

## 面板模式 ≠ 职业

`panelMode` 有 `standard`（通用）/ `rupture`（命破）/ `fengyu`（锋御），与 `roleTag` 是**两个字段**，
不可由职业推断：命破/锋御代理人的 `roleTag` 恰好等于模式名，通用代理人的 `roleTag` 仍是职业名。
「通用」二字在面向用户的文案里被隐藏（`HIDE_STANDARD_MODE_LABEL`），但 `panelMode` 仍写 `'standard'`。
