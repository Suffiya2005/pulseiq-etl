"""PulseIQ ETL pipeline for employees, payroll, attendance, and leave."""

from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timezone
from pathlib import Path
from src.validate import validate_employees, validate_payroll
import pandas as pd

# --------------------------------------------------
# 1. PROJECT PATHS AND CONFIGURATION
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

RAW = ROOT / os.getenv("RAW_DATA_DIR", "data/raw")
CLEAN = ROOT / os.getenv("CLEAN_DATA_DIR", "data/clean")
LOG_DIR = ROOT / os.getenv("LOG_DIR", "logs")
REJECTED_DIR = ROOT / os.getenv("REJECTED_DIR", "rejected")

AS_OF_DATE = pd.Timestamp(
    os.getenv("AS_OF_DATE", date.today().isoformat())
)

DATASETS = ("employees", "salary", "payroll", "attendance", "leave")

EMPLOYEE_REQUIRED = [
    "employee_key",
    "employee_id",
    "full_name",
    "hire_date",
    "employment_status",
    "is_current",
]

PAYROLL_REQUIRED = [
    "payroll_item_id",
    "employee_id",
    "employee_key",
    "period_end_date",
    "payable_days",
    "lop_days",
    "monthly_fixed_gross",
    "gross_pay",
    "total_deductions",
    "net_pay",
    "employer_cost",
]

ATTENDANCE_REQUIRED = [
    "attendance_fact_id",
    "employee_id",
    "employee_key",
    "period_end_date",
    "scheduled_days",
    "present_days",
    "attendance_rate",
]

LEAVE_REQUIRED = [
    "leave_request_id",
    "employee_id",
    "employee_key",
    "start_date",
    "end_date",
    "days",
    "status",
]

REQUIRED = {
    "employees": EMPLOYEE_REQUIRED,
    "payroll": PAYROLL_REQUIRED,
    "attendance": ATTENDANCE_REQUIRED,
    "leave": LEAVE_REQUIRED,
}

PAYROLL_MONEY_COLUMNS = [
    "monthly_fixed_gross",
    "basic",
    "hra",
    "conveyance",
    "medical",
    "special_allowance",
    "earned_fixed_pay",
    "overtime_pay",
    "variable_pay",
    "gross_pay",
    "pf_employee",
    "esi_employee",
    "professional_tax",
    "tds",
    "other_deductions",
    "total_deductions",
    "net_pay",
    "pf_employer",
    "esi_employer",
    "employer_cost",
]

PAYROLL_NUMERIC_COLUMNS = [
    "payable_days",
    "lop_days",
    "overtime_hours_paid",
] + PAYROLL_MONEY_COLUMNS

ATTENDANCE_NUMERIC_COLUMNS = [
    "scheduled_days",
    "present_days",
    "wfh_days",
    "half_days_unpaid",
    "paid_leave_days",
    "unpaid_absence_days",
    "late_arrivals",
    "avg_hours_worked",
    "overtime_hours",
    "attendance_rate",
]


# --------------------------------------------------
# 2. LOGGING AND DIRECTORY SETUP
# --------------------------------------------------

def setup() -> None:
    for folder in (CLEAN, LOG_DIR, REJECTED_DIR):
        folder.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(
                LOG_DIR / "pipeline.log",
                encoding="utf-8",
            ),
            logging.StreamHandler(),
        ],
        force=True,
    )


# --------------------------------------------------
# 3. EXTRACT
# --------------------------------------------------

def read_source(name: str) -> pd.DataFrame:
    path = RAW / f"{name}.csv"

    if not path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {path}. "
            f"Run the extraction script first."
        )

    df = pd.read_csv(path, low_memory=False)
    df.columns = [str(column).strip() for column in df.columns]

    logging.info(
        "READ dataset=%s rows=%d columns=%d",
        name,
        len(df),
        len(df.columns),
    )

    return df


# --------------------------------------------------
# 4. COMMON TRANSFORMATION HELPERS
# --------------------------------------------------

def check_required(
    df: pd.DataFrame,
    required: list[str],
    dataset: str,
) -> None:
    missing = [column for column in required if column not in df.columns]

    if missing:
        raise ValueError(
            f"{dataset}.csv missing required columns: {missing}. "
            f"Available columns: {list(df.columns)}"
        )


def to_numeric(
    df: pd.DataFrame,
    columns: list[str],
) -> None:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )


def parse_dates(
    df: pd.DataFrame,
    columns: list[str],
) -> None:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce",
            )


