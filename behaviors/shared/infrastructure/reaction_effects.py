"""Effect handlers for reaction system.

Effects define WHAT a reaction does. They are applied in deterministic order
after all conditions pass.
"""

from typing import Any, Callable, Dict, List


# Type alias for effect handler functions
EffectHandler = Callable[[Dict[str, Any], Any, Any, Dict[str, Any]], None]


def _unset_flags(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> None:
    """Remove flags from game state.

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being modified
        context: Event context
    """
    flags_to_unset = config.get("unset_flags", [])
    extra = state.extra if hasattr(state, "extra") else {}

    for flag_name in flags_to_unset:
        extra.pop(flag_name, None)


def _set_flags(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> None:
    """Set game state flags.

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being modified
        context: Event context
    """
    flags = config.get("set_flags", {})
    extra = state.extra if hasattr(state, "extra") else {}

    for flag_name, flag_value in flags.items():
        extra[flag_name] = flag_value


def _remove_condition(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> None:
    """Remove status effect from entity.

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being modified
        context: Event context
    """
    condition_type = config.get("remove_condition")
    if not condition_type or not hasattr(entity, "properties"):
        return

    conditions = entity.properties.get("conditions", {})
    if condition_type in conditions:
        del conditions[condition_type]

        # TODO: Hook firing should happen at engine level, not in effect handler
        # The condition system should detect condition changes and fire hooks


def _apply_condition(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> None:
    """Apply status effect to entity.

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being modified
        context: Event context
    """
    condition_config = config.get("apply_condition")
    if not condition_config or not hasattr(entity, "properties"):
        return

    # Ensure conditions dict exists
    if "conditions" not in entity.properties:
        entity.properties["conditions"] = {}

    conditions = entity.properties["conditions"]

    # condition_config can be string (name) or dict (name + details)
    condition_name = None
    if isinstance(condition_config, str):
        condition_name = condition_config
        conditions[condition_name] = {"severity": 50}  # Default severity
    elif isinstance(condition_config, dict):
        condition_name = condition_config.get("name") or condition_config.get("type")
        if condition_name:
            conditions[condition_name] = {
                "severity": condition_config.get("severity", 50),
                **{k: v for k, v in condition_config.items() if k not in ["name", "type"]}
            }

    # TODO: Hook firing should happen at engine level, not in effect handler
    # The condition system should detect condition changes and fire hooks


def _modify_property(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> None:
    """Modify property using game-agnostic Tier 1 primitive.

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being modified
        context: Event context
    """
    modifications = config.get("modify_property")
    if not modifications:
        return

    # Handle single modification or list
    if not isinstance(modifications, list):
        modifications = [modifications]

    for mod in modifications:
        _apply_property_modification(mod, state, entity)


def _apply_property_modification(mod: Dict[str, Any], state: Any, entity: Any) -> None:
    """Apply a single property modification.

    Args:
        mod: Modification dict with path and operation
        state: GameState instance
        entity: Entity being modified
    """
    path = mod.get("path")
    if not path:
        return

    # Get current value
    parts = path.split(".")
    if parts[0] == "extra":
        container = state.extra if hasattr(state, "extra") else None
        parts = parts[1:]
    elif hasattr(entity, "properties"):
        container = entity.properties
    else:
        return

    # Navigate to parent
    current = container
    for part in parts[:-1]:
        if not isinstance(current, dict):
            return
        if part not in current:
            current[part] = {}
        current = current[part]

    # Apply modification
    key = parts[-1]

    # Type guard: current should never be None at this point
    if current is None:
        return

    if "set" in mod:
        current[key] = mod["set"]
    elif "delta" in mod:
        current[key] = current.get(key, 0) + mod["delta"]
    elif "multiply" in mod:
        current[key] = current.get(key, 1) * mod["multiply"]
    elif "append" in mod:
        if key not in current:
            current[key] = []
        items = mod["append"] if isinstance(mod["append"], list) else [mod["append"]]
        for item in items:
            if item not in current[key]:
                current[key].append(item)
    elif "remove" in mod:
        if key not in current or not isinstance(current[key], list):
            return
        items = mod["remove"] if isinstance(mod["remove"], list) else [mod["remove"]]
        current[key] = [x for x in current[key] if x not in items]
    elif "merge" in mod:
        if key not in current:
            current[key] = {}
        current[key].update(mod["merge"])


def _apply_damage(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> None:
    """Deal damage (DEPRECATED - use modify_property).

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being modified
        context: Event context
    """
    damage = config.get("apply_damage", 0)
    if damage > 0 and hasattr(entity, "properties"):
        health = entity.properties.get("health", 0)
        entity.properties["health"] = max(0, health - damage)
        context["damage_dealt"] = damage


def _heal_entity(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> None:
    """Restore health (DEPRECATED - use modify_property).

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being modified
        context: Event context
    """
    heal_amount = config.get("heal_amount", 0)
    if heal_amount > 0 and hasattr(entity, "properties"):
        health = entity.properties.get("health", 0)
        max_health = entity.properties.get("max_health", 100)
        entity.properties["health"] = min(max_health, health + heal_amount)
        context["heal_amount"] = heal_amount


def _apply_trust_delta(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> None:
    """Modify trust (Tier 2 convenience - compiles to modify_property).

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being modified
        context: Event context
    """
    delta = config.get("trust_delta")
    if delta is None or not hasattr(entity, "properties"):
        return

    trust_state = entity.properties.get("trust_state", {})
    if not trust_state:
        return

    current = trust_state.get("current", 0)
    floor = trust_state.get("floor", -5)
    ceiling = trust_state.get("ceiling", 5)

    new_trust = max(floor, min(ceiling, current + delta))
    trust_state["current"] = new_trust
    context["trust"] = new_trust


def _apply_trust_transitions(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> None:
    """Auto-transition based on trust thresholds (Tier 2 convenience).

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being modified
        context: Event context
    """
    transitions = config.get("trust_transitions", {})
    if not transitions or not hasattr(entity, "properties"):
        return

    trust_state = entity.properties.get("trust_state", {})
    current_trust = trust_state.get("current", 0)

    # Find highest threshold met
    target_state = None
    max_threshold = -999
    for threshold_str, state_name in transitions.items():
        threshold = int(threshold_str)
        if current_trust >= threshold and threshold > max_threshold:
            max_threshold = threshold
            target_state = state_name

    if target_state:
        sm = entity.properties.get("state_machine", {})
        if sm:
            sm["current"] = target_state
            context["new_state"] = target_state


def _transition_state(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> None:
    """Transition entity state (Tier 2 convenience).

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being modified
        context: Event context
    """
    target_state = config.get("transition_to")
    if not target_state or not hasattr(entity, "properties"):
        return

    sm = entity.properties.get("state_machine", {})
    if sm:
        sm["current"] = target_state
        context["new_state"] = target_state


def _consume_item(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> None:
    """Remove item from player inventory.

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being modified
        context: Event context
    """
    should_consume = config.get("consume_item", False)
    if not should_consume:
        return

    item = context.get("item")
    if not item:
        return

    item_id = item.id if hasattr(item, "id") else str(item)
    player = state.actors.get("player") if hasattr(state, "actors") else None

    if player and hasattr(player, "inventory"):
        if item_id in player.inventory:
            player.inventory.remove(item_id)

    # Also update item location
    if hasattr(item, "location"):
        item.location = None


def _grant_items(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> None:
    """Add items to player inventory (Tier 3 common operation).

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being modified
        context: Event context
    """
    items_to_grant = config.get("grant_items", [])
    if not items_to_grant:
        return

    player = state.actors.get("player") if hasattr(state, "actors") else None
    if not player or not hasattr(player, "inventory"):
        return

    for item_id in items_to_grant:
        if item_id not in player.inventory:
            player.inventory.append(item_id)

        # Update item location
        item = state.get_item(item_id) if hasattr(state, "get_item") else None
        if item and hasattr(item, "location"):
            item.location = "player"


def _spawn_items(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> None:
    """Create items in current location.

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being modified
        context: Event context
    """
    items_to_spawn = config.get("spawn_items", [])
    # Implementation deferred - needs item template system


def _grant_knowledge(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> None:
    """Add knowledge flags (DEPRECATED - use modify_property with append).

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being modified
        context: Event context
    """
    knowledge_items = config.get("grant_knowledge", [])
    if not knowledge_items:
        return

    player = state.actors.get("player") if hasattr(state, "actors") else None
    if not player or not hasattr(player, "properties"):
        return

    if "knowledge" not in player.properties:
        player.properties["knowledge"] = []

    for item in knowledge_items:
        if item not in player.properties["knowledge"]:
            player.properties["knowledge"].append(item)


def _add_to_collection(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> None:
    """Add to collection (Tier 1 game-agnostic).

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being modified
        context: Event context
    """
    ops = config.get("add_to_collection")
    if not ops:
        return

    if not isinstance(ops, list):
        ops = [ops]

    extra = state.extra if hasattr(state, "extra") else {}

    for op in ops:
        path = op.get("path")
        if not path:
            continue

        if path not in extra:
            extra[path] = []

        value = op.get("value") or context.get(op.get("from_context", ""))
        if value and value not in extra[path]:
            extra[path].append(value)


def _remove_from_collection(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> None:
    """Remove from collection (Tier 1 game-agnostic).

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being modified
        context: Event context
    """
    ops = config.get("remove_from_collection")
    if not ops:
        return

    if not isinstance(ops, list):
        ops = [ops]

    extra = state.extra if hasattr(state, "extra") else {}

    for op in ops:
        path = op.get("path")
        if not path or path not in extra:
            continue

        value = op.get("value") or context.get(op.get("from_context", ""))
        if value and value in extra[path]:
            extra[path].remove(value)


def _invoke_system(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> None:
    """Invoke game system (Tier 1 game-agnostic).

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being modified
        context: Event context
    """
    invocations = config.get("invoke_system")
    # Implementation deferred - needs system registry


def _track_in_list(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> None:
    """Track in list (DEPRECATED - use add_to_collection).

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being modified
        context: Event context
    """
    list_name = config.get("track_in")
    if not list_name:
        return

    extra = state.extra if hasattr(state, "extra") else {}
    if list_name not in extra:
        extra[list_name] = []

    item = context.get("item")
    if item is None:
        return
    item_id = item.id if hasattr(item, "id") else str(item)

    if item_id not in extra[list_name]:
        extra[list_name].append(item_id)


def _increment_counter(config: Dict[str, Any], state: Any, entity: Any, context: Dict[str, Any]) -> None:
    """Increment counter (DEPRECATED - use modify_property with delta).

    Args:
        config: Reaction configuration
        state: GameState instance
        entity: Entity being modified
        context: Event context
    """
    counter_name = config.get("increment_counter")
    if not counter_name:
        return

    extra = state.extra if hasattr(state, "extra") else {}
    extra[counter_name] = extra.get(counter_name, 0) + 1
    context["count"] = extra[counter_name]


# Registry of all effect handlers
EFFECT_REGISTRY: Dict[str, EffectHandler] = {
    "unset_flags": _unset_flags,
    "remove_from_collection": _remove_from_collection,
    "remove_condition": _remove_condition,
    "modify_property": _modify_property,
    "set_flags": _set_flags,
    "apply_condition": _apply_condition,
    "apply_damage": _apply_damage,
    "heal_amount": _heal_entity,
    "trust_delta": _apply_trust_delta,
    "trust_transitions": _apply_trust_transitions,
    "transition_to": _transition_state,
    "consume_item": _consume_item,
    "grant_items": _grant_items,
    "spawn_items": _spawn_items,
    "grant_knowledge": _grant_knowledge,
    "add_to_collection": _add_to_collection,
    "invoke_system": _invoke_system,
    "track_in": _track_in_list,
    "increment_counter": _increment_counter,
}


# Deterministic execution order for effects
EFFECT_ORDER = [
    "unset_flags",
    "remove_from_collection",
    "remove_condition",
    "modify_property",
    "apply_damage",
    "heal_amount",
    "set_flags",
    "apply_condition",
    "trust_delta",
    "grant_knowledge",
    "trust_transitions",
    "transition_to",
    "consume_item",
    "grant_items",
    "spawn_items",
    "add_to_collection",
    "track_in",
    "increment_counter",
    "invoke_system",
]
