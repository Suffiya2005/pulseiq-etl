# Task 1 ? Quarantine Summary

## 1. Row Count Summary

| Dataset | Input Rows | Passed / Clean Rows | Quarantined Rows |
|---|---:|---:|---:|
| Employees | 1,606 | 1,605 | 1 |
| Salary | 4 | 4 | 0 |
| Payroll | 7,344 | 7,342 | 2 |
| Attendance | 7,343 | 7,343 | 0 |
| Leave | 3,441 | 3,439 | 2 |
| **Total** | **19,738** | **19,733** | **5** |

## 2. Quarantine Reasons

| Dataset | Rejection Reason | Number of Rows |
|---|---|---:|
| Employees | `overlapping_employee_history` | 1 |
| Payroll | `invalid_employee_dimension_key` | 2 |
| Leave | `start_date_after_end_date` | 2 |
| Salary | No rejected rows | 0 |
| Attendance | No rejected rows | 0 |
| **Total** | | **5** |

## 3. Handling Invalid Records

- Invalid records are written to quarantine outputs instead of being silently discarded.
- Each rejected record includes a rejection reason.
- Raw source CSV files are preserved unchanged.
- Exact duplicate rows are detected and rejected by the relevant pipeline cleaners.
- Invalid payroll employee keys are quarantined rather than loaded as valid records.
- Rejected records should be reviewed by the data owner before any correction to source data.

## 4. Result

The pipeline processed 19,738 input rows. A total of 19,733 rows passed the cleaning rules, and 5 rows were quarantined.

The pipeline was run twice with consistent counts. Recheck these results after future changes to validation rules or source data.
