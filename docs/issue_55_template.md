# Issue #55: Define and enforce behavior loading order across library tiers

## Problem

The current BehaviorManager uses a 1:1 verb→event mapping that prevents tier-based behavior libraries from working correctly. When Tier 1 defines "examine"→"on_examine_mushroom" and Tier 2 defines "examine"→"on_examine", only one event is stored in the mapping, blocking the shared library implementation needed for layered_game.

## Solution Overview

Implement directory depth-based tiering with both automatic event delegation and explicit handler delegation:

- **Directory depth-based tiers**: depth 0 = Tier 1, depth 1 = Tier 2, etc.
- **Automatic event delegation**: StateAccessor tries events in tier order until success
- **Explicit handler delegation**: Handlers can call `invoke_deeper_handler(verb, action)`
- **No breaking changes**: extended_game and simple_game continue working

## Design Document

See [docs/handler_precedence.md](docs/handler_precedence.md) for complete design including:
- Tier precedence rules (Tier 1 > Tier 2 > Tier 3)
- Conflict detection (error on within-tier conflicts, allow cross-tier)
- Handler delegation patterns (interception/augmentation)
- Event delegation patterns (automatic fallthrough)

## Implementation Plan

See [docs/handler_precedence_implementation.md](docs/handler_precedence_implementation.md) for phased implementation with TDD

## Success Criteria

- layered_game loads and runs with all three tiers working correctly
- extended_game and simple_game continue to work without changes
- Clear error messages for within-tier conflicts
- All tests pass with 80%+ coverage

---

**Command to create this issue:**
```bash
gh issue create --title "Define and enforce behavior loading order across library tiers" --body-file docs/issue_55_template.md
```
