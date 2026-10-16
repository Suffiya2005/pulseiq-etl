
import os
import subprocess
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

csv_file = ROOT / "data" / "reference" / "attendance_daily_sample.csv"
table_name = "demo_attendance_daily_sample"

if not csv_file.exists():
    raise FileNotFoundError(f"Demo CSV not found: {csv_file}")

df = pd.read_csv(csv_file)

required_columns = {
    "employee_id",
    "attendance_date",
    "department",
    "weekday",
    "scheduled",
    "present",
    "attendance_status",
    "late_arrival",
}

missing = required_columns - set(df.columns)
if missing:
    raise ValueError(f"Missing columns: {sorted(missing)}")

df["attendance_date"] = pd.to_datetime(
    df["attendance_date"], errors="raise"
).dt.date

def get_container_env(name):
    result = subprocess.run(
        [
            "docker", "compose", "exec", "-T",
            "postgres", "printenv", name,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    value = result.stdout.strip()
    if not value:
        raise RuntimeError(f"{name} is empty in PostgreSQL container.")
    return value

username = os.getenv("WAREHOUSE_USER") or get_container_env("POSTGRES_USER")
password = (
    os.getenv("WAREHOUSE_PASSWORD")
    or get_container_env("POSTGRES_PASSWORD")
)

url = URL.create(
    drivername="postgresql+psycopg",
    username=username,
    password=password,
    host=os.getenv("WAREHOUSE_HOST", "localhost"),
    port=int(os.getenv("WAREHOUSE_PORT", "5433")),
    database=os.getenv("WAREHOUSE_DB", "pulseiq_warehouse"),
)

engine = create_engine(url, pool_pre_ping=True)

try:
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS warehouse"))

        # This replaces only the dedicated synthetic demo table.
        # It does not modify the real attendance table.
        df.to_sql(
            table_name,
            con=conn,
            schema="warehouse",
            if_exists="replace",
            index=False,
            method="multi",
            chunksize=1000,
        )

        loaded = conn.execute(
            text(
                "SELECT COUNT(*) FROM "
                "warehouse.demo_attendance_daily_sample"
            )
        ).scalar_one()

    print(f"Demo rows loaded: {loaded}")
    print("Table: warehouse.demo_attendance_daily_sample")
    print("Data type: SYNTHETIC DEMO ONLY")
finally:
    engine.dispose()
