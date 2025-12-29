# Architectural Improvements and Development Process Enhancements

**Status:** Planning Document
**Created:** 2025-12-29
**Context:** Ideas generated after completing the Hook System Redesign (9-phase project)

## Overview

This document captures architectural improvements and development process enhancements identified during and after the Hook System Redesign project. The hook system redesign demonstrated that systematic, well-planned refactoring with comprehensive testing pays off. Similar approaches would work well for these improvements.

## Prioritization Framework

Improvements are categorized by priority based on value/effort ratio:

- **High Priority**: Immediate value, low risk, good ROI
- **Medium Priority**: Good ROI, moderate effort
- **Lower Priority**: Nice to have, can defer

---

## High Priority Improvements

### 1. Automated Validation Suite

**Problem**: Many content errors only discovered at runtime or during manual testing.

**Solution**: Create comprehensive validators similar to hook validation.

**Scope**:
- **Game content validation**
  - Validate all `game_state.json` files for common errors
  - Check required fields, ID formats, valid references
  - Detect orphaned entities (referenced but not defined)
  - Verify property structures match expected patterns

- **Behavior module validation**
  - Verify all required functions exist (handle_*, on_*)
  - Check function signatures match expected patterns
  - Validate vocabulary structure and required fields
  - Detect common mistakes (wrong parameter names, missing returns)

- **Walkthrough validation**
  - Automated walkthrough runner as CI check
  - Expected outcomes vs actual outcomes
  - Coverage metrics (what % of content is tested)

- **Cross-reference validation**
  - All referenced IDs exist (location, item, actor, lock IDs)
  - No orphaned entities
  - Behavior module paths are valid
  - Event/hook references are defined

**Implementation**:
1. Create `src/validators/` package
2. Validators for each domain (content, behaviors, references)
3. CLI tool: `python -m validators.validate_game examples/big_game`
4. Integration with test suite
5. Clear error messages with location and fix suggestions

**Success Metrics**:
- 90%+ of authoring errors caught at load/validation time
- Validation runs in <5 seconds for big_game
- Zero false positives in existing content

**Effort**: 1-2 weeks
**Value**: High - prevents runtime errors, improves author experience

---

### 2. Better Error Messages Throughout

**Problem**: Many error messages lack context and actionable guidance.

**Solution**: Apply hook system error message patterns everywhere.

**Principles** (from hook system):
- Show what went wrong and where it happened
- Include relevant context (entity IDs, locations, state)
- Suggest how to fix it
- Point to documentation when relevant

**Areas to Improve**:

1. **Parser errors**
   ```python
   # Bad
   "Parse error"

   # Good
   "Cannot parse command: 'take the red from box'
     Expected: [verb] [adjective?] [noun] [preposition?] [indirect_object?]
     Problem: 'from' is not a recognized preposition
     Did you mean: 'take red key from box'?"
   ```

2. **Runtime errors**
   ```python
   # Bad
   "Item not found"

   # Good
   "Item 'item_magic_sword' not found
     Referenced by: Actor 'npc_guard' in behaviors/guards.py:42
     Available items in location 'loc_armory': ['item_shield', 'item_helmet']
     Fix: Check item ID spelling or ensure item is in correct location"
   ```

3. **Validation errors**
   ```python
   # Bad
   "Invalid property"

   # Good
   "Invalid property 'helth' in actor 'player'
     Defined in: game_state.json:15
     Did you mean: 'health'?
     Valid core fields: id, name, description, location, inventory
     Custom properties go in 'properties' dict"
   ```

**Implementation**:
1. Audit all error/exception sites in codebase
2. Create error message templates/helpers
3. Add context objects to capture state
4. Update tests to verify error messages

**Effort**: 2-3 weeks
**Value**: High - dramatically improves debugging experience

---

### 3. Fix Type System Issues

**Problem**: Several type inconsistencies causing mypy errors and confusion.

**Critical Fixes**:

1. **locations.values() error**
   ```python
   # Current (WRONG)
   locations: List[Location]  # But code calls .values()

   # Fix
   locations: Dict[LocationId, Location]
   # Update all access patterns
   ```

2. **Missing type annotations in utilities**
   - Add full type coverage to `utilities/` package
   - Remove `Any` types where possible
   - Use TypedDict for dict structures

