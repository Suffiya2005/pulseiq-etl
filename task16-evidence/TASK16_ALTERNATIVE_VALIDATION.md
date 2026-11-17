# Task 16 – Alternative Validation Evidence

## 1. Objective

The objective of this validation is to demonstrate that the PulseIQ monthly report generation system works in a fresh Python environment, connects to the cloud warehouse, and generates a valid monthly PDF report.

A separate physical computer was not available for this test. Therefore, a fresh-environment validation was performed on the original development computer as an alternative.

## 2. Test Environment

| Component | Version / Details |
|---|---|
| Operating System | Windows |
| Git | 2.51.0 |
| Python | 3.14.3 |
| Python Environment | Fresh virtual environment |
| Environment Name | .venv_task16_test |
| Repository | pulseiq-etl |
| Repository Branch | master |
| Latest Tested Commit | 2c5ff5b |

## 3. Fresh Environment Validation

The project was tested using a newly created Python virtual environment.

Validation performed:

- Created a new virtual environment.
- Activated the environment successfully.
- Installed dependencies using requirements.txt.
- Verified dependency health using pip check.
- Confirmed that no broken requirements were found.
- Verified Python syntax using py_compile.

**Result: PASS**

## 4. Supabase Cloud Database Validation

The fresh environment was configured with the required warehouse environment variables.

The following variables were verified:

- WAREHOUSE_HOST
- WAREHOUSE_PORT
- WAREHOUSE_DB
- WAREHOUSE_USER
- WAREHOUSE_PASSWORD

The application successfully connected to the Supabase cloud database.

Verified database: pulseiq_warehouse

**Result: PASS**

## 5. Monthly PDF Report Generation

Executed:

`python build_report.py --month 2026-10`

Generated report:

`reports/pulseiq_2026-10.pdf`

Validation results:

| Check | Result |
|---|---|
| Report generation | PASS |
| PDF file existence | PASS |
| PDF file size | 7,056 bytes |
| PDF opens successfully | PASS |
| PDF page count | 4 |

## 6. Report Content Validation

All five required report sections were verified using pypdf.

| Required Section | Result |
|---|---|
| Executive KPI Summary | PASS |
| Financial Performance | PASS |
| Department Workforce Overview | PASS |
| Department Comparisons | PASS |
| Data Notes & Methodology | PASS |

**Result: PASS**

## 7. GitHub Actions Validation

The GitHub Actions workflow was previously executed successfully.

Verified activities:

- Repository checkout.
- Python setup.
- Dependency installation.
- Supabase warehouse connection.
- Monthly PDF report generation.
- PDF artifact upload.

Workflow: PulseIQ Monthly PDF Report

Artifact: pulseiq-monthly-report

**Result: PASS**

## 8. Physical Computer Test Limitation

A second physical computer was not available during this validation.

The fresh-environment test was performed on the original development computer. Therefore, this test does not constitute a separate physical computer validation.

The successful GitHub Actions execution provides additional evidence of execution in a separate hosted Ubuntu environment, but it is not represented as a second physical computer test.

A physical second-computer test remains subject to availability and evaluator requirements.

## 9. Final Validation Summary

| Validation | Status |
|---|---|
| Fresh Python environment | PASS |
| Dependency installation | PASS |
| Dependency health | PASS |
| Python syntax validation | PASS |
| Supabase connection | PASS |
| Monthly PDF generation | PASS |
| PDF integrity | PASS |
| Five report sections | PASS |
| GitHub Actions automation | PASS |
| Separate physical computer | NOT PERFORMED |

## 10. Conclusion

The PulseIQ monthly report builder was successfully validated in a fresh Python environment.

The cloud database connection, dependency installation, PDF generation, PDF integrity, report sections, and GitHub Actions automation all passed their respective checks.

The separate physical computer test was not performed because another physical device was unavailable.

This document records the alternative validation evidence transparently. Any substitution for a mandatory second-computer test remains subject to evaluator approval.