"""
Tests for trading behavior - NPC item exchanges via give command.

Tests:
1. Give triggers on_receive_item behavior
2. Trade execution (item exchange)
3. Service payment via give
4. Generic acceptance for non-trade items
"""
from src.types import ActorId

import unittest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.state_accessor import StateAccessor, HandlerResult
from src.behavior_manager import BehaviorManager
from src.state_manager import Actor, Item
from tests.conftest import make_action, create_test_state


class TestTradingBehavior(unittest.TestCase):
    """Tests for trading behavior and give command integration."""

    def _create_trading_state(self):
        """Create test state with trader NPCs and trade items."""
        state = create_test_state()

        # Create a trader NPC with trades config
        trader = Actor(
            id="npc_trader",
            name="trader",
            description="A trader",
            location="location_room",
            inventory=["item_reward"],
            properties={
                "trades": {
                    "item_trade_good": {
                        "gives": "item_reward",
                        "message": "Thanks! Here's your reward."
                    }
                }
            },
            behaviors=["behavior_libraries.actor_lib.trading"]
        )
        state.actors[ActorId("npc_trader")] = trader

        # Create trade item (player will give this)
        trade_good = Item(
            id="item_trade_good",
            name="trade good",
            description="Something the trader wants",
            location="player",
            properties={"portable": True},
            behaviors=[]
        )
        state.items.append(trade_good)

        # Create reward item (trader will give this)
        reward = Item(
            id="item_reward",
            name="reward",
            description="A valuable reward",
            location="npc_trader",
            properties={"portable": True},
            behaviors=[]
        )
        state.items.append(reward)

        # Add trade_good to player inventory
        state.actors[ActorId("player")].inventory.append("item_trade_good")

        return state

    def test_give_triggers_on_receive_item(self):
        """Test that give command invokes on_receive_item behavior."""
        state = self._create_trading_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.manipulation
        import behavior_libraries.actor_lib.trading
        behavior_manager.load_module(behaviors.core.manipulation)
        behavior_manager.load_module(behavior_libraries.actor_lib.trading)
        accessor = StateAccessor(state, behavior_manager)

        from behaviors.core.manipulation import handle_give
        action = make_action(object="trade good", indirect_object="trader", actor_id="player")
        result = handle_give(accessor, action)

        self.assertTrue(result.success)
        # Should include the trade message
        self.assertIn("Thanks!", result.message)

    def test_trade_execution_item_exchange(self):
        """Test that trade successfully exchanges items."""
        state = self._create_trading_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.manipulation
        import behavior_libraries.actor_lib.trading
        behavior_manager.load_module(behaviors.core.manipulation)
        behavior_manager.load_module(behavior_libraries.actor_lib.trading)
        accessor = StateAccessor(state, behavior_manager)

        player = state.actors[ActorId("player")]
        trader = state.actors[ActorId("npc_trader")]

        # Before trade
        self.assertIn("item_trade_good", player.inventory)
        self.assertIn("item_reward", trader.inventory)
        self.assertNotIn("item_reward", player.inventory)

        from behaviors.core.manipulation import handle_give
        action = make_action(object="trade good", indirect_object="trader", actor_id="player")
        result = handle_give(accessor, action)

        self.assertTrue(result.success)

        # After trade - player gave trade_good, received reward
        self.assertNotIn("item_trade_good", player.inventory)
        self.assertIn("item_trade_good", trader.inventory)
        self.assertIn("item_reward", player.inventory)
        self.assertNotIn("item_reward", trader.inventory)

    def test_give_non_trade_item_generic_acceptance(self):
        """Test that giving non-trade item results in generic acceptance."""
        state = self._create_trading_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.manipulation
        import behavior_libraries.actor_lib.trading
        behavior_manager.load_module(behaviors.core.manipulation)
        behavior_manager.load_module(behavior_libraries.actor_lib.trading)
        accessor = StateAccessor(state, behavior_manager)

        player = state.actors[ActorId("player")]

        # Give the sword (not a trade item) to the trader
        sword = state.get_item("item_sword")
        sword.location = "player"
        player.inventory.append("item_sword")

        from behaviors.core.manipulation import handle_give
        action = make_action(object="sword", indirect_object="trader", actor_id="player")
        result = handle_give(accessor, action)

        self.assertTrue(result.success)
        # Should have generic acceptance message
        self.assertIn("accepts", result.message.lower())

    def test_trade_without_reward_item(self):
        """Test trade when NPC doesn't have the reward item."""
        state = self._create_trading_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.manipulation
        import behavior_libraries.actor_lib.trading
        behavior_manager.load_module(behaviors.core.manipulation)
        behavior_manager.load_module(behavior_libraries.actor_lib.trading)
        accessor = StateAccessor(state, behavior_manager)

        # Remove reward from trader inventory
        trader = state.actors[ActorId("npc_trader")]
        trader.inventory.remove("item_reward")

        from behaviors.core.manipulation import handle_give
        action = make_action(object="trade good", indirect_object="trader", actor_id="player")
        result = handle_give(accessor, action)

        self.assertTrue(result.success)
        # Should mention they can't provide anything
        self.assertIn("unable to provide", result.message.lower())

    def test_give_to_npc_without_trading_behavior(self):
        """Test giving to NPC that doesn't have trading behavior loads gracefully."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behaviors.core.manipulation
        behavior_manager.load_module(behaviors.core.manipulation)
        accessor = StateAccessor(state, behavior_manager)

        # Create NPC without trading behavior
        guard = Actor(
            id="npc_guard",
            name="guard",
            description="A guard",
            location="location_room",
            inventory=[],
            properties={},
            behaviors=[]
        )
        state.actors[ActorId("npc_guard")] = guard

        # Give sword to guard
        player = state.actors[ActorId("player")]
        sword = state.get_item("item_sword")
        sword.location = "player"
        player.inventory.append("item_sword")

        from behaviors.core.manipulation import handle_give
        action = make_action(object="sword", indirect_object="guard", actor_id="player")
        result = handle_give(accessor, action)

        # Should succeed (basic give works)
        self.assertTrue(result.success)
        # Item should be transferred
        self.assertIn("item_sword", guard.inventory)


class TestOnReceiveItemBehavior(unittest.TestCase):
    """Direct tests for on_receive_item behavior function."""

    def test_on_receive_item_with_trade(self):
        """Test on_receive_item finds and executes a trade."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behavior_libraries.actor_lib.trading
        behavior_manager.load_module(behavior_libraries.actor_lib.trading)
        accessor = StateAccessor(state, behavior_manager)

        # Create trader with trade config
        trader = Actor(
            id="npc_trader",
            name="trader",
            description="A trader",
            location="location_room",
            inventory=["item_reward"],
            properties={
                "trades": {
                    "item_test": {
                        "gives": "item_reward",
                        "message": "Trade complete!"
                    }
                }
            },
            behaviors=[]
        )
        state.actors[ActorId("npc_trader")] = trader

        # Create items
        test_item = Item(
            id="item_test",
            name="test item",
            description="A test item",
            location="player",
            properties={"portable": True},
            behaviors=[]
        )
        state.items.append(test_item)

        reward = Item(
            id="item_reward",
            name="reward",
            description="A reward",
            location="npc_trader",
            properties={"portable": True},
            behaviors=[]
        )
        state.items.append(reward)

        from behavior_libraries.actor_lib.trading import on_receive_item
        context = {
            "item_id": "item_test",
            "item": test_item,
            "giver_id": "player"
        }
        result = on_receive_item(trader, accessor, context)

        self.assertTrue(result.allow)
        self.assertEqual("Trade complete!", result.message)

        # Check reward transferred
        player = state.actors[ActorId("player")]
        self.assertIn("item_reward", player.inventory)

    def test_on_receive_item_no_trade_generic_accept(self):
        """Test on_receive_item with no matching trade gives generic acceptance."""
        state = create_test_state()
        behavior_manager = BehaviorManager()
        import behavior_libraries.actor_lib.trading
        behavior_manager.load_module(behavior_libraries.actor_lib.trading)
        accessor = StateAccessor(state, behavior_manager)

        # Create trader without trades for the given item
        trader = Actor(
            id="npc_trader",
            name="trader",
            description="A trader",
            location="location_room",
            inventory=[],
            properties={
                "trades": {
                    "item_something_else": {
                        "gives": "item_other",
                        "message": "Different trade"
                    }
                }
            },
            behaviors=[]
        )
        state.actors[ActorId("npc_trader")] = trader

        sword = state.get_item("item_sword")

        from behavior_libraries.actor_lib.trading import on_receive_item
        context = {
            "item_id": "item_sword",
            "item": sword,
            "giver_id": "player"
        }
        result = on_receive_item(trader, accessor, context)

        self.assertTrue(result.allow)
        self.assertIn("accepts", result.message.lower())
        self.assertIn("sword", result.message.lower())


if __name__ == "__main__":
    unittest.main()
