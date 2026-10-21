import pandas as pd


def check_minimum_group_size(group_counts, minimum_size):
    """Return groups that are smaller than the configured minimum."""
    return group_counts[group_counts < minimum_size]


def test_groups_meeting_minimum_pass():
    counts = pd.Series({"Engineering": 12, "Finance": 8})
    violations = check_minimum_group_size(counts, minimum_size=5)
    assert violations.empty


def test_small_group_is_detected():
    counts = pd.Series({"Engineering": 12, "Small Team": 3})
    violations = check_minimum_group_size(counts, minimum_size=5)
    assert list(violations.index) == ["Small Team"]


def test_group_at_minimum_passes():
    counts = pd.Series({"Support": 5})
    violations = check_minimum_group_size(counts, minimum_size=5)
    assert violations.empty


if __name__ == "__main__":
    test_groups_meeting_minimum_pass()
    test_small_group_is_detected()
    test_group_at_minimum_passes()
    print("DQ-C14 isolated tests: 3 passed")