# PulseIQ ETL Pipeline

## Project Overview
PulseIQ ETL is a Python-based data engineering project that extracts,
cleans, validates, and transforms employee-related datasets.

The pipeline processes five datasets:
- Employees
- Salary
- Attendance
- Leave
- Payroll

**Important:** The current CSV files contain synthetic sample data
for development and testing. They are not official PulseIQ data.

## Technology Stack
- Python
- Pandas
- Pandera
- PyArrow
- Pytest
- Docker
- Docker Compose

## Project Structure

```text
pulseiq-etl/
--- data/
-   --- raw/
-   --- clean/
--- logs/
--- rejected/
--- src/
-   --- __init__.py
-   --- pipeline.py
-   --- quality_report.py
--- tests/
--- .env.example
--- compose.yaml
--- Dockerfile
--- requirements.txt
--- README.md
```

## ETL Workflow
1. Extract CSV files from `data/raw/`.
2. Clean and validate records.
3. Reject invalid records with rejection reasons.
4. Save cleaned datasets as CSV and Parquet files.
5. Generate execution logs and a JSON summary.
6. Generate a data-quality report.

## Run Locally

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the ETL pipeline:

```bash
python -m src.pipeline
```

Generate the data-quality report:

```bash
python -m src.quality_report
```

Run automated tests:

```bash
python -m pytest -v
```

## Docker

Run the ETL container:

```bash
docker compose run --rm etl
```

## Output Files

- `data/clean/` - cleaned CSV and Parquet datasets
- `rejected/rejected_rows.csv` - rejected records
- `logs/etl.log` - execution logs
- `logs/run_summary.json` - ETL execution summary
- `logs/data_quality_report.csv` - data-quality report

## Current Test Results

The latest verified test run completed with 14 passing tests.

## Future Improvements
- Integrate official PulseIQ datasets when received.
- Add stronger schema and referential-integrity checks.
- Add automated data-quality thresholds.
- Integrate a database or analytics dashboard.
- Add scheduled pipeline execution.

## Task 2 - Analytics Warehouse

The analytics warehouse uses PostgreSQL in Docker Compose. It separates analytical reporting from the ETL file-processing workflow.

### Warehouse Dimensions

- `dim_date` - calendar and reporting periods
- `dim_employee` - employee history, including SCD Type 2 fields
- `dim_department` - department information
- `dim_role` - role and job-level information
- `dim_leave_type` - leave policy categories

### Warehouse Fact Tables

**Attendance source limitation:** The available attendance dataset contains monthly employee summaries, not daily attendance events. Therefore, `fact_attendance_monthly` represents monthly grain. Daily attendance analysis requires a daily-grain source dataset; daily records are not inferred or fabricated.


- `fact_payroll` - payroll measures by payroll item
- `fact_attendance_monthly` - monthly employee attendance
- `fact_leave` - employee leave requests
- `fact_headcount_monthly` - monthly department headcount

### Start PostgreSQL

```bash
docker compose up -d postgres
```

### Load Warehouse Data

Run the existing warehouse loaders from the project root in this order:

```powershell
python .\src\load_date_dimension.py
python .\load_dimensions.py
python .\src\load_employees.py
python -m src.warehouse_loader
python .\src\load_facts.py
python .\src\load_headcount.py
```

The `load_dimensions.py` script also loads the six leave types from the
reference workbook. The separate `src/load_leave_types.py` script does
not need to be run again when using this sequence.

**Employee dimension:** The active loader is `src/load_employees.py`.
It loads employee history from `data/clean/employees.csv`, converts the
source `Y/N` current-version flags to PostgreSQL booleans, and upserts
records using `employee_key`. The `-1` UNKNOWN placeholder is preserved.

### Verify the Warehouse

Run the SQL reconciliation queries:

```bash
docker compose exec -T postgres psql -U pulseiq -d pulseiq_warehouse -f /docker-entrypoint-initdb.d/reconciliation_queries.sql
```

### Streamlit Dashboard

Start the dashboard:

```bash
python -m streamlit run app.py
```

The dashboard contains:
- Overview - project and ETL summary
- Task 1 - ETL - cleaned data and rejected records
- Task 2 - Warehouse - warehouse counts and analytical metrics

### Verified Results

- Automated tests: 14 passed in the latest verified run.
- Latest Docker ETL run: 19,738 input rows, 19,735 clean output rows, 3 rejected rows.
- Warehouse payroll: 7,344 rows.
- Warehouse attendance: 7,343 rows.
- Warehouse leave: 3,439 rows.
- Warehouse headcount: 891 rows.

These results describe the last verified run; rerun the checks before final submission.


### Known Source Data Quality Issue

- Employee `EMP-0001`, key `100001`, is rejected because its validity period (2012-05-03 to 2015-05-13) overlaps the preceding history record (2012-01-19 to 2012-05-12).
- The overlapping dates are present in the original backup source file.
- The source dates have not been changed because a verified correction is unavailable.
- The rejected record is retained in `rejected/employees_rejected.csv` for audit and review.



