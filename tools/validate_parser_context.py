#!/usr/bin/env python3
"""
Validator for parser context specification.

Checks that build_parser_context() follows the rules in docs/parser_context_specification.md
"""

from pathlib import Path
from typing import List, Dict, Any
from src.game_engine import GameEngine
from src.state_accessor import StateAccessor
from src.state_manager import GameState


def validate_parser_context(
    context: Dict[str, Any],
    game_state: GameState,
    actor_id: str
) -> List[str]:
    """
    Validate that parser context matches specification.

    Args:
        context: Result from build_parser_context()
        game_state: GameState being used
        actor_id: Actor whose context was built

    Returns:
        List of violation messages (empty if valid)
    """
    violations = []
    accessor = StateAccessor(game_state, None)  # None for behavior_manager - not needed for queries

    actor = game_state.actors.get(actor_id)
    if not actor:
        violations.append(f"Actor {actor_id} not found")
        return violations

    location_id = actor.location
    if not location_id:
        return violations  # No location, nothing to validate

    location_objects = set(context.get('location_objects', []))
    inventory = set(context.get('inventory', []))

    # Rule: Closed container contents should NOT appear
    items_here = accessor.get_entities_at(location_id, entity_type="item")
    for item in items_here:
        if hasattr(item, 'properties') and 'container' in item.properties:
            container_props = item.properties['container']
            is_container = container_props.get('is_container', False)
            is_open = item.states.get('open', True) if hasattr(item, 'states') and item.states else True

            if is_container and not is_open:
                # This is a closed container - its contents should NOT appear
                contents = accessor.get_entities_at(item.id, entity_type="item")
                for contained_item in contents:
                    contained_name = getattr(contained_item, 'name', contained_item.id)
                    if contained_name in location_objects:
                        violations.append(
                            f"VIOLATION: Item '{contained_name}' from closed container '{item.name}' "
                            f"appears in location_objects"
                        )

    # Rule: Hidden items should NOT appear
    all_items = accessor.get_entities_at(location_id, entity_type="item")
    for item in all_items:
        if hasattr(item, 'states') and item.states and item.states.get('hidden', False):
            item_name = getattr(item, 'name', item.id)
            if item_name in location_objects:
                violations.append(
                    f"VIOLATION: Hidden item '{item_name}' appears in location_objects"
                )

    # Rule: Actor should NOT appear in their own context
    actor_name = getattr(actor, 'name', actor_id)
    if actor_name in location_objects:
        violations.append(
            f"VIOLATION: Actor '{actor_name}' appears in their own location_objects"
        )

    # Rule: Items from other locations should NOT appear (except via containers/surfaces)
    # This is tricky to validate - we'd need to check every item in game and verify
    # it's either at location, or in a container at location, or in inventory
    all_game_items = game_state.items
    for item in all_game_items:
        item_name = getattr(item, 'name', item.id)

        # Skip if not in context
        if item_name not in location_objects and item_name not in inventory:
            continue

        # Check if this item should be accessible
        is_at_location = item.location == location_id
        is_in_inventory = item.location == actor_id
        is_in_accessible_container = False

        # Check if in a container at the location
        if not is_at_location and not is_in_inventory:
            container = accessor.get_item(item.location) if item.location else None
            if container and container.location == location_id:
                # Item is in a container at the location - check if accessible
                if hasattr(container, 'properties') and 'container' in container.properties:
                    container_props = container.properties['container']
                    is_surface = container_props.get('is_surface', False)
                    is_container_type = container_props.get('is_container', False)
                    is_open = container.states.get('open', True) if hasattr(container, 'states') and container.states else True

                    if is_surface or (is_container_type and is_open):
                        is_in_accessible_container = True

        # If item appears but isn't accessible, that's a violation
        if not (is_at_location or is_in_inventory or is_in_accessible_container):
            if item_name in location_objects:
                violations.append(
                    f"VIOLATION: Item '{item_name}' appears in location_objects but is not accessible "
                    f"(location: {item.location}, actor location: {location_id})"
                )
            if item_name in inventory:
                violations.append(
                    f"VIOLATION: Item '{item_name}' appears in inventory but location is not {actor_id} "
                    f"(actual location: {item.location})"
                )

    return violations


def run_test_scenarios(game_dir: Path) -> Dict[str, List[str]]:
    """
    Run validation on several test scenarios.

    Returns dict mapping scenario name to list of violations.
    """
    engine = GameEngine(game_dir)
    results = {}

    # Scenario 1: Player in Tower Entrance (initial state)
    player = engine.game_state.actors['player']
    player.location = 'loc_entrance'
    context = engine.build_parser_context('player')
    results['Tower Entrance (initial)'] = validate_parser_context(
        context, engine.game_state, 'player'
    )

    # Scenario 2: Player in Library
    player.location = 'loc_library'
    context = engine.build_parser_context('player')
    results['Library'] = validate_parser_context(
        context, engine.game_state, 'player'
    )

    # Scenario 3: Create a closed container with items and verify contents are hidden
    # (Would need to modify game state - skip for now)

    return results


if __name__ == '__main__':
    import sys

    game_dir = Path('examples/spatial_game')
    if len(sys.argv) > 1:
        game_dir = Path(sys.argv[1])

    print(f"Validating parser context for: {game_dir}")
    print("=" * 60)

    results = run_test_scenarios(game_dir)

    total_violations = 0
    for scenario, violations in results.items():
        print(f"\n{scenario}:")
        if violations:
            print(f"  ❌ {len(violations)} violation(s):")
            for v in violations:
                print(f"    - {v}")
            total_violations += len(violations)
        else:
            print("  ✓ No violations")

    print("\n" + "=" * 60)
    if total_violations == 0:
        print("✓ All scenarios passed validation")
        sys.exit(0)
    else:
        print(f"❌ {total_violations} total violations found")
        sys.exit(1)
