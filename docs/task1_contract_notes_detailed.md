# Task 1 — Detailed Data Contract Notes

## Core dataset (employees)

| Column | Data type | Nullable | Allowed values / rules | Description |
|---|---|---|---|---
| employee_key | integer | no | unique, positive integer | employees dataset column |
| employee_id | string | no | non-empty | employees dataset column |
| full_name | string | no | non-empty | employees dataset column |
| gender | string | yes | validate according to declared data type | employees dataset column |
| date_of_birth | date | yes | validate according to declared data type | employees dataset column |
| hire_date | date | no | valid date, not in the future | employees dataset column |
| exit_date | date | yes | blank or valid date on/after hire_date | employees dataset column |
| employment_status | string | no | validate according to declared data type | employees dataset column |
| employment_type | string | yes | validate according to declared data type | employees dataset column |
| department_id | string | yes | validate according to declared data type | employees dataset column |
| role_id | string | yes | validate according to declared data type | employees dataset column |
| role_title | string | yes | validate according to declared data type | employees dataset column |
| job_level | string | yes | validate according to declared data type | employees dataset column |
| manager_id | string | yes | validate according to declared data type | employees dataset column |
| work_location | string | yes | validate according to declared data type | employees dataset column |
| work_mode | string | yes | validate according to declared data type | employees dataset column |
| highest_education | string | yes | validate according to declared data type | employees dataset column |
| valid_from | date | yes | blank or valid date | employees dataset column |
| valid_to | date | yes | blank or valid date on/after valid_from | employees dataset column |
| is_current | char(1) | no | Y or N | employees dataset column |
| change_reason | string | yes | validate according to declared data type | employees dataset column |

## Core dataset (salary)

| Column | Data type | Nullable | Allowed values / rules | Description |
|---|---|---|---|---
| employee_id | string | no | non-empty | salary dataset column |
| salary | decimal(14,2) | no | numeric and non-negative | salary dataset column |
| effective_date | date | no | valid date | salary dataset column |

## Core dataset (leave)

| Column | Data type | Nullable | Allowed values / rules | Description |
|---|---|---|---|---
| leave_request_id | string | no | unique, non-empty | leave dataset column |
| employee_id | string | no | non-empty | leave dataset column |
| employee_key | string | no | required, valid employee dimension key | leave dataset column |
| leave_type_code | string | yes | validate according to declared data type | leave dataset column |
| start_date_key | string | yes | validate according to declared data type | leave dataset column |
| end_date_key | string | yes | validate according to declared data type | leave dataset column |
| start_date | date | no | valid date, not after end_date | leave dataset column |
| end_date | date | no | valid date | leave dataset column |
| days | decimal | no | numeric and non-negative | leave dataset column |
| status | string | no | non-empty | leave dataset column |
| applied_on | date | yes | validate according to declared data type | leave dataset column |
| decided_on | date | yes | validate according to declared data type | leave dataset column |
| approver_id | string | yes | validate according to declared data type | leave dataset column |
| reason | string | yes | validate according to declared data type | leave dataset column |
