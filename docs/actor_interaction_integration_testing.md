# Actor Interaction Integration Testing

This document describes the integration testing phase for the actor interaction system.

---

## Phase 10: Integration Testing

**Goal**: Validate complete scenarios from simplified use cases.

### 10.1 Use Case Tests

Create integration tests for each simplified use case:

| Use Case | Test File |
|----------|-----------|
| UC1: Infected Scholar | `test_uc1_infected_scholar.py` |
| UC2: Guardian Golems | `test_uc2_guardian_golems.py` |
| UC3: Hungry Wolf Pack | `test_uc3_wolf_pack.py` |
| UC4: Healer and Garden | `test_uc4_healer_garden.py` |
| UC5: Drowning Sailor | `test_uc5_drowning_sailor.py` |
| UC6: Injured Merchant | `test_uc6_injured_merchant.py` |
| UC7: Spider Swarm | `test_uc7_spider_swarm.py` |
| UC8: Broken Statue | `test_uc8_broken_statue.py` |

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

## Test Fixtures Required

### Game State Fixtures

Each use case needs a test fixture JSON file:

```
tests/fixtures/
├── test_actor_conditions.json     # Basic condition testing
├── test_environmental_effects.json # Environmental hazards
├── test_combat_scenarios.json     # Combat mechanics
├── test_npc_services.json         # Service interactions
├── uc1_infected_scholar.json      # Use case 1
├── uc2_guardian_golems.json       # Use case 2
├── uc3_wolf_pack.json             # Use case 3
├── uc4_healer_garden.json         # Use case 4
├── uc5_drowning_sailor.json       # Use case 5
├── uc6_injured_merchant.json      # Use case 6
├── uc7_spider_swarm.json          # Use case 7
└── uc8_broken_statue.json         # Use case 8
```

### Minimum Fixture Content

Each fixture should include:
- Player actor with health, max_health
- Test NPCs with relevant properties
- Test items with relevant properties
- Location(s) with parts if needed

---

## Success Criteria

Integration testing is complete when:

1. **All integration tests pass** for all 8 use cases
2. **Turn phases fire correctly** after successful commands
3. **Conditions progress** each turn with damage and duration
4. **Environmental effects apply** based on part properties
5. **NPCs take actions** including attacks when hostile
6. **Treatment works** via item properties
7. **Services execute** with trust discounts
8. **Pack coordination works** with disposition sync
9. **No code changes needed** for use case scenarios - all property-driven
