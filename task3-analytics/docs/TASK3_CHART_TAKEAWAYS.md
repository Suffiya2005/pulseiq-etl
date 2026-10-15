\# Task 3 — Headcount \& Departments: Chart Takeaways



\## 1. Current Headcount

The current employee dimension contains 745 distinct current employees, excluding the UNKNOWN placeholder. The latest monthly headcount snapshot for September 2026 is 441. These metrics use different definitions and must not be treated as interchangeable.



\## 2. Monthly Headcount Trend

Headcount increased from 409 in May 2026 to 441 in September 2026, a net increase of 32 employees.



\## 3. Headcount by Department

In September 2026, Engineering had the highest headcount at 167, followed by Customer Support at 59 and Data \& AI at 52. The department totals reconcile to 441.



\## 4. Role Mix

The current employee query shows QA Engineer as the most common role, with 50 employees, followed by Software Engineer (43) and Associate Software Engineer (40).



\## 5. Tenure Bands

Using `hire\_date` from raw employee data and filtering to records marked current and active, the provisional result is: 1–3 years (123), under 1 year (95), 3–5 years (109), and 5+ years (114). The 1–3 years band is the largest. These counts total 441 and need reconciliation with the warehouse's current employee dimension count of 745 before being treated as the final warehouse metric.

\## 6. Monthly Joiners vs Leavers

In September 2026, the warehouse recorded 17 hires and 3 exits.



\## Validation Notes

\- September monthly department totals reconcile to 441.

\- Current employee dimension count is 745; this differs from the September monthly snapshot.

\- Confirm the original joining-date field before publishing tenure as an official metric.

\- Confirm the Superset charts use the same metric definitions as the warehouse.



