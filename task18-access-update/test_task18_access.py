import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from task18_auth import verify_password
from task18_config import (
    get_allowed_metrics,
    get_allowed_dimensions,
    get_metric_config,
    RESTRICTED_METRICS,
)

salt = b"pulseiq-test-salt"
password = "CorrectHorseBatteryStaple!"
digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
encoded = salt.hex() + "$" + digest.hex()

assert verify_password(password, encoded)
assert not verify_password("wrong-password", encoded)
assert not verify_password(password, "invalid-hash")

assert "M16" in get_allowed_metrics("ADMIN")
assert "M16" in get_allowed_metrics("EXECUTIVE")
assert "M16" not in get_allowed_metrics("HR")
assert "M16" not in get_allowed_metrics("MANAGER")
assert get_metric_config("M16", "HR") is None
assert get_metric_config("M16", "EXECUTIVE") is not None
assert all(item not in get_allowed_metrics("ADMIN") for item in RESTRICTED_METRICS)

assert get_allowed_dimensions("MANAGER") == ["Team", "Sprint"]
assert get_allowed_dimensions("HR") == ["Company", "Department"]
assert get_allowed_dimensions("UNKNOWN") == []

print("PASS: Password verification and role metric/dimension allowlists.")
