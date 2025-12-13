# Big Game Integration Testing Plan

This document outlines integration testing for "The Shattered Meridian" (big_game). Integration tests verify that multiple game systems work correctly together, focusing on state cascades, cross-system interactions, and complete player journeys.

## Goals

1. **Test cross-system interactions** - Verify that actions in one system correctly cascade to others
2. **Test complete player journeys** - Validate end-to-end paths through the game
3. **Test time-sensitive mechanics** - Verify scheduled events and deadlines work correctly
4. **Test ending conditions** - Ensure all four endings are reachable and correctly determined

---

## Relationship to Functional Tests

| Aspect | Functional Tests | Integration Tests |
|--------|-----------------|-------------------|
| Scope | Single system | Multiple systems interacting |
| State | Fresh state per test | State evolves through test |
| Focus | "Does X work?" | "When X happens, does Y update?" |
| Example | "Can we purify a region?" | "When we heal Spore Mother, is spore spread cancelled?" |

---

## Test Categories

### Category 1: Quest Completion Cascades

Tests that verify quest completions trigger all expected side effects.

#### 1.1 Heal Spore Mother Quest
**Systems involved:** World Events, Regions, Factions, Scheduled Events

```
Trigger: on_quest_complete(quest_id="heal_spore_mother")

Expected cascades:
├── purify_region(FUNGAL_DEPTHS) called
│   └── All 5 fungal_depths locations: spore_level cleared
├── cancel_spore_spread() called
│   └── EVENT_SPORE_SPREAD removed from scheduler
├── Flag set: spore_mother_healed = true
└── Ending condition updated: regions_purified increments
```

**Test cases:**
- `test_heal_spore_mother_purifies_region` - Region state changes
- `test_heal_spore_mother_cancels_spread` - Scheduled event removed
- `test_heal_spore_mother_updates_ending` - Ending condition reflects change

#### 1.2 Repair Observatory Quest
**Systems involved:** World Events, Scheduled Events, Flags

```
Trigger: on_quest_complete(quest_id="repair_observatory")

Expected cascades:
├── cancel_cold_spread() called
│   └── EVENT_COLD_SPREAD removed from scheduler
├── Flag set: observatory_repaired = true
└── Message: "The observatory hums back to life..."
```

**Test cases:**
- `test_repair_observatory_cancels_cold_spread`
- `test_repair_observatory_sets_flag`

#### 1.3 Crystal Restoration Quests
**Systems involved:** World Events, Flags, Ending Conditions

```
Trigger: on_quest_complete(quest_id="restore_crystal_N") for N in 1,2,3

Expected cascades:
├── Flag set: crystal_N_restored = true
├── Message: "Crystal N pulses with renewed energy"
└── If all 3 crystals restored:
    └── Message: "All three crystals are restored!"
```

**Test cases:**
- `test_restore_single_crystal_sets_flag`
- `test_restore_all_crystals_triggers_message`
- `test_crystals_count_in_ending_conditions`

#### 1.4 Cure Aldric Quest
**Systems involved:** Flags only

```
Trigger: on_quest_complete(quest_id="cure_aldric")

Expected cascades:
├── Flag set: aldric_cured = true
└── Message about Aldric helping
```

**Test cases:**
- `test_cure_aldric_sets_flag`
- `test_aldric_cured_in_ending_conditions`

---

### Category 2: Scheduled Event Triggers

Tests that verify timed events fire correctly and have expected effects.

#### 2.1 Spore Spread Event (Turn 100)
**Systems involved:** Scheduler, Regions, Actors

```
Trigger: Turn reaches 100 with spore spread not cancelled

Expected cascades:
├── trigger_spore_spread() called
├── corrupt_region(CIVILIZED_REMNANTS, 'spore')
│   └── 6 civilized_remnants locations: spore_level = "low"
├── NPCs affected:
│   ├── npc_cr_gate_guard: spore_exposed = true
│   └── npc_cr_patrol_guard: spore_exposed = true
└── Flag set: spore_spread_started = true
```

**Test cases:**
- `test_spore_spread_triggers_at_turn_100`
- `test_spore_spread_corrupts_civilized_remnants`
- `test_spore_spread_affects_guards`
- `test_spore_spread_prevented_if_fungal_purified`

#### 2.2 Cold Spread Event (Turn 150)
**Systems involved:** Scheduler, Regions, Actors

