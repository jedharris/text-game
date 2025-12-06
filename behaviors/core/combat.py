"""Combat behaviors - attack.

Vocabulary and handlers for combat actions.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from utilities.utils import find_accessible_item, name_matches
from utilities.handler_utils import get_display_name, validate_actor_and_location


# Vocabulary extension - adds attack verb
vocabulary = {
    "verbs": [
        {
            "word": "attack",
            "event": "on_attack",
            "synonyms": ["hit", "strike", "fight", "kill"],
            "object_required": True,
            "narration_mode": "brief",
            "llm_context": {
                "traits": ["hostile action", "targets NPCs", "may have consequences"],
                "failure_narration": {
                    "not_found": "cannot find target",
                    "cannot_attack": "cannot attack that"
                }
            }
        }
    ],
    "nouns": [],
    "adjectives": [],
    "directions": []
}


def handle_attack(accessor, action):
    """
    Handle attack/hit/strike command.

    Allows an actor to attack another actor (NPC).

    CRITICAL: Extracts actor_id from action to support both player and NPCs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of target to attack (required)

    Returns:
        HandlerResult with success flag and message
    """
    # Validate actor and location
    actor_id, attacker, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error

    target_name = action.get("object")

    # Look for target NPC in same location
    target_actor = None
    for actor in accessor.game_state.actors.values():
        if actor.id != actor_id and actor.location == location.id:
            if name_matches(target_name, actor.name):
                target_actor = actor
                break

    if target_actor:
        # Found an NPC to attack - invoke entity behaviors
        result = accessor.update(
            target_actor,
            {},  # No state changes by default
            verb="attack",
            actor_id=actor_id
        )

        # Build message - include behavior message if present
        base_message = f"You attack the {target_actor.name}!"
        if result.message:
            return HandlerResult(success=True, message=f"{base_message} {result.message}")

        return HandlerResult(success=True, message=base_message)

    # Check for items - can't attack items
    item = find_accessible_item(accessor, target_name, actor_id)
    if item:
        return HandlerResult(
            success=False,
            message=f"You can't attack the {item.name}."
        )

    # Target not found
    return HandlerResult(
        success=False,
        message=f"You don't see any {get_display_name(target_name)} here."
    )
