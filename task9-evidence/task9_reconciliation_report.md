# Task 9 — Payroll Reconciliation and Exceptions

## 1. Payroll reconciliation
- Official answer-key months: 18
- Months compared: 18
- Matching payroll months: 18
- Mismatching payroll months against the official answer key: 0
- Reporting exclusions: duplicate payroll records PI-X0001 and PI-X0002
- ETL rejections: orphan records PI-X0003 and PI-X0004

The monthly payroll totals match the official answer key after the documented reporting exclusions. This result is separate from the ledger reconciliation exception described below.

## 2. Privacy and dashboard validation
- Leadership department D00 excluded from the department dashboard.
- Dashboard covers 10 departments over 18 months.
- No department/month group has fewer than 5 distinct paid employees, according to the existing validation evidence.
- Dashboard contains aggregate metrics only.
- Department and month filters were tested.
- No individual salary is displayed.

## 3. June 2026 ledger exception

### Verified overall variance
- Official payroll employer cost: INR 54,664,233.35
- Ledger payroll-related expense: INR 54,682,683.35
- Ledger expense above payroll: INR 18,450.00
- Source issue: DQ-04
- Journal entry: JE-002094
- Journal balances, but payroll-to-ledger reconciliation fails.

### Component-level investigation — department D01
- Payroll earned_fixed_pay: INR 19,873,074.18
- Account 5001 Salaries & Wages, line JL-005614: INR 19,891,524.18
- Salary posting excess over earned_fixed_pay: INR 18,450.00
- Payroll variable_pay: INR 10,000.00
- Account 5003 Incentives & Bonus, line JL-005615: INR 10,000.00
- Payroll employer PF: INR 260,158.00
- Account 5004 Employer PF Contribution, line JL-005616: INR 260,158.00

The bonus and employer PF postings match their respective payroll components. The D01 salary expense posting exceeds earned_fixed_pay by INR 18,450. The source workbook's DQ-04 entry identifies the June payroll-ledger mismatch and references JL-005614 and JL-005643.

### Root-cause disposition
- Technical variance: confirmed.
- Discrepant component: D01 Salaries & Wages ledger posting, JL-005614.
- Source-data issue: documented in DQ-04.
- Accounting reason for the excess: not independently established from available evidence.
- Approved correcting entry: not provided.
- Finance sign-off: pending.

The investigation isolates the discrepancy to the salary expense posting, but does not establish the business reason for the posted amount or authorize a correcting journal entry.

## 4. Data integrity and audit trail
- No payroll source records were changed.
- No ledger source records were changed.
- No balancing or correcting journal entry was invented.
- The INR 18,450 exception must remain visible until Finance approves its disposition.
- Any accounting correction must follow the approved accounting process and preserve the audit trail.

## 5. Final Task 9 status
- Dashboard implementation and existing dashboard test evidence: completed.
- Payroll answer-key comparison: passed for all 18 months.
- June ledger reconciliation: exception identified and technically investigated.
- Technical root-cause isolation: completed to the discrepant ledger component.
- Accounting cause confirmation and Finance sign-off: pending.

Overall status: TECHNICAL WORK COMPLETED; FINANCE EXCEPTION OPEN.

## Finance action required
Finance should review JE-002094 and the supporting payroll run PR-2026-06, confirm why JL-005614 exceeds D01 earned_fixed_pay by INR 18,450, and document an approved correction or accepted exception. The reconciliation should be rerun after the authorized disposition.
