\# Task 3 — Data Quality Checks Catalog



\## Objective

Document the 14 automated data quality checks in plain English, including what can go wrong and the expected action.



| Check ID | Check name | What can go wrong? | Why it matters |

|---|---|---|---|

| DQ-C01 | Payroll equals ledger | Payroll totals do not match the corresponding ledger amounts. | Financial reports may show incorrect payroll costs. |

| DQ-C02 | Ledger balanced | Total debit and credit amounts do not balance. | The financial ledger may be incomplete or incorrect. |

| DQ-C03 | Unique payroll rows | The same employee has duplicate payroll rows for the same period. | Payroll totals can be counted twice. |

| DQ-C04 | No orphan employees | Payroll references an employee ID that does not exist in the employee dimension. | Payroll records cannot be reliably linked to employees. |

| DQ-C05 | No attendance after exit | Attendance exists after an employee's permitted employment period. | Headcount and attendance metrics may be inaccurate. |

| DQ-C06 | Unpaid leave deducted | Recorded unpaid absences exceed payroll loss-of-pay days beyond the allowed tolerance. | Employees may be paid incorrectly. |

| DQ-C07 | Invoice arithmetic | An invoice is overpaid or its balance becomes negative beyond the allowed tolerance. | Receivables and invoice balances may be wrong. |

| DQ-C08 | Expense arithmetic | Expense amount plus tax does not equal the recorded total. | Expense and tax reporting may be inaccurate. |

| DQ-C09 | Task dates sensible | A task is completed before it starts, or marked Done without a completion date. | Delivery and cycle-time metrics become unreliable. |

| DQ-C10 | Leave dates sensible | A leave end date occurs before its start date. | Leave balances and attendance reporting may be wrong. |

| DQ-C11 | AI feeds are fresh | An attrition-risk prediction is missing its date or is too old. | Users may rely on outdated risk predictions. |

| DQ-C12 | Dimension history does not overlap | Historical employee validity periods overlap. | Fact records can join to multiple employee versions and inflate metrics. |

| DQ-C13 | Pipeline freshness | The ETL run summary is missing, invalid, or too old according to the configured rule. | Dashboards may use stale data. |

| DQ-C14 | Minimum group size | A reporting group has fewer records than the configured minimum. | Small groups may produce unreliable or privacy-sensitive reports. |



\## Important note

A FAIL means a data quality problem was detected; it does not necessarily mean the gatekeeper script crashed. A PASS means the configured rule found no bad rows. Every check must be tested using a known bad record in a disposable test copy.





