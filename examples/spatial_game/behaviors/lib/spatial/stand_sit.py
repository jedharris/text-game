"""Stand on and sit on commands for surface positioning.

Tier 2 library behavior - reusable across games.
"""

from typing import Dict, Any

from src.state_accessor import HandlerResult
from utilities.utils import find_accessible_item


# Vocabulary extension
vocabulary = {
    "verbs": [
        {
            "word": "stand",
            "event": "on_stand",
            "synonyms": ["get on"],
            "indirect_object_required": True,
            "llm_context": {
                "traits": ["positioning", "surface interaction"],
                "usage": ["stand on <surface>", "get on <surface>"]
            }
        },
        {
            "word": "sit",
            "event": "on_sit",
            "synonyms": [],
            "indirect_object_required": True,
            "llm_context": {
                "traits": ["positioning", "surface interaction"],
                "usage": ["sit on <surface>"]
            }
        }
    ],
    "nouns": [],
    "adjectives": [],
    "directions": []
}


def handle_stand(accessor, action: Dict[str, Any]) -> HandlerResult:
    """Handle 'stand on <surface>' command."""
    return _handle_surface_action(accessor, action, "stand on", "on_surface")


def handle_sit(accessor, action: Dict[str, Any]) -> HandlerResult:
    """Handle 'sit on <surface>' command."""
    return _handle_surface_action(accessor, action, "sit on", "on_surface")


def _handle_surface_action(accessor, action: Dict[str, Any], action_verb: str,
                           posture: str) -> HandlerResult:
    """Common logic for stand/sit on surface."""
    actor_id = action.get("actor_id", "player")
    # Parser may put surface in object or indirect_object depending on pattern
    surface_name = action.get("indirect_object") or action.get("object")
    adjective = action.get("indirect_adjective") or action.get("adjective")

    if not surface_name:
        return HandlerResult(success=False, message=f"What do you want to {action_verb}?")

    # Get actor
    actor = accessor.get_actor(actor_id)
    if not actor:
        return HandlerResult(
            success=False,
            message=f"INCONSISTENT STATE: Actor {actor_id} not found"
        )

    # Find surface
    surface = find_accessible_item(accessor, surface_name, actor_id, adjective)
    if not surface:
        return HandlerResult(
            success=False,
            message=f"You don't see any {surface_name} here."
        )

    # Check if it's a surface
    properties = surface.properties if hasattr(surface, 'properties') else {}
    container_props = properties.get("container", {})
    if not container_props.get("is_surface", False):
        return HandlerResult(
            success=False,
            message=f"You can't {action_verb} the {surface.name}."
        )

    # Set posture and focus
    actor.properties["focused_on"] = surface.id
    actor.properties["posture"] = posture

    message = f"You {action_verb} the {surface.name}."

    return HandlerResult(success=True, message=message)
