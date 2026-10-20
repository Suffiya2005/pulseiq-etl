

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TASK1_DIR = ROOT / "task1-etl"


def run_step(label, command, cwd=ROOT):
    print(f"\n=== {label} ===", flush=True)
    result = subprocess.run(
        [sys.executable, *command],
        cwd=cwd,
        check=False,
    )
    if result.returncode != 0:
        print(f"\nSTOPPED: {label} failed.")
        raise SystemExit(result.returncode)


def main():
    # The validator currently returns non-zero for any contract issue.
    # Run it first, but don't continue if it reports a problem.
    run_step("Contract validation", ["validate_contracts.py"])

    run_step("Load raw data into DuckDB", ["load_to_duckdb.py"])

    run_step(
        "Run ETL pipeline",
        ["-m", "src.pipeline"],
        cwd=TASK1_DIR,
    )


if __name__ == "__main__":
    main()
