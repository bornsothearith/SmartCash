# SmartCash spending diary form

This is the form specification for SCG-25. It is separate from the consent
form: consent gives permission; the diary collects transaction records.

## Required questions

1. Participant ID, for example `P001`
2. Transaction date
3. Transaction type: `expense` or `income`
4. Amount
5. Currency: `USD` or `KHR`
6. Category
7. Payment method: `Cash`, `Mobile banking / QR`, `Card`, or `Other`

## Optional question

8. Note, maximum 200 characters

## CSV export columns

```text
participant_id,tx_date,tx_type,amount,currency,category,payment_method,note
```

The exported file can be uploaded to the **Import diary** tab in the app.
Before sharing the form, collect consent first and do not ask for names,
account numbers, passwords, or card details.
