# Badge

Pill-shaped status badge that mirrors the Jira workflow: To Do, In Progress, In Review, Done, Blocked.

- Fill `surface-2`, text `ink-muted`, `radius-pill`, caption size.
- Status lives in the dot only: `ink-subtle` (To Do), `warning` (In Progress), `primary-hover` (In Review), `success` (Done), `danger` (Blocked). The text label always says the status too, so colour is never the only signal.
- Pass `children` to override the label (e.g. "Sprint 3").
