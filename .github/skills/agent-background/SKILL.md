---
name: agent-background
description: Download an agent's full-body image from gachabase and add it as a right-aligned, scrollable background to that agent's strategy detail page.
---

# Agent Background

## Steps

1. Find the agent on `https://zzz.gachabase.net/agents/beta?lang=chs` (beta). Search by Chinese name. The full-body image URL follows pattern `https://i.gachabase.net/.../plain/zzz/assets/<hash>.png`.
2. Download it to `frontend/public/images/strategy/<slug>/background.png`.
3. Add the background path to the **top level** of
   `strategy/<slug>/data/<slug>.strategy.json`:

```json
{
  "background": "/images/strategy/<slug>/background.png"
}
```

4. Run `python tools/normalize_strategy.py --check` and the frontend tests.

The shared renderer (`frontend/src/strategy/renderStrategy.ts`) reads this field and
renders a right-aligned, scrollable `.page-bg` layer. Do **not** edit HTML/CSS per page;
there are no per-agent `index.html` / `styles.css` files anymore. The background is
absolute (not fixed) and stays on the right without covering the page.
