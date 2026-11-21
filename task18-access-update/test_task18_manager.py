import ast
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import psycopg
from dotenv import load_dotenv

from task18_manager import load_manager_metric, MANAGER_METRICS
from task18_config import METRICS
load_dotenv(Path(".env"))

# Extract the real suppression function without importing Streamlit app.py.
source = Path("app.py").read_text(encoding="utf-8-sig")
tree = ast.parse(source)

function_node = next(
    node for node in tree.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "task18_suppress_small_groups"
)

module = ast.Module(body=[function_node], type_ignores=[])
code = compile(module, "app.py", "exec")

namespace = {"pd": pd, "MIN_EMPLOYEES": 5}
exec(code, namespace)
suppress_fn = namespace["task18_suppress_small_groups"]


def query_runner(query, params=None):
    with psycopg.connect(
        host=os.getenv("WAREHOUSE_HOST", "localhost"),
        port=int(os.getenv("WAREHOUSE_PORT", "5433")),
        dbname=os.getenv("WAREHOUSE_DB", "pulseiq_warehouse"),
        user=os.environ["TASK18_DB_USER"],
        password=os.environ["TASK18_DB_PASSWORD"],
        connect_timeout=10,
    ) as conn:
        return pd.read_sql_query(query, conn, params=params)


# Temporary test scope only. This is not a real Manager account.
departments = ["D03"]

assert MANAGER_METRICS == {"M22", "M23", "M24", "M25"}

for metric_id in sorted(MANAGER_METRICS):
    config = METRICS[metric_id]

    result = load_manager_metric(
        metric_id=metric_id,
        department_ids=departments,
        query_runner=query_runner,
        suppress_fn=suppress_fn,
        metric_config=config,
    )

    print(f"\n{metric_id} - {config['name']}")
    print("Returned groups:", len(result))

    if result is not None and not result.empty:
        print(result[
            ["reporting_period", "dimension_value",
             "metric_value", "privacy_count", "privacy_status"]
        ].to_string(index=False))

        suppressed = result["privacy_status"].eq("Suppressed")

        assert result.loc[suppressed, "metric_value"].isna().all()
        assert result.loc[suppressed, "privacy_count"].isna().all()
        assert result.loc[suppressed, "dimension_value"].isna().all()
        assert result.loc[suppressed, "group_name"].isna().all()
        assert result.loc[suppressed, "reporting_period"].isna().all()

    print(f"PASS: {metric_id} query and suppression checks")


# Reject KPIs outside the Manager allowlist.
try:
    load_manager_metric(
        "M01", departments, query_runner, suppress_fn, {}
    )
    raise AssertionError("Unauthorized KPI was not rejected")
except PermissionError:
    print("\nPASS: Unauthorized KPI rejected")
# Reject an empty department assignment.
try:
    load_manager_metric(
        "M22", [], query_runner, suppress_fn, dict(METRICS["M22"])
    )
    raise AssertionError("Empty department assignment was accepted.")
except PermissionError:
    print("PASS: Empty department assignment rejected")

# Reject an invalid department ID.
try:
    load_manager_metric(
        "M22", ["INVALID"], query_runner, suppress_fn, dict(METRICS["M22"])
    )
    raise AssertionError("Invalid department ID was accepted.")
except PermissionError:
    print("PASS: Invalid department ID rejected")

# Reject a privacy threshold below five.
bad_config = dict(METRICS["M22"])
bad_config["minimum"] = 4

try:
    load_manager_metric(
        "M22", departments, query_runner, suppress_fn, bad_config
    )
    raise AssertionError("Privacy threshold below five was accepted")
except ValueError:
    print("PASS: Privacy threshold below five rejected")


print("\nALL MANAGER KPI INTEGRATION CHECKS PASSED")
