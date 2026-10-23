
# PulseIQ Warehouse Star Schema

## Dimension Tables

- `dim_date` — Date and month details
- `dim_employee` — Employee details and SCD Type 2 history
- `dim_department` — Department details
- `dim_role` — Job role details
- `dim_leave_type` — Leave category details

## Fact Tables

- `fact_payroll` — Payroll transaction details
- `fact_attendance_monthly` — Monthly attendance summaries
- `fact_leave` — Leave records
- `fact_headcount_monthly` — Monthly department headcount
- `fact_anomaly` — Flagged anomaly results

## Schema Diagram

```mermaid
flowchart TD
    DATE[dim_date]
    EMP[dim_employee]
    DEPT[dim_department]
    ROLE[dim_role]
    LEAVE_TYPE[dim_leave_type]

    PAYROLL[fact_payroll]
    ATTENDANCE[fact_attendance_monthly]
    LEAVE[fact_leave]
    HEADCOUNT[fact_headcount_monthly]
    ANOMALY[fact_anomaly]

    DATE --> PAYROLL
    EMP --> PAYROLL
    DATE --> ATTENDANCE
    EMP --> ATTENDANCE
    DEPT --> ATTENDANCE
    DATE --> LEAVE
    EMP --> LEAVE
    LEAVE_TYPE --> LEAVE
    DATE --> HEADCOUNT
    DEPT --> HEADCOUNT
```

**Note:** The diagram shows the intended analytical relationships. `fact_anomaly` is included in the warehouse, but its employee relationship should be documented separately if needed.
