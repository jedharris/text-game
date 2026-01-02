# Exit and Connection Index - Implementation Plan

**Design Document**: [Entity Whereabouts and Connections](entity_whereabouts_index.md)

**GitHub Issue**: [#350](https://github.com/jedharris/text-game/issues/350)

**Prerequisites**: Phase 1-2 (Containment Index) completed ✅

## Overview

This document provides detailed implementation steps for Phases 3-7 of the exit migration, transforming exits from embedded `ExitDescriptor` objects into first-class entities with a connection index. This is a **high-risk migration** requiring extremely thorough testing at each phase.

## Branch Strategy

**IMPORTANT**: All work for Phases 3-7 will be done on a separate branch:

```bash
git checkout -b feature/exit-entity-migration
```

This allows:
- Iterative development without blocking main branch
- Easy rollback if major issues discovered
- Comprehensive testing before merge
- Ability to defer or redesign if needed

**Merge criteria**: ALL success criteria must be met before merging to main.

## Testing Strategy

### Test Pyramid

Each phase must pass ALL levels of testing before proceeding:

**Level 1: Unit Tests**
- New functionality has comprehensive unit tests
- All existing tests continue to pass
- Code coverage ≥80% for new code

**Level 2: Integration Tests**
- Exit traversal works end-to-end
- Door interactions work from both sides
- Parser context includes exits correctly
- Narration includes exits correctly

**Level 3: Walkthrough Tests**
- Automated walkthrough for basic exit scenarios
- Automated walkthrough for door/passage scenarios
- All walkthroughs achieve 100% expected results

**Level 4: Manual Testing**
- Play through all regions of big_game
- Test edge cases (locked doors, one-way passages, hidden exits)
- Verify narration quality
- Check for performance regressions

**Level 5: Type Safety**
- Mypy clean (0 errors)
- No type:ignore comments without justification

### Validation Requirements

Each phase must implement and pass validation checks:

**Load-time validation** (fail fast):
- Symmetric connection check: if A→B then B→A
- Exit connections reference existing entities
- Door locations are doorways
- Doorway connections reference existing exits
- No orphaned exits (exit without paired exit)
- Direction mapping correctness (north↔south, etc.)

**Migration validation**:
- Deterministic ID generation (run twice, diff outputs = identical)
- All original exits have corresponding Exit entities
- All doors have corresponding doorways
- Passage entities created where specified
- No data loss (all properties preserved)

**Regression validation**:
- All previously accessible locations still accessible
- All door interactions still work
- No new unreachable content
- Parser still resolves commands correctly

## Phase 3: Create Exit Entity Type

**Goal**: Add Exit entity type without breaking existing exit system.

**Estimated Effort**: 2-3 hours (Claude time)

### Implementation Steps

#### 3.1: Define Exit Class

Create new Exit class in [src/state_manager.py](../src/state_manager.py):

```python
@dataclass
class Exit:
    """An exit entity that connects locations.

    Exits are first-class entities with dual participation:
    - Containment space: .location indicates where the exit is accessed from
    - Connection space: .connections indicates what this exit links to
    """
    id: str
    name: str
    location: str  # LocationId where this exit is accessed from
    connections: List[str]  # Entity IDs this exit connects to (usually one paired exit)
    direction: Optional[str] = None  # Optional: "north", "south", etc.
    description: str = ""
    adjectives: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: List[str] = field(default_factory=list)
    traits: Dict[str, Any] = field(default_factory=dict)
```

**Design notes**:
- Exit has `.location` (participates in containment)
- Exit has `.connections` (participates in connection space)
- Direction is optional (supports portals, hidden exits)
- Synonyms support flexible matching ("opening", "passage")

#### 3.2: Add exits List to GameState

Update GameState:

```python
@dataclass
class GameState:
    # ... existing fields ...
    exits: List[Exit] = field(default_factory=list)
```

#### 3.3: Update State Loading

Update `load_game_state()` to parse exits:

```python
# In load_game_state()
exits = []
for exit_data in data.get('exits', []):
    exit_entity = Exit(
        id=exit_data['id'],
        name=exit_data['name'],
        location=exit_data['location'],
        connections=exit_data.get('connections', []),
        direction=exit_data.get('direction'),
        description=exit_data.get('description', ''),
        adjectives=exit_data.get('adjectives', []),
        synonyms=exit_data.get('synonyms', []),
        properties=exit_data.get('properties', {}),
        behaviors=exit_data.get('behaviors', []),
        traits=exit_data.get('traits', {})
    )
    exits.append(exit_entity)

game_state.exits = exits
```

#### 3.4: Update Index Building

Update `_build_whereabouts_index()` to include exits:

```python
# Add to _build_whereabouts_index() after indexing actors
# Index all exits
for exit_entity in game_state.exits:
    if hasattr(exit_entity, 'location') and exit_entity.location:
        if exit_entity.location not in game_state._entities_at:
            game_state._entities_at[exit_entity.location] = set()
        game_state._entities_at[exit_entity.location].add(exit_entity.id)
        game_state._entity_where[exit_entity.id] = exit_entity.location
```

#### 3.5: Add get_exit() Accessor

Add to GameState:

```python
def get_exit(self, exit_id: str) -> Exit:
    """Get exit by ID. Raises KeyError if not found (fail-fast pattern)."""
    exit_entity = next((e for e in self.exits if e.id == exit_id), None)
    if exit_entity is None:
        raise KeyError(f"Exit not found: {exit_id}")
    return exit_entity
```

### Testing Phase 3

#### Unit Tests (tests/test_exit_entity.py)

Create comprehensive test suite:

```python
class TestExitEntity(unittest.TestCase):
    """Tests for Exit entity type and containment index integration."""

    def test_exit_creation(self):
        """Test Exit entity can be created with all fields."""

    def test_exit_in_containment_index(self):
        """Test exits are indexed in _entities_at."""

    def test_get_entities_at_includes_exits(self):
        """Test get_entities_at can filter by entity_type='exit'."""

    def test_get_exit_by_id(self):
        """Test get_exit() returns correct exit."""

    def test_get_exit_not_found_raises_keyerror(self):
        """Test get_exit() fails fast for missing exit."""

    def test_exit_with_connections(self):
        """Test exit can have connections list."""

    def test_exit_without_direction(self):
        """Test exit works without direction (portal case)."""
```

**Acceptance criteria**:
- All new tests pass
- All existing 109 tests still pass
- Mypy clean
- Code coverage ≥80% on new Exit class

### Deliverables Phase 3

- [ ] Exit class defined with all fields
- [ ] GameState.exits list added
- [ ] State loading parses Exit entities
- [ ] Index building includes exits
- [ ] get_exit() accessor implemented
- [ ] Comprehensive unit tests (≥8 tests)
- [ ] All tests passing (new + existing)
- [ ] Mypy clean
- [ ] Code review complete

**Exit criteria**: Ready to proceed when all deliverables checked and validated.

---

## Phase 4: JSON Format Migration Tool

**Goal**: Create robust, deterministic tool to migrate game_state.json files from embedded ExitDescriptor to Exit entities.

**Estimated Effort**: 4-6 hours (Claude time)

### Implementation Steps

#### 4.1: Create Migration Tool Structure

Create [tools/migrate_exits.py](../tools/migrate_exits.py):

```python
"""Migrate game_state.json from embedded ExitDescriptor to Exit entities.

This tool:
1. Reads game_state.json with Location.exits dicts
2. Generates paired Exit entities for each direction
3. Creates Doorway entities for doors
4. Creates Passage entities where specified
5. Validates symmetric connections
6. Writes updated game_state.json

Usage:
    python tools/migrate_exits.py examples/big_game/game_state.json [--dry-run] [--output OUTPUT]
"""

import json
import argparse
from typing import Dict, List, Any, Set, Tuple
from pathlib import Path
```

#### 4.2: Direction Mapping

```python
# Bidirectional direction mappings
OPPOSITE_DIRECTIONS: Dict[str, str] = {
    'north': 'south',
    'south': 'north',
    'east': 'west',
    'west': 'east',
    'up': 'down',
    'down': 'up',
    'northeast': 'southwest',
    'southwest': 'northeast',
    'northwest': 'southeast',
    'southeast': 'northwest',
    'in': 'out',
    'out': 'in',
}

def get_opposite_direction(direction: str) -> str:
    """Get opposite direction. Raises ValueError if direction unknown."""
    if direction not in OPPOSITE_DIRECTIONS:
        raise ValueError(f"Unknown direction: {direction}")
    return OPPOSITE_DIRECTIONS[direction]
```

#### 4.3: Exit ID Generation (Deterministic)

```python
def generate_exit_id(location_id: str, direction: str) -> str:
    """Generate deterministic exit ID.

    Convention: exit_{location_id}_{direction}

    Examples:
        - generate_exit_id("loc_forest", "north") -> "exit_forest_north"
        - generate_exit_id("loc_cave", "south") -> "exit_cave_south"
    """
    # Strip "loc_" prefix if present for readability
    loc_part = location_id.replace('loc_', '', 1) if location_id.startswith('loc_') else location_id
    return f"exit_{loc_part}_{direction}"

def generate_doorway_id(exit_a_id: str, exit_b_id: str) -> str:
    """Generate deterministic doorway ID from two exit IDs.

    Uses sorted order to ensure same ID regardless of which exit processed first.
    """
    sorted_ids = sorted([exit_a_id, exit_b_id])
    # Create readable ID from the two exits
    return f"doorway_{sorted_ids[0]}_{sorted_ids[1]}"

def generate_passage_id(location_id: str, direction: str, passage_type: str) -> str:
    """Generate deterministic passage ID.

    Args:
        location_id: Source location
        direction: Direction of travel
        passage_type: Type of passage (stairs, tunnel, bridge, etc.)
    """
    loc_part = location_id.replace('loc_', '', 1) if location_id.startswith('loc_') else location_id
    return f"passage_{loc_part}_{direction}_{passage_type}"
```

#### 4.4: Exit Migration Logic

```python
def migrate_location_exits(
    location_id: str,
    exits_dict: Dict[str, Any],
    all_exits: List[Dict[str, Any]],
    created_exit_ids: Set[str]
) -> None:
    """Migrate exits from one location's exits dict to Exit entities.

    Creates paired exits automatically (both directions).

    Args:
        location_id: ID of location being processed
        exits_dict: Location.exits dictionary
        all_exits: Accumulated list of exit entities (modified in place)
        created_exit_ids: Set tracking which exit IDs already created (modified in place)
    """
    for direction, exit_desc in exits_dict.items():
        # Generate exit ID for this direction
        exit_id = generate_exit_id(location_id, direction)

        # Skip if already created (paired exit from opposite direction)
        if exit_id in created_exit_ids:
            continue

        destination_id = exit_desc['destination']

        # Generate paired exit ID
        opposite_dir = get_opposite_direction(direction)
        paired_exit_id = generate_exit_id(destination_id, opposite_dir)

        # Create this exit
        this_exit = {
            'id': exit_id,
            'name': exit_desc.get('name', direction),
            'location': location_id,
            'connections': [paired_exit_id],
            'direction': direction,
            'description': exit_desc.get('description', ''),
            'adjectives': exit_desc.get('adjectives', []),
            'synonyms': exit_desc.get('synonyms', []),
            'properties': exit_desc.get('properties', {}),
            'behaviors': exit_desc.get('behaviors', []),
            'traits': exit_desc.get('traits', {})
        }

        # Create paired exit (symmetric defaults, can be customized later)
        paired_exit = {
            'id': paired_exit_id,
            'name': exit_desc.get('paired_name', opposite_dir),  # Allow override
            'location': destination_id,
            'connections': [exit_id],
            'direction': opposite_dir,
            'description': exit_desc.get('paired_description', ''),  # Usually empty for auto-generated
            'adjectives': exit_desc.get('paired_adjectives', []),
            'synonyms': exit_desc.get('paired_synonyms', []),
            'properties': exit_desc.get('paired_properties', {}),
            'behaviors': exit_desc.get('paired_behaviors', []),
            'traits': exit_desc.get('paired_traits', {})
        }

        all_exits.append(this_exit)
        all_exits.append(paired_exit)
        created_exit_ids.add(exit_id)
        created_exit_ids.add(paired_exit_id)
```

#### 4.5: Door and Doorway Migration

```python
def migrate_doors(
    game_state: Dict[str, Any],
    all_exits: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Migrate doors to doorway-based system.

    Finds all items with type="door", creates doorways, updates door locations.

    Returns:
        Tuple of (doorways_list, updated_items_list)
    """
    doorways = []
    items = game_state.get('items', [])

    # Find all doors
    for item in items:
        if item.get('type') != 'door':
            continue

        # Old door format: has 'exit' property with synthetic ID like "exit:loc_library:up"
        exit_ref = item.get('properties', {}).get('exit')
        if not exit_ref:
            # Skip doors without exit reference (might be decorative)
            continue

        # Parse old exit reference: "exit:loc_library:up"
        if exit_ref.startswith('exit:'):
            parts = exit_ref.split(':')
            if len(parts) == 3:
                _, old_location_id, old_direction = parts

                # Find the two exits this door connects
                exit_a_id = generate_exit_id(old_location_id, old_direction)

                # Find paired exit (need to look it up)
                exit_a = next((e for e in all_exits if e['id'] == exit_a_id), None)
                if not exit_a or not exit_a['connections']:
                    print(f"Warning: Could not find paired exit for door {item['id']}")
                    continue

                exit_b_id = exit_a['connections'][0]

                # Generate doorway ID
                doorway_id = generate_doorway_id(exit_a_id, exit_b_id)

                # Create doorway if not exists
                if not any(d['id'] == doorway_id for d in doorways):
                    doorway = {
                        'id': doorway_id,
                        'connections': [exit_a_id, exit_b_id],
                        'type': 'doorway'
                    }
                    doorways.append(doorway)

                    # Update exits to connect to doorway
                    for exit_entity in all_exits:
                        if exit_entity['id'] in [exit_a_id, exit_b_id]:
                            # Add doorway to connections (in addition to paired exit)
                            if doorway_id not in exit_entity['connections']:
                                exit_entity['connections'].append(doorway_id)

                # Update door's location to doorway
                item['location'] = doorway_id

                # Remove old 'exit' property
                if 'exit' in item.get('properties', {}):
                    del item['properties']['exit']

    return doorways, items
```

#### 4.6: Validation

```python
def validate_migration(game_state: Dict[str, Any]) -> List[str]:
    """Validate migrated game state.

    Returns list of error messages (empty if valid).
    """
    errors = []

    exits = game_state.get('exits', [])
    doorways = game_state.get('doorways', [])
    items = game_state.get('items', [])
    locations = game_state.get('locations', [])

    # Build entity ID sets
    exit_ids = {e['id'] for e in exits}
    doorway_ids = {d['id'] for d in doorways}
    location_ids = {loc['id'] for loc in locations}
    all_entity_ids = exit_ids | doorway_ids | location_ids

    # Validate: All exit connections reference existing entities
    for exit_entity in exits:
        for conn_id in exit_entity.get('connections', []):
            if conn_id not in all_entity_ids:
                errors.append(f"Exit {exit_entity['id']} references non-existent entity: {conn_id}")

    # Validate: Symmetric connections
    connection_map: Dict[str, Set[str]] = {}
    for exit_entity in exits:
        exit_id = exit_entity['id']
        connection_map[exit_id] = set(exit_entity.get('connections', []))

    for doorway in doorways:
        doorway_id = doorway['id']
        connection_map[doorway_id] = set(doorway.get('connections', []))

    for entity_a, connected_to in connection_map.items():
        for entity_b in connected_to:
            if entity_b not in connection_map:
                errors.append(f"Connection {entity_a} → {entity_b} but {entity_b} doesn't exist")
            elif entity_a not in connection_map[entity_b]:
                errors.append(f"Asymmetric connection: {entity_a} → {entity_b} but not {entity_b} → {entity_a}")

    # Validate: Exit locations are valid locations
    for exit_entity in exits:
        loc = exit_entity.get('location')
        if loc not in location_ids:
            errors.append(f"Exit {exit_entity['id']} has invalid location: {loc}")

    # Validate: Doors have doorway locations
    for item in items:
        if item.get('type') == 'door':
            loc = item.get('location')
            if loc and not loc.startswith('doorway_'):
                errors.append(f"Door {item['id']} location is not a doorway: {loc}")
            if loc and loc not in doorway_ids and not loc.startswith('__'):
                errors.append(f"Door {item['id']} references non-existent doorway: {loc}")

    # Validate: No orphaned exits (exit without paired connection)
    for exit_entity in exits:
        connections = exit_entity.get('connections', [])
        if not connections:
            errors.append(f"Orphaned exit (no connections): {exit_entity['id']}")
        # Check paired exit exists
        paired_exits = [c for c in connections if c in exit_ids]
        if not paired_exits:
            errors.append(f"Exit {exit_entity['id']} has no paired exit connection")

    return errors
```

#### 4.7: Main Migration Function

```python
def migrate_game_state(input_path: Path, output_path: Path, dry_run: bool = False) -> None:
    """Migrate game_state.json from old to new format.

    Args:
        input_path: Path to original game_state.json
        output_path: Path to write migrated game_state.json
        dry_run: If True, validate but don't write output
    """
    print(f"Loading {input_path}...")
    with open(input_path, 'r') as f:
        game_state = json.load(f)

    # Collect all exits
    all_exits: List[Dict[str, Any]] = []
    created_exit_ids: Set[str] = set()

    print("Migrating exits from locations...")
    for location in game_state.get('locations', []):
        location_id = location['id']
        exits_dict = location.get('exits', {})

        if exits_dict:
            migrate_location_exits(location_id, exits_dict, all_exits, created_exit_ids)
            # Remove old exits dict from location
            del location['exits']

    # Add exits to game state
    game_state['exits'] = sorted(all_exits, key=lambda e: e['id'])

    print(f"Created {len(all_exits)} exit entities")

    # Migrate doors
    print("Migrating doors and doorways...")
    doorways, updated_items = migrate_doors(game_state, all_exits)
    game_state['doorways'] = sorted(doorways, key=lambda d: d['id'])
    game_state['items'] = updated_items

    print(f"Created {len(doorways)} doorway entities")

    # Validate
    print("Validating migrated state...")
    errors = validate_migration(game_state)

    if errors:
        print(f"\n❌ Validation failed with {len(errors)} errors:")
        for error in errors:
            print(f"  - {error}")
        return

    print("✅ Validation passed")

    if dry_run:
        print("\n[DRY RUN] Would write to:", output_path)
        print(f"  - {len(game_state['exits'])} exits")
        print(f"  - {len(game_state['doorways'])} doorways")
        return

    # Write output
    print(f"\nWriting {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(game_state, f, indent=2)

    print("✅ Migration complete")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Migrate game_state.json to exit entity format')
    parser.add_argument('input', type=Path, help='Input game_state.json')
    parser.add_argument('--output', type=Path, help='Output path (default: input path with .migrated suffix)')
    parser.add_argument('--dry-run', action='store_true', help='Validate but do not write output')

    args = parser.parse_args()

    output_path = args.output or args.input.with_suffix('.migrated.json')
    migrate_game_state(args.input, output_path, args.dry_run)
```

### Testing Phase 4

#### Unit Tests (tests/test_migrate_exits.py)

```python
class TestExitMigration(unittest.TestCase):
    """Tests for exit migration tool."""

    def test_direction_mapping_complete(self):
        """Test all directions have opposites."""

    def test_generate_exit_id_deterministic(self):
        """Test exit ID generation is deterministic."""

    def test_generate_doorway_id_order_independent(self):
        """Test doorway ID same regardless of exit order."""

    def test_migrate_simple_exit(self):
        """Test migrating a simple bidirectional exit."""

    def test_migrate_door(self):
        """Test door migration creates doorway."""

    def test_validation_catches_asymmetric_connections(self):
        """Test validation detects asymmetric connections."""

    def test_validation_catches_orphaned_exits(self):
        """Test validation detects exits without pairs."""

    def test_migration_deterministic(self):
        """Test running migration twice produces identical output."""
```

#### Integration Test: Migrate Test Game

Create minimal test game state in [tests/fixtures/test_game_old_format.json](../tests/fixtures/test_game_old_format.json):

```json
{
  "metadata": {
    "title": "Test Game",
    "version": "1.0",
    "start_location": "loc_room_a"
  },
  "locations": [
    {
      "id": "loc_room_a",
      "name": "Room A",
      "description": "First room",
      "exits": {
        "north": {
          "destination": "loc_room_b",
          "name": "doorway",
          "description": "A wooden door"
        }
      }
    },
    {
      "id": "loc_room_b",
      "name": "Room B",
      "description": "Second room",
      "exits": {
        "south": {
          "destination": "loc_room_a"
        }
      }
    }
  ],
  "items": [],
  "actors": {
    "player": {
      "id": "player",
      "name": "Player",
      "location": "loc_room_a",
      "inventory": []
    }
  }
}
```

Test:
```bash
python tools/migrate_exits.py tests/fixtures/test_game_old_format.json --dry-run
```

Should produce validation success with 2 exits.

#### Integration Test: Migrate big_game

**CRITICAL**: Backup before migration:

```bash
cp examples/big_game/game_state.json examples/big_game/game_state.json.backup
```

Run migration:
```bash
python tools/migrate_exits.py examples/big_game/game_state.json --output examples/big_game/game_state.json.new --dry-run
```

Validation checks:
- [ ] No validation errors
- [ ] Exit count = 2 × (number of old exits)
- [ ] Doorway count = number of old doors
- [ ] All locations still have same connectivity

#### Determinism Test

Run twice and diff:
```bash
python tools/migrate_exits.py tests/fixtures/test_game_old_format.json --output /tmp/migration1.json
python tools/migrate_exits.py tests/fixtures/test_game_old_format.json --output /tmp/migration2.json
diff /tmp/migration1.json /tmp/migration2.json
```

Should show no differences.

### Deliverables Phase 4

- [ ] Migration tool created with all functions
- [ ] Direction mapping complete and bidirectional
- [ ] Deterministic ID generation
- [ ] Exit pair creation logic
- [ ] Door/doorway migration logic
- [ ] Comprehensive validation
- [ ] Unit tests for migration functions
- [ ] Integration test with test game passes
- [ ] Determinism test passes
- [ ] big_game migration validates successfully (dry-run)
- [ ] Migration tool documentation
- [ ] Code review complete

**Exit criteria**: Migration tool validated on test data, ready to migrate big_game.

---

## Phase 5: Add Connection Index

**Goal**: Implement connection index infrastructure for exits and doorways.

**Estimated Effort**: 2-3 hours (Claude time)

### Implementation Steps

#### 5.1: Add Connection Index to GameState

```python
@dataclass
class GameState:
    # ... existing fields ...

    # Symmetric connection index (exits, doorways, passages)
    _connected_to: Dict[str, Set[str]] = field(default_factory=dict)
```

#### 5.2: Build Connection Index at Load Time

Create `_build_connection_index()` function:

```python
def _build_connection_index(game_state: GameState) -> None:
    """Build symmetric connection index from entity .connections lists.

    Validates symmetry: if A connects to B, B must connect to A.
    """
    game_state._connected_to.clear()

    # Collect all entities with connections
    connected_entities: List[Any] = []
    connected_entities.extend(game_state.exits)
    connected_entities.extend(game_state.get('doorways', []))  # May not exist yet
    connected_entities.extend(game_state.get('passages', []))  # Future

    # Build index from .connections lists
    for entity in connected_entities:
        if not hasattr(entity, 'connections'):
            continue

        entity_id = entity.id if hasattr(entity, 'id') else entity['id']
        connections = entity.connections if hasattr(entity, 'connections') else entity.get('connections', [])

        if entity_id not in game_state._connected_to:
            game_state._connected_to[entity_id] = set()

        for connected_id in connections:
            game_state._connected_to[entity_id].add(connected_id)

    # Validate symmetry
    errors = []
    for entity_a, connected_to in game_state._connected_to.items():
        for entity_b in connected_to:
            if entity_b not in game_state._connected_to:
                errors.append(f"Connection {entity_a} → {entity_b} but {entity_b} has no connections")
            elif entity_a not in game_state._connected_to[entity_b]:
                errors.append(f"Asymmetric connection: {entity_a} → {entity_b} but not {entity_b} → {entity_a}")

    if errors:
        raise ValueError(f"Connection symmetry violations:\n" + "\n".join(errors))
```

Call from `load_game_state()`:
```python
# After _build_whereabouts_index()
_build_connection_index(game_state)
```

#### 5.3: Connection Query and Mutation Methods

Add to StateAccessor:

```python
def get_connected(self, entity_id: str) -> Set[str]:
    """Get all entities connected to this one.

    Args:
        entity_id: ID of exit, doorway, or passage

    Returns:
        Set of connected entity IDs (empty set if none)
    """
    return self.game_state._connected_to.get(entity_id, set()).copy()

def add_connection(self, entity_a: str, entity_b: str) -> None:
    """Connect two entities. Symmetric - adds both directions.

    Args:
        entity_a: First entity ID
        entity_b: Second entity ID

    Raises:
        ValueError: If either entity doesn't exist or doesn't support connections
    """
    # Validate both entities exist and support connections
    # (exits, doorways, passages have .connections)
    entity_a_obj = self._get_connectable_entity(entity_a)
    entity_b_obj = self._get_connectable_entity(entity_b)

    if entity_a_obj is None:
        raise ValueError(f"Entity not found or not connectable: {entity_a}")
    if entity_b_obj is None:
        raise ValueError(f"Entity not found or not connectable: {entity_b}")

    # Update index
    if entity_a not in self.game_state._connected_to:
        self.game_state._connected_to[entity_a] = set()
    if entity_b not in self.game_state._connected_to:
        self.game_state._connected_to[entity_b] = set()

    self.game_state._connected_to[entity_a].add(entity_b)
    self.game_state._connected_to[entity_b].add(entity_a)

    # Update entity .connections lists
    if entity_b not in entity_a_obj.connections:
        entity_a_obj.connections.append(entity_b)
    if entity_a not in entity_b_obj.connections:
        entity_b_obj.connections.append(entity_a)

def remove_connection(self, entity_a: str, entity_b: str) -> None:
    """Disconnect two entities. Symmetric - removes both directions.

    Args:
        entity_a: First entity ID
        entity_b: Second entity ID
    """
    # Update index
    if entity_a in self.game_state._connected_to:
        self.game_state._connected_to[entity_a].discard(entity_b)
    if entity_b in self.game_state._connected_to:
        self.game_state._connected_to[entity_b].discard(entity_a)

    # Update entity .connections lists
    entity_a_obj = self._get_connectable_entity(entity_a)
    entity_b_obj = self._get_connectable_entity(entity_b)

    if entity_a_obj and entity_b in entity_a_obj.connections:
        entity_a_obj.connections.remove(entity_b)
    if entity_b_obj and entity_a in entity_b_obj.connections:
        entity_b_obj.connections.remove(entity_a)

def _get_connectable_entity(self, entity_id: str) -> Optional[Any]:
    """Get entity that supports connections (exit, doorway, passage).

    Returns None if not found or not connectable.
    """
    # Try exits
    exit_entity = next((e for e in self.game_state.exits if e.id == entity_id), None)
    if exit_entity:
        return exit_entity

    # Try doorways (may be dict or dataclass)
    doorways = getattr(self.game_state, 'doorways', [])
    doorway = next((d for d in doorways if d.get('id') == entity_id or getattr(d, 'id', None) == entity_id), None)
    if doorway:
        return doorway

    # Try passages (future)
    passages = getattr(self.game_state, 'passages', [])
    passage = next((p for p in passages if p.get('id') == entity_id or getattr(p, 'id', None) == entity_id), None)
    if passage:
        return passage

    return None
```

### Testing Phase 5

#### Unit Tests (tests/test_connection_index.py)

```python
class TestConnectionIndex(unittest.TestCase):
    """Tests for connection index infrastructure."""

    def test_connection_index_built_from_exits(self):
        """Test connection index built from exit .connections."""

    def test_symmetric_connections_validated(self):
        """Test asymmetric connections raise error at load time."""

    def test_get_connected(self):
        """Test get_connected returns connected entity IDs."""

    def test_add_connection_updates_index(self):
        """Test add_connection updates both directions."""

    def test_add_connection_updates_entity_lists(self):
        """Test add_connection updates .connections on entities."""

    def test_remove_connection_updates_index(self):
        """Test remove_connection removes both directions."""

    def test_add_connection_invalid_entity_raises(self):
        """Test add_connection with invalid entity raises ValueError."""

    def test_connection_index_with_doorways(self):
        """Test doorways participate in connection index."""
```

**Acceptance criteria**:
- All new tests pass
- All existing tests still pass
- Mypy clean
- Code coverage ≥80%

### Deliverables Phase 5

- [ ] _connected_to index added to GameState
- [ ] _build_connection_index() implemented with symmetry validation
- [ ] get_connected() query method
- [ ] add_connection() mutation method
- [ ] remove_connection() mutation method
- [ ] _get_connectable_entity() helper
- [ ] Comprehensive unit tests (≥8 tests)
- [ ] All tests passing
- [ ] Mypy clean
- [ ] Code review complete

**Exit criteria**: Connection index infrastructure working and tested.

---

## Phase 6: Migrate big_game and Update Traversal Logic

**Goal**: Migrate big_game to new format and update all exit-related code to use new entities and indices.

**Estimated Effort**: 6-8 hours (Claude time)

**Risk Level**: HIGH - Core gameplay changes

### Implementation Steps

#### 6.1: Backup and Migrate big_game

**CRITICAL**: Full backup before migration:

```bash
# Backup entire game directory
cp -r examples/big_game examples/big_game.backup.$(date +%Y%m%d)

# Backup just game_state.json
cp examples/big_game/game_state.json examples/big_game/game_state.json.pre-migration
```

Run migration:
```bash
python tools/migrate_exits.py examples/big_game/game_state.json
```

Validation:
```bash
# Should load without errors
python -c "from src.game_state_loader import load_game_state; load_game_state('examples/big_game')"
```

#### 6.2: Update Exit Vocabulary Generation

Update [src/vocabulary_generator.py](../src/vocabulary_generator.py):

```python
def generate_vocabulary_from_state(game_state: GameState) -> Dict[str, Any]:
    """Generate merged vocabulary from game state."""
    # ... existing code ...

    # Add exit names and synonyms to nouns
    for exit_entity in game_state.exits:
        # Exit name is a noun
        noun_entry = {
            'word': exit_entity.name,
            'synonyms': exit_entity.synonyms,
            'entity_id': exit_entity.id,
            'entity_type': 'exit'
        }
        nouns.append(noun_entry)

        # Exit adjectives
        for adj in exit_entity.adjectives:
            if not any(a['word'] == adj for a in adjectives):
                adjectives.append({'word': adj, 'synonyms': []})

        # Direction is both noun and adjective (for "go north" and "northern exit")
        if exit_entity.direction:
            # Add as noun (for "go north")
            if not any(n['word'] == exit_entity.direction for n in nouns):
                nouns.append({
                    'word': exit_entity.direction,
                    'synonyms': [],
                    'entity_id': exit_entity.id,
                    'entity_type': 'exit'
                })
```

**Note**: Directions remain in vocabulary for now. Future optimization can remove direction category entirely.

#### 6.3: Update Parser Context Building

Update [src/game_engine.py](../src/game_engine.py) `build_parser_context()`:

```python
def build_parser_context(self, actor_id: ActorId = ActorId("player")):
    """Build context dict for LLM parser from current game state."""
    # ... existing code for items and actors ...

    # Get exits from current location using index
    exits_here = accessor.get_entities_at(location_id, entity_type="exit")

    exits_list: List[Dict[str, Any]] = []
    for exit_entity in exits_here:
        exit_dict = {
            'id': exit_entity.id,
            'name': exit_entity.name,
            'description': exit_entity.description,
            'adjectives': exit_entity.adjectives
        }

        # Include direction if present
        if exit_entity.direction:
            exit_dict['direction'] = exit_entity.direction

        # Include destination for context (helps LLM understand "go to forest")
        if exit_entity.connections:
            # Get paired exit to find destination
            paired_exit_id = next((c for c in exit_entity.connections if c.startswith('exit_')), None)
            if paired_exit_id:
                try:
                    paired_exit = self.game_state.get_exit(paired_exit_id)
                    exit_dict['destination'] = paired_exit.location
                except KeyError:
                    pass

        exits_list.append(exit_dict)

    # Remove old 'exits' key (was list of direction strings)
    context['exits'] = exits_list  # Now list of exit entity dicts

    return context
```

#### 6.4: Update Exit Traversal Handler

Update [behaviors/core/exits.py](../behaviors/core/exits.py):

```python
"""Exit traversal behaviors."""

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult, StateAccessor
from src.types import ActorId, LocationId
from utilities.handler_utils import validate_actor_and_location, find_action_target
from utilities.entity_serializer import serialize_for_handler_result


def handle_go(accessor: StateAccessor, action) -> HandlerResult:
    """Handle go/move/enter commands with exit entities.

    Examples:
        go north
        enter cave
        go through the dark opening
    """
    actor_id, actor, location, error = validate_actor_and_location(
        accessor, action, require_object=True
    )
    if error:
        return error

    # Find the exit entity
    exit_entity, error = find_action_target(accessor, action)
    if error:
        return error

    # Verify it's an exit
    if not hasattr(exit_entity, 'connections'):
        return HandlerResult(
            success=False,
            primary=f"You can't go that way.",
            data={}
        )

    # Check if exit is blocked by behaviors
    block_result = accessor.behavior_manager.invoke_behavior(
        exit_entity,
        'on_before_traverse',
        accessor,
        {'actor_id': actor_id}
    )

    if block_result and not block_result.allow:
        return HandlerResult(
            success=False,
            primary=block_result.feedback or "You can't go that way.",
            data={}
        )

    # Find destination (paired exit's location)
    paired_exit_id = next((c for c in exit_entity.connections if c.startswith('exit_')), None)
    if not paired_exit_id:
        return HandlerResult(
            success=False,
            primary="That exit doesn't lead anywhere.",
            data={}
        )

    try:
        paired_exit = accessor.game_state.get_exit(paired_exit_id)
        destination_id = paired_exit.location
    except KeyError:
        return HandlerResult(
            success=False,
            primary="That exit doesn't lead anywhere.",
            data={}
        )

    # Move actor to destination
    accessor.set_entity_where(actor_id, destination_id)

    # Get destination location for serialization
    destination_location = accessor.game_state.get_location(LocationId(destination_id))

    # Trigger arrival events
    accessor.behavior_manager.invoke_behavior(
        destination_location,
        'on_actor_arrive',
        accessor,
        {'actor_id': actor_id, 'from_exit': exit_entity.id}
    )

    return HandlerResult(
        success=True,
        primary=f"You go {exit_entity.direction or exit_entity.name}.",
        data=serialize_for_handler_result(destination_location, accessor, actor_id)
    )
```

**Key changes**:
- Uses `find_action_target()` to find exit entity
- Checks `.connections` instead of old ExitDescriptor
- Uses connection index to find paired exit
- Destination comes from paired exit's `.location`

#### 6.5: Update Door Finding

Update door-related code to use connection queries:

```python
def find_door_on_exit(accessor: StateAccessor, exit_id: str) -> Optional[Item]:
    """Find door (if any) on this exit via doorway connection.

    Args:
        accessor: State accessor
        exit_id: Exit entity ID

    Returns:
        Door item if found, None otherwise
    """
    # Get connections from this exit
    connected_ids = accessor.get_connected(exit_id)

    # Look for doorway
    for connected_id in connected_ids:
        if connected_id.startswith('doorway_'):
            # Found doorway - check if it contains a door
            doors = accessor.get_entities_at(connected_id, entity_type='item')
            for door in doors:
                if door.properties.get('type') == 'door':
                    return door

    return None
```

Use in exit handler:
```python
# In handle_go(), before traversal
door = find_door_on_exit(accessor, exit_entity.id)
if door:
    # Check if door is locked
    if door.properties.get('locked', False):
        return HandlerResult(
            success=False,
            primary=f"The {door.name} is locked.",
            data={}
        )
```

#### 6.6: Update Narration

Update [utilities/location_serializer.py](../utilities/location_serializer.py):

```python
def build_location_context(location: Location, accessor: StateAccessor, actor_id: ActorId) -> Dict[str, Any]:
    """Build narration context for a location."""
    # ... existing code for items, actors ...

    # Get exits from index
    exits_here = accessor.get_entities_at(location.id, entity_type='exit')

    exit_contexts = []
    for exit_entity in exits_here:
        exit_context = {
            'name': exit_entity.name,
            'description': exit_entity.description,
            'direction': exit_entity.direction,
            'adjectives': exit_entity.adjectives,
            'traits': exit_entity.traits
        }

        # Check for door
        door = find_door_on_exit(accessor, exit_entity.id)
        if door:
            exit_context['door'] = {
                'name': door.name,
                'description': door.description,
                'locked': door.properties.get('locked', False),
                'open': door.properties.get('open', True)
            }

        exit_contexts.append(exit_context)

    context['exits'] = exit_contexts
    return context
```

### Testing Phase 6

#### Integration Tests

Create [tests/test_exit_integration.py](../tests/test_exit_integration.py):

```python
class TestExitIntegration(unittest.TestCase):
    """Integration tests for exit entities and traversal."""

    def setUp(self):
        """Load migrated big_game."""
        self.game_state = load_game_state('examples/big_game')
        self.behavior_manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_exit_entities_loaded(self):
        """Test exit entities are loaded from migrated game state."""

    def test_exit_vocabulary_generated(self):
        """Test exit names appear in vocabulary."""

    def test_parser_context_includes_exits(self):
        """Test parser context includes exit entities."""

    def test_basic_traversal(self):
        """Test going through an exit works end-to-end."""

    def test_traversal_with_direction(self):
        """Test 'go north' style commands work."""

    def test_traversal_with_name(self):
        """Test 'enter cave' style commands work."""

    def test_door_blocks_locked_exit(self):
        """Test locked door prevents traversal."""

    def test_door_accessible_from_both_sides(self):
        """Test door found from both connected exits."""

    def test_narration_includes_exits(self):
        """Test location narration includes exit descriptions."""
```

#### Walkthrough Tests

Create [walkthroughs/exit_migration_basic.txt](../walkthroughs/exit_migration_basic.txt):

```
# Basic exit traversal test

# Test direction-based navigation
look
go north
look
go south
look

# Test name-based navigation
go cave entrance
look
go forest
look

# Test exit descriptions in narration
examine northern exit
examine opening

# Expected: All commands succeed, locations change correctly
```

Create [walkthroughs/exit_migration_doors.txt](../walkthroughs/exit_migration_doors.txt):

```
# Door and doorway test

# Navigate to location with door
go library
go up

# Should be blocked if locked
unlock door with brass key
open door
go up
look

# Test from other side
go down
close door
lock door with brass key
```

Run walkthroughs:
```bash
python tools/walkthrough.py examples/big_game --file walkthroughs/exit_migration_basic.txt
python tools/walkthrough.py examples/big_game --file walkthroughs/exit_migration_doors.txt
```

**Acceptance criteria**: 100% expected results (all commands work or fail as intended).

#### Manual Testing Checklist

- [ ] Visit every location in big_game
- [ ] Traverse every exit in both directions
- [ ] Test all door interactions (open, close, lock, unlock)
- [ ] Verify narration quality (exits described appropriately)
- [ ] Test edge cases:
  - [ ] Hidden exits (if any)
  - [ ] One-way passages (if any)
  - [ ] Blocked/conditional exits
- [ ] Performance check (no noticeable slowdown)

### Deliverables Phase 6

- [ ] big_game migrated to new format (backup created)
- [ ] Exit vocabulary generation updated
- [ ] Parser context building updated
- [ ] Exit traversal handler rewritten
- [ ] Door finding updated to use connections
- [ ] Location narration updated
- [ ] Integration tests written and passing
- [ ] Walkthrough tests written and achieving 100%
- [ ] Manual testing checklist completed
- [ ] All 109 existing tests still pass
- [ ] Mypy clean
- [ ] Performance validated (no regression)
- [ ] Code review complete

**Exit criteria**: big_game fully playable with new exit system, all tests passing.

---

## Phase 7: Cleanup and Documentation

**Goal**: Remove legacy code, update documentation, finalize implementation.

**Estimated Effort**: 2-3 hours (Claude time)

### Implementation Steps

#### 7.1: Remove Legacy Fields

Remove deprecated fields from data structures:

**Location.exits dict**:
- Already removed during migration
- Verify no code references `location.exits` dict

**location.items and actor.inventory lists**:
```python
# Remove from Location dataclass
# Remove from Actor dataclass
```

Update any remaining code that referenced these lists to use index queries.

#### 7.2: Update Validators

Update game state validators to check new format:

```python
def validate_game_state(game_state: GameState) -> List[str]:
    """Validate game state structure and relationships."""
    errors = []

    # Validate exits
    for exit_entity in game_state.exits:
        # Must have location
        if not exit_entity.location:
            errors.append(f"Exit {exit_entity.id} has no location")

        # Must have connections
        if not exit_entity.connections:
            errors.append(f"Exit {exit_entity.id} has no connections")

        # Connections must reference existing entities
        for conn_id in exit_entity.connections:
            # Check if conn_id exists (exit, doorway, or passage)
            # ... validation logic ...

    # Validate symmetric connections
    # ... (already done in _build_connection_index) ...

    # Validate doorways
    for doorway in getattr(game_state, 'doorways', []):
        # Must connect to exactly two exits (initially)
        connections = doorway.get('connections', [])
        if len(connections) != 2:
            errors.append(f"Doorway {doorway['id']} must connect exactly 2 exits, has {len(connections)}")

    return errors
```

#### 7.3: Update Authoring Guide

Update [docs/authoring_guide.md](../docs/authoring_guide.md):

**Add section on Exit Entities**:
```markdown
## Exits

Exits are first-class entities that connect locations.

### Basic Exit

{
  "id": "exit_forest_north",
  "name": "cave entrance",
  "location": "loc_forest",
  "connections": ["exit_cave_south"],
  "direction": "north",
  "description": "A dark narrow opening in the hillside",
  "adjectives": ["dark", "narrow"],
  "synonyms": ["opening", "passage"]
}

### Exit Fields

- **id**: Unique identifier (convention: `exit_{location}_{direction}`)
- **name**: How the exit appears in narration ("cave entrance", "doorway", "stairs")
- **location**: Location ID where this exit is accessed from
- **connections**: List of entity IDs this connects to (usually one paired exit)
- **direction**: Optional direction ("north", "south", etc.) for "go north" commands
- **description**: Full description of the exit
- **adjectives**: Descriptive words ("dark", "narrow", "wooden")
- **synonyms**: Alternative names ("opening", "passage", "gateway")
- **properties**: Custom properties (same as items)
- **behaviors**: Behavior module list (e.g., conditional access)

### Paired Exits

Exits come in pairs - one in each connected location:

exit_forest_north (in forest) ↔ exit_cave_south (in cave)

When migrating, the tool creates pairs automatically. You can customize each direction independently.

### Doors and Doorways

A door is an item placed in a doorway that connects two exits:

exit_library_up → doorway_123 ← exit_sanctum_down
                       ↓
                  door_sanctum

The door's location is the doorway ID.

### Exit Behaviors

Exits support behaviors for conditional access:

on_before_traverse: Called before actor traverses exit (can block)
on_after_traverse: Called after successful traversal

Example: Require a key, check actor state, trigger events.
```

#### 7.4: Update Quick Reference

Update [docs/quick_reference.md](../docs/quick_reference.md):

Add to "Essential Imports":
```python
# State access
exit_entity = state.get_exit("exit_forest_north")  # Raises KeyError if missing
exits_here = accessor.get_entities_at(location_id, entity_type="exit")
connected_ids = accessor.get_connected(exit_id)
```

Add to "Common Utilities":
```python
# Finding exits
exits_here = accessor.get_entities_at(location_id, entity_type="exit")

# Traversal
accessor.set_entity_where(actor_id, destination_id)

# Connections
connected = accessor.get_connected(exit_id)
door = find_door_on_exit(accessor, exit_id)
```

#### 7.5: Update Design Document

Mark Phase 3-7 as completed in [docs/entity_whereabouts_index.md](../docs/entity_whereabouts_index.md):

```markdown
### Phase 3: Create Exit Entity Type ✅ COMPLETED
...

### Phase 7: Cleanup and Documentation ✅ COMPLETED
...

## Success Criteria

**Phase 3-7 (Exit/Connection Migration): ✅ ACHIEVED**
1. All exits traversable by direction, name, description ✅
2. Doors work correctly from both sides ✅
3. All game content migrated to new format ✅
4. Validation catches symmetric connection violations ✅
5. LLM parser matches exits as entities ✅
```

### Testing Phase 7

#### Regression Testing

Run full test suite:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

All tests must pass.

#### Walkthrough Regression

Run ALL walkthroughs:
```bash
python tools/walkthrough.py examples/big_game --file walkthroughs/frozen_reaches.txt
python tools/walkthrough.py examples/big_game --file walkthroughs/myconid_sanctuary.txt
# ... all other walkthroughs ...
```

All must achieve 100% expected results.

#### Manual Playthrough

Full playthrough of big_game:
- [ ] Start from beginning
- [ ] Visit all major regions
- [ ] Complete key quests
- [ ] Test all doors and passages
- [ ] Verify narration quality throughout

### Deliverables Phase 7

- [ ] Location.exits field removed (verify no references)
- [ ] location.items and actor.inventory lists removed
- [ ] Validators updated for new format
- [ ] Authoring guide updated with exit documentation
- [ ] Quick reference updated
- [ ] Design document marked complete
- [ ] All tests passing (unit + integration)
- [ ] All walkthroughs achieving 100%
- [ ] Manual playthrough successful
- [ ] Mypy clean
- [ ] Code review complete
- [ ] Migration guide written

**Exit criteria**: All legacy code removed, documentation complete, system fully validated.

---

## Final Validation and Merge

### Pre-Merge Checklist

Before merging feature/exit-entity-migration to main:

**Code Quality**:
- [ ] All tests passing (117+ tests)
- [ ] Mypy clean (0 errors)
- [ ] Code coverage ≥80%
- [ ] No TODO comments or debug code
- [ ] All code reviewed

**Functionality**:
- [ ] All walkthroughs achieving 100%
- [ ] Manual playthrough successful
- [ ] No known bugs
- [ ] No performance regression
- [ ] Narration quality maintained/improved

**Documentation**:
- [ ] Design document complete
- [ ] Implementation document complete
- [ ] Authoring guide updated
- [ ] Quick reference updated
- [ ] Migration tool documented

**Migration**:
- [ ] big_game successfully migrated
- [ ] Migration deterministic (verified)
- [ ] Backup created and verified
- [ ] Rollback procedure documented

### Merge Process

```bash
# On feature branch, ensure everything committed
git status  # Should be clean

# Run full test suite one final time
python -m unittest discover -s tests -p "test_*.py"
mypy src/ tests/ behaviors/

# Merge to main
git checkout main
git merge feature/exit-entity-migration

# Run tests on main
python -m unittest discover -s tests -p "test_*.py"

# Push
git push origin main
```

### Post-Merge Validation

After merge:
- [ ] Pull fresh clone, verify it works
- [ ] Run full test suite in fresh environment
- [ ] Play through big_game
- [ ] Monitor for issues over next few sessions

### Rollback Procedure

If critical issues discovered post-merge:

```bash
# Restore backup
cp examples/big_game.backup.YYYYMMDD/game_state.json examples/big_game/

# Revert commit
git revert <merge-commit-sha>

# Or hard reset if no other work done
git reset --hard HEAD~1
```

---

## Success Metrics

### Quantitative Metrics

- **Test Coverage**: ≥80% overall, 100% for new exit code
- **Test Count**: 117+ tests (17 containment + 8 exit + 8 connection + 8 migration + 76 integration)
- **Mypy Errors**: 0
- **Walkthroughs**: 100% success rate on all walkthroughs
- **Performance**: Exit traversal ≤1ms (negligible impact)
- **Migration Time**: <10 seconds for big_game

### Qualitative Metrics

- **Code Clarity**: Exit code simpler than old ExitDescriptor system
- **Narration Quality**: Exit descriptions appear naturally in narration
- **Parser Flexibility**: "go north", "enter cave", "go through opening" all work
- **Authoring Experience**: Exit entities easier to customize than embedded descriptors
- **Maintainability**: Single source of truth for connections

### User Impact

**Positive**:
- More flexible exit access (by name, description, not just direction)
- Better narration (exits described like other entities)
- Doors work consistently from both sides
- Future: magical exits, portals, complex passages

**Negative** (acceptable tradeoffs):
- Save file format change (one-time migration)
- Learning curve for exit entity format (documented)

---

## Risk Mitigation

### High-Risk Areas

**1. Migration Data Loss**
- **Mitigation**: Extensive validation, backup before migration, determinism testing
- **Rollback**: Restore from backup

**2. Traversal Breaking**
- **Mitigation**: Comprehensive walkthroughs, manual testing, integration tests
- **Rollback**: Feature branch allows safe development

**3. Performance Regression**
- **Mitigation**: Index queries are O(1), benchmark before/after
- **Rollback**: Revert if performance unacceptable

**4. Narration Quality Degradation**
- **Mitigation**: Manual review, side-by-side comparison
- **Rollback**: Adjust templates if needed

### Contingency Plans

**If Phase 3 fails**: Exit entities are additive, can remove without impact

**If Phase 4 migration fails**: Validate extensively in dry-run, iterate until perfect

**If Phase 5 fails**: Connection index is independent, can defer

**If Phase 6 fails**: This is critical - extensive testing required. Branch allows safe iteration.

**If Phase 7 cleanup causes issues**: Minimal risk, mostly documentation

---

## Timeline Estimates

**Claude Coding Time** (TDD, testing, debugging):
- Phase 3: 2-3 hours
- Phase 4: 4-6 hours
- Phase 5: 2-3 hours
- Phase 6: 6-8 hours
- Phase 7: 2-3 hours
- **Total: 16-23 hours Claude time**

**User Review Time** (approvals, feedback):
- Design review: 30 mins
- Per-phase review: 15 mins × 5 = 75 mins
- Final review: 30 mins
- **Total: ~2.5 hours user time**

**Total Elapsed**: Depends on iteration cycles, estimated 3-5 days if working continuously.

---

## Open Questions

Questions to resolve during implementation:

1. **Passage entity structure**: Should passages be dataclass or dict? (Recommend dataclass for consistency)

2. **Direction vocabulary category**: Keep or migrate to exit synonyms? (Recommend keep for now, migrate later)

3. **Exit naming convention**: Enforce `exit_{loc}_{dir}` or allow arbitrary? (Recommend enforce for consistency)

4. **Doorway mutability**: Allow gameplay to add/remove doors from doorways? (Recommend defer to future phase)

5. **Multi-destination portals**: Support now or defer? (Recommend defer - structure supports it but not needed yet)

---

## Appendix A: Test Data

### Minimal Test Game

For quick iteration testing, create [tests/fixtures/minimal_exit_game.json](../tests/fixtures/minimal_exit_game.json):

```json
{
  "metadata": {
    "title": "Minimal Exit Test",
    "version": "1.0",
    "start_location": "loc_a"
  },
  "locations": [
    {
      "id": "loc_a",
      "name": "Room A",
      "description": "A simple room"
    },
    {
      "id": "loc_b",
      "name": "Room B",
      "description": "Another room"
    }
  ],
  "exits": [
    {
      "id": "exit_a_north",
      "name": "doorway",
      "location": "loc_a",
      "connections": ["exit_b_south"],
      "direction": "north",
      "description": "A simple doorway"
    },
    {
      "id": "exit_b_south",
      "name": "doorway",
      "location": "loc_b",
      "connections": ["exit_a_north"],
      "direction": "south",
      "description": "A simple doorway"
    }
  ],
  "items": [],
  "actors": {
    "player": {
      "id": "player",
      "name": "Player",
      "location": "loc_a",
      "inventory": []
    }
  }
}
```

Use for rapid testing of exit traversal without loading full big_game.

---

## Appendix B: Migration Tool Usage Examples

### Basic Usage

```bash
# Dry run (validate only)
python tools/migrate_exits.py examples/big_game/game_state.json --dry-run

# Migrate (creates .migrated.json)
python tools/migrate_exits.py examples/big_game/game_state.json

# Migrate with custom output
python tools/migrate_exits.py examples/big_game/game_state.json --output examples/big_game/game_state_new.json

# Replace original (after backup!)
python tools/migrate_exits.py examples/big_game/game_state.json --output examples/big_game/game_state.json
```

### Batch Migration

```bash
# Migrate all game states
for game_state in examples/*/game_state.json; do
    echo "Migrating $game_state..."
    python tools/migrate_exits.py "$game_state" --dry-run
done
```

---

## Appendix C: Debugging Checklist

If exit traversal fails after migration:

**1. Check exit entities loaded**:
```python
print(f"Loaded {len(game_state.exits)} exits")
for exit in game_state.exits[:5]:
    print(f"  {exit.id}: {exit.location} → {exit.connections}")
```

**2. Check containment index**:
```python
location_id = "loc_forest"
entities = accessor.get_entities_at(location_id, entity_type="exit")
print(f"Exits at {location_id}: {[e.id for e in entities]}")
```

**3. Check connection index**:
```python
exit_id = "exit_forest_north"
connected = accessor.get_connected(exit_id)
print(f"{exit_id} connects to: {connected}")
```

**4. Check parser context**:
```python
context = game_engine.build_parser_context()
print(f"Parser sees {len(context['exits'])} exits")
for exit_dict in context['exits']:
    print(f"  {exit_dict}")
```

**5. Check vocabulary**:
```python
vocab = generate_vocabulary_from_state(game_state)
exit_nouns = [n for n in vocab['nouns'] if n.get('entity_type') == 'exit']
print(f"Exit vocabulary: {len(exit_nouns)} entries")
```

**6. Enable debug logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Summary

This implementation plan provides:

✅ **Comprehensive phasing**: 5 distinct phases with clear deliverables
✅ **Extensive testing**: Unit, integration, walkthrough, and manual testing at each phase
✅ **Risk mitigation**: Branch strategy, backups, rollback procedures
✅ **Validation**: Load-time validation, migration validation, regression validation
✅ **Documentation**: Updated guides, quick reference, design doc
✅ **Deterministic migration**: Repeatable, verifiable transformation
✅ **Quality gates**: No phase proceeds until all deliverables met

**Estimated effort**: 16-23 hours Claude coding time over 3-5 days elapsed time.

**Risk assessment**: HIGH but well-mitigated through testing and phasing.

**Expected outcome**: Unified entity model with exits as first-class entities, flexible LLM-driven access, and clean door/passage support.
