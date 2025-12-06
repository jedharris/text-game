# Spatial Structure Implementation and Testing Plan v2

## Overview

This document provides a comprehensive, detailed implementation and testing plan for the spatial structure system described in [spatial_structure.md](spatial_structure.md). This plan supersedes the preliminary sketch in `spatial_implementation_v1.md` with a more thorough, test-driven approach that follows the project's coding guidelines.

**Key Principles:**
- Every phase follows TDD (Test-Driven Development)
- Each phase has clear deliverables with passing tests before proceeding
- Changes are broken into small, manageable increments
- All vocabulary uses WordEntry, never hardcoded strings
- Progress, issues, and deferred work are tracked throughout

---

## Phase 1: Core Part Entity Infrastructure

**Duration:** 3-4 days
**Goal:** Part entity type exists and integrates with core game state systems

### 1.1 Add Part Dataclass to state_manager.py

**File:** `src/state_manager.py`

**Implementation:**
```python
@dataclass
class Part:
    """A spatial component of another entity (room, item, container, actor)."""
    id: str
    name: str
    part_of: str  # Parent entity ID
    properties: Dict[str, Any] = field(default_factory=dict)
    behaviors: List[str] = field(default_factory=list)

    @property
    def states(self) -> Dict[str, Any]:
        """Access states dict within properties."""
        if "states" not in self.properties:
            self.properties["states"] = {}
        return self.properties["states"]

    @states.setter
    def states(self, value: Dict[str, Any]) -> None:
        """Set states dict within properties."""
        self.properties["states"] = value

    @property
    def llm_context(self) -> Optional[Dict[str, Any]]:
        """Access llm_context from properties."""
        return self.properties.get("llm_context")

    @llm_context.setter
    def llm_context(self, value: Optional[Dict[str, Any]]) -> None:
        """Set llm_context in properties."""
        self.properties["llm_context"] = value
```

**Tests to Write First:**
```python
# tests/test_part_entity.py

class TestPartEntity(unittest.TestCase):
    def test_part_creation(self):
        """Test basic Part entity creation."""
        part = Part(
            id="part_throne_north_wall",
            name="north wall",
            part_of="loc_throne_room",
            properties={"material": "stone"},
            behaviors=[]
        )

        self.assertEqual(part.id, "part_throne_north_wall")
        self.assertEqual(part.name, "north wall")
        self.assertEqual(part.part_of, "loc_throne_room")
        self.assertEqual(part.properties["material"], "stone")

    def test_part_states_property(self):
        """Test Part states property access."""
        part = Part(id="part_1", name="test", part_of="loc_1")

        # States auto-initializes
        self.assertEqual(part.states, {})

        # Can set states
        part.states["damaged"] = True
        self.assertTrue(part.states["damaged"])

    def test_part_llm_context_property(self):
        """Test Part llm_context property access."""
        part = Part(id="part_1", name="test", part_of="loc_1")

        # Initially None
        self.assertIsNone(part.llm_context)

        # Can set llm_context
        part.llm_context = {"traits": ["stone", "damp"]}
        self.assertEqual(part.llm_context["traits"], ["stone", "damp"])
```

### 1.2 Add Parts Collection to GameState

**File:** `src/state_manager.py`

**Implementation:**
```python
@dataclass
class GameState:
    """Complete game state."""
    metadata: Metadata
    locations: List[Location]
    items: List[Item]
    actors: Dict[str, Actor]
    locks: List[Lock]
    parts: List[Part] = field(default_factory=list)  # New collection
    properties: Dict[str, Any] = field(default_factory=dict)
```

**Tests to Write First:**
```python
# tests/test_part_entity.py (continued)

def test_gamestate_includes_parts(self):
    """Test GameState has parts collection."""
    metadata = Metadata(title="Test", start_location="loc_1")
    game_state = GameState(
        metadata=metadata,
        locations=[],
        items=[],
        actors={},
        locks=[],
        parts=[]
    )

    self.assertIsInstance(game_state.parts, list)
    self.assertEqual(len(game_state.parts), 0)

def test_gamestate_with_parts(self):
    """Test GameState can contain Part entities."""
    metadata = Metadata(title="Test", start_location="loc_1")
    location = Location(id="loc_1", name="Room", description="A room")
    part = Part(id="part_1", name="wall", part_of="loc_1")

    game_state = GameState(
        metadata=metadata,
        locations=[location],
        items=[],
        actors={},
        locks=[],
        parts=[part]
    )

    self.assertEqual(len(game_state.parts), 1)
    self.assertEqual(game_state.parts[0].id, "part_1")
```

### 1.3 Update JSON Loading to Support Parts

**File:** `src/state_manager.py` (function `load_game_state`)

**Implementation:**
```python
# In load_game_state function, after loading locks:

# Load parts
parts = []
for part_data in data.get("parts", []):
    part = Part(
        id=part_data["id"],
        name=part_data["name"],
        part_of=part_data["part_of"],
        properties=part_data.get("properties", {}),
        behaviors=part_data.get("behaviors", [])
    )
    parts.append(part)

# Add parts to GameState constructor
game_state = GameState(
    metadata=metadata,
    locations=locations,
    items=items,
    actors=actors,
    locks=locks,
    parts=parts,  # New parameter
    properties=data.get("properties", {})
)
```

**Tests to Write First:**
```python
# tests/test_state_manager.py (add to existing tests)

def test_load_parts_from_json(self):
    """Test loading Part entities from JSON."""
    game_json = {
        "metadata": {
            "title": "Test Game",
            "start_location": "loc_room"
        },
        "locations": [
            {
                "id": "loc_room",
                "name": "Room",
                "description": "A room"
            }
        ],
        "parts": [
            {
                "id": "part_room_north_wall",
                "name": "north wall",
                "part_of": "loc_room",
                "properties": {
                    "material": "stone"
                },
                "behaviors": []
            }
        ],
        "items": [],
        "actors": {},
        "locks": []
    }

    # Write to temp file and load
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(game_json, f)
        temp_path = f.name

    try:
        game_state = load_game_state(temp_path)

        self.assertEqual(len(game_state.parts), 1)
        part = game_state.parts[0]
        self.assertEqual(part.id, "part_room_north_wall")
        self.assertEqual(part.name, "north wall")
        self.assertEqual(part.part_of, "loc_room")
        self.assertEqual(part.properties["material"], "stone")
    finally:
        os.unlink(temp_path)

def test_load_empty_parts_list(self):
    """Test loading game with no parts defined."""
    game_json = {
        "metadata": {"title": "Test", "start_location": "loc_1"},
        "locations": [{"id": "loc_1", "name": "Room", "description": "A room"}],
        "items": [],
        "actors": {},
        "locks": []
        # No parts field
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(game_json, f)
        temp_path = f.name

    try:
        game_state = load_game_state(temp_path)
        self.assertEqual(len(game_state.parts), 0)
    finally:
        os.unlink(temp_path)
```

### 1.4 Add Part Validation Rules

**File:** `src/state_manager.py` (function `validate_game_state`)

**Implementation:**
```python
# Add to validate_game_state after existing validations:

def validate_parts(state: GameState) -> List[str]:
    """Validate Part entities."""
    errors = []

    # Collect all entity IDs for uniqueness check
    all_ids = set()
    for loc in state.locations:
        all_ids.add(loc.id)
    for item in state.items:
        all_ids.add(item.id)
    for lock in state.locks:
        all_ids.add(lock.id)
    for actor_id in state.actors:
        all_ids.add(actor_id)

    # Validate each part
    for part in state.parts:
        # Check ID uniqueness
        if part.id in all_ids:
            errors.append(f"Part {part.id} has duplicate ID")
        all_ids.add(part.id)

        # Check required fields
        if not part.id:
            errors.append("Part has empty id")
        if not part.name:
            errors.append(f"Part {part.id} has empty name")
        if not part.part_of:
            errors.append(f"Part {part.id} missing required part_of field")

        # Check part_of references valid entity
        if part.part_of:
            parent = None
            for loc in state.locations:
                if loc.id == part.part_of:
                    parent = loc
                    break
            if not parent:
                for item in state.items:
                    if item.id == part.part_of:
                        parent = item
                        break
            if not parent:
                for actor_id in state.actors:
                    if actor_id == part.part_of:
                        parent = state.actors[actor_id]
                        break

            if not parent:
                errors.append(
                    f"Part {part.id} references non-existent parent {part.part_of}"
                )

        # Phase 1 constraint: parts cannot have parts (no nesting yet)
        if part.part_of.startswith("part_"):
            errors.append(
                f"Part {part.id} cannot have another part as parent "
                f"(nested parts not supported in Phase 1)"
            )

    return errors

# Add to main validate_game_state:
errors.extend(validate_parts(state))
```

