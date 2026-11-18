"""Validation rules for SmartCash transaction entries."""

from datetime import date
import math

CURRENCIES = ["USD", "KHR"]
EXPENSE_CATEGORIES = [
    "Food & drinks", "Groceries", "Transport", "Phone & internet",
    "Education", "Rent & utilities", "Shopping & personal care",
    "Entertainment & social", "Health", "Family, gifts & ceremonies", "Other",
]
PAYMENT_METHODS = ["Cash", "Mobile banking / QR", "Card", "Other"]
INCOME_CATEGORIES = ["Allowance", "Part-time job", "Scholarship", "Gift", "Other"]


def validate_transaction(transaction, today=None):
    """Return validation messages. An empty list means the entry is valid."""
    today = today or date.today()
    errors = []
    finite_amount = isinstance(transaction.amount, (int, float)) and math.isfinite(transaction.amount)
    if not finite_amount or transaction.amount <= 0:
        errors.append("Amount must be more than 0.")
    if getattr(transaction, 'tx_type', 'expense') not in {'expense', 'income'}:
        errors.append('Type must be expense or income.')
    if transaction.currency not in CURRENCIES:
        errors.append("Currency must be USD or KHR.")
    elif transaction.currency == "KHR" and finite_amount and transaction.amount != int(transaction.amount):
        errors.append("Riel amounts must be whole numbers.")
    allowed_categories = (INCOME_CATEGORIES if getattr(transaction, "tx_type", "expense") == "income"
                          else EXPENSE_CATEGORIES)
    if transaction.category not in allowed_categories:
        errors.append("Pick a category from the list.")
    if transaction.payment_method not in PAYMENT_METHODS:
        errors.append("Pick a payment method from the list.")
    if not isinstance(transaction.tx_date, date):
        errors.append('Date must be valid.')
    elif transaction.tx_date > today:
        errors.append("Date can't be in the future.")
    if not isinstance(transaction.note, str) or len(transaction.note) > 200:
        errors.append("Note must be 200 characters or fewer.")
    return errors


def validate_expense(expense, today=None):
    """Backward-compatible expense validation."""
    return validate_transaction(expense, today)
