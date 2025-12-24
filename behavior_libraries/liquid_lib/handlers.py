"""Liquid interaction behaviors - fill, pour, water.

Vocabulary and handlers for liquid-based interactions.
"""

from typing import Any, Dict, Optional

from src.state_accessor import HandlerResult, StateAccessor
from src.types import ActorId
from src.word_entry import WordEntry
from utilities.utils import find_item_in_inventory, find_accessible_item, name_matches
from utilities.handler_utils import get_display_name, validate_actor_and_location


# Vocabulary extension - adds fill, pour, and water verbs
vocabulary: Dict[str, Any] = {
    "verbs": [
        {
            "word": "fill",
            "event": "on_fill",
            "synonyms": [],
            "object_required": True,
            "llm_context": {
                "traits": ["fills container with liquid", "requires water source"],
                "failure_narration": {
                    "not_container": "cannot fill that",
                    "no_water": "no water source here",
                    "not_holding": "not carrying that"
                }
            }
        },
        {
            "word": "pour",
            "event": "on_pour",
            "synonyms": ["empty"],
            "object_required": True,
            "llm_context": {
                "traits": ["pours liquid from container", "transfers liquid to target"],
                "failure_narration": {
                    "not_container": "cannot pour that",
                    "empty": "container is empty",
                    "not_holding": "not carrying that"
                }
            }
        },
        {
            "word": "water",
            "word_type": ["verb", "noun"],
            "event": "on_water",
            "synonyms": [],
            "object_required": True,
            "llm_context": {
                "traits": ["applies water to target", "uses water from container"],
                "failure_narration": {
                    "no_water": "nothing to water with",
                    "no_target": "nothing to water"
                }
            }
        }
    ],
    "nouns": [],
    "adjectives": []
}


# Locations with water sources (can be extended by game content)
# Format: location_id -> description of water source
WATER_SOURCES = {
    "luminous_grotto": "the crystal-clear pool",
    "hot_springs": "the heated pools",
}


def _find_water_container(accessor: StateAccessor, actor_id: ActorId) -> Optional[Any]:
    """Find a container with water in the actor's inventory.

    Args:
        accessor: StateAccessor instance
        actor_id: ID of actor to search inventory

    Returns:
        Item with water_capacity property, or None if not found
    """
    actor = accessor.get_actor(actor_id)
    if not actor:
        return None

    for item_id in actor.inventory:
        item = accessor.get_item(item_id)
        if item and item.properties.get("water_capacity"):
            return item

    return None


def handle_fill(accessor: StateAccessor, action: Dict[str, Any]) -> HandlerResult:
    """Handle fill command - fill a container with water.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of container to fill (required)

    Returns:
        HandlerResult with success flag and message
    """
    # Validate actor and location
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error
    assert actor_id is not None and actor is not None and location is not None
    object_name = action.get("object")
    if not isinstance(object_name, WordEntry):
        return HandlerResult(success=False, primary="I didn't understand what to fill.")

    # Check if there's a water source in this location
    water_source = WATER_SOURCES.get(location.id)
    if not water_source:
        return HandlerResult(
            success=False,
            primary="There's no water source here to fill from."
        )

    # Find the container in inventory
    container = find_item_in_inventory(accessor, object_name, actor_id)
    if not container:
        # Check if it's in the location but not held
        local_item = find_accessible_item(accessor, object_name, actor_id)
        if local_item:
            return HandlerResult(
                success=False,
                primary=f"You need to be holding the {get_display_name(object_name)} to fill it."
            )
        return HandlerResult(
            success=False,
            primary=f"You're not carrying any {get_display_name(object_name)}."
        )

    # Check if it can hold water
    water_capacity = container.properties.get("water_capacity", 0)
    if not water_capacity:
        return HandlerResult(
            success=False,
            primary=f"The {container.name} can't hold water."
        )

    # Fill it
    state = accessor.game_state
    current_charges = state.extra.get("bucket_water_charges", 0)

    if current_charges >= water_capacity:
        return HandlerResult(
            success=True,
            primary=f"The {container.name} is already full of water."
        )

    state.extra["bucket_water_charges"] = water_capacity

    return HandlerResult(
        success=True,
        primary=f"You dip the {container.name} into {water_source} and fill it with water."
    )


