# Actor Interaction Integration Testing

This document describes the integration testing phase for the actor interaction system.

---

## Test Architecture Decisions

### Test Fixture Location

Test games will be created in `examples/` rather than `tests/fixtures/`. This provides:
- Proper module isolation via the subprocess pattern
- A real game structure that exercises the full loading path
- Reusable test games for future development

**Location**: `examples/actor_interaction_test/` with game state variations for each use case.

### Test Structure

**Multiple focused test classes per use case**: Each UC will have multiple test classes focusing on specific aspects (e.g., `TestUC1Infection`, `TestUC1Cure`, `TestUC1Contagion`). This provides:
- Isolation between test aspects
- Finer-grained failure reporting
- Each class starts with fresh state (no test-to-test interference)

**Self-contained helpers**: Each `_ucX_impl.py` file contains its own helper methods rather than importing from a shared base. This:
- Maximizes isolation
- Prevents base class changes from breaking multiple test files
- Makes each test file independently understandable

**One wrapper file per UC**: Following the subprocess pattern from `user_docs/integration_testing.md`:
- `tests/test_uc1_infected_scholar.py` (wrapper, runs impl in subprocess)
- `tests/_uc1_infected_scholar_impl.py` (actual test implementations)

### Implementation Order

Use cases will be implemented in this order based on complexity and coverage:

1. **UC1: Infected Scholar** - Simplest, tests conditions + treatment + environment
2. **UC3: Hungry Wolf Pack** - Tests pack coordination + morale + relationships
3. **UC5: Drowning Sailor** - Tests breath tracking + environmental effects
4. **UC2: Guardian Golems** - Tests combat + immunities + cover
5. **UC4: Healer and Garden** - Tests services + knowledge
6. **UC6: Injured Merchant** - Tests treatment + services + relationships
7. **UC7: Spider Swarm** - Tests pack + conditions + complex interactions
8. **UC8: Broken Statue** - Tests construct properties + repair mechanics

---

## Phase 10: Integration Testing

**Goal**: Validate complete scenarios from simplified use cases.

### 10.1 Use Case Tests

Create integration tests for each simplified use case:

| Use Case | Test File | Wrapper |
|----------|-----------|---------|
| UC1: Infected Scholar | `_uc1_infected_scholar_impl.py` | `test_uc1_infected_scholar.py` |
| UC2: Guardian Golems | `_uc2_guardian_golems_impl.py` | `test_uc2_guardian_golems.py` |
| UC3: Hungry Wolf Pack | `_uc3_wolf_pack_impl.py` | `test_uc3_wolf_pack.py` |
| UC4: Healer and Garden | `_uc4_healer_garden_impl.py` | `test_uc4_healer_garden.py` |
| UC5: Drowning Sailor | `_uc5_drowning_sailor_impl.py` | `test_uc5_drowning_sailor.py` |
| UC6: Injured Merchant | `_uc6_injured_merchant_impl.py` | `test_uc6_injured_merchant.py` |
| UC7: Spider Swarm | `_uc7_spider_swarm_impl.py` | `test_uc7_spider_swarm.py` |
| UC8: Broken Statue | `_uc8_broken_statue_impl.py` | `test_uc8_broken_statue.py` |

### 10.2 Example Integration Test

