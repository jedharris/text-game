"""Unified reaction interpreter.

Processes all reaction types through a single 3-phase execution model:
1. Evaluate conditions - all must pass
2. Apply effects - in deterministic order
3. Generate feedback - with template substitution
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from .reaction_conditions import CONDITION_ORDER, CONDITION_REGISTRY
from .reaction_effects import EFFECT_ORDER, EFFECT_REGISTRY
from .message_templates import get_message, substitute_templates


def process_reaction(
    entity: Any,
    config: Dict[str, Any],
    accessor: Any,
    context: Dict[str, Any],
    spec: Any
) -> EventResult:
    """Universal reaction interpreter.

    Args:
        entity: Target entity (NPC, item, location)
        config: Single reaction configuration dict
        accessor: StateAccessor instance
        context: Event context dict
        spec: ReactionSpec for this reaction type

    Returns:
        EventResult with feedback or failure

    Execution flow:
        1. Enrich context with reaction-specific values
        2. Evaluate all conditions - any failure stops execution
        3. Apply all effects - in deterministic order
        4. Generate feedback message with template substitution
    """
    state = accessor.game_state

    # PHASE 0: Enrich context
    context = spec.context_enrichment(context, config)

    # PHASE 1: Evaluate all conditions
    for condition_key in CONDITION_ORDER:
        if condition_key not in config:
            continue

        checker = CONDITION_REGISTRY.get(condition_key)
        if not checker:
            continue

        if not checker(config, state, entity, context):
            # Condition failed - return failure message
            failure_msg = config.get("failure_message", "")
            return EventResult(
                allow=True,
                feedback=substitute_templates(failure_msg, context) if failure_msg else None
            )

    # PHASE 2: Apply all effects (in deterministic order)
    for effect_key in EFFECT_ORDER:
        if effect_key not in config:
            continue

        handler = EFFECT_REGISTRY.get(effect_key)
        if handler:
            handler(config, state, entity, context)

    # PHASE 3: Generate feedback
    message = get_message(config, spec)
    if message:
        message = substitute_templates(message, context)

    return EventResult(allow=True, feedback=message)
