"""Death Reaction Infrastructure.

Provides generic handling for entity-specific reactions when entities die.

Supports two modes:
1. Data-driven: Entity properties define death consequences, gossip, trust changes
2. Handler escape hatch: Entity properties specify a Python function to call

Example data-driven config:
    "death_reactions": {
        "set_flags": {"wolf_alpha_dead": true},
        "create_gossip": {
            "id": "gossip_wolf_death",
            "content": "The alpha wolf has fallen...",
            "targets": ["npc_guard", "npc_merchant"]
        },
        "trust_changes": {"npc_pack_beta": -2},
        "trigger_state_changes": {"npc_pack_beta": "hostile"}
    }

Example handler escape hatch:
    "death_reactions": {
        "handler": "behaviors.regions.beast_wilds.wolf_pack:on_alpha_death"
    }
"""

from typing import Any

from examples.big_game.behaviors.infrastructure.dispatcher_utils import load_handler
from src.behavior_manager import EventResult
from src.infrastructure_types import GossipId
from src.infrastructure_utils import (
    create_gossip,
    modify_trust,
    transition_state,
)

# Vocabulary: wire hooks to events
vocabulary = {
    "events": [
        {
            "event": "on_entity_death",
            "hook": "on_actor_death",
            "description": "Handle entity death consequences",
        },
    ]
}


def on_entity_death(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle entity-specific death consequences.

    Checks the entity for death_reactions configuration.
    If config has "handler" key, calls that Python function.
    Otherwise, processes the data-driven config.

    Args:
        entity: The entity that died
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with death consequence
    """
    if not hasattr(entity, "properties"):
        return EventResult(allow=True, feedback=None)

    # Check for death_reactions configuration
    death_config = entity.properties.get("death_reactions", {})
    if not death_config:
        return EventResult(allow=True, feedback=None)

    # Check for handler escape hatch first
    handler_path = death_config.get("handler")
    if handler_path:
        handler = load_handler(handler_path)
        if handler:
            return handler(entity, accessor, context)
        # Handler failed to load - fall through to data-driven

    # Data-driven processing
    state = accessor.state
    entity_id = entity.id if hasattr(entity, "id") else str(entity)

    # Set flags
    flags = death_config.get("set_flags", {})
    for flag_name, flag_value in flags.items():
        state.extra[flag_name] = flag_value

    # Create gossip if configured
    gossip_config = death_config.get("create_gossip")
    if gossip_config:
        gossip_id = gossip_config.get("id", f"gossip_{entity_id}_death")
        create_gossip(
            state=state,
            content=gossip_config.get("content", f"{entity_id} has died"),
            source_npc=gossip_config.get("source", "witnesses"),
            target_npcs=gossip_config.get("targets", []),
            delay_turns=gossip_config.get("delay", 10),
            gossip_id=GossipId(gossip_id),
        )

    # Apply trust changes to other entities
    trust_changes = death_config.get("trust_changes", {})
    for target_id, delta in trust_changes.items():
        target = state.actors.get(target_id)
        if target:
            trust_state = target.properties.get("trust_state", {"current": 0})
            new_trust = modify_trust(
                current=trust_state.get("current", 0),
                delta=delta,
                floor=trust_state.get("floor", -5),
                ceiling=trust_state.get("ceiling", 5),
            )
            trust_state["current"] = new_trust
            target.properties["trust_state"] = trust_state

    # Trigger state changes on other entities
    state_changes = death_config.get("trigger_state_changes", {})
    for target_id, new_state in state_changes.items():
        target = state.actors.get(target_id)
        if target:
            sm = target.properties.get("state_machine")
            if sm:
                transition_state(sm, new_state)

    # Get death message
    message = death_config.get("message", "")

    return EventResult(allow=True, feedback=message if message else None)
