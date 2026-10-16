# Task 4 — Attendance Trends Analysis

## 1. Key Findings

### Finding 1: Attendance varies across months
The monthly attendance query shows rates including 93.46% in May 2025, 95.51% in July 2025, 95.48% in September 2025, and 93.71% in December 2025.

**Meaning:** Attendance is not constant across reporting periods.

**HR action:** Review months with lower attendance alongside leave records, holidays, staffing requirements, and operational schedules before deciding whether intervention is needed.

### Finding 2: Attendance differs by department
The department analysis recorded 95.00% attendance for Data & AI and Sales, while HR recorded 92.51%.

**Meaning:** Department-level attendance patterns differ, although these figures alone do not establish the reasons.

**HR action:** Review leave coverage, scheduling, workload, and the attendance recording process with the departments concerned. Confirm the full department ranking before identifying the overall lowest department.

### Finding 3: Attendance anomalies need investigation
The `attendance_monthly_features` subset contains 221 flagged employee-month records covering 18 months and 159 distinct employees. The monthly anomaly chart peaks at approximately 22 flagged records in July 2026.

**Meaning:** The anomaly sample identifies records for review; it does not prove misconduct or a confirmed attendance problem.

**HR action:** Check the flagged records and their reason codes against attendance and leave records. Validate possible missing attendance data before taking action.

## 2. Leave Pattern
Earned (Privilege) Leave accounts for 2,611 days, Casual Leave 2,226 days, and Sick Leave 1,960 days in the available leave summary.

HR should review leave coverage and staffing plans while considering headcount, eligibility, and the period covered.

## 3. Data Limitations
- The attendance source is aggregated by employee and month. It does not contain daily attendance observations, so a reliable weekday-level attendance analysis cannot be calculated.
- The anomaly sample contains employee-month flags, not individual flagged days.
- The analysis uses sample project data and should not be treated as verified real-world PulseIQ workforce results.
- Monthly differences and anomaly scores indicate patterns for investigation; they do not establish causes.
- Department comparisons should be interpreted alongside employee counts and reporting-period coverage.

## 4. Overall Recommendation
Use the dashboard to identify months, departments, and employee-month records requiring review. Validate the underlying records and operational context before taking HR action.
## 5. Weekday Attendance — Synthetic Demo Only

A separate synthetic daily attendance dataset was created to
demonstrate weekday-level analysis because the supplied
attendance data contains monthly summaries rather than daily logs.

Demo results:
- Monday: 90.48%
- Tuesday: 95.87%
- Wednesday: 95.56%
- Thursday: 93.85%
- Friday: 91.06%

These values are generated from simulated attendance probabilities.
They are not actual PulseIQ workforce findings and must not be used
to make HR decisions.

The real weekday attendance requirement remains dependent on
obtaining genuine or officially provided daily-level sample data.