import json
import os
import re
from pathlib import Path

import pandas as pd
import psycopg
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.example", override=False)

st.set_page_config(
    page_title="PulseIQ Analytics",
    page_icon="📊",
    layout="wide",
)

st.title("PulseIQ Analytics Dashboard")
st.caption(
    "Task 1 — ETL Pipeline | Task 2 — Analytics Warehouse | "
    "Task 3 — Analytics | Task 4 — Attendance Trends"
)

page = st.sidebar.radio(
    "Select Dashboard",
    [
        "Overview",
        "Task 1 - ETL",
        "Task 2 - Warehouse",
        "Task 3 - Analytics",
        "Task 4 - Attendance Trends Analysis",
        "Task 5 - Workforce & Headcount",
    ],
)

CLEAN_DIR = ROOT / os.getenv("CLEAN_DATA_DIR", "data/clean")
REJECTED_DIR = ROOT / os.getenv("REJECTED_DIR", "rejected")
SUMMARY_PATH = ROOT / os.getenv("LOG_DIR", "logs") / "run_summary.json"


def get_connection():
    return psycopg.connect(
        host=os.getenv("WAREHOUSE_HOST", "localhost"),
        port=int(os.getenv("WAREHOUSE_PORT", "5433")),
        dbname=os.getenv("WAREHOUSE_DB", "pulseiq_warehouse"),
        user=os.getenv("WAREHOUSE_USER", "pulseiq"),
        password=os.getenv("WAREHOUSE_PASSWORD", ""),
        connect_timeout=5,
    )


def warehouse_query(query):
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


def normalize_columns(frame):
    frame = frame.copy()
    frame.columns = [
        re.sub(
            r"[^a-z0-9]+",
            "_",
            str(column).strip().lower(),
        ).strip("_")
        for column in frame.columns
    ]
    return frame


def read_csv_safely(path):
    if not path.exists():
        return None

    try:
        return normalize_columns(pd.read_csv(path))
    except Exception as exc:
        st.warning(f"Could not read {path.name}: {exc}")
        return None


def find_column(frame, candidates, require_values=False):
    if frame is None:
        return None

    for candidate in candidates:
        if candidate in frame.columns:
            if not require_values or frame[candidate].notna().any():
                return candidate

    return None


def numeric_column(frame, column):
    return pd.to_numeric(frame[column], errors="coerce").fillna(0)


# ============================================================
# OVERVIEW
# ============================================================

