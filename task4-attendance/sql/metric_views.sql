-- Official Task 4 governed metric layer generated from the workbook dictionary.

-- M26 returns NULL where the available anomaly source contains flagged records only.

CREATE SCHEMA IF NOT EXISTS warehouse;

DROP VIEW IF EXISTS warehouse.metric_catalog,
    warehouse.metric_headcount,
    warehouse.metric_average_salary,
    warehouse.metric_attendance_rate,
    warehouse.metric_leave_days,
    warehouse.metric_total_net_payroll,
    warehouse.metric_attrition_rate,
    warehouse.metric_revenue,
    warehouse.metric_net_profit,
    warehouse.metric_forecast_error_mape,
    warehouse.metric_m01_headcount,
    warehouse.metric_m02_hires,
    warehouse.metric_m03_exits,
    warehouse.metric_m04_monthly_attrition_rate,
    warehouse.metric_m05_attrition_rate_rolling_12m,
    warehouse.metric_m06_voluntary_attrition_rate,
    warehouse.metric_m07_gross_pay,
    warehouse.metric_m08_net_pay,
    warehouse.metric_m09_payroll_cost,
    warehouse.metric_m10_cost_per_head,
    warehouse.metric_m11_overtime_share,
    warehouse.metric_m12_variable_pay_share,
    warehouse.metric_m13_attendance_rate,
    warehouse.metric_m14_late_arrival_rate,
    warehouse.metric_m15_leave_without_pay_days,
    warehouse.metric_m16_revenue,
    warehouse.metric_m17_net_profit,
    warehouse.metric_m18_operating_margin,
    warehouse.metric_m19_payroll_as_revenue_pct,
    warehouse.metric_m20_days_sales_outstanding,
    warehouse.metric_m21_overdue_receivables,
    warehouse.metric_m22_task_completion_rate,
    warehouse.metric_m23_on_time_delivery_rate,
    warehouse.metric_m24_velocity,
    warehouse.metric_m25_average_cycle_time,
    warehouse.metric_m26_anomaly_flag_rate,
    warehouse.metric_m27_high_risk_share,
    warehouse.metric_m28_forecast_error_mape;

CREATE VIEW warehouse.metric_m01_headcount AS
SELECT month_start_date, department_id,
       headcount_end AS headcount
FROM warehouse.fact_headcount_monthly
WHERE headcount_end >= 5;

CREATE VIEW warehouse.metric_m02_hires AS
SELECT month_start_date, department_id, hires
FROM warehouse.fact_headcount_monthly
WHERE headcount_end >= 5;

CREATE VIEW warehouse.metric_m03_exits AS
SELECT month_start_date, department_id, exits
FROM warehouse.fact_headcount_monthly
WHERE headcount_start >= 5;

CREATE VIEW warehouse.metric_m04_monthly_attrition_rate AS
SELECT month_start_date, department_id, headcount_start, exits,
       ROUND(100.0 * exits / NULLIF(headcount_start, 0), 4)
           AS attrition_rate_monthly_pct
FROM warehouse.fact_headcount_monthly
WHERE headcount_start >= 10
  AND headcount_start > 0;

CREATE VIEW warehouse.metric_m05_attrition_rate_rolling_12m AS
WITH rolling AS (
    SELECT month_start_date, department_id,
           SUM(exits) OVER w AS exits_12m,
           AVG(headcount_end::NUMERIC) OVER w AS avg_headcount_12m,
           COUNT(*) OVER w AS months_in_window
    FROM warehouse.fact_headcount_monthly
    WINDOW w AS (
        PARTITION BY department_id
        ORDER BY month_start_date
        ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
    )
)
SELECT month_start_date, department_id, exits_12m, avg_headcount_12m,
       ROUND(100.0 * exits_12m / NULLIF(avg_headcount_12m, 0), 4)
           AS attrition_rate_rolling_12m_pct
