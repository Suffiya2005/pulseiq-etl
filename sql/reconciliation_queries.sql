
-- Query 1: Payroll row count and gross pay
SELECT
    COUNT(*) AS payroll_rows,
    COUNT(DISTINCT employee_id) AS unique_employees,
    ROUND(SUM(gross_pay)::numeric, 2) AS total_gross_pay
FROM warehouse.fact_payroll;

-- Query 2: Attendance row count and average attendance rate
SELECT
    COUNT(*) AS attendance_rows,
    ROUND(AVG(attendance_rate)::numeric, 4) AS avg_attendance_rate
FROM warehouse.fact_attendance_monthly;

-- Query 3: Leave row count and total leave days
SELECT
    COUNT(*) AS leave_rows,
    ROUND(SUM(days)::numeric, 2) AS total_leave_days
FROM warehouse.fact_leave;
