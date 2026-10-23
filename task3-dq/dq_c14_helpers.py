
import re
from pathlib import Path

import pandas as pd


LEADERSHIP_DEPARTMENT = "D00"


def find_undersized_groups(group_counts, minimum_size):
    """Return reporting groups below the configured minimum."""
    if minimum_size <= 0:
        raise ValueError("minimum_size must be positive")
    return group_counts[group_counts < minimum_size]


def count_distinct_employees_by_group(df, group_columns):
    """Count distinct non-null employees in each reporting group."""
    required = set(group_columns) | {"employee_id"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    return df.groupby(
        list(group_columns), dropna=False
    )["employee_id"].nunique()


def count_tasks_by_group(df, group_columns=("team_id", "sprint_id")):
    """Count distinct tasks in each reporting group."""
    required = set(group_columns) | {"task_id"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    return df.groupby(
        list(group_columns), dropna=False
    )["task_id"].nunique()


def _parse_minimum(value):
    """Read a positive integer minimum, including values like '5 tasks'."""
    match = re.match(r"^\s*(\d+)", str(value))
    if not match:
        raise ValueError(f"Invalid minimum_group_size: {value!r}")

    minimum = int(match.group(1))
    if minimum <= 0:
        raise ValueError(f"Invalid minimum_group_size: {value!r}")

    return minimum


def validate_reporting_groups(workbook_path):
    """
    Validate configured minimum group sizes using workbook data.

    Returns:
        violations: undersized reporting groups
        checked_groups: number of reporting groups checked
        limitations: metrics that could not be validated safely
    """
    workbook_path = Path(workbook_path)
    metrics = pd.read_excel(
        workbook_path, sheet_name="metric_dictionary"
    )

    violations = []
    limitations = []
    checked_groups = 0
    cache = {}

    def read_sheet(name):
        if name not in cache:
            cache[name] = pd.read_excel(
                workbook_path, sheet_name=name
            )
        return cache[name].copy()

    def exclude_leadership(df):
        if "department_id" in df.columns:
            df = df[
                df["department_id"].astype(str)
                != LEADERSHIP_DEPARTMENT
            ].copy()
        return df

    for _, metric in metrics[
        metrics["minimum_group_size"].notna()
    ].iterrows():
        metric_id = str(metric["metric_id"]).strip()
        metric_name = str(metric["metric_name"]).strip()

        try:
            minimum = _parse_minimum(metric["minimum_group_size"])
        except ValueError as exc:
            limitations.append(f"{metric_id}: {exc}")
            continue

        counts = None

        # Historical department-month headcount/attrition groups.
        if metric_id in {"M01", "M04", "M05", "M06"}:
            employees = read_sheet("dim_employee")

            required = {
                "employee_id", "department_id", "hire_date",
                "exit_date", "valid_from", "valid_to",
            }
            missing = required.difference(employees.columns)

            if missing:
                limitations.append(
                    f"{metric_id} ({metric_name}): missing employee "
                    f"history columns {sorted(missing)}"
                )
                continue

            headcount = read_sheet("fact_headcount_monthly")
            if "month_start_date" not in headcount.columns:
                limitations.append(
                    f"{metric_id} ({metric_name}): missing "
                    "month_start_date in fact_headcount_monthly"
                )
                continue

            headcount["month_start_date"] = pd.to_datetime(
                headcount["month_start_date"], errors="coerce"
            )

            for col in (
                "hire_date", "exit_date", "valid_from", "valid_to"
            ):
                employees[col] = pd.to_datetime(
                    employees[col], errors="coerce"
                )

            month_ends = (
                headcount["month_start_date"]
                .dropna()
                .drop_duplicates()
                .sort_values()
                + pd.offsets.MonthEnd(0)
            )

            records = []
            for month_end in month_ends:
                active = employees[
                    (employees["hire_date"] <= month_end)
                    & (
                        employees["exit_date"].isna()
                        | (employees["exit_date"] > month_end)
                    )
                    & (employees["valid_from"] <= month_end)
                    & (employees["valid_to"] >= month_end)
                ].copy()

                # Resolve overlapping history deterministically.
                active = active.sort_values("valid_from").drop_duplicates(
                    "employee_id", keep="last"
                )
                active = exclude_leadership(active)
                for department, group in active.groupby(
                    "department_id", dropna=False
                ):
                    records.append({
                        "department_id": department,
                        "month_end": month_end,
                        "employee_count": group["employee_id"].nunique(),
                    })

            if not records:
                limitations.append(
                    f"{metric_id} ({metric_name}): no historical "
                    "department-month groups could be calculated"
                )
                continue

            counts = pd.DataFrame(records).set_index(
                ["department_id", "month_end"]
            )["employee_count"]

        # Monthly hire and exit events by department.
        elif metric_id in {"M02", "M03"}:
            employees = read_sheet("dim_employee")
            event_date = "hire_date" if metric_id == "M02" else "exit_date"

            required = {
                "employee_id", "department_id", event_date, "valid_from"
            }
            missing = required.difference(employees.columns)

            if missing:
                limitations.append(
                    f"{metric_id} ({metric_name}): missing columns "
                    f"{sorted(missing)}"
                )
                continue

            employees[event_date] = pd.to_datetime(
                employees[event_date], errors="coerce"
            )
            employees["valid_from"] = pd.to_datetime(
                employees["valid_from"], errors="coerce"
            )

            events = employees.dropna(
                subset=["employee_id", "department_id", event_date]
            ).copy()
            events["month"] = events[event_date].dt.to_period("M")
            events = exclude_leadership(events)

            events = events.sort_values("valid_from").drop_duplicates(
                ["employee_id", event_date], keep="last"
            )
            counts = events.groupby(
                ["department_id", "month"], dropna=False
            )["employee_id"].nunique()

        # Payroll metrics M07-M12 and M15 share payroll employee-month grain.
        elif metric_id in {
            "M07", "M08", "M09", "M10", "M11", "M12", "M15"
        }:
            fact = read_sheet("fact_payroll")
            required = {
                "employee_id", "department_id", "period_end_date"
            }
            missing = required.difference(fact.columns)

            if missing:
                limitations.append(
                    f"{metric_id} ({metric_name}): missing payroll "
                    f"columns {sorted(missing)}"
                )
                continue

            fact["period_end_date"] = pd.to_datetime(
                fact["period_end_date"], errors="coerce"
            )
            fact = fact.dropna(
                subset=["employee_id", "department_id", "period_end_date"]
            )
            fact["month"] = fact["period_end_date"].dt.to_period("M")
            fact = exclude_leadership(fact)

            counts = count_distinct_employees_by_group(
                fact, ["department_id", "month"]
            )

        # Attendance metrics by department and month.
        elif metric_id in {"M13", "M14"}:
            fact = read_sheet("fact_attendance_monthly")
            required = {
                "employee_id", "department_id", "period_end_date"
            }
            missing = required.difference(fact.columns)

            if missing:
                limitations.append(
                    f"{metric_id} ({metric_name}): missing attendance "
                    f"columns {sorted(missing)}"
                )
                continue

            fact["period_end_date"] = pd.to_datetime(
                fact["period_end_date"], errors="coerce"
            )
            fact = fact.dropna(
                subset=["employee_id", "department_id", "period_end_date"]
            )
            fact["month"] = fact["period_end_date"].dt.to_period("M")
            fact = exclude_leadership(fact)

            counts = count_distinct_employees_by_group(
                fact, ["department_id", "month"]
            )

        # Task metrics: count distinct tasks by team and sprint.
        elif metric_id in {"M22", "M23", "M25"}:
            fact = read_sheet("fact_task")
            counts = count_tasks_by_group(
                fact, ["team_id", "sprint_id"]
            )

        # Department-level attrition-risk reporting.
        elif metric_id == "M27":
            fact = read_sheet("fact_attrition_risk")
            required = {"employee_id", "department_id"}
            missing = required.difference(fact.columns)

            if missing:
                limitations.append(
                    f"{metric_id} ({metric_name}): missing risk "
                    f"columns {sorted(missing)}"
                )
                continue

            fact = exclude_leadership(fact)
            counts = count_distinct_employees_by_group(
                fact, ["department_id"]
            )

        else:
            limitations.append(
                f"{metric_id} ({metric_name}): no defined reporting "
                "aggregation implemented for this metric"
            )
            continue

        counts = counts.dropna()
        checked_groups += len(counts)

        for group, count in find_undersized_groups(
            counts, minimum
        ).items():
            violations.append(
                f"{metric_id} ({metric_name}): group {group} has "
                f"{int(count)} distinct employees/tasks; minimum {minimum}"
            )

    return violations, checked_groups, limitations

def suppress_undersized_groups(group_counts, minimum_size=10):
    """Suppress reporting counts below the configured privacy threshold."""
    if minimum_size <= 0:
        raise ValueError("minimum_size must be positive")

    return group_counts.where(group_counts >= minimum_size, other=pd.NA)
