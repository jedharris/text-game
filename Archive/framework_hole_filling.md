# Framework Hole Filling

Implementation plan for missing framework capabilities identified during big game design.

## Overview

This document covers implementations needed in the game engine or behavior libraries. Custom game behaviors specific to the big game are deferred to [big_game_implementation.md](big_game_implementation.md).

---

## 0. Add "about" Preposition (Minor Core Change)

### Goal
Add "about" to the base vocabulary prepositions to support dialog commands like "ask X about Y".

### Change
Add "about" to the prepositions list in `src/vocabulary.json`.

### Rationale
Required for the dialog library to parse `ask NPC about topic` commands.

### Estimated Effort
Trivial - 5 minutes

---

## 1. Turn Counter (Engine Extension)

### Goal
Add a global turn counter to GameState that increments after each successful command.

### Use Cases
- Time-pressure mechanics ("cure the scholar within 50 turns")
- Scheduled events ("spore spread worsens at turn 100")
- Turn-based ability cooldowns
- Statistics tracking

### Design

**Changes to state_manager.py:**
```python
@dataclass
class GameState:
    ...
    turn_count: int = 0

    def increment_turn(self) -> int:
        """Increment and return new turn count."""
        self.turn_count += 1
        return self.turn_count
```

**Changes to serialization:**
- Add `turn_count` to `_serialize_game_state()`
- Add `turn_count` to `load_game_state()` parsing

**Changes to llm_protocol.py:**
- Call `state.increment_turn()` at start of `_fire_turn_phases()`

### Testing
- Test turn increments on successful commands
- Test turn does NOT increment on failed commands
- Test serialization/deserialization preserves turn count
- Test turn count accessible from behaviors

### Estimated Effort
Small - ~2 hours including tests

---

## 2. Scheduled Events Library

### Goal
Allow scheduling events to fire at specific turn counts.

### Use Cases
- "If spore mother not healed by turn 100, infection spreads to town"
- "Merchant caravan arrives at turn 50"
- "Weather changes every 20 turns"

### Design

**Location:** `behavior_libraries/timing_lib/`

**Files:**
- `__init__.py` - Module init and vocabulary
- `scheduled_events.py` - Core scheduling logic

**API:**
```python
def schedule_event(state, event_name: str, trigger_turn: int, data: dict = None):
    """Schedule an event to fire at a specific turn."""

def cancel_event(state, event_name: str):
    """Cancel a scheduled event by name."""

def get_scheduled_events(state) -> list[dict]:
    """Get all scheduled events."""

def on_check_scheduled_events(entity, state, context) -> EventResult:
    """Turn phase handler - check and fire due events."""
```

**Storage:** Uses `state.extra["scheduled_events"]` list

**Event structure:**
```python
{
    "id": "unique_id",
    "event": "on_spore_spread",
    "turn": 100,
    "data": {"severity": "high"},
    "repeating": False,  # Optional: if True, reschedules after firing
    "interval": None     # For repeating events
}
```

**Vocabulary:**
```python
vocabulary = {
    "hooks": {
        "condition_tick": "on_check_scheduled_events"  # Piggyback on existing hook
    }
}
```

### Dependencies
- Requires turn counter (item 1)

### Testing
- Test event scheduling and firing at correct turn
- Test event cancellation
- Test repeating events
- Test multiple events at same turn
- Test event data passed correctly

### Estimated Effort
Medium - ~4 hours including tests

---

## 3. Darkness/Visibility Library

### Goal
Implement darkness mechanics where certain locations require light to see/interact.

### Use Cases
- Deep caves requiring torches
- Underground areas with bioluminescence
- Night-time outdoor areas

### Design

**Location:** `behavior_libraries/darkness_lib/`

**Files:**
- `__init__.py` - Module init and vocabulary
- `visibility.py` - Core visibility logic

**API:**
```python
def check_visibility(accessor, location_id: str) -> bool:
    """Check if location has sufficient light."""

def get_light_sources(accessor, location_id: str) -> list:
    """Get all active light sources in location."""

def on_visibility_check(entity, state, context) -> EventResult:
    """Hook handler - block actions in darkness."""

def get_darkness_description(accessor, location_id: str) -> str:
    """Get description for dark location."""
```

**Location properties:**
```json
{
  "requires_light": true,
  "ambient_light": false,
  "darkness_description": "You can't see anything in the absolute darkness."
}
```

