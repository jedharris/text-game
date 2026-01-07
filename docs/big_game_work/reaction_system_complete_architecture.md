# Reaction System: Complete Architecture Specification

**Status:** Architecture Specification (Complete)
**Date:** 2026-01-07
**Purpose:** Define complete property-based reaction system with all integration points
**Supersedes:** reaction_system_architecture.md (incomplete)

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Separation](#component-separation)
3. [Directory Structure](#directory-structure)
4. [Integration Flow](#integration-flow)
5. [Component Specifications](#component-specifications)
6. [Migration Requirements](#migration-requirements)
7. [Validation Requirements](#validation-requirements)
8. [Success Criteria](#success-criteria)

---

## Architecture Overview

### Core Principle

**Three-Layer Architecture: Commands → Hooks → Reactions**

```
Layer 1: COMMANDS (behavior_libraries/command_lib/)
  - Define game verbs (ask, talk, attack, use)
  - Parse user input
  - Fire hooks on target entities
  - Convert EventResult → HandlerResult
  - NO entity property lookups
  - NO business logic

Layer 2: HOOKS (engine infrastructure)
  - Hook definitions in vocabulary
  - Broadcast to subscribers
  - Invoke behavior: invoke_behavior(entity, hook_id, accessor, context)

Layer 3: REACTIONS (game-specific infrastructure)
  - Subscribe to hooks via vocabulary events
  - Check entity properties for reaction configs
  - Dispatch to unified interpreter OR custom handlers
  - Return EventResult with feedback
```

**Key Design Decisions:**

1. **Commands are general-purpose** → `behavior_libraries/command_lib/`
2. **Reaction infrastructure is general-purpose** → `behavior_libraries/reaction_lib/`
3. **Hook subscriptions are game-specific** → `examples/big_game/behaviors/shared/infrastructure/`
4. **Entity handlers are game-specific** → `examples/big_game/behaviors/regions/`

---

## Component Separation

### Commands vs Reactions

| Aspect | Commands | Reactions |
|--------|----------|-----------|
| **Location** | `behavior_libraries/command_lib/` | `game/behaviors/shared/infrastructure/` |
| **Purpose** | Parse input → Fire hooks | Listen to hooks → Execute logic |
| **Input** | User command string | Hook event with context |
| **Output** | HandlerResult | EventResult |
| **Knows About** | Parser, hooks, serialization | Entity properties, handlers, interpreter |
| **Does NOT Know** | Entity properties, game logic | User input format, commands |

**Example: Dialog System**

```
COMMAND (command_lib/dialog.py):
  - Defines: ask, talk verbs
  - Parses: "ask maren about trade"
  - Finds: NPC named "maren"
  - Fires: entity_dialog hook on maren
  - Returns: HandlerResult to game engine

REACTION (infrastructure/dialog_reactions.py):
  - Subscribes: to entity_dialog hook
  - Checks: maren.properties.dialog_reactions
  - Loads: handler from handler path
  - Calls: handler(maren, accessor, context)
  - Returns: EventResult to command
```

---

## Directory Structure

### Complete Layout

```
behavior_libraries/                    # GENERAL-PURPOSE LIBRARIES
│
├── reaction_lib/                      # Core reaction system
│   ├── __init__.py                    # Exports: process_reaction, EFFECT_REGISTRY, etc.
│   ├── interpreter.py                 # Unified interpreter: process_reaction()
│   ├── effects.py                     # Effect handlers registry (18 effects)
│   ├── conditions.py                  # Condition checkers registry (5 conditions)
│   ├── specs.py                       # ReactionSpec definitions (12 types)
│   ├── match_strategies.py            # Matching logic (keywords, items, etc.)
│   ├── message_templates.py           # Template substitution engine
│   └── dispatcher_utils.py            # Handler loading and caching
│
├── command_lib/                       # Command handlers (fire hooks only)
│   ├── __init__.py
│   ├── dialog.py                      # ask, talk → entity_dialog hook
│   ├── combat.py                      # attack → entity_combat hook (if needed)
│   └── treatment.py                   # treat → entity_treatment hook (if needed)
│
├── actor_lib/                         # Actor utilities (NO commands)
│   ├── conditions.py                  # Status effects (hooks only)
│   ├── relationships.py               # Trust, reputation
│   ├── packs.py                       # Pack mirroring
│   └── [other utilities]              # NO vocabulary with verbs
│
└── [other libs]/                      # companion_lib, puzzle_lib, etc.
    └── [no changes needed]


examples/big_game/behaviors/shared/
│
├── infrastructure/                    # GAME-SPECIFIC HOOK SUBSCRIBERS
│   ├── gift_reactions.py              # Listens: entity_gift → calls interpreter
│   ├── dialog_reactions.py            # Listens: entity_dialog → calls interpreter
│   ├── item_use_reactions.py          # Listens: entity_item_use → calls interpreter
│   ├── encounter_reactions.py         # Listens: entity_encounter → calls interpreter
│   ├── death_reactions.py             # Listens: entity_death → calls interpreter
│   ├── combat_reactions.py            # Listens: entity_combat → calls interpreter
│   ├── entry_reactions.py             # Listens: location_entry → calls interpreter
│   ├── turn_environmental.py          # Listens: turn_tick → calls interpreter
│   ├── commitment_reactions.py        # Listens: commitment_change → calls interpreter
│   ├── take_reactions.py              # Listens: entity_take → calls interpreter
│   ├── examine_reactions.py           # Listens: entity_examine → calls interpreter
│   ├── trade_reactions.py             # Listens: entity_trade → calls interpreter
│   │
│   ├── commitments.py                 # Commitment system (hooks only)
│   ├── gossip.py                      # Gossip system (hooks only)
│   ├── pack_mirroring.py              # Pack state sync (hooks only)
│   ├── scheduled_events.py            # Timed events (hooks only)
│   └── spreads.py                     # Environmental spreading (hooks only)
│
└── lib/                               # Symlinks to behavior_libraries
    └── [symlinks to behavior_libraries/*]


examples/big_game/behaviors/regions/   # GAME-SPECIFIC HANDLERS
├── beast_wilds/
│   ├── wolf_pack.py                   # Handler: on_wolf_gift (NO vocabulary)
│   ├── sira_rescue.py                 # Handler: on_sira_dialog (NO vocabulary)
│   └── bee_queen.py                   # Handler: on_queen_gift (NO vocabulary)
│
├── frozen_reaches/
│   ├── salamanders.py                 # Handler: on_salamander_gift (NO vocabulary)
│   ├── golem_puzzle.py                # Handler: on_golem_combat (NO vocabulary)
│   └── telescope_repair.py            # Handler: on_telescope_use (NO vocabulary)
│
├── civilized_remnants/
│   ├── services.py                    # Handler: on_service_request (NO vocabulary)
│   ├── mira.py                        # Handler: on_mira_dialog (NO vocabulary)
│   ├── vex.py                         # Handler: on_vex_dialog (NO vocabulary)
│   └── archivist.py                   # Handler: on_archivist_dialog (NO vocabulary)
│
└── [other regions]/
    └── [handlers only, NO vocabulary]
```

**Key Rules:**

1. ✅ Commands with vocabulary → `behavior_libraries/command_lib/`
2. ✅ Reaction core (interpreter, effects) → `behavior_libraries/reaction_lib/`
3. ✅ Hook subscribers → `game/behaviors/shared/infrastructure/`
4. ✅ Entity handlers → `game/behaviors/regions/`
5. ❌ NO vocabulary in `behaviors/regions/` files
6. ❌ NO vocabulary in `actor_lib/` files (except hooks)

---

## Integration Flow

### End-to-End Example: "ask maren about trade"

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER INPUT                                               │
│    Player types: "ask maren about trade"                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. PARSER (engine core)                                     │
│    Parses to action dict:                                   │
│    {                                                        │
│      "verb": "ask",                                         │
│      "object": WordEntry("maren"),                          │
│      "indirect_object": WordEntry("trade"),                 │
│      "actor_id": "player"                                   │
│    }                                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. COMMAND HANDLER (behavior_libraries/command_lib/dialog.py) │
│    handle_ask(accessor, action):                           │
│      - Find NPC: maren = find_accessible_actor("maren")    │
│      - Extract topic: "trade"                              │
│      - Build context: {"keyword": "trade", "speaker": "player"} │
│      - Fire hook: invoke_behavior(maren, "entity_dialog")  │
│      - Wait for EventResult                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. HOOK DISPATCH (engine core)                             │
│    invoke_behavior(maren, "entity_dialog", context):       │
│      - Find modules subscribing to "entity_dialog" hook    │
│      - Call each: on_dialog(maren, accessor, context)      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. REACTION INFRASTRUCTURE                                  │
│    (infrastructure/dialog_reactions.py)                     │
│    on_dialog(maren, accessor, context):                    │
│      - Check: maren.properties.dialog_reactions            │
│      - Found: {"handler": "services.py:on_service_request"}│
│      - Load handler: load_handler(path)                    │
│      - Call handler: handler(maren, accessor, context)     │
│      - Return EventResult                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. ENTITY HANDLER                                           │
│    (regions/civilized_remnants/services.py)                │
│    on_service_request(maren, accessor, context):           │
│      - Check keyword: "trade" in TRADE_KEYWORDS            │
│      - Get trust: maren.properties.trust_state.current     │
│      - Calculate prices with discount                      │
│      - Build shop menu message                             │
│      - Return EventResult(allow=True, feedback=msg)        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. COMMAND HANDLER (back in command_lib/dialog.py)         │
│    handle_ask (continued):                                 │
│      - Receive EventResult from hook                       │
│      - Extract feedback message                            │
│      - Serialize NPC data for narrator                     │
│      - Return HandlerResult(success=True, primary=msg)     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. GAME ENGINE                                              │
│    - Receive HandlerResult                                 │
│    - Display primary message to player                     │
│    - Send data to narrator (if LLM enabled)                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 9. OUTPUT TO PLAYER                                         │
│    "Maren shows you her wares:                             │
│      - healing moss (45 gold)                              │
│      - warm cloak (90 gold)"                               │
└─────────────────────────────────────────────────────────────┘
```

### Critical Integration Points

1. **Command → Hook**: Command handler MUST fire hook, not look up properties
2. **Hook → Reaction**: Reaction infrastructure MUST subscribe to hook
3. **Reaction → Handler**: Reaction infrastructure MUST load and call handler
4. **Handler → Interpreter**: Handler MAY delegate to interpreter for data-driven configs
5. **EventResult → HandlerResult**: Command handler MUST convert result types

---

## Component Specifications

### 1. Command Handlers (behavior_libraries/command_lib/)

**Template:**

```python
# behavior_libraries/command_lib/dialog.py

"""Dialog command handlers.

Provides ask/talk commands. Pure hook dispatch - NO game logic.
"""

from typing import Dict
from src.state_accessor import HandlerResult
from src.word_entry import WordEntry
from src.types import ActorId
from utilities.utils import find_accessible_actor
from utilities.handler_utils import get_display_name
from utilities.entity_serializer import serialize_for_handler_result

vocabulary = {
    "verbs": [
        {
            "word": "ask",
            "synonyms": ["inquire", "question"],
            "object_required": True,
            "preposition": "about"
        },
        {
            "word": "talk",
            "synonyms": ["speak", "converse"],
            "object_required": False,
            "preposition": "to"
        }
    ],
    "handlers": {
        "ask": "handle_ask",
        "talk": "handle_talk"
    }
}


def handle_ask(accessor, action: Dict) -> HandlerResult:
    """Handle 'ask <npc> about <topic>' command.

    Fires entity_dialog hook - ALL logic in reaction infrastructure.
    """
    actor_id = ActorId(action.get('actor_id', ActorId("player")))
    npc_name = action.get('object')
    topic = action.get('indirect_object') or action.get('raw_after_preposition', '')

    # Find NPC
    if not isinstance(npc_name, WordEntry):
        return HandlerResult(success=False, primary="Ask who?")

    npc = find_accessible_actor(accessor, npc_name, actor_id)
    if not npc:
        return HandlerResult(
            success=False,
            primary=f"You don't see any {get_display_name(npc_name)} here."
        )

    if not topic:
        return HandlerResult(success=False, primary=f"Ask {npc.name} about what?")

    # Fire hook (reaction infrastructure handles everything)
    topic_str = topic.word if isinstance(topic, WordEntry) else str(topic)
    context = {
        "keyword": topic_str,
        "dialog_text": topic_str,
        "speaker": actor_id
    }

    result = accessor.behavior_manager.invoke_behavior(
        npc, "entity_dialog", accessor, context
    )

    # Convert EventResult → HandlerResult
    npc_data = serialize_for_handler_result(npc, accessor, actor_id)

    if result and result.feedback:
        return HandlerResult(
            success=result.allow,
            primary=result.feedback,
            data=npc_data
        )
    else:
        return HandlerResult(
            success=False,
            primary=f"{npc.name} doesn't seem interested in conversation.",
            data=npc_data
        )
```

**Requirements:**
- ✅ Defines verbs with vocabulary
- ✅ Parses user input
- ✅ Finds target entities
- ✅ Fires hooks with context
- ✅ Converts EventResult → HandlerResult
- ❌ NO property lookups on entities
- ❌ NO game logic
- ❌ NO handler loading

### 2. Reaction Infrastructure (game/behaviors/shared/infrastructure/)

**Template:**

```python
# examples/big_game/behaviors/shared/infrastructure/dialog_reactions.py

"""Dialog Reaction Infrastructure.

Subscribes to entity_dialog hook and dispatches to handlers.
"""

from typing import Any
from behavior_libraries.reaction_lib import process_reaction, DIALOG_SPEC, load_handler
from src.behavior_manager import EventResult

# Hook subscription
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "entity_dialog",
            "invocation": "entity",
            "description": "Called when player talks to entity"
        }
    ],
    "events": [
        {
            "event": "on_dialog",
            "hook": "entity_dialog",
            "description": "Handle dialog reactions"
        }
    ]
}


def on_dialog(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle dialog reactions.

    Checks entity.properties.dialog_reactions and dispatches.
    """
    if not hasattr(entity, "properties"):
        return EventResult(allow=True, feedback=None)

    # Check for dialog_reactions config
    dialog_config = entity.properties.get("dialog_reactions", {})
    if not dialog_config:
        return EventResult(allow=True, feedback=None)

    # Handler escape hatch
    handler_path = dialog_config.get("handler")
    if handler_path:
        handler = load_handler(handler_path)
        if handler:
            return handler(entity, accessor, context)
        # Handler failed to load - fall through

    # Data-driven processing via unified interpreter
    match = DIALOG_SPEC.match_strategy.find_match(dialog_config, context)
    if not match:
        default_response = dialog_config.get("default_response")
        return EventResult(allow=True, feedback=default_response)

    reaction_name, reaction_config = match
    return process_reaction(entity, reaction_config, accessor, context, DIALOG_SPEC)
```

**Requirements:**
- ✅ Subscribes to hook via vocabulary.events
- ✅ Checks entity properties for config
- ✅ Loads handlers from paths
- ✅ Delegates to unified interpreter
- ✅ Returns EventResult
- ❌ NO command parsing
- ❌ NO HandlerResult (only EventResult)

### 3. Unified Interpreter (behavior_libraries/reaction_lib/)

**Already exists** - see reaction_system_design.md for full spec.

Key exports:
```python
from behavior_libraries.reaction_lib import (
    process_reaction,       # Core interpreter
    EFFECT_REGISTRY,        # 18 effect handlers
    CONDITION_REGISTRY,     # 5 condition checkers
    DIALOG_SPEC,           # ReactionSpec for dialog
    load_handler,          # Handler loading/caching
    # ... other specs
)
```

### 4. Entity Handlers (game/behaviors/regions/)

**Template:**

```python
# examples/big_game/behaviors/regions/civilized_remnants/services.py

"""Service handlers for NPCs (Maren, Elara).

NO vocabulary - pure handler functions only.
"""

from typing import Any
from src.behavior_manager import EventResult

# NO vocabulary dict here!


def on_service_request(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle service requests (trading, healing).

    Args:
        entity: The NPC (Maren or Elara)
        accessor: StateAccessor
        context: {"keyword": str, "speaker": ActorId}

    Returns:
        EventResult with service response
    """
    keyword = context.get("keyword", "").lower()

    # Maren - Trading
    if "maren" in entity.id.lower():
        if any(k in keyword for k in ["buy", "sell", "trade"]):
            return _handle_maren_trading(entity, accessor, context)

    # Elara - Healing
    if "elara" in entity.id.lower():
        if any(k in keyword for k in ["heal", "cure", "help"]):
            return _handle_elara_healing(entity, accessor, context)

    return EventResult(allow=True, feedback=None)


def _handle_maren_trading(entity, accessor, context):
    """Maren's trading logic."""
    # ... trading implementation
    return EventResult(
        allow=True,
        feedback="Maren shows you her wares: ..."
    )
```

**Requirements:**
- ✅ Pure functions: (entity, accessor, context) → EventResult
- ✅ Business logic only
- ❌ NO vocabulary dict
- ❌ NO command handling
- ❌ NO hook definitions

---

## Migration Requirements

### Phase 0: Delete Old Systems (MANDATORY FIRST STEP)

**Before creating new infrastructure:**

1. **Audit vocabulary-based commands:**
   ```bash
   grep -r "\"verbs\":" behavior_libraries/
   ```

2. **For each old system, document:**
   - What commands it provides
   - What entities use it
   - Replacement plan

3. **Delete old command systems:**
   ```bash
   rm -rf behavior_libraries/dialog_lib
   rm -rf behavior_libraries/crafting_lib    # if unused
   rm -rf behavior_libraries/offering_lib    # if unused
   ```

4. **Verify deletion:**
   ```bash
   grep -r "dialog_lib" examples/big_game/  # Must return 0 results
   ```

**Do NOT proceed to Phase 1 until old systems deleted.**

### Phase 1: Create General-Purpose Infrastructure

1. **Create behavior_libraries/reaction_lib/**
   - Move reaction core from current location
   - Create proper __init__.py with exports
   - Update all imports

2. **Create behavior_libraries/command_lib/dialog.py**
   - Implement ask/talk commands
   - Fire entity_dialog hook only
   - NO property lookups

3. **Test integration:**
   ```bash
   # Must work end-to-end
   python tools/test_command_integration.py dialog
   ```

### Phase 2: Migrate Entities

For each entity using old system:

1. **Update property name:**
   ```diff
   - "dialog_topics": {"handler": "path:func"}
   + "dialog_reactions": {"handler": "path:func"}
   ```

2. **Verify handler signature:**
   ```python
   def handler(entity, accessor, context) -> EventResult:
       ...
   ```

3. **Test with walkthrough:**
   ```bash
   python tools/walkthrough.py --file walkthroughs/npcs/${npc}.txt
   ```

### Phase 3: Update Global Configuration

```json
{
  "extra": {
    "behaviors": [
      "behavior_libraries.command_lib.dialog",
      "examples.big_game.behaviors.shared.infrastructure.dialog_reactions",
      ...
    ]
  }
}
```

### Phase 4: Validate Complete

```bash
# All must pass
python tools/validate_game_state.py examples/big_game
python tools/validate_no_old_systems.py
python tools/walkthrough.py --all
```

---

## Validation Requirements

### 1. No Old Systems Check

```python
# tools/validate_no_old_systems.py

def validate_no_old_systems():
    """Verify old vocabulary-based command systems deleted."""

    # Check directories don't exist
    old_dirs = [
        "behavior_libraries/dialog_lib",
        "behavior_libraries/crafting_lib",
        "behavior_libraries/offering_lib"
    ]
    for dir_path in old_dirs:
        if os.path.exists(dir_path):
            raise ValidationError(f"Old system still exists: {dir_path}")

    # Check no references in code
    result = subprocess.run(
        ["grep", "-r", "dialog_lib", "examples/big_game/"],
        capture_output=True
    )
    if result.returncode == 0:
        raise ValidationError("Found references to dialog_lib in game code")

    # Check no entities use old properties
    with open('examples/big_game/game_state.json') as f:
        state = json.load(f)

    for actor in state['actors'].values():
        if 'dialog_topics' in actor.get('properties', {}):
            raise ValidationError(
                f"Actor {actor['id']} still uses dialog_topics"
            )
```

### 2. Integration Testing

Each reaction type needs end-to-end test:

```python
# tests/integration/test_dialog_system.py

def test_dialog_command_to_response():
    """Test: user command → hook → reaction → response."""

    # Setup: NPC with dialog_reactions
    game = setup_game_with_npc({
        "id": "test_npc",
        "properties": {
            "dialog_reactions": {
                "handler": "test:handler"
            }
        }
    })

    # Execute: ask command
    result = game.execute_command("ask test_npc about test")

    # Verify: handler called, response returned
    assert result.success
    assert "response from handler" in result.primary
```

### 3. Architecture Compliance

```python
# tools/validate_architecture.py

def validate_architecture():
    """Verify architecture rules followed."""

    # Check: No vocabulary in region behaviors
    for file in glob("examples/big_game/behaviors/regions/**/*.py"):
        with open(file) as f:
            content = f.read()
        if "vocabulary = {" in content and '"verbs"' in content:
            raise ValidationError(
                f"Region behavior {file} has command vocabulary (should be pure handlers)"
            )

    # Check: All commands in command_lib
    for file in glob("behavior_libraries/**/**.py"):
        if "command_lib" in file:
            continue
        with open(file) as f:
            content = f.read()
        if '"verbs":' in content and '"handlers":' in content:
            raise ValidationError(
                f"Command vocabulary found outside command_lib: {file}"
            )
```

---

## Success Criteria

### Mandatory Requirements

- [ ] ✅ All old vocabulary-based command systems deleted
- [ ] ✅ `grep -r "dialog_lib" examples/` returns 0 results
- [ ] ✅ `grep -r "dialog_topics"` returns 0 results
- [ ] ✅ Zero entities use old property names
- [ ] ✅ All commands in `behavior_libraries/command_lib/`
- [ ] ✅ All reaction core in `behavior_libraries/reaction_lib/`
- [ ] ✅ All hook subscribers in `game/behaviors/shared/infrastructure/`
- [ ] ✅ All entity handlers in `game/behaviors/regions/`
- [ ] ✅ Zero vocabulary dicts in region behavior files
- [ ] ✅ All 12 reaction types have infrastructure modules
- [ ] ✅ `python tools/validate_game_state.py` shows 0 errors
- [ ] ✅ `python tools/validate_no_old_systems.py` passes
- [ ] ✅ `python tools/validate_architecture.py` passes
- [ ] ✅ All integration tests pass
- [ ] ✅ All walkthroughs pass (100% success rate)
- [ ] ✅ Game load time < 2 seconds
- [ ] ✅ Reaction dispatch < 1ms average

### Documentation Requirements

- [ ] ✅ Architecture diagram in this document
- [ ] ✅ Integration flow diagram in this document
- [ ] ✅ Each component type has template with requirements
- [ ] ✅ Migration plan references this document
- [ ] ✅ All success criteria explicitly listed

### Integration Requirements

- [ ] ✅ Test: "ask npc about topic" → response (dialog)
- [ ] ✅ Test: "give item to npc" → response (gift)
- [ ] ✅ Test: "use item on target" → response (item_use)
- [ ] ✅ Test: "attack target" → response (combat)
- [ ] ✅ Test: first location entry → response (encounter)
- [ ] ✅ Test: entity death → consequences (death)

---

## Comparison: What This Spec Adds

### vs. reaction_system_architecture.md

**That document had:**
- ✅ Reaction infrastructure module templates
- ✅ Load-time validation requirements
- ✅ Discoverability tooling specs
- ❌ Missing: Command handler specifications
- ❌ Missing: Integration flow diagrams
- ❌ Missing: Directory structure with locations
- ❌ Missing: Who fires hooks
- ❌ Missing: Delete old systems requirement

**This document adds:**
- ✅ Complete three-layer architecture
- ✅ Command vs Reaction separation
- ✅ Explicit directory structure with rules
- ✅ Integration flow with diagram
- ✅ Component specifications with templates
- ✅ Delete-first migration requirement
- ✅ Integration testing requirements
- ✅ Architecture validation requirements
- ✅ Success criteria checklist

### vs. reaction_system_design.md

**That document has:**
- ✅ Unified interpreter specification (THE MOST DETAILED)
- ✅ Effect/condition registries
- ✅ Data-driven mini-language
- ✅ Complete validation system
- ✅ Discoverability tooling
- ❌ Missing: Where components go
- ❌ Missing: Command handler specs

**This document references that for:**
- Interpreter implementation details
- Effect/condition specifications
- Validation algorithms

**This document adds:**
- Where everything goes (directory structure)
- How commands integrate (Layer 1)
- Complete system integration

---

## Usage

**For Implementation:**
1. Follow migration plan in complete_migration_plan.md
2. Use component templates from this document
3. Verify against success criteria checklist
4. Reference reaction_system_design.md for interpreter details

**For Architecture Review:**
1. Check directory structure matches
2. Verify three-layer separation maintained
3. Ensure no vocabulary in wrong places
4. Validate integration flow works

**For Validation:**
1. Run all validation scripts
2. Check success criteria
3. Verify old systems deleted
4. Test integration end-to-end
