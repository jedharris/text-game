"""
Structural validators for simplified state manager.

Validates structural integrity: IDs, references, cycles.
Does not validate behavior-specific properties.
"""
from typing import Dict, List, Set, Any, Optional, TYPE_CHECKING

from src.types import ActorId, ItemId

# Prohibited actor names (case-insensitive)
# These create ambiguity with self-reference or generic terms
PROHIBITED_ACTOR_NAMES = {"player", "npc", "self", "me", "myself"}

if TYPE_CHECKING:
    from src.state_manager import GameState


class ValidationError(Exception):
    """Raised when validation fails."""

    def __init__(self, message: str, errors: Optional[List[str]] = None):
        self.errors = errors or [message]
        if len(self.errors) == 1:
            super().__init__(self.errors[0])
        else:
            super().__init__(f"{len(self.errors)} validation errors:\n" +
                           "\n".join(f"  - {e}" for e in self.errors))


def validate_game_state(state: "GameState", loaded_modules: Optional[Set[str]] = None) -> None:
    """Validate structural integrity of game state.

    Args:
        state: GameState to validate
        loaded_modules: Optional set of loaded behavior module names. If provided,
                       validates that all behavior references in entities point to
                       loaded modules. Pass this after loading behavior modules.
    """
    errors: List[str] = []

    # Build ID registry
    id_registry = _build_id_registry(state, errors)

    # Validate references
    _validate_exit_references(state, id_registry, errors)
    _validate_item_locations(state, id_registry, errors)
    _validate_door_references(state, id_registry, errors)
    _validate_lock_references(state, id_registry, errors)
    _validate_container_lock_references(state, id_registry, errors)
    _validate_metadata(state, id_registry, errors)
    _validate_player_state(state, id_registry, errors)
    _validate_container_cycles(state, errors)
    _validate_actor_names(state, errors)
    _validate_parts(state, id_registry, errors)

    # Validate behavior module references if modules provided
    if loaded_modules is not None:
        _validate_behavior_references(state, loaded_modules, errors)

    if errors:
        raise ValidationError("Validation failed", errors)


def _build_id_registry(state: "GameState", errors: List[str]) -> Dict[str, str]:
    """Build registry of all entity IDs and check for duplicates/reserved."""
    registry: Dict[str, str] = {}
    registry["player"] = "player"  # Reserved

    def add_id(entity_id: str, entity_type: str):
        if entity_id == "player":
            errors.append(f"ID 'player' is reserved, cannot use for {entity_type}")
        elif entity_id in registry:
            errors.append(f"Duplicate ID '{entity_id}' (used by {registry[entity_id]} and {entity_type})")
        else:
            registry[entity_id] = entity_type

    for loc in state.locations:
        add_id(loc.id, "location")
    for item in state.items:
        # Items with properties.door are registered as "door_item" for unified model
        if item.is_door:
            add_id(item.id, "door_item")
        else:
            add_id(item.id, "item")
    for lock in state.locks:
        add_id(lock.id, "lock")
    for actor_id, actor in state.actors.items():
        if actor_id != "player":
            add_id(actor_id, "npc")
    for part in state.parts:
        add_id(part.id, "part")

    return registry


def _validate_exit_references(state: "GameState", registry: Dict[str, str],
                              errors: List[str]) -> None:
    """Validate exit references to locations and doors."""
    for loc in state.locations:
        for direction, exit_desc in loc.exits.items():
            # Check 'to' reference
            if exit_desc.to:
                if exit_desc.to not in registry:
                    errors.append(
                        f"Exit '{direction}' in '{loc.id}' references "
                        f"nonexistent location '{exit_desc.to}'"
                    )
                elif registry[exit_desc.to] != "location":
                    errors.append(
                        f"Exit '{direction}' in '{loc.id}' references "
                        f"'{exit_desc.to}' which is a {registry[exit_desc.to]}, not a location"
                    )

            # Check door_id reference
            if exit_desc.type == "door":
                if not exit_desc.door_id:
                    errors.append(
                        f"Exit '{direction}' in '{loc.id}' is type 'door' "
                        f"but missing door_id"
                    )
                elif exit_desc.door_id not in registry:
                    errors.append(
                        f"Exit '{direction}' in '{loc.id}' references "
                        f"nonexistent door '{exit_desc.door_id}'"
                    )
                elif registry[exit_desc.door_id] not in ("door", "door_item"):
                    # Accept both old-style doors and unified door items
                    errors.append(
                        f"Exit '{direction}' in '{loc.id}' references "
                        f"'{exit_desc.door_id}' which is a {registry[exit_desc.door_id]}, not a door"
                    )


