# PulseIQ Dashboard Style Guide

## 1. Purpose
Provide a consistent, readable, and accessible style for PulseIQ HR Analytics dashboards.

## 2. Colour Palette
- Navy — `#16324F`: dashboard header and primary headings.
- Blue — `#0072B2`: primary data series.
- Teal — `#009E73`: positive metrics and supporting data.
- Amber — `#E69F00`: highlights and attention points.

Use sufficient contrast. Do not communicate meaning through colour alone; include labels or legends.

## 3. Typography
- Use Inter or another clean sans-serif font.
- Keep chart titles short and descriptive.
- Use consistent font sizes and readable axis labels.

## 4. Dashboard Layout
- Place the dashboard title at the top.
- Place department and date filters near the top or in a left-side filter area.
- Show KPI cards before detailed charts.
- Arrange trend charts and department comparisons below the KPIs.
- Avoid unnecessary decoration and duplicated charts.

## 5. Number and Date Formats
- Headcount: whole numbers with thousands separators.
- Salary and payroll: consistent currency formatting.
- Percentages: one decimal place.
- Dates: `MMM YYYY` for monthly reporting.

## 6. Chart Standards
Every chart must have:
- A clear, descriptive title.
- A one-line takeaway supported by actual warehouse data.
- Readable labels and an appropriate legend.
- A suitable chart type for the data.

## 7. Data Accuracy
- Use the PostgreSQL warehouse as the reporting source.
- Apply date filters consistently.
- Validate dashboard totals against warehouse SQL queries.
- Clearly identify the latest reporting month.
- Do not present illustrative mockup values as actual results.
- Do not label SCD record dates as employee hire dates without verification.

## 8. Accessibility
- Use a colour-blind-conscious palette.
- Maintain readable contrast and font sizes.
- Use labels and legends in addition to colours.
- Keep layouts consistent and uncluttered.

## 9. Dashboard Review Checklist
- [ ] KPI values reconcile with warehouse queries.
- [ ] Department and date filters work correctly.
- [ ] Every chart has a title and a data-supported takeaway.
- [ ] Number and date formats are consistent.
- [ ] Dashboard export YAML is saved under `dashboards/`.
