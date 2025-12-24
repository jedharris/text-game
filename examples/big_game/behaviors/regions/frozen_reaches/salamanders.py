"""Salamander Befriending for Frozen Reaches.

Implements trust-building through fire item gifts
and companion recruitment mechanics.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_utils import (
    modify_trust,
    transition_state,
)

# Vocabulary: wire hooks to events
# Note: Pack state mirroring is handled by infrastructure/pack_mirroring.py
# Note: Gift reactions are handled by infrastructure/gift_reactions.py
# Salamanders must have:
#   - pack_behavior.pack_follows_leader_state=true for pack mirroring
#   - gift_reactions configuration for fire gift mechanics
vocabulary: Dict[str, Any] = {
    "events": [],
    # Add adjectives for multi-word NPC and item names
    "adjectives": [
        {"word": "fire", "synonyms": []},
        {"word": "steam", "synonyms": []},
        {"word": "frost", "synonyms": []},
        {"word": "ice", "synonyms": []},
    ]
}

# Fire items salamanders accept
FIRE_ITEMS = [
    "torch",
    "fire_crystal",
    "warm_coal",
    "heated_stone",
    "fire",
    "flame",
]


def on_fire_gift(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle giving fire items to salamanders.

    Fire-aspected gifts increase gratitude and may
    transition salamanders to friendly/companion state.

    Args:
        entity: The item being given
        accessor: StateAccessor instance
        context: Context with target_actor

    Returns:
        EventResult with gift result
    """
    target = context.get("target_actor")
    if not target:
        return EventResult(allow=True, feedback=None)

    # Check if target is a salamander
    target_id = target.id if hasattr(target, "id") else str(target)
    if "salamander" not in target_id.lower():
        return EventResult(allow=True, feedback=None)

    # Check if item is fire-aspected
    item = context.get("item") or entity
    item_id = item.id if hasattr(item, "id") else str(item)
    item_lower = item_id.lower()

    is_fire_item = any(fire in item_lower for fire in FIRE_ITEMS)
    if not is_fire_item:
        return EventResult(
            allow=True,
            feedback=(
                "The salamander sniffs at the offering, then backs away, "
                "shaking its head. Its flame dims with disappointment."
            ),
        )

    state = accessor.game_state

    # Find lead salamander (all trust changes apply to lead)
    lead = state.actors.get("salamander")
    if not lead:
        lead = target  # Use target if lead not found

    # Increase trust/gratitude
    trust_state = lead.properties.get("trust_state", {"current": 0})
    old_trust = trust_state.get("current", 0)
    new_trust = modify_trust(
        current=old_trust,
        delta=1,
        floor=0,
        ceiling=5,
    )
    trust_state["current"] = new_trust
    lead.properties["trust_state"] = trust_state

    # Check for state transitions
    sm = lead.properties.get("state_machine", {})
    current_state = sm.get("current", sm.get("initial", "neutral"))

    if current_state == "neutral" and new_trust >= 1:
        transition_state(sm, "friendly")
        _mirror_salamander_state(state, "friendly")

        return EventResult(
            allow=True,
            feedback=(
                "The salamander's flame brightens with delight as it accepts the "
                f"{item_id}. It approaches cautiously, curling near you with a "
                "contented crackle. The other salamanders watch with interest."
            ),
        )

    if current_state == "friendly" and new_trust >= 3:
        # Ready for companion - but needs invitation
        return EventResult(
            allow=True,
            feedback=(
                "The lead salamander's flame burns bright and steady. It nuzzles "
                f"against you after accepting the {item_id}, clearly comfortable "
                "in your presence. It seems willing to follow if you ask."
            ),
        )

    return EventResult(
        allow=True,
        feedback=(
            f"The salamander accepts the {item_id}, its flame flickering with "
            "gratitude. A pleasant crackle sounds as it moves closer."
        ),
    )


def on_salamander_talk(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle talk/ask commands for salamanders.

    Salamanders communicate through gestures, flame behavior,
    postures, and sounds - not words.

    Args:
        entity: The salamander being talked to
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with gesture-based communication
    """
    state = accessor.game_state

    # Get salamander
    salamander_id = entity.id if hasattr(entity, "id") else None
    if not salamander_id or "salamander" not in salamander_id.lower():
        return EventResult(allow=True, feedback=None)

    salamander = state.actors.get(salamander_id)
    if not salamander:
        return EventResult(allow=True, feedback=None)

    # Get current state
    sm = salamander.properties.get("state_machine", {})
    current_state = sm.get("current", sm.get("initial", "neutral"))

    # Gesture responses based on state
    gestures = {
        "neutral": (
            "The salamander watches you carefully, flame flickering with uncertainty. "
            "It tilts its head, curious but cautious. When you gesture toward the fire, "
            "it points with a tendril of flame, then looks back at you expectantly."
        ),
        "friendly": (
            "The salamander's flame brightens in greeting, crackling pleasantly. "
            "It approaches and curls near your feet, radiating comfortable warmth. "
            "When you speak, it makes a soft rumbling sound, like contentment."
        ),
        "companion": (
            "The salamander nuzzles against you affectionately, its flame dancing "
            "with joy. It points toward warm places, guides you away from the cold, "
            "and crackles happily when you acknowledge its gestures. You are bonded."
        ),
        "wild": (
            "The salamander hisses sharply, spines raised in warning. Its flame "
            "burns erratically, and it backs away, shaking its head vigorously. "
            "It clearly does not trust you."
        ),
        "curious": (
            "The salamander edges closer, flame dancing with interest. It points "
            "at various objects, clearly trying to communicate. When you point at "
            "fire, it brightens. When you point at cold things, it dims and backs away."
        ),
        "bonded": (
            "The salamander stays protectively close, its warmth a constant comfort. "
            "It responds to your words with gestures - pointing at dangers, guiding you "
            "to warmth, crackling with pleasure when you're safe. You understand each other perfectly."
        ),
    }

    feedback = gestures.get(current_state, gestures["neutral"])
    return EventResult(allow=True, feedback=feedback)


def on_salamander_state_change(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Mirror lead salamander state to followers.

    Salamanders 2 and 3 follow the lead's disposition.

    Args:
        entity: The lead salamander
        accessor: StateAccessor instance
        context: Context with new_state

    Returns:
        EventResult allowing the change
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "salamander":
        return EventResult(allow=True, feedback=None)

    new_state = context.get("new_state")
    if not new_state:
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    _mirror_salamander_state(state, new_state)

    return EventResult(allow=True, feedback=None)


def _mirror_salamander_state(state: Any, new_state: str) -> None:
    """Update follower salamander states to match lead.

    Salamanders 2 and 3 follow the lead's state changes.
    """
    follower_ids = ["steam_salamander_2", "steam_salamander_3"]

    for follower_id in follower_ids:
        follower = state.actors.get(follower_id)
        if follower:
            sm = follower.properties.get("state_machine", {})
            if sm:
                transition_state(sm, new_state)
