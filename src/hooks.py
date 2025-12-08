"""
Well-known hook names used by the engine.

Hooks are stable engine contracts. Modules wire events to hooks via vocabulary.
Engine code uses hook names, never event names directly.

Example usage:
    from src.hooks import LOCATION_ENTERED

    event = behavior_manager.get_event_for_hook(LOCATION_ENTERED)
    if event:
        behavior_manager.invoke_behavior(destination, event, accessor, context)
"""

# Location events
LOCATION_ENTERED = "location_entered"

# Visibility events
VISIBILITY_CHECK = "visibility_check"

# Turn phase hooks (fire after successful player command)
# These hooks fire in order after each successful command to progress game time.
NPC_ACTION = "npc_action"
ENVIRONMENTAL_EFFECT = "environmental_effect"
CONDITION_TICK = "condition_tick"
DEATH_CHECK = "death_check"
