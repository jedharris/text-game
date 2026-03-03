"""Look out of command for windows and openings.

Tier 2 library behavior - reusable across games.
Uses positive testing pattern.
"""

from typing import Dict, Any, cast

from src.state_accessor import HandlerResult
from src.types import ActorId


# No vocabulary needed - relies on handler chaining with core look handler
vocabulary: Dict[str, Any] = {
    "verbs": [],
    "nouns": [],
    "adjectives": []
}


def handle_look(accessor, action: Dict[str, Any]) -> HandlerResult:
    """
    Handle 'look out of <object>' command.

    Used for windows, doors, archways - anything with a view beyond.
    Uses positive testing: only handles if preposition is "out of" or "out".
    """
    actor_id = cast(ActorId, action.get("actor_id") or ActorId("player"))
    object_name = action.get("indirect_object")
    preposition = action.get("preposition")

    # Positive testing: only handle "look out of X" or "look out X"
    if not preposition or preposition not in ["out of", "out"]:
        return HandlerResult(success=False, primary="")  # Let other handlers try

    if not object_name:
        return HandlerResult(success=False, primary="Look out of what?")

    # Find the object (can be Item or Part)
    from utilities.positioning import find_and_position_part, find_and_position_item

    # Get actor's location
    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(success=False, primary="Actor not found")

    # Try finding as part first (windows are often parts)
    part, move_msg = find_and_position_part(accessor, actor_id, object_name, actor.location)
    if part:
        target = part
    else:
        # Try as item
        adjective = action.get("indirect_adjective")
        item, move_msg = find_and_position_item(accessor, actor_id, object_name, adjective)
        if item:
            target = item
        else:
            return HandlerResult(
                success=False,
                primary=f"You don't see any {object_name} here."
            )

    # Get description (the view)
    properties = target.properties if hasattr(target, 'properties') else {}
    description = properties.get("description", f"Nothing special to see through the {target.name}.")

    # Build result with optional positioning beat
    beats = [move_msg] if move_msg else []
    return HandlerResult(success=True, primary=description, beats=beats)