def _validate_item_locations(state: "GameState", registry: Dict[str, str],
                             errors: List[str]) -> None:
    """Validate item location references."""
    valid_location_types = {"location", "item", "npc", "player"}

    for item in state.items:
        loc = item.location
        if not loc:
            continue

        if loc == "player":
            continue  # Player is valid

        # Handle exit:loc_id:direction format for door items
        if loc.startswith("exit:"):
            if not item.is_door:
                errors.append(
                    f"Item '{item.id}' uses exit location '{loc}' "
                    f"but is not a door item"
                )
                continue
            # Validate format: exit:location_id:direction
            parts = loc.split(":")
            if len(parts) != 3:
                errors.append(
                    f"Door item '{item.id}' has malformed exit location '{loc}' "
                    f"(expected format: exit:location_id:direction)"
                )
                continue
            exit_loc_id = parts[1]
            if exit_loc_id not in registry:
                errors.append(
                    f"Door item '{item.id}' references nonexistent location "
                    f"'{exit_loc_id}' in exit location '{loc}'"
                )
            elif registry[exit_loc_id] != "location":
                errors.append(
                    f"Door item '{item.id}' exit location references '{exit_loc_id}' "
                    f"which is a {registry[exit_loc_id]}, not a location"
                )
            continue

        if loc not in registry:
            errors.append(
                f"Item '{item.id}' has invalid location '{loc}' "
                f"(entity does not exist)"
            )
        elif registry[loc] not in valid_location_types:
            errors.append(
                f"Item '{item.id}' has invalid location '{loc}' "
                f"(cannot be placed in a {registry[loc]})"
            )


def _validate_door_references(state: "GameState", registry: Dict[str, str],
                              errors: List[str]) -> None:
    """Validate door item references via exits."""
    # Door items are validated through exit references
    # No separate validation needed since doors are now items
    pass


def _validate_lock_references(state: "GameState", registry: Dict[str, str],
                              errors: List[str]) -> None:
    """Validate lock opens_with references and door lock_id references."""
    # Check lock opens_with references
    for lock in state.locks:
        opens_with = lock.properties.get("opens_with", [])
        for key_id in opens_with:
            if key_id not in registry:
                errors.append(
                    f"Lock '{lock.id}' opens_with references "
                    f"nonexistent item '{key_id}'"
                )
            elif registry[key_id] != "item":
                errors.append(
                    f"Lock '{lock.id}' opens_with references '{key_id}' "
                    f"which is a {registry[key_id]}, not an item"
                )

    # Check door item lock_id references
    lock_ids = {lock.id for lock in state.locks}
    for item in state.items:
        if item.is_door and item.door_lock_id:
            if item.door_lock_id not in lock_ids:
                errors.append(
                    f"Door '{item.id}' references nonexistent lock '{item.door_lock_id}'"
                )


def _validate_container_lock_references(state: "GameState", registry: Dict[str, str],
                                        errors: List[str]) -> None:
    """Validate container lock_id references."""
    lock_ids = {lock.id for lock in state.locks}

    for item in state.items:
        container = item.properties.get("container", {})
        lock_id = container.get("lock_id")
        if lock_id:
            if lock_id not in lock_ids:
                errors.append(
                    f"Container '{item.id}' references nonexistent lock '{lock_id}'"
                )


def _validate_metadata(state: "GameState", registry: Dict[str, str],
                       errors: List[str]) -> None:
    """Validate metadata references."""
    start = state.metadata.start_location
    if start:
        if start not in registry:
            errors.append(
                f"Metadata start_location '{start}' does not exist"
            )
        elif registry[start] != "location":
            errors.append(
                f"Metadata start_location '{start}' "
                f"is a {registry[start]}, not a location"
            )


