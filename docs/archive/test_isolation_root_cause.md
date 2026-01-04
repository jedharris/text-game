# Root Cause of Test Isolation Issues

## The Real Problem

Tests that use `GameEngine` with game-specific `behaviors/` directories create **persistent module cache pollution** that causes context-dependent failures.

## Two Distinct Import Patterns

### Pattern A: Direct Absolute Imports (No Isolation Needed)
```python
from examples.big_game.behaviors.regions.beast_wilds.sira_rescue import on_sira_encounter
from behavior_libraries.actor_lib.conditions import tick_conditions
```
- Uses absolute module paths
- No sys.path manipulation
- No module conflicts
- ✅ Works in unittest discover

### Pattern B: GameEngine + Relative Imports (NEEDS Isolation)
```python
# Manipulate sys.path
sys.path.insert(0, str(GAME_DIR))

# Load GameEngine - it imports behaviors with relative names
from src.game_engine import GameEngine
engine = GameEngine(GAME_DIR)  # Loads 'behaviors.magic_star'

# Also imports from behavior_libraries
from behavior_libraries.actor_lib.conditions import tick_conditions
```
- Requires sys.path manipulation
- Loads modules with short names (`behaviors.magic_star`)
- Creates module cache conflicts
- ❌ Fails in unittest discover due to pollution

## Why Isolation is Needed

When `GameEngine(GAME_DIR)` runs, it loads behaviors from that game's `behaviors/` directory. These get cached in `sys.modules` with short names like:
- `behaviors.magic_star`
- `behaviors.crystal_ball`

If another test runs `GameEngine(DIFFERENT_GAME_DIR)`, Python's module cache still has the old modules loaded, causing:
- Wrong behavior implementations to run
- Import errors
- Unexpected state

## Tests Requiring Isolation

All tests using `GameEngine(game_dir)` pattern:
1. `test_spatial_game_scenarios.py` → `_spatial_game_scenarios_impl.py`
2. `test_big_game_conditions.py` → `_big_game_conditions_impl.py`
3. `test_thermal_shock.py` → `_thermal_shock_impl.py`
4. `test_uc1_infected_scholar.py` → `_uc1_infected_scholar_impl.py`
5. `test_uc2_guardian_golems.py` → `_uc2_guardian_golems_impl.py`
6. `test_uc3_wolf_pack.py` → `_uc3_wolf_pack_impl.py`
7. `test_uc4_healer_garden.py` → `_uc4_healer_garden_impl.py`
8. `test_uc5_drowning_sailor.py` → `_uc5_drowning_sailor_impl.py`
9. `test_uc6_injured_merchant.py` → `_uc6_injured_merchant_impl.py`
10. `test_uc7_spider_swarm.py` → `_uc7_spider_swarm_impl.py`
11. `test_uc8_broken_statue.py` → `_uc8_broken_statue_impl.py`

## Tests NOT Requiring Isolation

Tests using direct imports from `examples.big_game.behaviors.*`:
- All 11 files in `tests/infrastructure/test_*_scenarios.py`
- These import behavior functions directly with absolute paths
- No GameEngine, no sys.path manipulation, no conflicts

## The Fixable Pattern

The common characteristic is **sys.path manipulation + GameEngine loading**.

### Option 1: Fix BehaviorManager to Use Absolute Paths

Make `GameEngine` load behaviors with absolute module names:
- Instead of: `behaviors.magic_star`
- Use: `examples.spatial_game.behaviors.magic_star`

This would eliminate module conflicts at the source.

### Option 2: Clear Module Cache Between Tests

Add test helper to clear behavior modules from `sys.modules`:
```python
def clear_behavior_modules():
    """Remove all 'behaviors.*' modules from cache."""
    to_remove = [k for k in sys.modules if k.startswith('behaviors.')]
    for key in to_remove:
        del sys.modules[key]
```

Call this in `tearDown()` of tests using GameEngine.

**Downside**: Fragile, doesn't prevent other pollution.

### Option 3: Keep Subprocess Isolation (Current Approach)

Maintain the two-file pattern for GameEngine-based tests.

**Downside**: Complexity, but it works reliably.

## Recommendation

**Short-term**: Keep subprocess isolation for GameEngine-based tests (it's solving a real problem)

**Long-term**: Fix BehaviorManager to load with absolute module paths (Option 1)
- Prevents all future isolation issues
- Makes GameEngine tests work in unittest discover
- Cleaner architecture overall

## What to Document in Test Style Guide

Add guidance:

**"When to Use Subprocess Isolation"**

Use the two-file subprocess pattern when tests:
1. Create `GameEngine` instances pointing to example game directories
2. Load game-specific behaviors via BehaviorManager
3. Manipulate sys.path to find game behaviors

Do NOT use subprocess isolation for:
- Tests that import behaviors directly with absolute paths
- Tests using only behavior_libraries
- Unit tests of core src/ modules
