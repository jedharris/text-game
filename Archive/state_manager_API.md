# Game State API Specification

This document defines the runtime API surface for interacting with parsed game
state objects inside the engine. It assumes the loader/serializer described in
`docs/state_manager_plan.md` produces a `GameState` aggregate composed of the
dataclasses outlined there.

## 1. Core Interfaces

### 1.1 `GameState`

Represents the entire world plus mutable runtime state.

```python
class GameState:
    metadata: Metadata
    vocabulary: Vocabulary
    locations: List[Location]  # Array of locations with unique IDs
    doors: List[Door]
    items: List[Item]
    locks: List[Lock]  # Array of locks with unique IDs
    npcs: List[NPC]
    scripts: List[Script]
    player: PlayerState

    def get_location(self, location_id: str) -> Location: ...
    def get_item(self, item_id: str) -> Item: ...
    def get_door(self, door_id: str) -> Door: ...
    def get_lock(self, lock_id: str) -> Lock: ...
    def get_npc(self, npc_id: str) -> NPC: ...
    def move_item(self, item_id: str, *, to_location: str | None = None,
                  to_container: str | None = None,
                  to_player: bool = False,
                  to_npc: str | None = None) -> None: ...
    def set_player_location(self, location_id: str) -> None: ...
    def set_flag(self, name: str, value: Any) -> None: ...
    def get_flag(self, name: str, default: Any = None) -> Any: ...
    def clone(self) -> GameState: ...
    def build_id_registry(self) -> Dict[str, str]: ...
```

* `locations`, `locks`, etc. are arrays (not dicts) indexed by internal unique IDs.
* `player` captures live status (current location, inventory, stats).
* `flags` (within `PlayerState` or GameState-level) store arbitrary state (e.g.,
  puzzles solved).
* Provide helpers like `get_location`, `get_lock`, etc. for safe lookup by ID with errors if not found.
* `build_id_registry()` returns a dict mapping all IDs to their entity type for validation.

### 1.2 `Location`

Includes static description plus dynamic lists of items/NPCs present.

```python
class Location:
    id: str
    name: str
    description: str
    tags: Set[str]
    exits: Dict[str, ExitDescriptor]
    items: List[str]
    npcs: List[str]

    def has_exit(self, direction: str) -> bool: ...
    def resolve_exit(self, direction: str) -> ExitDescriptor | None: ...
```

### 1.3 `ExitDescriptor`

```python
class ExitDescriptor:
    type: ExitType
    to: Optional[str]
    door_id: Optional[str]
    description: Optional[str]
    hidden: bool
    conditions: List[str]
    on_fail: Optional[str]

    def is_available(self, state: GameState) -> bool: ...
```

### 1.4 `Door`

```python
class Door:
    id: str
    locations: Tuple[str, ...]
    description: str
    locked: bool
    lock_id: Optional[str]
    open: bool
    one_way: bool

    def unlock(self, key_item_id: Optional[str], state: GameState) -> bool: ...
    def lock(self) -> None: ...
    def open_door(self) -> None: ...
    def close_door(self) -> None: ...
```

Door methods should update linked exits/locations as needed.

### 1.5 `Item`

```python
class Item:
    id: str
    name: str
    description: str
    type: ItemType
    portable: bool
    location: str  # location id, container item id, "player", or npc id
    states: Dict[str, Any]
    container: Optional[ContainerInfo]

    def is_accessible(self, state: GameState) -> bool: ...
    def add_state(self, key: str, value: Any) -> None: ...
```

**Item Location Field Format (V2.0 ID Design):**
- Location ID: `"loc_1"` - item is in that location
- Container item ID: `"item_5"` - item is inside that container item
- Player inventory: `"player"` - item is in player's inventory (reserved ID)
- NPC inventory: `"npc_3"` - item is held by that NPC (NPC ID directly, no prefix!)

All entity IDs are globally unique (including `"player"` which is reserved). **No prefixes like `"inventory:"` are used.** The validator checks that the referenced ID exists in the global ID registry and is an appropriate entity type (location, item, NPC, or the special `"player"` ID).

`ContainerInfo` exposes methods to add/remove contents, lock/unlock, etc.

### 1.6 `Lock`

```python
class Lock:
    id: str
    opens_with: List[str]
    auto_unlock: bool
    description: str
    fail_message: str

    def can_unlock(self, state: GameState, key_id: Optional[str] = None) -> bool: ...
```

### 1.7 `NPC`

Holds location reference, dialogue, states, and optional behavior hooks.

### 1.8 `PlayerState`

```python
class PlayerState:
    location: str  # Current location ID (matches Item.location field naming)
    inventory: List[str]  # List of item IDs in player's inventory
    flags: Dict[str, Any]  # Arbitrary game state flags
    stats: Dict[str, int]  # Player statistics (health, score, etc.)
```

Expose helpers for inventory management, stats adjustments, etc.

## 2. Mutation API

Provide high-level commands that encapsulate typical gameplay operations:

* `GameState.move_player(direction: str) -> MoveResult`
  * Resolves exits, checks doors/locks, updates player location, returns outcome.
* `GameState.set_player_location(location_id: str) -> None`
  * Directly sets player location (for teleportation, debugging, or initialization).
* `GameState.take_item(item_id: str) -> ActionResult`
  * Validates accessibility, portability, updates location/inventory.
* `GameState.use_item(item_id: str, target_id: Optional[str]) -> ActionResult`
  * Delegates to item-specific logic or script system.
* `GameState.apply_script(script_id: str) -> ActionResult`
  * Executes scripted effects (state mutations, messaging).

Each `ActionResult` includes:
```python
class ActionResult:
    success: bool
    messages: List[str]
    state_changes: Dict[str, Any]
```

## 3. Query Helpers

To drive UI/rendering:

* `GameState.describe_current_location(use_llm: bool = False) -> str`
  * Collates base description, items, exits, NPCs.
* `GameState.list_available_actions() -> List[str]`
  * Derived from exits, items, scripts.
* `GameState.get_inventory_descriptions() -> List[str]`

## 4. Serialization Hooks

* `GameState.to_dict()` / `.to_json()` – delegate to serializer module.
* `GameState.from_dict(data)` – convenience constructor.
* `GameState.snapshot()` – returns serializable dict capturing dynamic state
  (player location, inventory, door states, flags) for save games.
* `GameState.apply_snapshot(snapshot)` – restore from saved state.

## 5. Event & Script Integration

* Provide observer hooks: `GameState.subscribe(event_type, callback)` for engine
  systems (UI, audio).
* Script execution context receives references to `GameState`, `PlayerState`, and
  helper functions (e.g., `set_flag`, `give_item`).

## 6. Error Handling

* All mutating methods raise `StateError` on invalid operations (e.g., moving
  through a locked door without a key).
* Non-critical issues (e.g., attempting to pick up non-portable scenery) should
  return `ActionResult` with `success=False` and explanatory message.

## 7. Thread Safety & Concurrency

* Assume single-threaded gameplay by default.
* If asynchronous operations are added later (e.g., network play), wrap
  `GameState` access with locks or provide immutable snapshot clones.

## 8. Example Usage

```python
state = load_game_state("data/world.json")
result = state.move_player("north")
if result.success:
    print(state.describe_current_location())
else:
    print(result.messages[0])
```

This API ensures the engine can reason about world structure, apply player
actions, update state, trigger scripts, and serialize progress consistently.
