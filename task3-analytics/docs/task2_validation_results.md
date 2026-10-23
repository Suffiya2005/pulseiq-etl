# Task 2 — Warehouse Validation Results

## 1. Fact Table Reconciliation

| Fact Table | Clean Data Rows | Warehouse Rows | Status |
|---|---:|---:|---|
| Payroll | 7,342 | 7,342 | PASS |
| Attendance | 7,343 | 7,343 | PASS |
| Leave | 3,439 | 3,439 | PASS |

Two extra payroll records (`PI-X0003` and `PI-X0004`) were removed from the warehouse because they were not present in the clean payroll data.

## 2. Orphan Record Checks

| Fact Table | Orphan Rows | Status |
|---|---:|---|
| Payroll | 0 | PASS |
| Attendance | 0 | PASS |
| Leave | 0 | PASS |
| Headcount | 0 | PASS |

## 3. Dimension Table Counts

| Dimension | Rows |
|---|---:|
| `dim_date` | 2,557 |
| `dim_department` | 11 |
| `dim_employee` | 1,606 |
| `dim_leave_type` | 6 |
| `dim_role` | 58 |

## 4. Employee History Validation

- Employees with multiple current records: 0
- Invalid employee history date ranges: 0

## 5. Headcount Validation

- Total records: 891
- Duplicate month/department combinations: 0
- Orphan department references: 0

## 6. Anomaly Table Validation

- Total anomaly records: 405
- Missing required fields: 0
- Missing anomaly scores: 0
- Flagged records (`Y`): 405

| Source Dataset | Records |
|---|---:|
| `attendance_monthly_features` | 221 |
| `payroll_monthly_features` | 184 |
| **Total** | **405** |

## Summary

All checks listed above passed. The warehouse fact-table row counts match the clean payroll, attendance, and leave datasets, and the tested orphan-record checks returned zero rows.
## 7. Foreign Key Relationship Review

### Existing Foreign Keys Verified

- `fact_payroll.date_key` → `dim_date.date_key`
- `fact_payroll.employee_key` → `dim_employee.employee_key`
- `fact_payroll.department_id` → `dim_department.department_id`
- `fact_payroll.role_id` → `dim_role.role_id`
- `dim_employee.department_id` → `dim_department.department_id`
- `dim_employee.role_id` → `dim_role.role_id`
- `dim_role.department_id` → `dim_department.department_id`
- `fact_leave.leave_type_code` → `dim_leave_type.leave_type_code`

### Relationships Requiring Review

- `fact_attendance_monthly`: employee, date, and department references have zero orphan rows, but foreign key constraints are not currently enforced.
- `fact_headcount_monthly`: date and department references have zero orphan rows, but foreign key constraints are not currently enforced.
- `fact_leave`: employee and start/end date references have zero orphan rows; the leave-type foreign key exists.

**Note:** These checks verify referential data quality. Adding the missing constraints is a separate schema change and has not yet been performed.
## 8. Foreign Key Constraints — Final Verification

**Status: PASS**

The warehouse now has 13 foreign key constraints.

### Attendance
- `date_key` → `dim_date.date_key`
- `employee_key` → `dim_employee.employee_key`
- `department_id` → `dim_department.department_id`

### Headcount
- `date_key` → `dim_date.date_key`
- `department_id` → `dim_department.department_id`

All five newly added constraints were applied successfully and verified in PostgreSQL. The corresponding orphan checks returned zero rows before the constraints were added.

### Final Note
The payroll, attendance, and leave fact-table counts match their clean CSV datasets. The tested orphan checks, dimension validations, employee history checks, and anomaly data-quality checks passed.
## 9. Employee History Rule — SCD Type 2

If an employee moves from Sales to Support in July:

- June payroll belongs to Sales.
- July payroll belongs to Support.
- Each payroll record must join to `dim_employee` using `employee_key`, not just `employee_id`.
- The historical employee version effective for the payroll period determines the department.

This preserves accurate historical payroll reporting when employees change departments.
