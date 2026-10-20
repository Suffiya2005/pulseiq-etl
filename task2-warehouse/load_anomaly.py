
import os
import subprocess
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import (
    URL,
    MetaData,
    Table,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import insert

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

excel_file = (
    ROOT
    / "data"
    / "reference"
    / "03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"
)


def get_container_env(name):
    """Read a setting from the running PostgreSQL container."""
    result = subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "postgres",
            "printenv",
            name,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    value = result.stdout.strip()
    if not value:
        raise RuntimeError(f"{name} is empty in the PostgreSQL container.")
    return value


# Read anomaly data from Excel.
if not excel_file.exists():
    raise FileNotFoundError(f"Excel file not found: {excel_file}")

df = pd.read_excel(excel_file, sheet_name="fact_anomaly")
df.columns = [
    str(col).strip().lower().replace(" ", "_")
    for col in df.columns
]

if df.empty:
    raise RuntimeError("The fact_anomaly sheet contains no rows.")

if "result_id" not in df.columns:
    raise RuntimeError("The source data must contain result_id.")

if df["result_id"].isna().any():
    raise RuntimeError("result_id contains missing values.")

if df["result_id"].duplicated().any():
    raise RuntimeError("The source contains duplicate result_id values.")

# Use .env settings when available; otherwise use Docker settings.
warehouse_user = (
    os.getenv("WAREHOUSE_USER") or get_container_env("POSTGRES_USER")
)
warehouse_password = (
    os.getenv("WAREHOUSE_PASSWORD")
    or get_container_env("POSTGRES_PASSWORD")
)

url = URL.create(
    drivername="postgresql+psycopg",
    username=warehouse_user,
    password=warehouse_password,
    host=os.getenv("WAREHOUSE_HOST", "localhost"),
    port=int(os.getenv("WAREHOUSE_PORT", "5433")),
    database=os.getenv("WAREHOUSE_DB", "pulseiq_warehouse"),
)

engine = create_engine(url, pool_pre_ping=True)

try:
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS warehouse"))

        # Create the table only if it does not exist.
        # Existing table data and constraints are preserved.
        df.head(0).to_sql(
            "fact_anomaly",
            con=conn,
            schema="warehouse",
            if_exists="append",
            index=False,
        )

        metadata = MetaData()
        anomaly_table = Table(
            "fact_anomaly",
            metadata,
            schema="warehouse",
            autoload_with=conn,
        )

        # Verify the target table has the expected columns.
        if set(df.columns) != set(anomaly_table.columns.keys()):
            raise RuntimeError(
                "Source and warehouse columns do not match. "
                f"Source: {list(df.columns)}; "
                f"Warehouse: {list(anomaly_table.columns.keys())}"
            )

        # Insert new records and update existing records by result_id.
        records = df.astype(object).where(pd.notna(df), None).to_dict(
            orient="records"
        )

        stmt = insert(anomaly_table).values(records)

        updates = {
            column.name: stmt.excluded[column.name]
            for column in anomaly_table.columns
            if column.name != "result_id"
        }

        stmt = stmt.on_conflict_do_update(
            index_elements=["result_id"],
            set_=updates,
        )

        conn.execute(stmt)

        # Verify the final table contains the expected source records.
        source_count = len(df)
        count = conn.execute(
            text("SELECT COUNT(*) FROM warehouse.fact_anomaly")
        ).scalar_one()

        missing_count = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM unnest(CAST(:ids AS text[])) AS source(id)
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM warehouse.fact_anomaly AS target
                    WHERE target.result_id = source.id
                )
            """),
            {"ids": df["result_id"].astype(str).tolist()},
        ).scalar_one()

        if count != source_count or missing_count != 0:
            raise RuntimeError(
                f"Validation failed: source={source_count}, "
                f"warehouse={count}, missing_source_ids={missing_count}."
            )

    print(f"Successfully loaded {count} anomaly rows.")
    print("Duplicate result_id values in source: 0")
    print("All source result_id values exist in the warehouse.")
    print(f"Columns: {', '.join(df.columns)}")

finally:
    engine.dispose()
