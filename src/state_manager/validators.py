"""
Structural validators for simplified state manager.

Validates structural integrity: IDs, references, cycles.
Does not validate behavior-specific properties.
"""
from typing import Dict, List, Set, Any

from .state_manager import GameState


class ValidationError(Exception):
    """Raised when validation fails."""

    def __init__(self, message: str, errors: List[str] = None):
        self.errors = errors or [message]
        if len(self.errors) == 1:
            super().__init__(self.errors[0])
        else:
            super().__init__(f"{len(self.errors)} validation errors:\n" +
                           "\n".join(f"  - {e}" for e in self.errors))


def validate_game_state(state: GameState) -> None:
    """Validate structural integrity of game state."""
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

    if errors:
        raise ValidationError("Validation failed", errors)


def _build_id_registry(state: GameState, errors: List[str]) -> Dict[str, str]:
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
        add_id(item.id, "item")
    for door in state.doors:
        add_id(door.id, "door")
    for lock in state.locks:
        add_id(lock.id, "lock")
    for npc in state.npcs:
        add_id(npc.id, "npc")

    return registry


def _validate_exit_references(state: GameState, registry: Dict[str, str],
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
                elif registry[exit_desc.door_id] != "door":
                    errors.append(
                        f"Exit '{direction}' in '{loc.id}' references "
                        f"'{exit_desc.door_id}' which is a {registry[exit_desc.door_id]}, not a door"
                    )


def _validate_item_locations(state: GameState, registry: Dict[str, str],
                             errors: List[str]) -> None:
    """Validate item location references."""
    valid_location_types = {"location", "item", "npc", "player"}

    for item in state.items:
        loc = item.location
        if not loc:
            continue

        if loc == "player":
            continue  # Player is valid

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


def _validate_door_references(state: GameState, registry: Dict[str, str],
                              errors: List[str]) -> None:
    """Validate door location references."""
    for door in state.doors:
        for loc_id in door.locations:
            if loc_id not in registry:
                errors.append(
                    f"Door '{door.id}' references nonexistent location '{loc_id}'"
                )
            elif registry[loc_id] != "location":
                errors.append(
                    f"Door '{door.id}' references '{loc_id}' "
                    f"which is a {registry[loc_id]}, not a location"
                )


def _validate_lock_references(state: GameState, registry: Dict[str, str],
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

    # Check door lock_id references
    lock_ids = {lock.id for lock in state.locks}
    for door in state.doors:
        lock_id = door.properties.get("lock_id")
        if lock_id:
            if lock_id not in lock_ids:
                errors.append(
                    f"Door '{door.id}' references nonexistent lock '{lock_id}'"
                )


def _validate_container_lock_references(state: GameState, registry: Dict[str, str],
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


def _validate_metadata(state: GameState, registry: Dict[str, str],
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


def _validate_player_state(state: GameState, registry: Dict[str, str],
                           errors: List[str]) -> None:
    """Validate player state references."""
    if not state.player:
        return

    # Validate location
    loc = state.player.location
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
    for item_id in state.player.inventory:
        if item_id not in registry:
            errors.append(
                f"Player inventory contains nonexistent item '{item_id}'"
            )
        elif registry[item_id] != "item":
            errors.append(
                f"Player inventory contains '{item_id}' "
                f"which is a {registry[item_id]}, not an item"
            )


def _validate_container_cycles(state: GameState, errors: List[str]) -> None:
    """Detect circular containment in items."""
    # Build containment graph: item -> container
    item_ids = {item.id for item in state.items}

    for item in state.items:
        if item.location in item_ids:
            # This item is inside another item, check for cycle
            visited: Set[str] = set()
            current = item.id

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
                    current = current_item.location
                else:
                    break
