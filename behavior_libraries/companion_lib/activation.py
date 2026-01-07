"""Companion activation utilities.

Provides reusable patterns for activating companion status based on
trust levels, state machine transitions, or other triggers.

Works with companion_lib.following for standardized companion mechanics.
"""

from typing import Any, Callable, Optional

from src.behavior_manager import EventResult
from behavior_libraries.companion_lib.following import make_companion


def activate_companion_on_trust_threshold(
    actor: Any,
    accessor: Any,
    trust_threshold: int = 3,
    companion_message: Optional[str] = None,
) -> EventResult | None:
    """Activate companion status when actor's trust reaches threshold.

    Checks actor's trust_state.current and activates companion if >= threshold.
    Uses companion_lib.make_companion() for standardization.

    Args:
        actor: The actor to potentially activate as companion
        accessor: StateAccessor instance
        trust_threshold: Minimum trust level to activate (default 3)
        companion_message: Message when companion activates (optional)

    Returns:
        EventResult with companion activation message if activated,
        None if trust not high enough
    """
    trust_state = actor.properties.get("trust_state", {})
    current_trust = trust_state.get("current", 0)

    if current_trust < trust_threshold:
        return None

    # Check if already a companion
    if actor.properties.get("is_companion", False):
        return None

    # Activate companion status
    make_companion(accessor, actor.id)

    # Generate feedback
    if companion_message:
        feedback = companion_message
    else:
        feedback = (
            f"{actor.name} has become your companion! "
            f"They will follow you on your journey."
        )

    return EventResult(allow=True, feedback=feedback)


def activate_companion_on_state_transition(
    actor: Any,
    accessor: Any,
    context: dict[str, Any],
    companion_state: str = "companion",
    companion_message: Optional[str] = None,
) -> EventResult | None:
    """Activate companion status when state machine transitions to companion state.

    Intended for use in state change event handlers. Checks if new_state
    matches companion_state and activates companion if so.

    Args:
        actor: The actor whose state is changing
        accessor: StateAccessor instance
        context: Context dict with new_state
        companion_state: State name that triggers companion activation
        companion_message: Message when companion activates (optional)

    Returns:
        EventResult with companion activation message if state matches,
        None if state doesn't match or already a companion
    """
    new_state = context.get("new_state")
    if new_state != companion_state:
        return None

    # Check if already a companion
    if actor.properties.get("is_companion", False):
        return None

    # Activate companion status
    make_companion(accessor, actor.id)

    # Generate feedback
    if companion_message:
        feedback = companion_message
    else:
        feedback = (
            f"{actor.name} has become your companion! "
            f"They will follow you on your journey."
        )

    return EventResult(allow=True, feedback=feedback)


def check_companion_benefit(
    accessor: Any,
    companion_type: str,
    benefit_check: Optional[Callable[[Any], bool]] = None,
) -> bool:
    """Check if player has a companion that provides a specific benefit.

    Uses companion_lib.get_companions() to find active companions,
    then checks for companion_type match.

    Args:
        accessor: StateAccessor instance
        companion_type: String to match in companion ID (e.g., "salamander", "wolf")
        benefit_check: Optional callable(companion) -> bool for custom checks

    Returns:
        True if player has matching companion, False otherwise

    Example:
        # Check for salamander companion (cold immunity)
        has_salamander = check_companion_benefit(accessor, "salamander")

        # Check for wolf companion with custom criteria
        def is_alpha(comp):
            return "alpha" in comp.id.lower()
        has_alpha = check_companion_benefit(accessor, "wolf", is_alpha)
    """
    from behavior_libraries.companion_lib.following import get_companions

    companions = get_companions(accessor)

    for companion in companions:
        # Check type match
        if companion_type.lower() in companion.id.lower():
            # If no custom check, type match is sufficient
            if benefit_check is None:
                return True
            # Otherwise apply custom check
            if benefit_check(companion):
                return True

    return False