```python
class TestInfectedScholarUseCase(unittest.TestCase):
    """Test UC1: Infected Scholar scenario."""

    def setUp(self):
        self.state = load_game_state("tests/fixtures/uc1_infected_scholar.json")
        self.behavior_manager = BehaviorManager()
        # Load actor interaction behaviors
        modules = self.behavior_manager.discover_modules("behaviors/library/actors")
        self.behavior_manager.load_modules(modules)
        self.accessor = StateAccessor(self.state, self.behavior_manager)

    def test_cure_scholar_with_silvermoss(self):
        """Giving silvermoss to scholar cures fungal infection."""
        scholar = self.accessor.get_actor("npc_scholar")
        self.assertTrue(has_condition(scholar, "fungal_infection"))

        # Simulate give command
        silvermoss = self.accessor.get_item("item_silvermoss")
        player = self.accessor.get_actor("player")

        # Execute give
        result = handle_give(self.accessor, {
            "verb": "give",
            "object": WordEntry("silvermoss", WordType.NOUN, []),
            "indirect_object": WordEntry("scholar", WordType.NOUN, []),
            "actor_id": "player"
        })

        self.assertTrue(result.success)
        self.assertFalse(has_condition(scholar, "fungal_infection"))

    def test_environmental_infection_in_spore_area(self):
        """Player in high spore area gains fungal infection."""
        player = self.accessor.get_actor("player")
        player.location = "part_basement_center"  # high spores

        # Fire environmental effect
        fire_environmental_effects(self.accessor)

        self.assertTrue(has_condition(player, "fungal_infection"))

    def test_resistance_reduces_infection_severity(self):
        """Player disease resistance reduces infection severity."""
        player = self.accessor.get_actor("player")
        player.properties["resistances"] = {"disease": 50}
        player.location = "part_basement_center"

        # High spores = 15 severity, 50% resistance = 8 (rounded up)
        fire_environmental_effects(self.accessor)

        condition = get_condition(player, "fungal_infection")
        self.assertEqual(condition["severity"], 8)
```

### 10.3 Summary

Integration tests validate:
- Complete multi-turn scenarios
- Cross-module interactions
- Property-driven behavior works as designed
- All use cases achievable without code changes

---

## Custom Behaviors Per Use Case

Each use case requires custom behaviors that demonstrate how game-specific code integrates with library modules. These behaviors will be implemented in the test game's `behaviors/` directory.

### UC1: Infected Scholar

**Custom behaviors needed:**

| Behavior | Purpose | Implementation |
|----------|---------|----------------|
| `resistance_modifier` | Reduce condition severity based on `resistances` property | Wraps `apply_condition` to apply resistance calculation |
| `contagion_spread` | Spread conditions with `contagious_range` to nearby actors | Fires during condition tick for contagious conditions |

**File:** `behaviors/uc1_infection.py`

```python
def on_condition_apply_with_resistance(entity, accessor, context):
    """Apply resistance reduction before condition is applied."""
    condition_name = context.get("condition_name")
    condition_data = context.get("condition_data")

    # Get resistance for this condition type
    resistances = entity.properties.get("resistances", {})
    resistance = resistances.get(condition_name, 0)

    if resistance > 0:
        # Reduce severity by resistance percentage
        severity = condition_data.get("severity", 0)
        reduced = int(severity * (1 - resistance / 100))
        context["condition_data"]["severity"] = max(1, reduced)

    return None  # Continue with normal apply
```

### UC3: Hungry Wolf Pack

**Custom behaviors needed:**

| Behavior | Purpose | Implementation |
|----------|---------|----------------|
| `feeding_handler` | Check `satisfies` property against actor `needs` | `on_receive` handler for food items |
| `morale_on_damage` | Update morale when taking damage | `on_damage` handler that checks health thresholds |
| `directed_flee` | Flee to specific `flee_destination` | Override default flee to use destination property |

**File:** `behaviors/uc3_wolf_pack.py`

### UC5: Drowning Sailor

**Custom behaviors needed:**

| Behavior | Purpose | Implementation |
|----------|---------|----------------|
| `rope_pull` | Pull actors with `can_pull_actors` items | Handler for `pull` verb with rope |
| `escort_follow` | Make rescued NPC follow player | `on_rescue` sets following state |

**File:** `behaviors/uc5_drowning.py`

### UC2: Guardian Golems

**Custom behaviors needed:**

