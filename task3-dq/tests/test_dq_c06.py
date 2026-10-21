import unittest
import pandas as pd


def find_unpaid_leave_mismatches(attendance, payroll):
    """Apply the same comparison rule as DQ-C06."""
    matched = attendance.merge(
        payroll,
        on=["employee_id", "period_end_date"],
        how="inner",
    )
    return matched[
        matched["unpaid_absence_days"]
        > matched["lop_days"].fillna(0) + 0.5
    ]


class TestDQC06(unittest.TestCase):

    def test_clean_data_passes(self):
        attendance = pd.DataFrame({
            "employee_id": ["E01"],
            "period_end_date": ["2026-01-31"],
            "unpaid_absence_days": [2.0],
        })
        payroll = pd.DataFrame({
            "employee_id": ["E01"],
            "period_end_date": ["2026-01-31"],
            "lop_days": [2.0],
        })

        self.assertEqual(
            len(find_unpaid_leave_mismatches(attendance, payroll)), 0
        )

    def test_injected_mismatch_is_detected(self):
        attendance = pd.DataFrame({
            "employee_id": ["TEST-E01"],
            "period_end_date": ["2026-01-31"],
            "unpaid_absence_days": [5.0],
        })
        payroll = pd.DataFrame({
            "employee_id": ["TEST-E01"],
            "period_end_date": ["2026-01-31"],
            "lop_days": [2.0],
        })

        result = find_unpaid_leave_mismatches(attendance, payroll)

        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["employee_id"], "TEST-E01")


if __name__ == "__main__":
    unittest.main(verbosity=2)
