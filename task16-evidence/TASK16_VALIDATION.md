# Task 16 – Automated Report Builder and Release Candidate

## 1. Objective

Build a monthly PDF reporting system using the PulseIQ warehouse and automate report generation.

## 2. Implementation

- Created `build_report.py` to generate monthly management PDF reports.
- Used Python, PostgreSQL and ReportLab.
- Connected the report generator to the PulseIQ warehouse.
- Included reporting month, reporting date range and database data cut-off.
- Generated executive KPI summaries, financial performance, department workforce overview, department comparisons and methodology notes.
- Created `run_monthly_report.ps1` for local automation.
- Configured Windows Task Scheduler for monthly execution.
- Migrated the PulseIQ database to Supabase PostgreSQL.
- Configured GitHub Actions for automated monthly PDF generation.

## 3. Report Contents

The generated PDF contains:

1. Executive KPI Summary
2. Financial Performance – Recent Six Months
3. Department Workforce Overview
4. Department Comparisons
5. Data Notes & Methodology

## 4. Validation Results

| Test | Result |
|---|---|
| Python syntax validation | PASS |
| Local PostgreSQL connection | PASS |
| September 2026 PDF generation | PASS |
| October 2026 PDF generation | PASS |
| PDF file verification | PASS |
| PDF text extraction | PASS |
| All five report sections | PASS |
| Windows automation script | PASS |
| Windows Task Scheduler execution | PASS |
| Scheduled task result code | 0 |
| Fresh virtual environment dependency installation | PASS |
| Fresh environment Python syntax validation | PASS |
| Fresh environment PDF generation | PASS |
| Fresh environment PDF page and section validation | PASS |
| Supabase connection | PASS |
| Supabase database migration | PASS |
| Supabase warehouse tables verification | PASS |
| Supabase DQ reference tables verification | PASS |
| Supabase metric views verification | PASS |
| Supabase department records verification | PASS |
| GitHub Actions workflow execution | PASS |
| GitHub Actions PDF generation | PASS |
| GitHub Actions artifact upload | PASS |

### Supabase Migration Verification

| Database object | Verified count |
|---|---:|
| Warehouse base tables | 21 |
| DQ reference base tables | 5 |
| Warehouse views | 52 |
| Metric views | 29 |
| Department records | 11 |

## 5. Automation Schedule

- Task name: PulseIQ Monthly Report
- Frequency: Monthly
- Scheduled day: 1st
- Scheduled time: 09:00 AM
- Next scheduled execution: 01 December 2026
- Automation script: `run_monthly_report.ps1`

## 6. Evidence

- `pulseiq_2026-10.pdf` – Generated October 2026 report.
- GitHub Actions Run #1 – Successful monthly PDF generation.
- `pulseiq-monthly-report` – Uploaded GitHub Actions artifact.
- Supabase migration verification output.
- Fresh environment validation results.

## 7. GitHub Actions Status

GitHub Actions automation has been successfully configured and tested.

Workflow configuration:

`.github/workflows/monthly-report.yml`

Validation results:

- GitHub-hosted runner executed successfully.
- Python environment setup completed.
- Project dependencies installed successfully.
- Supabase database connection succeeded.
- Monthly PDF report generated successfully.
- PDF artifact uploaded successfully.
- Workflow Run #1 completed successfully.

The workflow supports manual execution and monthly scheduled execution.

## 8. Release Candidate Status

- Release tag: `v1.0.0-rc1`
- Release tag pushed to GitHub: YES
- Monthly PDF report generation: PASS
- Supabase cloud database: CONNECTED
- GitHub Actions automation: PASS

## 9. Remaining Work

- Complete validation on a separate physical computer.
- Update this validation document after completing the separate-computer test.

## 10. Conclusion

The PulseIQ monthly PDF report generator, local scheduled automation, Supabase cloud database migration and GitHub Actions automation have been implemented and successfully tested.

The GitHub-hosted workflow successfully generated and uploaded the monthly PDF report.

The remaining validation activity is testing the project on a separate physical computer.

Task 16 is pending final closure until this validation is completed.

## New Department Scenario Test

- Simulated a newly introduced department named New Test Department.
- Verified that load_departments() dynamically retrieves department rows from warehouse.dim_department.
- Verified that LEFT JOIN preserves departments when headcount, payroll and attendance metrics are unavailable.
- Missing metrics were returned as None rather than zero.
- Test result: PASS.
- The test used simulated query results and did not modify the live Supabase database.
