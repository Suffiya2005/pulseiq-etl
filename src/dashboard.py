

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
CLEAN = ROOT / "data" / "clean"
LOGS = ROOT / "logs"

st.set_page_config(
    page_title="PulseIQ | HR Analytics",
    page_icon="📊",
    layout="wide",
)


st.title("📊 PulseIQ HR Analytics Dashboard")
st.caption(
    "DEMONSTRATION — Synthetic sample data, not official PulseIQ data."
)

DATASETS = {
    "Employees": "employees.csv",
    "Salary": "salary.csv",
    "Attendance": "attendance.csv",
    "Leave": "leave.csv",
    "Payroll": "payroll.csv",
}


# --------------------------------------------------
# 1. LOAD CLEANED DATASETS
# --------------------------------------------------
@st.cache_data
def load_data():
    result = {}

    for name, filename in DATASETS.items():
        path = CLEAN / filename

        if path.exists():
            result[name] = pd.read_csv(path)

    return result


data = load_data()

if not data:
    st.error(
        "No cleaned datasets found. Run the ETL pipeline first."
    )
    st.stop()

employees = data.get("Employees", pd.DataFrame())
salary = data.get("Salary", pd.DataFrame())
attendance = data.get("Attendance", pd.DataFrame())
leave = data.get("Leave", pd.DataFrame())
payroll = data.get("Payroll", pd.DataFrame())


# --------------------------------------------------
# 2. SIDEBAR DEPARTMENT FILTER
# --------------------------------------------------
st.sidebar.header("Dashboard Filters")

