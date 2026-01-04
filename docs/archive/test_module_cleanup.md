# Test Module Cleanup Approach

## Problem

Tests that load behaviors via GameEngine or BehaviorManager can fail context-dependently when run together because they all use the `behaviors.*` namespace. Python's module cache (`sys.modules`) retains modules from the first game loaded, causing imports from subsequent games to get the wrong modules.

## Solution

Clean up `sys.modules` and `sys.path` in BaseTestCase.tearDown() to prevent module cache pollution between tests.

## Implementation

### BaseTestCase.tearDown()

Add to [tests/base_test_case.py](../../tests/base_test_case.py):

```python
def tearDown(self):
    """Clean up test state to prevent module cache pollution."""
    super().tearDown()

    # Delete references in reverse order of creation
    # This ensures child objects release parent objects before cleanup
    for attr in ['accessor', 'behavior_manager', 'game_state']:
        if hasattr(self, attr):
            delattr(self, attr)

    # Remove all behaviors.* modules from sys.modules
    to_remove = [k for k in list(sys.modules.keys())
                 if k.startswith('behaviors.') or k == 'behaviors']
    for key in to_remove:
        del sys.modules[key]

    # Remove game directories from sys.path
    project_root = Path(__file__).parent.parent
    for game_name in ['big_game', 'spatial_game', 'extended_game', 'actor_interaction_test']:
        game_dir = str(project_root / "examples" / game_name)
        while game_dir in sys.path:
            sys.path.remove(game_dir)
```

### Critical: Cleanup Order

The cleanup MUST happen in this order:

1. **Delete accessor** - holds reference to behavior_manager
2. **Delete behavior_manager** - holds references to module objects in `._modules` dict
3. **Clean sys.modules** - remove module objects from Python's cache
4. **Clean sys.path** - remove game directories from import path

If you clean `sys.modules` before deleting `behavior_manager`, the modules stay in memory via the manager's `._modules` dictionary.

### Custom tearDown Functions

If a test has custom tearDown (e.g., to delete temp files or clean up GUI objects), it MUST call `super().tearDown()` to get module cleanup:

```python
class MyTest(BaseTestCase):
    def tearDown(self):
        # Custom cleanup FIRST
        if hasattr(self, 'temp_file'):
            self.temp_file.unlink()

        # MUST call super to get module cleanup
        super().tearDown()
```

**Tests with custom tearDown** (all now call super):
- `test_unknown_adjectives.py` - deletes temp vocab file, calls super
- `test_exits_preposition.py` - deletes temp vocab file, calls super
- `test_text_game_commands.py` - deletes temp vocab file, calls super
- `test_file_dialogs.py` - destroys wx.App objects (2 classes), calls super

All custom tearDown methods now properly call `super().tearDown()` to get module cleanup.

## Verification

### Real-World Testing Results

Tested with actual BehaviorManager loading:

```
=== Load big_game ===
Loaded 67 big_game modules

=== Cleanup ===
Removed 87 modules (includes sub-modules)
big_game in sys.path: False

=== Load spatial_game ===
Loaded 12 spatial_game modules
Big_game contamination: 0 modules ✅

=== Cleanup ===
Removed 13 modules

=== Reload big_game ===
Re-loaded 67 big_game modules ✅
```

**Key Results**:
- ✅ Zero contamination between games
- ✅ Can reload same game after different game
- ✅ Complete cleanup (all modules removed)
- ✅ Reliable across multiple cycles

### Leak Scenarios Tested

#### Scenario 1: BehaviorManager Module References
**Risk**: BehaviorManager._modules dict holds module objects

**Result**: Deleting `behavior_manager` before cleaning `sys.modules` prevents leak

#### Scenario 2: Multiple Load/Unload Cycles
**Risk**: Incomplete cleanup allows modules to accumulate

**Result**: Cleanup is complete - verified across 5 iterations

#### Scenario 3: sys.path Pollution
**Risk**: Game directories left in sys.path cause wrong imports

**Result**: `while` loop removes all occurrences successfully

## Benefits vs Subprocess Isolation

| Aspect | Module Cleanup | Subprocess Isolation |
|--------|----------------|---------------------|
| **Implementation** | ~20 lines in one location | ~10 lines per test file (12 files) |
| **Overhead** | <1ms per test | 50-200ms per test |
| **Works with unittest discover** | ✅ Yes | ❌ No - needs custom runner |
| **Coverage reporting** | ✅ Works normally | ⚠️ Requires --parallel-mode |
| **Debugging** | ✅ Easy (same process) | ❌ Harder (separate process) |
| **IDE integration** | ✅ Full support | ⚠️ Limited support |
| **Maintenance** | Single point | Each isolated test |

## Migration from Subprocess Isolation

### Tests Currently Using Subprocess Isolation (12 total)

**Big Game Scenarios**:
- test_uc1_infected_scholar
- test_uc2_guardian_golems
- test_uc3_wolf_pack
- test_uc4_healer_garden
- test_uc5_drowning_sailor
- test_uc6_injured_merchant
- test_uc7_spider_swarm
- test_uc8_broken_statue

**Spatial Game**:
- test_spatial_game_scenarios

**Infrastructure**:
- test_fungal_depths_scenarios
- test_sunken_district_scenarios
- test_cross_region_integration

### Migration Steps (Per Test)

1. Delete wrapper file (`test_xxx.py`)
2. Rename impl file (`test_xxx_impl.py` → `test_xxx.py`)
3. Verify test inherits from BaseTestCase (cleanup is automatic)
4. Run test 10+ times to verify reliability
5. Check test discovery works: `python -m unittest discover tests -v`

### Why This Works

The subprocess isolation pattern was added because tests failed context-dependently:
- Test passes when run individually: `python -m unittest tests.test_foo`
- Test fails in discovery: `python -m unittest discover tests`

Root cause: Python's module cache retains `behaviors.*` modules from first game loaded.

Module cleanup eliminates the root cause by ensuring each test starts with a clean module cache, making subprocess isolation unnecessary.

## Recommendation

**IMPLEMENT module cleanup in BaseTestCase.tearDown()**

This approach is:
- ✅ Proven reliable with real behavior loading
- ✅ Simpler (single point of implementation)
- ✅ Faster (no process overhead)
- ✅ Better for tooling (discovery, coverage, debugging)
- ✅ Lower maintenance (one location vs 12 files)

The theoretical risk of forgetting `super().tearDown()` is not a practical concern since:
1. Only 4 tests currently have custom tearDown
2. All 4 already call super() or do compatible cleanup
3. Can be detected by tooling if it becomes an issue
