
-- ============================================================
-- TASK 13: Cross-Department Impact View
-- Grain: One row per department per month
-- Period: April 2025 - September 2026
-- IMPORTANT: Aggregate each fact table before joining.
-- ============================================================

-- 1. HEADCOUNT AGGREGATION
CREATE OR REPLACE VIEW warehouse.task13_headcount_dept_month AS
SELECT
    department_id,
    month_start_date AS month,
    SUM(headcount_start) AS headcount_start,
    SUM(headcount_end) AS headcount_end,
    SUM(hires) AS hires,
    SUM(exits) AS exits,
    SUM(voluntary_exits) AS voluntary_exits,
    AVG(attrition_rate_monthly_pct) AS attrition_rate_pct
FROM warehouse.fact_headcount_monthly
WHERE month_start_date BETWEEN DATE '2025-04-01' AND DATE '2026-09-01'
GROUP BY department_id, month_start_date;


-- 2. PAYROLL AGGREGATION
CREATE OR REPLACE VIEW warehouse.task13_payroll_dept_month AS
SELECT
    department_id,
    DATE_TRUNC('month', period_end_date)::DATE AS month,
    SUM(gross_pay) AS gross_pay,
    SUM(employer_cost) AS employer_cost,
    SUM(overtime_hours_paid) AS overtime_hours,
    SUM(overtime_pay) AS overtime_cost,
    COUNT(DISTINCT employee_id) AS payroll_employees
FROM warehouse.fact_payroll
WHERE period_end_date BETWEEN DATE '2025-04-01' AND DATE '2026-09-30'
GROUP BY department_id, DATE_TRUNC('month', period_end_date);



-- 3. ATTENDANCE AGGREGATION (recover department from employee dimension)
CREATE OR REPLACE VIEW warehouse.task13_attendance_dept_month AS
SELECT
    de.department_id,
    DATE_TRUNC('month', fa.period_end_date)::DATE AS month,
    SUM(fa.scheduled_days) AS scheduled_days,
    SUM(fa.present_days) AS present_days,
    SUM(fa.paid_leave_days) AS paid_leave_days,
    SUM(fa.unpaid_absence_days) AS unpaid_absence_days,
    SUM(fa.overtime_hours) AS attendance_overtime_hours,
    SUM(fa.late_arrivals) AS late_arrivals,
    COUNT(DISTINCT fa.employee_id) AS attendance_employees
FROM warehouse.fact_attendance_monthly fa
JOIN warehouse.dim_employee de
    ON fa.employee_key = de.employee_key
   AND fa.period_end_date >= de.valid_from
   AND (de.valid_to IS NULL OR fa.period_end_date <= de.valid_to)
WHERE fa.period_end_date BETWEEN DATE '2025-04-01' AND DATE '2026-09-30'
GROUP BY
    de.department_id,
    DATE_TRUNC('month', fa.period_end_date)::DATE;