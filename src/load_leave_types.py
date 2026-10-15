
import pandas as pd
import psycopg

FILE = "data/reference/03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"

df = pd.read_excel(FILE, sheet_name="dim_leave_type")

def flag(value):
    if pd.isna(value):
        return None
    return str(value).strip().upper() in {"Y", "YES", "TRUE", "1"}

rows = []
for _, r in df.iterrows():
    rows.append((
        str(r["leave_type_code"]).strip(),
        str(r["leave_type_name"]).strip(),
        str(r["pay_type"]).strip(),
        int(r["annual_quota_days"]),
        flag(r["prorated_for_joiners"]),
        flag(r["carry_forward_allowed"]),
        int(r["max_carry_forward_days"]),
        str(r["policy_note"]).strip(),
    ))

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
            INSERT INTO warehouse.dim_leave_type (
                leave_type_code, leave_type_name, pay_type,
                annual_quota_days, prorated_for_joiners,
                carry_forward_allowed, max_carry_forward_days,
                policy_note
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (leave_type_code) DO UPDATE SET
                leave_type_name = EXCLUDED.leave_type_name,
                pay_type = EXCLUDED.pay_type,
                annual_quota_days = EXCLUDED.annual_quota_days,
                prorated_for_joiners = EXCLUDED.prorated_for_joiners,
                carry_forward_allowed = EXCLUDED.carry_forward_allowed,
                max_carry_forward_days = EXCLUDED.max_carry_forward_days,
                policy_note = EXCLUDED.policy_note
            """,
            rows,
        )

print(f"Leave type records processed: {len(rows)}")