FROM rolling
WHERE months_in_window = 12
  AND avg_headcount_12m >= 10;

CREATE VIEW warehouse.metric_m06_voluntary_attrition_rate AS
WITH rolling AS (
    SELECT month_start_date, department_id,
           SUM(voluntary_exits) OVER w AS voluntary_exits_12m,
           AVG(headcount_end::NUMERIC) OVER w AS avg_headcount_12m,
           COUNT(*) OVER w AS months_in_window
    FROM warehouse.fact_headcount_monthly
    WINDOW w AS (
        PARTITION BY department_id
        ORDER BY month_start_date
        ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
    )
)
SELECT month_start_date, department_id, voluntary_exits_12m,
       avg_headcount_12m,
       ROUND(
           100.0 * voluntary_exits_12m / NULLIF(avg_headcount_12m, 0), 4
       ) AS voluntary_attrition_rate_pct
FROM rolling
WHERE months_in_window = 12
  AND avg_headcount_12m >= 10;

CREATE VIEW warehouse.metric_m07_gross_pay AS
SELECT p.period_end_date, de.department_id,
       SUM(p.gross_pay) AS gross_pay
FROM warehouse.fact_payroll p
JOIN warehouse.dim_employee de ON p.employee_key = de.employee_key
GROUP BY p.period_end_date, de.department_id
HAVING COUNT(DISTINCT p.employee_id) >= 5;

CREATE VIEW warehouse.metric_m08_net_pay AS
SELECT p.period_end_date, de.department_id,
       SUM(p.net_pay) AS net_pay
FROM warehouse.fact_payroll p
JOIN warehouse.dim_employee de ON p.employee_key = de.employee_key
GROUP BY p.period_end_date, de.department_id
HAVING COUNT(DISTINCT p.employee_id) >= 5;

CREATE VIEW warehouse.metric_m09_payroll_cost AS
SELECT p.period_end_date, de.department_id,
       SUM(p.employer_cost) AS payroll_cost
FROM warehouse.fact_payroll p
JOIN warehouse.dim_employee de ON p.employee_key = de.employee_key
GROUP BY p.period_end_date, de.department_id
HAVING COUNT(DISTINCT p.employee_id) >= 5;

CREATE VIEW warehouse.metric_m10_cost_per_head AS
SELECT p.period_end_date, de.department_id,
       SUM(p.employer_cost) / NULLIF(COUNT(DISTINCT p.employee_id), 0)
           AS cost_per_head
FROM warehouse.fact_payroll p
JOIN warehouse.dim_employee de ON p.employee_key = de.employee_key
GROUP BY p.period_end_date, de.department_id
HAVING COUNT(DISTINCT p.employee_id) >= 5;

CREATE VIEW warehouse.metric_m11_overtime_share AS
SELECT p.period_end_date, de.department_id,
       ROUND(
           100.0 * SUM(p.overtime_pay) / NULLIF(SUM(p.employer_cost), 0), 4
       ) AS overtime_share_pct
FROM warehouse.fact_payroll p
JOIN warehouse.dim_employee de ON p.employee_key = de.employee_key
GROUP BY p.period_end_date, de.department_id
HAVING COUNT(DISTINCT p.employee_id) >= 5;

CREATE VIEW warehouse.metric_m12_variable_pay_share AS
SELECT p.period_end_date, de.department_id,
       ROUND(
           100.0 * SUM(p.variable_pay) / NULLIF(SUM(p.gross_pay), 0), 4
       ) AS variable_pay_share_pct
FROM warehouse.fact_payroll p
JOIN warehouse.dim_employee de ON p.employee_key = de.employee_key
GROUP BY p.period_end_date, de.department_id
HAVING COUNT(DISTINCT p.employee_id) >= 5;

CREATE VIEW warehouse.metric_m13_attendance_rate AS
SELECT a.period_end_date, de.department_id,
       (
           SUM(a.present_days) + 0.5 * SUM(a.half_days_unpaid)
       ) / NULLIF(SUM(a.scheduled_days), 0) AS attendance_rate