| Behavior | Purpose | Implementation |
|----------|---------|----------------|
| `activation_trigger` | Activate golems when player enters trigger zone | `on_enter_part` checks `activation_trigger` property |
| `rune_deactivation` | Deactivate golems via rune interaction | `on_activate` handler for rune object |

**File:** `behaviors/uc2_golems.py`

### UC4: Healer and Garden

**Custom behaviors needed:**

| Behavior | Purpose | Implementation |
|----------|---------|----------------|
| `toxic_touch` | Apply condition when touching toxic plant | `on_take` checks `toxic_to_touch` property |
| `knowledge_gate` | Gate descriptions based on `knows` array | `on_examine` checks player knowledge |

**File:** `behaviors/uc4_healer.py`

### UC6: Injured Merchant

**Custom behaviors needed:**

| Behavior | Purpose | Implementation |
|----------|---------|----------------|
| `escort_mission` | NPC follows player to destination | `on_guide` verb handler |
| `reward_on_arrival` | Grant reward when reaching destination | `on_enter_location` checks destination |

**File:** `behaviors/uc6_merchant.py`

### UC7: Spider Swarm

**Custom behaviors needed:**

| Behavior | Purpose | Implementation |
|----------|---------|----------------|
| `alert_propagation` | Alert pack when `alerted_by` trigger fires | `on_enter_part` or `on_damage` propagates alert |
| `web_burning` | Reduce `web_density` when using fire item | `on_use` handler for torch on webs |
| `web_bonus` | Apply `web_bonus_attacks` damage modifier | Modifies attack damage in webbed areas |

**File:** `behaviors/uc7_spiders.py`

### UC8: Broken Statue

**Custom behaviors needed:**

| Behavior | Purpose | Implementation |
|----------|---------|----------------|
| `repair_handler` | Restore health with `repairs` items | `on_use` checks `repairs` matches `body.form` |
| `functional_threshold` | Set `functional: true` when health crosses threshold | `on_repair` checks health >= 80 |
| `guard_duty` | Attack hostile actors entering guarded location | `on_npc_action` when `current_duty: "guarding"` |

**File:** `behaviors/uc8_statue.py`

---

## Test Game Structure

The integration test game lives in `examples/actor_interaction_test/`:

```
examples/actor_interaction_test/
├── game_state.json           # Base game state (all UCs combined)
├── vocabulary.json           # Game vocabulary
├── behaviors/
│   ├── uc1_infection.py      # UC1 custom behaviors
│   ├── uc2_golems.py         # UC2 custom behaviors
│   ├── uc3_wolf_pack.py      # UC3 custom behaviors
│   ├── uc4_healer.py         # UC4 custom behaviors
│   ├── uc5_drowning.py       # UC5 custom behaviors
│   ├── uc6_merchant.py       # UC6 custom behaviors
│   ├── uc7_spiders.py        # UC7 custom behaviors
│   └── uc8_statue.py         # UC8 custom behaviors
└── uc_fixtures/              # Per-UC game state variations (optional)
    ├── uc1_state.json
    ├── uc3_state.json
    └── ...
```

### Game World Layout

The test game connects all use case locations via a central hub:

```
                    [UC2: Guardian Hall]
                           |
[UC1: Library] --- [Central Hub] --- [UC4: Garden/Healer]
      |                    |                    |
[UC1: Basement]    [UC3: Forest]        [UC4: Hut]
                           |
                   [UC5: Flooded Tunnel]
                           |
                   [UC6: Forest Road] --- [UC6: Town]
                           |
                   [UC7: Spider Gallery]
                           |
                   [UC8: Main Hall]
```

---

## Implementation Phases

### Phase 10.1: Base Test Game Setup

1. Create `examples/actor_interaction_test/` directory structure
2. Create base `game_state.json` with:
   - Player actor with standard properties
   - Central hub location
   - Basic vocabulary
3. Verify game loads and basic commands work
4. Create test wrapper infrastructure

### Phase 10.2: UC1 - Infected Scholar (Simplest)

