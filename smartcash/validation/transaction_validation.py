"""Validation rules for SmartCash transaction entries."""

from datetime import date

CURRENCIES = ["USD", "KHR"]
EXPENSE_CATEGORIES = [
    "Food & drinks", "Groceries", "Transport", "Phone & internet",
    "Education", "Rent & utilities", "Shopping & personal care",
    "Entertainment & social", "Health", "Family, gifts & ceremonies", "Other",
]
PAYMENT_METHODS = ["Cash", "Mobile banking / QR", "Card", "Other"]


def validate_expense(expense, today=None):
    """Return validation messages. An empty list means the entry is valid."""
    today = today or date.today()
    errors = []
    if expense.amount is None or expense.amount <= 0:
        errors.append("Amount must be more than 0.")
    if expense.currency not in CURRENCIES:
        errors.append("Currency must be USD or KHR.")
    elif expense.currency == "KHR" and expense.amount and expense.amount != int(expense.amount):
        errors.append("Riel amounts must be whole numbers.")
    if expense.category not in EXPENSE_CATEGORIES:
        errors.append("Pick a category from the list.")
    if expense.payment_method not in PAYMENT_METHODS:
        errors.append("Pick a payment method from the list.")
    if expense.tx_date > today:
        errors.append("Date can't be in the future.")
    if len(expense.note) > 200:
        errors.append("Note must be 200 characters or fewer.")
    return errors