**Item properties:**
```json
{
  "provides_light": true,
  "light_radius": 1
}
```

**Integration:**
- Hook into `VISIBILITY_CHECK` hook
- Affects: examine, take, attack, use (configurable)
- Does NOT affect: go, inventory, drop (can do in dark)

**Vocabulary:**
```python
vocabulary = {
    "hooks": {
        "visibility_check": "on_visibility_check"
    }
}
```

### Testing
- Test visibility check with/without light
- Test player-carried light sources
- Test location-based light sources
- Test actions blocked in darkness
- Test actions allowed in darkness
- Test ambient light locations

### Estimated Effort
Medium - ~4 hours including tests

---

## 4. Companion Following Library

### Goal
Allow domesticated creatures and befriended NPCs to follow the player between locations.

### Use Cases
- Wolf pack following player after domestication
- Hunter Sira as traveling companion
- Steam salamanders providing warmth aura while following

### Design

**Location:** `behavior_libraries/companion_lib/`

**Files:**
- `__init__.py` - Module init and vocabulary
- `following.py` - Core following logic
- `restrictions.py` - Movement restriction handling

**API:**
```python
def get_companions(accessor) -> list[Actor]:
    """Get all actors marked as companions."""

def make_companion(accessor, actor_id: str):
    """Mark an actor as a companion."""

def dismiss_companion(accessor, actor_id: str):
    """Remove companion status from an actor."""

def on_player_move(entity, state, context) -> EventResult:
    """Hook handler - companions follow player."""

def check_can_follow(accessor, companion, destination: str) -> tuple[bool, str]:
    """Check if companion can follow to destination."""
```

**Actor properties:**
```json
{
  "is_companion": true,
  "location_restrictions": ["civilized_remnants_gate"],
  "terrain_restrictions": ["underwater"],
  "follow_message": "The wolf pack lopes along beside you.",
  "cannot_follow_message": "The wolves won't enter the town."
}
```

**Integration:**
- Hook into `LOCATION_ENTERED` hook
- Fire after player successfully moves
- Generate messages for companions following/staying

**Vocabulary:**
```python
vocabulary = {
    "hooks": {
        "location_entered": "on_player_move_companions_follow"
    }
}
```

### Companion Behavior Extensions
- Companions in combat (loyalty threshold from relationships)
- Companion dismissal commands
- Companion wait/follow commands

### Testing
- Test companion follows player
- Test location restrictions prevent following
- Test terrain restrictions
- Test multiple companions
- Test companion messages
- Test make/dismiss companion

### Estimated Effort
Medium - ~5 hours including tests

---

## 5. NPC Movement/Patrol Library

### Goal
Allow NPCs to move between locations on their own schedule (patrol routes, wandering).

### Use Cases
- Hunter Sira wandering through Beast Wilds
- Guard patrols in Civilized Remnants
- Merchant moving between market locations

### Design

**Location:** `behavior_libraries/npc_movement_lib/`

**Files:**
- `__init__.py` - Module init and vocabulary
- `patrol.py` - Fixed route patrol logic
- `wander.py` - Random wandering logic

**API:**
```python
def patrol_step(accessor, actor) -> str | None:
    """Move actor one step along patrol route. Returns message or None."""

def wander_step(accessor, actor) -> str | None:
    """Move actor to random adjacent location. Returns message or None."""

def on_npc_movement(entity, state, context) -> EventResult:
    """Turn phase handler - process NPC movement."""

def set_patrol_route(accessor, actor_id: str, route: list[str]):
    """Set patrol route for an actor."""

def set_wander_area(accessor, actor_id: str, locations: list[str]):
    """Set allowed wander locations for an actor."""
```

**Actor properties:**
```json
{
  "patrol_route": ["forest_edge", "wolf_clearing", "bee_grove"],
  "patrol_index": 0,
  "patrol_frequency": 3
}
```

Or for wandering:
```json
{
  "wander_area": ["forest_edge", "wolf_clearing", "bee_grove", "predator_den"],
  "wander_frequency": 2,
  "wander_chance": 0.5
}
```

**Integration:**
- Hook into `NPC_ACTION` turn phase
- Process after NPC combat actions
- Respect patrol_frequency (move every N turns)

**Vocabulary:**
```python
vocabulary = {
    "hooks": {
        "npc_action": "on_npc_movement"
    }
}
```

