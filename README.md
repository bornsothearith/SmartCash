# SmartCash

Covers these stories:
- **SCG-31 Add expense**: date, amount, USD or KHR, category, payment method, note. Every field is checked before saving.
- **SCG-30 Add income**: amount, USD or KHR, date, income type (Allowance, Part-time job, Scholarship, Gift, Other),
  optional "received as" and note. Uses the same checks as expenses (amount > 0, whole riel, no future dates).
- **SCG-33 View and filter transactions**: filter by dates, categories and type (Income / Expense).
  Shows **Income, Spending and Net** in USD separately, plus the number of transactions.

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

## Notes
- Data is saved in a local file, `smartcash.db` (kept out of GitHub by `.gitignore`).
  It moves to PostgreSQL in SCG-35.
- Riel is converted at a fixed 4,100 KHR = $1 until the daily rate table (SCG-28) exists.
- "Demo data" in the sidebar adds 30 fake expenses and 4 fake income rows for testing. Never put real diary data in this app or on GitHub.
- Deploy: push to GitHub, then create an app on share.streamlit.io pointing to `app.py`.
