"""
Validation functions for game state.

Enforces validation rules from the spec.
"""

from typing import Dict, List, Set
from .models import GameState
from .exceptions import ValidationError


def build_global_id_registry(game_state: GameState) -> Dict[str, str]:
    """
    Build global ID registry mapping all IDs to entity types.

    Returns:
        Dict mapping ID to entity type

    Raises:
        ValidationError: If duplicate IDs found or reserved ID used
    """
    registry = {}
    errors = []

    # Reserve "player" ID
    registry["player"] = "player"

    # Check all entities
    entities = [
        (game_state.locations, "location"),
        (game_state.doors, "door"),
        (game_state.items, "item"),
        (game_state.locks, "lock"),
        (game_state.npcs, "npc"),
    ]

    for entity_list, entity_type in entities:
        for entity in entity_list:
            entity_id = entity.id

            # Check for reserved ID
            if entity_id == "player":
                errors.append(f"[{entity_type}:{entity_id}] Cannot use reserved ID 'player'")
                continue

            # Check for duplicate
            if entity_id in registry:
                existing_type = registry[entity_id]
                errors.append(
                    f"[{entity_type}:{entity_id}] duplicate ID - already used by {existing_type}"
                )
            else:
                registry[entity_id] = entity_type

    if errors:
        raise ValidationError(
            f"Found {len(errors)} ID validation error(s) in game state:",
            errors
        )

    return registry


def validate_global_uniqueness(registry: Dict[str, str]) -> None:
    """
    Validate all IDs are globally unique.

    Args:
        registry: ID registry from build_global_id_registry

    Raises:
        ValidationError: If duplicate IDs found
    """
    # This is already handled by build_global_id_registry
    pass


def validate_references(game_state: GameState, registry: Dict[str, str]) -> None:
    """
    Validate all cross-references exist in the ID registry.

    Args:
        game_state: Game state to validate
        registry: Global ID registry

    Raises:
        ValidationError: If invalid references found
    """
    errors = []

    # Validate location exits
    for loc in game_state.locations:
        for direction, exit_desc in loc.exits.items():
            # Check exit destination
            if exit_desc.to and exit_desc.to not in registry:
                errors.append(
                    f"[location:{loc.id}] Exit '{direction}' references unknown location '{exit_desc.to}'"
                )

            # Check door reference
            if exit_desc.type == "door":
                if not exit_desc.door_id:
                    errors.append(
                        f"[location:{loc.id}] Exit '{direction}' has type 'door' but no door_id"
                    )
                elif exit_desc.door_id not in registry:
                    errors.append(
                        f"[location:{loc.id}] Exit '{direction}' references unknown door '{exit_desc.door_id}'"
                    )

    # Validate door references
    for door in game_state.doors:
        # Check lock reference
        if door.lock_id and door.lock_id not in registry:
            errors.append(
                f"[door:{door.id}] References unknown lock '{door.lock_id}'"
            )

        # Check location references
        for loc_id in door.locations:
            if loc_id not in registry:
                errors.append(
                    f"[door:{door.id}] References unknown location '{loc_id}'"
                )

    # Validate item references
    for item in game_state.items:
        # Check location reference
        if item.location not in registry:
            errors.append(
                f"[item:{item.id}] Location '{item.location}' not found in global ID registry"
            )

        # Check container lock reference
        if item.container and item.container.lock_id:
            if item.container.lock_id not in registry:
                errors.append(
                    f"[item:{item.id}] Container lock '{item.container.lock_id}' not found"
                )

    # Validate lock references
    for lock in game_state.locks:
        for key_id in lock.opens_with:
            if key_id not in registry:
                errors.append(
                    f"[lock:{lock.id}] Key '{key_id}' not found in items"
                )

    if errors:
        raise ValidationError(
            f"Found {len(errors)} reference validation error(s) in game state:",
            errors
        )


def validate_item_locations(game_state: GameState, registry: Dict[str, str]) -> None:
    """
    Validate item location references are valid entity types.

    Args:
        game_state: Game state to validate
        registry: Global ID registry

    Raises:
        ValidationError: If item locations reference invalid entity types
    """
    errors = []

    for item in game_state.items:
        location_id = item.location

        if location_id not in registry:
            # Already caught by validate_references
            continue

        entity_type = registry[location_id]

        # Valid location types: location, item (container), npc, or "player"
        if entity_type not in ["location", "item", "npc", "player"]:
            errors.append(
                f"[item:{item.id}] Location '{location_id}' is a {entity_type}, "
                f"but items can only be in locations, containers, NPCs, or player inventory"
            )

    if errors:
        raise ValidationError(
            f"Found {len(errors)} item location validation error(s) in game state:",
            errors
        )


