
import json
import os
from pathlib import Path

import pandas as pd
import psycopg
import streamlit as st
from dotenv import load_dotenv

# --------------------------------------------------
# Configuration
# --------------------------------------------------

ROOT = Path(__file__).resolve().parent

load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.example", override=False)

CLEAN_DIR = ROOT / os.getenv("CLEAN_DATA_DIR", "data/clean")
REJECTED_DIR = ROOT / os.getenv("REJECTED_DIR", "rejected")
SUMMARY_PATH = ROOT / os.getenv("LOG_DIR", "logs") / "run_summary.json"

st.set_page_config(
    page_title="PulseIQ Analytics",
    page_icon="📊",
    layout="wide",
)

st.title("PulseIQ Analytics Dashboard")
st.caption(
    "Task 1 — ETL Pipeline | "
    "Task 2 — Analytics Warehouse | "
    "Task 3 — Analytics"
)

page = st.sidebar.radio(
    "Select Dashboard",
    [
        "Overview",
        "Task 1 - ETL",
        "Task 2 - Warehouse",
        "Task 3 - Analytics",
        "Task 4",
    ],
)


# --------------------------------------------------
# Database Connection
# --------------------------------------------------

def get_connection():
    return psycopg.connect(
        host=os.getenv("WAREHOUSE_HOST", "localhost"),
        port=int(os.getenv("WAREHOUSE_PORT", "5433")),
        dbname=os.getenv(
            "WAREHOUSE_DB", "pulseiq_warehouse"
        ),
        user=os.getenv("WAREHOUSE_USER", "pulseiq"),
        password=os.getenv("WAREHOUSE_PASSWORD", ""),
        connect_timeout=5,
    )


def warehouse_query(query):
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


# --------------------------------------------------
# Overview
# --------------------------------------------------