**Tests to Write First:**
```python
# tests/test_validation.py (create new file or add to existing)

class TestPartValidation(unittest.TestCase):
    def test_valid_part_passes_validation(self):
        """Test that valid part passes validation."""
        location = Location(id="loc_room", name="Room", description="A room")
        part = Part(id="part_wall", name="wall", part_of="loc_room")

        metadata = Metadata(title="Test", start_location="loc_room")
        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[],
            actors={},
            locks=[],
            parts=[part]
        )

        errors = validate_game_state(game_state)
        self.assertEqual(errors, [])

    def test_part_with_invalid_parent_fails(self):
        """Test part referencing non-existent parent fails validation."""
        part = Part(id="part_wall", name="wall", part_of="loc_nonexistent")

        metadata = Metadata(title="Test", start_location="loc_room")
        location = Location(id="loc_room", name="Room", description="A room")
        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[],
            actors={},
            locks=[],
            parts=[part]
        )

        errors = validate_game_state(game_state)
        self.assertTrue(any("non-existent parent" in e for e in errors))

    def test_part_duplicate_id_fails(self):
        """Test part with duplicate ID fails validation."""
        location = Location(id="loc_room", name="Room", description="A room")
        item = Item(
            id="item_duplicate",
            name="Item",
            description="An item",
            location="loc_room"
        )
        part = Part(
            id="item_duplicate",  # Duplicate ID
            name="wall",
            part_of="loc_room"
        )

        metadata = Metadata(title="Test", start_location="loc_room")
        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[item],
            actors={},
            locks=[],
            parts=[part]
        )

        errors = validate_game_state(game_state)
        self.assertTrue(any("duplicate ID" in e for e in errors))

    def test_nested_part_fails_in_phase_1(self):
        """Test part with part as parent fails in Phase 1."""
        location = Location(id="loc_room", name="Room", description="A room")
        parent_part = Part(id="part_wall", name="wall", part_of="loc_room")
        nested_part = Part(
            id="part_wall_section",
            name="section",
            part_of="part_wall"  # Not allowed in Phase 1
        )

        metadata = Metadata(title="Test", start_location="loc_room")
        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[],
            actors={},
            locks=[],
            parts=[parent_part, nested_part]
        )

        errors = validate_game_state(game_state)
        self.assertTrue(any("nested parts not supported" in e for e in errors))

    def test_part_can_have_item_as_parent(self):
        """Test part can have item as parent (multi-sided objects)."""
        location = Location(id="loc_room", name="Room", description="A room")
        item = Item(
            id="item_bench",
            name="bench",
            description="A bench",
            location="loc_room"
        )
        part = Part(id="part_bench_left", name="left side", part_of="item_bench")

        metadata = Metadata(title="Test", start_location="loc_room")
        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[item],
            actors={},
            locks=[],
            parts=[part]
        )

        errors = validate_game_state(game_state)
        self.assertEqual(errors, [])
```

### 1.5 Add Part Accessor Methods to StateAccessor

**File:** `src/state_accessor.py`

**Implementation:**
```python
# Add to StateAccessor class:

def get_part(self, part_id: str):
    """
    Get part by ID.

    Args:
        part_id: The part ID to look up

    Returns:
        Part or None if not found
    """
    for part in self.game_state.parts:
        if part.id == part_id:
            return part
    return None

def get_parts_of(self, entity_id: str):
    """
    Get all parts belonging to an entity.

    Args:
        entity_id: The parent entity ID

    Returns:
        List of Part objects belonging to entity
    """
    return [p for p in self.game_state.parts if p.part_of == entity_id]

def get_items_at_part(self, part_id: str):
    """
    Get items located at a part.

    Args:
        part_id: The part ID

    Returns:
        List of Item objects at this part
    """
    return [i for i in self.game_state.items if i.location == part_id]

def get_entity(self, entity_id: str):
    """
    Get any entity by ID regardless of type.

    Searches all entity collections: locations, items, actors, locks, parts.

    Args:
        entity_id: The entity ID to look up

    Returns:
        Entity or None if not found
    """
    # Check locations
    entity = self.get_location(entity_id)
    if entity:
        return entity

    # Check items
    entity = self.get_item(entity_id)
    if entity:
        return entity

    # Check actors
    entity = self.get_actor(entity_id)
    if entity:
        return entity

    # Check locks
    entity = self.get_lock(entity_id)
    if entity:
        return entity

    # Check parts
    entity = self.get_part(entity_id)
    if entity:
        return entity

    return None

def get_focused_entity(self, actor_id: str):
    """
    Get entity actor is focused on.

    The focused_on property can reference any entity type:
    item, container, part, or actor.

    Args:
        actor_id: The actor ID

    Returns:
        Entity actor is focused on, or None
    """
    actor = self.get_actor(actor_id)
    if not actor:
        return None

    focused_id = actor.properties.get("focused_on")
    if not focused_id:
        return None

    return self.get_entity(focused_id)
```

**Tests to Write First:**
```python
# tests/test_state_accessor_parts.py (new file)

class TestStateAccessorParts(unittest.TestCase):
    def setUp(self):
        """Set up test game state with parts."""
        metadata = Metadata(title="Test", start_location="loc_room")

        self.location = Location(
            id="loc_room",
            name="Room",
            description="A test room"
        )

        self.part_wall = Part(
            id="part_room_north_wall",
            name="north wall",
            part_of="loc_room",
            properties={"material": "stone"}
        )

        self.item = Item(
            id="item_bench",
            name="bench",
            description="A bench",
            location="loc_room"
        )

        self.part_bench = Part(
            id="part_bench_left",
            name="left side",
            part_of="item_bench"
        )

        self.item_at_part = Item(
            id="item_mortar",
            name="mortar",
            description="A stone mortar",
            location="part_bench_left"
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location],
            items=[self.item, self.item_at_part],
            actors={"player": Actor(id="player", name="Player", location="loc_room")},
            locks=[],
            parts=[self.part_wall, self.part_bench]
        )

        self.behavior_manager = None  # Not needed for these tests
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_get_part_by_id(self):
        """Test getting part by ID."""
        part = self.accessor.get_part("part_room_north_wall")

        self.assertIsNotNone(part)
        self.assertEqual(part.id, "part_room_north_wall")
        self.assertEqual(part.name, "north wall")

    def test_get_part_nonexistent(self):
        """Test getting non-existent part returns None."""
        part = self.accessor.get_part("part_nonexistent")
        self.assertIsNone(part)

    def test_get_parts_of_location(self):
        """Test getting all parts of a location."""
        parts = self.accessor.get_parts_of("loc_room")

        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0].id, "part_room_north_wall")

    def test_get_parts_of_item(self):
        """Test getting all parts of an item."""
        parts = self.accessor.get_parts_of("item_bench")

        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0].id, "part_bench_left")

    def test_get_parts_of_entity_with_no_parts(self):
        """Test getting parts of entity with no parts returns empty list."""
        parts = self.accessor.get_parts_of("item_mortar")
        self.assertEqual(parts, [])

    def test_get_items_at_part(self):
        """Test getting items located at a part."""
        items = self.accessor.get_items_at_part("part_bench_left")

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, "item_mortar")

    def test_get_items_at_part_with_no_items(self):
        """Test getting items at part with no items returns empty list."""
        items = self.accessor.get_items_at_part("part_room_north_wall")
        self.assertEqual(items, [])

    def test_get_entity_finds_part(self):
        """Test get_entity can find parts."""
        entity = self.accessor.get_entity("part_room_north_wall")

        self.assertIsNotNone(entity)
        self.assertIsInstance(entity, Part)
        self.assertEqual(entity.id, "part_room_north_wall")

    def test_get_entity_searches_all_types(self):
        """Test get_entity searches all entity types."""
        # Can find location
        self.assertIsNotNone(self.accessor.get_entity("loc_room"))

        # Can find item
        self.assertIsNotNone(self.accessor.get_entity("item_bench"))

        # Can find part
        self.assertIsNotNone(self.accessor.get_entity("part_room_north_wall"))

        # Can find actor
        self.assertIsNotNone(self.accessor.get_entity("player"))

    def test_get_focused_entity_returns_part(self):
        """Test get_focused_entity can return part."""
        player = self.accessor.get_actor("player")
        player.properties["focused_on"] = "part_bench_left"

        focused = self.accessor.get_focused_entity("player")

        self.assertIsNotNone(focused)
        self.assertIsInstance(focused, Part)
        self.assertEqual(focused.id, "part_bench_left")

    def test_get_focused_entity_returns_item(self):
        """Test get_focused_entity can return item."""
        player = self.accessor.get_actor("player")
        player.properties["focused_on"] = "item_bench"

        focused = self.accessor.get_focused_entity("player")

        self.assertIsNotNone(focused)
        self.assertIsInstance(focused, Item)
        self.assertEqual(focused.id, "item_bench")

    def test_get_focused_entity_no_focus(self):
        """Test get_focused_entity when actor not focused returns None."""
        focused = self.accessor.get_focused_entity("player")
        self.assertIsNone(focused)
```

### 1.6 Phase 1 Deliverables and Success Criteria

**Deliverables:**
1. Part dataclass added to state_manager.py
2. Parts collection added to GameState
3. JSON loading supports parts
4. Validation rules for parts implemented
5. StateAccessor has part query methods
6. All tests pass (minimum 20 tests for Phase 1)

**Success Criteria:**
- [ ] Can define parts in JSON game files
- [ ] Parts load correctly into GameState
- [ ] Validation catches invalid part configurations
- [ ] Can query parts by ID
- [ ] Can find parts belonging to an entity
- [ ] Can find items located at parts
- [ ] get_entity() finds parts along with other entity types
- [ ] All existing tests still pass (backward compatibility)

---

## Phase 2: Implicit Positioning in Core Behaviors

**Duration:** 3-4 days
**Goal:** Automatic positioning when interacting with entities that require proximity

### 2.1 Add interaction_distance Property Support

**Implementation:**
All entities already have flexible properties dict. No code changes needed - just define the property semantics:

**Property Definition:**
- **Name:** `interaction_distance`
- **Type:** string
- **Values:** `"any"` (default) or `"near"`
- **Location:** In entity's `properties` dict
- **Semantics:**
  - `"any"`: Can interact from anywhere in location (default for all entities)
  - `"near"`: Must be near entity to interact (sets focused_on automatically)

**Tests to Write First:**
```python
# tests/test_interaction_distance.py (new file)

class TestInteractionDistanceProperty(unittest.TestCase):
    def test_entity_defaults_to_any_distance(self):
        """Test entities default to interaction_distance 'any'."""
        item = Item(
            id="item_chandelier",
            name="chandelier",
            description="A chandelier",
            location="loc_room"
        )

        # Should default to "any"
        distance = item.properties.get("interaction_distance", "any")
        self.assertEqual(distance, "any")

    def test_entity_can_have_near_distance(self):
        """Test entity can specify interaction_distance 'near'."""
        item = Item(
            id="item_desk",
            name="desk",
            description="A desk",
            location="loc_room",
            properties={"interaction_distance": "near"}
        )

        distance = item.properties.get("interaction_distance", "any")
        self.assertEqual(distance, "near")

    def test_part_can_have_interaction_distance(self):
        """Test parts can have interaction_distance property."""
        part = Part(
            id="part_wall",
            name="wall",
            part_of="loc_room",
            properties={"interaction_distance": "near"}
        )

        distance = part.properties.get("interaction_distance", "any")
        self.assertEqual(distance, "near")
```

