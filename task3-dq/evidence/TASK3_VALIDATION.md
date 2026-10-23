# PulseIQ HR Analytics — Task 3 Data Quality Gatekeeper

## 1. Objective

Implement an automated data quality gatekeeper with 14 checks to identify data-quality issues in warehouse data and generate a CSV report for audit and review.

## 2. Execution

**Command**
```powershell
python .\task3-dq\dq_gatekeeper.py
```

**Generated report:** `task3-dq/dq_report.csv`  
**Evidence copy:** `task3-dq/evidence/dq_report_final.csv`

| Summary | Latest result |
|---|---:|
| Checks executed | 14 |
| PASS | 4 |
| FAIL | 10 |
| Automated tests | 54 passed |
| DQ-C03 duplicate payroll findings | 0 |
| DQ-C14 undersized-group violations | 1162 |

## 3. Check Results

| Check | Result | Interpretation |
|---|---|---|
| DQ-C01 Payroll equals ledger | FAIL — 1 | DQ-04: June 2026 ledger salary expense exceeds payroll by INR 18,450. |
| DQ-C02 Ledger balanced | PASS — 0 | No ledger imbalance detected. |
| DQ-C03 Unique payroll rows | PASS — 0 | No duplicate `payroll_item_id` records detected by the current check. |
| DQ-C04 No orphan employees | FAIL — 2 | DQ-03: PI-X0003 and PI-X0004 reference missing employees. |
| DQ-C05 No attendance after exit | FAIL — 4 | DQ-01: FA-X0001 through FA-X0004. |
| DQ-C06 Unpaid leave deducted | PASS — 0 | No violations detected by the check. |
| DQ-C07 Invoice arithmetic | FAIL — 1 | DQ-05: INV-00385 is overpaid by INR 100. |
| DQ-C08 Expense arithmetic | FAIL — 1 | DQ-10: EXP-00371 total is overstated by INR 500. |
| DQ-C09 Task dates sensible | FAIL — 20 | DQ-06/DQ-07: invalid task date sequences and Done tasks without completion dates. |
| DQ-C10 Leave dates sensible | FAIL — 2 | DQ-08: LR-002286 and LR-000025 have end dates before start dates. |
| DQ-C11 AI feeds are fresh | FAIL — 5 | DQ-09: five stale attrition predictions. |
| DQ-C12 Dimension history does not overlap | FAIL — 1 | DQ-11: overlapping employee history for EMP-0001. |
| DQ-C13 Pipeline freshness | PASS — 0 | The latest successful pipeline run is within 24 hours. |
| DQ-C14 Minimum group size | FAIL — 1162 | Reporting groups below their configured minimum require suppression or investigation. |

## 4. Severity Policy

**Critical checks:** DQ-C01, DQ-C02, DQ-C03, DQ-C04, DQ-C12 and DQ-C13.

**Warning checks:** DQ-C05, DQ-C06, DQ-C07, DQ-C08, DQ-C09, DQ-C10, DQ-C11 and DQ-C14.

Critical failures should block the affected load or publication when they threaten financial integrity, referential integrity, uniqueness, warehouse correctness or freshness. Warning failures should be logged, investigated and communicated to the responsible owner. DQ-C14 violations must also be suppressed in reporting outputs wherever required by the applicable privacy or minimum-group-size policy.

## 5. Planted-Issues Comparison

The reference catalogue documents 11 planted issues. The latest check report has findings consistent with the documented cases, but individual detection should be confirmed against the affected record IDs.

| Planted issue | Related check | Assessment |
|---|---|---|
| DQ-01 Attendance after exit | DQ-C05 | Finding detected; verify affected IDs. |
| DQ-02 Duplicate payroll rows | DQ-C03 | No duplicates in the latest report; confirm whether ETL cleanup removed the planted duplicate before validation. |
| DQ-03 Missing employee references | DQ-C04 | Two findings reported. |
| DQ-04 Payroll-ledger mismatch | DQ-C01 | One finding reported. |
| DQ-05 Invoice arithmetic | DQ-C07 | One finding reported. |
| DQ-06 Task completed before start | DQ-C09 | Included in task-date findings; verify record IDs. |
| DQ-07 Done task without completion date | DQ-C09 | Included in task-date findings; verify record IDs. |
| DQ-08 Invalid leave date order | DQ-C10 | Two findings reported. |
| DQ-09 Stale risk predictions | DQ-C11 | Five findings reported. |
| DQ-10 Expense arithmetic | DQ-C08 | One finding reported. |
| DQ-11 Employee history overlap | DQ-C12 | One finding reported. |

**Validation note:** A check result alone does not prove that every planted record was detected. The planted-issues review should compare record IDs and document any missed issue and its reason. DQ-C03 should also be tested against a deliberately duplicated payroll item in a test copy.

## 6. C14 Threshold and Suppression Review

The latest Gatekeeper result reports **1162 minimum-group-size violations**. This is an audit finding and must not be changed to PASS merely to obtain a clean report.

The metric dictionary contains different minimum thresholds, including 5 and 10 for certain metrics. The implementation must apply each metric's configured minimum rather than a single hard-coded threshold.

The Superset dashboard has a preliminary headcount suppression chart. Full compliance is not yet established because the other existing dashboard charts have not all been confirmed as using appropriately suppressed data. Small-group values must be hidden wherever the applicable policy requires suppression.

## 7. Additional Limitations

- DQ-C11 checks prediction `as_of_date` freshness. The workbook does not contain a `scored_at` column, so the separate 24-hour scoring freshness rule is not independently validated.
- DQ-C03 currently reports zero duplicate payroll items. This does not establish that the original planted duplicate was caught by the Gatekeeper if ETL removed it before the check ran.
- DQ-C14 requires metric-specific threshold verification and dashboard suppression verification.

## 8. Evidence Files

- `task3-dq/dq_report.csv`
- `task3-dq/evidence/dq_report_final.csv`
- `task3-dq/evidence/TASK3_VALIDATION.md`
- Automated test suite: 54 tests passed

The evidence CSV should be refreshed from the latest generated report after the final Gatekeeper run.

## 9. Final Status

**Task 3 implementation:** Automated checks and report generation are implemented; the test suite has passed.

**Latest data-quality outcome:** 4 PASS and 10 FAIL.

**Remaining evidence and compliance work:** Confirm the evidence CSV matches the latest report, verify the 11 planted issues against record IDs, ensure metric-specific C14 thresholds are applied, and confirm that relevant Superset charts suppress undersized groups.

Task 3 should be described as implementation-complete with validation findings outstanding until these final evidence checks are confirmed.
