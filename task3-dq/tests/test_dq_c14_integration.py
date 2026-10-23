
import pandas as pd


def calculate_tenure_groups(employees, today=None):
    """Calculate distinct employee counts by tenure band."""
    employees = employees[
        employees["is_current"].astype(str).str.upper()
        .isin(["Y", "TRUE", "1"])
    ].copy()

    employees["valid_from"] = pd.to_datetime(
        employees["valid_from"], errors="coerce"
    )
    employees = employees[
        employees["employee_id"].notna()
        & employees["valid_from"].notna()
    ].copy()

    if today is None:
        today = pd.Timestamp.today().normalize()

    tenure_days = (today - employees["valid_from"]).dt.days
    employees["tenure_band"] = pd.cut(
        tenure_days,
        bins=[-float("inf"), 364, 1094, 1824, float("inf")],
        labels=["0-1 years", "1-3 years", "3-5 years", "5+ years"],
    )

    return employees.groupby("tenure_band", observed=False)[
        "employee_id"
    ].nunique()


def test_realistic_tenure_groups_pass():
    employees = pd.DataFrame({
        "employee_id": ["E1", "E2", "E3", "E4", "E5"],
        "is_current": ["Y"] * 5,
        "valid_from": [
            "2026-06-01", "2026-06-02", "2026-06-03",
            "2026-06-04", "2026-06-05",
        ],
    })
    counts = calculate_tenure_groups(
        employees, today=pd.Timestamp("2026-10-21")
    )
    assert counts["0-1 years"] == 5


def test_non_current_employees_are_excluded():
    employees = pd.DataFrame({
        "employee_id": ["E1", "E2"],
        "is_current": ["Y", "N"],
        "valid_from": ["2026-06-01", "2026-06-02"],
    })
    counts = calculate_tenure_groups(
        employees, today=pd.Timestamp("2026-10-21")
    )
    assert counts["0-1 years"] == 1


def test_missing_start_date_is_excluded():
    employees = pd.DataFrame({
        "employee_id": ["E1", "E2"],
        "is_current": ["Y", "Y"],
        "valid_from": ["2026-06-01", None],
    })
    counts = calculate_tenure_groups(
        employees, today=pd.Timestamp("2026-10-21")
    )
    assert counts["0-1 years"] == 1

def test_undersized_reporting_group_is_detected():
    employees = pd.DataFrame({
        "employee_id": ["E1", "E2", "E3"],
        "is_current": ["Y", "Y", "Y"],
        "valid_from": [
            "2026-06-01",
            "2026-06-02",
            "2026-06-03",
        ],
    })

    counts = calculate_tenure_groups(
        employees, today=pd.Timestamp("2026-10-21")
    )

    violations = counts[counts < 5]

    assert violations["0-1 years"] == 3

   
if __name__ == "__main__":
    test_realistic_tenure_groups_pass()
    test_non_current_employees_are_excluded()
    test_missing_start_date_is_excluded()
    test_undersized_reporting_group_is_detected()
    print("DQ-C14 integration-logic tests: 4 passed")