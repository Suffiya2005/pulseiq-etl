\# Task 1 — ETL Repeatability Evidence



\## Objective



Verify that the PulseIQ ETL pipeline can be run repeatedly and produces consistent row counts without accumulating duplicate records.



\## Execution



Command used from the `task1-etl` directory:



```powershell

python -m src.pipeline

```



The pipeline was executed twice on 20 October 2026.



\## Results



| Dataset | Input Rows | Run 1 Clean | Run 1 Rejected | Run 2 Clean | Run 2 Rejected |

|---|---:|---:|---:|---:|---:|

| Employees | 1,606 | 1,605 | 1 | 1,605 | 1 |

| Salary | 4 | 4 | 0 | 4 | 0 |

| Payroll | 7,344 | 7,344 | 0 | 7,344 | 0 |

| Attendance | 7,343 | 7,343 | 0 | 7,343 | 0 |

| Leave | 3,441 | 3,439 | 2 | 3,439 | 2 |

| \*\*Total\*\* | \*\*19,738\*\* | \*\*19,735\*\* | \*\*3\*\* | \*\*19,735\*\* | \*\*3\*\* |



\## Conclusion



Both executions completed successfully and reported identical input, clean, and rejected row counts. The run summary was saved to `logs/run\_summary.json`.



The pipeline's output counts are repeatable for the tested source data. This demonstrates consistent reruns; a separate comparison of output file contents or hashes would provide stronger evidence that the complete outputs are identical.



\## Evidence to Retain



\- Terminal output from the first execution.

\- Terminal output from the second execution.

\- `logs/run\_summary.json` from the latest execution.



