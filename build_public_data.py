from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "data" / "reference" / "03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"
ATTENDANCE = ROOT / "data" / "clean" / "attendance.csv"
OUTPUT_DIR = ROOT / "public_data"
OUTPUT = OUTPUT_DIR / "public_monthly_metrics.csv"

def main():
    # Read and aggregate validated monthly headcount source.
    hc = pd.read_excel(SOURCE, sheet_name="fact_headcount_monthly")

    hc["month_start_date"] = pd.to_datetime(hc["month_start_date"])

    monthly_hc = hc.groupby("month_start_date", as_index=False).agg(
        headcount_start=("headcount_start", "sum"),
        hires=("hires", "sum"),
        exits=("exits", "sum"),
        voluntary_exits=("voluntary_exits", "sum"),
        transfers_in=("transfers_in", "sum"),
        transfers_out=("transfers_out", "sum"),
        headcount_end=("headcount_end", "sum"),
    )

    expected_end = (
        monthly_hc["headcount_start"]
        + monthly_hc["hires"]
        + monthly_hc["transfers_in"]
        - monthly_hc["exits"]
        - monthly_hc["transfers_out"]
    )
    if not expected_end.equals(monthly_hc["headcount_end"]):
        raise ValueError("Headcount reconciliation failed. Public data not created.")

    monthly_hc["monthly_attrition_pct"] = (
        monthly_hc["voluntary_exits"]
        / monthly_hc["headcount_start"].replace(0, pd.NA)
        * 100
    )

    monthly_hc = monthly_hc.sort_values("month_start_date")
    rolling_exits = monthly_hc["voluntary_exits"].rolling(12, min_periods=12).sum()
    rolling_base = monthly_hc["headcount_start"].rolling(12, min_periods=12).mean()
    monthly_hc["rolling_12m_attrition_pct"] = rolling_exits / rolling_base * 100

    # Read and aggregate attendance without exposing employee-level rows.
    attendance = pd.read_csv(ATTENDANCE)

    attendance_monthly = attendance.groupby("year_month", as_index=False).agg(
        scheduled_days=("scheduled_days", "sum"),
        present_days=("present_days", "sum"),
        late_arrivals=("late_arrivals", "sum"),
    )

    attendance_monthly["month_start_date"] = pd.to_datetime(
        attendance_monthly["year_month"] + "-01"
    )
    attendance_monthly["attendance_rate_pct"] = (
        attendance_monthly["present_days"]
        / attendance_monthly["scheduled_days"].replace(0, pd.NA)
        * 100
    )

    # Join only company-wide monthly aggregates.
    public = monthly_hc.merge(
        attendance_monthly.drop(columns=["year_month"]),
        on="month_start_date",
        how="left",
    )

    public = public[
        public["month_start_date"] <= pd.Timestamp("2026-09-01")
    ].copy()

    public["month"] = public["month_start_date"].dt.strftime("%Y-%m")

    columns = [
        "month", "headcount_start", "hires", "exits", "headcount_end",
        "monthly_attrition_pct", "rolling_12m_attrition_pct",
        "attendance_rate_pct", "late_arrivals",
    ]

    public[columns].to_csv(OUTPUT, index=False, float_format="%.2f")

    print("Public dataset created:", OUTPUT)
    print("Monthly rows:", len(public))
    print("Data cutoff: September 2026")
    print("Department and employee details: excluded")
    print("Headcount reconciliation: passed")
    print("\nLatest public metrics:")
    print(public[columns].tail(3).to_string(index=False))

if __name__ == "__main__":
    main()
