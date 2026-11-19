from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "public_data" / "public_monthly_metrics.csv"

st.set_page_config(
    page_title="PulseIQ | Workforce Intelligence",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
.stApp { background-color: #0b1120; color: #e5e7eb; }
[data-testid="stMetric"] {
    background: #151f33;
    border: 1px solid #293750;
    padding: 20px;
    border-radius: 12px;
}
[data-testid="stMetricLabel"] { color: #9ca3af; }
[data-testid="stMetricValue"] { color: #f8fafc; }
h1, h2, h3 { color: #f8fafc; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)
    df["month"] = pd.to_datetime(df["month"] + "-01")
    return df.sort_values("month")

try:
    df = load_data()
except Exception as exc:
    st.error(f"Unable to load public dashboard data: {exc}")
    st.stop()

latest = df.iloc[-1]
previous = df.iloc[-2]
attendance = df.dropna(subset=["attendance_rate_pct"])
latest_attendance = attendance.iloc[-1] if not attendance.empty else None

st.title("📊 PulseIQ Workforce Intelligence")
st.caption("Public Workforce Analytics Dashboard | Synthetic Demonstration Data")
st.info(
    "DEMO DATA — This dashboard uses synthetic project data for demonstration "
    "and educational purposes. It does not represent official company records."
)

page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Workforce Analytics", "Attendance Analytics", "About & Methodology"],
)

st.sidebar.markdown("---")
st.sidebar.caption("Data available through September 2026")
st.sidebar.caption("Public aggregated data only")

if page == "Overview":
    st.header("Executive Overview")
    st.caption("Latest reporting month: September 2026")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Closing Headcount",
        f"{int(latest['headcount_end']):,}",
        f"{int(latest['headcount_end'] - previous['headcount_end']):+}",
    )
    c2.metric("New Hires", f"{int(latest['hires']):,}")
    c3.metric("Monthly Exits", f"{int(latest['exits']):,}")
    c4.metric(
        "Attendance Rate",
        f"{latest_attendance['attendance_rate_pct']:.2f}%"
        if latest_attendance is not None else "N/A",
    )

    st.markdown("---")
    left, right = st.columns(2)

    with left:
        st.subheader("Workforce Growth")
        fig = px.line(
            df, x="month", y="headcount_end",
            labels={"month": "Month", "headcount_end": "Employees"},
            markers=True,
        )
        fig.update_layout(template="plotly_dark", height=350)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Monthly Hires vs Exits")
        fig = go.Figure()
        fig.add_bar(x=df["month"], y=df["hires"], name="Hires")
        fig.add_bar(x=df["month"], y=df["exits"], name="Exits")
        fig.update_layout(
            template="plotly_dark", barmode="group", height=350,
            xaxis_title="Month", yaxis_title="Employees",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Attendance Trend")
    if not attendance.empty:
        fig = px.line(
            attendance, x="month", y="attendance_rate_pct",
            labels={"month": "Month", "attendance_rate_pct": "Attendance (%)"},
            markers=True,
        )
        fig.update_layout(template="plotly_dark", height=320)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Attendance history is not available.")

elif page == "Workforce Analytics":
    st.header("Workforce Analytics")

    c1, c2, c3 = st.columns(3)
    c1.metric("Current Headcount", f"{int(latest['headcount_end']):,}")
    c2.metric("Monthly Attrition", f"{latest['monthly_attrition_pct']:.2f}%")
    c3.metric(
        "Rolling 12-Month Attrition",
        f"{latest['rolling_12m_attrition_pct']:.2f}%"
        if pd.notna(latest["rolling_12m_attrition_pct"]) else "N/A",
    )

    st.subheader("Headcount Trend")
    fig = px.line(df, x="month", y="headcount_end", markers=True)
    fig.update_layout(template="plotly_dark", yaxis_title="Headcount")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Attrition Trends")
    fig = go.Figure()
    fig.add_scatter(
        x=df["month"], y=df["monthly_attrition_pct"],
        name="Monthly Attrition", mode="lines",
    )
    fig.add_scatter(
        x=df["month"], y=df["rolling_12m_attrition_pct"],
        name="Rolling 12-Month Attrition", mode="lines",
    )
    fig.update_layout(
        template="plotly_dark", yaxis_title="Attrition (%)",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Monthly Workforce Movement")
    fig = px.bar(
        df, x="month", y=["hires", "exits"],
        barmode="group",
    )
    fig.update_layout(template="plotly_dark", yaxis_title="Employees")
    st.plotly_chart(fig, use_container_width=True)

elif page == "Attendance Analytics":
    st.header("Attendance Analytics")
    st.caption("Attendance reporting begins in April 2025.")

    if attendance.empty:
        st.warning("No attendance data available.")
    else:
        latest_a = attendance.iloc[-1]
        c1, c2 = st.columns(2)
        c1.metric("Latest Attendance", f"{latest_a['attendance_rate_pct']:.2f}%")
        c2.metric("Latest Late Arrivals", f"{int(latest_a['late_arrivals']):,}")

        fig = px.line(
            attendance, x="month", y="attendance_rate_pct",
            markers=True, title="Monthly Attendance Rate",
        )
        fig.update_layout(template="plotly_dark", yaxis_title="Attendance (%)")
        st.plotly_chart(fig, use_container_width=True)

        fig = px.bar(
            attendance, x="month", y="late_arrivals",
            title="Monthly Late Arrivals",
        )
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

else:
    st.header("About PulseIQ")
    st.write(
        "PulseIQ is a workforce analytics demonstration project designed "
        "to present aggregated workforce trends through an interactive dashboard."
    )

    st.subheader("Data Coverage")
    st.write("- Workforce history: January 2020 – September 2026")
    st.write("- Attendance history: April 2025 – September 2026")
    st.write("- Data type: Synthetic demonstration data")
    st.write("- Reporting level: Company-wide aggregates only")

    st.subheader("Metric Definitions")
    st.write(
        "- Headcount: Monthly closing workforce total.\n"
        "- Hires: New hires recorded during the month.\n"
        "- Exits: Employee exits recorded during the month.\n"
        "- Monthly attrition: Voluntary exits divided by opening headcount.\n"
        "- Rolling attrition: Rolling 12-month voluntary exits divided by "
        "the average monthly opening headcount over that period.\n"
        "- Attendance: Total present days divided by total scheduled days.\n"
        "- Late arrivals: Total recorded late arrivals during the month."
    )

    st.warning(
        "This is a synthetic demonstration dashboard, not an official "
        "company reporting system. Missing historical attendance values "
        "are intentionally left blank rather than treated as zero."
    )

st.markdown("---")
st.caption("PulseIQ | Public Demonstration Dashboard | Data cutoff: September 2026")
