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

## Design
- The app uses the SmartCash design system in `design-system/` (dark theme, one lavender accent).
  Start with `design-system/SKILL.md`, then `brand-book.md`. Use its tokens; don't invent colours, fonts or spacing.
- The theme lives in `.streamlit/config.toml`. Custom HTML (cards, money amounts, the transaction list) is built in `ui.py`,
  which loads `design-system/tokens.css` and `components/components.css`.
- The Transactions tab shows **Income, Spending and Net** in separate cards (all in USD) instead of one mixed total.
  Money is shown as `$1,284.50` / `៛40,000`, with + for income and − for spending.

## Notes
- Data is saved in a local file, `smartcash.db` (kept out of GitHub by `.gitignore`).
  It moves to PostgreSQL in SCG-35.
- Riel is converted at a fixed 4,100 KHR = $1 until the daily rate table (SCG-28) exists.
- "Demo data" in the sidebar adds fake expenses for testing. Never put real diary data in this app or on GitHub.
- Deploy: push to GitHub, then create an app on share.streamlit.io pointing to `app.py`.