if page == "Overview":
    st.subheader("Project Overview")
    st.write(
        "Explore the PulseIQ ETL pipeline, analytics warehouse, "
        "headcount dashboard, and attendance analysis."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Task 1 — ETL Pipeline")
        st.write(
            "Clean and validate data, preview cleaned files, "
            "and review rejected records."
        )

        clean_files = (
            list(CLEAN_DIR.glob("*.csv"))
            if CLEAN_DIR.exists()
            else []
        )

        st.metric("Clean CSV datasets", len(clean_files))

    with col2:
        st.markdown("### Task 2 — Analytics Warehouse")
        st.write(
            "Explore PostgreSQL dimensions, fact tables, "
            "and business metrics."
        )

        try:
            result = warehouse_query(
                "SELECT COUNT(*) AS total "
                "FROM warehouse.fact_payroll"
            )
            st.metric(
                "Payroll records",
                f"{int(result.iloc[0]['total']):,}",
            )
            st.success("PostgreSQL connection successful")

        except Exception:
            st.warning(
                "Warehouse unavailable. Check Docker PostgreSQL "
                "and WAREHOUSE_* settings."
            )

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("### Task 3 — Analytics Dashboard")
        st.write(
            "Explore headcount trends, departments, role mix, "
            "joiners, leavers, and tenure."
        )
        st.link_button(
            "Open Superset",
            "http://localhost:8088",
        )

    with col4:
        st.markdown("### Task 4 — Attendance Trends Analysis")
        st.write(
            "Analyze attendance and leave patterns, compare departments, "
            "and review trends, late arrivals, and AI/ML anomalies."
        )
        st.markdown(
            "- Monthly attendance trend and 3-month rolling average\n"
            "- Department-wise attendance comparison\n"
            "- Leave days by type\n"
            "- Monthly late-arrival trend\n"
            "- AI/ML anomaly chart\n"
            "- Weekday attendance trend (synthetic demo only)"
        )
        st.info(
            "Select Task 4 - Attendance Trends Analysis in the sidebar "
            "to open the detailed dashboard."
        )
    if SUMMARY_PATH.exists():
        st.subheader("Latest ETL Run")

        try:
            st.json(
                json.loads(
                    SUMMARY_PATH.read_text(encoding="utf-8")
                )
            )
        except (json.JSONDecodeError, OSError):
            st.warning("Could not read the ETL run summary.")


# ============================================================
# TASK 1 — ETL
# ============================================================

elif page == "Task 1 - ETL":
    st.subheader("ETL Pipeline Dashboard")

    if SUMMARY_PATH.exists():
        try:
            st.markdown("### Latest ETL Run")
            st.json(
                json.loads(
                    SUMMARY_PATH.read_text(encoding="utf-8")
                )
            )
        except (json.JSONDecodeError, OSError):
            st.error("Could not read the ETL summary.")
    else:
        st.info(
            "Run the ETL pipeline first to generate the summary."
        )

    st.markdown("### Clean Data Preview")

    if CLEAN_DIR.exists():
        csv_files = sorted(CLEAN_DIR.glob("*.csv"))

        if csv_files:
            selected = st.selectbox(
                "Select clean dataset",
                csv_files,
                format_func=lambda path: path.name,
            )

            try:
                dataframe = pd.read_csv(selected)

                col1, col2 = st.columns(2)
                col1.metric("Rows", f"{len(dataframe):,}")
                col2.metric("Columns", len(dataframe.columns))

                st.dataframe(
                    dataframe.head(100),
                    use_container_width=True,
                )

                st.download_button(
                    "Download selected CSV",
                    data=selected.read_bytes(),
                    file_name=selected.name,
                    mime="text/csv",
                )

            except Exception as exc:
                st.error(f"Could not read dataset: {exc}")
        else:
            st.info("No cleaned CSV files found.")
    else:
        st.info("Clean data folder has not been created yet.")

    st.markdown("### Rejected Data")

    if REJECTED_DIR.exists():
        rejected_files = sorted(
            REJECTED_DIR.glob("*.csv")
        )

        if rejected_files:
            selected_reject = st.selectbox(
                "Select rejected file",
                rejected_files,
                format_func=lambda path: path.name,
            )

            try:
                rejected_dataframe = pd.read_csv(selected_reject)
                st.metric(
                    "Rejected rows",
                    f"{len(rejected_dataframe):,}",
                )
                st.dataframe(
                    rejected_dataframe.head(100),
                    use_container_width=True,
                )
            except Exception as exc:
                st.error(f"Could not read rejected file: {exc}")
        else:
            st.info("No rejected CSV files found.")
    else:
        st.info("Rejected data folder has not been created yet.")


# ============================================================
# TASK 2 — ANALYTICS WAREHOUSE
# ============================================================

elif page == "Task 2 - Warehouse":
    st.subheader("PostgreSQL Analytics Warehouse")

    table_options = [
        "dim_date",
        "dim_department",
        "dim_role",
        "dim_employee",
        "dim_leave_type",
        "fact_payroll",
        "fact_attendance_monthly",
        "fact_leave",
        "fact_headcount_monthly",
    ]

    try:
        count_frames = []

        with get_connection() as connection:
            with connection.cursor() as cursor:
                for table in table_options:
                    cursor.execute(
                        f"SELECT COUNT(*) FROM warehouse.{table}"
                    )
                    count_frames.append(
                        {
                            "Table": table,
                            "Rows": cursor.fetchone()[0],
                        }
                    )

        st.markdown("### Warehouse Table Counts")
        st.dataframe(
            pd.DataFrame(count_frames),
            use_container_width=True,
            hide_index=True,
        )

        payroll = warehouse_query(
            """
            SELECT
                COUNT(*) AS payroll_rows,
                COUNT(DISTINCT employee_id) AS employees,
                COALESCE(SUM(gross_pay), 0) AS gross_pay,
                COALESCE(SUM(net_pay), 0) AS net_pay
            FROM warehouse.fact_payroll
            """
        )

        st.markdown("### Payroll KPIs")
        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Payroll Records",
            f"{int(payroll.iloc[0]['payroll_rows']):,}",
        )
        col2.metric(
            "Employees",
            f"{int(payroll.iloc[0]['employees']):,}",
        )
        col3.metric(
            "Gross Pay",
            f"₹{float(payroll.iloc[0]['gross_pay']):,.2f}",
        )
        col4.metric(
            "Net Pay",
            f"₹{float(payroll.iloc[0]['net_pay']):,.2f}",
        )

        attendance = warehouse_query(
            """
            SELECT
                COUNT(*) AS records,
                ROUND(AVG(attendance_rate)::numeric, 4) AS avg_rate
            FROM warehouse.fact_attendance_monthly
            """
        )

        st.markdown("### Attendance")
        col1, col2 = st.columns(2)

        col1.metric(
            "Attendance Records",
            f"{int(attendance.iloc[0]['records']):,}",
        )

        average_rate = attendance.iloc[0]["avg_rate"]
        col2.metric(
            "Average Attendance Rate",
            "N/A"
            if pd.isna(average_rate)
            else f"{float(average_rate) * 100:.2f}%",
        )

        leave = warehouse_query(
            """
            SELECT
                COUNT(*) AS records,
                COALESCE(SUM(days), 0) AS leave_days
            FROM warehouse.fact_leave
            """
        )

        st.markdown("### Leave")
        col1, col2 = st.columns(2)

        col1.metric(
            "Leave Requests",
            f"{int(leave.iloc[0]['records']):,}",
        )
        col2.metric(
            "Total Leave Days",
            f"{float(leave.iloc[0]['leave_days']):,.2f}",
        )

        headcount = warehouse_query(
            """
            SELECT
                COUNT(*) AS records,
                COALESCE(SUM(headcount_end), 0) AS headcount_end
            FROM warehouse.fact_headcount_monthly
            """
        )

        st.markdown("### Headcount")
        col1, col2 = st.columns(2)

        col1.metric(
            "Monthly Department Records",
            f"{int(headcount.iloc[0]['records']):,}",
        )
        col2.metric(
            "Sum of Monthly Ending Headcount",
            f"{int(headcount.iloc[0]['headcount_end']):,}",
        )

        st.markdown("### Explore Warehouse Table")
        selected_table = st.selectbox(
            "Select table",
            table_options,
        )

        preview = warehouse_query(
            f"SELECT * FROM warehouse.{selected_table} LIMIT 100"
        )

        st.dataframe(
            preview,
            use_container_width=True,
        )

        st.download_button(
            "Download table preview as CSV",
            data=preview.to_csv(index=False).encode("utf-8"),
            file_name=f"{selected_table}_preview.csv",
            mime="text/csv",
        )

    except Exception as exc:
        st.error(
            "Warehouse query failed. Check PostgreSQL is running "
            "and WAREHOUSE_* settings are correct."
        )
        st.caption(str(exc))


