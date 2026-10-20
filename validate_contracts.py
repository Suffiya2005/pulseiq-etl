
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"
CONTRACT_FILE = ROOT / "data" / "reference" / "data_contracts.csv"

DATASETS = ["employees", "salary", "payroll", "attendance", "leave"]


def is_blank(series):
    return series.isna() | series.astype("string").str.strip().eq("")


def main():
    contracts = pd.read_csv(CONTRACT_FILE, dtype=str).fillna("")
    total_errors = 0

    for name in DATASETS:
        feed = f"Core dataset ({name})"
        contract = contracts[contracts["feed"] == feed]
        path = RAW_DIR / f"{name}.csv"
        df = pd.read_csv(path, dtype="string")

        errors = []
        actual_columns = set(df.columns)
        contract_columns = set(contract["column_name"])

        for column in sorted(actual_columns - contract_columns):
            errors.append(f"{column}: missing contract")

        for column in sorted(contract_columns - actual_columns):
            errors.append(f"{column}: column missing from CSV")

        for _, rule in contract.iterrows():
            column = rule["column_name"]
            if column not in df.columns:
                continue

            values = df[column]
            blank = is_blank(values)
            nullable = rule["nullable"].strip().lower() == "yes"
            dtype = rule["data_type"].strip().lower()
            allowed = rule["rule_or_allowed_values"].strip().lower()

            if not nullable and blank.any():
                errors.append(
                    f"{column}: {int(blank.sum())} blank value(s), "
                    "but nullable=no"
                )

            present = values[~blank].str.strip()

            if dtype in {"integer", "decimal", "decimal(14,2)",
                         "decimal(4,3)"}:
                numeric = pd.to_numeric(present, errors="coerce")
                invalid = numeric.isna()
                if invalid.any():
                    errors.append(
                        f"{column}: {int(invalid.sum())} non-numeric value(s)"
                    )

            elif dtype == "date":
                parsed = pd.to_datetime(present, errors="coerce")
                invalid = parsed.isna()
                if invalid.any():
                    errors.append(
                        f"{column}: {int(invalid.sum())} invalid date(s)"
                    )

            if allowed == "y or n":
                invalid = ~present.str.upper().isin(["Y", "N"])
                if invalid.any():
                    errors.append(
                        f"{column}: {int(invalid.sum())} value(s) not Y/N"
                    )

            if "non-negative" in allowed and dtype.startswith("decimal"):
                numeric = pd.to_numeric(present, errors="coerce")
                invalid = numeric.notna() & (numeric < 0)
                if invalid.any():
                    errors.append(
                        f"{column}: {int(invalid.sum())} negative value(s)"
                    )

        print(f"\n{name}: {len(errors)} contract issue(s)")
        for error in errors:
            print(" -", error)

        total_errors += len(errors)

    print(f"\nTotal contract issues: {total_errors}")
    print("This is a validation report; no source data was changed.")


if __name__ == "__main__":
    main()
