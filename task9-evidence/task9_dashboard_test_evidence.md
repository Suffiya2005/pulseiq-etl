# Task 9 — Dashboard Interactive Test Evidence

## Test environment
- Application: PulseIQ Streamlit dashboard
- Page: Task 9 — Payroll Cost & Reconciliation

## Test 1 — Department filter
- Selected department: Customer Support
- Result: PASS
- Evidence: Screenshot showed updated KPI totals, monthly cost charts, and Customer Support rows only in the breakdown table.

## Test 2 — Month range filter
- Selected range: 2026-04-01 to 2026-09-01
- Selected department: Customer Support
- Result: PASS
- Evidence: Screenshot showed only 2026-04 through 2026-09 in the department/month breakdown table, and the KPI totals and chart updated to the filtered range.

## Privacy and exception checks
- Dashboard displays aggregate payroll totals and averages, not individual salary records.
- Finance warning remains visible after applying filters.
- June 2026 ledger discrepancy of INR 18,450 remains pending Finance review.
- No payroll or ledger source records were changed during testing.

## Overall result
Department and month-range interactive tests passed based on visual verification of the Streamlit dashboard.
