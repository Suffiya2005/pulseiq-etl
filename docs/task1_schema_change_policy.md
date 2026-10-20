\# Task 1 — Unexpected Column and Schema Change Policy



\## Objective



Define how the ETL pipeline should handle columns that are not defined in the approved data contract.



\## Policy



1\. \*\*Detect:\*\* Compare incoming CSV column names with the approved contract before processing.

2\. \*\*Flag:\*\* If an unexpected column is found, record the column name and dataset in the validation report.

3\. \*\*Review:\*\* Notify the data owner and confirm the column's meaning, data type, and business purpose.

4\. \*\*Approve:\*\* Add the new column to the contract only after the data owner approves the change.

5\. \*\*Validate:\*\* Update the pipeline and tests to validate the new column before accepting it.

6\. \*\*Protect data:\*\* Do not silently discard unexpected columns or modify the original raw CSV.

7\. \*\*Quarantine or hold:\*\* For a strict schema, hold the affected file or batch for review until the change is approved. Do not silently load an unapproved schema into downstream tables.



\## Reason



Unexpected columns may indicate an upstream schema change, a renamed field, or an accidental data export. Silently ignoring them can cause data loss, while accepting them without validation can introduce incorrect data into downstream analytics.



A review-and-approval process protects data quality and keeps the ETL pipeline predictable.



\## Current Implementation Note



The `validate\_contracts.py` script reports column mismatches between raw CSV files and their contracts. The current script is a basic validation report; it does not automatically stop the ETL pipeline when an unexpected column is found.



The strict hold-or-quarantine behavior described above is the recommended policy and must be implemented and tested before claiming that the pipeline enforces it automatically.



\## Test Evidence to Add



\- Test with an unexpected column.

\- Confirm that the column mismatch is detected.

\- Confirm that the raw source file remains unchanged.

\- If strict enforcement is implemented, confirm that the affected batch is held or rejected before loading.



