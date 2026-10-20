
from pathlib import Path
import pandas as pd
import duckdb

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "pulseiq_task1.duckdb"

DATASETS = ["employees", "salary", "payroll", "attendance", "leave"]

with duckdb.connect(str(DB_PATH), read_only=True) as con:
    all_match = True

    for name in DATASETS:
        csv_path = RAW_DIR / f"{name}.csv"
        csv_rows = len(pd.read_csv(csv_path))
        db_rows = con.execute(
            f'SELECT COUNT(*) FROM "{name}"'
        ).fetchone()[0]

        match = csv_rows == db_rows
        all_match = all_match and match

        print(
            f"{name}: CSV={csv_rows}, "
            f"DuckDB={db_rows}, MATCH={match}"
        )

    print("\nAll datasets match:", all_match)
