
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

WORKBOOK = (
    ROOT
    / "data"
    / "source"
    / "03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"
)

RAW_DIR = ROOT / "data" / "raw"
CONTRACT_DIR = ROOT / "data" / "reference"

SHEETS = {
    "dim_employee": "employees.csv",
    "fact_payroll": "payroll.csv",
    "fact_attendance_monthly": "attendance.csv",
    "fact_leave": "leave.csv",
    "data_contracts": "data_contracts.csv",
}


def main():
    if not WORKBOOK.exists():
        raise FileNotFoundError(
            f"Master workbook not found: {WORKBOOK}"
        )

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CONTRACT_DIR.mkdir(parents=True, exist_ok=True)

    print("Starting PulseIQ master data extraction...")

    for sheet_name, output_name in SHEETS.items():
        df = pd.read_excel(
            WORKBOOK,
            sheet_name=sheet_name,
            engine="openpyxl",
        )

        if sheet_name == "data_contracts":
            output_path = CONTRACT_DIR / output_name
        else:
            output_path = RAW_DIR / output_name

        df.to_csv(output_path, index=False)

        print(
            f"{sheet_name}: {len(df)} rows, "
            f"{len(df.columns)} columns -> {output_path}"
        )

    print("Master data extraction completed.")


if __name__ == "__main__":
    main()
