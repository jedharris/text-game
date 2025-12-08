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