if not employees.empty and "department" in employees.columns:
    departments = sorted(
        employees["department"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_departments = st.sidebar.multiselect(
        "Department",
        options=departments,
        default=departments,
    )

    filtered_employees = employees[
        employees["department"].isin(selected_departments)
    ].copy()
else:
    filtered_employees = employees.copy()


# --------------------------------------------------
# 3. FILTER RELATED DATASETS BY EMPLOYEE
# --------------------------------------------------
def filter_by_employee(df):
    if (
        "employee_id" in df.columns
        and "employee_id" in filtered_employees.columns
    ):
        return df[
            df["employee_id"].isin(
                filtered_employees["employee_id"]
            )
        ].copy()

    return df.copy()


# --------------------------------------------------
# 4. KPI: HEADCOUNT
# --------------------------------------------------
if "employee_id" in filtered_employees.columns:
    headcount = int(
        filtered_employees["employee_id"].nunique()
    )
else:
    headcount = len(filtered_employees)


# --------------------------------------------------
# 5. KPI: AVERAGE SALARY
# --------------------------------------------------
average_salary = 0.0

if not salary.empty and "salary" in salary.columns:
    salary_view = filter_by_employee(salary)

    salary_values = pd.to_numeric(
        salary_view["salary"],
        errors="coerce",
    ).dropna()

    if not salary_values.empty:
        average_salary = float(salary_values.mean())


# --------------------------------------------------
# 6. KPI: ATTENDANCE RATE
# --------------------------------------------------
attendance_rate = 0.0

if not attendance.empty and "status" in attendance.columns:
    attendance_view = filter_by_employee(attendance)

    statuses = (
        attendance_view["status"]
        .astype("string")
        .str.strip()
        .str.title()
    )

    valid_statuses = statuses.isin(
        ["Present", "Absent", "Leave", "Holiday"]
    )

    denominator = int(valid_statuses.sum())
    present_count = int((statuses == "Present").sum())

    if denominator > 0:
        attendance_rate = (
            present_count / denominator
        ) * 100


# --------------------------------------------------
# 7. KPI: TOTAL LEAVE DAYS
# --------------------------------------------------
leave_days = 0.0

if not leave.empty and "leave_days" in leave.columns:
    leave_view = filter_by_employee(leave)

    leave_values = pd.to_numeric(
        leave_view["leave_days"],
        errors="coerce",
    )

    if leave_values.notna().any():
        leave_days = float(leave_values.sum())


# --------------------------------------------------
# 8. KPI: TOTAL NET PAYROLL
# --------------------------------------------------
net_payroll = 0.0

if not payroll.empty and "net_pay" in payroll.columns:
    payroll_view = filter_by_employee(payroll)

    payroll_values = pd.to_numeric(
        payroll_view["net_pay"],
        errors="coerce",
    )

    if payroll_values.notna().any():
        net_payroll = float(payroll_values.sum())


# --------------------------------------------------
# 9. DISPLAY KPI CARDS
# --------------------------------------------------
c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Headcount", f"{headcount:,}")
c2.metric("Average Salary", f"₹{average_salary:,.0f}")
c3.metric("Attendance Rate", f"{attendance_rate:.1f}%")
c4.metric("Leave Days", f"{leave_days:,.0f}")
c5.metric("Net Payroll", f"₹{net_payroll:,.0f}")

st.divider()


# --------------------------------------------------
# 10. EMPLOYEES BY DEPARTMENT
# --------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("Employees by Department")

    if (
        not filtered_employees.empty
        and "department" in filtered_employees.columns
    ):
        department_counts = (
            filtered_employees["department"]
            .fillna("Unknown")
            .value_counts()
            .rename_axis("Department")
            .to_frame("Employees")
        )

        st.bar_chart(
            department_counts,
            y="Employees",
            horizontal=True,
        )
    else:
        st.info("No employee department data available.")


# --------------------------------------------------
# 11. SALARY BY EMPLOYEE
# --------------------------------------------------
with right:
    st.subheader("Salary by Employee")

    if not salary.empty and "salary" in salary.columns:
        salary_view = filter_by_employee(salary).copy()

        salary_view["salary"] = pd.to_numeric(
            salary_view["salary"],
            errors="coerce",
        )

        salary_view = salary_view.dropna(
            subset=["salary"]
        )

        if not salary_view.empty:
            if "employee_id" in salary_view.columns:
                salary_chart = (
                    salary_view.groupby("employee_id")["salary"]
                    .mean()
                    .sort_index()
                    .to_frame()
                )

                st.bar_chart(
                    salary_chart,
                    y="salary",
                )
            else:
                st.bar_chart(
                    salary_view[["salary"]]
                )
        else:
            st.info(
                "No salary records for the selected department."
            )
    else:
        st.info("Salary dataset is unavailable.")


# 12. MONTHLY PAYROLL TREND
st.divider()
st.subheader("Monthly Payroll Trend")

required_columns = {"payroll_month", "net_pay"}

if (
    not payroll.empty
    and required_columns.issubset(payroll.columns)
):
    payroll_trend = filter_by_employee(payroll).copy()

    payroll_trend["payroll_month"] = pd.to_datetime(
        payroll_trend["payroll_month"],
        errors="coerce",
    )

    payroll_trend["net_pay"] = pd.to_numeric(
        payroll_trend["net_pay"],
        errors="coerce",
    )

    payroll_trend = payroll_trend.dropna(
        subset=["payroll_month", "net_pay"]
    )

    if not payroll_trend.empty:

        # Group payroll records by calendar month
        payroll_trend["month"] = (
            payroll_trend["payroll_month"].dt.to_period("M")
        )

        monthly_totals = (
            payroll_trend.groupby("month")["net_pay"]
            .sum()
            .sort_index()
        )

        # Chronological month labels
        chart_data = pd.DataFrame({
            "Month": monthly_totals.index.to_timestamp(),
            "Net Payroll (₹)": monthly_totals.values,
        })

        # Display chart in chronological order
        st.line_chart(
            chart_data,
            x="Month",
            y="Net Payroll (₹)",
            x_label="Month",
            y_label="Net Payroll (₹)",
        )

        # Monthly payroll totals table
        st.subheader("Monthly Payroll Totals")


        totals_table = pd.DataFrame({
            "Month": monthly_totals.index.strftime("%b %Y"),
            "Net Payroll (₹)": monthly_totals.values,
        })

        totals_table["Net Payroll (₹)"] = (
            totals_table["Net Payroll (₹)"]
            .map(lambda amount: f"₹{amount:,.2f}")
        )

        st.dataframe(
            totals_table,
            use_container_width=True,
            hide_index=True,
        )

        # Download monthly payroll CSV
        monthly_download = pd.DataFrame({
            "month": monthly_totals.index.strftime("%Y-%m"),
            "net_payroll": monthly_totals.values,
        })

        st.download_button(
            label="Download Monthly Payroll CSV",
            data=monthly_download.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="monthly_payroll_summary.csv",
            mime="text/csv",
            key="monthly_payroll_download",
        )

    else:
        st.warning(
            "No valid payroll records found "
            "for the selected department."
        )

else:
    st.warning(
        "Payroll data must contain payroll_month "
        "and net_pay columns."
    )

# Month-over-Month Payroll Comparison
st.divider()
st.subheader("📈 Month-over-Month Payroll Comparison")

if (
    not payroll.empty
    and {"payroll_month", "net_pay"}.issubset(payroll.columns)
):
    comparison = filter_by_employee(payroll).copy()

    comparison["payroll_month"] = pd.to_datetime(
        comparison["payroll_month"],
        errors="coerce",
    )

    comparison["net_pay"] = pd.to_numeric(
        comparison["net_pay"],
        errors="coerce",
    )

    comparison = comparison.dropna(
        subset=["payroll_month", "net_pay"]
    )

    if not comparison.empty:
        comparison["month"] = (
            comparison["payroll_month"].dt.to_period("M")
        )

        monthly = (
            comparison.groupby("month")["net_pay"]
            .sum()
            .sort_index()
        )

        if len(monthly) >= 2:
            current_total = float(monthly.iloc[-1])
            previous_total = float(monthly.iloc[-2])
            difference = current_total - previous_total

            percentage_change = (
                difference / abs(previous_total) * 100
                if previous_total != 0
                else 0.0
            )

            current_month = monthly.index[-1].strftime("%b %Y")
            previous_month = monthly.index[-2].strftime("%b %Y")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                f"Payroll — {current_month}",
                f"₹{current_total:,.2f}",
            )

            col2.metric(
                f"Payroll — {previous_month}",
                f"₹{previous_total:,.2f}",
            )

            col3.metric(
                "Monthly Change",
                f"₹{difference:+,.2f}",
                delta=f"{percentage_change:+.2f}%",
            )

            if difference > 0:
                st.success(
                    f"Payroll increased by ₹{difference:,.2f} "
                    f"({percentage_change:+.2f}%) compared with "
                    f"{previous_month}."
                )
            elif difference < 0:
                st.warning(
                    f"Payroll decreased by ₹{abs(difference):,.2f} "
                    f"({percentage_change:+.2f}%) compared with "
                    f"{previous_month}."
                )
            else:
                st.info("Payroll remained unchanged from the previous month.")

        else:
            st.info(
                "At least two months of payroll data are required "
                "for a month-over-month comparison."
            )
    else:
        st.info("No valid payroll records available for comparison.")
else:
    st.info("Payroll month and net pay columns are required.")


# Data Quality Summary
st.divider()
st.subheader("🧹 Data Quality Summary")

quality_report_path = LOGS / "data_quality_report.csv"
run_summary_path = LOGS / "run_summary.json"

if quality_report_path.exists() and run_summary_path.exists():

    quality_df = pd.read_csv(quality_report_path)

    run_summary = pd.read_json(
        run_summary_path,
        typ="series",
    )

    total_input = int(run_summary.get("total_input", 0))
    total_clean = int(run_summary.get("total_output", 0))
    total_rejected = int(run_summary.get("total_rejected", 0))

    # Input, clean, and rejected record metrics
    q1, q2, q3 = st.columns(3)

    q1.metric("Input Records", f"{total_input:,}")
    q2.metric("Clean Records", f"{total_clean:,}")
    q3.metric("Rejected Records", f"{total_rejected:,}")

    # Data Quality Rate
    quality_percentage = (
        total_clean / total_input * 100
        if total_input > 0
        else 0.0
    )

    st.subheader("Data Quality Rate")
    st.metric("Records Retained", f"{quality_percentage:.1f}%")
    st.progress(quality_percentage / 100)

    st.caption(
        f"{total_clean:,} of {total_input:,} input records "
        "were retained by the ETL pipeline."
    )

    # Quality by dataset
    st.subheader("Quality by Dataset")

    st.dataframe(
        quality_df,
        use_container_width=True,
        hide_index=True,
    )

    # Missing cells chart
    if {"dataset", "missing_cells"}.issubset(quality_df.columns):

        missing_chart = (
            quality_df.set_index("dataset")[["missing_cells"]]
        )

        st.subheader("Missing Values by Dataset")

        st.bar_chart(
            missing_chart,
            y="missing_cells",
        )

else:
    st.info(
        "Quality reports are not available. "
        "Run the ETL pipeline and quality report first."
    )


# --------------------------------------------------
# 13. DATASET EXPLORER
# --------------------------------------------------
st.divider()
st.subheader("Dataset Explorer")

dataset_name = st.selectbox(
    "Choose a dataset",
    options=list(data.keys()),
)

display_df = data[dataset_name].copy()

# Show missing values clearly
display_df = display_df.astype(object).where(
    pd.notna(display_df),
    "Not Available",
)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)

# Download selected dataset
csv_data = data[dataset_name].to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label=f"Download {dataset_name} CSV",
    data=csv_data,
    file_name=f"{dataset_name.lower()}_sample.csv",
    mime="text/csv",
    key="dataset_download",
)


# --------------------------------------------------
# 14. FOOTER
# --------------------------------------------------
st.caption(
    "DEMONSTRATION — Synthetic sample data, not official PulseIQ data. "
    "Attendance rate = Present records / valid attendance records. "
    "Salary is averaged across available salary records. "
    "Monthly payroll = sum of net_pay grouped by calendar month. "
    "Confirm business definitions before using official data."
)
