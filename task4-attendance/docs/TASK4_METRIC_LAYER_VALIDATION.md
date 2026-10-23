# Task 4 — Governed Metric Layer Validation Evidence

## 1. Summary

**Status:** Core metric layer created and validated, with documented source limitations.

- Official metric dictionary: 28 metrics.
- SQL metric views created: 28.
- `warehouse.metric_catalog` rows: 28.
- All 28 views queried successfully for row counts.
- Five independent hand-checks: all PASS.
- Small-group privacy checks: tested metrics passed.
- SQL source file: `task4-attendance/sql/metric_views.sql`.
- Forecast loader: `task4-attendance/sql/load_forecast.sql`.
- Pre-official SQL backup: `task4-attendance/sql/metric_views_before_official_28.sql`.

## 2. Official metric view row counts

| ID | Metric view | Rows |
|---|---|---:|
| M01 | `metric_m01_headcount` | 810 |
| M02 | `metric_m02_hires` | 810 |
| M03 | `metric_m03_exits` | 810 |
| M04 | `metric_m04_monthly_attrition_rate` | 646 |
| M05 | `metric_m05_attrition_rate_rolling_12m` | 539 |
| M06 | `metric_m06_voluntary_attrition_rate` | 539 |
| M07 | `metric_m07_gross_pay` | 180 |
| M08 | `metric_m08_net_pay` | 180 |
| M09 | `metric_m09_payroll_cost` | 180 |
| M10 | `metric_m10_cost_per_head` | 180 |
| M11 | `metric_m11_overtime_share` | 180 |
| M12 | `metric_m12_variable_pay_share` | 180 |
| M13 | `metric_m13_attendance_rate` | 180 |
| M14 | `metric_m14_late_arrival_rate` | 180 |
| M15 | `metric_m15_leave_without_pay_days` | 180 |
| M16 | `metric_m16_revenue` | 18 |
| M17 | `metric_m17_net_profit` | 18 |
| M18 | `metric_m18_operating_margin` | 18 |
| M19 | `metric_m19_payroll_as_revenue_pct` | 18 |
| M20 | `metric_m20_days_sales_outstanding` | 1 |
| M21 | `metric_m21_overdue_receivables` | 28 |
| M22 | `metric_m22_task_completion_rate` | 608 |
| M23 | `metric_m23_on_time_delivery_rate` | 608 |
| M24 | `metric_m24_velocity` | 608 |
| M25 | `metric_m25_average_cycle_time` | 608 |
| M26 | `metric_m26_anomaly_flag_rate` | 36 |
| M27 | `metric_m27_high_risk_share` | 10 |
| M28 | `metric_m28_forecast_error_mape` | 880* |

M28 returns 880 historical naive backtest rows. The supplied future forecast model's measured accuracy remains unavailable because actual values do not yet overlap its forecast months.

## 3. Metric catalog

The catalog has 28 rows, matching the official workbook's `metric_dictionary` sheet. It stores the metric ID, name, business definition, formula, source, grain, time period, owner, unit, good direction, caveat, and configured minimum group size.

The privacy thresholds recorded in the catalog were checked against the official dictionary:
- M01–M03: 5
- M04–M06: 10
- M07–M15: 5
- M22–M23: 5
- M25: 5
- M27: 10
- Other metrics: no minimum group size specified in the dictionary.

## 4. Five independent hand-checks

All five checks had a zero difference between the independent calculation and the SQL view.

| Metric | Test slice | Independent calculation | View result | Difference | Status |
|---|---|---:|---:|---:|---|
| M07 Gross pay | April 2025, D01 | ₹2,11,89,054.97 | ₹2,11,89,054.97 | ₹0.00 | PASS |
| M08 Net pay | April 2025, D01 | ₹1,85,78,166.77 | ₹1,85,78,166.77 | ₹0.00 | PASS |
| M13 Attendance rate | April 2025, D01 | 0.9509 | 0.9509 | 0.0000 | PASS |
| M16 Revenue | April 2025 | ₹7,10,75,300.00 | ₹7,10,75,300.00 | ₹0.00 | PASS |
| M17 Net profit | April 2025 | ₹63,14,062.92 | ₹63,14,062.92 | ₹0.00 | PASS |

## 5. Small-group privacy validation