### 2.2 Enhance handle_examine for Implicit Positioning

**File:** `behaviors/core/perception.py`

**Implementation:**
```python
def handle_examine(accessor, action):
    """
    Handle examine command with implicit positioning support.

    If entity has interaction_distance: "near", automatically set
    actor's focused_on property to entity ID.
    """
    actor_id = action.get("actor_id", "player")
    actor = accessor.get_actor(actor_id)

    if not actor:
        return HandlerResult(
            success=False,
            message="Actor not found."
        )

    obj_entry = action.get("object")
    if not obj_entry:
        return HandlerResult(
            success=False,
            message="What do you want to examine?"
        )

    # Find entity in current location (items, parts, actors, containers)
    location_id = actor.location
    entity = _find_entity_in_location(accessor, location_id, obj_entry)

    if not entity:
        return HandlerResult(
            success=False,
            message=f"You don't see {obj_entry.word} here."
        )

    # Check interaction distance
    distance = entity.properties.get("interaction_distance", "any")

    movement_prefix = ""
    if distance == "near":
        # Check if already focused on this entity
        old_focus = actor.properties.get("focused_on")
        if old_focus != entity.id:
            # Move actor near entity
            actor.properties["focused_on"] = entity.id
            # Clear any posture when moving
            if "posture" in actor.properties:
                actor.properties["posture"] = None
            movement_prefix = f"You move closer to the {entity.name}. "

    # Get description
    description = entity.properties.get("description", f"You see the {entity.name}.")

    # If examining a part, list items at that part
    if hasattr(entity, "part_of"):  # It's a Part
        items_at_part = accessor.get_items_at_part(entity.id)
        if items_at_part:
            visible_items = [item for item in items_at_part
                           if not item.states.get("hidden", False)]
            if visible_items:
                item_names = ", ".join(f"a {item.name}" for item in visible_items)
                description += f" At the {entity.name}: {item_names}."

    # Build result data for LLM narration
    data = {
        "id": entity.id,
        "name": entity.name,
        "type": entity.__class__.__name__.lower(),
        "llm_context": entity.llm_context
    }

    return HandlerResult(
        success=True,
        message=movement_prefix + description,
        data=data
    )


def _find_entity_in_location(accessor, location_id: str, obj_entry):
    """
    Find entity matching obj_entry in given location.

    Searches items, parts, and actors in the location.
    Uses vocabulary system for matching.
    """
    from src.parser import matches_word_entry

    # Search items in location
    for item in accessor.game_state.items:
        if item.location == location_id:
            if matches_word_entry(item.name, obj_entry):
                return item

    # Search parts of location
    for part in accessor.game_state.parts:
        if part.part_of == location_id:
            if matches_word_entry(part.name, obj_entry):
                return part

    # Search parts of items in location (e.g., "left side of bench")
    for item in accessor.game_state.items:
        if item.location == location_id:
            for part in accessor.get_parts_of(item.id):
                if matches_word_entry(part.name, obj_entry):
                    return part

    # Search actors in location
    for actor in accessor.game_state.actors.values():
        if actor.location == location_id and actor.id != "player":
            if matches_word_entry(actor.name, obj_entry):
                return actor

    return None
```

**Tests to Write First:**
```python
# tests/test_implicit_positioning.py (new file)

class TestImplicitPositioning(unittest.TestCase):
    def setUp(self):
        """Set up test game with entities at different distances."""
        metadata = Metadata(title="Test", start_location="loc_room")

        self.location = Location(
            id="loc_room",
            name="Test Room",
            description="A test room"
        )

        # Item with "any" distance (default)
        self.item_far = Item(
            id="item_chandelier",
            name="chandelier",
            description="A crystal chandelier",
            location="loc_room"
            # No interaction_distance = defaults to "any"
        )

        # Item with "near" distance
        self.item_near = Item(
            id="item_desk",
            name="desk",
            description="A wooden desk",
            location="loc_room",
            properties={"interaction_distance": "near"}
        )

        # Part with "near" distance
        self.part = Part(
            id="part_room_north_wall",
            name="north wall",
            part_of="loc_room",
            properties={
                "description": "A stone wall",
                "interaction_distance": "near"
            }
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location],
            items=[self.item_far, self.item_near],
            actors={"player": Actor(id="player", name="Player", location="loc_room")},
            locks=[],
            parts=[self.part]
        )

        # Mock vocabulary
        self.vocab = load_merged_vocabulary([])

        self.behavior_manager = None
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_examine_any_distance_no_movement(self):
        """Test examining 'any' distance entity doesn't move player."""
        from behaviors.core.perception import handle_examine

        player = self.accessor.get_actor("player")

        # Create action
        action = {
            "verb": "examine",
            "object": WordEntry(word="chandelier"),
            "actor_id": "player"
        }

        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Should not include movement prefix
        self.assertNotIn("move closer", result.message.lower())
        # Player focused_on should not be set
        self.assertIsNone(player.properties.get("focused_on"))

    def test_examine_near_distance_moves_player(self):
        """Test examining 'near' entity moves player to it."""
        from behaviors.core.perception import handle_examine

        player = self.accessor.get_actor("player")

        # Create action
        action = {
            "verb": "examine",
            "object": WordEntry(word="desk"),
            "actor_id": "player"
        }

        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Should include movement prefix
        self.assertIn("move closer", result.message.lower())
        # Player focused_on should be set
        self.assertEqual(player.properties.get("focused_on"), "item_desk")

    def test_examine_near_already_focused_no_movement(self):
        """Test examining near entity when already there doesn't repeat movement."""
        from behaviors.core.perception import handle_examine

        player = self.accessor.get_actor("player")
        player.properties["focused_on"] = "item_desk"

        action = {
            "verb": "examine",
            "object": WordEntry(word="desk"),
            "actor_id": "player"
        }

        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Should NOT include movement prefix
        self.assertNotIn("move closer", result.message.lower())

    def test_examine_part_with_near_moves_player(self):
        """Test examining part with 'near' moves player."""
        from behaviors.core.perception import handle_examine

        player = self.accessor.get_actor("player")

        action = {
            "verb": "examine",
            "object": WordEntry(word="wall"),
            "actor_id": "player"
        }

        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("move closer", result.message.lower())
        self.assertEqual(player.properties.get("focused_on"), "part_room_north_wall")

    def test_implicit_movement_clears_posture(self):
        """Test implicit movement clears posture."""
        from behaviors.core.perception import handle_examine

        player = self.accessor.get_actor("player")
        player.properties["focused_on"] = "item_far"
        player.properties["posture"] = "cover"

        # Examine different near entity
        action = {
            "verb": "examine",
            "object": WordEntry(word="desk"),
            "actor_id": "player"
        }

        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Posture should be cleared
        self.assertIsNone(player.properties.get("posture"))

    def test_examine_part_lists_items_at_part(self):
        """Test examining part lists items located at that part."""
        from behaviors.core.perception import handle_examine

        # Add item at part
        item_at_wall = Item(
            id="item_tapestry",
            name="tapestry",
            description="A faded tapestry",
            location="part_room_north_wall"
        )
        self.game_state.items.append(item_at_wall)

        action = {
            "verb": "examine",
            "object": WordEntry(word="wall"),
            "actor_id": "player"
        }

        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("tapestry", result.message.lower())
        self.assertIn("at the", result.message.lower())
```

### 2.3 Enhance Other Core Verbs for Implicit Positioning

Apply the same implicit positioning logic to:
- `handle_take` (behaviors/core/manipulation.py)
- `handle_drop` (behaviors/core/manipulation.py)
- `handle_open` (behaviors/core/interaction.py)
- `handle_close` (behaviors/core/interaction.py)

**Pattern for each handler:**
```python
def handle_<verb>(accessor, action):
    # ... existing setup code ...

    # Find entity
    entity = _find_entity(...)

    # Check interaction distance and move if needed
    distance = entity.properties.get("interaction_distance", "any")
    movement_prefix = ""

    if distance == "near":
        old_focus = actor.properties.get("focused_on")
        if old_focus != entity.id:
            actor.properties["focused_on"] = entity.id
            if "posture" in actor.properties:
                actor.properties["posture"] = None
            movement_prefix = f"You move to the {entity.name}. "

    # ... existing verb logic ...

    return HandlerResult(
        success=True,
        message=movement_prefix + main_message,
        data=data
    )
```

**Tests to Write:**
Similar structure to examine tests, one test file per verb:
- tests/test_take_implicit_positioning.py
- tests/test_open_implicit_positioning.py
- etc.

### 2.4 Phase 2 Deliverables and Success Criteria

**Deliverables:**
1. interaction_distance property semantics defined
2. handle_examine enhanced with implicit positioning
3. handle_take, handle_drop, handle_open, handle_close enhanced
4. Comprehensive tests for all implicit positioning scenarios
5. All tests pass (minimum 25 new tests for Phase 2)

**Success Criteria:**
- [x] Entities default to "any" interaction distance
- [x] Setting "near" triggers automatic movement
- [x] Movement only happens if not already focused
- [x] Movement message appears before action result
- [x] Posture cleared when moving
- [x] Parts support implicit positioning
- [x] Items at parts visible when examining parts
- [x] All existing tests still pass

### Phase 2 Results

**Completion Date:** 2025-12-03

**Implementation Summary:**
1. Created helper functions in utilities/positioning.py:
   - `try_implicit_positioning()` - Core positioning logic
   - `find_and_position_item()` - Combined item finding + positioning
   - `find_and_position_part()` - Combined part finding + positioning
   - `build_message_with_positioning()` - Message assembly helper

2. Enhanced handlers with implicit positioning:
   - `handle_examine` (behaviors/core/perception.py) - Items and parts
   - `handle_take` (behaviors/core/manipulation.py) - Including container operations
   - `handle_open` (behaviors/core/interaction.py) - Containers and doors
   - `handle_close` (behaviors/core/interaction.py) - Containers and doors

