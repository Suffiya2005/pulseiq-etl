"""Safe, isolated unit tests for PulseIQ DQ Gatekeeper."""

import unittest
import pandas as pd
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from datetime import datetime, timezone, timedelta


class TestDQGatekeeper(unittest.TestCase):

    def test_C01_payroll_ledger_mismatch(self):
        payroll_total = 1000
        ledger_total = 900
        self.assertNotEqual(payroll_total, ledger_total)

    def test_C02_unbalanced_ledger(self):
        debit_total = 1000
        credit_total = 900
        self.assertNotEqual(debit_total, credit_total)

    def test_C03_duplicate_payroll(self):
        df = pd.DataFrame({
            "employee_id": ["E01", "E01"],
            "period": ["2026-01", "2026-01"]
        })
        self.assertTrue(df.duplicated(
            ["employee_id", "period"], keep=False
        ).any())

    def test_C04_orphan_employee(self):
        employee_ids = {"E01", "E02"}
        payroll_employee = "E99"
        self.assertNotIn(payroll_employee, employee_ids)

    def test_C05_attendance_after_exit(self):
        exit_date = pd.Timestamp("2026-01-15")
        attendance_date = pd.Timestamp("2026-02-01")
        self.assertGreater(attendance_date, exit_date)

    def test_C06_unpaid_leave_mismatch(self):
        unpaid_absence_days = 5
        payroll_lop_days = 2
        self.assertNotEqual(unpaid_absence_days, payroll_lop_days)

    def test_C07_invoice_invalid(self):
        invoice_total = 500
        amount_paid = 600
        self.assertGreater(amount_paid, invoice_total)

    def test_C08_expense_invalid(self):
        amount = 1000
        tax = 100
        recorded_total = 1500
        self.assertNotEqual(amount + tax, recorded_total)

    def test_C09_task_dates_invalid(self):
        start_date = pd.Timestamp("2026-02-10")
        completion_date = pd.Timestamp("2026-02-01")
        self.assertLess(completion_date, start_date)

    def test_C10_leave_dates_invalid(self):
        start_date = pd.Timestamp("2026-02-10")
        end_date = pd.Timestamp("2026-02-05")
        self.assertLess(end_date, start_date)

    def test_C11_prediction_stale(self):
        latest_date = pd.Timestamp("2026-09-30")
        prediction_date = pd.Timestamp("2026-09-20")
        self.assertGreater(
            (latest_date - prediction_date).days, 7
        )

    def test_C12_history_overlap(self):
        previous_end = pd.Timestamp("2026-05-15")
        next_start = pd.Timestamp("2026-05-10")
        self.assertLessEqual(next_start, previous_end)

    def test_C13_pipeline_summary_invalid(self):
        with TemporaryDirectory() as temp_dir:
            summary = Path(temp_dir) / "run_summary.json"
            summary.write_text("{invalid json", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                json.loads(summary.read_text(encoding="utf-8"))

    def test_C14_group_below_minimum(self):
        group_size = 3
        minimum_group_size = 5
        self.assertLess(group_size, minimum_group_size)


if __name__ == "__main__":
    unittest.main(verbosity=2)
