\# Task 1 — Data Contract Notes



\## 1. Employees Table



\- \*\*Purpose:\*\* Stores employee identity, department, role, employment dates, and status.

\- \*\*Data types:\*\* Employee keys use integer values; identifiers and names use text; employment dates use date values; status fields use text or Boolean-style values as specified in the contract.

\- \*\*Nullable rules:\*\* Fields marked `nullable = no` must not be blank. Fields marked `nullable = yes` may be blank.

\- \*\*Allowed values and validation:\*\*

&#x20; - Employee key must be a positive integer and should be unique where required by the contract.

&#x20; - Employee identifiers and names must not be blank when required.

&#x20; - `is\_current` must contain `Y` or `N`.

&#x20; - Dates must be valid dates.

&#x20; - Hire date must not be later than exit date when both dates are present.

\- \*\*Invalid records:\*\* Quarantine records that fail validation and record the reason. Do not silently remove duplicates or change source data.



\## 2. Salary Table



\- \*\*Purpose:\*\* Stores employee salary information and its effective date.

\- \*\*Data types:\*\* Salary amounts use decimal/numeric values; employee identifiers use the types specified in the contract; effective dates use date values.

\- \*\*Nullable rules:\*\* Required fields must not be blank. Optional fields may be blank only when the contract allows it.

\- \*\*Allowed values and validation:\*\*

&#x20; - Salary amounts must be numeric and non-negative.

&#x20; - Effective dates must be valid dates.

&#x20; - Employee references must correspond to valid employee records where referential validation is required.

&#x20; - Duplicate records must be checked against the contract's uniqueness rules.

\- \*\*Invalid records:\*\* Quarantine invalid rows with a clear reason. Keep the original CSV unchanged.



\## 3. Leave Table



\- \*\*Purpose:\*\* Records employee leave requests, leave dates, leave types, and approval status.

\- \*\*Data types:\*\* Identifiers and status values use text; leave dates use date values; leave duration uses numeric values where specified.

\- \*\*Nullable rules:\*\* Apply the `nullable` setting for each column in `data\_contracts.csv`.

\- \*\*Allowed values and validation:\*\*

&#x20; - Leave dates must be valid dates.

&#x20; - Start date must not be later than end date.

&#x20; - Leave duration must be non-negative where applicable.

&#x20; - Leave type and approval status must follow the values defined in the contract.

&#x20; - Employee references must be valid where required.

\- \*\*Invalid records:\*\* Quarantine records with validation failures and preserve their rejection reasons.



\## Unexpected Columns



Unexpected columns should not be silently discarded. Compare every incoming column with the approved data contract. If an unexpected column appears, flag it for review and report it to the data owner. Update the contract only after the column's meaning and data type are approved. This protects downstream tables and prevents unreviewed schema changes.



\## Validation Scope



The contract-validation script checks column matching, required nonblank values, numeric and date parsing, `Y`/`N` values, and applicable non-negative decimal values. These are basic checks, not a complete implementation of every business rule in the contract. Additional uniqueness, referential, allowed-value, and cross-column checks must be verified separately.



\## Data Protection



Raw CSV files remain unchanged. Invalid rows are recorded in quarantine outputs with rejection reasons. Pipeline runs should be repeatable and produce consistent row counts.