3. Created comprehensive tests (21 new tests):
   - tests/test_examine_implicit_positioning.py (9 tests)
   - tests/test_take_implicit_positioning.py (6 tests)
   - tests/test_open_close_implicit_positioning.py (7 tests)

4. Created implementation guide:
   - docs/implicit_positioning_patterns.md - Patterns and examples for future handlers

**Handlers Reviewed but Not Modified:**
- `handle_drop` - Doesn't target specific entities, drops at general location
- `handle_give` - Targets actors, not spatial entities (out of scope for Phase 2)
- `handle_put` - Deferred to Phase 3 (advanced container positioning)

**Test Results:**
- All 21 new Phase 2 tests passing
- All 1,321 existing tests still passing
- Zero regressions

**Issues Encountered:**
- None

**Work Deferred:**
- None for Phase 2 core requirements

---

## Phase 3: Explicit Positioning Commands

**Duration:** 2-3 days
**Goal:** Players can explicitly position themselves for precise puzzle requirements

### 3.1 Add Approach Vocabulary

**File:** `behaviors/core/perception.py` (or new `behaviors/core/spatial.py`)

**Implementation:**
```python
# Add to VOCABULARY dict in perception.py (or new spatial.py):

VOCABULARY = {
    "verbs": [
        {
            "word": "approach",
            "synonyms": ["go to", "move to", "walk to"],
            "object_required": True,
            "llm_context": {
                "traits": ["moves actor near object"],
                "usage": ["approach <object>", "go to <object>"]
            }
        }
    ]
}
```

**Tests to Write First:**
```python
# tests/test_approach_vocabulary.py

class TestApproachVocabulary(unittest.TestCase):
    def test_approach_verb_in_vocabulary(self):
        """Test approach verb is registered."""
        vocab = load_merged_vocabulary(["behaviors/core/perception.py"])

        approach_entry = None
        for verb in vocab.get("verbs", []):
            if verb["word"] == "approach":
                approach_entry = verb
                break

        self.assertIsNotNone(approach_entry)
        self.assertIn("go to", approach_entry.get("synonyms", []))
        self.assertTrue(approach_entry.get("object_required"))
```

### 3.2 Implement handle_approach

**File:** `behaviors/core/perception.py` (or `behaviors/core/spatial.py`)

**Implementation:**
```python
def handle_approach(accessor, action):
    """
    Handle approach command for explicit positioning.

    Moves actor to be focused on target entity (item, part, container, actor).
    """
    actor_id = action.get("actor_id", "player")
    actor = accessor.get_actor(actor_id)

    if not actor:
        return HandlerResult(
            success=False,
            message="Actor not found."
        )

    obj_entry = action.get("object")
    if not obj_entry:
        return HandlerResult(
            success=False,
            message="What do you want to approach?"
        )

    # Find target entity in current location
    location_id = actor.location
    target = _find_entity_in_location(accessor, location_id, obj_entry)

    if not target:
        return HandlerResult(
            success=False,
            message=f"You don't see {obj_entry.word} here."
        )

    # Check if target is accessible
    if not _is_accessible(accessor, actor, target):
        return HandlerResult(
            success=False,
            message=f"You can't reach the {target.name} from here."
        )

    # Check old focus
    old_focus = actor.properties.get("focused_on")

    # Update focus
    actor.properties["focused_on"] = target.id

    # Clear posture when explicitly moving
    if "posture" in actor.properties:
        actor.properties["posture"] = None

    # Build message
    if old_focus == target.id:
        message = f"You're already at the {target.name}."
    else:
        message = f"You move to the {target.name}."

    # Build result data
    data = {
        "id": target.id,
        "name": target.name,
        "type": target.__class__.__name__.lower(),
        "focused_on": True,
        "llm_context": target.llm_context
    }

    return HandlerResult(success=True, message=message, data=data)


def _is_accessible(accessor, actor, target):
    """
    Check if target entity is accessible from actor's location.

    Returns True if target is in same location or is a part whose parent
    is in same location.
    """
    actor_location = actor.location

    # If target is an item/actor, check same location
    if hasattr(target, 'location'):
        return target.location == actor_location

    # If target is a part, check parent is in same location
    if hasattr(target, 'part_of'):
        parent = accessor.get_entity(target.part_of)
        if parent:
            # If parent is a location, check actor is in that location
            if hasattr(parent, 'exits'):  # It's a Location
                return parent.id == actor_location
            # If parent is an item/actor, check parent's location
            if hasattr(parent, 'location'):
                return parent.location == actor_location

    return False
```

**Tests to Write First:**
```python
# tests/test_approach_command.py

class TestApproachCommand(unittest.TestCase):
    def setUp(self):
        """Set up test game with various entities."""
        metadata = Metadata(title="Test", start_location="loc_room")

        self.location = Location(
            id="loc_room",
            name="Test Room",
            description="A test room"
        )

        self.item = Item(
            id="item_bench",
            name="bench",
            description="A wooden bench",
            location="loc_room"
        )

        self.part = Part(
            id="part_bench_left",
            name="left side of bench",
            part_of="item_bench",
            properties={"description": "The left end of the bench"}
        )

        self.wall_part = Part(
            id="part_room_north_wall",
            name="north wall",
            part_of="loc_room",
            properties={"description": "A stone wall"}
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location],
            items=[self.item],
            actors={"player": Actor(id="player", name="Player", location="loc_room")},
            locks=[],
            parts=[self.part, self.wall_part]
        )

        self.behavior_manager = None
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_approach_item_sets_focus(self):
        """Test approaching item sets focused_on."""
        from behaviors.core.perception import handle_approach

        player = self.accessor.get_actor("player")

        action = {
            "verb": "approach",
            "object": WordEntry(word="bench"),
            "actor_id": "player"
        }

        result = handle_approach(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("move to", result.message.lower())
        self.assertEqual(player.properties.get("focused_on"), "item_bench")

    def test_approach_part_of_item_sets_focus(self):
        """Test approaching part sets focused_on to part."""
        from behaviors.core.perception import handle_approach

        player = self.accessor.get_actor("player")

        action = {
            "verb": "approach",
            "object": WordEntry(word="left side of bench"),
            "actor_id": "player"
        }

        result = handle_approach(self.accessor, action)

        self.assertTrue(result.success)
        self.assertEqual(player.properties.get("focused_on"), "part_bench_left")

    def test_approach_part_of_location_sets_focus(self):
        """Test approaching part of location sets focused_on."""
        from behaviors.core.perception import handle_approach

        player = self.accessor.get_actor("player")

        action = {
            "verb": "approach",
            "object": WordEntry(word="north wall"),
            "actor_id": "player"
        }

        result = handle_approach(self.accessor, action)

        self.assertTrue(result.success)
        self.assertEqual(player.properties.get("focused_on"), "part_room_north_wall")

    def test_approach_already_focused_acknowledges(self):
        """Test approaching current focus returns 'already there' message."""
        from behaviors.core.perception import handle_approach

        player = self.accessor.get_actor("player")
        player.properties["focused_on"] = "item_bench"

        action = {
            "verb": "approach",
            "object": WordEntry(word="bench"),
            "actor_id": "player"
        }

        result = handle_approach(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("already at", result.message.lower())

    def test_approach_nonexistent_entity_fails(self):
        """Test approaching non-existent entity fails."""
        from behaviors.core.perception import handle_approach

        action = {
            "verb": "approach",
            "object": WordEntry(word="unicorn"),
            "actor_id": "player"
        }

        result = handle_approach(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.message.lower())

    def test_approach_entity_in_different_location_fails(self):
        """Test approaching entity in different location fails."""
        from behaviors.core.perception import handle_approach

        # Add another location with item
        other_location = Location(
            id="loc_other",
            name="Other Room",
            description="Another room"
        )
        other_item = Item(
            id="item_other",
            name="table",
            description="A table",
            location="loc_other"
        )
        self.game_state.locations.append(other_location)
        self.game_state.items.append(other_item)

        action = {
            "verb": "approach",
            "object": WordEntry(word="table"),
            "actor_id": "player"
        }

        result = handle_approach(self.accessor, action)

        # Should not find table (not in current location)
        self.assertFalse(result.success)

    def test_approach_clears_posture(self):
        """Test approaching clears current posture."""
        from behaviors.core.perception import handle_approach

        player = self.accessor.get_actor("player")
        player.properties["focused_on"] = "part_room_north_wall"
        player.properties["posture"] = "cover"

        # Approach different entity
        action = {
            "verb": "approach",
            "object": WordEntry(word="bench"),
            "actor_id": "player"
        }

        result = handle_approach(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIsNone(player.properties.get("posture"))
```

### 3.3 Create Example: Multi-Part Object Puzzle

**File:** `examples/alchemy_bench/game.json`

Create example game demonstrating position-dependent interactions:
```json
{
  "metadata": {
    "title": "Alchemy Bench Example",
    "start_location": "loc_workshop"
  },
  "locations": [
    {
      "id": "loc_workshop",
      "name": "Alchemist's Workshop",
      "description": "A cluttered workshop with a long workbench.",
      "exits": {}
    }
  ],
  "items": [
    {
      "id": "item_bench",
      "name": "bench",
      "description": "A long wooden workbench.",
      "location": "loc_workshop",
      "properties": {
        "portable": false,
        "interaction_distance": "near"
      }
    },
    {
      "id": "item_herbs",
      "name": "herbs",
      "description": "Dried herbs.",
      "location": "loc_workshop",
      "properties": {
        "portable": true
      }
    }
  ],
  "parts": [
    {
      "id": "part_bench_left",
      "name": "left side of bench",
      "part_of": "item_bench",
      "properties": {
        "description": "Grinding tools and a mortar are at this end.",
        "activity": "grinding"
      }
    },
    {
      "id": "part_bench_center",
      "name": "center of bench",
      "part_of": "item_bench",
      "properties": {
        "description": "Beakers and burners for mixing.",
        "activity": "mixing"
      }
    }
  ],
  "actors": {},
  "locks": []
}
```

**File:** `examples/alchemy_bench/behaviors/alchemy.py`

