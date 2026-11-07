"""Keep the Task 22 fixture frozen and compatible with the action-plan context."""

from integration.task22_baseline import load_frozen_cases


def test_frozen_cases_remain_valid():
    suite, _ = load_frozen_cases()
    assert suite["fixture_version"] == "task22-heldout-1"
    assert suite["scoring_version"] == "task22-action-usability-1"
