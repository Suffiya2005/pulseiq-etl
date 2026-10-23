import pandas as pd


MINIMUM_GROUP_SIZE = 5


def find_undersized_groups(group_counts, minimum_size=MINIMUM_GROUP_SIZE):
    """Return reporting groups below the configured minimum."""
    return group_counts[group_counts < minimum_size]


def calculate_tenure_groups(employees, today=None):
    """Count current employees by tenure band."""
    employees = employees.copy()

    employees = employees[
        employees["is_current"].astype(str).str.upper().isin(
            ["Y", "TRUE", "1"]
        )
    ]

    employees["valid_from"] = pd.to_datetime(
        employees["valid_from"], errors="coerce"
    )

    employees = employees.dropna(
        subset=["employee_id", "valid_from"]
    )

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


def test_tenure_groups_meet_minimum():
    counts = pd.Series({
        "0-1 years": 207,
        "1-3 years": 250,
        "3-5 years": 154,
        "5+ years": 134,
    })

    assert find_undersized_groups(counts).empty


def test_undersized_tenure_group_is_detected():
    counts = pd.Series({
        "0-1 years": 207,
        "Small group": 3,
    })

    violations = find_undersized_groups(counts)

    assert violations.to_dict() == {"Small group": 3}


def test_department_headcount_meets_minimum():
    counts = pd.Series({
        "D01": 167,
        "D02": 26,
        "D03": 52,
        "D04": 46,
        "D05": 13,
        "D06": 59,
        "D07": 20,
        "D08": 17,
        "D09": 29,
        "D10": 11,
    })

    assert find_undersized_groups(counts).empty


def test_department_headcount_detects_small_group():
    counts = pd.Series({
        "Engineering": 167,
        "Small Department": 3,
    })

    violations = find_undersized_groups(counts)

    assert violations.to_dict() == {"Small Department": 3}


if __name__ == "__main__":
    test_tenure_groups_meet_minimum()
    test_undersized_tenure_group_is_detected()
    test_department_headcount_meets_minimum()
    test_department_headcount_detects_small_group()

    print("DQ-C14 reporting tests: 4 passed")