"""Golem Puzzle for Frozen Reaches.

Implements the multi-solution golem deactivation puzzle
with password, control crystal, ritual, and combat options.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_utils import transition_state, get_current_state

# Vocabulary: wire hooks to events
# Note: Dialog reactions (password) are handled by infrastructure/dialog_reactions.py
# Note: Item use reactions are handled by infrastructure/item_use_reactions.py
# Note: Death reactions are handled by infrastructure/death_reactions.py
# Golems must have dialog_reactions, item_use_reactions, and death_reactions config
vocabulary: Dict[str, Any] = {
    "events": [
        {
            "event": "on_damage",
            "description": "Called when a golem takes damage - transitions both to hostile"
        }
    ],
    # Add adjectives for multi-word item/NPC names
    "adjectives": [
        {"word": "stone", "synonyms": []},
        {"word": "control", "synonyms": []},
        {"word": "command", "synonyms": []},  # for command_crystal
        {"word": "crystal", "synonyms": []},
        {"word": "mounting", "synonyms": []},
        {"word": "cold", "synonyms": []},
        {"word": "resistance", "synonyms": []},
        {"word": "lore", "synonyms": []},  # for lore_tablets
        {"word": "fire", "synonyms": []},  # for fire_crystal
    ]
}

# The correct password (case-insensitive)
GOLEM_PASSWORD = "fire-that-gives-life and water-that-cleanses, united in purpose"

# Keywords that might contain the password
PASSWORD_KEYWORDS = [
    "fire",
    "water",
    "united",
    "purpose",
    "gives-life",
    "cleanses",
]


def on_golem_password(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Check if player speaks the correct password.

    The password deactivates both golems to passive state.

    Args:
        entity: The golem being addressed
        accessor: StateAccessor instance
        context: Context with keyword/dialog_text

    Returns:
        EventResult with deactivation result
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if not actor_id or "golem" not in actor_id.lower():
        return EventResult(allow=True, feedback=None)

    # Check for password in dialog
    dialog_text = context.get("dialog_text", "").lower()
    keyword = context.get("keyword", "").lower()
    full_text = f"{dialog_text} {keyword}"

    # If no keyword provided (from "talk to guardian"), provide hint
    if not full_text.strip():
        return EventResult(
            allow=True,
            feedback=(
                "The golem remains motionless, watching with eyeless vigilance. "
                "Ancient inscriptions on the walls might hold the key to passage."
            )
        )

    # Check if password matches (simplified check - key phrases present)
    key_phrases = ["fire-that-gives-life", "water-that-cleanses", "united in purpose"]
    matches = sum(1 for phrase in key_phrases if phrase in full_text)

    if matches < 2:
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state

    # Deactivate both golems
    _deactivate_golems(state, "passive")

    return EventResult(
        allow=True,
        feedback=(
            "The ancient words echo through the sanctum. Both golems freeze, "
            "their runes shifting from red to a calm blue. They step aside, "
            "allowing passage but not offering service. The password is accepted."
        ),
    )


def on_golem_item_use(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle using items on golems (control crystal or ritual items).

    Routes to appropriate handler based on item type.

    Args:
        entity: The item being used
        accessor: StateAccessor instance
        context: Context with target

    Returns:
        EventResult with result
    """
    item_id = entity.id if hasattr(entity, "id") else str(entity)
    item_lower = item_id.lower()

    # Check for command crystal first (specific item)
    if "command_crystal" in item_lower or "command_orb" in item_lower:
        return _handle_control_crystal(entity, accessor, context)

    # Check for ritual items (fire + water combination)
    return _handle_ritual(entity, accessor, context)


