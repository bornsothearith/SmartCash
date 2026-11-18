"""SCG-37: Pandera checks before a diary row enters clean transactions."""
from datetime import date
import math

import pandas as pd
import pandera.pandas as pa

from .transaction_validation import EXPENSE_CATEGORIES, INCOME_CATEGORIES, PAYMENT_METHODS


def validate_row(row, date_format='%Y-%m-%d'):
    """Return all failed rules. Values are normalized by the importer first."""
    schema = pa.DataFrameSchema({
        'tx_date': pa.Column(str, checks=pa.Check(
            lambda s: pd.to_datetime(s, format=date_format, errors='coerce').notna()
            & (pd.to_datetime(s, format=date_format, errors='coerce') <= pd.Timestamp(date.today())),
            error='Date must be valid and not in the future')),
        'tx_type': pa.Column(str, checks=pa.Check.isin(['income', 'expense'])),
        'amount': pa.Column(float, coerce=True, checks=[
            pa.Check.gt(0), pa.Check(lambda s: s.map(math.isfinite), error='Amount must be finite')]),
        'currency': pa.Column(str, checks=pa.Check.isin(['USD', 'KHR'])),
        'category': pa.Column(str, checks=pa.Check.isin(sorted(set(EXPENSE_CATEGORIES + INCOME_CATEGORIES)))),
        'payment_method': pa.Column(str, checks=pa.Check.isin(PAYMENT_METHODS)),
    }, checks=pa.Check(
        lambda df: df.apply(lambda r: r['category'] in (
            INCOME_CATEGORIES if r['tx_type'] == 'income' else EXPENSE_CATEGORIES), axis=1),
        error='Category must match transaction type'), strict=False)
    try:
        schema.validate(pd.DataFrame([row]), lazy=True)
    except pa.errors.SchemaErrors as exc:
        return list(dict.fromkeys(
            f"{failure.get('column') or 'row'}: {failure['check']}"
            for failure in exc.failure_cases.to_dict('records')))
    return []