def add_period_columns(
    df: pd.DataFrame,
    date_column: str,
) -> None:
    if date_column not in df.columns:
        return

    parsed = pd.to_datetime(df[date_column], errors="coerce")

    df["year"] = parsed.dt.year.astype("Int64")
    df["month"] = parsed.dt.month.astype("Int64")
    df["year_month"] = parsed.dt.strftime("%Y-%m")


def add_reason(
    reasons: pd.Series,
    mask: pd.Series,
    message: str,
) -> None:
    mask = mask.reindex(reasons.index).fillna(False).astype(bool)

    reasons.loc[mask] = reasons.loc[mask].map(
        lambda old: f"{old}; {message}" if old else message
    )


def split_valid_rejected(
    df: pd.DataFrame,
    reasons: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    reasons = reasons.reindex(df.index).fillna("").astype(str)
    rejected_mask = reasons.str.len() > 0

    valid = df.loc[~rejected_mask].copy()
    rejected = df.loc[rejected_mask].copy()

    if not rejected.empty:
        rejected.insert(
            0,
            "reject_reason",
            reasons.loc[rejected_mask].values,
        )

    logging.info(
        "VALIDATION input=%d valid=%d rejected=%d",
        len(df),
        len(valid),
        len(rejected),
    )

    return valid, rejected


# --------------------------------------------------
# 5. TRANSFORM EMPLOYEES
# --------------------------------------------------

def clean_employees(
    source: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    check_required(source, EMPLOYEE_REQUIRED, "employees")

    df = source.copy()

    # Standardise whitespace in text fields.
    for column in df.select_dtypes(include=["object", "string"]).columns:
        df[column] = df[column].map(
            lambda value: value.strip() if isinstance(value, str) else value
        )
        df[column] = df[column].replace("", pd.NA)

    parse_dates(
        df,
        ["date_of_birth", "hire_date", "exit_date", "valid_from", "valid_to"],
    )
    to_numeric(df, ["employee_key"])

    # Exact duplicate rows are removed.
    df = df.drop_duplicates().reset_index(drop=True)

    reasons = pd.Series("", index=df.index, dtype="object")

    for column in [
        "employee_key",
        "employee_id",
        "full_name",
        "hire_date",
    ]:
        add_reason(
            reasons,
            df[column].isna(),
            f"missing_or_invalid_{column}",
        )

    # employee_key identifies a dimension row.
    # employee_id can repeat across historical SCD records.
    add_reason(
        reasons,
        df["employee_key"].duplicated(keep=False),
        "duplicate_employee_key",
    )

    current = df["is_current"].astype("string").str.strip().str.upper()
    df["is_current"] = current

    add_reason(
        reasons,
        ~current.isin(["Y", "N"]),
        "invalid_is_current",
    )

    if "exit_date" in df.columns:
        add_reason(
            reasons,
            df["exit_date"].notna()
            & (df["hire_date"] > df["exit_date"]),
            "hire_date_after_exit_date",
        )

    add_reason(
        reasons,
        df["hire_date"] > AS_OF_DATE,
        "hire_date_in_future",
    )

    if "date_of_birth" in df.columns:
        add_reason(
            reasons,
            df["date_of_birth"] > AS_OF_DATE,
            "date_of_birth_in_future",
        )
        add_reason(
        reasons,
        df["exit_date"].notna()
        & (df["hire_date"] > df["exit_date"]),
        "hire_date_after_exit_date",
    )
    df["tenure_days"] = (AS_OF_DATE - df["hire_date"]).dt.days
    df["tenure_years"] = (df["tenure_days"] / 365.25).round(2)
    # Reject overlapping employee history periods.
    if {"employee_id", "valid_from", "valid_to"}.issubset(df.columns):
        history = df.sort_values(
            ["employee_id", "valid_from"]
        ).copy()

        previous_to = history.groupby("employee_id")["valid_to"].shift()

        overlap_index = history.index[
            previous_to.notna()
            & history["valid_from"].notna()
            & (history["valid_from"] <= previous_to)
        ]

        add_reason(
            reasons,
            pd.Series(df.index.isin(overlap_index), index=df.index),
            "overlapping_employee_history",
        )
    valid, rejected = split_valid_rejected(df, reasons)

    if not valid.empty:
        validate_employees(valid)

    return valid, rejected


def clean_salary(
    source: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    required = ["employee_id", "salary", "effective_date"]
    check_required(source, required, "salary")

    df = source.copy()
    reasons = pd.Series("", index=df.index, dtype="object")

    for column in ["employee_id"]:
        df[column] = df[column].astype("string").str.strip()

    df["salary"] = pd.to_numeric(df["salary"], errors="coerce")
    df["effective_date"] = pd.to_datetime(
        df["effective_date"], errors="coerce"
    )

    add_reason(
        reasons,
        df["employee_id"].isna() | df["employee_id"].eq(""),
        "missing_employee_id",
    )
    add_reason(
        reasons,
        df["salary"].isna(),
        "invalid_salary",
    )
    add_reason(
        reasons,
        df["salary"] < 0,
        "negative_salary",
    )
    add_reason(
        reasons,
        df["effective_date"].isna(),
        "invalid_effective_date",
    )
    
    valid, rejected = split_valid_rejected(df, reasons)
    return valid, rejected
# --------------------------------------------------
# 6. TRANSFORM PAYROLL
# --------------------------------------------------


def clean_payroll(
    source: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    check_required(source, PAYROLL_REQUIRED, "payroll")

    df = source.copy()

    parse_dates(df, ["period_end_date"])
    to_numeric(df, PAYROLL_NUMERIC_COLUMNS)

    for column in [
        "employee_key",
        "date_key",
        "department_id",
        "role_id",
        "run_id",
    ]:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    df = df.drop_duplicates().reset_index(drop=True)
    reasons = pd.Series("", index=df.index, dtype="object")

    for column in [
        "payroll_item_id",
        "employee_id",
        "employee_key",
        "period_end_date",
    ]:
        add_reason(
            reasons,
            df[column].isna(),
            f"missing_or_invalid_{column}",
        )

    add_reason(
        reasons,
        df["payroll_item_id"].duplicated(keep=False),
        "duplicate_payroll_item_id",
    )

    for column in PAYROLL_NUMERIC_COLUMNS:
        if column in df.columns:
            add_reason(
                reasons,
                df[column].isna(),
                f"missing_or_non_numeric_{column}",
            )
            add_reason(
                reasons,
                df[column] < 0,
                f"negative_{column}",
            )

    add_reason(
        reasons,
        df["lop_days"] > df["payable_days"],
        "lop_days_exceed_payable_days",
    )

    add_period_columns(df, "period_end_date")

    # Separate rows that failed basic cleaning rules.
    valid, rejected = split_valid_rejected(df, reasons)

    # Validate rows that passed basic cleaning with Pandera.
    if not valid.empty:
        try:
            validate_payroll(valid)
        except Exception as exc:
            raise ValueError(
                f"Pandera payroll validation failed: {exc}"
            ) from exc

    return valid, rejected

# --------------------------------------------------
# 7. TRANSFORM ATTENDANCE
# --------------------------------------------------

def clean_attendance(
    source: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    check_required(source, ATTENDANCE_REQUIRED, "attendance")

    df = source.copy()

    parse_dates(df, ["period_end_date"])
    to_numeric(df, ATTENDANCE_NUMERIC_COLUMNS)

    for column in ["employee_key", "date_key", "department_id"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.drop_duplicates().reset_index(drop=True)
    reasons = pd.Series("", index=df.index, dtype="object")

    for column in [
        "attendance_fact_id",
        "employee_id",
        "employee_key",
        "period_end_date",
    ]:
        add_reason(
            reasons,
            df[column].isna(),
            f"missing_or_invalid_{column}",
        )

    add_reason(
        reasons,
        df["attendance_fact_id"].duplicated(keep=False),
        "duplicate_attendance_fact_id",
    )

    # Convert percentages such as 95 to 0.95.
    if "attendance_rate" in df.columns:
        max_rate = df["attendance_rate"].max(skipna=True)

        if pd.notna(max_rate) and 1 < max_rate <= 100:
            df["attendance_rate"] = df["attendance_rate"] / 100.0

    for column in ATTENDANCE_NUMERIC_COLUMNS:
        if column in df.columns:
            add_reason(
                reasons,
                df[column].isna(),
                f"missing_or_non_numeric_{column}",
            )
            add_reason(
                reasons,
                df[column] < 0,
                f"negative_{column}",
            )

    add_reason(
        reasons,
        df["present_days"] > df["scheduled_days"],
        "present_days_exceed_scheduled_days",
    )

    add_reason(
        reasons,
        (df["attendance_rate"] < 0) | (df["attendance_rate"] > 1),
        "attendance_rate_out_of_range",
    )

    add_period_columns(df, "period_end_date")

    return split_valid_rejected(df, reasons)


# --------------------------------------------------
# 8. TRANSFORM LEAVE
# --------------------------------------------------

def clean_leave(
    source: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    check_required(source, LEAVE_REQUIRED, "leave")

    df = source.copy()

    parse_dates(
        df,
        ["start_date", "end_date", "applied_on", "decided_on"],
    )
    to_numeric(df, ["days", "employee_key"])

    df = df.drop_duplicates().reset_index(drop=True)
    reasons = pd.Series("", index=df.index, dtype="object")

    for column in [
        "leave_request_id",
        "employee_id",
        "employee_key",
        "start_date",
        "end_date",
        "days",
        "status",
    ]:
        add_reason(
            reasons,
            df[column].isna(),
            f"missing_or_invalid_{column}",
        )

    add_reason(
        reasons,
        df["leave_request_id"].duplicated(keep=False),
        "duplicate_leave_request_id",
    )

    add_reason(
        reasons,
        df["start_date"] > df["end_date"],
        "start_date_after_end_date",
    )

    add_reason(
        reasons,
        df["days"] < 0,
        "negative_leave_days",
    )

    add_period_columns(df, "start_date")

    return split_valid_rejected(df, reasons)


# --------------------------------------------------
# 9. COMMON CLEAN FUNCTION FOR TESTS
# --------------------------------------------------

def clean(
    dataset: str,
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    cleaners = {
    "employees": clean_employees,
    "salary": clean_salary,
    "payroll": clean_payroll,
    "attendance": clean_attendance,
    "leave": clean_leave,
}

    if dataset not in cleaners:
        raise ValueError(
            f"Unknown dataset: {dataset}. "
            f"Supported datasets: {list(cleaners)}"
        )

    return cleaners[dataset](df)


# --------------------------------------------------
# 10. LOAD CLEAN AND REJECTED OUTPUTS
# --------------------------------------------------

def save_dataset(
    name: str,
    valid: pd.DataFrame,
    rejected: pd.DataFrame,
) -> dict:
    CLEAN.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)

    clean_path = CLEAN / f"{name}.csv"
    rejected_path = REJECTED_DIR / f"{name}_rejected.csv"

    valid.to_csv(clean_path, index=False, date_format="%Y-%m-%d")
    rejected.to_csv(rejected_path, index=False, date_format="%Y-%m-%d")

    try:
        valid.to_parquet(CLEAN / f"{name}.parquet", index=False)
        parquet_status = "saved"
    except (ImportError, ModuleNotFoundError, ValueError) as exc:
        parquet_status = f"skipped: {exc}"
        logging.warning(
            "Parquet skipped for %s: %s",
            name,
            exc,
        )

    return {
        "dataset": name,
        "input_rows": len(valid) + len(rejected),
        "output_rows": len(valid),
        "rejected_rows": len(rejected),
        "csv_output": str(clean_path.relative_to(ROOT)),
        "rejected_output": str(rejected_path.relative_to(ROOT)),
        "parquet_status": parquet_status,
    }


# --------------------------------------------------
# 11. MAIN ETL PIPELINE
# --------------------------------------------------

def main() -> None:
    setup()

    started_at = datetime.now(timezone.utc).isoformat()

    logging.info("Starting PulseIQ ETL")

    report = {
        "pipeline": "PulseIQ ETL",
        "started_at_utc": started_at,
        "as_of_date": AS_OF_DATE.strftime("%Y-%m-%d"),
        "datasets": [],
        "total_input": 0,
        "total_output": 0,
        "total_rejected": 0,
    }

    for name in DATASETS:
        source = read_source(name)

        valid, rejected = clean(name, source)

        result = save_dataset(name, valid, rejected)
        report["datasets"].append(result)

        report["total_input"] += result["input_rows"]
        report["total_output"] += result["output_rows"]
        report["total_rejected"] += result["rejected_rows"]

        logging.info(
            "RESULT dataset=%s input=%d output=%d rejected=%d",
            name,
            result["input_rows"],
            result["output_rows"],
            result["rejected_rows"],
        )

    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()

    summary_path = LOG_DIR / "run_summary.json"
    summary_path.write_text(
        json.dumps(report, indent=2, default=str),
        encoding="utf-8",
    )

    logging.info(
        "ETL COMPLETE input=%d output=%d rejected=%d",
        report["total_input"],
        report["total_output"],
        report["total_rejected"],
    )
    logging.info("Run summary saved to %s", summary_path)


if __name__ == "__main__":
    main()

