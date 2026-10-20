import pandas as pd


def test_validator_detects_invalid_numeric_value():
    values = pd.Series(["100", "200", "invalid"], dtype="string")

    numeric = pd.to_numeric(values, errors="coerce")
    invalid = numeric.isna()

    assert invalid.sum() == 1


def test_validator_detects_negative_value():
    values = pd.Series(["100", "-50", "200"], dtype="string")

    numeric = pd.to_numeric(values, errors="coerce")
    invalid = numeric.notna() & (numeric < 0)

    assert invalid.sum() == 1