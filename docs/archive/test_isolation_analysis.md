# Test Isolation Pattern Analysis

## Summary

Only **spatial_game** requires subprocess isolation and sys.path manipulation. The **big_game infrastructure tests** import behaviors directly without any isolation machinery. This reveals the key difference.

## Two Distinct Patterns

### Pattern A: Direct Behavior Import (big_game)
**Used by**: `tests/infrastructure/test_*_scenarios.py` (11 files)

**Characteristics**:
- Imports behaviors directly from `examples.big_game.behaviors.regions.*`
- Imports behavior functions (e.g., `on_sira_encounter`, `on_gift_given`)
- Uses mock framework (`ScenarioState`, `MockEntity`, `ScenarioAccessor`)
- **NO subprocess isolation required**
- **NO sys.path manipulation required**
- Tests run successfully in unittest discover

**Example**:
```python
from examples.big_game.behaviors.regions.beast_wilds.sira_rescue import (
    on_sira_death,
    on_sira_encounter,
    on_sira_healed,
)
from tests.infrastructure.test_scenario_framework import (
    ScenarioTestCase,
    ScenarioState,
)

class TestSiraRescueScenarios(ScenarioTestCase):
    def setUp(self):
        super().setUp()
        self.setup_player(location="loc_beast_wilds_clearing")
        # Create mocks and test directly against behavior functions
```

### Pattern B: GameEngine Loading (spatial_game)
**Used by**: `tests/test_spatial_game_scenarios.py` + `tests/_spatial_game_scenarios_impl.py`

**Characteristics**:
- Creates full `GameEngine` instance pointing to game directory
- Loads behaviors via BehaviorManager from game's `behaviors/` directory
- Tests against the full engine (not individual behavior functions)
- **REQUIRES subprocess isolation**
- **REQUIRES sys.path manipulation**

**Example**:
```python
# sys.path manipulation needed
def _setup_paths():
    while '' in sys.path:
        sys.path.remove('')
    sys.path.insert(0, str(SPATIAL_GAME_DIR))
    sys.path.insert(1, str(PROJECT_ROOT))

_setup_paths()

from src.game_engine import GameEngine

class TestMagicStaircaseVisibility(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(SPATIAL_GAME_DIR)
        self.player = self.engine.game_state.get_actor('player')
```

## Root Cause: Module Path Conflicts

### Why Pattern B Needs Isolation

When `GameEngine` loads behaviors from `examples/spatial_game/behaviors/`, it imports modules like:
- `behaviors.magic_staircase`
- `behaviors.magic_star`
- `behaviors.tower_entrance`

These modules conflict with:
- Project root's `behaviors/` package (core behaviors)
- Other example games' `behaviors/` packages

Python's module cache (`sys.modules`) can't distinguish between:
- `behaviors.magic_star` (from spatial_game)
- `behaviors.magic_star` (from extended_game if it existed)

The sys.path manipulation ensures the correct `behaviors/` is found first, but this creates cross-contamination between tests.

### Why Pattern A Doesn't Need Isolation

Direct imports use full absolute paths:
- `examples.big_game.behaviors.regions.beast_wilds.sira_rescue`
- `examples.big_game.behaviors.shared.infrastructure.dispatcher_utils`

These are unique module paths that won't conflict with other games. No sys.path manipulation needed, no module cache pollution.

## The Architectural Problem

The spatial_game test uses `GameEngine` which loads behaviors via:
```python
# Inside GameEngine/__init__ or similar
behavior_manager.load_modules_from_dir(game_dir / "behaviors")
```

This loads modules with short relative names like `behaviors.magic_star`, which are ambiguous across different example games.

## Solutions

### Option 1: Convert spatial_game Tests to Pattern A (Recommended)

**Change**: Import and test individual behavior functions directly, like big_game tests do.

**Pros**:
- No subprocess isolation needed
- No sys.path manipulation
- Tests run in unittest discover
- Consistent with existing infrastructure tests

**Cons**:
- More work to refactor (need to create mocks)
- Loses end-to-end testing via GameEngine

### Option 2: Fix GameEngine to Use Absolute Module Paths

**Change**: Make GameEngine load behaviors with unique absolute module names like `examples.spatial_game.behaviors.magic_star` instead of just `behaviors.magic_star`.

**Pros**:
- Eliminates module path conflicts at the source
- Would allow GameEngine-based tests to run without isolation
- More robust architecture overall

**Cons**:
- Requires changes to BehaviorManager loading mechanism
- May affect how behaviors reference each other
- Could break existing game behavior imports

### Option 3: Keep Current Isolation Pattern (Not Recommended)

**Status quo**: Use subprocess isolation for GameEngine-based tests.

**Pros**:
- Works today
- No refactoring required

**Cons**:
- Fragile - "new ones keep cropping up as the context evolves"
- Slow (subprocess overhead)
- Complexity (two-file pattern)
- Doesn't address root cause

## Recommendation

**Immediate action**: Remove subprocess isolation from spatial_game tests

The isolation pattern is solving a problem that doesn't exist. We can:

1. **Remove the wrapper pattern**
   - Delete `tests/test_spatial_game_scenarios.py`
   - Rename `tests/_spatial_game_scenarios_impl.py` → `tests/test_spatial_game_scenarios.py`
   - Remove `_setup_paths()` function
   - Let tests run normally in unittest discover

2. **Document the real constraint**
   - Update integration_testing.md to explain when isolation is actually needed
   - "Only use subprocess isolation if you have multiple games with conflicting module names being tested in the same run"
   - Currently no such conflicts exist

3. **Alternative: Convert to Pattern A** (if we want consistency)
   - Change spatial_game tests to import behaviors directly
   - Use ScenarioTestCase framework like big_game tests
   - This unifies all scenario tests under one pattern
   - More work but creates better consistency

## Files That Need Isolation Today

- `tests/test_spatial_game_scenarios.py` (wrapper)
- `tests/_spatial_game_scenarios_impl.py` (implementation)

**All other scenario tests** (11 files in `tests/infrastructure/`) run successfully without isolation.

## Validation

### Infrastructure Tests (Pattern A)
```bash
python -m unittest discover -s tests/infrastructure -v
# Result: 139 tests run, no import errors, no isolation needed
```

✅ All infrastructure scenario tests run without subprocess isolation

### Spatial Game Tests (Pattern B)
```bash
python -m unittest tests._spatial_game_scenarios_impl -v
# Result: Tests run successfully, no import errors
```

**FINDING**: The spatial_game tests actually DON'T require subprocess isolation!

The subprocess pattern was implemented based on a *theoretical concern* about module name conflicts between different example games (e.g., `behaviors.crystal_ball` from spatial_game vs extended_game).

**However**:
- Only spatial_game has scenario tests using GameEngine
- No other games have scenario tests that would conflict
- Tests run successfully without subprocess isolation
- The isolation pattern is **unnecessary complexity**

### Real Risk vs Current Reality

**Theoretical risk**: If we had scenario tests for multiple games (spatial_game, extended_game, fancy_game) all using GameEngine and loading `behaviors.crystal_ball`, they could conflict.

**Current reality**:
- Only spatial_game has GameEngine-based scenario tests
- No module conflicts exist
- Subprocess isolation adds complexity without current benefit

## Next Steps

1. Discuss with user which approach to take
2. If Option 1: Refactor spatial_game tests to import behaviors directly
3. If Option 2: Design BehaviorManager absolute path loading mechanism
4. Update test style guide with guidance on which pattern to use