### Testing
- Test patrol route cycling
- Test patrol frequency
- Test wander randomness within area
- Test wander chance
- Test NPC visible when entering player's location
- Test NPC leaving player's location

### Estimated Effort
Medium - ~5 hours including tests

---

## 6. Crafting/Combining Library

### Goal
Allow combining items to create new items, optionally with location/skill requirements.

### Use Cases
- Repair telescope with components at observatory
- Combine herbs to create potions
- Assemble breathing apparatus from parts

### Design

**Location:** `behavior_libraries/crafting_lib/`

**Files:**
- `__init__.py` - Module init and vocabulary
- `recipes.py` - Recipe matching and execution
- `handlers.py` - Command handlers for combine/craft verbs

**API:**
```python
def find_recipe(accessor, item_ids: list[str]) -> dict | None:
    """Find recipe matching given items."""

def check_requirements(accessor, recipe: dict) -> tuple[bool, str]:
    """Check if recipe requirements are met (location, skill, etc.)."""

def execute_craft(accessor, recipe: dict, item_ids: list[str]) -> EventResult:
    """Execute crafting: consume ingredients, create result."""

def handle_combine(entity, state, context) -> EventResult:
    """Handler for 'combine X with Y' command."""

def handle_craft(entity, state, context) -> EventResult:
    """Handler for 'craft X' command (uses recipe by name)."""
```

**Recipe storage (in game_state.json `extra`):**
```json
{
  "extra": {
    "recipes": {
      "working_telescope": {
        "ingredients": ["crystal_lens", "mounting_bracket", "cleaning_supplies"],
        "creates": "working_telescope",
        "requires_location": "frozen_observatory",
        "requires_skill": null,
        "consumes_ingredients": true,
        "success_message": "You carefully assemble the telescope components. The ancient device hums to life."
      },
      "healing_potion": {
        "ingredients": ["silvermoss", "clean_water"],
        "creates": "healing_potion",
        "requires_location": null,
        "requires_skill": "herbalism",
        "consumes_ingredients": true,
        "success_message": "You brew a healing potion from the ingredients."
      }
    }
  }
}
```

**Result item handling:**
- If result item doesn't exist in game_state, create from template
- Template can be in recipe or in separate items list

**Vocabulary:**
```python
vocabulary = {
    "verbs": [
        {"word": "combine", "synonyms": ["mix", "merge"]},
        {"word": "craft", "synonyms": ["create", "make", "build", "assemble"]}
    ],
    "handlers": {
        "combine": "handle_combine",
        "craft": "handle_craft"
    }
}
```

### Command Patterns
- `combine lens with bracket` - Two specific items
- `combine lens, bracket, supplies` - Multiple items
- `craft telescope` - By recipe name (looks up required items)

### Testing
- Test recipe matching
- Test ingredient consumption
- Test location requirements
- Test skill requirements
- Test result item creation
- Test failure messages
- Test combine vs craft commands

### Estimated Effort
Medium-Large - ~6 hours including tests

---

## 7. Dialog/Conversation Library

### Goal
Manage the **game state consequences** of NPC conversations. The LLM handles narration; this library handles mechanics.

### What This Library Does (Framework Responsibility)
- Track which topics have been discussed
- Manage topic prerequisites (flags, items, relationship levels)
- Execute state changes when topics are discussed (set flags, unlock topics, grant items)
- Determine which topics are currently available to discuss

### What This Library Does NOT Do (LLM Responsibility)
- Generate natural language responses
- Handle conversational nuance or tone
- Determine how NPCs express information

### Use Cases
- Ask Scholar Aldric about infection → **sets flag** `knows_about_infection`, **unlocks** cure topic
- Ask healer about rare herbs → **sets flag** `knows_silvermoss_location`
- Topic availability based on game state (flags, items held, relationship level)

### Design

**Location:** `behavior_libraries/dialog_lib/`

**Files:**
- `__init__.py` - Module init and vocabulary
- `topics.py` - Topic management and queries
- `handlers.py` - Command handlers for ask/talk verbs

**API:**
```python
def get_available_topics(accessor, npc) -> list[str]:
    """Get topics NPC can currently discuss."""

def get_topic_hints(accessor, npc) -> list[str]:
    """Get hint text for available topics."""

def handle_ask_about(accessor, npc, topic: str) -> EventResult:
    """Process asking NPC about a topic."""

def handle_talk_to(accessor, npc) -> EventResult:
    """Process general talk - shows available topics."""
```

