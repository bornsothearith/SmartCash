# SmartCash architecture (current system)

Only what exists **today**. We add boxes when new parts are built.

```mermaid
flowchart LR
    user([Student in browser])

    subgraph cloud["Streamlit Community Cloud"]
        app["app.py<br/>screens: log in, overview, transactions,<br/>add / edit, import, budgets, forecast"]
        secrets[["Secrets box<br/>DATABASE_URL"]]
    end

    subgraph pkg["smartcash/ package"]
        auth["auth.py<br/>sign up, log in,<br/>password hashing"]
        tx["transactions.py<br/>add, edit, delete, filter"]
        imp["diary_import.py<br/>CSV / Google Form import"]
        rates["rates.py<br/>rate_for, sync_rates"]
        db["database/connection.py<br/>PostgreSQL or SQLite"]
        pgad["database/postgres.py<br/>adapter + migrations"]
        config["config.py<br/>paths + secrets"]
        ui["ui/theme.py + ui/charts.py<br/>look and charts"]
        validation["validation/<br/>transaction + CSV rules"]
    end

    neon[("Neon PostgreSQL<br/>hosted, survives restarts")]
    migr["migrations/*.sql<br/>run once, in order"]
    sqlite[("data/smartcash.db<br/>SQLite, local only<br/>(not on GitHub)")]
    csv["data/exchange_rates.csv<br/>NBC official rate"]
    gh["GitHub repo"]

    user --> app
    app --> auth
    app --> tx
    app --> imp
    app --> ui
    imp --> validation
    imp --> tx
    tx --> validation
    tx --> rates
    auth --> db
    tx --> db
    db --> config
    config -. reads .-> secrets
    db -- "DATABASE_URL set" --> pgad
    pgad --> neon
    migr --> pgad
    db -- "no DATABASE_URL<br/>(local / tests)" --> sqlite
    csv -- "loaded at start<br/>(gaps filled)" --> rates
    gh -- "auto deploy on push" --> cloud
```

**How data moves**
- The student logs in. `auth.py` checks the password hash. The password itself is never saved.
- `app.py` never writes SQL. It calls `auth.py`, `transactions.py` and `diary_import.py`.
- Every transaction function needs the `user_id`, so a user only sees their own rows.
- `database/connection.py` uses **PostgreSQL** when `DATABASE_URL` is set (live app), else the local SQLite file.
- On PostgreSQL, the first start runs any new `migrations/*.sql` file and loads the exchange rates.
- `rates.py` turns KHR into USD with the official rate of that day.
- `config.py` keeps all file paths and reads secrets from the environment or Streamlit secrets.
- A push to GitHub updates the live app on Streamlit Cloud.
