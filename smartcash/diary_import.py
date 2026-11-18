"""Import spending-diary CSV files into a user's transaction history."""

import csv
import io
import json
import math
import uuid
import hashlib
from decimal import Decimal
from datetime import datetime

from smartcash.transactions import Transaction, add_transaction
from smartcash.validation import missing_columns, validate_transaction
from smartcash.validation.diary_schema import validate_row


CSV_COLUMNS = (
    "tx_date", "tx_type", "amount", "currency", "category",
    "payment_method", "note",
)

ALIASES = {
    'date': 'tx_date', 'transaction date': 'tx_date',
    'type': 'tx_type', 'transaction type': 'tx_type',
    'amount': 'amount', 'currency': 'currency', 'category': 'category',
    'payment method': 'payment_method', 'paid with': 'payment_method',
    'note': 'note', 'notes': 'note', 'note (optional)': 'note',
}


def read_csv(file_obj):
    content = file_obj.read()
    if isinstance(content, bytes):
        content = content.decode('utf-8-sig')
    return csv.DictReader(io.StringIO(content.lstrip('\ufeff')), strict=True)


def suggested_mapping(headers):
    return {h: ALIASES.get(h.strip().lower(), h.strip().lower()) for h in headers}


def _as_bool(value):
    return str(value or "0").strip().lower() in {"1", "true", "yes"}


def _duplicate(conn, user_id, transaction):
    row = conn.execute(
        "SELECT 1 FROM transactions WHERE user_id = ? AND tx_date = ? AND tx_type = ?"
        " AND amount = ? AND currency = ? AND category = ? AND payment_method = ?"
        " AND note = ? LIMIT 1",
        (user_id, transaction.tx_date.isoformat(), transaction.tx_type,
         float(transaction.amount), transaction.currency, transaction.category,
         transaction.payment_method, transaction.note.strip()),
    ).fetchone()
    return row is not None


def fingerprint(user_id, transaction):
    """Canonical key includes owner and required fields plus type/payment.

    Including type/payment prevents legitimate income/expense or different
    payment-method records from being silently merged.
    """
    values = [str(user_id), transaction.tx_date.isoformat(),
              format(Decimal(str(transaction.amount)).normalize(), 'f'),
              transaction.currency, transaction.category, transaction.note.strip(),
              transaction.tx_type, transaction.payment_method]
    return hashlib.sha256(json.dumps(values, ensure_ascii=False).encode('utf-8')).hexdigest()


def rejection_log(conn, user_id):
    """Only the signed-in owner's rejected records, including original values."""
    return [dict(row) for row in conn.execute(
        'SELECT row_number AS row, batch_id, reason, payload FROM diary_raw '
        "WHERE user_id = ? AND status = 'rejected' ORDER BY batch_id, row_number", (user_id,))]


def rejection_csv(conn, user_id):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=['row', 'batch_id', 'reason', 'payload'])
    writer.writeheader()
    for record in rejection_log(conn, user_id):
        # Prevent spreadsheet formulas in untrusted rejection messages.
        writer.writerow({key: "'" + value if isinstance(value, str) and
                         value.lstrip().startswith(('=', '+', '-', '@')) else value
                         for key, value in record.items()})
    return output.getvalue().encode('utf-8-sig')


def import_csv(conn, user_id, file_obj, mapping=None, date_format='%Y-%m-%d'):
    """Import a diary CSV and return imported, duplicate, and rejected counts."""
    if not user_id:
        raise ValueError('You must be logged in.')
    reader = read_csv(file_obj)
    headers = reader.fieldnames or []
    mapping = suggested_mapping(headers) if mapping is None else mapping
    targets = [mapping.get(h) for h in headers if mapping.get(h)]
    missing = missing_columns(targets)
    if len(headers) != len(set(headers)):
        raise ValueError('CSV headers must be unique.')
    if len(targets) != len(set(targets)):
        raise ValueError('Multiple columns map to the same field. Adjust the mapping.')
    if missing:
        return {"read": 0, "imported": 0, "duplicates": 0,
                "rejected": [{"row": 1, "reason": "Missing columns: " + ", ".join(missing)}]}

    result = {"read": 0, "imported": 0, "duplicates": 0, "rejected": []}
    batch = str(uuid.uuid4())
    for row_number, original in enumerate(reader, start=2):
        result['read'] += 1
        row = {mapping[h]: value for h, value in original.items() if mapping.get(h)}
        raw_id = str(uuid.uuid4())
        conn.execute('INSERT INTO diary_raw (id, batch_id, user_id, row_number, payload, status) '
                     'VALUES (?, ?, ?, ?, ?, ?)',
                     (raw_id, batch, user_id, row_number, json.dumps(original), 'pending'))
        status, reason = 'imported', ''
        conn.execute('SAVEPOINT diary_row')
        try:
            if None in original:
                raise ValueError('Too many cells in this CSV row.')
            row = {key: value.strip() if isinstance(value, str) else value for key, value in row.items()}
            row['tx_type'] = str(row.get('tx_type') or '').lower()
            row['currency'] = str(row.get('currency') or '').upper()
            schema_errors = validate_row(row, date_format)
            if schema_errors:
                raise ValueError('; '.join(schema_errors))
            if row.get('tx_type', '').strip().lower() not in {'expense', 'income'}:
                raise ValueError('Type must be expense or income.')
            if not math.isfinite(float(row['amount'])):
                raise ValueError('Amount must be a finite number.')
            transaction = Transaction(
                tx_date=datetime.strptime(str(row['tx_date']).strip(), date_format).date(),
                tx_type=str(row["tx_type"]).strip().lower(),
                amount=float(row["amount"]),
                currency=str(row["currency"]).strip().upper(),
                category=str(row["category"]).strip(),
                payment_method=str(row["payment_method"]).strip(),
                note=str(row.get("note") or "").strip(),
            )
            errors = validate_transaction(transaction)
            if errors:
                raise ValueError(" ".join(errors))
            claimed = conn.execute(
                'INSERT INTO diary_import_keys (fingerprint, user_id) VALUES (?, ?) '
                'ON CONFLICT (fingerprint) DO NOTHING RETURNING fingerprint',
                (fingerprint(user_id, transaction), user_id)).fetchone()
            if claimed is None or _duplicate(conn, user_id, transaction):
                result["duplicates"] += 1
                status = 'duplicate'
            else:
                add_transaction(conn, user_id, transaction,
                            is_demo=_as_bool(row.get("is_demo")) or row.get("source") == "synthetic",
                            commit=False)
                result["imported"] += 1
        except (KeyError, TypeError, ValueError) as exc:
            conn.execute('ROLLBACK TO SAVEPOINT diary_row')
            result["rejected"].append({"row": row_number, "reason": str(exc)})
            status, reason = 'rejected', str(exc)
        except Exception:
            conn.rollback()
            raise
        conn.execute('RELEASE SAVEPOINT diary_row')
        conn.execute('UPDATE diary_raw SET status = ?, reason = ? WHERE id = ? AND user_id = ?',
                     (status, reason, raw_id, user_id))
        conn.commit()
    return result