3. **Inconsistent ID types**
   - Enforce typed IDs everywhere (LocationId, ActorId, etc.)
   - No bare strings for entity references
   - Type checkers catch ID mismatches

**Implementation**:
1. Fix locations dict structure (breaking change, needs migration)
2. Add types to all utilities
3. Enable strict mypy for utilities/
4. Create type stubs for any untyped dependencies

**Effort**: 1 week
**Value**: High - prevents entire class of bugs, improves IDE experience

---

### 4. Development Tools

**Problem**: Common tasks require manual work and are error-prone.

**Tools to Build**:

1. **Game content linter**
   ```bash
   python -m tools.lint examples/big_game
   ```
   - Check vocabulary consistency
   - Enforce naming conventions
   - Detect common mistakes
   - Suggest improvements
   - Integration with pre-commit hooks

2. **Behavior scaffolding generator**
   ```bash
   python -m tools.scaffold behavior my_game/custom_magic
   ```
   - Generate behavior module template
   - Includes vocabulary structure
   - Placeholder handler functions
   - Test file template
   - Documentation template

3. **Interactive debugger/REPL**
   ```bash
   python -m tools.debug examples/big_game
   ```
   - Load game state
   - Inspect entities interactively
   - Test commands without LLM
   - Modify state and test effects
   - Save modified state

4. **Dependency visualizer**
   ```bash
   python -m tools.visualize dependencies examples/big_game
   ```
   - Show turn phase execution order (graph)
   - Behavior module dependencies
   - Entity relationship graphs
   - Vocabulary composition (what overrides what)

**Implementation**:
1. Create `tools/` package
2. Each tool as separate module
3. Shared utilities for common operations
4. Rich CLI output (colors, tables, graphs)

**Effort**: 2-3 weeks
**Value**: High - accelerates development, reduces errors

---

## Medium Priority Improvements

### 5. Vocabulary System Refactor

**Problem**: Vocabulary system has grown organically, lacks clear structure.

**Improvements**:

1. **Unified vocabulary schema validation**
   - Define schema for vocabulary structure
   - Validate at load time (like hooks)
   - Clear error messages for schema violations
   - Version vocabulary schema for compatibility

2. **Vocabulary composition patterns**
   - Explicit rules for merge/override behavior
   - Layering: core → library → game
   - Conflict detection (multiple modules define same verb)
   - Composition debugging (where did this word come from?)

3. **LLM context standardization**
   ```python
   # Define standard schema
   @dataclass
   class LLMContext:
       traits: List[str]
       valid_objects: Optional[List[str]]
       state_variants: Optional[Dict[str, str]]
       examples: Optional[List[str]]
   ```
   - Type checking for llm_context
   - Required vs optional fields
   - Validation of field values

**Implementation**:
1. Define vocabulary schema (JSON Schema or dataclass)
2. Add schema validation to BehaviorManager
3. Document composition rules
4. Migrate existing vocabularies to schema
5. Add debugging tools

**Effort**: 2-3 weeks
**Value**: Medium-High - cleaner system, better validation

---

### 6. State Access Audit

**Problem**: Code mixes direct `game_state` access with `StateAccessor` patterns.

**Goals**:
1. **Single source of truth**: All state access through StateAccessor
2. **No bypassing**: Enforce accessor usage
3. **Read-only views**: Prevent accidental mutations

**Changes**:

1. **Audit all game_state access**
   ```bash
   # Find all direct access
   grep -r "game_state\." src/ behaviors/ behavior_libraries/
   # Review and migrate to accessor
   ```

2. **Make StateAccessor comprehensive**
   - Add any missing accessor methods
   - Ensure all entity types covered
   - Consistent naming patterns

3. **Consider read-only views**
   ```python
   class ReadOnlyGameState:
       """Immutable view of game state."""
       def __setattr__(self, name, value):
           raise AttributeError("Cannot modify read-only game state")
   ```

**Implementation**:
1. Inventory all direct access patterns
2. Add missing accessor methods
3. Migrate code to use accessor
4. Add runtime checks (debug mode only)
5. Update documentation

**Effort**: 2-3 weeks
**Value**: Medium - prevents bugs, clearer boundaries

---

### 7. Entity Lifecycle Hooks

