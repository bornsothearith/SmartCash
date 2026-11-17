# SmartCash

Track what students spend in US dollars (USD) and Cambodian riel (KHR).

**Sprint 1**
- **SCG-31 Add expense**: date, amount, USD or KHR, category, payment method, note. Every field is checked before saving.
- **SCG-33 View and filter transactions**: filter by dates, categories and type; shows count and USD total.

**Sprint 2**
- **SCG-68 Keep data private**: see "Data & privacy" below.
- **SCG-28 USD/KHR exchange-rate table**: see "Exchange rates" below.
- **SCG-21 Diagrams**: [architecture](docs/architecture.md) and [database ERD](docs/erd.md).
- **New look** (from [docs/design/smartcash-ui-design.pdf](docs/design/smartcash-ui-design.pdf)):
  sidebar menu, coloured cards, USD shown next to every KHR amount.

**Backlog, built early**
- **SCG-75 User accounts**: sign up, log in, log out. Each user only sees their own data.

## Run it
```
pip install -r requirements.txt
streamlit run app.py
```
Then click **Sign up** and make an account (use a nickname, not your real name).

## Test it
```
pip install pytest
python -m pytest tests
```

## Folders
```
app.py                  the Streamlit app (screens only, starts here)
smartcash/              all the logic
  config.py             file paths + secrets (SCG-68)
  db.py                 SQLite connection and tables
  auth.py               sign up, log in, password hashing (SCG-75)
  transactions.py       add, check and filter transactions (SCG-31, SCG-33)
  rates.py              daily USD/KHR rates (SCG-28)
  synthetic.py          fake test data (SCG-29)
  theme.py              colours, cards and table (UI design)
data/
  exchange_rates.csv    NBC official rates (public, on GitHub)
  smartcash.db          the database (NOT on GitHub)
  synthetic/, real/     data files (NOT on GitHub)
docs/                   diagrams, design PDF
tests/                  one test file per story
.streamlit/config.toml  theme colours
```

## Accounts and passwords (SCG-75)
- **Passwords are never saved.** We save a **scrypt hash** with a random salt
  (built into Python, no extra library). Even we can't read your password.
- Wrong username and wrong password show the **same** message, so nobody can
  find out which usernames exist.
- **5 wrong passwords → account locked for 5 minutes.**
- Password rules: at least 8 characters, with a letter and a number, not the same as the username.
- Only a username is stored. **No real name, email or phone number.**
- Every transaction has a `user_id`. All reads and deletes filter by it, so
  users can't see each other's data.
- Log out clears everything from the session. Reloading the page also logs you out
  (Streamlit keeps the login only while the page is open).

## Fake test data (SCG-29)
```
python -m smartcash.synthetic          # writes data/synthetic/sample.csv
```
- Normal rows: expenses + income in USD and KHR.
- Messy rows: broken on purpose (the `problem` column says how) to test validation. Includes duplicates.
- Every row has `source = synthetic`. **Never use it for findings.**

## Data & privacy (SCG-68)
- **Real diary data never goes on GitHub.** Keep it in `data/real/` on your own computer only.
- `.gitignore` blocks: `data/real/`, `data/synthetic/`, `*.db`, `.env`, `.streamlit/secrets.toml`.
- **Secrets** (for example the database password) are never written in the code.
  Read them with `config.get_secret("DB_PASSWORD")`. It looks in:
  1. an environment variable, then
  2. `.streamlit/secrets.toml` (local) or the **Secrets** box on Streamlit Cloud.
- No names, phone numbers or account numbers in any file, test or screenshot.
- Before you push, run `git status` and check that no data or secret file is listed.

## Exchange rates (SCG-28)
- **Source:** National Bank of Cambodia (NBC) official exchange rate,
  https://www.nbc.gov.kh/english/economic_research/exchange_rate.php
- File: `data/exchange_rates.csv` with `date, khr_per_usd, source`. Public data, OK on GitHub.
- NBC only publishes on working days. Missing days (weekends, holidays) use the
  **last earlier rate** and are flagged `is_filled = 1` in the `exchange_rates` table.
- `rates.rate_for(day)`: exact day, else most recent earlier day (`filled=True`), else `None`
  if the day is before the first date in the file.
- The app shows the rate it used, e.g. "4,067 KHR = $1".
- **To add new days:** open the NBC page, pick the date, and add one line per day to the CSV.
  The table reloads when the app starts.

## Diagrams (SCG-21)
- [System architecture](docs/architecture.md)
- [Database ERD](docs/erd.md)

GitHub draws these Mermaid diagrams automatically.

## Notes
- The database is a local SQLite file, `data/smartcash.db`. It moves to PostgreSQL in SCG-35.
- **On Streamlit Cloud the SQLite file is reset when the app restarts**, so accounts and
  transactions there are lost. This is fixed when we move to PostgreSQL (SCG-35).
- "Demo data" in the sidebar adds fake expenses to **your own** account only.
- Deploy: push to GitHub, then create an app on share.streamlit.io pointing to `app.py`.
