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

**Sprint 3**
- **SCG-30 Add income**: record allowance, part-time work, scholarship, gifts, or other income in USD or KHR.
- **SCG-32 Edit or delete transactions**: update or remove only the signed-in user's transactions, with delete confirmation.
- **SCG-34 Dual currency**: preserve the original amount and currency while showing USD equivalents using the transaction-date rate.
- **SCG-35 PostgreSQL-ready storage**: set `DATABASE_URL` to use PostgreSQL; local development continues to use SQLite when it is absent.
- **SCG-36 Diary CSV import**: import standard diary columns, skip duplicates, and report rejected rows.

## Run it
```
pip install -r requirements.txt
streamlit run app.py
```
Then click **Sign up** and make an account (use a nickname, not your real name).

## Sprint 4: clean imports and spending analytics

- **SCG-37:** Pandera checks required fields, dates, finite positive amounts,
  currencies, categories, transaction types and payment methods. Invalid rows
  remain in private raw storage, not the clean transaction table.
- **SCG-38:** Imports report read, accepted, duplicate and rejected counts.
  Rejection history includes original values and reasons and can be downloaded
  as CSV. The database retains it across app restarts; exports are private data.
- **SCG-39:** A database-enforced SHA-256 key prevents repeat imports, including
  concurrent uploads. Keys include user, date, normalized amount, currency,
  category and note, plus type and payment method to distinguish otherwise
  identical transactions. Each raw row and clean write commit together.
  Keys remain after editing/deleting an imported transaction, so re-uploading
  the original file does not silently restore it.
- **SCG-43:** Synthetic-data exploration is separate from real study findings.
- **SCG-50/51/52:** Overview contains period KPIs, weekly spending trends and
  category comparisons. All monetary analytics use USD equivalents.

Install the updated requirements before restarting the app. Startup adds the
`diary_import_keys` table without deleting existing transactions. Existing
transactions are also checked when their file is imported for the first time
after this upgrade. Identical legitimate purchases with all key fields equal
are indistinguishable: use distinct notes when recording these purchases.

Sprint 4 does not complete the separate SCG-35 hosted PostgreSQL/star-schema
deployment. A live PostgreSQL connection must still be checked in that environment.

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
  database/connection.py SQLite connection and tables
  database/schema.sql   PostgreSQL schema
  auth.py               sign up, log in, password hashing (SCG-75)
  transactions.py       add, check and filter transactions (SCG-31, SCG-33)
  rates.py              daily USD/KHR rates (SCG-28)
  synthetic.py          fake test data (SCG-29)
  ui/theme.py            colours, cards and table (UI design)
  validation/            transaction and CSV validation rules
  diary_import.py        CSV diary import and duplicate detection
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

## PostgreSQL (SCG-35)
- Set `DATABASE_URL` in an environment variable or `.streamlit/secrets.toml`.
- When `DATABASE_URL` exists, the app creates and uses PostgreSQL tables from `smartcash/database/schema.sql`.
- Without it, the app uses local `data/smartcash.db` for development and tests.

## Diary CSV import (SCG-36)
Upload a UTF-8 CSV in **Import diary**. Review the column mapping before importing.
Standard headers map directly: `tx_date, tx_type, amount, currency, category, payment_method`.
Optional fields: `note, is_demo, source`. Google Form headings `Date` or `Transaction date`,
`Transaction type`, `Amount`, `Currency`, `Category`, `Paid with` or `Payment method`,
and `Notes` are recognized automatically. Map other question headings manually.
Select ISO (`%Y-%m-%d`), day/month/year, or month/day/year explicitly; ambiguous dates
are never guessed. Use the app's category/payment choices and expense/income types.

Each parsed row is stored in private `diary_raw` with a batch ID, owner, original JSON,
row number, status, and rejection reason. Even ignored columns remain in raw storage:
exclude personal identifiers and bank details before uploading. Valid rows also enter
`transactions`; duplicates are recorded but not inserted twice. The UI reports rows read,
imported, duplicated, and rejected. Missing headers prevent import; malformed CSV can
stop a partially completed import. Re-uploading skips existing matching transactions.

Synthetic examples: `tests/fixtures/diary_standard.csv` and
`tests/fixtures/diary_google_form.csv`. No real participant records are included.
The minimal raw table is created on app startup on SQLite and PostgreSQL; the full
analytics schema and hosted deployment remain separate SCG-35 work.
- Open **Import diary** after logging in.
- Required columns: `tx_date, tx_type, amount, currency, category, payment_method`.
- Optional columns: `note, is_demo, source`.
- Duplicate rows for the same user are skipped. Invalid rows appear in the rejected-row report.

## Notes
- The database is a local SQLite file, `data/smartcash.db`. It moves to PostgreSQL in SCG-35.
- **On Streamlit Cloud the SQLite file is reset when the app restarts**, so accounts and
  transactions there are lost. This is fixed when we move to PostgreSQL (SCG-35).
- "Demo data" in the sidebar adds fake expenses to **your own** account only.
- Deploy: push to GitHub, then create an app on share.streamlit.io pointing to `app.py`.

## After every push to main (deploy checklist)
1. Run `python -m pytest tests` **before** pushing. All tests must pass.
2. Push. Streamlit Cloud updates the live app in about a minute.
3. If you changed any file inside `smartcash/`, open the live app → **Manage app → ⋮ → Reboot app**.
   (Streamlit can keep old copies of those files in memory. `smartcash/freshness.py` tries to
   reload them by itself, but rebooting is the sure way.)
4. Click through the live app: log in, Add demo data, Transactions → Edit → Save, Delete,
   Overview, Budgets, Forecast, Import diary.
5. If you see a red error, open **Manage app → Logs** for the full message.

Note: a reboot also empties the live SQLite database (all accounts). This stops when we move to
PostgreSQL (SCG-35).
