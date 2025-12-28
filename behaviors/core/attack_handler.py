"""Attack command handler for big_game.

Routes attack commands to the actor_lib combat system.
"""

from src.state_accessor import HandlerResult
from utilities.handler_utils import validate_actor_and_location, get_display_name
from utilities.utils import name_matches, find_accessible_item

# Vocabulary - register attack verb with handler
vocabulary = {
    "verbs": [
        {
            "word": "attack",
            "handler": "handle_attack",
            "synonyms": ["hit", "strike", "fight", "kill"],
            "object_required": True,
            "narration_mode": "brief"
        }
    ]
}


def handle_attack(accessor, action):
    """
    Handle attack command - routes to combat system.

    Finds target NPC and invokes on_attack event on attacker entity.
    The event handler (from actor_lib.combat) executes the actual combat.

    Args:
        accessor: StateAccessor instance
        action: Action dict with actor_id and object

    Returns:
        HandlerResult with combat result
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
        # Call combat system's on_attack handler
        from behaviors.shared.lib.actor_lib import combat

        # Build context with target_id
        context = {"target_id": target_actor.id}

        # Check if a specific weapon was specified ("attack X with Y")
        if "indirect_object" in action:
            weapon_name = action["indirect_object"]
            weapon_adjective = action.get("indirect_adjective")
            # Try to find the weapon in inventory
            weapon_item = find_accessible_item(accessor, weapon_name, actor_id, weapon_adjective)
            if weapon_item:
                # Verify it's in inventory
                if weapon_item.location == actor_id:
                    context["weapon_id"] = weapon_item.id
                else:
                    return HandlerResult(
                        success=False,
                        primary=f"You need to be holding the {weapon_item.name} to attack with it."
                    )
            else:
                return HandlerResult(
                    success=False,
                    primary=f"You don't have a {get_display_name(weapon_name)}."
                )

        result = combat.on_attack(
            attacker,
            accessor,
            context
        )

        if result.feedback:
            return HandlerResult(success=result.allow, primary=result.feedback)

        # Fallback if no feedback
        return HandlerResult(
            success=True,
            primary=f"You attack the {target_actor.name}!"
        )

    # Check for items - can't attack items
    item = find_accessible_item(accessor, target_name, actor_id)
    if item:
        return HandlerResult(
            success=False,
            primary=f"You can't attack the {item.name}."
        )

    # Target not found
    return HandlerResult(
        success=False,
        primary=f"You don't see any {get_display_name(target_name)} here."
    )