FROM warehouse.fact_attendance_monthly a
JOIN warehouse.dim_employee de ON a.employee_key = de.employee_key
GROUP BY a.period_end_date, de.department_id
HAVING COUNT(DISTINCT a.employee_id) >= 5;

CREATE VIEW warehouse.metric_m14_late_arrival_rate AS
SELECT a.period_end_date, de.department_id,
       SUM(a.late_arrivals) / NULLIF(SUM(a.present_days), 0)
           AS late_arrival_rate
FROM warehouse.fact_attendance_monthly a
JOIN warehouse.dim_employee de ON a.employee_key = de.employee_key
GROUP BY a.period_end_date, de.department_id
HAVING COUNT(DISTINCT a.employee_id) >= 5;

CREATE VIEW warehouse.metric_m15_leave_without_pay_days AS
SELECT p.period_end_date, de.department_id,
       SUM(p.lop_days) AS leave_without_pay_days
FROM warehouse.fact_payroll p
JOIN warehouse.dim_employee de ON p.employee_key = de.employee_key
GROUP BY p.period_end_date, de.department_id
HAVING COUNT(DISTINCT p.employee_id) >= 5;

CREATE VIEW warehouse.metric_m16_revenue AS
SELECT record->>'posting_period' AS posting_period,
       ROUND(
           -SUM((record->>'signed_amount_debit_positive')::NUMERIC), 2
       ) AS revenue
FROM dq_reference.fact_ledger
WHERE record->>'account_code' ~ '^[0-9]+$'
  AND (record->>'account_code')::INTEGER BETWEEN 4001 AND 4004
GROUP BY record->>'posting_period';

CREATE VIEW warehouse.metric_m17_net_profit AS
SELECT record->>'posting_period' AS posting_period,
       ROUND(
           -SUM((record->>'signed_amount_debit_positive')::NUMERIC), 2
       ) AS net_profit
FROM dq_reference.fact_ledger
WHERE record->>'account_code' ~ '^[0-9]+$'
  AND (
       (record->>'account_code')::INTEGER BETWEEN 4000 AND 4999
       OR (record->>'account_code')::INTEGER BETWEEN 5000 AND 5999
  )
GROUP BY record->>'posting_period';

CREATE VIEW warehouse.metric_m18_operating_margin AS
SELECT n.posting_period, n.net_profit, r.revenue,
       ROUND(100.0 * n.net_profit / NULLIF(r.revenue, 0), 4)
           AS operating_margin_pct
FROM warehouse.metric_m17_net_profit n
JOIN warehouse.metric_m16_revenue r USING (posting_period);

CREATE VIEW warehouse.metric_m19_payroll_as_revenue_pct AS
WITH payroll_ledger AS (
    SELECT record->>'posting_period' AS posting_period,
           SUM((record->>'signed_amount_debit_positive')::NUMERIC)
               AS ledger_payroll_cost
    FROM dq_reference.fact_ledger
    WHERE record->>'account_code' ~ '^[0-9]+$'
      AND (record->>'account_code')::INTEGER BETWEEN 5001 AND 5005
    GROUP BY record->>'posting_period'
)
SELECT p.posting_period, p.ledger_payroll_cost, r.revenue,
       ROUND(
           100.0 * p.ledger_payroll_cost / NULLIF(r.revenue, 0), 4
       ) AS payroll_as_revenue_pct
FROM payroll_ledger p
JOIN warehouse.metric_m16_revenue r USING (posting_period);

