"""Ice Extraction for Frozen Reaches.

Handles extracting items frozen in ice using heat sources or risky chipping.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.state_accessor import IGNORE_EVENT
from utilities.utils import find_accessible_item

# Vocabulary: wire on_take event to frozen items
vocabulary: Dict[str, Any] = {
    "events": [
        {
            "event": "on_take",
            "handler": "on_take",
            "description": "Handle taking frozen items from ice"
        },
        {
            "event": "on_use",
            "handler": "on_use",
            "description": "Handle using heat sources on frozen items"
        },
        {
            "event": "on_observe",
            "handler": "on_observe",
            "description": "Handle observe event (uses standard description)"
        }
    ],
    # Add extraction verbs
    "adjectives": [
        {"word": "frozen", "synonyms": ["iced", "frosted"]},
    ],
    "verbs": [
        {"word": "chip", "synonyms": ["chisel"], "object_required": True},
        {"word": "melt", "synonyms": ["thaw", "heat"], "object_required": True},
        {"word": "extract", "synonyms": [], "object_required": True},
    ]
}

# Heat source item IDs that can safely melt ice
HEAT_SOURCES = [
    "torch",
    "fire_wand",
    "salamander_heated_stone",
    "lit_torch",  # In case torch becomes lit_torch when lit
]

# Fire-aspected items that provide heat
FIRE_ASPECTS = [
    "fire",
    "flame",
    "ember",
    "heated",
    "torch",
]


def on_take(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle taking items frozen in ice.

    Items with frozen_in_ice=true require heat to extract safely.
    Fragile items break if extracted without heat.
    Non-fragile items can be chipped free with multiple attempts.

    Args:
        entity: The item being taken
        accessor: StateAccessor instance
        context: Context with actor_id and verb

    Returns:
        EventResult allowing or blocking the take action
    """
    # Check if this item is frozen in ice
    if not entity.properties.get("frozen_in_ice", False):
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    actor_id = context.get("actor_id", "player")
    actor = state.actors.get(actor_id)

    if not actor:
        return EventResult(allow=True, feedback=None)

    # Check if player has a heat source
    has_heat_source = _check_for_heat_source(actor, state)

    # Check if item is fragile
    is_fragile = entity.properties.get("fragile", False)

    # Check if item requires heat
    requires_heat = entity.properties.get("requires_heat_to_extract", False)

    # If player has heat source, allow safe extraction
    if has_heat_source:
        # Clear the frozen flag so normal take proceeds
        entity.properties["frozen_in_ice"] = False

        return EventResult(
            allow=True,
            feedback=(
                f"You carefully apply heat to the ice surrounding the {entity.name}. "
                f"The ice melts away, revealing the {entity.name} intact."
            )
        )

    # No heat source - check if risky extraction is possible
    if is_fragile:
        # Fragile items break if you try to chip them out
        return EventResult(
            allow=False,
            feedback=(
                f"The {entity.name} is frozen solid in the ice. You'll need a heat source "
                f"to melt it free - trying to chip it out would shatter it."
            )
        )

    if requires_heat:
        # Non-fragile but requires heat - allow multiple attempts
        attempt_count = entity.properties.get("extraction_attempts", 0)
        entity.properties["extraction_attempts"] = attempt_count + 1

        if attempt_count == 0:
            return EventResult(
                allow=False,
                feedback=(
                    f"The {entity.name} is frozen solid in the ice. You try to pull it free "
                    f"but make no progress. Perhaps with more effort, or a heat source..."
                )
            )
        elif attempt_count == 1:
            return EventResult(
                allow=False,
                feedback=(
                    f"You chip away at the ice around the {entity.name}. It's slow going. "
                    f"One more attempt might do it, or you could find a heat source to melt it safely."
                )
            )
        else:
            # Third attempt succeeds
            entity.properties["frozen_in_ice"] = False
            entity.properties.pop("extraction_attempts", None)

            return EventResult(
                allow=True,
                feedback=(
                    f"With determined effort, you finally chip the {entity.name} free from the ice. "
                    f"It's undamaged, but that took real work."
                )
            )

    # Default: not frozen or doesn't require special handling
    return EventResult(allow=True, feedback=None)


def on_use(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle using heat sources on frozen items.

    Allows "use torch on crystal_lens" style commands.

    Args:
        entity: The heat source item
        accessor: StateAccessor instance
        context: Context with target

    Returns:
        EventResult with extraction result
    """
    # Check if this is a heat source
    item_id = entity.id if hasattr(entity, "id") else str(entity)
    item_lower = item_id.lower()

    is_heat = (
        item_id in HEAT_SOURCES or
        any(aspect in item_lower for aspect in FIRE_ASPECTS)
    )

    if not is_heat:
        return EventResult(allow=True, feedback=None)

    # Check if target is a frozen item
    target = context.get("target")
    if not target:
        return EventResult(allow=True, feedback=None)

    # Check if target is frozen
    if not target.properties.get("frozen_in_ice", False):
        return EventResult(allow=True, feedback=None)

    # Melt the ice
    target.properties["frozen_in_ice"] = False
    target.properties.pop("extraction_attempts", None)  # Reset attempts

    return EventResult(
        allow=True,
        feedback=(
            f"You apply the {entity.name}'s heat to the ice surrounding the {target.name}. "
            f"The ice melts away carefully, leaving the {target.name} free to take."
        )
    )


def _check_for_heat_source(actor: Any, state: Any) -> bool:
    """Check if actor has a heat source in inventory.

    Args:
        actor: Actor to check
        state: Game state

    Returns:
        True if actor has a heat source
    """
    # Check for specific heat source items in inventory
    inventory = actor.inventory
    for item_id in inventory:
        if item_id in HEAT_SOURCES:
            return True

        # Check if item name contains fire aspects
        item = next((i for i in state.items if i.id == item_id), None)
        if item:
            item_lower = item.id.lower()
            if any(aspect in item_lower for aspect in FIRE_ASPECTS):
                return True

    # Check if player has salamander companion (provides heat aura)
    companions = state.extra.get("companions", [])
    for companion_id in companions:
        if "salamander" in companion_id.lower():
            return True

    return False


def on_observe(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle observe event for ice extraction items.

    Uses standard description.

    Args:
        entity: The item
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        IGNORE_EVENT to use standard description
    """
    return IGNORE_EVENT
