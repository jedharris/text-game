"""Magic wand behavior module.

Demonstrates:
- Adding a new verb (wave)
- Item must be in inventory to use
- Modifying item state through behavior
"""

from typing import Dict, Any, cast

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from src.types import ActorId
from utilities.utils import find_item_in_inventory


# Vocabulary extension - adds "wave" verb
vocabulary = {
    "verbs": [
        {
            "word": "wave",
            "event": "on_wave",
            "synonyms": ["brandish", "flourish"],
            "object_required": True
        }
    ],
    "nouns": [],
    "adjectives": []
}


def handle_wave(accessor, action: Dict) -> HandlerResult:
    """
    Handle the wave command.

    Args:
        accessor: StateAccessor instance
        action: Action dict with verb, object, actor_id

    Returns:
        HandlerResult with success flag and message
    """
    actor_id = cast(ActorId, action.get("actor_id") or ActorId("player"))
    obj_name = action.get("object")

    if not obj_name:
        return HandlerResult(success=False, primary="Wave what?")

    # Must be holding the item to wave it
    item = find_item_in_inventory(accessor, obj_name, actor_id)

    if not item:
        return HandlerResult(
            success=False,
            primary=f"You need to be holding the {obj_name} to wave it."
        )

    # Invoke entity behavior via accessor.update() with verb
    result = accessor.update(item, {}, verb="wave", actor_id=actor_id)

    if not result.success:
        return HandlerResult(success=False, primary=result.detail)

    # Build response message
    if result.detail:
        message = result.detail
    else:
        message = f"You wave the {item.name} around, but nothing happens."

    return HandlerResult(success=True, primary=message)


def on_wave(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Entity behavior for being waved.

    This is called when the magic wand is waved.

    Args:
        entity: The wand
        accessor: StateAccessor instance
        context: Context dict with actor_id, verb

    Returns:
        EventResult with allow and message
    """
    properties = entity.properties if hasattr(entity, 'properties') else {}

    # Check if this is a magical item
    if not properties.get("magical", False):
        return EventResult(allow=True, feedback=None)  # Default message will be used

    # Track wand usage
    if not hasattr(entity, 'states') or entity.states is None:
        entity.states = {}

    wave_count = entity.states.get("wave_count", 0) + 1
    entity.states["wave_count"] = wave_count

    # Generate messages based on wave count
    if wave_count == 1:
        message = (
            "You wave the wand dramatically!\n"
            "Sparks of light burst from its tip, illuminating the room.\n"
            "You feel a tingle of magical energy run through your arm."
        )
    elif wave_count == 2:
        message = (
            "You wave the wand again!\n"
            "A shower of golden stars erupts from the crystal tip.\n"
            "They spiral upward before fading away."
        )
    elif wave_count == 3:
        message = (
            "You wave the wand with a flourish!\n"
            "The crystal tip glows brightly, then dims.\n"
            "For a moment, you could swear you saw the wizard's ghost smile at you."
        )
    elif wave_count < 10:
        message = (
            "You wave the wand.\n"
            "A few sparks sputter from the tip. The wand seems tired."
        )
    else:
        message = (
            "You wave the wand, but it only produces a weak flicker.\n"
            "Perhaps some magics have limits."
        )

    return EventResult(allow=True, feedback=message)
