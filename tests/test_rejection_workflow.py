
import pandas as pd
from src.pipeline import clean


def test_invalid_payroll_row_is_rejected():
    df = pd.DataFrame({
        "payroll_item_id": [1],
        "employee_id": ["E101"],
        "employee_key": [101],
        "period_end_date": ["2024-01-31"],
        "payable_days": [30],
        "lop_days": [0],
        "monthly_fixed_gross": [30000],
        "gross_pay": [-100],
        "total_deductions": [2000],
        "net_pay": [28000],
        "employer_cost": [32000],
    })

    valid, rejected = clean("payroll", df)

    assert len(valid) == 0
    assert len(rejected) == 1
    assert "negative_gross_pay" in rejected.iloc[0]["reject_reason"]


def test_valid_leave_row_is_kept():
    df = pd.DataFrame({
        "leave_request_id": [1],
        "employee_id": ["E101"],
        "employee_key": [101],
        "start_date": ["2024-02-01"],
        "end_date": ["2024-02-02"],
        "days": [2],
        "status": ["Approved"],
    })

    valid, rejected = clean("leave", df)

    assert len(valid) == 1
    assert len(rejected) == 0