def handle_pour(accessor: StateAccessor, action: Dict[str, Any]) -> HandlerResult:
    """Handle pour command - pour water from container onto target.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of container to pour from (required)
            - indirect_object: Name of target to pour onto (optional)

    Returns:
        HandlerResult with success flag and message
    """
    # Validate actor and location
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error
    assert actor_id is not None and actor is not None and location is not None
    object_name = action.get("object")
    if not isinstance(object_name, WordEntry):
        return HandlerResult(success=False, primary="I didn't understand what to pour.")

    target_name = action.get("indirect_object")

    # Handle "pour water" - find a water container in inventory
    if object_name.word.lower() == "water":
        container = _find_water_container(accessor, actor_id)
        if not container:
            return HandlerResult(
                success=False,
                primary="You don't have anything containing water."
            )
    else:
        # Find the named container in inventory
        container = find_item_in_inventory(accessor, object_name, actor_id)
        if not container:
            return HandlerResult(
                success=False,
                primary=f"You're not carrying any {get_display_name(object_name)}."
            )

    # Check if it has water
    state = accessor.game_state
    water_charges = state.extra.get("bucket_water_charges", 0)
    if water_charges <= 0:
        return HandlerResult(
            success=False,
            primary=f"The {container.name} is empty."
        )

    # If no target, just pour on ground
    if not target_name:
        state.extra["bucket_water_charges"] = water_charges - 1
        return HandlerResult(
            success=True,
            primary=f"You pour water from the {container.name} onto the ground."
        )

    # Find the target
    if not isinstance(target_name, WordEntry):
        return HandlerResult(
            success=False,
            primary="I didn't understand what to pour onto."
        )

    target = find_accessible_item(
        accessor, target_name, actor_id, action.get("indirect_adjective")
    )
    if not target:
        return HandlerResult(
            success=False,
            primary=f"You don't see any {get_display_name(target_name)} here."
        )

    # Check if target has item_use_reactions for water
    item_reactions = target.properties.get("item_use_reactions", {})
    handler_path = item_reactions.get("handler")

    if handler_path:
        # Load and call the handler via behavior_manager
        handler = accessor.behavior_manager.load_behavior(handler_path)
        if handler:
            context = {"target": target}
            result = handler(container, accessor, context)
            if result and result.feedback:
                # Handler consumed the water
                return HandlerResult(
                    success=result.allow,
                    primary=result.feedback
                )

    # Default behavior - just pour on the target
    state.extra["bucket_water_charges"] = water_charges - 1
    return HandlerResult(
        success=True,
        primary=f"You pour water from the {container.name} onto the {target.name}."
    )


def handle_water(accessor: StateAccessor, action: Dict[str, Any]) -> HandlerResult:
    """Handle water command - water a target with available water source.

    This is a convenience command that automatically uses a water container
    from inventory to water the target.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of target to water (required)

    Returns:
        HandlerResult with success flag and message
    """
    # Validate actor and location
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error
    assert actor_id is not None and actor is not None and location is not None
    target_name = action.get("object")
    if not isinstance(target_name, WordEntry):
        return HandlerResult(success=False, primary="I didn't understand what to water.")

    # Find a water container in inventory
    state = accessor.game_state
    water_charges = state.extra.get("bucket_water_charges", 0)

    # Look for bucket in inventory
    bucket = None
    for item_id in actor.inventory:
        item = accessor.get_item(item_id)
        if item and item.properties.get("water_capacity"):
            bucket = item
            break

    if not bucket:
        return HandlerResult(
            success=False,
            primary="You don't have anything to water with."
        )

    if water_charges <= 0:
        return HandlerResult(
            success=False,
            primary=f"The {bucket.name} is empty. Fill it from a water source first."
        )

    # Find the target
    target = find_accessible_item(
        accessor, target_name, actor_id, action.get("adjective")
    )
    if not target:
        return HandlerResult(
            success=False,
            primary=f"You don't see any {get_display_name(target_name)} here."
        )

    # Check if target has item_use_reactions for water
    item_reactions = target.properties.get("item_use_reactions", {})
    handler_path = item_reactions.get("handler")

    if handler_path:
        # Load and call the handler via behavior_manager
        handler = accessor.behavior_manager.load_behavior(handler_path)
        if handler:
            context = {"target": target}
            result = handler(bucket, accessor, context)
            if result and result.feedback:
                return HandlerResult(
                    success=result.allow,
                    primary=result.feedback
                )

    # Default behavior - just water the target
    state.extra["bucket_water_charges"] = water_charges - 1
    return HandlerResult(
        success=True,
        primary=f"You water the {target.name} with water from the {bucket.name}."
    )