```python
def handle_grind(accessor, action):
    """Grind herbs - requires being at left side of bench."""
    actor_id = action.get("actor_id", "player")
    actor = accessor.get_actor(actor_id)

    # Check if player has herbs
    herbs = accessor.get_item("item_herbs")
    if not herbs or herbs.location != actor_id:
        return HandlerResult(
            success=False,
            message="You need to be holding the herbs."
        )

    # Check if focused on correct part
    focused = actor.properties.get("focused_on")
    if focused != "part_bench_left":
        return HandlerResult(
            success=False,
            message="You need to be at the left side of the bench where the mortar is."
        )

    # Perform grinding
    herbs.states["ground"] = True

    return HandlerResult(
        success=True,
        message="You crush the dried herbs into a fine powder using the mortar and pestle."
    )

VOCABULARY = {
    "verbs": [
        {
            "word": "grind",
            "synonyms": ["crush", "pulverize"],
            "object_required": True
        }
    ]
}
```

**Tests for Example:**
```python
# examples/alchemy_bench/test_alchemy.py

class TestAlchemyBenchExample(unittest.TestCase):
    def setUp(self):
        """Load alchemy bench example game."""
        self.game_state = load_game_state("examples/alchemy_bench/game.json")
        self.behavior_manager = BehaviorManager()
        self.behavior_manager.load_behaviors(["examples/alchemy_bench/behaviors/alchemy.py"])
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_grind_fails_when_not_at_left_side(self):
        """Test grinding requires being at left side of bench."""
        from examples.alchemy_bench.behaviors.alchemy import handle_grind

        player = self.accessor.get_actor("player")

        # Give player herbs
        herbs = self.accessor.get_item("item_herbs")
        herbs.location = "player"
        player.inventory.append("item_herbs")

        # Player not at correct position
        action = {
            "verb": "grind",
            "object": WordEntry(word="herbs"),
            "actor_id": "player"
        }

        result = handle_grind(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("left side of the bench", result.message)

    def test_grind_succeeds_at_left_side(self):
        """Test grinding succeeds when at left side."""
        from examples.alchemy_bench.behaviors.alchemy import handle_grind

        player = self.accessor.get_actor("player")

        # Give player herbs
        herbs = self.accessor.get_item("item_herbs")
        herbs.location = "player"
        player.inventory.append("item_herbs")

        # Move player to left side
        player.properties["focused_on"] = "part_bench_left"

        action = {
            "verb": "grind",
            "object": WordEntry(word="herbs"),
            "actor_id": "player"
        }

        result = handle_grind(self.accessor, action)

        self.assertTrue(result.success)
        self.assertTrue(herbs.states.get("ground"))
```

### 3.4 Phase 3 Deliverables and Success Criteria

**Deliverables:**
1. `approach` command vocabulary
2. `handle_approach` implementation
3. `_is_accessible` helper for checking reachability
4. Example game demonstrating position-dependent puzzles
5. All tests pass (minimum 15 new tests for Phase 3)

**Success Criteria:**
- [x] Can approach items, parts, containers, actors
- [x] Approach sets focused_on to target
- [x] Approach clears posture
- [x] Can't approach entities in different location
- [x] "Already there" message when approaching current focus
- [x] All existing tests still pass

### Phase 3 Results

**Completion Date:** 2025-12-04

**Implementation Summary:**
1. Created behaviors/core/spatial.py - New module for explicit positioning commands
   - `approach` verb with synonyms "go to", "move to", "walk to"
   - `handle_approach()` - Explicit positioning handler
   - `_find_entity_in_location()` - Universal entity lookup
   - `_is_accessible()` - Accessibility validation

2. Functionality:
   - Players can explicitly position at any entity (items, parts, actors)
   - Always sets `focused_on` to target entity
   - Clears posture when moving
   - "Already there" message if already focused
   - Validates accessibility (must be in same location)

3. Created comprehensive tests (10 new tests):
   - tests/test_approach_command.py

**Test Results:**
- All 10 new Phase 3 tests passing
- All 1,336 total tests passing
- Zero regressions

**Issues Encountered:**
- None

**Work Deferred:**
- Example game demonstrating position-dependent puzzles (not essential for core functionality)

---

## Phase 4: Universal Surface Fallback

**Duration:** 2 days
**Goal:** Players can examine universal surfaces (ceiling, floor, walls, sky, ground) without explicit parts

### 4.1 Create behaviors/core/spatial.py

**File:** `behaviors/core/spatial.py`

**Implementation:**
```python
"""
Spatial behavior module for universal surfaces and spatial commands.

Universal surfaces are common room features (ceiling, floor, walls, sky, ground)
that exist in every location but don't require explicit Part entities unless
authors want custom descriptions or special behaviors.
"""

# Universal surface vocabulary
VOCABULARY = {
    "nouns": [
        {
            "word": "ceiling",
            "synonyms": [],
            "properties": {
                "universal_surface": True,
                "default_description": "Nothing remarkable about the ceiling."
            }
        },
        {
            "word": "floor",
            "synonyms": ["ground"],
            "properties": {
                "universal_surface": True,
                "default_description": "Nothing remarkable about the floor."
            }
        },
        {
            "word": "sky",
            "synonyms": [],
            "properties": {
                "universal_surface": True,
                "default_description": "The sky stretches above you."
            }
        },
        {
            "word": "walls",
            "synonyms": [],
            "properties": {
                "universal_surface": True,
                "default_description": "The walls surround you."
            }
        }
    ]
}


def get_universal_surface_nouns():
    """Return list of universal surface noun words."""
    return [entry["word"] for entry in VOCABULARY["nouns"]
            if entry.get("properties", {}).get("universal_surface")]


def is_universal_surface(word_entry):
    """Check if word entry refers to a universal surface."""
    universal_words = get_universal_surface_nouns()

    # Check primary word
    if word_entry.word in universal_words:
        return True

    # Check synonyms
    for entry in VOCABULARY["nouns"]:
        if entry.get("properties", {}).get("universal_surface"):
            if word_entry.word in entry.get("synonyms", []):
                return True

    return False


def get_default_description(word_entry):
    """Get default description for universal surface."""
    for entry in VOCABULARY["nouns"]:
        if entry["word"] == word_entry.word:
            return entry.get("properties", {}).get("default_description")
        if word_entry.word in entry.get("synonyms", []):
            return entry.get("properties", {}).get("default_description")

    return f"Nothing remarkable about the {word_entry.word}."
```

**Tests to Write First:**
```python
# tests/test_universal_surfaces.py

class TestUniversalSurfaces(unittest.TestCase):
    def test_universal_surface_vocabulary_loaded(self):
        """Test universal surface vocabulary is present."""
        from behaviors.core.spatial import VOCABULARY

        nouns = VOCABULARY.get("nouns", [])

        # Should have ceiling, floor, sky, walls
        words = [n["word"] for n in nouns]
        self.assertIn("ceiling", words)
        self.assertIn("floor", words)
        self.assertIn("sky", words)
        self.assertIn("walls", words)

    def test_get_universal_surface_nouns(self):
        """Test getting list of universal surface nouns."""
        from behaviors.core.spatial import get_universal_surface_nouns

        surfaces = get_universal_surface_nouns()

        self.assertIn("ceiling", surfaces)
        self.assertIn("floor", surfaces)
        self.assertIn("sky", surfaces)
        self.assertIn("walls", surfaces)

    def test_is_universal_surface_recognizes_surfaces(self):
        """Test is_universal_surface identifies surfaces."""
        from behaviors.core.spatial import is_universal_surface

        self.assertTrue(is_universal_surface(WordEntry(word="ceiling")))
        self.assertTrue(is_universal_surface(WordEntry(word="floor")))
        self.assertTrue(is_universal_surface(WordEntry(word="sky")))
        self.assertTrue(is_universal_surface(WordEntry(word="walls")))

        # Synonym
        self.assertTrue(is_universal_surface(WordEntry(word="ground")))

    def test_is_universal_surface_rejects_non_surfaces(self):
        """Test is_universal_surface rejects non-surfaces."""
        from behaviors.core.spatial import is_universal_surface

        self.assertFalse(is_universal_surface(WordEntry(word="table")))
        self.assertFalse(is_universal_surface(WordEntry(word="door")))

    def test_get_default_description_returns_description(self):
        """Test getting default description for surfaces."""
        from behaviors.core.spatial import get_default_description

        desc = get_default_description(WordEntry(word="ceiling"))
        self.assertIn("ceiling", desc.lower())

        desc = get_default_description(WordEntry(word="floor"))
        self.assertIn("floor", desc.lower())
```

### 4.2 Enhance handle_examine to Support Universal Surfaces

**File:** `behaviors/core/perception.py`

**Implementation:**
```python
def handle_examine(accessor, action):
    """Enhanced examine with universal surface fallback."""
    # ... existing code to find entity ...

    if entity:
        # Found explicit entity - examine it normally
        # ... existing examine logic ...
        return HandlerResult(...)

    # Entity not found - check if it's a universal surface
    from behaviors.core.spatial import is_universal_surface, get_default_description

    if is_universal_surface(obj_entry):
        description = get_default_description(obj_entry)
        return HandlerResult(success=True, message=description)

    # Not found and not universal surface
    return HandlerResult(
        success=False,
        message=f"You don't see {obj_entry.word} here."
    )
```

