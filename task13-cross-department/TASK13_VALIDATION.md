# Task 13 – Cross-Department Impact Analysis

## Official PQ-13 Reference Validation

### Coverage
- Reference dataset: unlock_PQ-13_reference_summary_dept_month.csv
- Total compared department-month records: 198
- Departments covered: 11
- Months covered: 18

### Validation Results

| Metric | Result |
|---|---:|
| Gross pay mismatches | 2 |
| Employer cost mismatches | 2 |
| Overtime mismatches | 0 |

### Identified Data Quality Issues

| Department | Month | Duplicate Employee | Gross Pay Difference | Employer Cost Difference |
|---|---|---|---:|---:|
| D02 – Product & Design | February 2026 | EMP-0194 | 153011.89 | 154811.89 |
| D08 – Finance & Accounts | May 2025 | EMP-0598 | 60013.15 | 61813.15 |

### Root Cause
Source-level investigation of warehouse.fact_payroll identified duplicate payroll records for the above employees and department-month periods. These duplicate records explain the exact differences against the official PQ-13 reference.

### Data Integrity
- Original payroll source records were preserved.
- No payroll records were deleted or modified.
- Differences were documented as data quality findings.
- Overtime cost reconciliation matched the official reference across all 198 records.

### Evidence
- actual_task13.csv – Actual Task 13 department-month data.
- pq13_mismatch_evidence.csv – Official PQ-13 mismatch evidence.
- task13-cross-department.sql – Task 13 SQL implementation.

### Conclusion
Task 13 cross-department analysis and official PQ-13 reference validation are completed. The two payroll discrepancies are explained by duplicate source records and documented for data quality follow-up.
