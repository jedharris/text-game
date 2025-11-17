"""
Helper utilities for state manager tests.
"""
import json
from pathlib import Path
from typing import Any, Dict


def get_fixture_path(filename: str) -> Path:
    """Get the absolute path to a test fixture file."""
    return Path(__file__).parent / "fixtures" / filename


def load_fixture(filename: str) -> Dict[str, Any]:
    """Load a JSON fixture file and return parsed data."""
    fixture_path = get_fixture_path(filename)
    with open(fixture_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def assert_validation_error_contains(error, expected_substring: str):
    """
    Assert that a validation error message contains expected text.

    Args:
        error: The ValidationError exception
        expected_substring: Substring expected in error message
    """
    error_str = str(error)
    assert expected_substring in error_str, (
        f"Expected '{expected_substring}' in error message, "
        f"got: {error_str}"
    )


def assert_ids_match(actual_ids: set, expected_ids: set):
    """Assert that two sets of IDs match exactly."""
    missing = expected_ids - actual_ids
    extra = actual_ids - expected_ids

    assert not missing and not extra, (
        f"ID mismatch:\n"
        f"  Missing: {missing}\n"
        f"  Extra: {extra}"
    )


def normalize_json(data: Dict[str, Any]) -> str:
    """
    Normalize JSON for comparison by sorting keys and consistent formatting.

    Args:
        data: Dictionary to normalize

    Returns:
        Normalized JSON string
    """
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)


def json_equal(data1: Dict[str, Any], data2: Dict[str, Any]) -> bool:
    """
    Compare two JSON structures for semantic equality.

    Args:
        data1: First dictionary
        data2: Second dictionary

    Returns:
        True if semantically equal
    """
    return normalize_json(data1) == normalize_json(data2)
