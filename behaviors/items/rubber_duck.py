"""Rubber duck behavior module.

A complete example demonstrating:
- Vocabulary extension (squeeze verb)
- Protocol handler (handle_squeeze)
- Entity behavior (on_squeeze)
"""

from typing import Dict, Any

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.utils import find_item_in_inventory


# Vocabulary extension - adds "squeeze" verb
vocabulary = {
    "verbs": [
        {
            "word": "squeeze",
            "event": "on_squeeze",
            "synonyms": ["squish"],
            "object_required": True
        }
    ],
    "directions": []
}


def handle_squeeze(accessor, action: Dict) -> HandlerResult:
    """
    Handle the squeeze command.

    Args:
        accessor: StateAccessor instance
        action: Action dict with verb, object, actor_id

    Returns:
        HandlerResult with success flag and message
    """
    # Extract actor_id at the top (critical for NPC support)
    actor_id = action.get("actor_id", "player")
    obj_name = action.get("object")

    if not obj_name:
        return HandlerResult(success=False, message="Squeeze what?")

    # Find item in actor's inventory
    item = find_item_in_inventory(accessor, obj_name, actor_id)

    if not item:
        return HandlerResult(success=False, message="You're not carrying that.")

    # Invoke entity behavior via accessor.update() with verb
    # This triggers on_squeeze if the item has behaviors
    result = accessor.update(item, {}, verb="squeeze", actor_id=actor_id)

    if not result.success:
        return HandlerResult(success=False, message=result.message)

    # Build response message
    base_message = f"You squeeze the {item.name}."
    if result.message:
        message = f"{base_message} {result.message}"
    else:
        message = base_message

    return HandlerResult(success=True, message=message)


def on_squeeze(entity: Any, state: Any, context: Dict) -> EventResult:
    """
    Entity behavior for being squeezed.

    Args:
        entity: The item being squeezed
        state: GameState object
        context: Context dict with location, verb

    Returns:
        EventResult with allow and message
    """
    # Increment squeak counter
    if "squeaks" not in entity.states:
        entity.states["squeaks"] = 0

    entity.states["squeaks"] += 1
    squeaks = entity.states["squeaks"]

    # Generate message based on squeak count
    if squeaks == 1:
        message = "The rubber duck lets out a satisfying squeak!"
    elif squeaks < 5:
        message = f"Squeak! (That's {squeaks} squeaks so far.)"
    elif squeaks < 10:
        message = f"The duck squeaks enthusiastically! ({squeaks} squeaks)"
    else:
        message = f"SQUEAK! The duck seems to enjoy this. ({squeaks} squeaks total)"

    return EventResult(allow=True, message=message)
