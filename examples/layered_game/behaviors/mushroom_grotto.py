"""Mushroom Grotto puzzle behavior.

Demonstrates:
- Custom verb (water) for puzzle interaction
- Using puzzle_lib.state_revealer for progressive light level and hidden item revelation
- Location state management
"""

from typing import Dict, Any
from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from src.word_entry import WordEntry, WordType
from utilities.utils import find_item_in_inventory, find_accessible_item

# Import library functions
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from behavior_libraries.puzzle_lib.state_revealer import reveal_item, check_state_threshold


# Vocabulary extension - adds "water" verb
vocabulary = {
    "verbs": [
        {
            "word": "water",
            "event": "on_water",
            "synonyms": ["pour"],
            "object_required": True
        }
    ],
    "nouns": [],
    "adjectives": []
}


def handle_water(accessor, action: Dict) -> HandlerResult:
    """
    Handle the water command.

    Args:
        accessor: StateAccessor instance
        action: Action dict with verb, object, actor_id

    Returns:
        HandlerResult with success flag and message
    """
    actor_id = action.get("actor_id", "player")
    obj_name = action.get("object")
    adjective = action.get("adjective")

    if not obj_name:
        return HandlerResult(success=False, message="Water what?")

    # Find the target (mushroom)
    target = find_accessible_item(accessor, obj_name, actor_id, adjective)

    if not target:
        return HandlerResult(success=False, message=f"You don't see any {obj_name} here.")

    # Check if player has the bucket
    bucket_word = WordEntry(word="bucket", synonyms=[], word_type=WordType.NOUN)
    bucket = find_item_in_inventory(accessor, bucket_word, actor_id)
    if not bucket:
        return HandlerResult(
            success=False,
            message="You need a bucket of water to water things."
        )

    # Invoke entity behavior
    result = accessor.update(target, {}, verb="water", actor_id=actor_id)

    if not result.success:
        return HandlerResult(success=False, message=result.message)

    # Build response message
    if result.message:
        message = result.message
    else:
        message = f"You water the {target.name}."

    return HandlerResult(success=True, message=message)


def on_water(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Entity behavior for mushroom being watered.

    Each mushroom that gets watered increases the grotto's light level.
    When light level reaches 3, the ceiling sigil is revealed.

    Args:
        entity: The mushroom being watered
        accessor: StateAccessor instance
        context: Context dict with actor_id, verb

    Returns:
        EventResult with allow and message
    """
    # Initialize entity states if needed
    if not hasattr(entity, 'states') or entity.states is None:
        entity.states = {}

    # Check if already watered
    if entity.states.get("watered", False):
        return EventResult(
            allow=True,
            message=f"The {entity.properties.get('color', '')} mushroom is already glowing brightly."
        )

    # Mark as watered
    entity.states["watered"] = True

    # Get the grotto location
    location = accessor.get_location("loc_mushroom_grotto")
    if not hasattr(location, 'states') or location.states is None:
        location.states = {}

    # Increase light level
    current_light = location.states.get("light_level", 0)
    new_light = current_light + 1
    location.states["light_level"] = new_light

    # Get mushroom color for message
    color = entity.properties.get("color", "")

    # Build message based on light level
    if new_light == 1:
        message = (
            f"You pour water on the {color} mushroom.\n"
            f"It begins to glow softly! The grotto is slightly brighter now."
        )
    elif new_light == 2:
        message = (
            f"You water the {color} mushroom.\n"
            f"It bursts into luminescence! The grotto grows much brighter."
        )
    elif new_light >= 3:
        # Reveal the ceiling sigil
        revealed = reveal_item(accessor, "item_ceiling_sigil")

        message = (
            f"You water the {color} mushroom.\n"
            f"It shines brilliantly! The grotto is now fully illuminated.\n"
            f"In the bright light, you can now read symbols carved into the ceiling!"
        )
    else:
        message = f"The {color} mushroom glows brighter."

    return EventResult(allow=True, message=message)
