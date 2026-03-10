# Rewrite Mock-Based big_game Tests to Use Real Game State

**Issue**: #456

## Problem

60 big_game infrastructure tests fail because they construct mock objects that have diverged from the actual game state. The mock-based approach (`MockState`, `MockAccessor`, `ScenarioState`, `ScenarioAccessor`) creates fragile tests that break silently when game content changes.

### Root causes

1. **Actor ID mismatches** — Tests create actors as `"npc_alpha_wolf"` but handlers hardcode `state.actors.get("alpha_wolf")`
2. **Incomplete mock structures** — Missing `behavior_manager` on accessors, missing `get_item` on state, missing `current` in state machines
3. **Stale feedback text** — Tests assert on specific feedback strings that no longer match handler output
4. **No `invoke_behavior` dispatch** — Mock `behavior_manager` returns `MagicMock` instead of `EventResult`, causing cascading empty-feedback failures

### CLAUDE.md principle violated

> "When loading game state for tests, use the same loading functions as the real game"

## Solution

Replace mock-based test setup with `GameEngine(GAME_DIR)`, following the pattern in `test_big_game_conditions.py`:

```python
from tests.conftest import BaseTestCase
from src.game_engine import GameEngine
from src.state_accessor import StateAccessor

GAME_DIR = (Path(__file__).parent.parent / 'examples' / 'big_game').resolve()

class TestSomething(BaseTestCase):
    def setUp(self):
        self.engine = GameEngine(GAME_DIR)
        self.accessor = StateAccessor(
            self.engine.game_state,
            self.engine.behavior_manager
        )
```

### Key changes per test

- Replace mock entity creation with lookups from real game state
- Replace hardcoded property assumptions with reads from actual entities
- Update feedback assertions to match actual handler output (or test structurally: check state changed, not exact feedback text)
- Use `BaseTestCase` for proper sys.path/module cleanup between tests
- Tests that modify state should work on a fresh `GameEngine` instance per test (setUp creates new engine)

### Test contamination

When multiple test files run in the same process, `GameEngine` adds the game directory to `sys.path`, which can pollute module resolution for subsequent tests. `BaseTestCase.tearDown()` handles this cleanup. All rewritten tests must extend `BaseTestCase`.

## Files to rewrite (by failure count)

| File | Failures | Total Tests | Notes |
|------|----------|-------------|-------|
| `test_beast_wilds_scenarios.py` | 18 | ~30 | Largest file, most handler tests |
| `regions/test_beast_wilds.py` | 11 | ~15 | Unit-level handler tests |
| `test_frozen_reaches_scenarios.py` | 9 | ~12 | Salamander, hypothermia, hot springs |
| `test_e2e_scenarios.py` | 8 | ~51 | Already uses real state partially; needs location/content updates |
| `test_sunken_district_scenarios.py` | 4 | ~16 | Drowning mechanics |
| `test_cross_region_scenarios.py` | 3 | ~6 | Cross-region flower/gossip |
| `test_cross_region_integration.py` | 2 | ~4 | Handler wiring checks |
| `regions/test_fungal_depths.py` | 1 | ~5 | Light puzzle |
| `test_gift_reactions.py` | 1 | ~12 | Track items key |
| `test_item_use_reactions.py` | 1 | ~17 | Item self-reaction |
| `test_phase1_conditions.py` | 1 | ~18 | List vs dict format |
| `test_thermal_shock.py` | 1 | ~3 | Damage calc + module import |

## Phasing

### Phase 1: Establish pattern + fix one-offs (4 files)
Fix the 4 files with only 1 failure each, since these are likely small targeted fixes rather than full rewrites:
- `test_phase1_conditions.py` — conditions format changed from list to dict
- `test_gift_reactions.py` — track_items key issue
- `test_item_use_reactions.py` — item self-reaction feedback
- `test_thermal_shock.py` — damage calc off-by-one + module import path

### Phase 2: Region unit tests (2 files)
- `regions/test_beast_wilds.py` — 11 failures, rewrite to use real game state
- `regions/test_fungal_depths.py` — 1 failure, rewrite to use real game state

### Phase 3: Scenario tests (4 files) ✅ COMPLETE
These are the largest rewrites:
- `test_beast_wilds_scenarios.py` — 18 failures → 0 (27 tests, all pass)
- `test_frozen_reaches_scenarios.py` — 9 failures → 0 (13 tests, all pass)
- `test_sunken_district_scenarios.py` — 4 failures → 0 (16 tests, all pass)
- `test_cross_region_scenarios.py` — 5 failures → 0 (14 tests, all pass)

All four files rewritten to use `GameEngine(GAME_DIR)` + `BaseTestCase`.
`ScenarioTestCase` / `ScenarioAccessor` / `ScenarioState` no longer used by any test.

**Test contamination fix**: Added `_cleanup_test_module()` call in the setup phase
of the autouse fixture (not just teardown), to clear stale `behaviors.*` entries
left by collection-time imports from test modules that import handler functions
at module level (e.g. `test_cross_region_integration.py`).

### Phase 4: E2E test updates + remaining fixes ✅ COMPLETE
- `test_e2e_scenarios.py` — 7 failures fixed: stale location IDs (wolf_den→wolf_clearing), wrong exit directions, undercity removed
- `test_cross_region_integration.py` — 2 failures fixed: handler names (`on_flower_offer`→`on_receive_item`)
- Escape hatch tests — 5 failures fixed: `patch.object(module_ref, ...)` instead of `patch("string.path")`
- `test_dispatcher_utils.py` — 1 failure fixed: compare `__module__`+`__name__` not identity
- **Spider nest handler bugs** found (not test bugs): `on_web_movement` checks `"spider_nest"` but real locations are `spider_thicket`/`spider_matriarch_lair`; `on_spider_respawn_check` sets `spider.properties["location"]` instead of `spider.location`

## What to preserve

- Test intent and coverage should be preserved — we're changing how tests set up state, not what they verify
- Tests for infrastructure behavior (commitments, gossip, conditions) that already pass should not be touched

## Success criteria

- All 60 currently-failing tests pass (some may need test logic changes if the game behavior itself changed)
- No test uses `MockState`, `MockAccessor`, or `ScenarioState` with hand-crafted entity data that duplicates real game state
- No new test contamination issues when running full suite

## Progress

| Phase | Status | Before | After |
|-------|--------|--------|-------|
| Phase 1 | ✅ | 81 failures | 57 failures |
| Phase 2 | ✅ | 57 failures | 52 failures (contamination masked some fixes) |
| Contamination fix | ✅ | N/A | autouse fixture with before+after cleanup |
| Phase 3 | ✅ | 52 failures | 17 failures |
| Phase 4 | ✅ | 17 failures | 0 failures |

**Final result: 585 passed, 0 failed**
