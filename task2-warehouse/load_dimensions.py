import pandas as pd
import psycopg

FILE = "data/reference/03_PulseIQ_Analytics_Star_Schema_Dataset.xlsx"

departments = pd.read_excel(FILE, sheet_name="dim_department")
roles = pd.read_excel(FILE, sheet_name="dim_role")

with psycopg.connect(
    host="localhost",
    port=5433,
    dbname="pulseiq_warehouse",
    user="pulseiq",
    password="pulseiq_dev_password",
) as conn:
    with conn.cursor() as cur:
        for _, r in departments.iterrows():
            cur.execute("""
                INSERT INTO warehouse.dim_department
                    (department_id, department_name, cost_center,
                     description, is_leadership)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (department_id) DO NOTHING
            """, tuple(None if pd.isna(v) else v for v in r[
                ["department_id", "department_name", "cost_center",
                 "description", "is_leadership"]
            ]))

        for _, r in roles.iterrows():
            cur.execute("""
                INSERT INTO warehouse.dim_role
                    (role_id, department_id, role_title, level, grade,
                     band_min_annual, band_mid_annual, band_max_annual,
                     overtime_eligible, band_reference_year)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (role_id) DO NOTHING
            """, tuple(None if pd.isna(v) else v for v in r[
                ["role_id", "department_id", "role_title", "level", "grade",
                 "band_min_annual", "band_mid_annual", "band_max_annual",
                 "overtime_eligible", "band_reference_year"]
            ]))

print(f"Departments processed: {len(departments)}")
print(f"Roles processed: {len(roles)}")

# Load leave types from the reference workbook
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
leave_script = ROOT / "task1-etl" / "src" / "load_leave_types.py"

subprocess.run(
    [sys.executable, str(leave_script)],
    cwd=ROOT,
    check=True,
)

