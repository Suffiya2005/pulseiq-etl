
import pandas as pd
import psycopg

FILE = "data/reference/03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"

def main():
    df = pd.read_excel(FILE, sheet_name="fact_headcount_monthly")

    columns = [
        "date_key", "month_start_date", "department_id",
        "headcount_start", "hires", "exits", "voluntary_exits",
        "transfers_in", "transfers_out", "headcount_end",
        "attrition_rate_monthly_pct",
    ]
    df = df[columns]

    # Handle pandas missing values and Excel's numeric representations.
    records = [
        tuple(None if pd.isna(v) else v for v in row)
        for row in df.itertuples(index=False, name=None)
    ]

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
                INSERT INTO warehouse.fact_headcount_monthly (
                    date_key, month_start_date, department_id,
                    headcount_start, hires, exits, voluntary_exits,
                    transfers_in, transfers_out, headcount_end,
                    attrition_rate_monthly_pct
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (date_key, department_id) DO UPDATE SET
                    month_start_date = EXCLUDED.month_start_date,
                    headcount_start = EXCLUDED.headcount_start,
                    hires = EXCLUDED.hires,
                    exits = EXCLUDED.exits,
                    voluntary_exits = EXCLUDED.voluntary_exits,
                    transfers_in = EXCLUDED.transfers_in,
                    transfers_out = EXCLUDED.transfers_out,
                    headcount_end = EXCLUDED.headcount_end,
                    attrition_rate_monthly_pct =
                        EXCLUDED.attrition_rate_monthly_pct
                """,
                records,
            )

    print(f"Headcount records processed: {len(df)}")

if __name__ == "__main__":
    main()
