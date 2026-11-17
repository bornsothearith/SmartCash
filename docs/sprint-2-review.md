# Sprint 2 review checklist

Sprint period: 3 November to 9 November

## Final status

The repository work for Sprint 2 is complete. The remaining external actions
are publishing the approved volunteer form, collecting consented responses, and
submitting the review materials through the course channel.

## Completed in the repository

- SCG-20: white and light-gray UI design, navigation, user flow, dashboard, and budget page
- SCG-21: system-flow diagram and database ER diagram in `docs/architecture.md`
- SCG-25: income and expense transaction entry plus spending diary CSV import
- SCG-28: daily USD/KHR exchange-rate table and date-based conversion
- SCG-68: privacy rules, consent wording, data-minimisation rules, and synthetic-data separation
- SCG-26: volunteer invitation, Google Form structure, CSV hand-off, and launch checklist
- SCG-155: customer report and this review checklist

## Evidence to collect before final submission

- Link or screenshot of the published Google Form
- Screenshot or export showing at least one consented test response
- Volunteer recruitment/launch evidence
- Screenshot of the app importing a diary CSV
- Screenshot showing duplicate and rejected-row handling
- Screenshot of the dashboard chart and budget progress

## Demo sequence

1. Explain the privacy rule and participant ID.
2. Add one USD expense and one KHR expense.
3. Add one income transaction.
4. Import `data/synthetic/demo_transactions.csv`.
5. Import the same file again and show duplicates are skipped.
6. Show the transaction totals and dashboard chart.

## Sprint completion decision

Mark the sprint **Done** after the team attaches the external evidence listed
above and submits the review report. The code and documentation needed for
those actions are already in this repository.
