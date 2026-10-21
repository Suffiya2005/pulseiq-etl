\# Task 3 — Planted Issues Validation Report



\## 1. Purpose



Compare the Data Quality Gatekeeper report against the 11 expected planted data-quality issues. Record each result only when supported by the current report, a verification query, or an executed test.



\## 2. Planted-Issue Validation Results



| Check | Expected issue | Available evidence | Status |

|---|---|---|---|

| DQ-C01 | June 2026 payroll/ledger mismatch | June difference: -18,450.00; included in three reported monthly mismatches | CAUGHT |

| DQ-C03 | Duplicate payroll rows | Gatekeeper report shows 2 duplicate groups | DETECTED; exact planted records still need confirmation |

| DQ-C04 | Orphan payroll employees | Orphan IDs PI-X0003 and PI-X0004 | CAUGHT |

| DQ-C05 | Attendance after exit | Invalid records FA-X0001 to FA-X0004 | CAUGHT |

| DQ-C07 | Invoice arithmetic | Gatekeeper report shows 1 problematic row | DETECTED; exact planted record still needs confirmation |

| DQ-C08 | Expense arithmetic | Gatekeeper report shows 1 problematic row | DETECTED; exact planted record still needs confirmation |

| DQ-C09 | Invalid task dates | Gatekeeper report shows 20 problematic rows | DETECTED; exact planted records still need confirmation |

| DQ-C10 | Invalid leave dates | Invalid leave IDs LR-000025 and LR-002286 | CAUGHT |

| DQ-C11 | Stale AI predictions | Gatekeeper report shows 5 problematic rows | DETECTED; exact planted IDs still need confirmation |

| DQ-C12 | Overlapping employee history | Overlap reported for EMP-0001 | CAUGHT |

| DQ-C03 | Duplicate payroll rows | Duplicate groups include PI-X0001 and PI-X0002 | CAUGHT |

| DQ-C07 | Invoice arithmetic | INV-00385: amount paid exceeds total by 100 | CAUGHT |

| DQ-C08 | Expense arithmetic | EXP-00371: total differs from expected amount by 500 | CAUGHT |

| DQ-C09 | Invalid task dates | 20 problematic rows, including completion-before-start and missing completion dates | CAUGHT |

| DQ-C11 | Stale AI predictions | AR-0119, AR-0221, AR-0238, AR-0278 and AR-0279 | CAUGHT |

| DQ-C12 | Overlapping employee history | Workbook records for EMP-0001: keys 100000 and 100001 overlap from 2012-05-03 to 2012-05-12 | CAUGHT |



\*\*Important:\*\* These results do not establish that all 11 expected planted issues have been individually verified. Do not claim 11/11 caught until each planted issue is matched to its expected record and check.



\## 3. June 2026 Payroll Reconciliation



The read-only reconciliation query returned three mismatched months.



| Month | Payroll cost | Ledger debits | Difference |

|---|---:|---:|---:|

| May 2025 | 40,717,628.17 | 40,655,815.02 | 61,813.15 |

| February 2026 | 44,198,850.60 | 44,044,038.71 | 154,811.89 |

| June 2026 | 54,664,233.35 | 54,682,683.35 | -18,450.00 |



DQ-C01 reported three mismatched monthly rows. June 2026 was included, confirming that the planted payroll/ledger mismatch was caught. The negative difference means ledger debits exceeded payroll cost by 18,450.00.



\## 4. Other Check Results and Limitations



\- \*\*DQ-C02 — Ledger balanced:\*\* Reported PASS with zero problematic rows. An unbalanced-ledger planted defect has not been confirmed.

\- \*\*DQ-C06 — Unpaid leave deducted:\*\* The current database query and official workbook comparison found zero violations across 7,341 matched employee-month rows. Two isolated sample tests passed: clean data produced no mismatch, and an injected mismatch was detected. This validates the comparison rule, but does not prove that the full database-based check catches a planted defect. No specific DQ-C06 planted issue has been confirmed.

\- \*\*DQ-C13 — Pipeline freshness:\*\* Reported PASS. Six tests of the actual `check\_pipeline\_freshness()` function passed using temporary files and a temporary root directory. The tests covered a missing summary, missing finish time, invalid JSON, a recent run, an old run, and a future timestamp.

\-- \*\*DQ-C14 — Minimum group size:\*\* The current gatekeeper checks that configured `minimum\_group\_size` thresholds are positive for 16 metrics. Three isolated sample tests passed: groups above the threshold pass, groups below it are detected, and groups exactly at the threshold pass. However, this sample rule is not integrated into the gatekeeper, and actual reporting-group counts have not been checked. \*\*Status: PARTIALLY TESTED; INTEGRATION PENDING.\*\*



\## 5. Test Evidence



The preliminary test suite ran 14 tests successfully. These tests check sample defect conditions; they do not prove that all 14 actual gatekeeper checks detect their intended defects.



The separate DQ-C06 sample test ran 2 tests successfully:

\- Clean data produced no mismatch.

\- An injected unpaid-leave mismatch was detected.



The DQ-C13 real-function test ran 6 tests successfully.



\- The DQ-C14 isolated sample test ran 3 tests successfully. Results are saved in `task3-dq/tests/dq\_c14\_test\_results.txt`. These tests do not validate the full gatekeeper implementation.



\## 6. Remaining Actions



1\. Verify the exact planted records for duplicate payroll, invoice arithmetic, expense arithmetic, task dates, stale predictions, and history overlap.

2\. Confirm whether an unbalanced-ledger defect was included in the planted-issue set.

3\. Confirm whether a specific unpaid-leave discrepancy was planted. If so, test it in isolated data.

4\. Implement and test DQ-C14 against actual reporting-group counts and configured minimum thresholds.

5\. Continue testing with isolated data; do not inject defects into the working warehouse or official reference workbook.

6\. Record any missed issues honestly. A check returning FAIL does not prove it caught a particular planted defect unless the expected record is identified.



\## 7. Evidence Files



\- `task3-dq/dq\_report.csv`

\- `task3-dq/tests/preliminary\_test\_results.txt`

\- `task3-dq/tests/pipeline\_freshness\_results.txt`

\- `task3-dq/tests/dq\_c06\_test\_results.txt`

\- `task3-dq/tests/DQ\_TEST\_PLAN.md`

\- `task3-dq/tests/PLANTED\_ISSUES\_VALIDATION.md`





