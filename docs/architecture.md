# SmartCash architecture

## Sprint 2 data flow

```text
Spending diary CSV or Streamlit form
                |
                v
       Validation and duplicate checks
                |
                v
      SQLite (Sprint 2) / PostgreSQL (later)
          |                 |
          v                 v
   Daily USD/KHR rates   Dashboard summaries
```

The working Sprint 2 implementation is still intentionally small: `app.py`
provides the Streamlit screens and `db.py` provides the SQLite data layer.
The `smartcash/` package contains boundaries for the future PostgreSQL,
analytics, chart, and validation modules.

## Data rules

- Every transaction has a date, type, amount, currency, category, payment
  method, and optional note.
- KHR is converted with the rate on the transaction date, or the latest
  earlier rate when that date has no entry.
- CSV imports report imported, duplicate, and rejected rows.
- Synthetic records are marked with `is_demo = 1` and can be removed safely.
