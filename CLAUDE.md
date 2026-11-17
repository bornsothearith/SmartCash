# SmartCash: project context for Claude Code

Read this whole file before doing any work. Then read `app.py`, `db.py` and `tests/`.

## The project
- **SmartCash** is a web app for tracking spending in **USD and KHR (riel)**, setting monthly budgets, and forecasting next week's spending. First users: university students in Phnom Penh. Freemium model (Free $0, Premium $1.99/month).
- It is a **student team project (Group 11, CADT, Cambodia)** that covers 4 courses: Project Management, Data Engineering (DE), Statistical Data Analysis (SDA), and Data Visualization.
- **Team:** BORN Chansothearith (Product Owner), IN Uddam Darren (Scrum Master), SOEM Vibolrathana (Data Engineer lead), LY Meas (Data Engineer / Tester), HENG Sovannreach (Data Analyst / ML), LEANG SivMing (Dashboard Developer).
- **Jira:** https://smartcash168.atlassian.net, project key **SCG**, board 36. Weekly sprints.
- **GitHub:** https://github.com/bornsothearith/SmartCash
- **Live app:** https://smartcash.streamlit.app (Streamlit Community Cloud, deploys from `main`).

## Current code (checked 17 Nov 2026)
- **`main`** (what the live app runs): Sprint 1 code. `app.py` has 2 tabs, **Add expense** (SCG-31) and **Transactions** (SCG-33); `db.py` is the SQLite layer; tests in `tests/test_sprint1.py`.
- **`SCG-30-add-income`** (pushed, not merged yet): adds the **Add income** tab (3 tabs now) and separate **Income / Spending / Net** totals. `db.py` adds `Income`, `INCOME_TYPES`, `validate_income`, `add_income`, `summarize`, `load_demo_income`. New tests in `tests/test_income.py`.
- `db.py`: SQLite (`smartcash.db`, gitignored). One `transactions` table: `id, tx_date, tx_type ('expense'|'income'), amount (>0), currency ('USD'|'KHR'), category, payment_method, note, is_demo, created_at`. Core functions: `connect`, `validate_expense`, `add_expense`, `to_usd`, `filter_transactions`, `load_demo_data`, `clear_demo_data`.
- KHR is converted at a **fixed placeholder of 4,100 KHR = $1** (`KHR_PER_USD`). SCG-28 and SCG-34 replace this.
- Tests: everything in `tests/` (`test_sprint1.py`, `test_income.py`, ...). Run `python -m pytest tests`; all must pass.
- `requirements.txt`: streamlit, pandas. `.gitignore` excludes `*.db`, `__pycache__/`, `.pytest_cache/`, `.env`, `data/real/`.
- Windows line endings: this repo is edited on Windows. Keep `core.autocrlf=true`; never commit a change that only flips line endings.

## Branches
- `main`: live app. Only merge through reviewed pull requests.
- `SCG-30-add-income`: SCG-30, ready for review. **Merge first** (demo 18–20 Nov).
- `SCG-70-team-docs`: adds this `CLAUDE.md` and `design-system/` so the whole team has them. Merge to `main` too.
- `design-transactions-tab`: **don't merge yet.** Its commit is labelled `SCG-XX` (no real Jira key, breaks rule 2) and it switches the app to the dark theme, which the team hasn't agreed. It needs a real story key and team approval first. A stash on it (`stash@{0}`) only holds an old brand-book logo edit, now already in `SCG-70-team-docs`.
- `Heng-Sovannreach`, `rathana` (remote only): teammates' branches, not reviewed. Ask the owner before building on them.

## Rules for every change
1. **One branch per story**, named after its Jira key, e.g. `SCG-30-add-income`. Never commit straight to `main`; the live app deploys from it.
2. **Commit messages start with the Jira key:** `SCG-30 add income form`.
3. Keep logic in `db.py` (or new modules) and keep `app.py` thin, so the logic stays testable without Streamlit.
4. **Every story gets tests** that check its acceptance criteria. Run `python -m pytest tests` before each commit; all tests must pass.
5. **Privacy:** no real diary data, names, phone numbers or secrets ever go into the repo. Secrets go in `.env` / `.streamlit/secrets.toml` (both gitignored). Synthetic data must be clearly labelled (`is_demo=1`).
6. Show me a short plan before editing, and explain what you changed after. I have to present this code at sprint reviews.
7. Update `README.md` when setup or usage changes.