def _validate_player_state(state: "GameState", registry: Dict[str, str],
                           errors: List[str]) -> None:
    """Validate player state references."""
    player = state.actors.get(ActorId("player"))
    if not player:
        return

    # Validate location
    loc = player.location
    if loc:
        if loc not in registry:
            errors.append(
                f"Player location '{loc}' does not exist"
            )
        elif registry[loc] != "location":
            errors.append(
                f"Player location '{loc}' "
                f"is a {registry[loc]}, not a location"
            )

    # Validate inventory
    for item_id in player.inventory:
        if item_id not in registry:
            errors.append(
                f"Player inventory contains nonexistent item '{item_id}'"
            )
        elif registry[item_id] != "item":
            errors.append(
                f"Player inventory contains '{item_id}' "
                f"which is a {registry[item_id]}, not an item"
            )


def _validate_container_cycles(state: "GameState", errors: List[str]) -> None:
    """Detect circular containment in items."""
    # Build containment graph: item -> container
    item_ids = {item.id for item in state.items}

    for item in state.items:
        if item.location in item_ids:
            # This item is inside another item, check for cycle
            visited: Set[ItemId] = set()
            current: Optional[ItemId] = item.id

            while current:
                if current in visited:
                    errors.append(
                        f"Containment cycle detected involving '{item.id}'"
                    )
                    break
                visited.add(current)

                # Find the container for current item
                current_item = next(
                    (i for i in state.items if i.id == current), None
                )
                if current_item and current_item.location in item_ids:
                    current = ItemId(current_item.location)
                else:
                    break


def _validate_behavior_references(state: "GameState", loaded_modules: Set[str],
                                   errors: List[str]) -> None:
    """Validate that all behavior module references point to loaded modules."""

    def check_behaviors(entity_id: str, entity_type: str, behaviors: Any) -> None:
        if not behaviors:
            return
        if isinstance(behaviors, list):
            for module_name in behaviors:
                if module_name not in loaded_modules:
                    errors.append(
                        f"{entity_type} '{entity_id}' references unknown behavior "
                        f"module '{module_name}'"
                    )

    # Check items
    for item in state.items:
        if hasattr(item, 'behaviors'):
            check_behaviors(item.id, "Item", item.behaviors)

    # Check actors
    for actor_id, actor in state.actors.items():
        if hasattr(actor, 'behaviors'):
            check_behaviors(actor_id, "Actor", actor.behaviors)

    # Check locations
    for location in state.locations:
        if hasattr(location, 'behaviors'):
            check_behaviors(location.id, "Location", location.behaviors)

    # Check door items
    for item in state.items:
        if item.is_door and hasattr(item, 'behaviors'):
            check_behaviors(item.id, "Door", item.behaviors)


def _validate_actor_names(state: "GameState", errors: List[str]) -> None:
    """Validate that actors don't have prohibited names.

    Prohibited names (case-insensitive):
    - "player", "npc": ambiguous in multiplayer and general contexts
    - "self", "me", "myself": reserved for self-reference vocabulary
    """
    for actor_id, actor in state.actors.items():
        if actor.name and actor.name.lower() in PROHIBITED_ACTOR_NAMES:
            errors.append(
                f"Actor '{actor_id}' has prohibited name '{actor.name}' "
                f"(reserved words: {', '.join(sorted(PROHIBITED_ACTOR_NAMES))})"
            )


def _validate_parts(state: "GameState", registry: Dict[str, str],
                    errors: List[str]) -> None:
    """Validate Part entities.

    Checks:
    - Required fields (id, name, part_of)
    - part_of references valid entity
    - No nested parts (parts cannot have parts as parents in Phase 1)
    """
    for part in state.parts:
        # Check required fields
        if not part.id:
            errors.append("Part has empty id")
        if not part.name:
            errors.append(f"Part {part.id} has empty name")
        if not part.part_of:
            errors.append(f"Part {part.id} missing required part_of field")

        # Check part_of references valid entity
        if part.part_of:
            if part.part_of not in registry:
                errors.append(
                    f"Part {part.id} references non-existent parent {part.part_of}"
                )
            # Phase 1 constraint: parts cannot have parts (no nesting yet)
            elif registry.get(part.part_of) == "part":
                errors.append(
                    f"Part {part.id} cannot have another part as parent "
                    f"(nested parts not supported in Phase 1)"
                )
