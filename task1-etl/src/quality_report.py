import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CLEAN = ROOT / "data" / "clean"
LOGS = ROOT / "logs"

DATASETS = [
    "employees",
    "salary",
    "attendance",
    "leave",
    "payroll",
]


def main():
    summary_path = LOGS / "run_summary.json"

    if not summary_path.exists():
        raise FileNotFoundError(
            "Run the ETL pipeline before generating the report."
        )

    summary = json.loads(
        summary_path.read_text(encoding="utf-8")
    )

    report = []

    for name in DATASETS:
        path = CLEAN / f"{name}.csv"

        if not path.exists():
            raise FileNotFoundError(
                f"Missing cleaned dataset: {path}"
            )

        df = pd.read_csv(path)

        report.append({
            "dataset": name,
            "clean_rows": len(df),
            "duplicate_rows": int(df.duplicated().sum()),
            "missing_cells": int(df.isna().sum().sum()),
            "missing_leaving_dates": (
                int(df["leaving_date"].isna().sum())
                if name == "employees" else 0
            ),
        })

    result = pd.DataFrame(report)
    output = LOGS / "data_quality_report.csv"
    result.to_csv(output, index=False)

    print(result.to_string(index=False))
    print(f"\nReport saved to: {output}")
    print(f"Sample data: {summary['sample_data']}")


if __name__ == "__main__":
    main()