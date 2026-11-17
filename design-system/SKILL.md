---
name: smartcash-design
description: SmartCash design system (dark, Linear-inspired, one lavender accent). Use whenever you build or change SmartCash UI — Streamlit screens, theme, charts, HTML/CSS, or sprint review pages and slides — so colours, type, spacing and status styles stay on-system.
---

# SmartCash design system

Source of truth: the SmartCash Design System artifact on claude.ai. This folder is a copy of it:

- `brand-book.md` — read first: voice, colour rules, type, spacing, shapes, sprint-slide guidance.
- `tokens.json` — every token with a usage note. `tokens.css` — the same as CSS variables.
- `components/*.md` — guidelines per component (Button, Badge, Card, Input, IssueRow, Amount).
- `components/components.css` — `sc-*` classes that implement those components in plain HTML/CSS.

## Core rules (short version)

- **Dark only.** Ground `canvas` #010102. Hierarchy = lift onto `surface-1` #0f1011 → `surface-4`, each with a 1px `hairline` #23252a border. No drop shadows, no gradients.
- **Text:** `ink` #f7f8f8 main, `ink-muted` #d0d6e0 secondary, `ink-subtle` #8a8f98 tertiary. `ink-tertiary` #62666d is for disabled only.
- **One accent:** `primary` #5e6ad2 for the main button, focus rings, brand mark. ONE primary button per view. Lavender **text** (links) uses `primary-hover` #828fff for contrast.
- **Semantic:** `success` #27a644 = income / Done; `danger` #eb5757 = expense / error / Blocked; `warning` #f2994a = In Progress / near budget. Always pair colour with a word or a +/− sign.
- **Type:** Inter (sans) and JetBrains Mono (keys, story points, money columns). Display weight 600 with negative tracking; body 400.
- **Shape:** buttons and inputs `radius-md` 8px, cards `radius-lg` 12px, badges pill. Never pill-round a button. Spacing on a 4px grid; card padding 24px.
- **Money:** tabular mono figures; USD as `$1,284.50`, KHR as `៛40,000` (whole riel).

## Applying it in this Streamlit app

Theme lives in `.streamlit/config.toml`. The on-system values are:

```toml
[theme]
base = "dark"
primaryColor = "#5e6ad2"
backgroundColor = "#010102"
secondaryBackgroundColor = "#0f1011"
textColor = "#f7f8f8"
font = "sans serif"
```

- Changing the theme changes the live app (it deploys from `main`). Follow CLAUDE.md: own branch, show the plan first, and check with the team before switching the live demo to dark.
- For custom HTML (cards, badges, amounts), inject `tokens.css` + `components/components.css` once with `st.markdown("<style>…</style>", unsafe_allow_html=True)` and use the `sc-*` classes. Keep this in a small helper module (e.g. `ui.py`), not scattered through `app.py`.
- Charts (plotly/altair): background `canvas` or `surface-1`, gridlines `hairline`, text `ink-subtle`. Income `success`, spending `danger`. Category colours must stay fixed across pages (see CLAUDE.md); pick them so neighbours differ in lightness, not hue only.
- Check text contrast is ≥ 4.5:1 on its background.
