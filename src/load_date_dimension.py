
import pandas as pd
import psycopg

FILE = "data/reference/03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"


def flag(value):
    """Convert Excel Y/N flags into PostgreSQL booleans."""
    if pd.isna(value):
        return None

    return str(value).strip().upper() in ("Y", "YES", "TRUE", "1")


def main():
    # Read the date dimension from the reference workbook.
    df = pd.read_excel(FILE, sheet_name="dim_date")

    columns = [
        "date_key",
        "date",
        "year",
        "quarter",
        "month_number",
        "month_name",
        "year_month",
        "week_of_year",
        "day_of_week",
        "is_weekend",
        "is_holiday",
        "is_working_day",
        "financial_year",
        "fiscal_quarter",
        "fiscal_month_number",
        "is_month_end",
        "month_start_date",
        "month_end_date",
    ]

    df = df[columns].copy()

    # Convert weekday names to integers: Monday=1 ... Sunday=7.
    df["day_of_week"] = (
        pd.to_datetime(df["date"]).dt.isocalendar().day.astype(int)
    )

    # Convert Y/N values to booleans.
    flag_columns = [
        "is_weekend",
        "is_holiday",
        "is_working_day",
        "is_month_end",
    ]

    for column in flag_columns:
        df[column] = df[column].map(flag)

    # Convert missing pandas values to SQL NULL.
    records = [
        tuple(None if pd.isna(value) else value for value in row)
        for row in df.itertuples(index=False, name=None)
    ]

    # Connect to the local PostgreSQL warehouse.
    with psycopg.connect(
        host="localhost",
        port=5433,
        dbname="pulseiq_warehouse",
        user="pulseiq",
        password="pulseiq_dev_password",
    ) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO warehouse.dim_date (
                    date_key,
                    date,
                    year,
                    quarter,
                    month_number,
                    month_name,
                    year_month,
                    week_of_year,
                    day_of_week,
                    is_weekend,
                    is_holiday,
                    is_working_day,
                    financial_year,
                    fiscal_quarter,
                    fiscal_month_number,
                    is_month_end,
                    month_start_date,
                    month_end_date
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (date_key) DO UPDATE SET
                    date = EXCLUDED.date,
                    year = EXCLUDED.year,
                    quarter = EXCLUDED.quarter,
                    month_number = EXCLUDED.month_number,
                    month_name = EXCLUDED.month_name,
                    year_month = EXCLUDED.year_month,
                    week_of_year = EXCLUDED.week_of_year,
                    day_of_week = EXCLUDED.day_of_week,
                    is_weekend = EXCLUDED.is_weekend,
                    is_holiday = EXCLUDED.is_holiday,
                    is_working_day = EXCLUDED.is_working_day,
                    financial_year = EXCLUDED.financial_year,
                    fiscal_quarter = EXCLUDED.fiscal_quarter,
                    fiscal_month_number = EXCLUDED.fiscal_month_number,
                    is_month_end = EXCLUDED.is_month_end,
                    month_start_date = EXCLUDED.month_start_date,
                    month_end_date = EXCLUDED.month_end_date
                """,
                records,
            )

    print(f"Date dimension records processed: {len(df)}")


if __name__ == "__main__":
    main()
