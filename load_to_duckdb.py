
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "pulseiq_task1.duckdb"

DATASETS = ["employees", "salary", "payroll", "attendance", "leave"]


def main():
    with duckdb.connect(str(DB_PATH)) as con:
        for name in DATASETS:
            csv_path = RAW_DIR / f"{name}.csv"

            con.execute(
                f"""
                CREATE OR REPLACE TABLE "{name}" AS
                SELECT *
                FROM read_csv(
                    ?, delim=',', header=true, strict_mode=false
                )
                """,
                [str(csv_path)],
            )

            count = con.execute(
                f'SELECT COUNT(*) FROM "{name}"'
            ).fetchone()[0]

            print(f"{name}: {count} rows loaded")

    print(f"\nDatabase saved: {DB_PATH}")


if __name__ == "__main__":
    main()
