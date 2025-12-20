"""Dialog Reaction Infrastructure.

Provides generic handling for entity-specific reactions to dialog keywords.

Supports two modes:
1. Data-driven: Entity properties define triggers, responses, state changes
2. Handler escape hatch: Entity properties specify a Python function to call

Example data-driven config:
    "dialog_reactions": {
        "help_request": {
            "triggers": ["help", "save", "please"],
            "requires_state": "critical",
            "response": "Please help me...",
            "set_flags": {"asked_for_help": true},
            "create_commitment": "commit_help_npc"
        }
    }

Example handler escape hatch:
    "dialog_reactions": {
        "handler": "behaviors.regions.fungal_depths.aldric_rescue:on_aldric_commitment"
    }
"""

from typing import Any

from examples.big_game.behaviors.infrastructure.dispatcher_utils import load_handler
from src.behavior_manager import EventResult
from src.infrastructure_utils import (
    create_commitment,
    get_current_turn,
    modify_trust,
    transition_state,
)

# Vocabulary: wire hooks to events
vocabulary = {
    "events": [
        {
            "event": "on_dialog_received",
            "hook": "on_dialog_keyword",
            "description": "Handle entity reactions to dialog keywords",
        },
    ]
}


def on_dialog_received(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle entity-specific reactions to dialog keywords.

    Checks the entity for dialog_reactions configuration.
    If config has "handler" key, calls that Python function.
    Otherwise, processes the data-driven config.

    Args:
        entity: The entity being spoken to
        accessor: StateAccessor instance
        context: Context with keyword, dialog_text

    Returns:
        EventResult with dialog reaction
    """
    if not hasattr(entity, "properties"):
        return EventResult(allow=True, feedback=None)

    # Check for dialog_reactions configuration
    dialog_config = entity.properties.get("dialog_reactions", {})
    if not dialog_config:
        return EventResult(allow=True, feedback=None)

    # Check for handler escape hatch first
    handler_path = dialog_config.get("handler")
    if handler_path:
        handler = load_handler(handler_path)
        if handler:
            return handler(entity, accessor, context)
        # Handler failed to load - fall through to data-driven

    # Data-driven processing
    # Get the keyword/dialog text
    keyword = context.get("keyword", "").lower()
    dialog_text = context.get("dialog_text", "").lower()
    full_text = f"{keyword} {dialog_text}"

    state = accessor.state

    # Check each reaction pattern
    for reaction_name, reaction_config in dialog_config.items():
        if reaction_name in ("handler", "_metadata"):
            continue  # Skip special keys

        if not isinstance(reaction_config, dict):
            continue

        triggers = reaction_config.get("triggers", [])
        if not triggers:
            continue

        # Check if any trigger matches
        triggered = any(trigger.lower() in full_text for trigger in triggers)
        if not triggered:
            continue

        # Check conditions
        if not _check_conditions(reaction_config, state, entity):
            continue

        # Process the reaction
        return _process_dialog_reaction(
            entity=entity,
            reaction_name=reaction_name,
            reaction_config=reaction_config,
            accessor=accessor,
            context=context,
        )

    return EventResult(allow=True, feedback=None)


def _check_conditions(
    reaction_config: dict[str, Any],
    state: Any,
    entity: Any,
) -> bool:
    """Check if reaction conditions are met."""
    # Check required flags
    required_flags = reaction_config.get("requires_flags", {})
    for flag, value in required_flags.items():
        if state.extra.get(flag) != value:
            return False

    # Check forbidden flags
    forbidden_flags = reaction_config.get("forbidden_flags", [])
    for flag in forbidden_flags:
        if state.extra.get(flag):
            return False

    # Check entity state
    required_state = reaction_config.get("requires_state")
    if required_state:
        sm = entity.properties.get("state_machine", {})
        current = sm.get("current", sm.get("initial"))
        if current != required_state:
            return False

    return True


def _process_dialog_reaction(
    entity: Any,
    reaction_name: str,
    reaction_config: dict[str, Any],
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Process a matched dialog reaction."""
    state = accessor.state
    entity_id = entity.id if hasattr(entity, "id") else str(entity)

    # Set flags
    flags = reaction_config.get("set_flags", {})
    for flag_name, flag_value in flags.items():
        state.extra[flag_name] = flag_value

    # Apply trust changes
    trust_delta = reaction_config.get("trust_delta", 0)
    if trust_delta:
        trust_state = entity.properties.get("trust_state", {"current": 0})
        new_trust = modify_trust(
            current=trust_state.get("current", 0),
            delta=trust_delta,
            floor=trust_state.get("floor", -5),
            ceiling=trust_state.get("ceiling", 5),
        )
        trust_state["current"] = new_trust
        entity.properties["trust_state"] = trust_state

    # State transitions
    new_state = reaction_config.get("transition_to")
    if new_state:
        sm = entity.properties.get("state_machine")
        if sm:
            transition_state(sm, new_state)

    # Create commitment if configured
    commitment_id = reaction_config.get("create_commitment")
    if commitment_id:
        current_turn = get_current_turn(state)
        create_commitment(
            state=state,
            config_id=commitment_id,
            current_turn=current_turn,
        )

    # Get response message
    message = reaction_config.get("response", "")

    return EventResult(allow=True, feedback=message if message else None)
