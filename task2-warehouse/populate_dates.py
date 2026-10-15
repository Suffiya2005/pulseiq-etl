import pandas as pd
import psycopg
import os

df = pd.read_csv("data/clean/payroll.csv", usecols=["period_end_date"])
dates = pd.to_datetime(df["period_end_date"]).dropna().drop_duplicates()

with psycopg.connect(
    host="localhost",
    port=5433,
    dbname="pulseiq_warehouse",
    user="pulseiq",
    password=os.getenv("WAREHOUSE_PASSWORD", "pulseiq_dev_password"),
) as conn:
    with conn.cursor() as cur:
        for value in dates:
            d = value.date()
            cur.execute("""
                INSERT INTO warehouse.dim_date (
                    date_key, date, year, quarter, month_number,
                    month_name, year_month, week_of_year, day_of_week,
                    is_weekend, is_holiday, is_working_day,
                    financial_year, fiscal_quarter, fiscal_month_number,
                    is_month_end, month_start_date, month_end_date
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, FALSE, %s, %s, %s, %s, TRUE,
                    %s, %s
                )
                ON CONFLICT (date_key) DO NOTHING
            """, (
                int(d.strftime("%Y%m%d")), d, d.year,
                (d.month - 1) // 3 + 1, d.month,
                d.strftime("%B"), d.strftime("%Y-%m"),
                int(value.isocalendar().week), d.isoweekday(),
                d.isoweekday() >= 6, d.isoweekday() <= 5,
                f"{d.year}-{str(d.year + 1)[-2:]}" if d.month >= 4 else f"{d.year - 1}-{str(d.year)[-2:]}",
                f"Q{(d.month - 1) // 3 + 1}",
                (d.month - 4) % 12 + 1,
                d.replace(day=1),
                (d.replace(day=28) + pd.Timedelta(days=4)).replace(day=1) - pd.Timedelta(days=1),
            ))

print(f"Processed {len(dates)} unique payroll dates.")
