\# Task 3 — Data Quality Gatekeeper Test Plan



\## Purpose

Prove that each of the 14 data quality checks detects a deliberately introduced defect. Tests must run against disposable test data, never against the working warehouse or reference workbook.



\## Test cases



| Test ID | Check ID | Deliberately bad test data | Expected result |

|---|---|---|---|

| T01 | DQ-C01 | Payroll monthly total differs from salary-related ledger debits | FAIL; mismatch returned |

| T02 | DQ-C02 | One ledger entry has unequal debit and credit totals | FAIL; unbalanced entry returned |

| T03 | DQ-C03 | Duplicate an employee's payroll row for the same period | FAIL; duplicate group returned |

| T04 | DQ-C04 | Add a payroll row with a nonexistent employee ID | FAIL; orphan payroll row returned |

| T05 | DQ-C05 | Add attendance after the employee's exit month | FAIL; invalid attendance returned |

| T06 | DQ-C06 | Make unpaid absence days exceed payroll LOP days by more than the tolerance | FAIL; discrepancy returned |

| T07 | DQ-C07 | Make an invoice's amount paid exceed its total or its balance negative | FAIL; invalid invoice returned |

| T08 | DQ-C08 | Make expense amount plus tax differ from its total | FAIL; invalid expense returned |

| T09 | DQ-C09 | Set task completion before its start, or mark Done without a completion date | FAIL; invalid task returned |

| T10 | DQ-C10 | Set a leave end date before its start date | FAIL; invalid leave returned |

| T11 | DQ-C11 | Insert a prediction date older than the latest date by more than seven days | FAIL; stale prediction returned |

| T12 | DQ-C12 | Create overlapping validity periods for the same employee history | FAIL; overlapping history returned |

| T13 | DQ-C13 | Remove or invalidate the pipeline run summary in a disposable test folder | FAIL; freshness error returned |

| T14 | DQ-C14 | Create a reporting group smaller than the configured minimum | FAIL; undersized group returned |



\## Test execution rules

1\. Use isolated test tables, a disposable schema/database, or copied input files.

2\. Never insert test defects into the main warehouse or official reference workbook.

3\. Record the test ID, check ID, injected defect, actual result, expected result, and PASS/FAIL outcome.

4\. A test passes only when the intended check detects the injected defect.

5\. Also run a clean-data control test where practical, to ensure valid data does not trigger a false failure.

6\. Do not mark a test as passed until it has actually been executed and its output recorded.



\## Evidence

Save execution results in `task3-dq/tests/` and document any checks that fail to detect their intended defect.



