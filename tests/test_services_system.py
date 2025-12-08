"""Tests for services framework (Phase 6 of Actor Interaction)."""

import unittest
from unittest.mock import Mock

from src.state_manager import Actor, Item, Location, GameState, Metadata
from src.state_accessor import StateAccessor


class TestGetAvailableServices(unittest.TestCase):
    """Test get_available_services function."""

    def test_get_services_returns_dict(self):
        """Returns services dict from NPC properties."""
        from behaviors.actors.services import get_available_services

        npc = Actor(
            id="npc_healer",
            name="Healer",
            description="A healer",
            location="loc_test",
            inventory=[],
            properties={
                "services": {
                    "cure": {"accepts": ["gold"], "amount_required": 5, "cure_amount": 100},
                    "heal": {"accepts": ["gold"], "amount_required": 3, "restore_amount": 50}
                }
            }
        )

        services = get_available_services(npc)

        self.assertEqual(len(services), 2)
        self.assertIn("cure", services)
        self.assertIn("heal", services)

    def test_get_services_empty(self):
        """Returns empty dict if NPC has no services."""
        from behaviors.actors.services import get_available_services

        npc = Actor(
            id="npc_guard",
            name="Guard",
            description="A guard",
            location="loc_test",
            inventory=[],
            properties={}
        )

        services = get_available_services(npc)

        self.assertEqual(services, {})

    def test_get_services_none_actor(self):
        """Returns empty dict for None actor."""
        from behaviors.actors.services import get_available_services

        services = get_available_services(None)

        self.assertEqual(services, {})


class TestGetServiceCost(unittest.TestCase):
    """Test get_service_cost function."""

    def setUp(self):
        """Create test NPC with services."""
        self.npc = Actor(
            id="npc_healer",
            name="Healer",
            description="A healer",
            location="loc_test",
            inventory=[],
            properties={
                "services": {
                    "cure": {"accepts": ["gold"], "amount_required": 10, "cure_amount": 100}
                }
            }
        )

        self.customer = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_test",
            inventory=[],
            properties={}
        )

    def test_get_service_cost_base(self):
        """Returns base cost when no relationship."""
        from behaviors.actors.services import get_service_cost

        cost = get_service_cost(self.npc, "cure", self.customer)

        self.assertEqual(cost, 10)

    def test_get_service_cost_trust_discount(self):
        """High trust gives 50% discount."""
        from behaviors.actors.services import get_service_cost

        # NPC trusts customer
        self.npc.properties["relationships"] = {
            "player": {"trust": 3}
        }

        cost = get_service_cost(self.npc, "cure", self.customer)

        self.assertEqual(cost, 5)  # 50% off

    def test_get_service_cost_low_trust_no_discount(self):
        """Trust below threshold gives no discount."""
        from behaviors.actors.services import get_service_cost

        self.npc.properties["relationships"] = {
            "player": {"trust": 2}
        }

        cost = get_service_cost(self.npc, "cure", self.customer)

        self.assertEqual(cost, 10)  # No discount

    def test_get_service_cost_unknown_service(self):
        """Returns 0 for unknown service."""
        from behaviors.actors.services import get_service_cost

        cost = get_service_cost(self.npc, "unknown_service", self.customer)

        self.assertEqual(cost, 0)


