import csv
import unittest
from pathlib import Path
from decimal import Decimal

ROOT = Path(__file__).resolve().parent
COMPARISON = ROOT / "monthly_reconciliation_comparison.csv"
REPORT = ROOT / "task9_reconciliation_report.md"
DASHBOARD = ROOT / "task9_dashboard_test_evidence.md"


class TestTask9Evidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with COMPARISON.open(encoding="utf-8-sig", newline="") as f:
            cls.rows = list(csv.DictReader(f))
        cls.report = REPORT.read_text(encoding="utf-8-sig")
        cls.dashboard = DASHBOARD.read_text(encoding="utf-8-sig")

    def test_all_18_months_match_official_answer_key(self):
        self.assertEqual(len(self.rows), 18)
        self.assertTrue(all(r["status"] == "MATCH" for r in self.rows))

    def test_all_monthly_metric_differences_are_zero(self):
        difference_columns = [
            "difference_employees_paid",
            "difference_gross_pay",
            "difference_net_pay",
            "difference_employer_cost",
        ]
        for row in self.rows:
            for column in difference_columns:
                with self.subTest(month=row["month"], metric=column):
                    self.assertEqual(Decimal(row[column]), Decimal("0"))

    def test_june_2026_is_included_in_monthly_comparison(self):
        june = [r for r in self.rows if r["month"] == "2026-06"]
        self.assertEqual(len(june), 1)
        self.assertEqual(june[0]["status"], "MATCH")

    def test_ledger_exception_remains_documented(self):
        for expected in [
            "18,450.00",
            "DQ-04",
            "JE-002094",
            "JL-005614",
            "Finance sign-off: pending",
            "FINANCE EXCEPTION OPEN",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.report)

    def test_dashboard_evidence_keeps_finance_warning(self):
        self.assertIn("INR 18,450", self.dashboard)
        self.assertIn("pending Finance review", self.dashboard)
        self.assertIn("tests passed", self.dashboard)


if __name__ == "__main__":
    unittest.main(verbosity=2)