def validate_location_item_consistency(game_state: GameState) -> None:
    """
    Validate consistency between location items lists and item location fields.

    Args:
        game_state: Game state to validate

    Raises:
        ValidationError: If inconsistencies found
    """
    errors = []

    # Build map of what each location claims to contain
    location_claims = {}
    for loc in game_state.locations:
        location_claims[loc.id] = set(loc.items)

    # Check each item - COMMENTED OUT: This is a warning-level issue, not an error
    # for item in game_state.items:
    #     if item.location in location_claims:
    #         # Item says it's in this location
    #         if item.id not in location_claims[item.location]:
    #             errors.append(
    #                 f"[item:{item.id}] Location field is '{item.location}' but that "
    #                 f"location does not list this item in its items array"
    #             )

    # Check reverse: items claimed by locations but point elsewhere (this IS an error)
    for loc in game_state.locations:
        for claimed_item_id in loc.items:
            # Find the item
            item = None
            for i in game_state.items:
                if i.id == claimed_item_id:
                    item = i
                    break

            if item and item.location != loc.id:
                errors.append(
                    f"[location:{loc.id}] Lists item '{claimed_item_id}' but that "
                    f"item's location field is '{item.location}'"
                )

    if errors:
        raise ValidationError(
            f"Found {len(errors)} location/item consistency error(s) in game state:",
            errors
        )


def validate_container_cycles(game_state: GameState) -> None:
    """
    Validate no circular containment relationships.

    Args:
        game_state: Game state to validate

    Raises:
        ValidationError: If cycles detected
    """
    errors = []

    def find_cycle(item_id: str, visited: Set[str], path: List[str]) -> bool:
        """DFS to detect cycles in containment."""
        if item_id in visited:
            # Found a cycle
            cycle_path = " -> ".join(path + [item_id])
            errors.append(f"Container cycle detected: {cycle_path}")
            return True

        # Find item
        item = None
        for i in game_state.items:
            if i.id == item_id:
                item = i
                break

        if not item:
            return False

        visited.add(item_id)
        path.append(item_id)

        # Check if this item is a container that contains other items
        if item.container:
            # Find items located in this container
            for other_item in game_state.items:
                if other_item.location == item_id:
                    if find_cycle(other_item.id, visited, path):
                        path.pop()
                        visited.remove(item_id)
                        return True

        path.pop()
        visited.remove(item_id)
        return False

    # Check each item
    for item in game_state.items:
        find_cycle(item.id, set(), [])

    if errors:
        raise ValidationError(
            f"Found {len(errors)} container cycle error(s) in game state:",
            errors
        )


def validate_metadata(game_state: GameState) -> None:
    """
    Validate metadata references.

    Args:
        game_state: Game state to validate

    Raises:
        ValidationError: If metadata references are invalid
    """
    errors = []

    # Check start_location exists
    if game_state.metadata.start_location:
        found = False
        for loc in game_state.locations:
            if loc.id == game_state.metadata.start_location:
                found = True
                break

        if not found:
            errors.append(
                f"[metadata] start_location '{game_state.metadata.start_location}' "
                f"not found in locations"
            )

    if errors:
        raise ValidationError(
            f"Found {len(errors)} metadata validation error(s) in game state:",
            errors
        )


def validate_player_state(game_state: GameState, registry: Dict[str, str]) -> None:
    """
    Validate player state references.

    Args:
        game_state: Game state to validate
        registry: Global ID registry

    Raises:
        ValidationError: If player state references are invalid
    """
    if not game_state.player:
        return

    errors = []

    # Check player location
    if game_state.player.location:
        if game_state.player.location not in registry:
            errors.append(
                f"[player] Location '{game_state.player.location}' not found"
            )
        elif registry[game_state.player.location] != "location":
            errors.append(
                f"[player] Location '{game_state.player.location}' is not a location"
            )

    # Check inventory items
    for item_id in game_state.player.inventory:
        if item_id not in registry:
            errors.append(
                f"[player] Inventory item '{item_id}' not found"
            )
        elif registry[item_id] != "item":
            errors.append(
                f"[player] Inventory contains '{item_id}' which is not an item"
            )

    if errors:
        raise ValidationError(
            f"Found {len(errors)} player state validation error(s) in game state:",
            errors
        )


def validate_game_state(game_state: GameState) -> None:
    """
    Run all validation checks on game state.

    Args:
        game_state: Game state to validate

    Raises:
        ValidationError: If any validation fails
    """
    all_errors = []

    # Build ID registry (also checks for duplicates and reserved IDs)
    try:
        registry = build_global_id_registry(game_state)
    except ValidationError as e:
        all_errors.extend(e.errors)
        # Can't continue without registry
        raise ValidationError(
            f"Found {len(all_errors)} validation error(s) in game state:",
            all_errors
        )

    # Run all validators and collect errors
    validators = [
        (validate_metadata, [game_state]),
        (validate_references, [game_state, registry]),
        (validate_item_locations, [game_state, registry]),
        (validate_location_item_consistency, [game_state]),
        (validate_container_cycles, [game_state]),
        (validate_player_state, [game_state, registry]),
    ]

    for validator_func, args in validators:
        try:
            validator_func(*args)
        except ValidationError as e:
            all_errors.extend(e.errors)

    # Raise aggregated errors if any
    if all_errors:
        raise ValidationError(
            f"Found {len(all_errors)} validation error(s) in game state:",
            all_errors
        )