## Design system
- For ANY UI work (Streamlit screens, `.streamlit/config.toml` theme, charts, custom HTML/CSS, sprint review pages or slides), first read `design-system/SKILL.md`, then `design-system/brand-book.md`. Follow its tokens; don't invent colours, fonts or spacing.
- `design-system/` lives on branch `SCG-70-team-docs` (also merged into `SCG-30-add-income`). If it's missing on your branch, merge `SCG-70-team-docs` or `main` once it's merged.
- Tokens: `design-system/tokens.json` (with usage notes) and `design-system/tokens.css`. Component guidelines: `design-system/components/`.
- **Logo: not chosen yet.** The team is picking one from Claude Design options (ideas: $ + ៛ riel sign, coin/wallet shape, "S"/"SC" monogram, balance/upward trend). Until it is added to `design-system/`, use the wordmark "SmartCash" in Inter 600 only. Don't draw, generate or add a logo, favicon or app icon yourself.
- Any new logo must be flat, 1–2 colours from the tokens, readable at 16px, and must not look like Linear, Wise, Revolut, Stripe or a bank. If you show the riel sign ៛, check the font renders it.
- The app's current theme (light, navy) is NOT yet on-system. Switching the live app to the dark theme is a team decision: propose it as its own story and branch; don't change it as a side effect of another story.

**Definition of Done (SCG-83):** code reviewed by a teammate and merged on GitHub · works with real or test data and tests pass · docs updated · shown at the sprint review and accepted by the PO.

## Sprint status (checked in Jira on 17 Nov 2026)
- **Sprint 1**: closed on 17 Nov. Done: SCG-18, SCG-19, SCG-31, SCG-33. SCG-24 consent form and SCG-29 synthetic data (both In Progress) moved to Sprint 4.
- **Sprint 2** (3–9 Nov): never started. All stories To Do.
- **Sprint 3**: closed on 17 Nov. Done: SCG-156. Not built, moved to Sprint 4: SCG-30, SCG-32, SCG-34, SCG-35, SCG-36.
- **Sprint 4** (17–23 Nov): current, but not yet started in Jira. Carried over: SCG-24, SCG-29 (from Sprint 1); SCG-30, SCG-32, SCG-34, SCG-35, SCG-36 (from Sprint 3).
- **SCG-30**: code built and pushed on `SCG-30-add-income`; waiting for review, merge and deploy. Not Done until it's live.
- **Milestone 3 sprint review: 18–20 Nov.** This is a live demo on the deployed app (no slides) that walks through **SCG-30 Add income** and its subtasks. SCG-30 must be working and deployed before then.

---

## Catch-up mode (we are behind: finish everything from Sprints 1–3)
Goal: really finish the 13 open stories from Sprints 1–3, fast. **Never mark a story Done in Jira unless it is built, tests pass and it is merged** (Definition of Done above). Working fast is fine; faking Done is not.

Do them in this order, one branch + PR per story, and stop after each one to give me a 3-line summary I can present:
1. **SCG-30 Add income**: code is built. Remaining: pull request → teammate review → merge to `main` → check it works on https://smartcash.streamlit.app → then mark Done.
2. **SCG-32 Edit or delete transactions**
3. **SCG-68 Keep real data private**
4. **SCG-29 Synthetic test data**
5. **SCG-28 USD/KHR exchange-rate table**
6. **SCG-34 Dual currency**
7. **SCG-21 Architecture and DB diagrams** (Mermaid in `docs/`)
8. **SCG-35 PostgreSQL schema** (SQLite fallback; I give you `DATABASE_URL`)
9. **SCG-36 Import diary and CSV files**
10. **SCG-24 Consent form** and **SCG-25 Diary form**: draft only, in `docs/drafts/`. The team writes the final wording.
11. People only, don't build: **SCG-20 Figma screens**, **SCG-26 Recruit volunteers**.

Details for each story are in the Work plan below. Speed rules: keep each PR small; reuse the existing validation and test patterns; don't refactor unrelated code; don't start Phase 2+ stories until this list is done.

# Work plan, in order

Do the phases in order. Within a phase, do the stories top to bottom.

## Phase 0: before the 18–20 Nov demo (top priority)

### SCG-30 Add income (3 pts)
- Form fields: amount, currency (USD/KHR), date, income type: **Allowance, Part-time job, Scholarship, Gift, Other**.
- Amount > 0; date can't be in the future; clear error message for every invalid field (reuse the expense rules, e.g. whole riel only).
- Saved income appears in the transaction list as **Income**.
- Income counts in the totals and in the Income filter. The Transactions tab should show **Income, Spending and Net** separately instead of one mixed total.
- Tests: a valid save, and an invalid amount.
- Subtasks: SCG-116 UI form · SCG-117 income types and checks · SCG-118 save to DB · SCG-119 tests · SCG-120 demo on the live app.
- Hint: add an `Income` dataclass, `INCOME_TYPES`, `validate_income`, `add_income`. Store the income type in `category` and use a suitable `payment_method` (or allow it to be optional for income).