**Problem**: No way to react to entity creation, destruction, or major state changes.

**Solution**: Add lifecycle hooks similar to turn phases.

**Hook Types**:

1. **Creation hooks**
   ```python
   vocabulary = {
       "hook_definitions": [{
           "hook_id": "entity_created",
           "invocation": "entity",
           "description": "Called when entity is created"
       }],
       "events": [{
           "event": "on_entity_created",
           "hook": "entity_created"
       }]
   }

   def on_entity_created(entity, accessor, context):
       # Initialize derived state
       # Set up relationships
       # Trigger effects
   ```

2. **Destruction hooks**
   - `entity_destroyed` - Before entity removed
   - Cleanup resources, update relationships

3. **Movement hooks**
   - `entity_moved` - After location change
   - Trigger traps, update tracking

4. **State change hooks**
   - `entity_state_changed` - Generic state changes
   - Context includes old/new values

**Use Cases**:
- Traps triggered when item enters location
- NPCs react to new actors entering their location
- Cleanup when entity destroyed
- Logging/tracking entity movements

**Implementation**:
1. Define lifecycle hook names
2. Add invocation points in StateAccessor
3. Update hook validation
4. Create examples
5. Document patterns

**Effort**: 1-2 weeks
**Value**: Medium - enables new behaviors, cleaner code

---

### 8. Documentation Generation

**Problem**: Documentation gets out of sync with code.

**Solution**: Auto-generate reference documentation from code.

**Generated Docs**:

1. **Hook reference**
   ```bash
   python -m tools.doc_gen hooks > docs/reference/hooks.md
   ```
   - Extract all hooks from vocabularies
   - Group by type (turn_phase, entity)
   - Show dependencies
   - List events that use each hook

2. **Event catalog**
   ```bash
   python -m tools.doc_gen events > docs/reference/events.md
   ```
   - All events with descriptions
   - Which behaviors handle them
   - Example usage

3. **Vocabulary reference**
   ```bash
   python -m tools.doc_gen vocab examples/big_game > docs/reference/vocabulary.md
   ```
   - All verbs, nouns, adjectives
   - Synonyms and alternate forms
   - Which modules contribute each word

4. **API documentation**
   ```bash
   python -m tools.doc_gen api > docs/reference/api.md
   ```
   - Extract from docstrings
   - Type signatures
   - Usage examples

**Implementation**:
1. Create doc generation framework
2. Templates for each doc type
3. Extraction logic
4. Markdown generation
5. CI integration (regenerate on change)

**Effort**: 2 weeks
**Value**: Medium - always up-to-date docs

---

### 9. Testing Infrastructure Improvements

**Problem**: Writing tests requires boilerplate, fixtures scattered.

**Improvements**:

1. **Behavior test helpers**
   ```python
   from test_helpers import BehaviorTestCase

   class TestMyBehavior(BehaviorTestCase):
       def test_fire_spell(self):
           # Helper loads minimal state
           state = self.minimal_state()
           actor = self.add_actor(state, "wizard")
           target = self.add_actor(state, "goblin")

           # Helper invokes behavior
           result = self.invoke("on_cast_spell", actor, {
               "spell": "fireball",
               "target": target.id
           })

           self.assertSuccess(result)
           self.assertDamage(target, amount=20)
   ```

2. **Game state fixtures**
   ```python
   from test_fixtures import (
       empty_location,
       basic_combat_setup,
       inventory_test_setup
   )

   def test_combat():
       state = basic_combat_setup()  # Player + enemy + weapons
       # Test combat mechanics
   ```

3. **Performance benchmarks**
   ```python
   from benchmarks import benchmark

   @benchmark(max_time_ms=100)
   def test_parse_complex_command():
       # Ensure parsing stays fast
   ```

4. **Integration test framework**
   ```python
   from test_scenarios import GameScenario

   scenario = GameScenario("examples/big_game")
   scenario.run_commands([
       "take sword",
       "go north",
       "attack goblin"
   ])
   scenario.assert_state({
       "player.location": "loc_cave_entrance",
       "npc_goblin.states.health": 80
   })
   ```

**Implementation**:
1. Create `tests/helpers/` package
2. Reusable test base classes
3. Fixture library
4. Assertion helpers
5. Scenario framework