# ============================================================
# TASK 3 — ANALYTICS
# ============================================================

elif page == "Task 3 - Analytics":
    st.subheader("Task 3 — Superset Analytics")
    st.write(
        "Open the interactive Superset dashboard to use "
        "department filters and explore saved charts."
    )

    st.link_button(
        "Open PulseIQ Superset",
        "http://localhost:8088",
    )

    st.markdown("### Included analytics")
    st.markdown(
        "- Monthly headcount trend\n"
        "- Headcount by department\n"
        "- Role mix\n"
        "- Monthly joiners vs leavers\n"
        "- Current headcount KPI\n"
        "- Department-wise tenure distribution"
    )

    st.info(
        "Superset opens separately; the interactive charts are "
        "linked here rather than embedded inside Streamlit."
    )


# ============================================================
# TASK 4 — ATTENDANCE TRENDS ANALYSIS
# ============================================================

elif page == "Task 4 - Attendance Trends Analysis":
    st.subheader("Task 4 — Attendance Trends Analysis")
    st.caption(
        "Monthly attendance, department comparisons, leave, late arrivals, "
        "AI/ML anomalies, and a clearly labelled synthetic weekday demo."
    )

    task4_dir = ROOT / "task4-attendance"
    task4_note = task4_dir / "docs" / "TASK4_ATTENDANCE_INSIGHTS.md"
    demo_candidates = [
        task4_dir / "data" / "attendance_daily_sample.csv",
        ROOT / "data" / "reference" / "attendance_daily_sample.csv",
    ]
    demo_path = next((path for path in demo_candidates if path.exists()), None)
    anomaly_path = (
        ROOT / "data" / "reference" / "03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"
    )

    attendance_path = CLEAN_DIR / "attendance.csv"
    employees_path = CLEAN_DIR / "employees.csv"
    leave_path = CLEAN_DIR / "leave.csv"
    attendance_df = read_csv_safely(attendance_path)
    employees_df = read_csv_safely(employees_path)
    leave_df = read_csv_safely(leave_path)

    if attendance_df is None or attendance_df.empty:
        st.error(
            f"Clean attendance data was not found or is empty at {attendance_path}. "
            "Run the ETL pipeline first."
        )
    else:
        date_column = find_column(
            attendance_df, ["period_end_date", "attendance_date", "date"], require_values=True
        )
        scheduled_column = find_column(attendance_df, ["scheduled_days", "scheduled"])
        present_column = find_column(attendance_df, ["present_days", "present"])
        half_column = find_column(attendance_df, ["half_days_unpaid"])
        late_column = find_column(attendance_df, ["late_arrivals", "late_arrival"])

        if not date_column or not scheduled_column or not present_column:
            st.error(
                "Attendance data needs date, scheduled-days, and present-days columns. "
                "Detected columns: " + ", ".join(attendance_df.columns)
            )
        else:
            attendance_df[date_column] = pd.to_datetime(attendance_df[date_column], errors="coerce")
            attendance_df = attendance_df.dropna(subset=[date_column]).copy()
            attendance_df["_scheduled"] = numeric_column(attendance_df, scheduled_column)
            attendance_df["_present"] = numeric_column(attendance_df, present_column)
            attendance_df["_half"] = numeric_column(attendance_df, half_column) if half_column else 0
            attendance_df["_late"] = numeric_column(attendance_df, late_column) if late_column else 0
            attendance_df["_attendance_numerator"] = attendance_df["_present"] + 0.5 * attendance_df["_half"]
            attendance_df["_month"] = attendance_df[date_column].dt.to_period("M").dt.to_timestamp()

            # Resolve department names from attendance values first, then join employees.
            department_names = {
                "D00": "Executive Office", "D01": "Engineering", "D02": "Product & Design",
                "D03": "Data & AI", "D04": "Sales", "D05": "Marketing",
                "D06": "Customer Support", "D07": "Human Resources", "D08": "Finance & Accounts",
                "D09": "Operations & IT", "D10": "Legal & Compliance",
            }
            attendance_df["_department_name"] = pd.NA
            direct_name_col = find_column(attendance_df, ["department_name", "department", "dept_name"], require_values=True)
            if direct_name_col:
                attendance_df["_department_name"] = attendance_df[direct_name_col].astype("string").str.strip()
            else:
                direct_id_col = find_column(attendance_df, ["department_id", "dept_id"], require_values=True)
                if direct_id_col:
                    ids = attendance_df[direct_id_col].astype("string").str.strip().str.upper()
                    attendance_df["_department_name"] = ids.map(department_names).fillna(ids)

            if employees_df is not None and not employees_df.empty:
                emp_key = find_column(employees_df, ["employee_key", "employee_id", "employeeid"], require_values=True)
                emp_dept = find_column(employees_df, ["department_id", "dept_id"], require_values=True)
                emp_name = find_column(employees_df, ["department_name", "department", "dept_name"], require_values=True)
                att_key = find_column(attendance_df, ["employee_key", "employee_id", "employeeid"], require_values=True)
                if att_key and emp_key and (emp_dept or emp_name):
                    employee_map = employees_df[[emp_key] + ([emp_dept] if emp_dept else []) + ([emp_name] if emp_name else [])].copy()
                    employee_map[emp_key] = employee_map[emp_key].astype("string").str.strip()
                    employee_map = employee_map.drop_duplicates(subset=[emp_key], keep="first").set_index(emp_key)
                    att_keys = attendance_df[att_key].astype("string").str.strip()
                    if emp_name:
                        mapped_names = att_keys.map(employee_map[emp_name])
                    else:
                        mapped_ids = att_keys.map(employee_map[emp_dept]).astype("string").str.strip().str.upper()
                        mapped_names = mapped_ids.map(department_names).fillna(mapped_ids)
                    attendance_df["_department_name"] = attendance_df["_department_name"].fillna(mapped_names)

            st.markdown("### Filters")
            if attendance_df.empty:
                st.warning("No valid attendance dates are available.")
            else:
                minimum_date = attendance_df[date_column].min().date()
                maximum_date = attendance_df[date_column].max().date()
                selected_range = st.date_input(
                    "Reporting date range", value=(minimum_date, maximum_date),
                    min_value=minimum_date, max_value=maximum_date, key="task4_date_range",
                )
                filtered = attendance_df.copy()
                if isinstance(selected_range, (tuple, list)) and len(selected_range) == 2:
                    start_date, end_date = selected_range
                    filtered = filtered[filtered[date_column].dt.date.between(start_date, end_date)]

                department_values = sorted(
                    filtered["_department_name"].dropna().astype(str).unique().tolist()
                )
                if department_values:
                    chosen_department = st.selectbox(
                        "Department", ["All departments"] + department_values, key="task4_department"
                    )
                    if chosen_department != "All departments":
                        filtered = filtered[filtered["_department_name"].astype(str) == chosen_department]
                else:
                    st.info("Department values could not be mapped from attendance.csv and employees.csv.")

                total_scheduled = filtered["_scheduled"].sum()
                attendance_rate = 100 * filtered["_attendance_numerator"].sum() / total_scheduled if total_scheduled else 0
                total_late = filtered["_late"].sum()
                total_records = len(filtered)
                col1, col2, col3 = st.columns(3)
                col1.metric("Weighted attendance rate", f"{attendance_rate:.2f}%")
                col2.metric("Late arrivals", f"{total_late:,.0f}")
                col3.metric("Employee-month records", f"{total_records:,}")

                st.markdown("### 1. Monthly Attendance Trend")
                monthly = (
                    filtered.groupby("_month", as_index=False)
                    .agg(scheduled_days=("_scheduled", "sum"), attendance_numerator=("_attendance_numerator", "sum"), late_arrivals=("_late", "sum"))
                    .sort_values("_month")
                )
                monthly["attendance_rate_pct"] = 100 * monthly["attendance_numerator"] / monthly["scheduled_days"].mask(monthly["scheduled_days"].eq(0))
                monthly["rolling_3_month_avg_pct"] = monthly["attendance_rate_pct"].rolling(3, min_periods=1).mean()
                if not monthly.empty:
                    trend = monthly.set_index("_month")[["attendance_rate_pct", "rolling_3_month_avg_pct"]].rename(columns={"attendance_rate_pct": "Monthly attendance %", "rolling_3_month_avg_pct": "3-month rolling average %"})
                    st.line_chart(trend)
                    monthly["mom_change_pp"] = monthly["attendance_rate_pct"].diff()
                    st.dataframe(monthly[["_month", "attendance_rate_pct", "rolling_3_month_avg_pct", "mom_change_pp"]].rename(columns={"_month": "Month", "attendance_rate_pct": "Attendance rate %", "rolling_3_month_avg_pct": "3-month rolling avg %", "mom_change_pp": "MoM change (percentage points)"}), use_container_width=True, hide_index=True)
                    st.caption("Weighted monthly rate = (present days + 0.5 × unpaid half-days) / scheduled days.")
                else:
                    st.info("No attendance records match the selected filters.")

                st.markdown("### 2. Monthly Late Arrivals")
                if not monthly.empty:
                    st.line_chart(monthly.set_index("_month")[["late_arrivals"]])

                st.markdown("### 3. Department-wise Attendance")
                department_summary = (
                    filtered.dropna(subset=["_department_name"])
                    .groupby("_department_name", as_index=False)
                    .agg(scheduled_days=("_scheduled", "sum"), attendance_numerator=("_attendance_numerator", "sum"), late_arrivals=("_late", "sum"))
                )
                if not department_summary.empty:
                    department_summary["attendance_rate_pct"] = 100 * department_summary["attendance_numerator"] / department_summary["scheduled_days"].mask(department_summary["scheduled_days"].eq(0))
                    department_summary = department_summary.dropna(subset=["attendance_rate_pct"]).sort_values("attendance_rate_pct", ascending=False)
                    if not department_summary.empty:
                        st.bar_chart(department_summary.set_index("_department_name")[["attendance_rate_pct"]])
                        highest, lowest = department_summary.iloc[0], department_summary.iloc[-1]
                        st.write(f"Highest in selected data: **{highest['_department_name']}** ({highest['attendance_rate_pct']:.2f}%). Lowest: **{lowest['_department_name']}** ({lowest['attendance_rate_pct']:.2f}%).")
                        st.dataframe(department_summary, use_container_width=True, hide_index=True)
                else:
                    st.info("Department comparison needs valid department values in employees.csv.")

                st.markdown("### 4. Leave Days by Type")
                if leave_df is not None and not leave_df.empty:
                    leave_type_column = find_column(leave_df, ["leave_type_name", "leave_type", "leave_type_code", "type"], require_values=True)
                    leave_days_column = find_column(leave_df, ["days", "leave_days", "duration_days", "leave_duration"])
                    if leave_type_column and leave_days_column:
                        leave_df["_leave_days"] = numeric_column(leave_df, leave_days_column)
                        leave_summary = leave_df.groupby(leave_type_column)["_leave_days"].sum().sort_values(ascending=False)
                        st.bar_chart(leave_summary)
                        st.dataframe(leave_summary.rename("Total leave days").reset_index(), use_container_width=True, hide_index=True)
                    else:
                        st.info("Leave file found, but leave type/day columns need review.")
                else:
                    st.info(f"Clean leave data not found at {leave_path}.")

                st.markdown("### 5. Weekday Attendance Trend — Synthetic Demo Only")

                if demo_path:
                    demo_df = read_csv_safely(demo_path)
                    if demo_df is not None and not demo_df.empty:
                        weekday_column = find_column(demo_df, ["weekday"])
                        demo_present_column = find_column(demo_df, ["present"])
                        demo_scheduled_column = find_column(demo_df, ["scheduled"])
                        demo_late_column = find_column(demo_df, ["late_arrival"])
                        if weekday_column and demo_present_column and demo_scheduled_column:
                            demo_df["_present"] = numeric_column(demo_df, demo_present_column)
                            demo_df["_scheduled"] = numeric_column(demo_df, demo_scheduled_column)
                            demo_df["_late"] = numeric_column(demo_df, demo_late_column) if demo_late_column else 0
                            weekday_summary = demo_df.groupby(weekday_column).agg(scheduled_days=("_scheduled", "sum"), present_days=("_present", "sum"), late_arrivals=("_late", "sum"))
                            weekday_summary["attendance_rate_pct"] = 100 * weekday_summary["present_days"] / weekday_summary["scheduled_days"].mask(weekday_summary["scheduled_days"].eq(0))
                            weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                            weekday_summary = weekday_summary.reindex([day for day in weekday_order if day in weekday_summary.index])
                            st.bar_chart(weekday_summary[["attendance_rate_pct"]])
                            st.dataframe(weekday_summary.reset_index(), use_container_width=True, hide_index=True)
                        else:
                            st.info("Synthetic demo data exists, but expected columns were not found.")
                else:
                    st.info("Synthetic weekday sample CSV was not found.")

                st.markdown("### 6. AI/ML Attendance Anomaly Context")
                if anomaly_path.exists():
                    try:
                        anomaly_df = normalize_columns(pd.read_excel(anomaly_path, sheet_name="fact_anomaly"))
                        source_column = find_column(anomaly_df, ["source_dataset"])
                        flagged_column = find_column(anomaly_df, ["flagged"])
                        period_column = find_column(anomaly_df, ["period"])
                        if source_column and flagged_column and period_column:
                            anomaly_df = anomaly_df[
                                anomaly_df[source_column].astype(str).str.lower().eq("attendance_monthly_features")
                                & anomaly_df[flagged_column].astype(str).str.upper().eq("Y")
                            ].copy()
                            anomaly_df[period_column] = pd.to_datetime(anomaly_df[period_column], errors="coerce")
                            anomaly_df = anomaly_df.dropna(subset=[period_column])
                            anomaly_df["_month"] = anomaly_df[period_column].dt.to_period("M").dt.to_timestamp()
                            anomaly_monthly = anomaly_df.groupby("_month").size().rename("Flagged employee-month records")
                            if not anomaly_monthly.empty:
                                st.bar_chart(anomaly_monthly)
                            else:
                                st.info("No flagged attendance anomaly records were found in the workbook.")
                            st.caption("The AI/ML sample flags employee-month records, not individual days.")
                        else:
                            st.info("Anomaly workbook does not have the expected columns.")
                    except Exception as exc:
                        st.warning(f"Could not load the anomaly workbook: {exc}")
                else:
                    st.info(f"AI/ML sample workbook not found at {anomaly_path}.")

                st.markdown("### 7. HR Takeaways and Limitations")
                st.markdown(
                    "- Compare lower-attendance months with leave, public holidays, staffing coverage, and reporting completeness before acting.\n"
                    "- Department differences indicate where to review staffing and records; they do not establish causes.\n"
                    "- The supplied PulseIQ attendance source is monthly aggregated, so actual weekday attendance cannot be derived from it.\n"
                    "- The weekday chart is synthetic demonstration data, not real workforce results.\n"
                    "- AI/ML flags represent employee-month records, not individual flagged days."
                )
                if task4_note.exists():
                    with st.expander("View saved Task 4 insight note"):
                        st.markdown(task4_note.read_text(encoding="utf-8"))


