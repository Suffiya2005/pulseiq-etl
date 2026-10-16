
import os
import subprocess
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

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


# Read the anomaly sample from Excel.
if not excel_file.exists():
    raise FileNotFoundError(f"Excel file not found: {excel_file}")

df = pd.read_excel(excel_file, sheet_name="fact_anomaly")
df.columns = [
    str(col).strip().lower().replace(" ", "_")
    for col in df.columns
]

if df.empty:
    raise RuntimeError("The fact_anomaly sheet contains no rows.")

# Use .env settings when available; otherwise use Docker's settings.
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

        # Fail safely if the table already exists; never replace its data.
        df.to_sql(
            "fact_anomaly",
            con=conn,
            schema="warehouse",
            if_exists="fail",
            index=False,
            method="multi",
            chunksize=500,
        )

        count = conn.execute(
            text("SELECT COUNT(*) FROM warehouse.fact_anomaly")
        ).scalar_one()

    print(f"Successfully loaded {count} anomaly rows.")
    print(f"Columns: {', '.join(df.columns)}")

finally:
    engine.dispose()
