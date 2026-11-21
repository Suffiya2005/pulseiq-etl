# PulseIQ Task 20 — Release Notes (Draft)

**Release candidate:** v1.0.0  
**Evidence date:** 21 November 2026  
**Status:** Review candidate — not a clean production sign-off

## Included
- 10-slide board pack covering people, cost, cash, teams, AI signals, data quality and governance.
- Task 11–15 validation summaries and Task 20 final DQ report.

## Excluded / not claimed
- Dataset is synthetic/demo data, not official company actuals.
- AI estimated exposure is not confirmed financial loss.
- No historical attrition forecast accuracy claim.
- No cash performance conclusion because verified numeric cash-flow values were not included in the reviewed evidence.
- No department-level payroll cost-reduction recommendation while source reconciliation remains unresolved.
- No claim that external feed freshness or deployment freshness is independently verified.

## Known limitations
- DQ-C01 Payroll equals ledger: 1 critical failure; June 2026 D01 difference ₹18,450.
- DQ-C12 Dimension history overlap: 1 critical failure for EMP-0001.
- DQ-C14 Minimum group size: 1,162 violations across 7,393 reporting groups.
- Warning failures: C05 (4), C07 (1), C08 (1), C09 (20), C10 (2), C11 (5).
- Task 12 screenshot evidence is pending in its validation document.
- Task 15 validation wording conflicts on final Overtime Share navigation retesting.
- 221 AI anomaly signals have no risk estimate.
- Historical attrition forecast error could not be calculated because matching records are unavailable.

## Release decision
Retain as a review candidate. Do not describe the release as fully reconciled or production-ready until critical DQ failures are resolved, reviewed and re-run successfully.

## Final Challenge — improvement documented
Improved ETL payroll cleaning to preserve alphanumeric department IDs and corrected the duplicate check to identify duplicate business records. Updated DQ-C03 to check unique payroll item IDs and DQ-C04 to validate payroll employees against the live employee dimension. Source records were preserved; unresolved issues remain visible rather than being masked.
