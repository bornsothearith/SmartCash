# IssueRow

One dense row for a Jira-style issue: priority bars, key, title, story points and status badge. Use it on sprint review slides and backlog screens.

- Canvas row with a `hairline` bottom rule; hover lifts to `surface-1`.
- Key and points in the mono face, `ink-subtle`. Title in `ink`, truncated with an ellipsis.
- Priority is 0–3 bars in `ink-muted` (no colour), so the status badge stays the only coloured mark.
- Wrap rows in a bordered container with `radius-lg`. The consumer provides the issue data (copy it from Jira).