CREATE VIEW warehouse.metric_m20_days_sales_outstanding AS
WITH report_date AS (
    SELECT (
        MAX(month_start_date) + INTERVAL '1 month' - INTERVAL '1 day'
    )::DATE AS as_of_date
    FROM warehouse.fact_headcount_monthly
),
invoices AS (
    SELECT
        record->>'status' AS status,
        record->>'client_id' AS client_id,
        (record->>'invoice_date')::TIMESTAMP::DATE AS invoice_date,
        (record->>'total_amount')::NUMERIC AS total_amount,
        (record->>'balance_due')::NUMERIC AS balance_due
    FROM dq_reference.fact_invoice
)
SELECT d.as_of_date,
       SUM(i.balance_due) FILTER (
           WHERE UPPER(COALESCE(i.status, '')) NOT IN ('DRAFT', 'CANCELLED')
       ) AS closing_receivables,
       SUM(i.total_amount) FILTER (
           WHERE UPPER(COALESCE(i.status, '')) NOT IN ('DRAFT', 'CANCELLED')
             AND i.invoice_date BETWEEN d.as_of_date - 89 AND d.as_of_date
       ) AS revenue_incl_gst_last_90_days,
       ROUND(
           90.0 * SUM(i.balance_due) FILTER (
               WHERE UPPER(COALESCE(i.status, '')) NOT IN ('DRAFT', 'CANCELLED')
           ) / NULLIF(
               SUM(i.total_amount) FILTER (
                   WHERE UPPER(COALESCE(i.status, '')) NOT IN ('DRAFT', 'CANCELLED')
                     AND i.invoice_date BETWEEN d.as_of_date - 89 AND d.as_of_date
               ), 0
           ), 4
       ) AS dso_days
FROM report_date d
CROSS JOIN invoices i
GROUP BY d.as_of_date;

CREATE VIEW warehouse.metric_m21_overdue_receivables AS
WITH report_date AS (
    SELECT (
        MAX(month_start_date) + INTERVAL '1 month' - INTERVAL '1 day'
    )::DATE AS as_of_date
    FROM warehouse.fact_headcount_monthly
),
invoices AS (
    SELECT
        record->>'client_id' AS client_id,
        record->>'status' AS status,
        (record->>'due_date')::TIMESTAMP::DATE AS due_date,
        (record->>'balance_due')::NUMERIC AS balance_due
    FROM dq_reference.fact_invoice
)
SELECT d.as_of_date, i.client_id,
       SUM(i.balance_due) AS overdue_receivables
FROM report_date d
CROSS JOIN invoices i
WHERE i.due_date < d.as_of_date
  AND UPPER(COALESCE(i.status, '')) NOT IN ('DRAFT', 'CANCELLED')
GROUP BY d.as_of_date, i.client_id;

CREATE VIEW warehouse.metric_m22_task_completion_rate AS
SELECT record->>'team_id' AS team_id,
       record->>'sprint_id' AS sprint_id,
       COUNT(*) FILTER (
           WHERE record->>'status' = 'Done'
       ) AS done_tasks,
       COUNT(*) FILTER (
           WHERE COALESCE(record->>'status', '') <> 'Cancelled'
       ) AS planned_non_cancelled_tasks,
       ROUND(
           100.0 * COUNT(*) FILTER (WHERE record->>'status' = 'Done')
           / NULLIF(
               COUNT(*) FILTER (
                   WHERE COALESCE(record->>'status', '') <> 'Cancelled'
               ), 0
           ), 4
       ) AS task_completion_rate_pct
FROM dq_reference.fact_task
GROUP BY record->>'team_id', record->>'sprint_id'
HAVING COUNT(*) FILTER (
    WHERE COALESCE(record->>'status', '') <> 'Cancelled'
) >= 5;

CREATE VIEW warehouse.metric_m23_on_time_delivery_rate AS
SELECT record->>'team_id' AS team_id,
       record->>'sprint_id' AS sprint_id,
       COUNT(*) FILTER (
           WHERE record->>'status' = 'Done'
       ) AS done_tasks,
       COUNT(*) FILTER (
           WHERE record->>'status' = 'Done'
             AND record->>'completed_on_time' = 'Y'
       ) AS on_time_done_tasks,
       ROUND(
           100.0 * COUNT(*) FILTER (
               WHERE record->>'status' = 'Done'
                 AND record->>'completed_on_time' = 'Y'
           ) / NULLIF(
               COUNT(*) FILTER (WHERE record->>'status' = 'Done'), 0
           ), 4
       ) AS on_time_delivery_rate_pct
