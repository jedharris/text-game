"""Rubber duck behavior module.

A complete example demonstrating:
- Vocabulary extension (squeeze verb)
- Protocol handler (handle_squeeze)
- Entity behavior (on_squeeze)
"""

from typing import Dict, Any

from src.behavior_manager import EventResult


# Vocabulary extension - adds "squeeze" verb
vocabulary = {
    "verbs": [
        {
            "word": "squeeze",
            "synonyms": ["squish", "press"],
            "object_required": True
        }
    ],
    "directions": []
}


def handle_squeeze(state: Any, action: Dict, context: Dict) -> Dict:
    """
    Handle the squeeze command.

    Args:
        state: GameState object
        action: Action dict with verb, object, etc.
        context: Context dict with location, verb

    Returns:
        Result dict for JSON protocol
    """
    obj_name = action.get("object")

    if not obj_name:
        return {
            "type": "result",
            "success": False,
            "action": "squeeze",
            "error": {"message": "Squeeze what?"}
        }

    # Find item in inventory
    item = None
    for item_id in state.player.inventory:
        for i in state.items:
            if i.id == item_id and i.name == obj_name:
                item = i
                break
        if item:
            break

    if not item:
        return {
            "type": "result",
            "success": False,
            "action": "squeeze",
            "error": {"message": "You're not carrying that."}
        }

    # Build result with entity_obj for behavior invocation
    result = {
        "type": "result",
        "success": True,
        "action": "squeeze",
        "entity": {
            "id": item.id,
            "name": item.name,
            "type": "item",
            "description": item.description
        },
        "entity_obj": item
    }

    # Apply behavior if present
    from src.behavior_manager import get_behavior_manager
    manager = get_behavior_manager()

    event_name = "on_squeeze"
    behavior_context = {
        "location": state.player.location,
        "verb": "squeeze"
    }

    behavior_result = manager.invoke_behavior(item, event_name, state, behavior_context)

    # Remove entity_obj from result
    del result["entity_obj"]

    if behavior_result:
        if behavior_result.message:
            result["message"] = behavior_result.message
        if not behavior_result.allow:
            result["success"] = False

    return result


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
