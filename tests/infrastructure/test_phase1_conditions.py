"""
Phase 1 Condition System Tests

Tests for condition creation, modification, and querying.
"""

import unittest

from src.infrastructure_types import ConditionInstance, ConditionType
from src.infrastructure_utils import (
    create_condition,
    get_actor_conditions,
    get_condition,
    get_condition_severity,
    has_condition,
    modify_condition_severity,
    remove_condition,
)


class TestCreateCondition(unittest.TestCase):
    """Test condition creation."""

    def test_create_basic_condition(self) -> None:
        """Create a condition with defaults."""
        condition = create_condition(ConditionType.BLEEDING)
        self.assertEqual(condition["type"], ConditionType.BLEEDING)
        self.assertEqual(condition["severity"], 0)
        self.assertNotIn("source", condition)

    def test_create_condition_with_severity(self) -> None:
        """Create a condition with initial severity."""
        condition = create_condition(ConditionType.HYPOTHERMIA, initial_severity=50)
        self.assertEqual(condition["severity"], 50)

    def test_create_condition_with_source(self) -> None:
        """Create a condition with source tracking."""
        condition = create_condition(ConditionType.POISON, initial_severity=30, source="toxic_mushroom")
        self.assertEqual(condition["source"], "toxic_mushroom")


class TestModifyConditionSeverity(unittest.TestCase):
    """Test condition severity modification."""

    def test_increase_severity(self) -> None:
        """Increasing severity works."""
        condition: ConditionInstance = {"type": ConditionType.BLEEDING, "severity": 20}
        new_severity = modify_condition_severity(condition, 10)
        self.assertEqual(new_severity, 30)
        self.assertEqual(condition["severity"], 30)

    def test_decrease_severity(self) -> None:
        """Decreasing severity works."""
        condition: ConditionInstance = {"type": ConditionType.BLEEDING, "severity": 50}
        new_severity = modify_condition_severity(condition, -20)
        self.assertEqual(new_severity, 30)

    def test_severity_clamped_to_zero(self) -> None:
        """Severity doesn't go below 0."""
        condition: ConditionInstance = {"type": ConditionType.BLEEDING, "severity": 10}
        new_severity = modify_condition_severity(condition, -50)
        self.assertEqual(new_severity, 0)

    def test_severity_clamped_to_max(self) -> None:
        """Severity doesn't exceed max."""
        condition: ConditionInstance = {"type": ConditionType.BLEEDING, "severity": 80}
        new_severity = modify_condition_severity(condition, 50, max_severity=100)
        self.assertEqual(new_severity, 100)

    def test_custom_max_severity(self) -> None:
        """Custom max severity is respected."""
        condition: ConditionInstance = {"type": ConditionType.INFECTION, "severity": 40}
        new_severity = modify_condition_severity(condition, 30, max_severity=50)
        self.assertEqual(new_severity, 50)


class TestConditionQueries(unittest.TestCase):
    """Test condition query functions."""

    def setUp(self) -> None:
        """Create a list of conditions for testing."""
        self.conditions: list[ConditionInstance] = [
            {"type": ConditionType.BLEEDING, "severity": 30},
            {"type": ConditionType.POISON, "severity": 50, "source": "spider_venom"},
            {"type": ConditionType.HYPOTHERMIA, "severity": 20},
        ]

    def test_get_condition_exists(self) -> None:
        """Get condition returns the condition if it exists."""
        condition = get_condition(self.conditions, ConditionType.POISON)
        self.assertIsNotNone(condition)
        assert condition is not None
        self.assertEqual(condition["severity"], 50)
        self.assertEqual(condition.get("source"), "spider_venom")

    def test_get_condition_not_found(self) -> None:
        """Get condition returns None if not found."""
        condition = get_condition(self.conditions, ConditionType.DROWNING)
        self.assertIsNone(condition)

    def test_has_condition_true(self) -> None:
        """Has condition returns True when present."""
        self.assertTrue(has_condition(self.conditions, ConditionType.BLEEDING))

    def test_has_condition_false(self) -> None:
        """Has condition returns False when absent."""
        self.assertFalse(has_condition(self.conditions, ConditionType.DROWNING))

    def test_get_condition_severity_exists(self) -> None:
        """Get severity returns correct value."""
        severity = get_condition_severity(self.conditions, ConditionType.POISON)
        self.assertEqual(severity, 50)

    def test_get_condition_severity_not_found(self) -> None:
        """Get severity returns 0 for missing condition."""
        severity = get_condition_severity(self.conditions, ConditionType.DROWNING)
        self.assertEqual(severity, 0)


class TestRemoveCondition(unittest.TestCase):
    """Test condition removal."""

    def test_remove_existing_condition(self) -> None:
        """Removing existing condition returns True."""
        conditions: list[ConditionInstance] = [
            {"type": ConditionType.BLEEDING, "severity": 30},
            {"type": ConditionType.POISON, "severity": 50},
        ]
        result = remove_condition(conditions, ConditionType.BLEEDING)
        self.assertTrue(result)
        self.assertEqual(len(conditions), 1)
        self.assertFalse(has_condition(conditions, ConditionType.BLEEDING))

    def test_remove_nonexistent_condition(self) -> None:
        """Removing nonexistent condition returns False."""
        conditions: list[ConditionInstance] = [
            {"type": ConditionType.BLEEDING, "severity": 30},
        ]
        result = remove_condition(conditions, ConditionType.POISON)
        self.assertFalse(result)
        self.assertEqual(len(conditions), 1)


class TestGetActorConditions(unittest.TestCase):
    """Test actor conditions accessor."""

    def test_get_conditions_initializes(self) -> None:
        """Getting conditions initializes if missing."""
        class MockActor:
            properties: dict = {}

        actor = MockActor()
        conditions = get_actor_conditions(actor)  # type: ignore[arg-type]
        self.assertEqual(conditions, [])
        self.assertIn("conditions", actor.properties)

    def test_get_conditions_returns_existing(self) -> None:
        """Getting conditions returns existing list."""
        class MockActor:
            properties = {
                "conditions": [{"type": "injured", "severity": 20}]
            }

        actor = MockActor()
        conditions = get_actor_conditions(actor)  # type: ignore[arg-type]
        self.assertEqual(len(conditions), 1)
        self.assertEqual(conditions[0]["type"], "injured")


if __name__ == "__main__":
    unittest.main()
