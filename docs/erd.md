# SmartCash database (current tables)

Only the tables that exist **today** in `data/smartcash.db` (SQLite).
We grow this diagram when new tables are added (SCG-35 PostgreSQL schema).

```mermaid
erDiagram
    users ||--o{ transactions : "owns"
    transactions }o..|| exchange_rates : "tx_date = rate_date"

    users {
        INTEGER id PK
        TEXT username "unique, not case sensitive"
        TEXT password_hash "scrypt + salt, never the password"
        INTEGER failed_logins "wrong tries in a row"
        TEXT locked_until "locked 5 min after 5 wrong tries"
        TEXT created_at
    }
    transactions {
        INTEGER id PK
        INTEGER user_id FK "owner"
        TEXT tx_date "YYYY-MM-DD, not in the future"
        TEXT tx_type "expense or income"
        REAL amount "more than 0; whole number for KHR"
        TEXT currency "USD or KHR"
        TEXT category
        TEXT payment_method
        TEXT note "optional, max 200"
        INTEGER is_demo "1 = fake demo row"
        TEXT created_at
    }
    exchange_rates {
        TEXT rate_date PK "every day, no gaps"
        REAL khr_per_usd "KHR for 1 USD"
        TEXT source "NBC official exchange rate"
        INTEGER is_filled "1 = copied from an earlier day"
    }
```

**Notes**
- `transactions.user_id` → `users.id`. Deleting a user deletes their transactions.
- The rate link is by date only. It is not a foreign key.
- No table has real names, emails, phone numbers or account numbers (SCG-68).