**Tests to Write First:**
```python
# tests/test_universal_surface_fallback.py

class TestUniversalSurfaceFallback(unittest.TestCase):
    def setUp(self):
        """Set up test game without explicit ceiling/floor parts."""
        metadata = Metadata(title="Test", start_location="loc_room")

        self.location = Location(
            id="loc_room",
            name="Simple Room",
            description="A simple room"
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location],
            items=[],
            actors={"player": Actor(id="player", name="Player", location="loc_room")},
            locks=[],
            parts=[]  # No parts defined
        )

        self.behavior_manager = None
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_examine_ceiling_without_part_uses_fallback(self):
        """Test examining ceiling without explicit part uses fallback."""
        from behaviors.core.perception import handle_examine

        action = {
            "verb": "examine",
            "object": WordEntry(word="ceiling"),
            "actor_id": "player"
        }

        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("ceiling", result.message.lower())
        # Should not say "don't see"
        self.assertNotIn("don't see", result.message.lower())

    def test_examine_floor_without_part_uses_fallback(self):
        """Test examining floor without explicit part uses fallback."""
        from behaviors.core.perception import handle_examine

        action = {
            "verb": "examine",
            "object": WordEntry(word="floor"),
            "actor_id": "player"
        }

        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("floor", result.message.lower())

    def test_examine_ground_synonym_uses_fallback(self):
        """Test examining ground (synonym for floor) uses fallback."""
        from behaviors.core.perception import handle_examine

        action = {
            "verb": "examine",
            "object": WordEntry(word="ground"),
            "actor_id": "player"
        }

        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Should mention floor or ground
        self.assertTrue(
            "floor" in result.message.lower() or "ground" in result.message.lower()
        )

    def test_explicit_ceiling_part_overrides_fallback(self):
        """Test explicit ceiling part overrides universal fallback."""
        from behaviors.core.perception import handle_examine

        # Add explicit ceiling part
        ceiling_part = Part(
            id="part_room_ceiling",
            name="ceiling",
            part_of="loc_room",
            properties={
                "description": "A magnificent vaulted ceiling with frescoes."
            }
        )
        self.game_state.parts.append(ceiling_part)

        action = {
            "verb": "examine",
            "object": WordEntry(word="ceiling"),
            "actor_id": "player"
        }

        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Should use explicit description, not fallback
        self.assertIn("vaulted", result.message.lower())
        self.assertIn("frescoes", result.message.lower())

    def test_examine_nonexistent_non_surface_still_fails(self):
        """Test examining non-existent non-surface still fails."""
        from behaviors.core.perception import handle_examine

        action = {
            "verb": "examine",
            "object": WordEntry(word="unicorn"),
            "actor_id": "player"
        }

        result = handle_examine(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.message.lower())
```

### 4.3 Phase 4 Deliverables and Success Criteria

**Deliverables:**
1. `behaviors/core/spatial.py` with universal surface vocabulary
2. Helper functions for checking universal surfaces
3. Enhanced handle_examine with fallback logic
4. Comprehensive tests for fallback behavior
5. All tests pass (minimum 10 new tests for Phase 4)

**Success Criteria:**
- [x] Can examine ceiling, floor, sky, walls, ground without explicit parts
- [x] Universal surfaces return sensible default descriptions
- [x] Explicit parts override universal surface fallbacks
- [x] Non-surface entities still fail with "don't see" message
- [x] Synonyms work (ground = floor)
- [x] All existing tests still pass

### Phase 4 Results

**Completion Date:** 2025-12-04

**Implementation Summary:**
1. Enhanced behaviors/core/spatial.py with universal surface vocabulary:
   - Added ceiling, floor (ground), sky, walls as universal surface nouns
   - Each has a default_description property
   - Universal surface nouns marked with `universal_surface: true` property

2. Created helper functions in spatial.py:
   - `get_universal_surface_nouns()` - Returns list of surface words
   - `is_universal_surface(word_entry)` - Checks if word is a universal surface
   - `get_default_description(word_entry)` - Returns default description for surface
   - All functions handle both WordEntry and string inputs
   - Case-insensitive matching
   - Synonym support (ground = floor)

3. Enhanced handle_examine (behaviors/core/perception.py):
   - Added universal surface fallback before "don't see" error
   - Checks if unmatched object is a universal surface
   - Returns default description for universal surfaces
   - Explicit Part entities always override fallback
   - Universal surfaces don't set focus or trigger positioning

4. Created comprehensive tests (33 new tests):
   - tests/test_universal_surfaces.py (21 tests)
     - Vocabulary tests
     - Helper function tests
     - String and WordEntry input tests
   - tests/test_universal_surface_fallback.py (12 tests)
     - Fallback behavior tests
     - Explicit part override tests
     - No focus/positioning tests

**Test Results:**
- All 33 new Phase 4 tests passing
- All 1,369 total tests passing
- Zero regressions

**Issues Encountered:**
- None

**Work Deferred:**
- None

---

## Phase 5: Posture System (Optional)

**Duration:** 2-3 days
**Goal:** Enable cover, concealment, climbing, and other positioning modes for tactical gameplay

### 5.1 Add posture Property Support

**Implementation:**
All actors already have flexible properties dict. No code changes needed - just define the property semantics:

**Property Definition:**
- **Name:** `posture`
- **Type:** string or null
- **Values:** `null` (default), `"cover"`, `"concealed"`, `"climbing"`, or custom values
- **Location:** In actor's `properties` dict
- **Semantics:**
  - `null` or omitted: Normal positioning (examining, interacting)
  - `"cover"`: Taking cover behind entity (combat/stealth)
  - `"concealed"`: Hiding inside/within entity
  - `"climbing"`: Climbing on entity
  - Custom values as needed by game behaviors

**Tests to Write First:**
```python
# tests/test_posture_property.py

class TestPostureProperty(unittest.TestCase):
    def test_actor_defaults_to_no_posture(self):
        """Test actors default to no posture."""
        actor = Actor(id="player", name="Player", location="loc_room")

        posture = actor.properties.get("posture")
        self.assertIsNone(posture)

    def test_actor_can_have_posture(self):
        """Test actor can have posture property."""
        actor = Actor(id="player", name="Player", location="loc_room")
        actor.properties["posture"] = "cover"

        self.assertEqual(actor.properties["posture"], "cover")

    def test_posture_cleared_when_moving(self):
        """Test posture cleared when actor moves (via examine)."""
        # This is tested in implicit positioning tests
        # but documenting the behavior here
        pass
```

### 5.2 Implement handle_take_cover

**File:** `behaviors/core/spatial.py` (or new `behaviors/core/combat.py`)

**Implementation:**
```python
# Add to VOCABULARY in spatial.py:
{
    "word": "cover",
    "synonyms": ["hide behind", "take cover"],
    "preposition_required": True,  # "take cover behind <object>"
    "llm_context": {
        "traits": ["tactical positioning", "concealment"],
        "usage": ["take cover behind <object>"]
    }
}

def handle_take_cover(accessor, action):
    """
    Take cover behind an object or part.

    Requires entity to have provides_cover property.
    """
    actor_id = action.get("actor_id", "player")
    actor = accessor.get_actor(actor_id)

    if not actor:
        return HandlerResult(
            success=False,
            message="Actor not found."
        )

    # Get target from indirect_object ("behind <object>")
    target_entry = action.get("indirect_object")
    if not target_entry:
        return HandlerResult(
            success=False,
            message="Take cover behind what?"
        )

    # Find cover entity
    location_id = actor.location
    cover = _find_entity_in_location(accessor, location_id, target_entry)

    if not cover:
        return HandlerResult(
            success=False,
            message=f"You don't see {target_entry.word} here."
        )

    # Check if entity provides cover
    if not cover.properties.get("provides_cover", False):
        return HandlerResult(
            success=False,
            message=f"The {cover.name} doesn't provide cover."
        )

    # Set cover state
    actor.properties["focused_on"] = cover.id
    actor.properties["posture"] = "cover"

    message = f"You take cover behind the {cover.name}."

    data = {
        "id": cover.id,
        "name": cover.name,
        "posture": "cover",
        "llm_context": cover.llm_context
    }

    return HandlerResult(success=True, message=message, data=data)
```

**Tests to Write First:**
```python
# tests/test_take_cover.py

class TestTakeCover(unittest.TestCase):
    def setUp(self):
        """Set up test game with cover objects."""
        metadata = Metadata(title="Test", start_location="loc_room")

        self.location = Location(
            id="loc_room",
            name="Test Room",
            description="A room"
        )

        # Item that provides cover
        self.cover_item = Item(
            id="item_pillar",
            name="pillar",
            description="A stone pillar",
            location="loc_room",
            properties={
                "portable": False,
                "provides_cover": True
            }
        )

        # Item that doesn't provide cover
        self.no_cover_item = Item(
            id="item_chair",
            name="chair",
            description="A wooden chair",
            location="loc_room",
            properties={"portable": False}
        )

        self.game_state = GameState(
            metadata=metadata,
            locations=[self.location],
            items=[self.cover_item, self.no_cover_item],
            actors={"player": Actor(id="player", name="Player", location="loc_room")},
            locks=[],
            parts=[]
        )

        self.behavior_manager = None
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    def test_take_cover_behind_pillar_succeeds(self):
        """Test taking cover behind object with provides_cover."""
        from behaviors.core.spatial import handle_take_cover

        player = self.accessor.get_actor("player")

        action = {
            "verb": "cover",
            "indirect_object": WordEntry(word="pillar"),
            "actor_id": "player"
        }

        result = handle_take_cover(self.accessor, action)

        self.assertTrue(result.success)
        self.assertIn("take cover", result.message.lower())
        self.assertEqual(player.properties.get("focused_on"), "item_pillar")
        self.assertEqual(player.properties.get("posture"), "cover")

    def test_take_cover_behind_non_cover_fails(self):
        """Test taking cover behind object without provides_cover fails."""
        from behaviors.core.spatial import handle_take_cover

        action = {
            "verb": "cover",
            "indirect_object": WordEntry(word="chair"),
            "actor_id": "player"
        }

        result = handle_take_cover(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("doesn't provide cover", result.message.lower())

    def test_take_cover_behind_nonexistent_fails(self):
        """Test taking cover behind non-existent object fails."""
        from behaviors.core.spatial import handle_take_cover

        action = {
            "verb": "cover",
            "indirect_object": WordEntry(word="boulder"),
            "actor_id": "player"
        }

        result = handle_take_cover(self.accessor, action)

        self.assertFalse(result.success)
        self.assertIn("don't see", result.message.lower())

    def test_leaving_cover_clears_posture(self):
        """Test moving away from cover clears posture."""
        from behaviors.core.perception import handle_examine

        player = self.accessor.get_actor("player")
        player.properties["focused_on"] = "item_pillar"
        player.properties["posture"] = "cover"

        # Examine different object
        action = {
            "verb": "examine",
            "object": WordEntry(word="chair"),
            "actor_id": "player"
        }

        result = handle_examine(self.accessor, action)

        self.assertTrue(result.success)
        # Posture should be cleared
        self.assertIsNone(player.properties.get("posture"))
```

