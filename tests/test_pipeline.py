
import pandas as pd
from src.pipeline import clean


def test_valid_employee_is_kept():
    df = pd.DataFrame({
        "employee_key": [101],
        "employee_id": ["E101"],
        "full_name": ["  Asha Kumar  "],
        "hire_date": ["2024-01-10"],
        "employment_status": ["Active"],
        "is_current": ["Y"],
        "exit_date": [None],
    })

    clean_df, rejected = clean("employees", df)

    assert len(clean_df) == 1
    assert len(rejected) == 0
    assert clean_df.iloc[0]["full_name"] == "Asha Kumar"


def test_missing_employee_key_is_rejected():
    df = pd.DataFrame({
        "employee_key": [None],
        "employee_id": ["E101"],
        "full_name": ["Sample Employee"],
        "hire_date": ["2024-01-10"],
        "employment_status": ["Active"],
        "is_current": ["Y"],
    })

    clean_df, rejected = clean("employees", df)

    assert len(clean_df) == 0
    assert len(rejected) == 1
    assert "missing_or_invalid_employee_key" in rejected.iloc[0]["reject_reason"]


def test_duplicate_employee_key_is_rejected():
    df = pd.DataFrame({
        "employee_key": [101, 101],
        "employee_id": ["E101", "E101"],
        "full_name": ["First Employee", "Second Employee"],
        "hire_date": ["2024-01-10", "2024-02-10"],
        "employment_status": ["Active", "Active"],
        "is_current": ["N", "Y"],
    })

    clean_df, rejected = clean("employees", df)

    assert len(clean_df) == 0
    assert len(rejected) == 2
    assert rejected["reject_reason"].str.contains(
        "duplicate_employee_key"
    ).all()


def test_hire_date_after_exit_date_is_rejected():
    df = pd.DataFrame({
        "employee_key": [102],
        "employee_id": ["E102"],
        "full_name": ["Test Employee"],
        "hire_date": ["2025-02-01"],
        "exit_date": ["2025-01-01"],
        "employment_status": ["Exited"],
        "is_current": ["N"],
    })

    clean_df, rejected = clean("employees", df)

    assert len(clean_df) == 0
    assert len(rejected) == 1
    assert "hire_date_after_exit_date" in rejected.iloc[0]["reject_reason"]


def test_negative_payroll_is_rejected():
    df = pd.DataFrame({
        "payroll_item_id": [1],
        "employee_id": ["E101"],
        "employee_key": [101],
        "period_end_date": ["2024-01-31"],
        "payable_days": [30],
        "lop_days": [0],
        "monthly_fixed_gross": [-1000],
        "gross_pay": [-1000],
        "total_deductions": [0],
        "net_pay": [0],
        "employer_cost": [0],
    })

    clean_df, rejected = clean("payroll", df)

    assert len(clean_df) == 0
    assert len(rejected) == 1
    assert rejected["reject_reason"].str.contains("negative_").any()
