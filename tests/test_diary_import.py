import io
import json
from pathlib import Path

import pytest
from smartcash import db, diary_import


@pytest.mark.parametrize('filename', ['diary_standard.csv', 'diary_google_form.csv'])
def test_binary_upload_raw_storage_and_repeat_import(tmp_path, filename):
    conn = db.connect(tmp_path / 'import.db')
    conn.execute("INSERT INTO users (username,password_hash) VALUES ('test','unused')")
    conn.commit()
    content = (Path(__file__).parent / 'fixtures' / filename).read_bytes()
    result = diary_import.import_csv(conn, 1, io.BytesIO(content))
    assert result == {'read': 1, 'imported': 1, 'duplicates': 0, 'rejected': []}
    raw = conn.execute('SELECT * FROM diary_raw WHERE user_id = 1').fetchone()
    assert raw['status'] == 'imported'
    assert json.loads(raw['payload'])
    again = diary_import.import_csv(conn, 1, io.BytesIO(content))
    assert again['duplicates'] == 1
    assert conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0] == 1
    conn.close()


def test_custom_mapping_and_invalid_row_retained(tmp_path):
    conn = db.connect(tmp_path / 'import.db')
    conn.execute("INSERT INTO users (username,password_hash) VALUES ('test','unused')")
    conn.commit()
    content = 'When,Kind,Value,Currency,Category,Paid with\n01/02/2026,expense,NaN,USD,Transport,Cash\n'
    mapping = diary_import.suggested_mapping(content.splitlines()[0].split(','))
    mapping.update(When='tx_date', Kind='tx_type', Value='amount')
    result = diary_import.import_csv(conn, 1, io.StringIO(content), mapping, '%d/%m/%Y')
    assert result['read'] == 1 and len(result['rejected']) == 1
    assert conn.execute('SELECT status FROM diary_raw').fetchone()[0] == 'rejected'
    conn.close()
