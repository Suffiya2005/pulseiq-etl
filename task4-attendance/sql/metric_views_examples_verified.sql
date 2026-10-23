-- Task 4: Verified replacement examples
-- Example 1: Read official metric definitions
SELECT metric_id, metric_name, source, grain, minimum_group_size
FROM warehouse.metric_catalog
WHERE metric_id IN ('M07', 'M13', 'M28')
ORDER BY metric_id;

-- Example 2: Read monthly attendance trend for department D01
SELECT period_end_date, department_id, attendance_rate
FROM warehouse.metric_m13_attendance_rate
WHERE department_id = 'D01'
  AND period_end_date >= DATE '2025-04-01'
  AND period_end_date < DATE '2025-07-01'
ORDER BY period_end_date;

-- Example 3: Summarize historical forecast backtest performance
SELECT
    evaluation_type,
    model_version,
    method,
    COUNT(*) AS evaluated_months,
    ROUND(AVG(absolute_percentage_error_pct), 4) AS mean_ape_pct,
    MIN(month_start_date) AS first_month,
    MAX(month_start_date) AS last_month
FROM warehouse.metric_m28_forecast_error_mape
GROUP BY evaluation_type, model_version, method
ORDER BY evaluation_type, model_version;
