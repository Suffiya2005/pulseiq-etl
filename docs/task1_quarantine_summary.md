\# Task 1 — Quarantine Summary



\## 1. Row Count Summary



The following results were produced by the current ETL pipeline run.



| Dataset | Input Rows | Passed / Clean Rows | Quarantined Rows |

|---|---:|---:|---:|

| Employees | 1,606 | 1,605 | 1 |

| Salary | 4 | 4 | 0 |

| Payroll | 7,344 | 7,344 | 0 |

| Attendance | 7,343 | 7,343 | 0 |

| Leave | 3,441 | 3,439 | 2 |

| \*\*Total\*\* | \*\*19,738\*\* | \*\*19,735\*\* | \*\*3\*\* |



\## 2. Quarantine Reasons



| Dataset | Rejection Reason | Number of Rows |

|---|---|---:|

| Employees | `overlapping\_employee\_history` | 1 |

| Leave | `start\_date\_after\_end\_date` | 2 |

| Salary | No rejected rows | 0 |

| Payroll | No rejected rows | 0 |

| Attendance | No rejected rows | 0 |

| \*\*Total\*\* | | \*\*3\*\* |



\## 3. Handling Invalid Records



\- Invalid records are written to quarantine outputs instead of being silently discarded.

\- Each rejected record includes a rejection reason.

\- Raw source CSV files are preserved unchanged.

\- Exact duplicate rows are detected and rejected by the relevant pipeline cleaners.

\- Rejected records should be reviewed by the data owner before any correction to source data.



\## 4. Result



The pipeline processed 19,738 input rows. A total of 19,735 rows passed the current cleaning rules, and 3 rows were quarantined.



The counts represent the current pipeline run and should be rechecked after future changes to validation rules or source data.



