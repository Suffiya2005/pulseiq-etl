# Task 14 — AI Signals Dashboard Validation

## 1. Overview
Task 14 integrates AI-generated anomaly signals, forecasts, historical forecast validation, and model governance into the PulseIQ Analytics Streamlit dashboard.

## 2. AI Anomaly Signals
- Total anomaly signals: 405
- Quantified money at risk: ₹31,421,239.07
- Signals without risk estimate: 221
- Anomaly categories are displayed for investigation.
- Highest-risk flagged records are available for human review.

Note: Money at risk represents estimated exposure, not confirmed financial loss. Unquantified risk values are not treated as zero.

## 3. AI Forecasts
- Forecast metric: Monthly attrition rate
- Forecast horizon: October 2026 – March 2027
- Confidence interval: 80%
- Forecast method: Same-month average of the last three years
- Trained through: September 2026

The dashboard displays forecast values and lower_80 / upper_80 confidence bounds.

## 4. Historical Headcount Forecast Validation
- Historical comparisons: 880
- Overall MAE: 0.66 employees
- Overall MAPE: 2.62%
- Department-level results: forecast_error_by_department.csv

The historical backtest uses the previous-month headcount method.

## 5. Attrition Forecast Validation
Historical attrition forecast error could not be calculated because matching historical forecast records are unavailable. Current attrition forecasts cover future periods only.

## 6. Model Governance
- AI signals are decision-support outputs.
- Anomaly flags are not proof of fraud or misconduct.
- Forecasts may not capture unexpected future changes.
- 80% confidence intervals are not guaranteed outcome ranges.
- Historical accuracy does not guarantee future accuracy.
- Human validation and domain review are required before operational or financial decisions.

## 7. Evidence Files
- forecast_error_by_department.csv
- dashboard_screenshot.png (dashboard evidence)
- Task 14 dashboard screenshots covering anomaly signals, forecasts, validation, and governance

## 8. Validation Status
Task 14 dashboard loaded successfully in Streamlit. Anomaly analytics, forecast visualizations, historical headcount validation, and governance guidance were reviewed.
