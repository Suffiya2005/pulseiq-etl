"""Tests the real pipeline freshness function using a temporary ROOT."""

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

GATEKEEPER_PATH = (
    Path(__file__).resolve().parents[1] / "dq_gatekeeper.py"
)

spec = importlib.util.spec_from_file_location(
    "dq_gatekeeper", GATEKEEPER_PATH
)
dq_gatekeeper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dq_gatekeeper)


class TestPipelineFreshness(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.original_root = dq_gatekeeper.ROOT
        dq_gatekeeper.ROOT = Path(self.temp.name)
        self.summary_dir = dq_gatekeeper.ROOT / "logs"
        self.summary_dir.mkdir(parents=True)

    def tearDown(self):
        dq_gatekeeper.ROOT = self.original_root

    def write_summary(self, value):
        path = self.summary_dir / "run_summary.json"
        path.write_text(json.dumps(value), encoding="utf-8")

    def test_missing_summary_fails(self):
        bad_rows, status, _ = dq_gatekeeper.check_pipeline_freshness()
        self.assertEqual((bad_rows, status), (1, "FAIL"))

    def test_missing_finish_time_fails(self):
        self.write_summary({})
        bad_rows, status, _ = dq_gatekeeper.check_pipeline_freshness()
        self.assertEqual((bad_rows, status), (1, "FAIL"))

    def test_invalid_json_returns_error(self):
        path = self.summary_dir / "run_summary.json"
        path.write_text("{invalid json", encoding="utf-8")
        bad_rows, status, _ = dq_gatekeeper.check_pipeline_freshness()
        self.assertEqual((bad_rows, status), (1, "ERROR"))

    def test_recent_run_passes(self):
        recent = datetime.now(timezone.utc).isoformat()
        self.write_summary({"finished_at_utc": recent})
        bad_rows, status, _ = dq_gatekeeper.check_pipeline_freshness()
        self.assertEqual((bad_rows, status), (0, "PASS"))

    def test_old_run_fails(self):
        old = (
            datetime.now(timezone.utc) - timedelta(hours=25)
        ).isoformat()
        self.write_summary({"finished_at_utc": old})
        bad_rows, status, _ = dq_gatekeeper.check_pipeline_freshness()
        self.assertEqual((bad_rows, status), (1, "FAIL"))

    def test_future_run_fails(self):
        future = (
            datetime.now(timezone.utc) + timedelta(hours=1)
        ).isoformat()
        self.write_summary({"finished_at_utc": future})
        bad_rows, status, _ = dq_gatekeeper.check_pipeline_freshness()
        self.assertEqual((bad_rows, status), (1, "FAIL"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