The source groups were compared against the corresponding views. No groups below the tested threshold were exposed in these audits.

| Metric IDs | Raw undersized groups found | Exposed by view | Result |
|---|---:|---:|---|
| M01 | 81 | 0 | PASS |
| M02 | 81 | 0 | PASS |
| M03 | 81 | 0 | PASS |
| M04 | 245 | 0 | PASS |
| M05 | 231 | 0 | PASS |
| M06 | 231 | 0 | PASS |
| Each of M07–M15 | 18 | 0 | PASS |
| M22 | 0 | 0 | PASS |
| M23 | 0 | 0 | PASS |
| M25 | 0 | 0 | PASS |
| M27 | 3 | 0 | PASS |

The configured thresholds for metrics without a dictionary value were not invented. The table above records the metrics and groups covered by the privacy checks; it does not claim that every possible reporting surface or every metric was independently privacy-tested.

## 6. Attrition denominator decision

The official metric dictionary defines different denominators for different attrition metrics:

- **M04 Monthly attrition:** monthly exits divided by start-of-month headcount, multiplied by 100.
- **M05 Rolling 12-month attrition:** exits across the last 12 months divided by average ending headcount over those months, multiplied by 100.
- **M06 Voluntary attrition:** voluntary exits across the last 12 months divided by average ending headcount over those months, multiplied by 100.

The SQL definitions follow these official formulas rather than forcing one denominator onto every attrition metric.

## 7. Source and data limitations

### M26 - Estimated anomaly flag rate

The anomaly source contains flagged records only; it does not contain the complete model-scored population. The metric view therefore uses matched monthly source population counts as a denominator and labels the result as an estimate.

- Attendance source: 221 flagged records matched employee and month in the attendance data.
- Payroll source: 184 flagged records matched exact payroll source record IDs.
- Total flagged records: 405.
- Attendance estimated rate averaged 3.0011% for April 2025 through September 2026.
- Payroll estimated rate averaged 2.5036% for April 2025 through September 2026.

These are matched-source-population estimates, not verified model scoring rates. Flags are signals for review, not proof of misconduct or confirmed operational problems.

### M28 - Official forecast error and historical backtest

The original workbook supplied 72 forecasts covering October 2026 through March 2027. Actual headcount currently ends in September 2026, so the supplied future forecast model has no overlapping actuals and its measured future accuracy is not yet available.

A separate naive historical backtest uses previous-month headcount as the prediction:
- Comparable department-months: 880.
- Departments: 11.
- Historical naive MAPE: 2.6157%.
- Test period: February 2020 through September 2026.

The `warehouse.metric_m28_forecast_error_mape` view labels rows with `evaluation_type` and `model_version` so that historical backtest results remain distinguishable from the supplied future forecast model. The historical result is not a substitute for measuring the supplied model's future accuracy.

Some ledger, invoice, task and attrition-risk sources are stored under `dq_reference` as JSON reference records rather than normalized warehouse fact tables. These source dependencies are identified in the metric catalog. The source data is project sample data and must not be treated as verified real-world workforce results.

## 8. Final checklist

- [x] 28 official metric views exist.
- [x] Catalog contains 28 official dictionary entries.
- [x] All 28 views execute and return a row count without query errors.
- [x] Five independent metric hand-checks pass.
- [x] Configured minimum group sizes are present in catalog metadata.
- [x] Small-group exposure checks pass for the tested metrics.
- [x] Attrition denominator definitions documented.
- [x] M26 and M28 limitations documented.
- [x] SQL backup preserved before replacing the initial implementation.

**Evidence result:** The governed metric layer is implemented and the above checks passed, with the documented limitations remaining visible for reporting and follow-up.

## 9. Final M03 Exits privacy recheck

- Raw groups below the configured minimum: 81
- Small groups exposed by warehouse.metric_m03_exits: 0
- Result: PASS
- Check date: 23 October 2026


## 10. M26 and M28 Follow-up Validation

### M26
- Estimated monthly rows: 36.
- Attendance average estimated rate: 3.0011%.
- Payroll average estimated rate: 2.5036%.
- Limitation: the available anomaly feed contains flagged records only.