def _handle_control_crystal(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle using the control crystal on golems.

    The control crystal gives full control - golems serve the player.
    """
    target = context.get("target")
    target_id = target.id if target and hasattr(target, "id") else str(target) if target else ""
    if "golem" not in target_id.lower() and "sanctum" not in target_id.lower():
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state

    # Take full control of both golems
    _deactivate_golems(state, "serving")
    state.extra["golem_control"] = True

    return EventResult(
        allow=True,
        feedback=(
            "The control crystal flares with power as you raise it. Both golems "
            "immediately kneel, their runes blazing white. They await your commands, "
            "bound to serve whoever holds the crystal. This is their original purpose."
        ),
    )


def _handle_ritual(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle ritual offering to golems.

    Fire item + hot springs water = ancient protocol recognized.
    """
    item_id = entity.id if hasattr(entity, "id") else str(entity)
    item_lower = item_id.lower()

    state = accessor.game_state

    # Check for fire + water combination
    has_fire = any(
        fire in item_lower
        for fire in ["fire", "torch", "flame", "ember", "crystal"]
    )
    has_water = "spring" in item_lower or "water" in item_lower

    # Check if other component is present
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, feedback=None)

    inventory = str(player.inventory)

    if has_fire and not has_water:
        if "spring" not in inventory.lower() and "water" not in inventory.lower():
            return EventResult(allow=True, feedback=None)
    elif has_water and not has_fire:
        if not any(f in inventory.lower() for f in ["fire", "torch", "flame", "ember"]):
            return EventResult(allow=True, feedback=None)
    elif not has_fire and not has_water:
        return EventResult(allow=True, feedback=None)

    # Check location (must be in temple)
    player_loc = player.properties.get("location", "")
    if "temple" not in player_loc.lower() and "sanctum" not in player_loc.lower():
        return EventResult(allow=True, feedback=None)

    # Ritual succeeds
    _deactivate_golems(state, "passive")
    state.extra["golem_ritual_completed"] = True

    return EventResult(
        allow=True,
        feedback=(
            "You combine fire and water in the ancient manner. Steam rises, "
            "carrying the essence of both elements. The golems pause, recognizing "
            "the protocol of their creators. Their runes shift to blue as they "
            "step aside, acknowledging your right of passage."
        ),
    )


def on_golem_death(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle golem destruction consequences.

    Destroying golems loses their future protection value.

    Args:
        entity: The golem that died
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult noting the loss
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if not actor_id or "golem" not in actor_id.lower():
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state

    # Track destruction
    destroyed = state.extra.get("golems_destroyed", 0)
    state.extra["golems_destroyed"] = destroyed + 1

    # Check if both destroyed
    golem1 = state.actors.get("stone_golem_1")
    golem2 = state.actors.get("stone_golem_2")

    both_dead = True
    for golem in [golem1, golem2]:
        if golem:
            sm = golem.properties.get("state_machine", {})
            if sm.get("current") != "destroyed":
                both_dead = False

    if both_dead:
        state.extra["golem_protection_lost"] = True
        return EventResult(
            allow=True,
            feedback=(
                "The last guardian crumbles. The temple is now unprotected - "
                "whatever these golems would have guarded against, you now face alone."
            ),
        )

    return EventResult(
        allow=True,
        feedback=(
            "The golem falls, its runes flickering out. Ancient protection, "
            "lost to violence."
        ),
    )


def _deactivate_golems(state: Any, new_state: str) -> None:
    """Deactivate both golems to the specified state."""
    for golem_id in ["stone_golem_1", "stone_golem_2"]:
        golem = state.actors.get(golem_id)
        if golem:
            sm = golem.properties.get("state_machine", {})
            if sm:
                transition_state(sm, new_state)


def on_damage(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle golem taking damage - transitions both golems to hostile.

    When a golem is attacked, both golems transition to "hostile" state
    due to their linked behavior. This makes combat engage both golems
    simultaneously.

    Args:
        entity: The golem that was damaged
        accessor: StateAccessor instance
        context: Context with damage and attacker_id

    Returns:
        EventResult with hostile transition message
    """
    state = accessor.game_state

    # Check if this is a golem
    golem_id = entity.id if hasattr(entity, "id") else None
    if not golem_id or "golem" not in golem_id.lower():
        return EventResult(allow=True, feedback=None)

    # Get the golem's state machine
    sm = entity.properties.get("state_machine")
    if not sm:
        return EventResult(allow=True, feedback=None)

    # If already hostile, no need to transition
    current_state = get_current_state(sm)
    if current_state == "hostile":
        return EventResult(allow=True, feedback=None)

    # Get game state from accessor
    state = accessor.game_state

    # Transition this golem to hostile
    transition_state(sm, "hostile")

    # Set AI disposition to hostile for combat system
    if "ai" not in entity.properties:
        entity.properties["ai"] = {}
    entity.properties["ai"]["disposition"] = "hostile"

    # Find and transition linked golem
    linked_id = entity.properties.get("linked_to")
    if linked_id:
        linked = state.get_actor(linked_id)
        linked_sm = linked.properties.get("state_machine")
        if linked_sm:
            linked_state = get_current_state(linked_sm)
            if linked_state != "hostile":
                transition_state(linked_sm, "hostile")
                # Set linked golem's AI disposition
                if "ai" not in linked.properties:
                    linked.properties["ai"] = {}
                linked.properties["ai"]["disposition"] = "hostile"

    # Set flag that combat has begun
    state.extra["golem_combat_initiated"] = True

    return EventResult(
        allow=True,
        feedback=(
            f"The {entity.name}'s runes flare bright crimson! "
            "Both guardians move forward with grinding purpose, ready to crush any threat."
        ),
    )
