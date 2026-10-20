\# Task 1 — ETL Count Summary



\## Execution



\*\*Command used:\*\* Load the raw CSV files into DuckDB, then run the ETL validation pipeline.



\*\*Execution date:\*\* 20 October 2026



\## Dataset Counts



| Dataset | Rows In | Rows Passed | Rows Quarantined |

|---|---:|---:|---:|

| Employees | 1,606 | 1,605 | 1 |

| Salary | 4 | 4 | 0 |

| Payroll | 7,344 | 7,344 | 0 |

| Attendance | 7,343 | 7,343 | 0 |

| Leave | 3,441 | 3,439 | 2 |

| \*\*Total\*\* | \*\*19,738\*\* | \*\*19,735\*\* | \*\*3\*\* |



\## Count Reconciliation



For every dataset:



\*\*Rows In = Rows Passed + Rows Quarantined\*\*



The counts balance for all five datasets.



\- Total input: 19,738 rows

\- Total passed: 19,735 rows

\- Total quarantined: 3 rows



\## Quarantine Reasons



| Dataset | Reason | Rows |

|---|---|---:|

| Employees | `overlapping\_employee\_history` | 1 |

| Leave | `start\_date\_after\_end\_date` | 2 |

| \*\*Total\*\* | | \*\*3\*\* |



\## Output Locations



\- DuckDB database: `data/pulseiq\_task1.duckdb`

\- Clean CSV and Parquet outputs: `data/clean/`

\- Quarantine CSV outputs: `rejected/`

\- ETL summary JSON: `logs/run\_summary.json`



\## Result



The combined DuckDB-loading and ETL-validation command completed successfully. All five datasets were processed, and three invalid records were quarantined with recorded reasons. The raw source CSV files were not intentionally modified by the pipeline.



This report documents the observed execution results. The terminal output and `run\_summary.json` provide supporting evidence.



