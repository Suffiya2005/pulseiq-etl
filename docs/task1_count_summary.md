# Task 1 ? ETL Count Summary

## Execution

**Command used:** `python run_task1.py`

**Execution date:** 20 October 2026

## Dataset Counts

| Dataset | Rows In | Rows Passed | Rows Quarantined |
|---|---:|---:|---:|
| Employees | 1,606 | 1,605 | 1 |
| Salary | 4 | 4 | 0 |
| Payroll | 7,344 | 7,342 | 2 |
| Attendance | 7,343 | 7,343 | 0 |
| Leave | 3,441 | 3,439 | 2 |
| **Total** | **19,738** | **19,733** | **5** |

## Count Reconciliation

For every dataset:

**Rows In = Rows Passed + Rows Quarantined**

- Total input: 19,738 rows
- Total passed: 19,733 rows
- Total quarantined: 5 rows

## Quarantine Reasons

| Dataset | Reason | Rows |
|---|---|---:|
| Employees | `overlapping_employee_history` | 1 |
| Payroll | `invalid_employee_dimension_key` | 2 |
| Leave | `start_date_after_end_date` | 2 |
| **Total** | | **5** |

## Output Locations

- DuckDB database: `data/pulseiq_task1.duckdb`
- Clean CSV and Parquet outputs: `data/clean/`
- Quarantine CSV outputs: `rejected/`
- ETL summary JSON: `logs/run_summary.json`

## Result

The combined contract-validation, DuckDB-loading, and ETL pipeline completed successfully. All five datasets were processed. Five invalid records were quarantined with recorded reasons. The pipeline was run twice with consistent results, and all 15 automated tests passed. The raw source CSV files were not intentionally modified by the pipeline.
