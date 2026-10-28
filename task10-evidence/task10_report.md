# Task 10 — Budget vs Actual and KPI Targets

## 1. Objective
Compare departmental monthly payroll against budget, evaluate KPI performance against targets, identify overspending patterns, and recommend departments for review.

## 2. Payroll variance methodology

- **Variance amount** = Actual payroll cost - Budget payroll cost
- **Variance %** = (Variance amount / Budget payroll cost) * 100
- Positive variance = actual payroll cost exceeded budget (overspend).
- Negative variance = actual payroll cost was below budget (underspend).
- Zero variance = actual payroll cost matched budget.

A positive variance is a review signal, not proof of avoidable spending. Budgets may not reflect changes following the hiring freeze.

## 3. Data loading and coverage

- Budget payroll rows loaded: 198
- KPI target rows loaded: 180
- Department-month payroll variance rows available for analysis: 180
- Budget rows excluded from department-level variance reporting: 18, all for D00.

D00 has fewer than five employees. Its department-level payroll actuals are excluded under the minimum-group-size privacy rule. These rows are not interpreted as zero spending.

## 4. Manual variance verification

Three department-month cases were independently checked against the variance formula.

| Month | Department | Budget | Actual | Variance | Variance % |
|---|---|---:|---:|---:|---:|
| 2025-04-01 | D03 | 7,562,000.00 | 7,461,816.00 | -100,184.00 | -1.32% |
| 2025-10-01 | D04 | 5,180,000.00 | 5,044,494.31 | -135,505.69 | -2.62% |
| 2026-06-01 | D08 | 2,317,000.00 | 2,357,750.76 | 40,750.76 | 1.76% |

All three cases follow the stated formula and sign convention.

Detailed evidence: `manual_verification.csv`

## 5. Department overspend ranking

Departments are ranked by cumulative positive monthly variance, which measures the sum of overspend months before offsetting underspend months in other periods.

| Rank | Department | Cumulative positive variance | Overspend months | Net variance |
|---:|---|---:|---:|---:|
| 1 | D01 | 4,830,371.46 | 8 | -2,054,508.87 |
| 2 | D04 | 2,609,956.20 | 9 | 57,542.69 |
| 3 | D03 | 2,607,803.07 | 10 | 992,768.20 |
| 4 | D02 | 1,437,142.16 | 13 | 763,163.71 |
| 5 | D06 | 889,467.28 | 12 | 482,050.62 |
| 6 | D08 | 836,438.66 | 10 | 123,908.63 |
| 7 | D07 | 575,006.80 | 10 | 275,182.07 |
| 8 | D09 | 500,090.60 | 6 | -408,673.89 |
| 9 | D10 | 445,555.61 | 10 | 5,719.45 |
| 10 | D05 | 279,905.62 | 7 | -370,121.56 |

Detailed evidence: `department_overspend_ranking.csv`

## 6. Recommended department reviews

### Priority 1 — D01
D01 has the highest cumulative positive monthly variance (4,830,371.46 across eight overspend months), but its net variance is -2,054,508.87. This indicates that underspend months offset the positive variances. Review the largest overspend months and corresponding underspend months together before deciding whether the budget or staffing assumptions need adjustment.

### Priority 2 — D04
D04 has the second-highest cumulative positive variance (2,609,956.20 across nine overspend months), while its net variance is only 57,542.69. Review month-level swings and determine whether recurring overruns are offset by underspending elsewhere.

D03 is a close third, with cumulative positive variance of 2,607,803.07 and net positive variance of 992,768.20. It should be the next review priority.

These are review priorities based on variance patterns, not conclusions that spending was unnecessary.

## 7. KPI traffic-light methodology

- Attendance rate: GREEN when actual >= target; otherwise RED.
- Overtime share: GREEN when actual <= target; otherwise RED.
- Monthly attrition: GREEN when actual <= target; otherwise RED.
- N/A is used when a required target or actual value is unavailable.
- No AMBER band was introduced because the supplied target rules did not specify a tolerance range.

### KPI status results

| KPI | Green | Red | N/A |
|---|---:|---:|---:|
| Attendance rate | 106 | 74 | 0 |
| Overtime share | 177 | 3 | 0 |
| Monthly attrition | 109 | 59 | 12 |

Detailed evidence: `kpi_status.csv` and `kpi_status_summary.csv`

The 12 attrition N/A rows are explained by the metric view's privacy eligibility rule: it includes only months with starting headcount >= 10. D10 has 18 source months; 6 meet the threshold and 12 have starting headcount below 10. These are expected privacy suppressions, not missing source records. Keep them N/A and do not infer a zero attrition rate.

## 8. Task-completion KPI limitation

The supplied task-completion target could not be evaluated at department-month level using the available metric. The existing task-completion metric is at team/sprint grain, while the target table is department/month grain. The task-completion actual and traffic-light status are therefore N/A in this view rather than being inferred or incorrectly joined.

To complete this KPI, define an approved aggregation from team/sprint to department/month, verify the mapping, and then compare the aggregated actual with the target.

## 9. Fairness and interpretation

Budgets may not have been updated after the hiring freeze. Before attributing any variance to departmental decisions, confirm the applicable budget version, hiring assumptions, timing of payroll charges, and whether one-off costs or timing differences explain the result.

Privacy-suppressed departmental values must not be reconstructed or disclosed through this report.

## 10. Evidence checklist

- [x] Budget and KPI target tables loaded
- [x] Payroll variance view created
- [x] KPI status view created
- [x] Three manual variance cases verified
- [x] Department overspend ranking exported
- [x] KPI status and summary exported
- [x] KPI traffic-light rules independently validated across 180 rows; zero mismatches
- [ ] Task-completion KPI aggregation resolved
- [ ] Evidence screenshot captured
- [ ] Final review and commit completed



