# SmartCash

A dark, precise, quiet system for the SmartCash app and its sprint reviews: one lavender accent, a charcoal surface ladder, hairline borders, dense rows.

> **Source.** Adapted from the Linear-inspired `DESIGN.md` in VoltAgent's awesome-design-md collection (listed in awesome-claude-design). Values are copied exactly from it. This is *inspired by* that look; it carries no Linear name, logo or font. Additions made for SmartCash are marked **Added** below.

## Where it is used

1. **The SmartCash app** (USD/KHR spending tracker): screens, forms, balances.
2. **Sprint review material**: slides, sprint reports and demo pages that show Jira issues, velocity and goals.

## Content fundamentals

- Short, plain, specific. Sentence case for everything except eyebrows.
- Say the number: "21 points", "$1,284.50 spent", not "great progress".
- Issue keys in mono (`SC-42`). Status words match the Jira board exactly: To Do, In Progress, In Review, Done, Blocked.
- Buttons are verbs: "Add expense", "Start sprint".

## Visual foundations

**Colour.** Dark only (the source has no light theme).
- Ground is `canvas` (#010102). Hierarchy comes from lifting onto `surface-1` → `surface-4`, each with a 1px `hairline` border. No drop shadows.
- Text: `ink` for main text, `ink-muted` secondary, `ink-subtle` tertiary. `ink-tertiary` is for disabled only (3.6:1).
- `primary` lavender is scarce: the one primary button per view, focus rings, the brand mark. For lavender **text** (links) use `primary-hover`, since `primary` text on `surface-1` is only 4.0:1.
- Semantic: `success` (Done, income). **Added:** `danger` (expense, error, Blocked) and `warning` (In Progress, near budget). They differ in lightness as well as hue, and every coloured state also has a text label or sign.
- Don't: lavender fills on sections, gradients, a second decorative accent, pure #000 as the ground.

**Type.** Inter (stand-in for the source's proprietary face) and JetBrains Mono, both from Google Fonts.
- Display weight 600 with strong negative tracking (`display-xl` 80px at −3px); body 400 at near-zero tracking.
- `eyebrow` is the only style with positive tracking (+0.4px), uppercase.
- Mono only for issue keys, story points and money columns.

**Space and shape.** 4px base: `space-xxs` 4 → `space-section` 96. Card padding `space-lg` (24px).
- `radius-md` (8px) for buttons and inputs, `radius-lg` (12px) for cards, `radius-xl` (16px) for screenshot panels, `radius-pill` for status badges only. Never pill-round a button.

**Layout.** Max width ~1280px. Card grids 3-up desktop, 2-up tablet, 1-up phone. Product screenshots are the hero of each section and are framed in `surface-1` panels.

## Components

`Button`, `Badge` (sprint status), `Card`, `Input`, `IssueRow` (one Jira issue), `Amount` (USD/KHR money). See each component's guidelines.

## For sprint slides

- Title slide: `display-lg` on `canvas`, eyebrow "SPRINT 3 REVIEW".
- Goal / velocity: two `Card`s, the current one `featured`.
- Done vs not done: a stack of `IssueRow`s copied from the Jira board.
- Demo: app screenshot in a `surface-1` panel with `radius-xl`.

## Iconography and logo

No logo yet (the team is choosing one from Claude Design options). Until then, use the name "SmartCash" in Inter 600 as a wordmark; never improvise a mark. If icons are needed, use simple 1.5px stroke line icons in `ink-muted`.
