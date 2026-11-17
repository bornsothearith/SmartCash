# SmartCash architecture (current system)

Only what exists **today**. We add boxes when new parts are built
(for example PostgreSQL in SCG-35).

```mermaid
flowchart LR
    user([Student in browser])

    subgraph cloud["Streamlit Community Cloud"]
        app["app.py<br/>screens: log in, transactions, add"]
    end

    subgraph pkg["smartcash/ package"]
        auth["auth.py<br/>sign up, log in,<br/>password hashing"]
        tx["transactions.py<br/>add, check, filter"]
        rates["rates.py<br/>rate_for, sync_rates"]
        db["db.py<br/>connection + tables"]
        config["config.py<br/>paths + secrets"]
        theme["theme.py<br/>colours, cards, table"]
        syn["synthetic.py<br/>fake test data"]
    end

    sqlite[("data/smartcash.db<br/>SQLite<br/>(not on GitHub)")]
    csv["data/exchange_rates.csv<br/>NBC official rate"]
    fake["data/synthetic/*.csv<br/>(not on GitHub)"]
    gh["GitHub repo"]

    user --> app
    app --> auth
    app --> tx
    app --> theme
    auth --> db
    tx --> db
    tx --> rates
    db --> sqlite
    db --> config
    csv -- "loaded at start<br/>(gaps filled)" --> rates
    syn --> tx
    syn --> fake
    gh -- "auto deploy on push" --> cloud
```

**How data moves**
- The student logs in. `auth.py` checks the password hash. The password itself is never saved.
- `app.py` never writes SQL. It calls `auth.py` and `transactions.py`.
- Every transaction function needs the `user_id`, so a user only sees their own rows.
- `rates.py` turns KHR into USD with the official rate of that day.
- `config.py` keeps all file paths and reads secrets from the environment or Streamlit secrets.
- A push to GitHub updates the live app on Streamlit Cloud.
