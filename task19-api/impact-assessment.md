\# PulseIQ Task 19 — Raw Column Impact Assessment



\## 1. Purpose



This assessment identifies the impact of raw source field changes on the five financial KPIs exposed through the PulseIQ Metrics API.



The assessment is based on the existing PostgreSQL metric view definitions.



\## 2. Impact Summary



| Source table | Field | Affected metric | Impact |

|---|---|---|---|

| `dq\_reference.fact\_ledger` | `posting\_period` | M16, M17, M18, M19 | Reporting-period grouping and joins may fail |

| `dq\_reference.fact\_ledger` | `account\_code` | M16, M17, M19 | Account filters may fail or return incorrect results |

| `dq\_reference.fact\_ledger` | `signed\_amount\_debit\_positive` | M16, M17, M19 | Financial aggregation may fail or produce incorrect values |

| `dq\_reference.fact\_invoice` | `status` | M20 | Invoice exclusion rules may fail |

| `dq\_reference.fact\_invoice` | `invoice\_date` | M20 | 90-day revenue window may fail |

| `dq\_reference.fact\_invoice` | `total\_amount` | M20 | Revenue denominator may fail |

| `dq\_reference.fact\_invoice` | `balance\_due` | M20 | Closing receivables calculation may fail |

| `dq\_reference.fact\_invoice` | `client\_id` | M20 source CTE | Currently selected but not used in the final aggregate |

| `warehouse.fact\_headcount\_monthly` | `month\_start\_date` | M20 | Reporting date calculation may fail |



\## 3. Detailed Impact Analysis



\### 3.1 Ledger Source Fields



\*\*Source:\*\* `dq\_reference.fact\_ledger`



\#### A. `posting\_period`



Used to group M16 and M17 by reporting period.



Impact:

\- M16 Revenue: direct impact.

\- M17 Net Profit: direct impact.

\- M18 Operating Margin: indirect impact through M16 and M17 period matching.

\- M19 Payroll as % Revenue: direct impact on payroll aggregation and revenue matching.



Potential consequence: missing reporting periods, SQL errors, or incorrect joins.



\#### B. `account\_code`



Used to identify account ranges.



Impact:

\- M16: account codes 4001–4004.

\- M17: account codes 4000–4999 and 5000–5999.

\- M19: payroll account codes 5001–5005.

\- M18: indirect impact through M16 and M17.



Potential consequence: account filtering may fail or include incorrect ledger records.



\#### C. `signed\_amount\_debit\_positive`



Used in signed financial aggregations.



Impact:

\- M16: revenue calculation.

\- M17: net profit calculation.

\- M19: payroll cost calculation.

\- M18: indirect impact through M16 and M17.



Potential consequence: SQL errors or incorrect financial KPI values.



\### 3.2 Invoice Source Fields



\*\*Source:\*\* `dq\_reference.fact\_invoice`



\#### A. `status`



Used to exclude DRAFT and CANCELLED invoices.



Impact: M20.



Potential consequence: incorrect receivables or revenue calculations if invoice status handling changes.



\#### B. `invoice\_date`



Used to select invoice revenue within the last 90 days.



Impact: M20.



Potential consequence: incorrect reporting window or missing invoice records.



\#### C. `total\_amount`



Used to calculate the last 90-day invoice revenue denominator.



Impact: M20.



Potential consequence: incorrect DSO denominator.



\#### D. `balance\_due`



Used to calculate closing receivables.



Impact: M20.



Potential consequence: incorrect outstanding receivables and DSO.



\#### E. `client\_id`



Selected in the source CTE but not used in the final DSO aggregation.



Impact: no direct impact on the current final M20 aggregate based on the inspected view definition.



However, this field may become important if future DSO calculations introduce client-level grouping.



\### 3.3 Reporting Date Dependency



\*\*Source:\*\* `warehouse.fact\_headcount\_monthly`



Field: `month\_start\_date`



Used to determine the latest reporting date for M20.



Potential consequence: M20 reporting date calculation may fail if the field is renamed, removed or changes data type.



\## 4. Risk Classification



| Risk | Severity | Affected metrics |

|---|---|---|

| Ledger period field change | High | M16–M19 |

| Ledger account field change | Critical | M16, M17, M19; M18 indirectly |

| Ledger amount field change | Critical | M16, M17, M19; M18 indirectly |

| Invoice status change | High | M20 |

| Invoice date change | High | M20 |

| Invoice amount change | Critical | M20 |

| Invoice balance change | Critical | M20 |

| Headcount reporting date change | High | M20 |



Severity describes potential business impact, not a measured probability of occurrence.



\## 5. Recommended Change-Control Process



Before changing any source field:



1\. Identify all dependent warehouse views.

2\. Search SQL definitions for references to the affected field.

3\. Update the source mapping or view definition.

4\. Run SQL validation against the affected metric views.

5\. Compare before-and-after metric results.

6\. Test the corresponding FastAPI endpoint.

7\. Verify the Streamlit dashboard.

8\. Record the change and supporting test evidence.

9\. Deploy only after validation.



\## 6. Validation Checklist



\- \[ ] Source schema change identified.

\- \[ ] Dependent metric views identified.

\- \[ ] SQL definitions updated if required.

\- \[ ] M16–M20 affected endpoints tested.

\- \[ ] Metric values compared with the previous version.

\- \[ ] Streamlit dashboard checked.

\- \[ ] Freshness status checked.

\- \[ ] Change documented and approved.



\## 7. Limitations



\- The upstream ingestion process for `dq\_reference.fact\_ledger` and `dq\_reference.fact\_invoice` has not yet been verified.

\- The source tables use JSON record fields, so changes to JSON keys may not be detected through conventional table-column checks.

\- No source-level refresh metadata has been verified.

\- This assessment reflects the current inspected metric view definitions and should be updated when those definitions change.



\## 8. Conclusion



Changes to the ledger source fields can affect M16–M19, while invoice and reporting-date field changes can affect M20.



A controlled schema-change process, SQL validation, API testing and dashboard verification are required to protect financial KPI accuracy.

