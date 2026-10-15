
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_full_etl_pipeline_outputs():
    result = subprocess.run(
        [sys.executable, "-m", "src.pipeline"],
        cwd=ROOT / "task1-etl",
        capture_output=True,
        text=True,
        timeout=180,
    )

    assert result.returncode == 0, (
        f"Pipeline failed.\nSTDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    clean_dir = ROOT / "data" / "clean"
    rejected_dir = ROOT / "rejected"
    summary_file = ROOT / "logs" / "run_summary.json"

    datasets = ["employees", "payroll", "attendance", "leave"]

    for name in datasets:
        assert (clean_dir / f"{name}.csv").exists(), (
            f"Missing clean CSV: {name}.csv"
        )
        assert (rejected_dir / f"{name}_rejected.csv").exists(), (
            f"Missing rejected CSV: {name}_rejected.csv"
        )

    assert summary_file.exists(), "Run summary was not created"

    summary = json.loads(
        summary_file.read_text(encoding="utf-8")
    )

    assert len(summary["datasets"]) == 5
    assert summary["total_input"] > 0
    assert summary["total_output"] >= 0
    assert summary["total_rejected"] >= 0

    assert (
        summary["total_input"]
        == summary["total_output"] + summary["total_rejected"]
    )


