
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"
CONTRACT_FILE = ROOT / "data" / "reference" / "data_contracts.csv"

# Rules are based on the current ETL pipeline and the raw CSV columns.
# These are initial contracts and should be reviewed against the assignment
# specification before treating every rule as final.
RULES = {
    "employees": {
        "required": {
            "employee_key", "employee_id", "full_name",
            "hire_date", "employment_status", "is_current",
        },
        "types": {
            "employee_key": "integer",
            "date_of_birth": "date",
            "hire_date": "date",
            "exit_date": "date",
            "valid_from": "date",
            "valid_to": "date",
            "is_current": "char(1)",
        },
        "rules": {
            "employee_key": "unique, positive integer",
            "employee_id": "non-empty",
            "full_name": "non-empty",
            "hire_date": "valid date, not in the future",
            "exit_date": "blank or valid date on/after hire_date",
            "is_current": "Y or N",
            "valid_from": "blank or valid date",
            "valid_to": "blank or valid date on/after valid_from",
        },
    },
    "salary": {
        "required": {"employee_id", "salary", "effective_date"},
        "types": {
            "employee_id": "string",
            "salary": "decimal(14,2)",
            "effective_date": "date",
        },
        "rules": {
            "employee_id": "non-empty",
            "salary": "numeric and non-negative",
            "effective_date": "valid date",
        },
    },
    "payroll": {
        "required": {
            "payroll_item_id", "employee_id", "employee_key",
            "period_end_date", "payable_days", "lop_days",
            "monthly_fixed_gross", "gross_pay", "total_deductions",
            "net_pay", "employer_cost",
        },
        "types": {
            "payroll_item_id": "string",
            "period_end_date": "date",
            "payable_days": "decimal",
            "lop_days": "decimal",
            "overtime_hours_paid": "decimal",
            "monthly_fixed_gross": "decimal(14,2)",
            "basic": "decimal(14,2)",
            "hra": "decimal(14,2)",
            "conveyance": "decimal(14,2)",
            "medical": "decimal(14,2)",
            "special_allowance": "decimal(14,2)",
            "earned_fixed_pay": "decimal(14,2)",
            "overtime_pay": "decimal(14,2)",
            "variable_pay": "decimal(14,2)",
            "gross_pay": "decimal(14,2)",
            "pf_employee": "decimal(14,2)",
            "esi_employee": "decimal(14,2)",
            "professional_tax": "decimal(14,2)",
            "tds": "decimal(14,2)",
            "other_deductions": "decimal(14,2)",
            "total_deductions": "decimal(14,2)",
            "net_pay": "decimal(14,2)",
            "pf_employer": "decimal(14,2)",
            "esi_employer": "decimal(14,2)",
            "employer_cost": "decimal(14,2)",
            "headcount_flag": "integer",
        },
        "rules": {
            "payroll_item_id": "unique, non-empty",
            "employee_id": "non-empty",
            "employee_key": "required, valid employee dimension key",
            "period_end_date": "valid date",
            "payable_days": "numeric and non-negative",
            "lop_days": "numeric and non-negative, not greater than payable_days",
            "monetary columns": "numeric and non-negative",
            "headcount_flag": "0 or 1",
        },
    },
    "attendance": {
        "required": {
            "attendance_fact_id", "employee_id", "employee_key",
            "period_end_date", "scheduled_days", "present_days",
            "attendance_rate",
        },
        "types": {
            "attendance_fact_id": "string",
            "period_end_date": "date",
            "scheduled_days": "decimal",
            "present_days": "decimal",
            "wfh_days": "decimal",
            "half_days_unpaid": "decimal",
            "paid_leave_days": "decimal",
            "unpaid_absence_days": "decimal",
            "late_arrivals": "integer",
            "avg_hours_worked": "decimal",
            "overtime_hours": "decimal",
            "attendance_rate": "decimal(4,3)",
        },
        "rules": {
            "attendance_fact_id": "unique, non-empty",
            "employee_id": "non-empty",
            "employee_key": "required, valid employee dimension key",
            "period_end_date": "valid date",
            "day and hour measures": "numeric and non-negative",
            "present_days": "not greater than scheduled_days",
            "attendance_rate": "between 0 and 1 after normalisation",
        },
    },
    "leave": {
        "required": {
            "leave_request_id", "employee_id", "employee_key",
            "start_date", "end_date", "days", "status",
        },
        "types": {
            "leave_request_id": "string",
            "start_date": "date",
            "end_date": "date",
            "applied_on": "date",
            "decided_on": "date",
            "days": "decimal",
        },
        "rules": {
            "leave_request_id": "unique, non-empty",
            "employee_id": "non-empty",
            "employee_key": "required, valid employee dimension key",
            "start_date": "valid date, not after end_date",
            "end_date": "valid date",
            "days": "numeric and non-negative",
            "status": "non-empty",
        },
    },
}

def main():
    if not CONTRACT_FILE.exists():
        raise FileNotFoundError(f"Contract file not found: {CONTRACT_FILE}")

    existing = pd.read_csv(CONTRACT_FILE, dtype=str).fillna("")
    required_columns = [
        "feed", "column_name", "data_type", "nullable",
        "rule_or_allowed_values", "description",
    ]

    missing = set(required_columns) - set(existing.columns)
    if missing:
        raise ValueError(f"Contract file is missing columns: {sorted(missing)}")

    additions = []

    for dataset, config in RULES.items():
        csv_path = RAW_DIR / f"{dataset}.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Raw dataset not found: {csv_path}")

        columns = pd.read_csv(csv_path, nrows=0).columns.tolist()
        required = config["required"]

        missing_required = required - set(columns)
        if missing_required:
            raise ValueError(
                f"{dataset}.csv missing required columns: "
                f"{sorted(missing_required)}"
            )

        for column in columns:
            data_type = config["types"].get(column, "string")
            nullable = "no" if column in required else "yes"
            rule = config["rules"].get(column, "")
            if not rule:
                rule = "validate according to declared data type"
            description = f"{dataset} dataset column"

            additions.append({
                "feed": f"Core dataset ({dataset})",
                "column_name": column,
                "data_type": data_type,
                "nullable": nullable,
                "rule_or_allowed_values": rule,
                "description": description,
            })

    new_rows = pd.DataFrame(additions, columns=required_columns)

    # Keep existing rows and avoid duplicate dataset/column contract pairs.
    combined = pd.concat([existing, new_rows], ignore_index=True)
    combined = combined.drop_duplicates(
        subset=["feed", "column_name"],
        keep="first",
    )

    # Write only after all inputs and headers have been checked.
    combined.to_csv(CONTRACT_FILE, index=False)

    print("Contract update completed.")
    print(f"Existing contract rows: {len(existing)}")
    print(f"New core contract rows considered: {len(new_rows)}")
    print(f"Final contract rows: {len(combined)}")
    print("\nCore contract counts:")
    print(
        combined[combined["feed"].str.startswith("Core dataset (")]
        .groupby("feed")
        .size()
        .to_string()
    )

if __name__ == "__main__":
    main()