### SCG-32 Edit or delete transactions (3 pts)
- Every row in the list has **Edit** and **Delete**.
- The edit form is pre-filled and uses the same checks as Add.
- Delete asks for confirmation first.
- The list and totals update right after an edit or delete.
- Tests for edit and delete.
- Subtasks: SCG-121 edit form · SCG-122 delete with confirm · SCG-123 `update_transaction` / `delete_transaction` in db.py · SCG-124 tests.

## Phase 1: data foundation

### SCG-68 Keep real data private (3 pts)
- `.gitignore` excludes data files, `.env`, `*.db` (mostly done; check it).
- The DB password lives in `.env` / Streamlit secrets; nothing secret in the code.
- Real diary data only in a private team folder (`data/real/`, gitignored).
- No names, phone numbers or account numbers in any table.
- Scan the repo history for committed data or secrets.

### SCG-29 Synthetic test data (3 pts)
- A generator script (e.g. `scripts/make_synthetic.py`) creates normal **and** messy rows: bad dates, negative amounts, wrong currency, unknown category, duplicates, KHR decimals. Use a fixed seed.
- Output is labelled synthetic and **never used for findings**.

### SCG-28 USD/KHR exchange-rate table (2 pts)
- Choose one rate source (e.g. the National Bank of Cambodia official rate) and document it in the README.
- Table `exchange_rates(date, usd_khr_rate, source, is_filled)` with a row for every day of the study.
- Missing days are filled with the previous day's rate and flagged (`is_filled=1`).
- Load the table into the DB; a test checks there are no gaps.
- If live download isn't possible, use a committed CSV (`data/rates/usd_khr.csv`) that a teammate fills in.

### SCG-34 Dual currency (5 pts)
- Store the original amount and currency for every transaction (already done) and add a computed USD amount.
- USD is computed with **that day's rate** from SCG-28, replacing the fixed 4,100.
- All totals shown in USD; KHR shown with thousand separators.
- Tests cover conversion, including a day with a filled-in rate.

### SCG-21 Architecture and database diagrams (3 pts)
- System diagram: Google Form → pipeline → PostgreSQL → Streamlit app.
- ERD of the star schema: `fact_transaction` + `dim_date`, `dim_category`, `dim_user`, `dim_rate`, with keys.
- Save both as PNG in `/docs` and link them from the README. (Draft them in Mermaid in `docs/` first; a teammate can redraw them in draw.io.)

### SCG-35 PostgreSQL schema (5 pts)
- A free hosted PostgreSQL database (Neon or Supabase). **I create the account myself and give you only the connection string through `.env`.**
- A SQL script (`sql/create_tables.sql`) creates **raw**, **clean** and **analytics** tables; the star schema matches the ERD (SCG-21).
- The app reads and writes PostgreSQL instead of SQLite, so data survives a restart.
- The connection string is read from `DATABASE_URL` in secrets. **Keep SQLite as the fallback when `DATABASE_URL` isn't set**, so tests and local runs still work.
- Subtasks: SCG-111 create DB · SCG-112 SQL script · SCG-113 connect app · SCG-114 test that data survives a restart · SCG-115 README setup steps.

## Phase 2: data pipeline (DE course)

### SCG-36 Import diary and CSV files (5 pts)
- A Google Form export and a standard CSV both load into the **raw** table.
- Column mapping documented in the README; the import shows how many rows were read; sample file in `tests/`.
- Expected diary fields: date, type (income/expense), amount, currency (USD/KHR), category, payment method, optional note.

### SCG-37 Validation rules (5 pts)
- **pandera** rules: valid date, amount > 0, currency USD or KHR, category in the list, required fields present.
- Rows that fail are not loaded into the clean table. One test per rule.

### SCG-38 Rejected rows log (3 pts)
- Each import reports rows read, accepted and rejected; every rejected row lists its reason.
- The log is saved as CSV and shown in the app.

### SCG-39 Duplicate-safe imports (5 pts)
- Each record gets a unique key: a hash of user, date, amount, currency, category, note.
- Importing the same file twice adds 0 new rows; a test proves it.

### SCG-40 Totals reconciliation check (2 pts)
- A check script reports that loaded totals match the source file **to the cent** for every import.

### SCG-41 One-command pipeline run (3 pts)
- One command (e.g. `python -m pipeline run`) does extract → validate → load → refresh views, and can be scheduled.