### 5.3 Implement handle_hide_in (Concealment)

**File:** `behaviors/core/spatial.py`

**Implementation:**
```python
# Add to VOCABULARY:
{
    "word": "hide",
    "synonyms": ["conceal"],
    "preposition_required": True,  # "hide in <object>"
    "llm_context": {
        "traits": ["stealth", "concealment"],
        "usage": ["hide in <object>"]
    }
}

def handle_hide_in(accessor, action):
    """Hide inside a container or concealed space."""
    actor_id = action.get("actor_id", "player")
    actor = accessor.get_actor(actor_id)

    if not actor:
        return HandlerResult(
            success=False,
            message="Actor not found."
        )

    # Get target from indirect_object ("in <object>")
    target_entry = action.get("indirect_object")
    if not target_entry:
        return HandlerResult(
            success=False,
            message="Hide in what?"
        )

    # Find hiding spot
    location_id = actor.location
    hiding_spot = _find_entity_in_location(accessor, location_id, target_entry)

    if not hiding_spot:
        return HandlerResult(
            success=False,
            message=f"You don't see {target_entry.word} here."
        )

    # Check if entity allows concealment
    if not hiding_spot.properties.get("allows_concealment", False):
        return HandlerResult(
            success=False,
            message=f"You can't hide in the {hiding_spot.name}."
        )

    # Set concealed state
    actor.properties["focused_on"] = hiding_spot.id
    actor.properties["posture"] = "concealed"

    message = f"You squeeze into the {hiding_spot.name} and remain very still."

    data = {
        "id": hiding_spot.id,
        "name": hiding_spot.name,
        "posture": "concealed",
        "llm_context": hiding_spot.llm_context
    }

    return HandlerResult(success=True, message=message, data=data)
```

**Tests:** Similar structure to take_cover tests.

### 5.4 Implement handle_climb

**File:** `behaviors/core/spatial.py`

**Implementation:**
```python
# Add to VOCABULARY:
{
    "word": "climb",
    "synonyms": ["scale"],
    "object_required": True,
    "llm_context": {
        "traits": ["vertical movement", "climbing"],
        "usage": ["climb <object>"]
    }
}

def handle_climb(accessor, action):
    """Climb a tree, ladder, or wall."""
    actor_id = action.get("actor_id", "player")
    actor = accessor.get_actor(actor_id)

    if not actor:
        return HandlerResult(
            success=False,
            message="Actor not found."
        )

    target_entry = action.get("object")
    if not target_entry:
        return HandlerResult(
            success=False,
            message="Climb what?"
        )

    # Find climbable entity
    location_id = actor.location
    target = _find_entity_in_location(accessor, location_id, target_entry)

    if not target:
        return HandlerResult(
            success=False,
            message=f"You don't see {target_entry.word} here."
        )

    # Check if entity is climbable
    if not target.properties.get("climbable", False):
        return HandlerResult(
            success=False,
            message=f"You can't climb the {target.name}."
        )

    # Set climbing posture
    actor.properties["focused_on"] = target.id
    actor.properties["posture"] = "climbing"

    message = f"You climb up the {target.name}."

    data = {
        "id": target.id,
        "name": target.name,
        "posture": "climbing",
        "llm_context": target.llm_context
    }

    return HandlerResult(success=True, message=message, data=data)
```

**Tests:** Similar structure to take_cover tests.

### 5.5 Phase 5 Deliverables and Success Criteria

**Deliverables:**
1. `posture` property semantics defined
2. `handle_take_cover` implementation
3. `handle_hide_in` implementation
4. `handle_climb` implementation
5. Comprehensive tests for all posture commands
6. Example game demonstrating tactical gameplay
7. All tests pass (minimum 20 new tests for Phase 5)

**Success Criteria:**
- [x] Can take cover behind objects with provides_cover
- [x] Can hide in objects with allows_concealment
- [x] Can climb objects with climbable
- [x] Posture set correctly for each command
- [x] Posture cleared when moving away
- [x] Cannot use posture commands on inappropriate objects
- [x] All existing tests still pass

### Phase 5 Results

**Completion Date:** 2025-12-04

**Implementation Summary:**
1. Defined posture property semantics:
   - Property: `posture` in actor's properties dict
   - Values: null (default), "cover", "concealed", "climbing", or custom
   - Automatically cleared when moving to different entity (only if actual movement)
   - Preserved when examining "any" distance items (no movement)

2. Implemented handle_take_cover (behaviors/core/spatial.py):
   - New verb: "cover" with synonyms "take cover", "hide behind"
   - Requires `provides_cover: true` property on target entity
   - Sets `focused_on` and `posture: "cover"`
   - Works with items and parts

3. Implemented handle_hide_in (behaviors/core/spatial.py):
   - New verb: "hide" with synonym "conceal"
   - Requires `allows_concealment: true` property on target entity
   - Sets `focused_on` and `posture: "concealed"`
   - Supports hiding in containers and concealed spaces

4. Implemented handle_climb (behaviors/core/spatial.py):
   - New verb: "climb"
   - Requires `climbable: true` property on target entity
   - Sets `focused_on` and `posture: "climbing"`
   - Enables vertical positioning

5. Created comprehensive tests (27 new tests):
   - tests/test_posture_property.py (7 tests) - Property semantics and clearing
   - tests/test_take_cover.py (8 tests) - Take cover command
   - tests/test_hide_climb_postures.py (12 tests) - Hide and climb commands

**Test Results:**
- All 27 new Phase 5 tests passing
- All 1,396 total tests passing (27 new + 1,369 existing)
- Zero regressions

**Issues Encountered:**
- None

**Work Deferred:**
- Example game demonstrating tactical gameplay (not essential for core functionality)

---

## Phase 6: Documentation and Polish

**Duration:** 2-3 days
**Goal:** Complete documentation and ensure system is ready for authors

### 6.1 Update Author Documentation

**Files to Create/Update:**
1. `user_docs/authoring_spatial_rooms.md` - Already exists, verify completeness
2. `user_docs/spatial_patterns.md` - Pattern library with examples
3. `user_docs/spatial_troubleshooting.md` - Common mistakes and solutions

**Content to Include:**
- When to create parts (decision flowchart)
- Standard patterns (4 walls, multi-part objects, room areas)
- Universal surface fallback explanation
- Interaction distance usage guide
- Posture system guide (if Phase 5 completed)
- Complete worked examples
- Performance considerations

### 6.2 Create Example Games

**Files to Create:**
1. `examples/spatial_simple/` - Simple room with wall parts
2. `examples/spatial_puzzle/` - Position-dependent puzzle
3. `examples/spatial_combat/` - Tactical combat with cover

Each example should include:
- Complete game.json
- Custom behaviors (if any)
- Test file demonstrating gameplay
- README explaining the example

### 6.3 Update Core Documentation

**Files to Update:**
1. `docs/spatial_structure.md` - Ensure accurate after implementation
2. `CHANGELOG.md` - Document new features
3. `README.md` - Add mention of spatial features

### 6.4 Phase 6 Deliverables and Success Criteria

**Deliverables:**
1. Complete author documentation
2. At least 3 example games
3. Updated core documentation
4. Troubleshooting guide

**Success Criteria:**
- [ ] Authors can understand when to use spatial features
- [ ] Examples demonstrate all major features
- [ ] Documentation accurate and complete
- [ ] Common mistakes documented with solutions

---

## Integration Testing

**File:** `tests/test_spatial_integration.py`

Create comprehensive integration tests that exercise the entire spatial system:

```python
class TestSpatialIntegration(unittest.TestCase):
    """
    Integration tests for complete spatial scenarios.

    Tests realistic gameplay sequences using spatial features.
    """

    def test_wall_mounted_item_puzzle(self):
        """Test complete wall-mounted item puzzle scenario."""
        # Load game with tapestry hiding button on wall
        # 1. Examine wall - see tapestry
        # 2. Examine tapestry - move close
        # 3. Look behind tapestry - reveal button
        # 4. Push button - trigger event
        pass

    def test_multi_part_object_workflow(self):
        """Test multi-part object with position requirements."""
        # Load game with alchemy bench
        # 1. Take herbs
        # 2. Approach left side of bench
        # 3. Grind herbs - succeeds
        # 4. Approach center of bench
        # 5. Mix - succeeds
        pass

    def test_cover_system_workflow(self):
        """Test tactical cover system."""
        # Load game with combat scenario
        # 1. Examine pillar
        # 2. Take cover behind pillar
        # 3. Check posture is "cover"
        # 4. Approach different location
        # 5. Check posture cleared
        pass

    def test_universal_surface_with_override(self):
        """Test universal surface fallback with explicit override."""
        # Load game with one explicit ceiling part, one without
        # 1. In room without ceiling part, examine ceiling - fallback
        # 2. Move to room with ceiling part
        # 3. Examine ceiling - explicit description
        pass
```

---

## Performance Testing

**File:** `tests/test_spatial_performance.py`

Test performance with large numbers of parts:

```python
class TestSpatialPerformance(unittest.TestCase):
    """Performance tests for spatial system."""

    def test_large_part_collection(self):
        """Test performance with 1000 parts."""
        # Create game with 100 locations, each with 10 parts
        # Time: get_part, get_parts_of, get_entity
        # Verify acceptable performance
        pass

    def test_entity_resolution_with_parts(self):
        """Test entity resolution speed with many parts."""
        # Create game with many entities
        # Time: _find_entity_in_location
        # Verify no significant slowdown
        pass
```

---

## Migration and Backward Compatibility

### Existing Games

**Guarantee:** All existing games work unchanged.

**Why:** Parts are optional. Games without parts:
- Load successfully (empty parts list)
- All existing features work
- No performance impact
- No breaking changes