**Custom behavior implementation:**
1. Write `behaviors/uc1_infection.py` with resistance and contagion behaviors
2. Unit test the custom behaviors in isolation

**Game content:**
1. Add Library and Basement locations with parts
2. Add Scholar NPC with fungal_infection condition
3. Add silvermoss item with `cures` property
4. Set spore_level on basement parts

**Integration tests (`_uc1_infected_scholar_impl.py`):**
- `TestUC1Infection`: Spore exposure applies condition
- `TestUC1Resistance`: Player resistance reduces severity
- `TestUC1Cure`: Giving silvermoss cures scholar
- `TestUC1Contagion`: Proximity to infected spreads condition
- `TestUC1Progression`: Condition worsens over turns

### Phase 10.3: UC3 - Hungry Wolf Pack

**Custom behavior implementation:**
1. Write `behaviors/uc3_wolf_pack.py` with feeding, morale, flee behaviors
2. Unit test custom behaviors

**Game content:**
1. Add Forest clearing and Wolf den locations
2. Add Alpha wolf and pack followers with pack properties
3. Add venison item with `satisfies` property

**Integration tests (`_uc3_wolf_pack_impl.py`):**
- `TestUC3PackSync`: Followers copy alpha disposition
- `TestUC3Feeding`: Giving food pacifies wolves
- `TestUC3MoraleFlee`: Damaged wolves flee when health low
- `TestUC3Relationship`: Repeated feeding builds gratitude
- `TestUC3Domestication`: High gratitude makes wolves friendly

### Phase 10.4: UC5 - Drowning Sailor

**Custom behavior implementation:**
1. Write `behaviors/uc5_drowning.py` with rope pull and escort behaviors
2. Unit test custom behaviors

**Game content:**
1. Add flooded tunnel with breathable/non-breathable parts
2. Add sailor NPC with low breath and exhaustion condition
3. Add breathing reed and rope items

**Integration tests (`_uc5_drowning_sailor_impl.py`):**
- `TestUC5Breath`: Breath decreases in non-breathable areas
- `TestUC5Drowning`: Damage when breath depleted
- `TestUC5BreathingItem`: Reed prevents breath loss
- `TestUC5RopePull`: Pulling sailor with rope
- `TestUC5Rescue`: Complete rescue scenario

### Phase 10.5: UC2 - Guardian Golems

**Custom behavior implementation:**
1. Write `behaviors/uc2_golems.py` with activation and rune behaviors
2. Unit test custom behaviors

**Game content:**
1. Add Guardian Hall with parts and pillar items
2. Add golem NPCs with attacks, immunities, activation triggers
3. Add wall part with rune

**Integration tests (`_uc2_guardian_golems_impl.py`):**
- `TestUC2Activation`: Golems activate on trigger
- `TestUC2Combat`: Golem attacks and damage
- `TestUC2Cover`: Cover reduces damage
- `TestUC2Immunity`: Golems immune to poison/disease
- `TestUC2Deactivation`: Rune deactivates golems

### Phase 10.6: UC4 - Healer and Garden

**Custom behavior implementation:**
1. Write `behaviors/uc4_healer.py` with toxic touch and knowledge behaviors
2. Unit test custom behaviors

**Game content:**
1. Add Garden with plant beds and Healer's hut
2. Add healer NPC with services
3. Add toxic and curative plants

**Integration tests (`_uc4_healer_garden_impl.py`):**
- `TestUC4ToxicPlant`: Touching toxic plant applies poison
- `TestUC4Knowledge`: Knowledge gates plant descriptions
- `TestUC4CureService`: Healer cures for payment
- `TestUC4TeachService`: Healer teaches herbalism
- `TestUC4TrustDiscount`: Trust reduces service cost

### Phase 10.7: UC6 - Injured Merchant

**Custom behavior implementation:**
1. Write `behaviors/uc6_merchant.py` with escort and reward behaviors
2. Unit test custom behaviors

