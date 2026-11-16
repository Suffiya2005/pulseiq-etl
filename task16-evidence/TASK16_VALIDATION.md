

\# Task 16 – Automated Report Builder and Release Candidate



\## 1. Objective



Build a monthly PDF reporting system using the PulseIQ warehouse and automate report generation.



\## 2. Implementation



\- Created `build\_report.py` to generate monthly management PDF reports.

\- Used Python, Pandas-related project dependencies, PostgreSQL and ReportLab.

\- Connected the report generator to the existing PostgreSQL warehouse.

\- Included reporting month, reporting date range and database data cut-off.

\- Generated executive KPI summaries, financial performance, department workforce overview, department comparisons and methodology notes.

\- Created `run\_monthly\_report.ps1` for local automation.

\- Configured Windows Task Scheduler for monthly execution.



\## 3. Report Contents



The generated PDF contains:



1\. Executive KPI Summary

2\. Financial Performance – Recent Six Months

3\. Department Workforce Overview

4\. Department Comparisons

5\. Data Notes \& Methodology



\## 4. Validation Results



| Test | Result |

|---|---|

| Python syntax validation | PASS |

| PostgreSQL connection | PASS |

| September 2026 PDF generation | PASS |

| October 2026 PDF generation | PASS |

| PDF file verification | PASS |

| PDF text extraction | PASS |

| All five report sections | PASS |

| Windows automation script | PASS |

| Windows Task Scheduler execution | PASS |

| Scheduled task result code | 0 |



\## 5. Automation Schedule



\- Task name: PulseIQ Monthly Report

\- Frequency: Monthly

\- Scheduled day: 1st

\- Scheduled time: 09:00 AM

\- Next scheduled execution: 01 December 2026

\- Automation script: `run\_monthly\_report.ps1`



\## 6. Evidence



\- `pulseiq\_2026-10.pdf` – Generated October 2026 report.



\## 7. GitHub Actions Status



A GitHub Actions workflow configuration was created at:



`.github/workflows/monthly-report.yml`



Remote GitHub Actions execution has not yet been validated. The current working automation uses Windows Task Scheduler and the local Docker PostgreSQL warehouse.



\## 8. Remaining Work



\- Validate execution on a clean computer.

\- Establish a secure remote database access strategy if GitHub-hosted Actions execution is required.

\- Validate the GitHub Actions workflow.

\- Complete release candidate preparation and tag `v1.0.0-rc1`.



\## 9. Conclusion



The monthly PDF report generator and local scheduled automation have been implemented and tested successfully using the existing PulseIQ PostgreSQL warehouse.

| Fresh virtual environment dependency installation | PASS |

| Fresh environment Python syntax validation | PASS |

| Fresh environment PDF generation | PASS |

| PDF page count and five-section validation | PASS |