FROM dq_reference.fact_task
GROUP BY record->>'team_id', record->>'sprint_id'
HAVING COUNT(*) FILTER (WHERE record->>'status' = 'Done') >= 5;

CREATE VIEW warehouse.metric_m24_velocity AS
SELECT record->>'team_id' AS team_id,
       record->>'sprint_id' AS sprint_id,
       SUM(
           CASE WHEN record->>'status' = 'Done'
                THEN (record->>'story_points')::NUMERIC
           END
       ) AS velocity_story_points
FROM dq_reference.fact_task
GROUP BY record->>'team_id', record->>'sprint_id';

CREATE VIEW warehouse.metric_m25_average_cycle_time AS
WITH task_dates AS (
    SELECT record->>'team_id' AS team_id,
           record->>'sprint_id' AS sprint_id,
           record->>'status' AS status,
           CASE WHEN NULLIF(record->>'started_date', '') IS NOT NULL
                THEN (record->>'started_date')::TIMESTAMP END AS started_at,
           CASE WHEN NULLIF(record->>'completed_date', '') IS NOT NULL
                THEN (record->>'completed_date')::TIMESTAMP END AS completed_at
    FROM dq_reference.fact_task
)
SELECT team_id, sprint_id,
       AVG(
           EXTRACT(EPOCH FROM (completed_at - started_at)) / 86400.0
       ) FILTER (
           WHERE status = 'Done'
             AND started_at IS NOT NULL
             AND completed_at IS NOT NULL
             AND completed_at >= started_at
       ) AS average_cycle_time_days,
       COUNT(*) FILTER (
           WHERE status = 'Done'
             AND started_at IS NOT NULL
             AND completed_at IS NOT NULL
             AND completed_at < started_at
       ) AS negative_cycle_time_rows
FROM task_dates
GROUP BY team_id, sprint_id
HAVING COUNT(*) FILTER (
    WHERE status = 'Done'
      AND started_at IS NOT NULL
      AND completed_at IS NOT NULL
      AND completed_at >= started_at
) >= 5;

CREATE OR REPLACE VIEW warehouse.metric_m26_anomaly_flag_rate AS
SELECT
    source_dataset,
    DATE_TRUNC('month', period)::DATE AS month_start,
    COUNT(*)::BIGINT AS scored_records,
    COUNT(*) FILTER (WHERE flagged = 'Y')::BIGINT AS flagged_records,
    COUNT(*) FILTER (WHERE flagged = 'N')::BIGINT AS unflagged_records,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE flagged = 'Y')
        / NULLIF(COUNT(*), 0),
        4
    ) AS anomaly_flag_rate_pct,
    'SCORED_RECORDS_ONLY_INCOMPLETE_COVERAGE'::TEXT AS rate_status
FROM warehouse.fact_anomaly
GROUP BY source_dataset, DATE_TRUNC('month', period)::DATE;

CREATE VIEW warehouse.metric_m27_high_risk_share AS
SELECT record->>'as_of_date' AS as_of_date,
       record->>'department_id' AS department_id,
       COUNT(DISTINCT record->>'employee_id') AS employees_in_group,
       COUNT(DISTINCT record->>'employee_id') FILTER (
           WHERE record->>'risk_band' = 'High'
       ) AS high_risk_employees,
       ROUND(
           100.0 * COUNT(DISTINCT record->>'employee_id') FILTER (
               WHERE record->>'risk_band' = 'High'
           ) / NULLIF(COUNT(DISTINCT record->>'employee_id'), 0), 4
       ) AS high_risk_share_pct
