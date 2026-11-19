# Task 17 – Public Dashboard Deployment

**Project:** PulseIQ ETL – Workforce Intelligence

**Deployment Platform:** Streamlit Community Cloud

**Live Application:** https://pulseiq-workforce-2026.streamlit.app

**GitHub Repository:** https://github.com/Suffiya2005/pulseiq-etl

**Branch:** master

**Deployment Entry File:** public_dashboard.py

## Implementation Summary

Developed and deployed a separate public-facing workforce analytics dashboard using Streamlit, Pandas and Plotly.

The dashboard includes:
- Executive Overview
- Workforce Analytics
- Attendance Analytics
- About & Methodology

The public application uses sanitized company-wide monthly aggregates and excludes employee-level details and payroll information.

## Validation Results

- Local application testing: Successful
- Headcount reconciliation: Passed
- Public dataset validation: Passed
- GitHub integration: Successful
- Cloud deployment: Successful
- Public access without login: Verified

**Data Coverage:** January 2020 – September 2026 for workforce metrics; April 2025 – September 2026 for attendance metrics.

**Data Classification:** Synthetic demonstration data.

## Conclusion

Task 17 deployment has been completed successfully. The PulseIQ Workforce Intelligence dashboard is publicly accessible through Streamlit Community Cloud and ready for project demonstration and management review.
## Hosting Platform Comparison

The following platforms were evaluated for deploying the PulseIQ Workforce Intelligence dashboard.

| Platform | Free resources and data limits | Sleeping behaviour | Price |
|---|---|---|---|
| Streamlit Community Cloud | Approximately 0.078–2 CPU cores, 690 MB–2.7 GB RAM and up to 50 GB storage. Limits may change. | Free apps may sleep after inactivity and restart when accessed. | Free |
| Render | Free web service: 512 MB RAM and 750 free instance hours per workspace per month. Filesystem is ephemeral. | Sleeps after 15 minutes without inbound traffic; waking can take about one minute. | Free tier; paid web service starts at $7/month |
| Hugging Face Spaces | CPU Basic: 2 vCPU, 16 GB RAM and 50 GB non-persistent disk. | Free CPU Basic Spaces sleep after approximately 48 hours of inactivity. | Free CPU Basic; paid hardware available |

### Selected Hosting Platform: Streamlit Community Cloud

Streamlit Community Cloud was selected for PulseIQ because:

- It directly supports Streamlit applications.
- It integrates with GitHub for deployment and automatic redeployment.
- It provides a public dashboard URL without requiring payment.
- It supports application secrets and environment configuration.
- Its available resources are sufficient for the lightweight, company-wide aggregate dataset used by this demonstration dashboard.

### Data Size and Privacy Decision

The dashboard publishes a small CSV containing monthly company-wide aggregate metrics rather than the complete warehouse.

Employee-level records, department-level records, payroll details, and raw source datasets are excluded from the public dashboard.

This keeps the published dataset small and reduces privacy exposure. The current public CSV is approximately 2.9 KB.

### Scheduled Refresh

A GitHub Actions workflow named `PulseIQ Public Data Refresh` was configured.

- Schedule: First day of every month at 09:15 AM IST.
- Manual execution: Supported through GitHub Actions.
- Data source: Hosted PulseIQ warehouse accessed through GitHub Secrets.
- Output: Updated `public_data/public_monthly_metrics.csv`.
- Publishing: Updated data is committed to the GitHub `master` branch when changes are detected.
- Validation: Headcount reconciliation is checked before publishing.

The workflow was manually tested successfully. The latest verified data cutoff is September 2026, with closing headcount of 441.

### Production Decision

Streamlit Community Cloud was chosen because this project is an educational demonstration and does not require guaranteed enterprise availability. The free hosting option avoids unnecessary payment while providing a publicly accessible dashboard. A paid hosting plan can be considered if future production usage requires guaranteed uptime, higher resources, or persistent infrastructure.
### Mobile Compatibility Testing

The live PulseIQ dashboard was opened successfully using a mobile browser.

The mobile test verified:
- Public application accessibility.
- Dashboard title and landing page.
- Executive Overview navigation.
- Latest reporting month: September 2026.
- Closing headcount: 441.
- Synthetic demonstration data disclaimer.

Evidence: `Task17_Phone_Dashboard.png`

### Final Deployment Verification

- Live URL: https://pulseiq-workforce-2026.streamlit.app
- Hosting: Streamlit Community Cloud
- GitHub branch: master
- Automated refresh: GitHub Actions
- Latest verified data cutoff: September 2026
- Latest closing headcount: 441
- Latest attendance rate: 95.19%
- Mobile browser test: Passed
- Public access test: Passed
- Secrets: Stored in GitHub Secrets