**NPC configuration:**
```json
{
  "id": "scholar_aldric",
  "properties": {
    "dialog_topics": {
      "infection": {
        "keywords": ["infection", "sick", "illness", "spores"],
        "summary": "Aldric explains that spores are everywhere and he has been studying them.",
        "unlocks_topics": ["cure", "spore_mother"],
        "sets_flags": {"knows_about_infection": true},
        "requires_flags": {}
      },
      "cure": {
        "keywords": ["cure", "treatment", "heal", "remedy"],
        "summary": "Aldric reveals that silvermoss slows infection, but heartmoss from deep caves is needed for a true cure.",
        "unlocks_topics": ["heartmoss"],
        "sets_flags": {"knows_about_silvermoss": true, "knows_heartmoss_location": true},
        "requires_flags": {}
      },
      "spore_mother": {
        "keywords": ["spore mother", "source", "origin"],
        "summary": "Aldric speaks of an ancient creature in the depths - the source of all the spores.",
        "sets_flags": {"knows_about_spore_mother": true},
        "requires_flags": {}
      }
    },
    "default_topic_summary": "Aldric doesn't know about that topic."
  }
}
```

**Note:** The `summary` field describes what information is conveyed. The LLM uses this to narrate the conversation naturally - it is NOT literal dialog text.

**Topic structure:**
- `keywords` - Words/phrases that match this topic (case-insensitive)
- `summary` - What information is conveyed (displayed in text_game, narrated by LLM)
- `unlocks_topics` - Topics now available after discussion
- `sets_flags` - Flags to set when topic discussed
- `requires_flags` - Flags needed to access topic
- `requires_items` - Items player must have (optional)
- `grants_items` - Items given to player (optional)
- `one_time` - If true, topic disappears after use (optional)

### Implementation Notes

**Keyword matching approach:**
1. Parser handles `ask NPC about X` using the "about" preposition (added in item 0)
2. Topic text is extracted from raw input after the preposition
3. Keywords are matched against extracted text (case-insensitive substring matching)
4. Keywords can be multi-word phrases (e.g., "spore mother")
5. Topic keywords do NOT need to be in game vocabulary - matching is independent

**Dual-mode output:**
- `summary` field serves both text_game and LLM game
- text_game: displays summary verbatim as response
- LLM game: passes summary to LLM for narrated elaboration

**Vocabulary:**
```python
vocabulary = {
    "verbs": [
        {"word": "ask", "synonyms": ["inquire", "question"]},
        {"word": "talk", "synonyms": ["speak", "converse", "chat"]}
    ],
    "handlers": {
        "ask": "handle_ask",
        "talk": "handle_talk"
    }
}
```

### Command Patterns
- `ask aldric about infection`
- `talk to aldric` (lists available topics)
- `ask about cure` (if only one NPC present)

### Testing
- Test topic availability with/without prerequisites
- Test topic unlocking
- Test flag setting
- Test keyword matching
- Test default response
- Test one-time topics

### Estimated Effort
Medium-Large - ~6 hours including tests

---

## Implementation Order

Based on dependencies and priority for big game:

### Phase 1: Foundation
1. **Turn Counter** (no dependencies, enables scheduled events)

### Phase 2: Core Libraries
2. **Companion Following** (needed for wolf pack, hunter companion)
3. **Crafting Library** (telescope repair, potions)
4. **Darkness/Visibility** (cave exploration)

### Phase 3: Enhancement Libraries
5. **NPC Movement/Patrol** (hunter Sira wandering)
6. **Scheduled Events** (requires turn counter)
7. **Dialog Library** (richer NPC interaction)

---

## Total Estimated Effort

Estimates assume Claude Code implementation with human review.

| Item | Session Time |
|------|-------------|
| Turn Counter | ~1 hour |
| Scheduled Events | ~1.5 hours |
| Darkness/Visibility | ~1.5 hours |
| Companion Following | ~2 hours |
| NPC Movement/Patrol | ~2 hours |
| Crafting Library | ~2 hours |
| Dialog Library | ~2 hours |
| **Total** | **~12 hours** |

*Session time = active Claude Code interaction including design discussion, implementation, and testing. Does not include breaks or context switching.*

---

## Testing Strategy

Each library should have:
1. Unit tests for all API functions
2. Integration tests showing typical usage patterns
3. Edge case tests (empty inputs, missing data, etc.)

All tests should follow existing test patterns using unittest.
