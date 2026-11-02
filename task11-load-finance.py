
from pathlib import Path

import pandas as pd
import psycopg

WORKBOOK = Path(
    "data/source/03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"
)


def connect():
    return psycopg.connect(
        host="localhost",
        port=5433,
        dbname="pulseiq_warehouse",
        user="pulseiq",
        password="pulseiq_dev_password",
    )


def load_table(conn, df, table, columns, definitions, key_columns):
    df = df[columns].copy()
    df = df.astype(object).where(pd.notna(df), None)

    create_columns = ", ".join(
        f'"{col}" {definitions[col]}'
        for col in columns
    )
    primary_key = ", ".join(
        f'"{col}"' for col in key_columns
    )

    with conn.cursor() as cur:
        cur.execute(
            f'CREATE TABLE IF NOT EXISTS warehouse."{table}" '
            f'({create_columns}, PRIMARY KEY ({primary_key}))'
        )

        placeholders = ", ".join(["%s"] * len(columns))
        col_sql = ", ".join(f'"{col}"' for col in columns)

        updates = ", ".join(
            f'"{col}" = EXCLUDED."{col}"'
            for col in columns
            if col not in key_columns
        )

        sql = (
            f'INSERT INTO warehouse."{table}" ({col_sql}) '
            f'VALUES ({placeholders}) '
            f'ON CONFLICT ({primary_key}) DO UPDATE SET {updates}'
        )

        records = list(df.itertuples(index=False, name=None))
        cur.executemany(sql, records)

    print(f"{table}: loaded {len(df)} rows")


def main():
    accounts = pd.read_excel(
        WORKBOOK, sheet_name="dim_account"
    )
    vendors = pd.read_excel(
        WORKBOOK, sheet_name="dim_vendor"
    )
    ledger = pd.read_excel(
        WORKBOOK, sheet_name="fact_ledger"
    )
    expenses = pd.read_excel(
        WORKBOOK, sheet_name="fact_expense"
    )

    # Validation: account codes must be unique.
    if accounts["account_code"].duplicated().any():
        raise ValueError("Duplicate account codes detected!")

    # Validation: ledger account codes must exist in dim_account.
    known_accounts = set(accounts["account_code"])
    unknown_accounts = (
        set(ledger["account_code"]) - known_accounts
    )
    if unknown_accounts:
        raise ValueError(
            f"Unknown ledger account codes: {unknown_accounts}"
        )

    # Validation: vendor IDs in expenses must exist.
    known_vendors = set(vendors["vendor_id"])
    unknown_vendors = (
        set(expenses["vendor_id"].dropna()) - known_vendors
    )
    if unknown_vendors:
        raise ValueError(
            f"Unknown vendor IDs in expenses: {unknown_vendors}"
        )

    # Convert date columns before loading.
    ledger["entry_date"] = pd.to_datetime(
        ledger["entry_date"]
    ).dt.date

    expenses["expense_date"] = pd.to_datetime(
        expenses["expense_date"]
    ).dt.date
    expenses["due_date"] = pd.to_datetime(
        expenses["due_date"], errors="coerce"
    ).dt.date
    expenses["paid_date"] = pd.to_datetime(
        expenses["paid_date"], errors="coerce"
    ).dt.date

    account_definitions = {
        "account_code": "INTEGER NOT NULL",
        "account_name": "TEXT NOT NULL",
        "account_type": "TEXT NOT NULL",
        "normal_balance": "TEXT",
        "parent_code": "INTEGER",
        "is_group": "TEXT NOT NULL",
        "statement": "TEXT",
        "is_active": "TEXT",
    }

    vendor_definitions = {
        "vendor_id": "TEXT NOT NULL",
        "vendor_name": "TEXT NOT NULL",
        "primary_expense_account": "INTEGER",
        "payment_terms_days": "INTEGER",
        "city": "TEXT",
        "gst_registration": "TEXT",
        "is_active": "TEXT",
    }

    ledger_definitions = {
        "line_id": "TEXT NOT NULL",
        "entry_id": "TEXT",
        "date_key": "INTEGER",
        "entry_date": "DATE",
        "posting_period": "TEXT",
        "financial_year": "TEXT",
        "account_code": "INTEGER NOT NULL",
        "debit": "NUMERIC(16,2)",
        "credit": "NUMERIC(16,2)",
        "signed_amount_debit_positive": "NUMERIC(16,2)",
        "cost_center_department_id": "TEXT",
        "source_type": "TEXT",
        "source_id": "TEXT",
    }

    expense_definitions = {
        "expense_id": "TEXT NOT NULL",
        "expense_date": "DATE",
        "expense_date_key": "INTEGER",
        "category_account": "INTEGER",
        "vendor_id": "TEXT",
        "bill_reference": "TEXT",
        "description": "TEXT",
        "department_id": "TEXT",
        "amount_excl_gst": "NUMERIC(16,2)",
        "gst_rate_percent": "NUMERIC(8,2)",
        "gst_amount": "NUMERIC(16,2)",
        "total_amount": "NUMERIC(16,2)",
        "due_date": "DATE",
        "paid_date": "DATE",
        "status": "TEXT",
        "payment_mode": "TEXT",
        "submitted_by": "TEXT",
        "approved_by": "TEXT",
        "ledger_entry_id": "TEXT",
        "payment_ledger_entry_id": "TEXT",
    }

    with connect() as conn:
        load_table(
            conn,
            accounts,
            "dim_account",
            list(account_definitions),
            account_definitions,
            ["account_code"],
        )

        load_table(
            conn,
            vendors,
            "dim_vendor",
            list(vendor_definitions),
            vendor_definitions,
            ["vendor_id"],
        )

        load_table(
            conn,
            ledger,
            "fact_ledger",
            list(ledger_definitions),
            ledger_definitions,
            ["line_id"],
        )

        load_table(
            conn,
            expenses,
            "fact_expense",
            list(expense_definitions),
            expense_definitions,
            ["expense_id"],
        )

    print("\nTask 11 financial tables loaded successfully!")


if __name__ == "__main__":
    main()