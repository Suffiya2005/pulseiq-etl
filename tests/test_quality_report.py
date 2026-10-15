import pandas as pd

from src.quality_report import DATASETS


def test_quality_report_dataset_list():
    assert DATASETS == [
        "employees",
        "salary",
        "attendance",
        "leave",
        "payroll",
    ]


def test_employee_leaving_dates_are_counted():
    df = pd.DataFrame({
        "employee_id": ["E001", "E002", "E003"],
        "leaving_date": [None, None, "2025-12-31"],
    })

    missing_leaving_dates = int(df["leaving_date"].isna().sum())

    assert missing_leaving_dates == 2