**Game content:**
1. Add Forest road and Town locations
2. Add merchant NPC with bleeding condition and services
3. Add bandages item

**Integration tests (`_uc6_injured_merchant_impl.py`):**
- `TestUC6Treatment`: Bandages treat bleeding
- `TestUC6Trading`: Merchant trades while injured
- `TestUC6Escort`: Guiding merchant to town
- `TestUC6Reward`: Reward on successful escort

### Phase 10.8: UC7 - Spider Swarm

**Custom behavior implementation:**
1. Write `behaviors/uc7_spiders.py` with alert, web burning, bonus behaviors
2. Unit test custom behaviors

**Game content:**
1. Add Gallery with web-covered parts
2. Add spider pack with venomous attacks
3. Add torch and repellent items

**Integration tests (`_uc7_spider_swarm_impl.py`):**
- `TestUC7PackAlert`: Alerting one spider alerts pack
- `TestUC7VenomousAttack`: Spider bites apply venom
- `TestUC7Entanglement`: Web spray entangles
- `TestUC7WebBonus`: Spiders get bonus in heavy webs
- `TestUC7BurnWebs`: Torch reduces web density

### Phase 10.9: UC8 - Broken Statue

**Custom behavior implementation:**
1. Write `behaviors/uc8_statue.py` with repair and guard behaviors
2. Unit test custom behaviors

**Game content:**
1. Add Main Hall with statue
2. Add statue NPC with damaged health, knowledge
3. Add repair kit item

**Integration tests (`_uc8_broken_statue_impl.py`):**
- `TestUC8Repair`: Repair kit restores statue health
- `TestUC8Functional`: Statue becomes functional at health threshold
- `TestUC8Knowledge`: Statue answers knowledge queries
- `TestUC8Guard`: Activated statue guards area

### Phase 10.10: Full Scenario Playthrough

After all UC tests pass, implement end-to-end scenario tests that verify complete gameplay flows through multiple turns.

---

## Playable Demo (Future Enhancement)

A playable demo would allow a human to walk through all use cases in sequence. This would:

1. **Validate narrative flow**: Ensure LLM descriptions work with actor interaction
2. **Test player agency**: Verify multiple solution paths work
3. **Demonstrate capability**: Provide a showcase of the system

**Implementation approach:**
- Add interstitial narrative connecting the use cases
- Player starts at Central Hub
- Each "wing" contains one use case scenario
- Completing a scenario unlocks the next
- Optional: Add a meta-quest that requires visiting all areas

**Deferred to separate task**: This is valuable but out of scope for integration testing. Create a follow-up issue if desired.

---

## Success Criteria

Integration testing is complete when:

1. **All custom behaviors implemented** for all 8 use cases
2. **All custom behaviors have unit tests** verifying their logic
3. **All integration tests pass** for all 8 use cases
4. **Turn phases fire correctly** after successful commands
5. **Conditions progress** each turn with damage and duration
6. **Environmental effects apply** based on part properties
7. **NPCs take actions** including attacks when hostile
8. **Treatment works** via item properties
9. **Services execute** with trust discounts
10. **Pack coordination works** with disposition sync
11. **Custom behaviors integrate cleanly** with library modules
12. **No core engine changes needed** - all scenarios work via properties and behaviors

---

## Test Execution

### Running Individual UC Tests

```bash
# Run UC1 tests
python -m unittest tests.test_uc1_infected_scholar

# Run UC3 tests
python -m unittest tests.test_uc3_wolf_pack
```

### Running All Integration Tests

```bash
# Run all actor interaction integration tests
python -m unittest discover -s tests -p "test_uc*.py"
```

### Test Isolation

Each test class:
1. Loads fresh game state from `examples/actor_interaction_test/`
2. Runs in subprocess to prevent state leakage
3. Does not share state with other test classes
4. Cleans up after itself