**Effort**: 2-3 weeks
**Value**: Medium - faster test writing, better coverage

---

## Lower Priority Improvements

### 10. Behavior Module Discovery & Plugin System

**Problem**: Behavior modules use manual lists and symlinks.

**Solution**: Standardized plugin/module system.

**Features**:

1. **Plugin registration**
   ```python
   # In behavior module
   from src.plugin_system import register_plugin

   @register_plugin(
       name="advanced_magic",
       version="1.0.0",
       requires=["core>=0.5.0"],
       provides=["spell_system", "mana_management"]
   )
   class AdvancedMagicPlugin:
       def load(self, game_engine):
           # Register behaviors
           pass
   ```

2. **Dependency declaration**
   - Modules declare what they depend on
   - Automatic dependency resolution
   - Version compatibility checking

3. **Discovery**
   - Auto-discover from configured paths
   - No manual registration needed
   - Plugin metadata in standardized location

**Effort**: 3-4 weeks
**Value**: Low-Medium - nice to have, current system works

---

### 11. Consistent Naming Conventions

**Problem**: Some naming is inconsistent across systems.

**Solution**: Apply hook-style prefixes to other systems.

**Conventions**:

1. **Events**: Already using `on_*` prefix
   - Continue this pattern
   - Add `before_*`, `after_*` for lifecycle

2. **Properties**: Use domain prefixes
   ```python
   # Instead of mixed bag in properties dict
   properties = {
       "health": 100,
       "is_locked": True,
       "description_override": "...",
       "faction": "guards"
   }

   # Use prefixed organization
   properties = {
       "stat_health": 100,
       "stat_mana": 50,
       "flag_locked": True,
       "flag_invisible": False,
       "meta_faction": "guards",
       "meta_description_override": "..."
   }
   ```

3. **Handlers**: Already using `handle_*`
   - Enforce more strictly
   - Catch violations in linter

**Effort**: 2-3 weeks (if migrating existing content)
**Value**: Low - consistency nice but not critical

---

### 12. Unified Result Types

**Problem**: Mix of `EventResult`, `HandlerResult`, `UpdateResult`.

**Solution**: Unify or clarify relationships.

**Options**:

1. **Single result type with context**
   ```python
   @dataclass
   class Result:
       success: bool
       message: Optional[str]
       data: Optional[Dict[str, Any]]
       context: ResultContext  # NEW

   class ResultContext(Enum):
       EVENT = "event"
       HANDLER = "handler"
       UPDATE = "update"
   ```

2. **Clarify current types**
   - Document when to use each
   - Conversion utilities
   - Consistent patterns for composition

**Effort**: 2-3 weeks
**Value**: Low-Medium - current system works, just inconsistent

---

### 13. LLM Integration Cleanup

**Problem**: LLM logic mixed with game logic, redundant calls.

**Improvements**:

1. **Separate narration logic**
   - Clear boundary between game state and narration
   - Narration as separate layer
   - Game logic never calls LLM directly

2. **Standardized prompt construction**
   ```python
   from narration import PromptTemplate

   template = PromptTemplate.load("combat_narration")
   prompt = template.render({
       "attacker": actor,
       "defender": target,
       "weapon": weapon,
       "damage": damage_dealt
   })
   ```

3. **Caching strategy**
   - Cache entity descriptions
   - Cache location descriptions
   - Invalidate on state changes only

4. **Fallback handling**
   - Offline mode (no LLM available)
   - API failure recovery
   - Degraded mode (basic text only)

**Effort**: 3-4 weeks
**Value**: Low-Medium - current system functional

---

### 14. CoreFieldProtectingDict Expansion

**Problem**: Only protects properties dict currently.

**Solution**: Extend to other dicts.

**Protection for**:

1. **States dict**
   ```python
   actor.states = CoreFieldProtectingDict(
       actor._states,
       core_fields=["health", "mana"],
       error_msg="Use actor.health or actor.mana, not actor.states['health']"
   )
   ```

2. **Stats dict** (if we add one)
   - Enforce stat validation
   - Type checking for numeric stats
   - Range validation

3. **Properties validation**
   - Known property patterns
   - Type checking
   - Deprecation warnings

**Effort**: 1 week
**Value**: Low - nice to have, catches mistakes earlier