### SCG-42 Weekly and monthly summary views (3 pts)
- SQL views of weekly and monthly totals per user and category.

## Phase 3: dashboard (Data Viz course)

### SCG-50 KPI cards (3 pts)
- Income, spending, net cash flow and savings rate for the chosen period.
- Each card shows the change vs the previous period, with an arrow and words.
- Values match a direct SQL query.

### SCG-51 Spending trend chart (3 pts)
- Weekly spending line with a 4-week moving average; y-axis starts at $0, labelled in USD; hover shows the exact weekly total.

### SCG-52 Spending by category chart (3 pts)
- Bars sorted biggest first; **one fixed colour per category, the same on every page**; top 7 categories + Other.

### SCG-53 Date and category filters (3 pts)
- All dashboard charts update together when the filters change.

### SCG-55 Dashboard accuracy checks (2 pts)
- At least 5 dashboard numbers are checked against direct database queries (as tests).

### SCG-54 Study insights page (3 pts)
- Payday curve, weekday vs weekend, and category share charts, using **aggregated data only**.

## Phase 4: budgets and Free/Premium

### SCG-56 Set monthly category budgets (5 pts)
- Users set spending limits per category, saved per month. **Free users: max 3 budgets.**

### SCG-57 Budget vs actual (3 pts)
- A progress bar per category, with the amount left shown; it turns red when over budget.

### SCG-64 Plan switch for demo (3 pts)
- A Free/Premium toggle; Premium features show a lock in Free mode. **No real payments.**

### SCG-66 Premium: overspending alerts (3 pts)
- An alert appears when spending crosses 80% and 100% of a budget, with the reason.

## Phase 5: analysis and forecasting (SDA course)
Use synthetic data (clearly labelled) until the real diary data arrives. Put the work in `notebooks/` plus reusable code in `analysis/`.

- **SCG-43 Descriptive stats (3):** mean, median and IQR per category and per user; category share table and charts.
- **SCG-44 Outlier analysis (2):** IQR / z-score rule; each outlier kept or removed, with a reason.
- **SCG-45 H2 weekday vs weekend (3):** check assumptions; correct test, p-value and effect size.
- **SCG-46 H3 food share by living situation (3):** group test, p-value, effect size, plain-language explanation.
- **SCG-47 H1 spending after payday (5):** needs the full diary data (after week 6); test, effect size, interpretation.
- **SCG-48 H4 cash vs digital (3):** test and effect size, or a written reason why the data was too small.
- **SCG-58 Forecast features (5):** e.g. last weeks' spending, days since income. **Past information only (no leakage)**; documented.
- **SCG-59 Baseline forecasts (3):** last week, 3-week average, personal average.
- **SCG-60 ML forecast models (5):** Ridge and Random Forest trained on pooled participant-weeks.
- **SCG-61 Fair model evaluation (5):** rolling-origin (time-based) testing with MAE and RMSE; best model picked by a written rule; report it honestly even if a baseline wins.
- **SCG-62 Forecast page (5):** chart of history + next week's forecast, its accuracy, and a short note that it's an estimate.
- **SCG-65 Premium forecast range (3):** a likely range based on model errors; hidden in Free mode.
- **SCG-49 Final analysis notebook (3):** runs top to bottom from the database; every result has a written explanation.

## Phase 6: quality and docs

- **SCG-69 Automated tests (5):** the pytest suite runs on every pull request with GitHub Actions (`.github/workflows/tests.yml`); core logic covered.
- **SCG-70 Setup and architecture docs (3):** a README a new teammate can follow from zero.

## Not code (done by people, not by Claude)
- SCG-24 consent form · SCG-25 Google Form diary · SCG-26 recruit volunteers · SCG-27 weekly diary reminders · SCG-13 validate the problem · SCG-17 MVP requirements · SCG-63 Free vs Premium feature table · SCG-67 willingness-to-pay check · SCG-71 usability test · SCG-72 fix issues from testing · SCG-73 final report and presentation · SCG-20 Figma screens.
- Scrum Master (Darren): SCG-22 run Scrum events (notes for every planning, review and retro; at least 2 stand-ups a week) · SCG-23 risk register reviewed at each retro, burndown screenshot saved each sprint.

## Out of scope (after MVP, don't build now)
SCG-74 in-app payments · SCG-75 user accounts · SCG-76 savings goals · SCG-77 monthly reports · SCG-78 forecast by category · SCG-79 recurring transactions · SCG-80 campus plan dashboard · SCG-81 model monitoring.
