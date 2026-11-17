# SmartCash (Sprint 1)

Covers two Sprint 1 stories:
- **SCG-31 Add expense**: date, amount, USD or KHR, category, payment method, note. Every field is checked before saving.
- **SCG-33 View and filter transactions**: filter by dates, categories and type; shows count and USD total.

## Run it
```
pip install -r requirements.txt
streamlit run app.py
```

## Test it
```
pip install pytest
python -m pytest tests
```

## Fake test data (SCG-29)
```
python synthetic.py          # writes data/synthetic/sample.csv
```
- Normal rows: expenses + income in USD and KHR.
- Messy rows: broken on purpose (the `problem` column says how) to test validation. Includes duplicates.
- Every row has `source = synthetic`. **Never use it for findings.**

## Notes
- Data is saved in a local file, `smartcash.db` (kept out of GitHub by `.gitignore`).
  It moves to PostgreSQL in SCG-35.
- Riel is converted at a fixed 4,100 KHR = $1 until the daily rate table (SCG-28) exists.
- "Demo data" in the sidebar adds fake expenses for testing. Never put real diary data in this app or on GitHub.
- Deploy: push to GitHub, then create an app on share.streamlit.io pointing to `app.py`.
