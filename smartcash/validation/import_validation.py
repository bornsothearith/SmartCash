"""Validation helpers for diary CSV imports."""

REQUIRED_COLUMNS = {
    "tx_date",
    "tx_type",
    "amount",
    "currency",
    "category",
    "payment_method",
}


def missing_columns(columns):
    """Return required CSV columns that are absent, in stable order."""
    return sorted(REQUIRED_COLUMNS.difference(columns))
