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
            "Analyze attendance and leave patterns, compare "
            "departments, and review late arrivals and AI/ML anomalies."
        )

        st.markdown(
            "- Monthly attendance trend and 3-month rolling average\n"
            "- Department-wise attendance comparison\n"
            "- Leave days by type\n"
            "- Monthly late-arrival trend\n"
            "- AI/ML flagged employee-month anomaly chart\n"
            "- Weekday attendance trend (synthetic demo only)"
        )

        st.info(
            "Select **Task 4** in the sidebar to open "
            "the detailed attendance analysis."
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
    task4_note = (
        task4_dir / "docs" / "TASK4_ATTENDANCE_INSIGHTS.md"
    )

    demo_candidates = [
        task4_dir / "data" / "attendance_daily_sample.csv",
        ROOT / "data" / "reference" / "attendance_daily_sample.csv",
    ]

    demo_path = next(
        (path for path in demo_candidates if path.exists()),
        None,
    )

    anomaly_path = (
        ROOT
        / "data"
        / "reference"
        / "03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"
    )

    attendance_path = CLEAN_DIR / "attendance.csv"
    employees_path = CLEAN_DIR / "employees.csv"
    leave_path = CLEAN_DIR / "leave.csv"

    attendance_df = read_csv_safely(attendance_path)
    employees_df = read_csv_safely(employees_path)
    leave_df = read_csv_safely(leave_path)

    if attendance_df is None:
        st.error(
            f"Clean attendance data was not found at {attendance_path}. "
            "Run the ETL pipeline first."
        )
    else:
        date_column = find_column(
            attendance_df,
            ["period_end_date", "attendance_date", "date"],
            require_values=True,
        )

        scheduled_column = find_column(
            attendance_df,
            ["scheduled_days", "scheduled"],
        )
        present_column = find_column(
            attendance_df,
            ["present_days", "present"],
        )
        half_column = find_column(
            attendance_df,
            ["half_days_unpaid"],
        )
        late_column = find_column(
            attendance_df,
            ["late_arrivals", "late_arrival"],
        )

        if not date_column or not scheduled_column or not present_column:
            st.error(
                "Attendance data needs date, scheduled-days, and "
                "present-days columns. Detected columns: "
                + ", ".join(attendance_df.columns)
            )
        else:
            attendance_df[date_column] = pd.to_datetime(
                attendance_df[date_column],
                errors="coerce",
            )

            attendance_df = attendance_df.dropna(
                subset=[date_column]
            ).copy()

            attendance_df["_scheduled"] = numeric_column(
                attendance_df,
                scheduled_column,
            )
            attendance_df["_present"] = numeric_column(
                attendance_df,
                present_column,
            )
            attendance_df["_half"] = (
                numeric_column(attendance_df, half_column)
                if half_column
                else 0
            )
            attendance_df["_late"] = (
                numeric_column(attendance_df, late_column)
                if late_column
                else 0
            )

            attendance_df["_attendance_numerator"] = (
                attendance_df["_present"]
                + 0.5 * attendance_df["_half"]
            )

            attendance_df["_month"] = (
                attendance_df[date_column]
                .dt.to_period("M")
                .dt.to_timestamp()
            )

            # Identify a populated department field or join through employees.
            department_column = find_column(
                attendance_df,
                [
                    "department_name",
                    "department",
                    "dept_name",
                    "department_id",
                    "dept_id",
                ],
                require_values=True,
            )

            if department_column is None and employees_df is not None:
                attendance_key = find_column(
                    attendance_df,
                    ["employee_key", "employee_id", "employee_code"],
                )
                employee_key = find_column(
                    employees_df,
                    ["employee_key", "employee_id", "employee_code"],
                )
                employee_department = find_column(
                    employees_df,
                    [
                        "department_name",
                        "department",
                        "dept_name",
                        "department_id",
                        "dept_id",
                    ],
                    require_values=True,
                )

                if (
                    attendance_key
                    and employee_key
                    and employee_department
                ):
                    left = attendance_df.copy()
                    right = employees_df[
                        [employee_key, employee_department]
                    ].copy()

                    left["_employee_join_key"] = (
                        left[attendance_key].astype(str)
                    )
                    right["_employee_join_key"] = (
                        right[employee_key].astype(str)
                    )

                    right = right.drop_duplicates(
                        "_employee_join_key"
                    )

                    merged = left.merge(
                        right[
                            ["_employee_join_key", employee_department]
                        ],
                        on="_employee_join_key",
                        how="left",
                        suffixes=("", "_employee"),
                    )

                    if merged[employee_department].notna().any():
                        attendance_df = merged
                        department_column = employee_department

            st.markdown("### Filters")

            minimum_date = (
                attendance_df[date_column].min().date()
            )
            maximum_date = (
                attendance_df[date_column].max().date()
            )

            selected_range = st.date_input(
                "Reporting date range",
                value=(minimum_date, maximum_date),
                min_value=minimum_date,
                max_value=maximum_date,
                key="task4_date_range",
            )

            filtered = attendance_df.copy()

            if (
                isinstance(selected_range, (tuple, list))
                and len(selected_range) == 2
            ):
                start_date, end_date = selected_range

                filtered = filtered[
                    filtered[date_column].dt.date.between(
                        start_date,
                        end_date,
                    )
                ]

            if department_column:
                department_values = sorted(
                    filtered[department_column]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

                if department_values:
                    chosen_department = st.selectbox(
                        "Department",
                        ["All departments"] + department_values,
                        key="task4_department",
                    )

                    if chosen_department != "All departments":
                        filtered = filtered[
                            filtered[department_column].astype(str)
                            == chosen_department
                        ]
                else:
                    st.info(
                        "Department values are blank in the available "
                        "attendance data."
                    )
            else:
                st.info(
                    "Department filter is unavailable because a matching "
                    "department field could not be found."
                )

            total_scheduled = filtered["_scheduled"].sum()

            attendance_rate = (
                100
                * filtered["_attendance_numerator"].sum()
                / total_scheduled
                if total_scheduled
                else 0
            )

            total_late = filtered["_late"].sum()
            total_records = len(filtered)

            col1, col2, col3 = st.columns(3)
            col1.metric(
                "Weighted attendance rate",
                f"{attendance_rate:.2f}%",
            )
            col2.metric(
                "Late arrivals",
                f"{total_late:,.0f}",
            )
            col3.metric(
                "Employee-month records",
                f"{total_records:,}",
            )

            # Monthly attendance trend and rolling average.
            st.markdown("### 1. Monthly Attendance Trend")

            monthly = (
                filtered.groupby("_month", as_index=False)
                .agg(
                    scheduled_days=("_scheduled", "sum"),
                    attendance_numerator=(
                        "_attendance_numerator",
                        "sum",
                    ),
                    late_arrivals=("_late", "sum"),
                )
                .sort_values("_month")
            )

            monthly["attendance_rate_pct"] = (
                100
                * monthly["attendance_numerator"]
                / monthly["scheduled_days"].mask(
                    monthly["scheduled_days"].eq(0)
                )
            )

            monthly["rolling_3_month_avg_pct"] = (
                monthly["attendance_rate_pct"]
                .rolling(3, min_periods=1)
                .mean()
            )

            if not monthly.empty:
                trend = monthly.set_index("_month")[
                    [
                        "attendance_rate_pct",
                        "rolling_3_month_avg_pct",
                    ]
                ].rename(
                    columns={
                        "attendance_rate_pct": "Monthly attendance %",
                        "rolling_3_month_avg_pct": (
                            "3-month rolling average %"
                        ),
                    }
                )

                st.line_chart(trend)

                monthly["mom_change_pp"] = (
                    monthly["attendance_rate_pct"].diff()
                )

                st.dataframe(
                    monthly[
                        [
                            "_month",
                            "attendance_rate_pct",
                            "rolling_3_month_avg_pct",
                            "mom_change_pp",
                        ]
                    ].rename(
                        columns={
                            "_month": "Month",
                            "attendance_rate_pct": "Attendance rate %",
                            "rolling_3_month_avg_pct": (
                                "3-month rolling avg %"
                            ),
                            "mom_change_pp": (
                                "MoM change (percentage points)"
                            ),
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

                st.caption(
                    "Weighted monthly rate = (present days + "
                    "0.5 × unpaid half-days) / scheduled days."
                )

            # Late arrivals.
            st.markdown("### 2. Monthly Late Arrivals")

            if not monthly.empty:
                st.line_chart(
                    monthly.set_index("_month")[["late_arrivals"]]
                )

            # Department comparison.
            st.markdown("### 3. Department-wise Attendance")

            if department_column:
                department_summary = (
                    filtered.dropna(subset=[department_column])
                    .groupby(department_column)
                    .agg(
                        scheduled_days=("_scheduled", "sum"),
                        attendance_numerator=(
                            "_attendance_numerator",
                            "sum",
                        ),
                        late_arrivals=("_late", "sum"),
                    )
                    .reset_index()
                )

                department_summary["attendance_rate_pct"] = (
                    100
                    * department_summary["attendance_numerator"]
                    / department_summary["scheduled_days"].mask(
                        department_summary["scheduled_days"].eq(0)
                    )
                )

                department_summary = department_summary.dropna(
                    subset=["attendance_rate_pct"]
                ).sort_values(
                    "attendance_rate_pct",
                    ascending=False,
                )

                if not department_summary.empty:
                    st.bar_chart(
                        department_summary.set_index(
                            department_column
                        )[["attendance_rate_pct"]]
                    )

                    highest = department_summary.iloc[0]
                    lowest = department_summary.iloc[-1]

                    st.write(
                        f"Highest in selected data: "
                        f"**{highest[department_column]}** "
                        f"({highest['attendance_rate_pct']:.2f}%). "
                        f"Lowest: **{lowest[department_column]}** "
                        f"({lowest['attendance_rate_pct']:.2f}%)."
                    )

                    st.dataframe(
                        department_summary,
                        use_container_width=True,
                        hide_index=True,
                    )
            else:
                st.info(
                    "Department comparison needs a department field "
                    "or valid employee mapping."
                )

            # Leave analysis.
            st.markdown("### 4. Leave Days by Type")

            if leave_df is not None:
                leave_type_column = find_column(
                    leave_df,
                    [
                        "leave_type_name",
                        "leave_type",
                        "leave_type_code",
                        "type",
                    ],
                    require_values=True,
                )

                leave_days_column = find_column(
                    leave_df,
                    [
                        "days",
                        "leave_days",
                        "duration_days",
                        "leave_duration",
                    ],
                )

                if leave_type_column and leave_days_column:
                    leave_df["_leave_days"] = numeric_column(
                        leave_df,
                        leave_days_column,
                    )

                    leave_summary = (
                        leave_df.groupby(leave_type_column)["_leave_days"]
                        .sum()
                        .sort_values(ascending=False)
                    )

                    st.bar_chart(leave_summary)

                    st.dataframe(
                        leave_summary.rename(
                            "Total leave days"
                        ).reset_index(),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info(
                        "Leave file found, but leave type/day columns "
                        "need review."
                    )
            else:
                st.info(
                    f"Clean leave data not found at {leave_path}."
                )

            # Weekday demonstration.
            st.markdown(
                "### 5. Weekday Attendance Trend — Synthetic Demo Only"
            )

            st.warning(
                "These weekday results use simulated attendance. "
                "They are for demonstration only and are not actual "
                "PulseIQ employee findings."
            )

            if demo_path:
                demo_df = read_csv_safely(demo_path)

                weekday_column = find_column(
                    demo_df,
                    ["weekday"],
                )
                demo_present_column = find_column(
                    demo_df,
                    ["present"],
                )
                demo_scheduled_column = find_column(
                    demo_df,
                    ["scheduled"],
                )
                demo_late_column = find_column(
                    demo_df,
                    ["late_arrival"],
                )

                if (
                    demo_df is not None
                    and weekday_column
                    and demo_present_column
                    and demo_scheduled_column
                ):
                    demo_df["_present"] = numeric_column(
                        demo_df,
                        demo_present_column,
                    )
                    demo_df["_scheduled"] = numeric_column(
                        demo_df,
                        demo_scheduled_column,
                    )
                    demo_df["_late"] = (
                        numeric_column(demo_df, demo_late_column)
                        if demo_late_column
                        else 0
                    )

                    weekday_summary = (
                        demo_df.groupby(weekday_column)
                        .agg(
                            scheduled_days=("_scheduled", "sum"),
                            present_days=("_present", "sum"),
                            late_arrivals=("_late", "sum"),
                        )
                    )

                    weekday_summary["attendance_rate_pct"] = (
                        100
                        * weekday_summary["present_days"]
                        / weekday_summary["scheduled_days"].mask(
                            weekday_summary["scheduled_days"].eq(0)
                        )
                    )

                    weekday_order = [
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday",
                    ]

                    weekday_summary = weekday_summary.reindex(
                        [
                            day
                            for day in weekday_order
                            if day in weekday_summary.index
                        ]
                    )

                    st.bar_chart(
                        weekday_summary[["attendance_rate_pct"]]
                    )

                    st.dataframe(
                        weekday_summary.reset_index(),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info(
                        "Synthetic demo data exists, but expected "
                        "columns were not found."
                    )
            else:
                st.info(
                    "Synthetic weekday sample CSV was not found."
                )

            # AI/ML anomaly context.
            st.markdown("### 6. AI/ML Attendance Anomaly Context")

            if anomaly_path.exists():
                try:
                    anomaly_df = normalize_columns(
                        pd.read_excel(
                            anomaly_path,
                            sheet_name="fact_anomaly",
                        )
                    )

                    source_column = find_column(
                        anomaly_df,
                        ["source_dataset"],
                    )
                    flagged_column = find_column(
                        anomaly_df,
                        ["flagged"],
                    )
                    period_column = find_column(
                        anomaly_df,
                        ["period"],
                    )

                    if (
                        source_column
                        and flagged_column
                        and period_column
                    ):
                        anomaly_df = anomaly_df[
                            anomaly_df[source_column]
                            .astype(str)
                            .str.lower()
                            .eq("attendance_monthly_features")
                            & anomaly_df[flagged_column]
                            .astype(str)
                            .str.upper()
                            .eq("Y")
                        ].copy()

                        anomaly_df[period_column] = pd.to_datetime(
                            anomaly_df[period_column],
                            errors="coerce",
                        )

                        anomaly_df = anomaly_df.dropna(
                            subset=[period_column]
                        )

                        anomaly_df["_month"] = (
                            anomaly_df[period_column]
                            .dt.to_period("M")
                            .dt.to_timestamp()
                        )

                        anomaly_monthly = (
                            anomaly_df.groupby("_month")
                            .size()
                            .rename(
                                "Flagged employee-month records"
                            )
                        )

                        st.bar_chart(anomaly_monthly)

                        st.caption(
                            "The AI/ML sample flags employee-month "
                            "records, not individual days."
                        )
                    else:
                        st.info(
                            "Anomaly workbook does not have the "
                            "expected columns."
                        )

                except Exception as exc:
                    st.warning(
                        f"Could not load the anomaly workbook: {exc}"
                    )
            else:
                st.info(
                    f"AI/ML sample workbook not found at {anomaly_path}."
                )

            # HR takeaways and limitations.
            st.markdown("### 7. HR Takeaways and Limitations")

            st.markdown(
                "- Compare lower-attendance months with leave, public "
                "holidays, staffing coverage, and reporting completeness "
                "before acting.\n"
                "- Department differences indicate where to review staffing "
                "and records; they do not establish causes.\n"
                "- The supplied PulseIQ attendance source is monthly "
                "aggregated, so actual weekday attendance cannot be "
                "derived from it.\n"
                "- The weekday chart is synthetic demonstration data, "
                "not real workforce results.\n"
                "- AI/ML flags represent employee-month records, "
                "not individual flagged days."
            )

            if task4_note.exists():
                with st.expander("View saved Task 4 insight note"):
                    st.markdown(
                        task4_note.read_text(encoding="utf-8")
                    )