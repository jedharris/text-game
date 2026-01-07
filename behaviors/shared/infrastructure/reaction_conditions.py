"""Condition checkers for reaction system.

Conditions determine WHEN a reaction applies. All conditions must pass
for the reaction to execute.
"""

from typing import Any, Callable, Dict


# Type alias for condition checker functions
ConditionChecker = Callable[[Dict[str, Any], Any, Any, Dict[str, Any]], bool]


def _check_flags(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> bool:
    """Check if all required flags match.

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being checked
        context: Event context

    Returns:
        True if all flags match required values
    """
    required = config.get("requires_flags", {})
    if not required:
        return True

    extra = state.extra if hasattr(state, "extra") else {}
    return all(extra.get(k) == v for k, v in required.items())


def _check_not_flags(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> bool:
    """Check that required flags do NOT match (negated check).

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being checked
        context: Event context

    Returns:
        True if all flags do NOT match required values
    """
    required = config.get("requires_not_flags", {})
    if not required:
        return True

    extra = state.extra if hasattr(state, "extra") else {}
    return all(extra.get(k) != v for k, v in required.items())


def _check_state(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> bool:
    """Check if entity is in one of required states.

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being checked
        context: Event context

    Returns:
        True if entity state matches one of required states
    """
    required_states = config.get("requires_state", [])
    if not required_states:
        return True

    if not hasattr(entity, "properties"):
        return False

    sm = entity.properties.get("state_machine", {})
    current = sm.get("current", sm.get("initial"))

    return current in required_states


def _check_trust(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> bool:
    """Check if entity trust >= threshold.

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being checked
        context: Event context

    Returns:
        True if trust meets or exceeds threshold
    """
    min_trust = config.get("requires_trust")
    if min_trust is None:
        return True

    if not hasattr(entity, "properties"):
        return False

    trust_state = entity.properties.get("trust_state", {})
    current_trust = trust_state.get("current", 0)

    return current_trust >= min_trust


def _check_items(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> bool:
    """Check if player has required items.

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being checked
        context: Event context

    Returns:
        True if player has all required items
    """
    required_items = config.get("requires_items", [])
    if not required_items:
        return True

    # Get player actor
    player = state.actors.get("player") if hasattr(state, "actors") else None
    if not player:
        return False

    inventory = player.inventory if hasattr(player, "inventory") else []

    return all(item_id in inventory for item_id in required_items)


def _check_property(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> bool:
    """Check property condition (game-agnostic Tier 1 primitive).

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being checked
        context: Event context

    Returns:
        True if property condition satisfied
    """
    prop_conditions = config.get("require_property")
    if not prop_conditions:
        return True

    # Handle single condition or list of conditions
    if not isinstance(prop_conditions, list):
        prop_conditions = [prop_conditions]

    for condition in prop_conditions:
        if not _check_single_property(condition, state, entity):
            return False

    return True


def _check_single_property(condition: Dict[str, Any], state: Any, entity: Any) -> bool:
    """Check a single property condition.

    Args:
        condition: Property condition dict with path and constraints
        state: GameState instance
        entity: Entity being checked

    Returns:
        True if property satisfies all constraints
    """
    path = condition.get("path")
    if not path:
        return True

    # Get property value
    value = _get_property_value(path, state, entity)
    if value is None:
        return False

    # Check constraints
    if "min" in condition and value < condition["min"]:
        return False
    if "max" in condition and value > condition["max"]:
        return False
    if "equals" in condition and value != condition["equals"]:
        return False
    if "in" in condition and value not in condition["in"]:
        return False
    if "not_equals" in condition and value == condition["not_equals"]:
        return False
    if "not_in" in condition and value in condition["not_in"]:
        return False

    return True


def _get_property_value(path: str, state: Any, entity: Any) -> Any:
    """Get property value from dot-notation path.

    Args:
        path: Dot-notation path like "trust_state.current" or "extra.flag_name"
        state: GameState instance
        entity: Entity being checked

    Returns:
        Property value or None if not found
    """
    parts = path.split(".")

    # Decide whether to start from entity or state
    if parts[0] == "extra":
        current = state.extra if hasattr(state, "extra") else None
        parts = parts[1:]  # Skip "extra" prefix
    elif hasattr(entity, "properties"):
        current = entity.properties
    else:
        return None

    # Navigate path
    for part in parts:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)

    return current


# Registry of all condition checkers
CONDITION_REGISTRY: Dict[str, ConditionChecker] = {
    "requires_flags": _check_flags,
    "requires_not_flags": _check_not_flags,
    "requires_state": _check_state,
    "requires_trust": _check_trust,
    "requires_items": _check_items,
    "require_property": _check_property,
}


# Execution order for conditions (all must pass)
CONDITION_ORDER = [
    "require_property",  # Generic first
    "requires_flags",
    "requires_not_flags",
    "requires_state",
    "requires_trust",
    "requires_items",
]