```
Trigger: Turn reaches 150 with cold spread not cancelled

Expected cascades:
├── trigger_cold_spread() called
├── corrupt_region(BEAST_WILDS, 'cold')
│   └── 5 beast_wilds locations: temperature affected
├── Creatures affected:
│   ├── creature_bw_alpha_wolf: cold_affected = true
│   └── creature_bw_wolf_pack: cold_affected = true
└── Flag set: cold_spread_started = true
```

**Test cases:**
- `test_cold_spread_triggers_at_turn_150`
- `test_cold_spread_corrupts_beast_wilds`
- `test_cold_spread_affects_creatures`
- `test_cold_spread_prevented_if_observatory_repaired`

#### 2.3 Deadline Boundary Testing
**Critical edge cases for timing:**

- `test_heal_spore_mother_at_turn_99_prevents_spread`
- `test_heal_spore_mother_at_turn_100_too_late`
- `test_repair_observatory_at_turn_149_prevents_spread`
- `test_repair_observatory_at_turn_150_too_late`

---

### Category 3: Faction Reputation Cascades

Tests that verify faction actions propagate correctly.

#### 3.1 Faction Action → Member Sync
**Systems involved:** Factions, Relationships

```
Trigger: on_faction_action(entity, action="help", faction_id="myconid_collective")

Expected cascades:
├── modify_faction_reputation(trust=+1, gratitude=+1)
│   └── faction_myconid relationships updated
├── sync_faction_reputation() for synced dimensions
│   └── All myconid members get updated trust
└── Disposition may change if threshold crossed
```

**Test cases:**
- `test_positive_action_increases_faction_reputation`
- `test_reputation_syncs_to_faction_members`
- `test_faction_disposition_changes_at_threshold`
- `test_negative_action_increases_fear`

#### 3.2 Disposition Thresholds
**Threshold values:**
- hostile: fear >= 5 AND trust < 3
- friendly: trust >= 5
- allied: trust >= 8

**Test cases:**
- `test_disposition_hostile_at_high_fear`
- `test_disposition_friendly_at_trust_5`
- `test_disposition_allied_at_trust_8`
- `test_disposition_neutral_default`

---

### Category 4: Region State Cascades

Tests that verify region operations affect all appropriate entities.

#### 4.1 Region Corruption
**Systems involved:** Regions, Locations

```
Trigger: corrupt_region(accessor, "beast_wilds", "cold")

Expected cascades:
├── All 5 beast_wilds locations get corruption property
├── Region state updated in extra['regions']
└── Messages returned for each affected location
```

**Test cases:**
- `test_corruption_affects_all_region_locations`
- `test_corruption_type_applied_correctly`
- `test_corruption_returns_messages`

#### 4.2 Region Purification
**Systems involved:** Regions, Locations, Flags

```
Trigger: purify_region(accessor, "fungal_depths")

Expected cascades:
├── All 5 fungal_depths locations cleared
├── Region purified flag set
└── Messages returned
```

**Test cases:**
- `test_purification_clears_all_locations`
- `test_purification_sets_region_flag`
- `test_is_region_purified_returns_true_after`

---

### Category 5: The Echo Integration

Tests that verify The Echo's behavior integrates with game state.

#### 5.1 Appearance Probability
**Systems involved:** The Echo, Flags, Random

```
Base chance: 10%
Per restoration flag: +15%
Restoration flags: 7 total
Maximum: 85%
```

**Test cases:**
- `test_echo_base_chance_10_percent`
- `test_echo_chance_increases_with_flags`
- `test_echo_chance_capped_at_85_percent`
- `test_echo_only_appears_in_nexus`

#### 5.2 Message State Awareness
**Systems involved:** The Echo, Flags, World Events

```
Message varies based on:
├── First meeting vs returning (met_the_echo flag)
├── Crystal restoration count (0, 1, 2, or 3)
├── Spore spread warning (spore_spread_started)
├── Cold spread warning (cold_spread_started)
└── Completion state
```

**Test cases:**
- `test_echo_first_meeting_message`
- `test_echo_returning_message`
- `test_echo_spore_warning_message`
- `test_echo_cold_warning_message`
- `test_echo_crystal_progress_message`

---

### Category 6: Ending Condition Paths

Tests that verify all four endings are correctly determined.