if page == "Overview":

    st.subheader("Project Overview")
    st.write(
        "One Streamlit app for the PulseIQ ETL pipeline, "
        "warehouse, and analytics."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Task 1 — ETL Pipeline")
        st.write(
            "Clean and validate data, inspect cleaned files, "
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
            "Explore PostgreSQL tables and business metrics."
        )

        try:
            result = warehouse_query(
                "SELECT COUNT(*) AS total "
                "FROM warehouse.fact_payroll"
            )

            st.metric(
                "Payroll records",
                int(result.iloc[0]["total"]),
            )
            st.success("PostgreSQL connection successful")

        except Exception as exc:
            st.warning(
                "Warehouse unavailable. Check Docker PostgreSQL "
                "and your WAREHOUSE_* settings."
            )
            st.caption(str(exc))

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("### Task 3 — Analytics Dashboard")
        st.write(
            "Headcount trends, department filtering, "
            "role mix, and tenure analytics."
        )

        st.link_button(
            "Open PulseIQ Superset",
            "http://localhost:8088",
        )

    with col4:
        st.markdown("### Task 4 — Upcoming")
        st.write(
            "Task 4 functionality can be added once "
            "its requirements are available."
        )

    if SUMMARY_PATH.exists():
        st.subheader("Latest ETL Run")

        try:
            summary = json.loads(
                SUMMARY_PATH.read_text(encoding="utf-8")
            )
            st.json(summary)

        except (json.JSONDecodeError, OSError) as exc:
            st.warning(f"Could not read ETL summary: {exc}")


# --------------------------------------------------
# Task 1 — ETL Pipeline
# --------------------------------------------------

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

        except (json.JSONDecodeError, OSError) as exc:
            st.error(f"Could not read ETL summary: {exc}")

    else:
        st.info(
            "Run the ETL pipeline first to generate its summary."
        )

    st.markdown("### Clean Data Preview")

    if CLEAN_DIR.exists():
        csv_files = sorted(CLEAN_DIR.glob("*.csv"))

        if csv_files:
            selected = st.selectbox(
                "Select clean dataset",
                csv_files,
                format_func=lambda p: p.name,
            )

            try:
                df = pd.read_csv(selected)

                col1, col2 = st.columns(2)
                col1.metric("Rows", len(df))
                col2.metric("Columns", len(df.columns))

                st.dataframe(
                    df.head(100),
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
        reject_files = sorted(REJECTED_DIR.glob("*.csv"))

        if reject_files:
            selected_reject = st.selectbox(
                "Select rejected file",
                reject_files,
                format_func=lambda p: p.name,
            )

            try:
                rejected_df = pd.read_csv(selected_reject)

                st.metric("Rejected rows", len(rejected_df))
                st.dataframe(
                    rejected_df.head(100),
                    use_container_width=True,
                )

            except Exception as exc:
                st.error(
                    f"Could not read rejected file: {exc}"
                )

        else:
            st.info("No rejected CSV files found.")

    else:
        st.info("Rejected data folder has not been created yet.")


# --------------------------------------------------
# Task 2 — PostgreSQL Warehouse
# --------------------------------------------------

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

        with get_connection() as conn:
            with conn.cursor() as cur:
                for table in table_options:
                    cur.execute(
                        f"SELECT COUNT(*) FROM warehouse.{table}"
                    )

                    count_frames.append({
                        "Table": table,
                        "Rows": cur.fetchone()[0],
                    })

        st.markdown("### Warehouse Table Counts")
        st.dataframe(
            pd.DataFrame(count_frames),
            use_container_width=True,
            hide_index=True,
        )

        # Payroll KPIs
        payroll = warehouse_query("""
            SELECT
                COUNT(*) AS payroll_rows,
                COUNT(DISTINCT employee_id) AS employees,
                COALESCE(SUM(gross_pay), 0) AS gross_pay,
                COALESCE(SUM(net_pay), 0) AS net_pay
            FROM warehouse.fact_payroll
        """)

        st.markdown("### Payroll KPIs")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Payroll Records",
            f"{int(payroll.iloc[0]['payroll_rows']):,}",
        )
        c2.metric(
            "Employees",
            f"{int(payroll.iloc[0]['employees']):,}",
        )
        c3.metric(
            "Gross Pay",
            f"₹{float(payroll.iloc[0]['gross_pay']):,.2f}",
        )
        c4.metric(
            "Net Pay",
            f"₹{float(payroll.iloc[0]['net_pay']):,.2f}",
        )

        # Attendance KPIs
        attendance = warehouse_query("""
            SELECT
                COUNT(*) AS records,
                ROUND(AVG(attendance_rate)::numeric, 4)
                    AS avg_rate
            FROM warehouse.fact_attendance_monthly
        """)

        st.markdown("### Attendance")

        c1, c2 = st.columns(2)

        c1.metric(
            "Attendance Records",
            f"{int(attendance.iloc[0]['records']):,}",
        )

        avg_rate = attendance.iloc[0]["avg_rate"]

        c2.metric(
            "Average Attendance Rate",
            "N/A"
            if pd.isna(avg_rate)
            else f"{float(avg_rate) * 100:.2f}%",
        )

        # Leave KPIs
        leave = warehouse_query("""
            SELECT
                COUNT(*) AS records,
                COALESCE(SUM(days), 0) AS leave_days
            FROM warehouse.fact_leave
        """)

        st.markdown("### Leave")

        c1, c2 = st.columns(2)

        c1.metric(
            "Leave Requests",
            f"{int(leave.iloc[0]['records']):,}",
        )
        c2.metric(
            "Total Leave Days",
            f"{float(leave.iloc[0]['leave_days']):,.2f}",
        )

        # Headcount KPIs
        headcount = warehouse_query("""
            SELECT
                COUNT(*) AS records,
                COALESCE(SUM(headcount_end), 0)
                    AS headcount_end
            FROM warehouse.fact_headcount_monthly
        """)

        st.markdown("### Headcount")

        c1, c2 = st.columns(2)

        c1.metric(
            "Monthly Department Records",
            f"{int(headcount.iloc[0]['records']):,}",
        )
        c2.metric(
            "Sum of Monthly Ending Headcount",
            f"{int(headcount.iloc[0]['headcount_end']):,}",
        )

        # Warehouse table explorer
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
            "Warehouse query failed. Check that PostgreSQL "
            "is running and WAREHOUSE_* settings are correct."
        )
        st.exception(exc)


# --------------------------------------------------
# Task 3 — Superset Analytics
# --------------------------------------------------

elif page == "Task 3 - Analytics":

    st.subheader("Task 3 — Superset Analytics")

    st.write(
        "Open the interactive Superset dashboard to use "
        "the Department filter and explore saved charts."
    )

    st.link_button(
        "Open PulseIQ Superset",
        "http://localhost:8088",
    )

    st.markdown("### Included Analytics")

    st.markdown("""
    - Monthly headcount trend
    - Headcount by department
    - Role mix
    - Monthly joiners vs leavers
    - Current headcount KPI
    - Department-wise tenure distribution
    """)

    st.info(
        "Superset opens separately; charts are linked here, "
        "not embedded inside Streamlit."
    )


# --------------------------------------------------
# Task 4 — Pending Requirements
# --------------------------------------------------

elif page == "Task 4":

    st.subheader("Task 4")

    st.info(
        "Task 4 requirements are not available yet. "
        "Add the actual Task 4 brief to implement this section."
    )
