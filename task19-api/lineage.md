\# PulseIQ Task 19 — KPI Data Lineage



\## 1. Purpose



This document records the verified data lineage for the five financial KPIs exposed by the PulseIQ Metrics API.



The lineage follows the existing PostgreSQL metric views used by the API and Streamlit dashboard.



\## 2. Overall Architecture



```mermaid

flowchart TD

&#x20;   A\["Financial reference source tables"]

&#x20;   B\["dq\_reference.fact\_ledger"]

&#x20;   C\["dq\_reference.fact\_invoice"]

&#x20;   D\["Warehouse metric views"]

&#x20;   E\["M16 Revenue"]

&#x20;   F\["M17 Net Profit"]

&#x20;   G\["M18 Operating Margin"]

&#x20;   H\["M19 Payroll as % Revenue"]

&#x20;   I\["M20 Days Sales Outstanding"]

&#x20;   J\["Streamlit Dashboard"]

&#x20;   K\["FastAPI Metrics API"]



&#x20;   A --> B

&#x20;   A --> C

&#x20;   B --> D

&#x20;   C --> D

&#x20;   D --> E

&#x20;   D --> F

&#x20;   E --> G

&#x20;   F --> G

&#x20;   E --> H

&#x20;   B --> H

&#x20;   C --> I

&#x20;   L\["warehouse.fact\_headcount\_monthly"] --> I



&#x20;   E --> J

&#x20;   F --> J

&#x20;   G --> J

&#x20;   H --> J

&#x20;   I --> J



&#x20;   E --> K

&#x20;   F --> K

&#x20;   G --> K

&#x20;   H --> K

&#x20;   I --> K

```



\*\*Important:\*\* The upstream ingestion process populating the two `dq\_reference` financial source tables has not yet been verified. The diagram identifies the database objects used by the metric views, not a confirmed ingestion job.



\## 3. Metric-Level Lineage



\### M16 — Revenue



\- Source table: `dq\_reference.fact\_ledger`

\- Source fields:

&#x20; - `record.posting\_period`

&#x20; - `record.signed\_amount\_debit\_positive`

&#x20; - `record.account\_code`

\- Account filter: 4001–4004

\- Aggregation: Negative sum of signed ledger amounts grouped by posting period.

\- Warehouse output: `warehouse.metric\_m16\_revenue`

\- API output: Revenue by reporting period.



\### M17 — Net Profit



\- Source table: `dq\_reference.fact\_ledger`

\- Source fields:

&#x20; - `record.posting\_period`

&#x20; - `record.signed\_amount\_debit\_positive`

&#x20; - `record.account\_code`

\- Account filters: 4000–4999 and 5000–5999

\- Aggregation: Negative sum of signed ledger amounts grouped by posting period.

\- Warehouse output: `warehouse.metric\_m17\_net\_profit`

\- API output: Net profit by reporting period.



\### M18 — Operating Margin



\- Dependencies:

&#x20; - M16 Revenue

&#x20; - M17 Net Profit

\- Formula: Net Profit / Revenue × 100

\- Warehouse output: `warehouse.metric\_m18\_operating\_margin`

\- API output: Operating margin percentage by reporting period.



\### M19 — Payroll as % Revenue



\- Source table: `dq\_reference.fact\_ledger`

\- Additional dependency: M16 Revenue

\- Source fields:

&#x20; - `record.posting\_period`

&#x20; - `record.signed\_amount\_debit\_positive`

&#x20; - `record.account\_code`

\- Payroll account filter: 5001–5005

\- Formula: Payroll ledger cost / Revenue × 100

\- Warehouse output: `warehouse.metric\_m19\_payroll\_as\_revenue\_pct`

\- API output: Payroll as a percentage of revenue.



\### M20 — Days Sales Outstanding



\- Source table: `dq\_reference.fact\_invoice`

\- Additional reporting-date source: `warehouse.fact\_headcount\_monthly`

\- Invoice JSON fields:

&#x20; - `record.status`

&#x20; - `record.client\_id`

&#x20; - `record.invoice\_date`

&#x20; - `record.total\_amount`

&#x20; - `record.balance\_due`

\- Reporting date: Maximum `month\_start\_date` from `warehouse.fact\_headcount\_monthly`, adjusted to month end.

\- Closing receivables: Sum of `balance\_due`, excluding DRAFT and CANCELLED invoices.

\- Last 90-day invoice revenue: Sum of `total\_amount` over the 90-day reporting window, excluding DRAFT and CANCELLED invoices.

\- Formula: 90 × Closing Receivables / Last 90-day Invoice Revenue.

\- Warehouse output: `warehouse.metric\_m20\_days\_sales\_outstanding`

\- API output: Days sales outstanding.



Note: `client\_id` is selected in the source query but is not used in the final DSO aggregation.



\## 4. Warehouse and Application Consumers



The existing metric views are consumed independently by:



1\. \*\*Streamlit dashboard\*\* — reads the configured warehouse metric views.

2\. \*\*FastAPI service\*\* — reads the same configured warehouse metric views through a read-only database connection.



The current architecture does not establish that the Streamlit dashboard calls the FastAPI service.



\## 5. Database Access Controls



The API uses the read-only database account.



Verified permissions:



\- Warehouse schema usage: permitted.

\- SELECT on the five metric views: permitted.

\- INSERT, UPDATE and DELETE on metric views: not permitted.

\- Direct SELECT on `dq\_reference.fact\_ledger`: not permitted.

\- Direct SELECT on `dq\_reference.fact\_invoice`: not permitted.



The API therefore retrieves financial metrics through approved warehouse views without direct access to the underlying financial reference tables.



\## 6. Freshness and Lineage Limitations



Current API freshness status:



\- Pipeline status: `not\_checked`

\- Financial feed status: `unverified`

\- Last refresh: `null`



No verified source-level refresh timestamp is currently available to the API.



The general ETL run summary is not sufficient evidence that the financial reference tables have been refreshed.



\## 7. Verification Status



| Lineage item | Status |

|---|---|

| M16 source and formula | Verified |

| M17 source and formula | Verified |

| M18 dependencies and formula | Verified |

| M19 source and formula | Verified |

| M20 source and formula | Verified |

| Metric views accessible to API account | Verified |

| API and dashboard consume warehouse views | Verified |

| Upstream financial ingestion process | Not verified |

| Financial source refresh timestamp | Not verified |



\## 8. Conclusion



The five financial KPIs are exposed through existing warehouse metric views and authenticated FastAPI endpoints.



The database permissions enforce read-only access. The remaining lineage work is to verify the upstream ingestion process and establish source-level refresh metadata for the financial reference feeds.

