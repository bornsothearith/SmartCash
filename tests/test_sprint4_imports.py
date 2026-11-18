"""SCG-37/38/39 acceptance tests using isolated databases, never live data."""
import csv
import io
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import pytest

from smartcash import db, diary_import
from smartcash.validation.diary_schema import validate_row

VALID = dict(tx_date='2026-01-01', tx_type='expense', amount='3.00', currency='USD',
             category='Transport', payment_method='Cash', note='Synthetic test')


@pytest.mark.parametrize('field,value', [
    ('tx_date', 'not a date'), ('tx_date', '2026-02-30'),
    ('tx_date', (date.today() + timedelta(days=1)).isoformat()),
    ('amount', '0'), ('amount', '-1'), ('amount', 'NaN'), ('amount', 'inf'),
    ('currency', 'EUR'), ('category', 'Unknown'), ('tx_type', 'refund'),
    ('payment_method', 'Unknown'), ('category', 'Allowance'),
])
def test_each_validation_rule(field, value):
    assert validate_row({**VALID, field: value})


@pytest.mark.parametrize('field', ['tx_date', 'tx_type', 'amount', 'currency', 'category', 'payment_method'])
def test_required_fields(field):
    missing = VALID.copy()
    del missing[field]
    assert validate_row(missing)
    assert validate_row({**VALID, field: ''})


def csv_file(rows):
    result = io.StringIO()
    writer = csv.DictWriter(result, fieldnames=list(VALID))
    writer.writeheader()
    writer.writerows(rows)
    result.seek(0)
    return result


def setup_db(path):
    conn = db.connect(path)
    conn.execute("INSERT INTO users (username,password_hash) VALUES ('one','unused'), ('two','unused')")
    conn.commit()
    return conn


def test_rejection_survives_reconnect_and_csv_is_owner_scoped(tmp_path):
    path = tmp_path / 'reject.db'
    conn = setup_db(path)
    result = diary_import.import_csv(conn, 1, csv_file([VALID, {**VALID, 'amount': '-2'}]))
    assert result['read'] == 2 and result['imported'] == 1 and len(result['rejected']) == 1
    assert conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0] == 1
    conn.close()
    conn = db.connect(path)
    records = list(csv.DictReader(io.StringIO(diary_import.rejection_csv(conn, 1).decode('utf-8-sig'))))
    assert len(records) == 1 and records[0]['reason'] and '-2' in records[0]['payload']
    assert diary_import.rejection_log(conn, 2) == []
    conn.close()


def test_fingerprint_repeat_normalization_and_user_isolation(tmp_path):
    conn = setup_db(tmp_path / 'repeat.db')
    assert diary_import.import_csv(conn, 1, csv_file([VALID]))['imported'] == 1
    assert diary_import.import_csv(conn, 1, csv_file([{**VALID, 'amount': '3', 'currency': 'usd'}]))['duplicates'] == 1
    assert diary_import.import_csv(conn, 2, csv_file([VALID]))['imported'] == 1
    assert conn.execute('SELECT COUNT(*) FROM diary_import_keys').fetchone()[0] == 2
    conn.close()


def test_concurrent_imports_add_one_record(tmp_path):
    path = tmp_path / 'concurrent.db'
    conn = setup_db(path)
    conn.close()

    def load():
        conn = db.connect(path)
        try:
            return diary_import.import_csv(conn, 1, csv_file([VALID]))['imported']
        finally:
            conn.close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(lambda _: load(), range(2))) == 1


def test_failed_clean_write_does_not_claim_key(tmp_path, monkeypatch):
    conn = setup_db(tmp_path / 'rollback.db')
    def fail(*args, **kwargs):
        raise RuntimeError('simulated database failure')
    with monkeypatch.context() as patch:
        patch.setattr(diary_import, 'add_transaction', fail)
        with pytest.raises(RuntimeError):
            diary_import.import_csv(conn, 1, csv_file([VALID]))
    assert conn.execute('SELECT COUNT(*) FROM diary_import_keys').fetchone()[0] == 0
    assert diary_import.import_csv(conn, 1, csv_file([VALID]))['imported'] == 1
    conn.close()


def test_rejected_clean_write_releases_key(tmp_path, monkeypatch):
    conn = setup_db(tmp_path / 'rejected.db')
    def fail(*args, **kwargs):
        raise ValueError('Exchange rate unavailable')
    with monkeypatch.context() as patch:
        patch.setattr(diary_import, 'add_transaction', fail)
        result = diary_import.import_csv(conn, 1, csv_file([VALID]))
    assert len(result['rejected']) == 1
    assert conn.execute('SELECT COUNT(*) FROM diary_import_keys').fetchone()[0] == 0
    assert diary_import.import_csv(conn, 1, csv_file([VALID]))['imported'] == 1
    conn.close()
