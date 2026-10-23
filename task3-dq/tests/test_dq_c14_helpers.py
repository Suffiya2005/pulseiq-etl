import importlib.util
from pathlib import Path

import pandas as pd
import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "dq_c14_helpers.py"
SPEC = importlib.util.spec_from_file_location("dq_c14_helpers", MODULE_PATH)
c14 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(c14)


def test_group_at_minimum_passes():
    counts = pd.Series({"D01": 5, "D02": 8})
    assert c14.find_undersized_groups(counts, 5).empty


def test_group_below_minimum_is_detected():
    counts = pd.Series({"D01": 5, "D02": 3})
    assert c14.find_undersized_groups(counts, 5).to_dict() == {"D02": 3}


def test_ten_employee_threshold():
    counts = pd.Series({"D01": 9, "D02": 10})
    assert c14.find_undersized_groups(counts, 10).to_dict() == {"D01": 9}


def test_distinct_employee_count():
    df = pd.DataFrame({
        "department_id": ["D01", "D01", "D01", "D02"],
        "employee_id": ["E1", "E1", "E2", "E3"],
    })
    counts = c14.count_distinct_employees_by_group(df, ["department_id"])
    assert counts.to_dict() == {"D01": 2, "D02": 1}


def test_task_count_uses_distinct_task_ids():
    df = pd.DataFrame({
        "team_id": ["T1", "T1", "T1"],
        "sprint_id": ["S1", "S1", "S1"],
        "task_id": ["A", "A", "B"],
    })
    counts = c14.count_tasks_by_group(df)
    assert counts[("T1", "S1")] == 2


def test_invalid_threshold_rejected():
    with pytest.raises(ValueError):
        c14.find_undersized_groups(pd.Series({"D01": 3}), 0)
def test_suppression_hides_undersized_groups():
    counts = pd.Series({"Small group": 4, "Valid group": 10})
    result = c14.suppress_undersized_groups(counts, minimum_size=5)

    assert pd.isna(result["Small group"])
    assert result["Valid group"] == 10
