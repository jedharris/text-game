# Big Game Implementation Plan

Implementation plan for "The Shattered Meridian" game, covering custom behaviors and game-specific code.

**Prerequisites:** Framework capabilities from [framework_hole_filling.md](framework_hole_filling.md) should be implemented first.

---

## Overview

This document covers game-specific implementations that don't belong in shared libraries. These are deferred until actual game implementation begins.

---

## Custom Game Behaviors (Deferred)

### 1. Area-Wide Effects / Region Management

**Purpose:** Handle region-wide state changes like "purifying the Fungal Depths" or "cold spreading from Frozen Reaches."

**Why custom behavior (not library):**
- Region definitions are game-specific
- Effect propagation rules vary by game
- Better to show pattern than over-generalize

**Design pattern:**
```python
# big_game/behaviors/regions.py

# Define regions as location lists
REGIONS = {
    "fungal_depths": ["cavern_entrance", "luminous_grotto", "spore_heart",
                      "myconid_sanctuary", "deep_root_caverns"],
    "beast_wilds": ["forest_edge", "wolf_clearing", "bee_grove",
                    "predator_den", "spider_nest"],
    "frozen_reaches": ["frozen_pass", "temple_sanctum", "ice_caves",
                       "hot_springs", "frozen_observatory"],
    # etc.
}

def purify_fungal_region(accessor):
    """When Spore Mother is healed, purify all fungal areas."""
    for loc_id in REGIONS["fungal_depths"]:
        location = accessor.get_location(loc_id)
        if location:
            for part in accessor.get_parts_at(loc_id):
                part.properties["spore_level"] = "none"
            location.properties["state"] = "purified"

    accessor.state.set_flag("fungal_region_purified", True)

def spread_cold_to_region(accessor, region_name: str):
    """Spread cold effects to a region (observatory not repaired in time)."""
    for loc_id in REGIONS[region_name]:
        location = accessor.get_location(loc_id)
        if location:
            for part in accessor.get_parts_at(loc_id):
                if part.properties.get("temperature") == "normal":
                    part.properties["temperature"] = "cold"
```

**Triggered by:**
- `on_spore_mother_healed` event (custom)
- Scheduled event at turn N if observatory not repaired

---

### 2. Faction Reputation System

**Purpose:** Track reputation with factions (Myconids, Town Council, Undercity) that affects multiple NPCs.

