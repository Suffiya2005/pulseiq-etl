

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
    all_errors = []
    frames = {}

    for name in DATASETS:
        path = RAW_DIR / f"{name}.csv"
        if not path.exists():
            print(f"ERROR: Missing source file: {path}")
            raise SystemExit(1)

        frames[name] = pd.read_csv(path, dtype="string")

    employee_keys = pd.to_numeric(
        frames["employees"].get(
            "employee_key", pd.Series(dtype="string")
        ),
        errors="coerce",
    ).dropna()

    valid_employee_keys = set(employee_keys[employee_keys > 0])

    for name in DATASETS:
        feed = f"Core dataset ({name})"
        contract = contracts[contracts["feed"] == feed]
        df = frames[name]
        errors = []

        actual_columns = set(df.columns)
        contract_columns = set(contract["column_name"])

        for column in sorted(actual_columns - contract_columns):
            errors.append(f"{column}: unexpected column")

        for column in sorted(contract_columns - actual_columns):
            errors.append(f"{column}: column missing from CSV")

        def check(mask, message):
            count = int(mask.fillna(False).sum())
            if count:
                errors.append(f"{message}: {count} invalid value(s)")

        for _, rule in contract.iterrows():
            column = rule["column_name"]
            if column not in df.columns:
                continue

            values = df[column].astype("string").str.strip()
            blank = is_blank(values)
            present = values[~blank]
            dtype = rule["data_type"].strip().lower()
            allowed = rule["rule_or_allowed_values"].strip().lower()
            nullable = rule["nullable"].strip().lower() == "yes"

            if not nullable:
                check(blank, f"{column}: required value is blank")

            if dtype in {"integer", "decimal", "decimal(14,2)",
                         "decimal(4,3)"}:
                numeric = pd.to_numeric(present, errors="coerce")
                check(numeric.isna(), f"{column}: non-numeric")

                if dtype == "integer":
                    check(
                        numeric.notna() & (numeric % 1 != 0),
                        f"{column}: not an integer",
                    )

                if dtype == "decimal(14,2)":
                    from decimal import Decimal, InvalidOperation

                    invalid_precision = []
                    for value in present:
                        try:
                            number = Decimal(str(value))
                            invalid_precision.append(
                                number.is_finite()
                                and number != number.quantize(
                                    Decimal("0.01")
                                )
                            )
                        except (InvalidOperation, ValueError):
                            invalid_precision.append(False)

                    check(
                        pd.Series(
                            invalid_precision,
                            index=present.index,
                        ),
                        f"{column}: more than 2 decimal places",
                    )
                if dtype == "decimal(4,3)" and column != "attendance_rate":
                    check(
                        numeric.notna()
                        & ((numeric * 1000).round() != numeric * 1000),
                        f"{column}: more than 3 decimal places",
                    )
                if "non-negative" in allowed:
                    check(
                        numeric.notna() & (numeric < 0),
                        f"{column}: negative value",
                    )

                if "positive integer" in allowed:
                    check(
                        numeric.notna() & (numeric <= 0),
                        f"{column}: must be positive",
                    )

                if "0 or 1" in allowed:
                    check(
                        numeric.notna() & ~numeric.isin([0, 1]),
                        f"{column}: must be 0 or 1",
                    )

            if dtype == "date":
                parsed = pd.to_datetime(present, errors="coerce")
                check(parsed.isna(), f"{column}: invalid date")

                if "not in the future" in allowed:
                    check(
                        parsed.notna()
                        & (parsed.dt.normalize() > pd.Timestamp.today().normalize()),
                        f"{column}: date in the future",
                    )

            if allowed == "y or n":
                check(
                    ~present.str.upper().isin(["Y", "N"]),
                    f"{column}: must be Y or N",
                )

            if "non-empty" in allowed:
                check(blank, f"{column}: must not be empty")

            if "unique" in allowed:
                nonblank = values[~blank]
                check(
                    values.duplicated(keep=False) & ~blank,
                    f"{column}: duplicate value",
                )

        # Cross-column date checks
        if name == "employees":
            hire = pd.to_datetime(df["hire_date"], errors="coerce")

            if "exit_date" in df.columns:
                exit_date = pd.to_datetime(df["exit_date"], errors="coerce")
                check(
                    exit_date.notna() & hire.notna() & (exit_date < hire),
                    "exit_date: before hire_date",
                )

            if {"valid_from", "valid_to"}.issubset(df.columns):
                start = pd.to_datetime(df["valid_from"], errors="coerce")
                end = pd.to_datetime(df["valid_to"], errors="coerce")
                check(
                    end.notna() & start.notna() & (end < start),
                    "valid_to: before valid_from",
                )

        if name == "payroll":
            if {"lop_days", "payable_days"}.issubset(df.columns):
                lop = pd.to_numeric(df["lop_days"], errors="coerce")
                payable = pd.to_numeric(df["payable_days"], errors="coerce")
                check(
                    lop.notna() & payable.notna() & (lop > payable),
                    "lop_days: exceeds payable_days",
                )

        if name == "attendance":
            if {"present_days", "scheduled_days"}.issubset(df.columns):
                present_days = pd.to_numeric(
                    df["present_days"], errors="coerce"
                )
                scheduled = pd.to_numeric(
                    df["scheduled_days"], errors="coerce"
                )
                check(
                    present_days.notna() & scheduled.notna()
                    & (present_days > scheduled),
                    "present_days: exceeds scheduled_days",
                )

            if "attendance_rate" in df.columns:
                rate = pd.to_numeric(
                    df["attendance_rate"], errors="coerce"
                )
                # Accept percentages such as 95 and normalise to 0.95
                normalised = rate.where(rate <= 1, rate / 100)
                check(
                    normalised.notna()
                    & ((normalised < 0) | (normalised > 1)),
                    "attendance_rate: outside 0 to 1 after normalisation",
                )

        if name == "leave":
            start = pd.to_datetime(df["start_date"], errors="coerce")
            end = pd.to_datetime(df["end_date"], errors="coerce")
            check(
                start.notna() & end.notna() & (start > end),
                "start_date: after end_date",
            )

        # Check employee dimension keys in related datasets
        if name in {"payroll", "attendance", "leave"}:
            if "employee_key" in df.columns:
                keys = pd.to_numeric(df["employee_key"], errors="coerce")
                check(
                    keys.isna() | ~keys.isin(valid_employee_keys),
                    "employee_key: missing or invalid employee dimension key",
                )

        print(f"\n{name}: {len(errors)} contract issue(s)")
        for error in errors:
            print(" -", error)

        all_errors.extend(errors)

        total_errors += len(errors)

    print(f"\nTotal contract issues: {total_errors}")
    print("Validation report only; source files were not modified.")
    # Stop only for missing or unexpected columns.
    schema_errors = any(
        "unexpected column" in error or "column missing from CSV" in error
        for error in all_errors
    )
    if schema_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
