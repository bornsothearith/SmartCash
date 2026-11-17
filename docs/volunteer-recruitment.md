# SmartCash volunteer recruitment and diary launch pack

This document completes the project materials for SCG-26. It is ready to copy
into a class group, email, or Google Form description. The team still needs to
publish the form and send the invitation.

## Invitation message

**Help test SmartCash spending diary**

We are inviting students to help test SmartCash, a course project that studies
student spending patterns and presents anonymous summaries in USD and KHR.

Participation involves recording ordinary spending or income entries for about
five weeks. Each entry takes about one minute. Do not enter your name, bank
account number, card number, password, receipt, or another person's private
information.

Participation is voluntary. You may stop at any time. The project team will use
participant IDs and publish only anonymous summaries. Individual transactions
will not be shown publicly.

## Google Form structure

Create the form with these sections:

1. **Consent**
   - Checkbox, required: `I have read the information above and agree to participate.`
   - Checkbox, required: `I agree that anonymous aggregated results may be used for the course project.`
   - Multiple choice, required: `I understand that I can stop participating at any time.`
     - `Yes, I understand`
     - `No`
   - Do not collect email addresses unless the course supervisor explicitly requires it.

2. **Participant setup**
   - Short answer, required: `Participant ID`
   - Help text: `Use the ID assigned by the project team, such as P001. Do not enter your name.`

3. **Diary entry**
   - Date, required: `Transaction date`
   - Multiple choice, required: `Transaction type` with `Expense` and `Income`
   - Short answer, required: `Amount`
   - Multiple choice, required: `Currency` with `USD` and `KHR`
   - Dropdown, required: `Category` with `Food & drinks`, `Transport`, `Study`, `Bills`, `Shopping`, `Health`, `Entertainment`, `Other`
   - Dropdown, required: `Paid with` with `Cash`, `Bank transfer`, `Card`, `Mobile wallet`, `Other`
   - Paragraph, optional: `Note`

4. **Finish**
   - Confirmation text: `Thank you. Your entry was recorded. Please do not submit passwords, account numbers, or other private information.`

## Launch checklist

- [ ] Supervisor approves the consent wording.
- [ ] The form does not collect email addresses automatically.
- [ ] The team assigns participant IDs without using names in the diary CSV.
- [ ] The team tests one USD expense, one KHR expense, and one income entry.
- [ ] Responses are exported to CSV using the SmartCash column names.
- [ ] The exported file is stored locally in `data/raw/` and is not committed to Git.
- [ ] The team imports the CSV into SmartCash and checks rejected rows and duplicates.
- [ ] The team shares only anonymous aggregate charts in the review.

## CSV hand-off columns

The export should be mapped to:

`tx_date,tx_type,amount,currency,category,payment_method,note,is_demo`

For real volunteer records, set `is_demo` to `0`. Keep the raw response file
outside GitHub and do not place it in `data/synthetic/`.