# TASK 5 ? WORKFORCE & HEADCOUNT
elif page == "Task 5 - Workforce & Headcount":
    st.subheader("Task 5 ? Workforce & Headcount")
    st.caption("CEO workforce dashboard | Governed metric views only")

    department_names = {
        "D00": "Executive Office",
        "D01": "Engineering",
        "D02": "Product & Design",
        "D03": "Data & AI",
        "D04": "Sales",
        "D05": "Marketing",
        "D06": "Customer Support",
        "D07": "Human Resources",
        "D08": "Finance & Accounts",
        "D09": "Operations & IT",
        "D10": "Legal & Compliance",
    }

    try:
        headcount = warehouse_query("""
            SELECT month_start_date, department_id, headcount
            FROM warehouse.metric_m01_headcount
            ORDER BY month_start_date, department_id
        """)

        hires = warehouse_query("""
            SELECT month_start_date, department_id, hires
            FROM warehouse.metric_m02_hires
            ORDER BY month_start_date, department_id
        """)

        exits = warehouse_query("""
            SELECT month_start_date, department_id, exits
            FROM warehouse.metric_m03_exits
            ORDER BY month_start_date, department_id
        """)

        if headcount.empty:
            st.warning("No headcount records are available in the governed metric view.")
        else:
            headcount["month_start_date"] = pd.to_datetime(headcount["month_start_date"])
            hires["month_start_date"] = pd.to_datetime(hires["month_start_date"])
            exits["month_start_date"] = pd.to_datetime(exits["month_start_date"])

            min_date = headcount["month_start_date"].min().date()
            max_date = headcount["month_start_date"].max().date()

            st.markdown("### Filters")
            filter_col1, filter_col2 = st.columns(2)

            with filter_col1:
                selected_departments = st.multiselect(
                    "Department",
                    options=sorted(headcount["department_id"].dropna().unique()),
                    default=sorted(headcount["department_id"].dropna().unique()),
                    format_func=lambda d: f"{d} ? {department_names.get(d, d)}",
                )

            with filter_col2:
                date_range = st.date_input(
                    "Date range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                )

            if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
                start_date, end_date = date_range
            else:
                start_date, end_date = min_date, max_date

            start_ts = pd.Timestamp(start_date)
            end_ts = pd.Timestamp(end_date)

            filtered = headcount[
                headcount["department_id"].isin(selected_departments)
                & headcount["month_start_date"].between(start_ts, end_ts)
            ].copy()

            filtered_hires = hires[
                hires["department_id"].isin(selected_departments)
                & hires["month_start_date"].between(start_ts, end_ts)
            ].copy()

            filtered_exits = exits[
                exits["department_id"].isin(selected_departments)
                & exits["month_start_date"].between(start_ts, end_ts)
            ].copy()

            if filtered.empty:
                st.info("No headcount data matches the selected filters.")
            else:
                latest_month = filtered["month_start_date"].max()
                latest = filtered[filtered["month_start_date"] == latest_month]
                current_headcount = int(latest["headcount"].sum())

                previous_month = latest_month - pd.DateOffset(months=1)
                previous = filtered[filtered["month_start_date"] == previous_month]
                previous_headcount = int(previous["headcount"].sum()) if not previous.empty else None

                total_hires = int(filtered_hires["hires"].sum()) if not filtered_hires.empty else 0
                total_exits = int(filtered_exits["exits"].sum()) if not filtered_exits.empty else 0

                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Latest Headcount", f"{current_headcount:,}")
                k2.metric(
                    "Month-on-Month Change",
                    "N/A" if previous_headcount is None else f"{current_headcount - previous_headcount:+,}",
                )
                k3.metric("Hires in Selected Period", f"{total_hires:,}")
                k4.metric("Exits in Selected Period", f"{total_exits:,}")

                st.markdown("### CEO Questions")
                st.markdown(
                    "1. What is our latest available workforce size?\n"
                    "2. How has headcount changed over time?\n"
                    "3. Which departments have the largest teams?\n"
                    "4. How many hires and exits occurred in the selected period?\n"
                    "5. What location-tier and work-mode data is available for workforce planning?"
                )

                st.markdown("### Headcount trend")
                trend = (
                    filtered.groupby("month_start_date", as_index=False)["headcount"]
                    .sum()
                    .sort_values("month_start_date")
                )
                st.line_chart(trend, x="month_start_date", y="headcount")
                first_value = int(trend.iloc[0]["headcount"])
                last_value = int(trend.iloc[-1]["headcount"])
                st.caption(
                    f"Insight: Headcount changed from {first_value:,} to {last_value:,} "
                    f"across the selected date range."
                )

                st.markdown("### Department workforce breakdown")
                dept = (
                    latest.groupby("department_id", as_index=False)["headcount"]
                    .sum()
                    .sort_values("headcount", ascending=False)
                )
                dept["department"] = dept["department_id"].map(department_names).fillna(dept["department_id"])
                dept_chart = dept.rename(columns={"department": "Department", "headcount": "Employees"})
                st.bar_chart(dept_chart, x="Department", y="Employees", horizontal=True)
                if not dept.empty:
                    st.caption(
                        f"Insight: {dept.iloc[0]['department']} has the largest headcount "
                        f"({int(dept.iloc[0]['headcount']):,}) in the latest selected month."
                    )

                st.markdown("### Hires and exits")
                movement = pd.merge(
                    filtered_hires.groupby("month_start_date", as_index=False)["hires"].sum(),
                    filtered_exits.groupby("month_start_date", as_index=False)["exits"].sum(),
                    on="month_start_date",
                    how="outer",
                ).fillna(0).sort_values("month_start_date")
                if not movement.empty:
                    movement_chart = movement.rename(
                        columns={"month_start_date": "Month", "hires": "Hires", "exits": "Exits"}
                    ).sort_values("Month")
                    st.line_chart(movement_chart, x="Month", y=["Hires", "Exits"])
                    st.caption(
                        f"Insight: The selected period contains {total_hires:,} hires "
                        f"and {total_exits:,} exits."
                    )
                else:
                    st.info("No hires or exits are available for the selected filters.")

                st.markdown("### Location tier and work mode")
                st.info(
                    "Not displayed yet: the current warehouse does not contain "
                    "warehouse.dim_location or governed location-tier/work-mode metric views. "
                    "Add governed metric views before displaying these breakdowns."
                )

    except Exception as exc:
        st.error(f"Task 5 dashboard could not load: {exc}")
        st.caption(
            "Check the database connection settings and availability of the Task 5 metric views."
        )
