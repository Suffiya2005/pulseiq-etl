import os
import psycopg
import pytest


@pytest.fixture(scope="module")
def warehouse_connection():
    conn = psycopg.connect(
        host=os.getenv("WAREHOUSE_HOST", "localhost"),
        port=os.getenv("WAREHOUSE_PORT", "5433"),
        dbname=os.getenv("WAREHOUSE_DB", "pulseiq_warehouse"),
        user=os.getenv("WAREHOUSE_USER", "pulseiq"),
        password=os.getenv("WAREHOUSE_PASSWORD", "pulseiq_dev_password"),
    )
    yield conn
    conn.close()


def test_fact_tables_have_no_missing_employee_references(
    warehouse_connection,
):
    tables = [
        "fact_payroll",
        "fact_attendance_monthly",
        "fact_leave",
    ]

    with warehouse_connection.cursor() as cur:
        for table in tables:
            cur.execute(
                f"""
                SELECT COUNT(*)
                FROM warehouse.{table} f
                LEFT JOIN warehouse.dim_employee e
                    ON f.employee_key = e.employee_key
                WHERE e.employee_key IS NULL
                """
            )
            missing = cur.fetchone()[0]
            assert missing == 0, (
                f"{table} contains {missing} missing employee references"
            )


@pytest.mark.parametrize(
    ("table", "expected_count"),
    [
        ("fact_payroll", 7342),
        ("fact_attendance_monthly", 7343),
        ("fact_leave", 3439),
    ],
)
def test_fact_table_row_counts(
    warehouse_connection, table, expected_count
):
    with warehouse_connection.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM warehouse.{table}")
        actual_count = cur.fetchone()[0]

    assert actual_count == expected_count
