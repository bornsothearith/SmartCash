# SmartCash database (current tables)

The tables that exist **today** in the hosted PostgreSQL database (SCG-35).
They are created by `migrations/001_core_tables.sql` and `migrations/002_diary_import.sql`.
Local development uses the same tables in SQLite (`data/smartcash.db`).
We grow this diagram when a new migration adds a table.

```mermaid
erDiagram
    users ||--o{ transactions : "owns"
    users ||--o{ diary_raw : "uploaded"
    users ||--o{ diary_import_keys : "owns"
    transactions }o..|| exchange_rates : "tx_date = rate_date"

    users {
        BIGINT id PK
        TEXT username "unique, ignoring upper/lower case"
        TEXT password_hash "scrypt + salt, never the password"
        INTEGER failed_logins "wrong tries in a row"
        TIMESTAMP locked_until "locked 5 min after 5 wrong tries"
        TIMESTAMPTZ created_at
    }
    transactions {
        BIGINT id PK
        BIGINT user_id FK "owner, deleted with the user"
        DATE tx_date "not in the future"
        TEXT tx_type "expense or income"
        NUMERIC amount "14,2 - more than 0, whole number for KHR"
        TEXT currency "USD or KHR"
        TEXT category
        TEXT payment_method
        TEXT note "optional, max 200"
        SMALLINT is_demo "1 = fake demo row"
        TIMESTAMPTZ created_at
    }
    exchange_rates {
        DATE rate_date PK "every day, no gaps"
        NUMERIC khr_per_usd "10,2 - KHR for 1 USD"
        TEXT source "NBC official exchange rate"
        SMALLINT is_filled "1 = copied from an earlier day"
    }
    diary_raw {
        TEXT id PK "uuid"
        TEXT batch_id "one upload"
        BIGINT user_id FK
        INTEGER row_number
        TEXT payload "original CSV row as JSON"
        TEXT status "imported, duplicate or rejected"
        TEXT reason "why it was rejected"
    }
    diary_import_keys {
        TEXT fingerprint PK "sha256 of user + transaction fields"
        BIGINT user_id FK
    }
```

**Notes**
- Every table with user data has `user_id`; deleting a user deletes their rows (`ON DELETE CASCADE`).
- The rate link is by date only. It is not a foreign key.
- `schema_migrations` (not drawn) lists which migration files already ran.
- No table has real names, emails, phone numbers or account numbers (SCG-68).