#### 6.1 Perfect Ending
**Condition:** crystals_restored == 3 AND regions_purified == 3

```
Required state:
├── crystal_1_restored = true
├── crystal_2_restored = true
├── crystal_3_restored = true
├── fungal_depths purified
├── beast_wilds purified
└── frozen_reaches purified
```

**Test case:** `test_perfect_ending_all_crystals_all_regions`

#### 6.2 Partial Restoration Ending
**Condition:** crystals_restored == 3 AND regions_purified < 3

```
Required state:
├── All 3 crystals restored
└── At least one corrupted region NOT purified
```

**Test case:** `test_partial_ending_crystals_but_not_regions`

#### 6.3 Catastrophe Ending
**Condition:** spore_spread_started AND cold_spread_started

```
Required state:
├── spore_spread_started = true
└── cold_spread_started = true
```

**Test case:** `test_catastrophe_ending_both_spreads`

#### 6.4 In Progress (No Ending)
**Condition:** None of the above

```
Default state when:
├── Less than 3 crystals restored
├── AND not both spreads started
```

**Test case:** `test_in_progress_default_state`

---

### Category 7: Complete Player Journeys

End-to-end tests that simulate complete game paths.

#### 7.1 Perfect Run Journey
```
1. Player heals Spore Mother (before turn 100)
   → Fungal Depths purified, spore spread cancelled
2. Player repairs Observatory (before turn 150)
   → Cold spread cancelled
3. Player restores Crystal 1
4. Player restores Crystal 2
5. Player restores Crystal 3
6. Player purifies Beast Wilds (via unknown quest)
7. Player purifies Frozen Reaches (via unknown quest)
→ check_ending_conditions returns ending="perfect"
```

**Test case:** `test_journey_perfect_ending`

#### 7.2 Catastrophe Run Journey
```
1. Player does NOT heal Spore Mother
2. Turn 100 passes → spore spread triggers
3. Player does NOT repair Observatory
4. Turn 150 passes → cold spread triggers
→ check_ending_conditions returns ending="catastrophe"
```

**Test case:** `test_journey_catastrophe_ending`

#### 7.3 Partial Restoration Journey
```
1. Player restores all 3 crystals
2. Player purifies only 1-2 regions
→ check_ending_conditions returns ending="partial_restoration"
```

**Test case:** `test_journey_partial_restoration`

#### 7.4 Race Against Time Journey
```
1. Turn 95: Player heals Spore Mother (just in time)
   → Spore spread cancelled
2. Turn 145: Player repairs Observatory (just in time)
   → Cold spread cancelled
3. Complete remaining objectives
→ Perfect ending still achievable
```

**Test case:** `test_journey_deadline_completion`

---

## Test Implementation

### File Structure

```
tests/
├── test_big_game_integration.py      # Subprocess wrapper
└── _big_game_integration_impl.py     # Test implementations
```

### Test Class Organization

```python
# Category 1: Quest Cascades
class TestQuestCompletionCascades(unittest.TestCase):
    """Tests for quest completion side effects."""

# Category 2: Scheduled Events
class TestScheduledEventTriggers(unittest.TestCase):
    """Tests for timed event mechanics."""

class TestDeadlineBoundaries(unittest.TestCase):
    """Tests for deadline edge cases."""

# Category 3: Factions
class TestFactionReputationCascades(unittest.TestCase):
    """Tests for faction reputation propagation."""

# Category 4: Regions
class TestRegionStateCascades(unittest.TestCase):
    """Tests for region state changes."""

# Category 5: The Echo
class TestEchoIntegration(unittest.TestCase):
    """Tests for The Echo's state-aware behavior."""

# Category 6: Endings
class TestEndingConditionPaths(unittest.TestCase):
    """Tests for all four ending conditions."""

# Category 7: Journeys
class TestCompletePlayerJourneys(unittest.TestCase):
    """End-to-end journey tests."""
```

### Helper Functions

```python
def advance_turns(accessor, count: int) -> List[str]:
    """Simulate turn passage and process scheduled events."""

def complete_quest(accessor, quest_id: str) -> EventResult:
    """Trigger quest completion with all side effects."""

def set_game_flags(accessor, **flags) -> None:
    """Set multiple game flags for test setup."""

def verify_ending(accessor, expected: str) -> None:
    """Assert current ending condition matches expected."""
```

---

## Test Count Summary