**Tests to Verify:**
```python
# tests/test_backward_compatibility.py

class TestBackwardCompatibility(unittest.TestCase):
    """
    Test that existing games without parts work unchanged.

    Critical for ensuring no breaking changes to existing content.
    """

    def test_game_without_parts_field_loads(self):
        """Test game JSON without 'parts' field loads successfully."""
        game_json = {
            "metadata": {
                "title": "Legacy Game",
                "start_location": "loc_start"
            },
            "locations": [
                {
                    "id": "loc_start",
                    "name": "Start Room",
                    "description": "A starting room",
                    "exits": {}
                }
            ],
            "items": [
                {
                    "id": "item_key",
                    "name": "key",
                    "description": "A brass key",
                    "location": "loc_start"
                }
            ],
            "actors": {},
            "locks": []
            # Note: No 'parts' field - should default to empty list
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(game_json, f)
            temp_path = f.name

        try:
            game_state = load_game_state(temp_path)

            # Should load successfully
            self.assertIsNotNone(game_state)

            # Parts should be empty list
            self.assertEqual(len(game_state.parts), 0)

            # Other entities should load normally
            self.assertEqual(len(game_state.locations), 1)
            self.assertEqual(len(game_state.items), 1)

        finally:
            os.unlink(temp_path)

    def test_game_with_empty_parts_list(self):
        """Test game with explicit empty parts list."""
        game_json = {
            "metadata": {"title": "Test", "start_location": "loc_1"},
            "locations": [{"id": "loc_1", "name": "Room", "description": "A room"}],
            "items": [],
            "actors": {},
            "locks": [],
            "parts": []  # Explicit empty list
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(game_json, f)
            temp_path = f.name

        try:
            game_state = load_game_state(temp_path)
            self.assertEqual(len(game_state.parts), 0)
        finally:
            os.unlink(temp_path)

    def test_examine_works_without_parts(self):
        """Test examine command works normally without any parts."""
        from behaviors.core.perception import handle_examine

        metadata = Metadata(title="Test", start_location="loc_room")
        location = Location(id="loc_room", name="Room", description="A room")
        item = Item(
            id="item_table",
            name="table",
            description="A wooden table",
            location="loc_room"
        )

        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[item],
            actors={"player": Actor(id="player", name="Player", location="loc_room")},
            locks=[],
            parts=[]  # No parts
        )

        accessor = StateAccessor(game_state, None)

        action = {
            "verb": "examine",
            "object": WordEntry(word="table"),
            "actor_id": "player"
        }

        result = handle_examine(accessor, action)

        # Should work exactly as before
        self.assertTrue(result.success)
        self.assertIn("table", result.message.lower())

        # Should not set focused_on (default interaction_distance is "any")
        player = accessor.get_actor("player")
        self.assertIsNone(player.properties.get("focused_on"))

    def test_take_command_works_without_parts(self):
        """Test take command unaffected by parts system."""
        from behaviors.core.manipulation import handle_take

        metadata = Metadata(title="Test", start_location="loc_room")
        location = Location(id="loc_room", name="Room", description="A room")
        item = Item(
            id="item_key",
            name="key",
            description="A key",
            location="loc_room",
            properties={"portable": True}
        )

        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[item],
            actors={"player": Actor(id="player", name="Player", location="loc_room")},
            locks=[],
            parts=[]  # No parts
        )

        accessor = StateAccessor(game_state, None)

        action = {
            "verb": "take",
            "object": WordEntry(word="key"),
            "actor_id": "player"
        }

        result = handle_take(accessor, action)

        # Should work normally
        self.assertTrue(result.success)
        self.assertEqual(item.location, "player")

    def test_existing_game_state_serialization(self):
        """Test that games without parts serialize correctly."""
        metadata = Metadata(title="Test", start_location="loc_room")
        location = Location(id="loc_room", name="Room", description="A room")

        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[],
            actors={"player": Actor(id="player", name="Player", location="loc_room")},
            locks=[],
            parts=[]  # Empty parts - should not appear in output or be minimal
        )

        # Serialize to dict (for save file)
        # Implementation depends on your save system
        # This is a placeholder showing the concept

        # Should be able to serialize without errors
        # Parts field should either not appear or be empty list
        pass

    def test_state_accessor_methods_safe_with_no_parts(self):
        """Test StateAccessor part methods safe when no parts exist."""
        metadata = Metadata(title="Test", start_location="loc_room")
        location = Location(id="loc_room", name="Room", description="A room")

        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[],
            actors={"player": Actor(id="player", name="Player", location="loc_room")},
            locks=[],
            parts=[]  # No parts
        )

        accessor = StateAccessor(game_state, None)

        # All part methods should handle empty parts gracefully
        part = accessor.get_part("nonexistent")
        self.assertIsNone(part)

        parts = accessor.get_parts_of("loc_room")
        self.assertEqual(parts, [])

        items_at_part = accessor.get_items_at_part("nonexistent")
        self.assertEqual(items_at_part, [])

        # get_entity should still work for non-part entities
        loc = accessor.get_entity("loc_room")
        self.assertIsNotNone(loc)
        self.assertEqual(loc.id, "loc_room")

    def test_validation_passes_with_no_parts(self):
        """Test validation succeeds for games without parts."""
        metadata = Metadata(title="Test", start_location="loc_room")
        location = Location(id="loc_room", name="Room", description="A room")
        item = Item(
            id="item_key",
            name="key",
            description="A key",
            location="loc_room"
        )

        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[item],
            actors={"player": Actor(id="player", name="Player", location="loc_room")},
            locks=[],
            parts=[]  # No parts
        )

        errors = validate_game_state(game_state)

        # Should have no errors
        self.assertEqual(errors, [])

    def test_performance_no_regression_without_parts(self):
        """Test no performance impact for games not using parts."""
        import time

        # Create a moderately-sized game without parts
        metadata = Metadata(title="Test", start_location="loc_1")

        locations = []
        items = []
        for i in range(50):
            loc = Location(
                id=f"loc_{i}",
                name=f"Room {i}",
                description=f"Room number {i}"
            )
            locations.append(loc)

            # Add items to each location
            for j in range(10):
                item = Item(
                    id=f"item_{i}_{j}",
                    name=f"item {j}",
                    description=f"Item {j} in room {i}",
                    location=f"loc_{i}"
                )
                items.append(item)

        game_state = GameState(
            metadata=metadata,
            locations=locations,
            items=items,
            actors={"player": Actor(id="player", name="Player", location="loc_1")},
            locks=[],
            parts=[]  # No parts
        )

        accessor = StateAccessor(game_state, None)

        # Time common operations
        start = time.time()
        for _ in range(1000):
            # Entity lookup
            item = accessor.get_item("item_25_5")
            loc = accessor.get_location("loc_30")

            # get_entity (which now checks parts too)
            entity = accessor.get_entity("item_25_5")

        elapsed = time.time() - start

        # Should complete quickly (< 1 second for 1000 iterations)
        # This is a rough benchmark - adjust threshold as needed
        self.assertLess(elapsed, 1.0,
                       f"Performance regression detected: {elapsed:.3f}s for 1000 ops")

    def test_items_at_location_not_confused_with_parts(self):
        """Test items in locations not confused with items at parts."""
        metadata = Metadata(title="Test", start_location="loc_room")
        location = Location(id="loc_room", name="Room", description="A room")

        item1 = Item(
            id="item_table",
            name="table",
            description="A table",
            location="loc_room"
        )
        item2 = Item(
            id="item_key",
            name="key",
            description="A key",
            location="loc_room"
        )

        game_state = GameState(
            metadata=metadata,
            locations=[location],
            items=[item1, item2],
            actors={"player": Actor(id="player", name="Player", location="loc_room")},
            locks=[],
            parts=[]  # No parts
        )

        accessor = StateAccessor(game_state, None)

        # Items should be findable at location
        items_in_room = [i for i in game_state.items if i.location == "loc_room"]
        self.assertEqual(len(items_in_room), 2)

        # No items at any part
        items_at_parts = [i for i in game_state.items
                         if i.location.startswith("part_")]
        self.assertEqual(len(items_at_parts), 0)
```

---

## Progress Tracking Template

For each phase, track:

### Phase X: [Name]

**Started:** [Date]
**Completed:** [Date]
**Actual Duration:** [X days]

**Progress:**
- [x] Task 1
- [x] Task 2
- [ ] Task 3 (deferred - see below)

**Issues Encountered:**
1. Issue description
   - Solution: ...
   - Time impact: +X hours

2. Issue description
   - Solution: ...

**Work Deferred:**
1. Feature X - Reason: Y
   - Moved to: Phase Z

**Lessons Learned:**
- Lesson 1
- Lesson 2

**Test Results:**
- Tests written: X
- Tests passing: Y
- Coverage: Z%

---

## Total Effort Estimate

**Core Implementation (Phases 1-4):**
- Phase 1: 3-4 days
- Phase 2: 3-4 days
- Phase 3: 2-3 days
- Phase 4: 2 days
**Subtotal: 10-13 days (2-2.5 weeks)**

**Optional Features (Phase 5):**
- Phase 5: 2-3 days

**Documentation (Phase 6):**
- Phase 6: 2-3 days

**Integration & Testing:**
- Integration tests: 1 day
- Performance tests: 0.5 days
- Bug fixes: 1-2 days

**Total Estimate: 15-22 days (3-4.5 weeks)**

**Critical Path:** Phases 1 → 2 → 3 are sequential. Phase 4 can overlap with Phase 3. Phase 5 is optional. Phase 6 should be last.

---

## Success Criteria Summary

**System is ready for release when:**

1. **All Phase 1-4 tests pass** (minimum 70 tests)
2. **Backward compatibility verified** (existing games unchanged)
3. **Documentation complete** (author guide, examples, patterns)
4. **Examples working** (at least 3 example games)
5. **Integration tests pass** (realistic scenarios work)
6. **Performance acceptable** (no significant slowdown)
7. **Code reviewed** (follows project standards)
8. **Design documents accurate** (reflect actual implementation)

---

## Notes

- This is a living document - update after each phase
- Track actual time vs estimates to improve future planning
- Document all deviations from the plan
- Review and discuss if any phase becomes unexpectedly complex
- Maintain test discipline - never proceed without passing tests
