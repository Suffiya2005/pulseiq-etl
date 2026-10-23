CREATE OR REPLACE VIEW warehouse.metric_m28_historical_backtest AS
WITH history AS (
    SELECT
        month_start_date,
        department_id,
        headcount_end::NUMERIC AS actual_headcount,
        LAG(headcount_end::NUMERIC) OVER (
            PARTITION BY department_id
            ORDER BY month_start_date
        ) AS naive_forecast
    FROM warehouse.fact_headcount_monthly
)
SELECT
    month_start_date,
    department_id,
    actual_headcount,
    naive_forecast AS naive_forecast_headcount,
    ROUND(
        100.0 * ABS(actual_headcount - naive_forecast)
        / NULLIF(actual_headcount, 0),
        4
    ) AS absolute_percentage_error_pct,
    'PREVIOUS_MONTH_HEADCOUNT_NAIVE_BACKTEST'::TEXT AS backtest_method
FROM history
WHERE naive_forecast IS NOT NULL
  AND actual_headcount > 0;