| Category | Test Count |
|----------|------------|
| Quest Completion Cascades | 10 |
| Scheduled Event Triggers | 8 |
| Deadline Boundaries | 4 |
| Faction Reputation Cascades | 6 |
| Region State Cascades | 6 |
| The Echo Integration | 7 |
| Ending Condition Paths | 4 |
| Complete Player Journeys | 4 |
| **Total** | **~49** |

---

## Turn Advancement Approaches

Integration tests need two approaches for turn advancement:

### 1. Direct Manipulation (for deadline testing)

For testing exact deadline boundaries (turn 99 vs 100):

```python
def advance_turns_direct(accessor, target_turn: int) -> List[str]:
    """Set turn count directly and process scheduled events."""
    from behavior_libraries.timing_lib.scheduled_events import on_check_scheduled_events

    accessor.game_state.turn_count = target_turn
    result = on_check_scheduled_events(None, accessor, {})
    return result.message.split('\n') if result.message else []
```

### 2. Gameplay Simulation (for journey tests)

For testing realistic play sequences:

```python
def simulate_turns(handler, count: int) -> List[dict]:
    """Simulate gameplay turns by issuing 'wait' commands."""
    results = []
    for _ in range(count):
        result = handler.handle_command({
            "type": "command",
            "action": {"verb": "wait"}
        })
        results.append(result)
    return results
```

### When to Use Each

| Scenario | Approach |
|----------|----------|
| Test event fires at exactly turn 100 | Direct manipulation |
| Test event doesn't fire at turn 99 | Direct manipulation |
| Test full player journey | Gameplay simulation |
| Test turn counter increments | Gameplay simulation |
| Test quest completion timing | Either (quest can be triggered directly) |

---

## Dependencies

- Uses subprocess isolation (same pattern as functional tests)
- Requires timing_lib for scheduled event testing
- Uses StateAccessor for direct state access

---

## Design Holes to Fill

Analysis of `Archive/big_game_overview.md` revealed missing implementations:

### 1. Beast Wilds Purification - NOT IMPLEMENTED

Per the design document, Beast Wilds becomes "safe" when:
- Wolf pack is domesticated (gratitude >= 3)
- Dire Bear cubs are healed (bear becomes grateful)
- Spider Queen is dealt with (alliance or defeat)

**Required implementation:**
```python
# In world_events.py on_quest_complete handler
elif quest_id == 'pacify_beast_wilds':
    messages.extend(purify_region(accessor, REGION_BEAST_WILDS))
    accessor.game_state.extra.setdefault('flags', {})['beast_wilds_pacified'] = True
    messages.append("The Beast Wilds grows calm. The creatures accept your presence.")
```

### 2. Frozen Reaches Purification - NOT IMPLEMENTED

Per the design document, Frozen Reaches is restored when:
- Temple Sanctum golems are deactivated (password or control crystal)
- Steam Salamander alliance formed
- Note: Observatory repair prevents cold SPREAD but doesn't PURIFY the region

**Required implementation:**
```python
elif quest_id == 'restore_frozen_reaches':
    messages.extend(purify_region(accessor, REGION_FROZEN_REACHES))
    accessor.game_state.extra.setdefault('flags', {})['frozen_reaches_restored'] = True
    messages.append("The Frozen Reaches begins to thaw. Ancient warmth returns.")
```

### 3. Flood Mechanics - DECISION NEEDED

The config has `flood_deadline_turn: 50` but:
- No `trigger_flood_spread()` function exists
- No prevention handler in `on_quest_complete`
- The design doc describes floods as local hazards (drowning), not spreading threats

**Options:**
- **Option A:** Remove `flood_deadline_turn` from config (simplest)
- **Option B:** Implement flood spread similar to spore/cold, targeting adjacent regions

**Recommendation:** Option A - the Sunken District is already flooded as its base state. The "flood deadline" doesn't fit the narrative as well as spore/cold spread.

---

## Success Criteria

1. All integration tests pass (0 failures)
2. Each ending path has at least one journey test
3. All quest completion cascades verified
4. Deadline boundary conditions tested
5. Tests run in < 10 seconds total (subprocess overhead)

---

## Notes

- Integration tests use fresh game state but may evolve it through multiple operations
- Tests should verify STATE changes, not just return values
- Cascading effects should be verified at each level of the cascade
- Use descriptive test names that explain the scenario being tested