### M28
- Supplied future forecast rows: 72.
- Historical naive backtest rows: 880.
- Historical test departments: 11.
- Historical naive MAPE: 2.6157%.
- Historical test period: February 2020 through September 2026.
- Supplied-model actual-versus-forecast accuracy remains unavailable until actuals overlap the October 2026 through March 2027 forecast period.


* M28's 880 rows are historical naive backtest comparisons only. The supplied future forecast model still has no overlapping actual months, so its measured forecast accuracy remains unavailable.

## 11. Final follow-up validation

### 11.1 Starter SQL examples
The original `05_Starter/metric_views_examples.sql` file was not available in the project files searched. As a documented substitute, `task4-attendance/sql/metric_views_examples_verified.sql` was created and executed successfully with `ON_ERROR_STOP=1`. All three queries passed:
1. Metric catalog lookup returned M07, M13 and M28.
2. Department D01 attendance trend returned April-June 2025.
3. Historical forecast backtest summary returned 880 evaluated rows and mean absolute percentage error of 2.6157%, covering February 2020 to September 2026.
These are replacement examples; the unavailable original starter file is not claimed to have been executed.

### 11.2 M26 anomaly matching and denominator caveat
Reconciliation found 221 flagged attendance anomaly records; all 221 matched source attendance rows by employee and month, across 159 distinct employees. Payroll reconciliation found 184 flagged records, all 184 matching exact payroll record IDs, across 92 distinct employees.
The M26 view reports source-population counts and the matched flagged-record counts by month. However, `warehouse.fact_anomaly` contains only `flagged = 'Y'` records for these model versions in the inspected data. The completeness of model scoring across the entire source population therefore cannot be independently established. `anomaly_flag_rate_pct` remains an estimated source-population share and must not be represented as a fully verified model flag rate.



### 11.3 M28 forecast accuracy limitation
The historical naive previous-month headcount backtest returned 880 comparisons with mean APE/MAPE of 2.6157% for February 2020 through September 2026. This is a historical baseline diagnostic and is not the official supplied forecast model's accuracy.
Actual headcount data currently ends in September 2026, while supplied official forecasts cover future months beginning October 2026. Official forecast accuracy cannot be calculated until actuals for the corresponding forecast months are available.

### 11.3.1 Reconstructed headcount forecast backtest

- Backtest results file: `task4-attendance/docs/HEADCOUNT_RECONSTRUCTED_BACKTEST.csv`.
- Method: reconstructed 36-month linear trend with half-strength month-of-year seasonality.
- Evaluation horizon: six months, using rolling historical forecast origins.
- Forecast comparisons: 2,640 across 11 departments.
- Evaluation period: January 2023 through September 2026.
- Overall mean absolute error (MAE): 2.8943 employees.
- Overall mean absolute percentage error (MAPE): 9.8672%.
- Highest department-level MAPE: D07, 19.3089%.
- D00 MAPE: 0%; this department has a constant headcount of 1 in the evaluated records, so its result is not a meaningful accuracy benchmark.

**Limitation:** The original supplied model implementation was not found in the inspected project files. This backtest uses a reconstructed approximation of the documented method and does not establish the official model's accuracy. Its results must be reported separately from the historical naive baseline and the supplied future forecasts.
### 11.4 Final acceptance status
The 28-view governed metric layer, 28-row metric catalog, five manual metric checks, privacy audit, replacement SQL examples and validation evidence are implemented and tested. The original starter-file execution could not be reproduced because that file was unavailable. M26 remains explicitly estimated because scoring coverage is unverified; official future forecast accuracy remains pending actual data. These are documented source/data limitations, not claims of completed validation.



### 11.5 Confirmation from the original anomaly workbook
The original `fact_anomaly` worksheet was inspected directly. It contains 405 rows: 221 flagged attendance records and 184 flagged payroll records. All 405 rows have `flagged = 'Y'`; no `flagged = 'N'` rows are supplied. Therefore, the workbook does not establish the complete scored population or the model's exact flag rate. M26 remains an explicitly estimated source-population share until complete scoring output, including unflagged observations or equivalent scoring-coverage evidence, is provided.

**Closure decision:** The missing original starter SQL file is documented, and three replacement examples have been saved and executed. M26's data limitation has been investigated and confirmed. Official supplied-forecast accuracy cannot yet be measured because corresponding future actuals are unavailable. Neither M26 nor M28 is reported as fully verified beyond the available evidence.

