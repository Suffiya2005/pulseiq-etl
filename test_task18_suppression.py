import ast
from pathlib import Path
import pandas as pd

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

sample = pd.DataFrame({
    "group_name": ["A", "B", "C", "D", "E"],
    "employee_count": [1, 2, 4, 5, 6],
    "metric_value": [100, 200, 400, 500, 600],
})

result = namespace["task18_suppress_small_groups"](
    sample, "employee_count"
)

print(result.to_string(index=False))

suppressed_rows = result["privacy_status"] == "Suppressed"

assert result.loc[
    suppressed_rows, "group_name"
].isna().all()

assert result.loc[
    suppressed_rows, "metric_value"
].isna().all()

assert result.loc[
    suppressed_rows, "employee_count"
].isna().all()

print("PASS: Small-group labels, counts and metrics are hidden.")