---

## Process Improvements

### 15. Phased Development Template

**Success**: The 9-phase hook redesign approach worked extremely well.

**Create template for**:

1. **Large refactors**
   - Standard phasing strategy
   - How to break into phases
   - Commit boundaries
   - Testing between phases

2. **Issue templates**
   - Phase issue format
   - Success criteria checklist
   - Files modified section
   - Dependencies tracking

3. **Design doc template**
   - Required sections
   - Phasing plan format
   - Validation approach
   - Migration strategy

**Template structure**:
```markdown
# [Feature/Refactor Name]

## Problem Statement
[What needs to change and why]

## Goals
[Clear objectives]

## Non-Goals
[Explicitly out of scope]

## Design
[High-level approach]

## Phases
### Phase 1: [Name]
- Goal: [What this phase achieves]
- Changes: [What code changes]
- Tests: [What tests added]
- Success: [How we know it worked]
- Commit: [Commit message pattern]

[... more phases ...]

## Validation Strategy
[How we ensure correctness]

## Migration Path
[How existing content migrates]

## Risks
[What could go wrong]
```

**Effort**: 1-2 days
**Value**: High - accelerates future large changes

---

### 16. Commit Strategy & Changelog

**Current**: Good commit messages, but no automated tracking.

**Improvements**:

1. **Enforce commit message format**
   ```
   <type>(<scope>): <subject>

   <body>

   <footer>

   🤖 Generated with [Claude Code](https://claude.com/claude-code)
   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
   ```
   - Types: feat, fix, docs, refactor, test, chore
   - Scope: module or feature area
   - Breaking changes marked in footer

2. **Automated changelog**
   ```bash
   python -m tools.changelog --since v0.5.0
   ```
   - Generate from commits
   - Group by type
   - Link to issues
   - Highlight breaking changes

3. **Breaking change tracking**
   ```
   BREAKING CHANGE: locations is now Dict, not List

   Migration: Update all `for loc in locations:` to `for loc in locations.values():`
   ```

**Effort**: 1 week
**Value**: Medium - better project tracking

---

### 17. Continuous Integration

**Problem**: No automated testing on push/PR.

**Solution**: CI pipeline.

**Pipeline**:

1. **Pre-commit hooks**
   ```bash
   # Runs on git commit
   - mypy src/
   - python -m tests.fast_tests
   - python -m validators.lint
   ```

2. **CI (GitHub Actions)**
   ```yaml
   on: [push, pull_request]

   jobs:
     test:
       - Run full test suite
       - Run all walkthroughs
       - Check test coverage (80%+)
       - Run mypy strict
       - Run game content validator
       - Build documentation
   ```

3. **Coverage tracking**
   - Track coverage over time
   - Prevent coverage from decreasing
   - Highlight uncovered new code

**Effort**: 1-2 weeks
**Value**: High - catch errors before merge

---

## Implementation Strategy

### Suggested Order

Based on dependencies and impact:

**Phase 1** (1-2 months):
1. Fix type system issues (foundational)
2. Better error messages throughout
3. Development tools (linter, scaffolder)
4. CI pipeline setup

**Phase 2** (1-2 months):
5. Automated validation suite
6. Testing infrastructure improvements
7. Documentation generation
8. Phased development template

**Phase 3** (2-3 months):
9. Vocabulary system refactor
10. State access audit
11. Entity lifecycle hooks

**Phase 4** (As needed):
12. Lower priority items based on pain points

### Measuring Success

For each improvement track:
- **Errors prevented**: How many bugs caught earlier
- **Time saved**: Developer time saved
- **Code quality**: Coverage, type safety metrics
- **Author experience**: Survey feedback from game authors

---

## Conclusion

The hook system redesign proved that systematic refactoring pays off:
- Clear phasing
- Comprehensive testing
- Excellent documentation
- No backward compatibility hacks

Apply the same discipline to these improvements for similar success.

**Next Steps**:
1. Review and prioritize this list
2. Create issues for high-priority items
3. Design first improvement using template
4. Execute in phases with full testing

**Questions for Discussion**:
- Which improvements provide the most value?
- What are current biggest pain points?
- What dependencies exist between improvements?
- What's a realistic timeline for Phase 1?