**Why custom behavior (not library):**
- Uses existing relationship system as foundation
- Faction definitions are game-specific
- Propagation rules vary (some factions share reputation, others don't)

**Design pattern:**
```python
# big_game/behaviors/factions.py

from behaviors.actors.relationships import modify_relationship

FACTIONS = {
    "myconid_collective": {
        "representative": "myconid_faction",  # Virtual actor for faction relationship
        "members": ["myconid_elder", "myconid_guard", "myconid_healer"],
        "sync_dimensions": ["trust", "fear"],  # Which dimensions sync to members
    },
    "town_council": {
        "representative": "council_faction",
        "members": ["guard_captain", "herbalist_vendor", "councilor_pragmatist"],
        "sync_dimensions": ["trust"],
    },
    "undercity": {
        "representative": "undercity_faction",
        "members": ["fence", "info_broker"],
        "sync_dimensions": ["trust", "fear"],
    }
}

def modify_faction_reputation(accessor, faction_name: str, dimension: str, delta: int):
    """Modify reputation with faction, syncing to members."""
    faction_def = FACTIONS.get(faction_name)
    if not faction_def:
        return

    # Modify faction representative
    rep = accessor.get_actor(faction_def["representative"])
    if rep:
        modify_relationship(accessor, rep, "player", dimension, delta)

    # Sync to members if this dimension syncs
    if dimension in faction_def["sync_dimensions"]:
        for member_id in faction_def["members"]:
            member = accessor.get_actor(member_id)
            if member:
                modify_relationship(accessor, member, "player", dimension, delta)

def get_faction_reputation(accessor, faction_name: str) -> dict:
    """Get current reputation with faction."""
    faction_def = FACTIONS.get(faction_name)
    if not faction_def:
        return {}

    rep = accessor.get_actor(faction_def["representative"])
    if rep:
        return rep.properties.get("relationships", {}).get("player", {})
    return {}
```

**Usage:**
```python
# When player helps Myconids
modify_faction_reputation(accessor, "myconid_collective", "trust", 1)

# When player kills spore creatures (Myconids notice)
modify_faction_reputation(accessor, "myconid_collective", "trust", -1)
```

---

### 3. Cross-Region Event Propagation

**Purpose:** Handle events that affect multiple regions (infection spreading, cold expanding).

**Why custom behavior:**
- Specific to this game's narrative structure
- Timing and triggers are game-specific

**Design pattern:**
```python
# big_game/behaviors/world_events.py

def on_check_world_events(entity, state, context):
    """Check for cross-region events each turn."""
    accessor = context["accessor"]

    # Check spore spread deadline
    if not state.get_flag("spore_mother_healed"):
        if state.turn_count >= 100 and not state.get_flag("spore_spread_started"):
            trigger_spore_spread(accessor)
            state.set_flag("spore_spread_started", True)

    # Check cold spread deadline
    if not state.get_flag("observatory_repaired"):
        if state.turn_count >= 150 and not state.get_flag("cold_spread_started"):
            trigger_cold_spread(accessor)
            state.set_flag("cold_spread_started", True)

def trigger_spore_spread(accessor):
    """Spore infection begins spreading to other regions."""
    # Add spore effects to town entrance
    town_gate = accessor.get_location("town_gate")
    if town_gate:
        # Guards become suspicious
        for guard_id in ["gate_guard_1", "gate_guard_2"]:
            guard = accessor.get_actor(guard_id)
            if guard:
                guard.properties["suspicious"] = True

        # Some town NPCs get infected
        # etc.

def trigger_cold_spread(accessor):
    """Cold begins spreading from Frozen Reaches."""
    # Make Beast Wilds outdoor areas cold
    spread_cold_to_region(accessor, "beast_wilds")
```

---

### 4. Inventory Weight (If Desired)

**Purpose:** Limit how much player can carry.

**Why custom behavior:**
- Many games don't want encumbrance
- Weight values are game-specific
- Simple enough to implement per-game

**Design pattern:**
```python
# big_game/behaviors/inventory_limits.py

MAX_CARRY_WEIGHT = 100

def get_current_weight(accessor) -> int:
    """Calculate total weight of carried items."""
    player = accessor.get_player()
    total = 0
    for item_id in player.inventory:
        item = accessor.get_item(item_id)
        if item:
            total += item.properties.get("weight", 1)
    return total

def on_take(entity, state, context) -> EventResult:
    """Check weight before allowing take."""
    accessor = context["accessor"]

    current = get_current_weight(accessor)
    item_weight = entity.properties.get("weight", 1)

    if current + item_weight > MAX_CARRY_WEIGHT:
        return EventResult(
            allow=False,
            message="You're carrying too much already."
        )
    return EventResult(allow=True)
```

---

### 5. Game-Specific NPC Behaviors

**Purpose:** Custom behaviors for specific NPCs that don't fit general patterns.

**Examples:**

**The Echo (spectral guide):**
```python
# big_game/behaviors/the_echo.py

def on_turn_end_echo_appearance(entity, state, context):
    """The Echo appears intermittently based on game state."""
    accessor = context["accessor"]
    player = accessor.get_player()
    echo = accessor.get_actor("the_echo")

    # Echo only appears in Nexus locations
    nexus_locations = ["nexus_chamber", "observatory_platform",
                       "keepers_quarters", "crystal_garden"]

    if player.location not in nexus_locations:
        echo.location = None  # Not visible
        return

    # Appearance chance based on player's restoration progress
    restoration_count = sum([
        state.get_flag("waystone_repaired", False),
        state.get_flag("crystal_1_restored", False),
        state.get_flag("crystal_2_restored", False),
        state.get_flag("crystal_3_restored", False),
    ])

    appearance_chance = 0.1 + (restoration_count * 0.15)

    if random.random() < appearance_chance:
        echo.location = player.location
        # Echo comments on player's progress
        # ...
```

**Scholar Aldric (dying NPC with timer):**
```python
# big_game/behaviors/scholar_aldric.py

def on_turn_end_aldric_condition(entity, state, context):
    """Track Aldric's deteriorating condition."""
    accessor = context["accessor"]
    aldric = accessor.get_actor("scholar_aldric")

    if not aldric or aldric.properties.get("dead"):
        return

    # Check if already cured
    if state.get_flag("aldric_cured"):
        return

    # Progress infection
    infection = aldric.properties.get("conditions", {}).get("fungal_infection", {})
    severity = infection.get("severity", 80)

    if severity >= 100:
        # Aldric dies
        aldric.properties["dead"] = True
        aldric.properties["description"] = "The scholar lies still, overcome by the infection."
        state.set_flag("aldric_dead", True)
        # This affects available information later
```

---

## Game Data Requirements

### Virtual Faction Actors
Create actors to represent factions (no physical location):
```json
{
  "id": "myconid_faction",
  "name": "Myconid Collective",
  "description": "The collective will of the Myconid colony",
  "location": null,
  "properties": {
    "is_faction": true,
    "relationships": {"player": {"trust": 0, "gratitude": 0, "fear": 0}}
  }
}
```

### Region Metadata
Store region definitions in game_state.json `extra`:
```json
{
  "extra": {
    "regions": {
      "fungal_depths": {
        "locations": ["cavern_entrance", "luminous_grotto", "spore_heart"],
        "default_spore_level": "medium",
        "purified": false
      }
    },
    "world_event_turns": {
      "spore_spread": 100,
      "cold_spread": 150
    }
  }
}
```

---

## Implementation Phases

### Phase 1: Region System
- Define all regions in game data
- Implement region state change functions
- Test purification/corruption mechanics

### Phase 2: Faction System
- Create faction representative actors
- Implement reputation modification
- Test reputation propagation

### Phase 3: World Events
- Implement cross-region event triggers
- Set up scheduled events for deadlines
- Test cascading effects

### Phase 4: NPC Specifics
- Implement The Echo appearance logic
- Implement Aldric timer
- Other game-specific NPC behaviors

### Phase 5: Optional Systems
- Inventory weight (if desired)
- Any other game-specific mechanics

---

## Dependencies

These custom behaviors depend on framework capabilities:

| Custom Behavior | Required Framework |
|-----------------|-------------------|
| Region state changes | Global flags (exists) |
| World event timing | Turn counter, scheduled events |
| Cross-region propagation | Scheduled events |
| NPC-specific behaviors | Various existing systems |

---

## Notes

- All custom behaviors should be in `big_game/behaviors/` directory
- Use existing library functions where possible
- Keep game-specific logic separate from reusable patterns
- Document any patterns that might be useful for future games
