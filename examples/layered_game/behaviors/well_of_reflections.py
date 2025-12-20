"""Well of Reflections puzzle behavior.

Demonstrates:
- Using offering_lib.offering_handler for "toss <item> into well" interactions
- Using offering_lib.alignment_tracker for moral choice tracking
- Entity behavior for receiving offerings
"""

from typing import Dict, Any, cast
from src.behavior_manager import EventResult
from src.types import ActorId

# Import library functions
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from behavior_libraries.offering_lib.alignment_tracker import (
    record_choice, get_alignment, get_alignment_descriptor
)


# Add "toss" as a synonym for "offer"
# The offering_handler already provides the "offer" verb
vocabulary = {
    "verbs": [
        {
            "word": "toss",
            "event": "on_receive_offering",
            "synonyms": ["throw"],
            "object_required": True,
            "preposition": "into"
        }
    ],
    "nouns": [],
    "adjectives": []
}


def on_receive_offering(entity: Any, accessor: Any, context: Dict) -> EventResult:
    """
    Entity behavior for well receiving an offering.

    Different items affect alignment differently:
    - Weapons: evil choice (destroying rather than preserving)
    - Flowers/plants: good choice (beauty and life)
    - Coins/treasure: neutral (neither good nor evil)
    - Food: good choice (sharing sustenance)

    Args:
        entity: The well
        accessor: StateAccessor instance
        context: Context dict with actor_id, verb, offered_item, offered_item_id

    Returns:
        EventResult with allow and message
    """
    actor_id = cast(ActorId, context.get("actor_id") or ActorId("player"))
    offered_item = context.get("offered_item")

    if not offered_item:
        return EventResult(
            allow=False,
            feedback="The well ripples expectantly, but nothing was offered."
        )

    # Determine the type of offering and its moral weight
    item_type = offered_item.properties.get("type", "object") if hasattr(offered_item, 'properties') else "object"
    item_name = offered_item.name if hasattr(offered_item, 'name') else "item"

    # Categorize the offering and record moral choice
    if item_type == "weapon":
        # Weapon = violence/destruction = evil
        record_choice(accessor, actor_id, "evil", weight=2.0)
        vision = "You see yourself standing over fallen enemies, weapon in hand. Their blood stains your hands."
        moral_response = "The well's waters darken ominously."

    elif item_type in ["plant", "flower"]:
        # Flowers = beauty/life = good
        record_choice(accessor, actor_id, "good", weight=2.0)
        vision = "You see yourself in a garden, surrounded by blooming flowers. You are smiling, at peace."
        moral_response = "The well's waters glow warmly."

    elif item_type == "food":
        # Food = sharing/sustenance = good
        record_choice(accessor, actor_id, "good", weight=1.5)
        vision = "You see yourself sharing a meal with strangers, all of you laughing together."
        moral_response = "The well's waters shimmer with golden light."

    elif item_type in ["treasure", "object"]:
        # Treasure/objects = material wealth = neutral (slightly greedy)
        record_choice(accessor, actor_id, "neutral", weight=0.5)
        vision = "You see yourself hoarding gold and jewels. You are alone, but wealthy."
        moral_response = "The well's waters ripple neutrally."

    else:
        # Unknown = neutral
        record_choice(accessor, actor_id, "neutral", weight=0.0)
        vision = f"You see a reflection of yourself tossing the {item_name} into the well."
        moral_response = "The well accepts your offering without judgment."

    # Get current alignment and descriptor
    alignment = get_alignment(accessor, actor_id)
    descriptor = get_alignment_descriptor(alignment)

    # Build the response message
    message = (
        f"You toss the {item_name} into the Well of Reflections.\n"
        f"{moral_response}\n\n"
        f"A vision appears in the water:\n"
        f"{vision}\n\n"
        f"Your alignment: {descriptor} ({alignment:.1f})"
    )

    return EventResult(allow=True, feedback=message)