class TestCanAffordService(unittest.TestCase):
    """Test can_afford_service function."""

    def setUp(self):
        """Create test actors and items."""
        self.npc = Actor(
            id="npc_healer",
            name="Healer",
            description="A healer",
            location="loc_test",
            inventory=[],
            properties={
                "services": {
                    "cure": {"accepts": ["gold"], "amount_required": 5, "cure_amount": 100}
                }
            }
        )

        self.customer = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_test",
            inventory=["item_gold"],
            properties={}
        )

        self.gold = Item(
            id="item_gold",
            name="gold",
            description="Gold coins",
            location="player",
            properties={"type": "gold", "amount": 10}
        )

        self.location = Location(
            id="loc_test",
            name="Test",
            description="Test"
        )

    def test_can_afford_with_enough_gold(self):
        """Returns True when customer has enough payment."""
        from behaviors.actors.services import can_afford_service

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[self.gold],
            actors={"player": self.customer, "npc_healer": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        can_afford, reason = can_afford_service(accessor, self.customer, "cure", self.npc)

        self.assertTrue(can_afford)

    def test_cannot_afford_insufficient_gold(self):
        """Returns False when customer doesn't have enough."""
        from behaviors.actors.services import can_afford_service

        self.gold.properties["amount"] = 2  # Less than required 5

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[self.gold],
            actors={"player": self.customer, "npc_healer": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        can_afford, reason = can_afford_service(accessor, self.customer, "cure", self.npc)

        self.assertFalse(can_afford)
        self.assertIn("not enough", reason.lower())

    def test_cannot_afford_wrong_payment_type(self):
        """Returns False when customer has wrong payment type."""
        from behaviors.actors.services import can_afford_service

        # Customer only has herbs, but service accepts gold
        herb = Item(
            id="item_herb",
            name="herb",
            description="An herb",
            location="player",
            properties={"type": "herb", "amount": 10}
        )

        self.customer.inventory = ["item_herb"]

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[herb],
            actors={"player": self.customer, "npc_healer": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        can_afford, reason = can_afford_service(accessor, self.customer, "cure", self.npc)

        self.assertFalse(can_afford)


class TestExecuteService(unittest.TestCase):
    """Test execute_service function."""

    def setUp(self):
        """Create test actors and items."""
        self.npc = Actor(
            id="npc_healer",
            name="Healer",
            description="A healer",
            location="loc_test",
            inventory=[],
            properties={
                "services": {
                    "cure": {"accepts": ["gold"], "amount_required": 5, "cure_amount": 100},
                    "teach_herbalism": {"accepts": ["gold"], "amount_required": 10, "grants": "herbalism"},
                    "heal": {"accepts": ["gold"], "amount_required": 3, "restore_amount": 50}
                }
            }
        )

        self.customer = Actor(
            id="player",
            name="Player",
            description="Test",
            location="loc_test",
            inventory=["item_gold"],
            properties={
                "health": 50,
                "max_health": 100,
                "conditions": {
                    "poison": {"severity": 30}
                }
            }
        )

        self.gold = Item(
            id="item_gold",
            name="gold",
            description="Gold coins",
            location="player",
            properties={"type": "gold", "amount": 20}
        )

        self.location = Location(
            id="loc_test",
            name="Test",
            description="Test"
        )

    def test_execute_service_cure(self):
        """Cure service removes conditions."""
        from behaviors.actors.services import execute_service

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[self.gold],
            actors={"player": self.customer, "npc_healer": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = execute_service(accessor, self.customer, self.npc, "cure", self.gold)

        self.assertTrue(result.success)
        # Condition should be removed
        self.assertNotIn("poison", self.customer.properties.get("conditions", {}))

    def test_execute_service_teach(self):
        """Teaching service grants knowledge."""
        from behaviors.actors.services import execute_service

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[self.gold],
            actors={"player": self.customer, "npc_healer": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = execute_service(accessor, self.customer, self.npc, "teach_herbalism", self.gold)

        self.assertTrue(result.success)
        # Customer should have learned herbalism
        self.assertIn("herbalism", self.customer.properties.get("knows", []))

    def test_execute_service_heal(self):
        """Healing service restores health."""
        from behaviors.actors.services import execute_service

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[self.gold],
            actors={"player": self.customer, "npc_healer": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = execute_service(accessor, self.customer, self.npc, "heal", self.gold)

        self.assertTrue(result.success)
        # Health should be restored (50 + 50 = 100)
        self.assertEqual(self.customer.properties["health"], 100)

    def test_execute_service_heal_capped(self):
        """Healing doesn't exceed max health."""
        from behaviors.actors.services import execute_service

        self.customer.properties["health"] = 80  # Only needs 20

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[self.gold],
            actors={"player": self.customer, "npc_healer": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = execute_service(accessor, self.customer, self.npc, "heal", self.gold)

        self.assertTrue(result.success)
        # Health capped at max
        self.assertEqual(self.customer.properties["health"], 100)

    def test_execute_service_payment_accepted(self):
        """Correct payment type is accepted."""
        from behaviors.actors.services import execute_service

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[self.gold],
            actors={"player": self.customer, "npc_healer": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = execute_service(accessor, self.customer, self.npc, "heal", self.gold)

        self.assertTrue(result.success)

    def test_execute_service_payment_rejected(self):
        """Wrong payment type is rejected."""
        from behaviors.actors.services import execute_service

        # Payment item that service doesn't accept
        herb = Item(
            id="item_herb",
            name="herb",
            description="An herb",
            location="player",
            properties={"type": "herb", "amount": 100}
        )

        self.customer.inventory = ["item_herb"]

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[herb],
            actors={"player": self.customer, "npc_healer": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = execute_service(accessor, self.customer, self.npc, "heal", herb)

        self.assertFalse(result.success)
        self.assertIn("doesn't accept", result.message.lower())

    def test_execute_service_insufficient_payment(self):
        """Insufficient payment amount is rejected."""
        from behaviors.actors.services import execute_service

        self.gold.properties["amount"] = 1  # Less than required

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[self.gold],
            actors={"player": self.customer, "npc_healer": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = execute_service(accessor, self.customer, self.npc, "heal", self.gold)

        self.assertFalse(result.success)
        self.assertIn("not enough", result.message.lower())

    def test_execute_service_unknown_service(self):
        """Unknown service is rejected."""
        from behaviors.actors.services import execute_service

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[self.gold],
            actors={"player": self.customer, "npc_healer": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = execute_service(accessor, self.customer, self.npc, "unknown", self.gold)

        self.assertFalse(result.success)
        self.assertIn("doesn't offer", result.message.lower())

    def test_execute_service_consumes_payment(self):
        """Payment item is consumed after service."""
        from behaviors.actors.services import execute_service

        game_state = GameState(
            metadata=Metadata(title="Test", start_location="loc_test"),
            locations=[self.location],
            items=[self.gold],
            actors={"player": self.customer, "npc_healer": self.npc},
            locks=[],
            parts=[]
        )

        accessor = StateAccessor(game_state, None)

        result = execute_service(accessor, self.customer, self.npc, "heal", self.gold)

        self.assertTrue(result.success)
        # Payment should be consumed (removed from inventory)
        self.assertNotIn("item_gold", self.customer.inventory)


class TestServiceResult(unittest.TestCase):
    """Test ServiceResult dataclass."""

    def test_service_result_creation(self):
        """ServiceResult can be created with all fields."""
        from behaviors.actors.services import ServiceResult

        result = ServiceResult(
            success=True,
            service_provided="heal",
            message="Healer provides heal"
        )

        self.assertTrue(result.success)
        self.assertEqual(result.service_provided, "heal")


class TestServicesVocabulary(unittest.TestCase):
    """Test services vocabulary exports."""

    def test_vocabulary_has_events(self):
        """Vocabulary exports events."""
        from behaviors.actors.services import vocabulary

        self.assertIn("events", vocabulary)


if __name__ == '__main__':
    unittest.main()