FROM dq_reference.fact_attrition_risk
GROUP BY record->>'as_of_date', record->>'department_id'
HAVING COUNT(DISTINCT record->>'employee_id') >= 10;

CREATE OR REPLACE VIEW warehouse.metric_m28_forecast_error_mape AS
WITH comparison AS (
    SELECT
        f.forecast_month AS month_start_date,
        f.department_id,
        f.model_version,
        f.method,
        CASE
            WHEN f.model_version = 'naive-previous-month-backtest-1'
                THEN 'HISTORICAL_BACKTEST'
            WHEN h.headcount_end IS NULL
                THEN 'SUPPLIED_FORECAST_PENDING_ACTUALS'
            ELSE 'SUPPLIED_FORECAST'
        END AS evaluation_type,
        h.headcount_end::NUMERIC AS actual_headcount,
        f.forecast_value::NUMERIC AS forecast_headcount,
        CASE
            WHEN h.headcount_end > 0 THEN
                100.0 * ABS(
                    h.headcount_end::NUMERIC - f.forecast_value::NUMERIC
                ) / h.headcount_end::NUMERIC
            ELSE NULL
        END AS absolute_percentage_error_pct
    FROM warehouse.fact_forecast f
    LEFT JOIN warehouse.fact_headcount_monthly h
      ON h.month_start_date = f.forecast_month
     AND h.department_id = f.department_id
    WHERE f.metric = 'headcount_end'
      AND f.department_id <> 'ALL'
      AND f.model_version IN (
          'trend-seasonal-baseline-0.1',
          'naive-previous-month-backtest-1'
      )
)
SELECT
    month_start_date,
    department_id,
    model_version,
    method,
    evaluation_type,
    actual_headcount,
    forecast_headcount,
    ROUND(absolute_percentage_error_pct, 4)
        AS absolute_percentage_error_pct,
    ROUND(
        AVG(absolute_percentage_error_pct) OVER (
            PARTITION BY department_id, model_version
            ORDER BY month_start_date
            ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
        ),
        4
    ) AS forecast_error_mape_pct
FROM comparison;

CREATE VIEW warehouse.metric_catalog AS
SELECT * FROM (VALUES
    ('M01', 'Headcount', 'Active employees on the last day of the month (permanent and contract).', 'COUNT(DISTINCT employee_id) with hire_date <= month_end AND (exit_date IS NULL OR exit_date > month_end)', 'warehouse.fact_headcount_monthly', 'Department x month', 'Month end', 'HR Analytics', 'count', 'Context dependent', 'Excludes CEO if you compare departments only', 5),
    ('M02', 'Hires', 'Employees whose hire_date falls in the month.', 'COUNT(employee_id) where hire_date in month', 'warehouse.fact_headcount_monthly', 'Department x month', 'Month', 'HR Analytics', 'count', 'Context dependent', 'Transfers are not hires', 5),
    ('M03', 'Exits', 'Employees whose exit_date falls in the month (resigned, terminated or contract ended).', 'COUNT(employee_id) where exit_date in month', 'warehouse.fact_headcount_monthly', 'Department x month', 'Month', 'HR Analytics', 'count', 'Lower is better', NULL, 5),
    ('M04', 'Attrition rate (monthly)', 'Share of people who left in the month.', 'Exits / headcount_start x 100', 'warehouse.fact_headcount_monthly', 'Department x month', 'Month', 'HR Analytics', 'percent', 'Lower is better', 'Very noisy for small departments', 10),
    ('M05', 'Attrition rate (rolling 12 months)', 'Leavers in the last 12 months divided by average headcount over the same months.', 'SUM(exits, 12m) / AVG(headcount_end, 12m) x 100', 'warehouse.fact_headcount_monthly', 'Department x month', '12 months', 'HR Analytics', 'percent', 'Lower is better', 'Use for headline reporting; monthly is too noisy', 10),
    ('M06', 'Voluntary attrition rate', 'Same as M05 but only resignations (voluntary_exits).', 'SUM(voluntary_exits, 12m) / AVG(headcount_end, 12m) x 100', 'warehouse.fact_headcount_monthly', 'Department x month', '12 months', 'HR Analytics', 'percent', 'Lower is better', NULL, 10),
    ('M07', 'Gross pay', 'Total earnings before deductions for the month.', 'SUM(gross_pay)', 'warehouse.fact_payroll', 'Employee x month', 'Month', 'Payroll', 'INR', 'Context dependent', 'Includes overtime and variable pay', 5),
    ('M08', 'Net pay', 'Take-home pay after employee deductions.', 'SUM(net_pay)', 'warehouse.fact_payroll', 'Employee x month', 'Month', 'Payroll', 'INR', 'Context dependent', NULL, 5),
    ('M09', 'Payroll cost (employer cost)', 'Full cost of employees to the company: gross pay plus employer PF and ESI.', 'SUM(employer_cost)', 'warehouse.fact_payroll', 'Employee x month', 'Month', 'Finance', 'INR', 'Lower is better when output is equal', 'Must reconcile with ledger accounts 5001-5005', 5),
    ('M10', 'Cost per head', 'Average employer cost per paid employee.', 'SUM(employer_cost) / COUNT(DISTINCT employee_id)', 'warehouse.fact_payroll', 'Department x month', 'Month', 'Finance', 'INR', 'Context dependent', 'Part-month joiners lower the average', 5),
    ('M11', 'Overtime share', 'How much of payroll cost is overtime pay.', 'SUM(overtime_pay) / SUM(employer_cost) x 100', 'warehouse.fact_payroll', 'Department x month', 'Month', 'Payroll', 'percent', 'Lower is better', 'Only overtime-eligible roles earn overtime', 5),
    ('M12', 'Variable pay share', 'Bonus, incentive and award pay as a share of gross pay.', 'SUM(variable_pay) / SUM(gross_pay) x 100', 'warehouse.fact_payroll', 'Department x month', 'Month', 'Payroll', 'percent', 'Context dependent', 'April bonus and quarter-end incentives create spikes', 5),
    ('M13', 'Attendance rate', 'Days present (half day counts 0.5) divided by scheduled working days.', '(SUM(present_days) + 0.5 x SUM(half_days_unpaid)) / SUM(scheduled_days)', 'warehouse.fact_attendance_monthly + warehouse.dim_employee', 'Department x month', 'Month', 'HR Analytics', 'ratio', 'Higher is better', 'Paid leave counts as not present', 5),
    ('M14', 'Late arrival rate', 'Late check-ins per present day.', 'SUM(late_arrivals) / SUM(present_days)', 'warehouse.fact_attendance_monthly + warehouse.dim_employee', 'Department x month', 'Month', 'HR Analytics', 'ratio', 'Lower is better', 'Work-from-home days use web check-in time', 5),
    ('M15', 'Leave without pay days', 'Unpaid absence and unpaid leave days.', 'SUM(lop_days) in fact_payroll', 'warehouse.fact_payroll', 'Employee x month', 'Month', 'Payroll', 'days', 'Lower is better', 'Half-day unpaid counts 0.5', 5),
    ('M16', 'Revenue', 'Income booked in the ledger (accounts 4001-4004).', '-SUM(signed_amount) for accounts 4001-4004', 'dq_reference.fact_ledger (JSON reference records)', 'Account x month', 'Month', 'Finance', 'INR', 'Higher is better', 'Excludes GST (booked to 2200)', NULL),
    ('M17', 'Net profit', 'Revenue minus all expenses (4xxx less 5xxx).', '-SUM(signed_amount) for accounts 4xxx and 5xxx', 'dq_reference.fact_ledger (JSON reference records)', 'Month', 'Month', 'Finance', 'INR', 'Higher is better', 'Interest income (4900) is included', NULL),
    ('M18', 'Operating margin', 'Net profit as a share of revenue.', 'Net profit / Revenue x 100', 'dq_reference.fact_ledger (JSON reference records)', 'Month', 'Month', 'Finance', 'percent', 'Higher is better', NULL, NULL),
    ('M19', 'Payroll as % of revenue', 'Share of revenue consumed by payroll cost.', 'Payroll cost / Revenue x 100', 'dq_reference.fact_ledger (payroll and revenue accounts)', 'Month', 'Month', 'Finance', 'percent', 'Lower is better', 'Use ledger payroll accounts to avoid mismatch', NULL),
    ('M20', 'Days sales outstanding (DSO)', 'Average days to collect: receivables divided by credit sales x days.', 'Closing receivables / revenue incl GST (last 90 days) x 90', 'dq_reference.fact_invoice (JSON reference records)', 'Month', '90 days', 'Finance', 'days', 'Lower is better', 'Carried-in invoices included', NULL),
    ('M21', 'Overdue receivables', 'Unpaid invoice balance past due date at the report date.', 'SUM(balance_due) where due_date < report date and status not DRAFT/CANCELLED', 'dq_reference.fact_invoice (JSON reference records)', 'Client x date', 'Point in time', 'Finance', 'INR', 'Lower is better', NULL, NULL),
    ('M22', 'Task completion rate', 'Tasks done divided by tasks planned in the sprint (cancelled tasks excluded).', 'COUNT(status = Done) / COUNT(status != Cancelled)', 'dq_reference.fact_task (JSON reference records)', 'Team x sprint', 'Sprint', 'Engineering Ops', 'percent', 'Higher is better', 'Sample feed until the live board is ready', 5),
    ('M23', 'On-time delivery rate', 'Done tasks completed on or before the sprint end date.', 'COUNT(completed_on_time = Y) / COUNT(status = Done)', 'dq_reference.fact_task (JSON reference records)', 'Team x sprint', 'Sprint', 'Engineering Ops', 'percent', 'Higher is better', NULL, 5),
    ('M24', 'Velocity', 'Story points completed in the sprint.', 'SUM(story_points) where status = Done', 'dq_reference.fact_task (JSON reference records)', 'Team x sprint', 'Sprint', 'Engineering Ops', 'points', 'Context dependent', 'Do not compare across teams', NULL),
    ('M25', 'Average cycle time', 'Days from start to completion for done tasks.', 'AVG(completed_date - started_date)', 'dq_reference.fact_task (JSON reference records)', 'Team x sprint', 'Sprint', 'Engineering Ops', 'days', 'Lower is better', 'Negative values are data errors', 5),
    ('M26', 'Anomaly flag rate', 'Share of scored records flagged by the AI anomaly service.', 'COUNT(flagged = Y) / COUNT(*)', 'warehouse.fact_anomaly + warehouse.fact_attendance_monthly + warehouse.fact_payroll', 'Source x month', 'Month', 'AI/ML', 'percent', 'Context dependent', 'Flags are leads, not proof', NULL),
    ('M27', 'High-risk share', 'Share of employees in the High attrition-risk band.', 'COUNT(risk_band = High) / COUNT(*)', 'dq_reference.fact_attrition_risk (JSON reference records)', 'Department', 'Point in time', 'AI/ML', 'percent', 'Lower is better', 'Show by group only; never rank named people', 10),
    ('M28', 'Forecast error (MAPE)', 'Average absolute percentage error of headcount forecasts versus actuals.', 'AVG(ABS(actual - forecast) / actual) x 100', 'warehouse.fact_forecast + warehouse.fact_headcount_monthly', 'Department x month', 'Rolling', 'AI/ML', 'percent', 'Lower is better', 'Needs actuals for the forecast months', NULL)
) AS v(
    metric_id, metric_name, definition, formula, source, grain,
    time_period, owner, unit, good_direction, caveat, minimum_group_size
);
