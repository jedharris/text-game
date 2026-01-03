## Design priorities
- Always maximize author capability and player agency, especially when they don't conflict
- When adding features, do as much as necessary to make all relevant entities first-class citizens, participating fully in game narration and action.
- Separation of concerns: Engine manages state, LLM narrates
- Behavior-driven extension: New functionality via external modules, not core modifications
- Validation over runtime checks: Fail fast during load, not during play
- Property-based entities: Flexible properties dict, minimal core fields 

## Coding guidelines
- NEVER build vocabulary into the code, instead ALWAYS use the merged vocabulary and WordEntry.
- NEVER add local heuristics for word matching or special vocabulary
- Vocabulary handling rules apply to testing as well as normal code
- **Start here for new sessions**: `docs/Guides/claude_session_guide.md` - Critical gotchas, decision tree, essential patterns
- **Primary reference**: `docs/Guides/quick_reference.md` - Condensed API reference, common utilities
- For detailed information, consult:
  - `docs/Guides/authoring_guide.md` for utility routines, handler patterns, and common pitfalls
  - `docs/Guides/debugging_guide.md` for vocabulary, parsing, and error diagnosis
  - `docs/Guides/test_style_guide.md` for test structure and patterns
  - `user_docs/architectural_conventions.md` for type system and core architecture
- Use existing utility functions from `utilities/handler_utils.py` and `utilities/utils.py` rather than writing custom code

## Handler design
- Handlers should test positively for what they CAN handle, not negatively for what they CAN'T handle
- Each handler should check if the target entity is the right type for that handler, then return failure if not
- This maintains clean separation of concerns and avoids cross-module dependencies
- Example: exits.py checks if target is an exit and rejects non-exits; spatial.py checks if target is climbable and rejects non-climbable items

## Role of game engine vs. LLM  
- in any LLM augmented game, the game engine must be responsible for all state management, including all state changes caused by user commands.
- The LLM should never cause state changes, it should only narrate state changes.

## Testing
- use unittest, do not use pytest
- Tests must use the same parameter types, data formats, and calling conventions as production code
- Never create test-specific shortcuts, variant data formats, or simplified calling patterns
- If a test needs to call a function, it should call it exactly as production code would
- Test helpers should wrap complexity, not change interfaces
- When loading game state for tests, use the same loading functions as the real game
- When sending commands for tests, use the same message format as the real game engine

## Game Authoring Workflow (MANDATORY)

When authoring or updating game content (regions, behaviors, items, NPCs), follow these requirements:

### 1. Walkthrough-Driven Development
- ALWAYS create a comprehensive walkthrough test file BEFORE claiming completion
- The walkthrough must cover all new/modified mechanics, items, NPCs, and interactions
- Include EXPECTED FAILURES in walkthrough comments where mechanics intentionally block actions
- 100% success means all expected behaviors occur (including expected failures), not all actions succeeding
- Run the walkthrough using `tools/walkthrough.py` and verify results
- NEVER declare completion without a successful walkthrough run

### 2. Common Pitfalls (Red Flags)
If you encounter any of these, STOP and discuss with user:
- Event handler function names don't exactly match event names in vocabulary
- Behavior module paths in game_state.json don't match actual load paths
- Using `state.items.get()` instead of `next()` comprehension (items is a list)
- Using `next()` for `state.actors` instead of `.get()` (actors is a dict)
- Item_use_reactions on the tool instead of the target item
- Multi-word item names sharing common words without unique synonyms
- Claiming "mostly working" or "98% complete" without walkthrough verification

### 3. Completion Criteria
Work is complete ONLY when:
- Comprehensive walkthrough file exists in `walkthroughs/`
- Walkthrough has been run with `tools/walkthrough.py`
- All expected behaviors occur (success AND intentional failures as documented)
- Any unexpected failures have been diagnosed and fixed
- Results have been verified and shared with user

## Breaking changes
- For the current development phase, we will continue to change the code base in ways that make a new version of the game unable to run old game save files. Right now such changes are are fine if they lead to cleaner designs.
- Going forward, when changes make incompatible changes to the game save format, do not provide backward compatibility within the code base. Instead create a separate tool that migrates the previous format game save files to the new format files.

## Refactoring
- For codebase-wide refactoring (renaming functions, changing method calls, updating type annotations), use `tools/refactor_using_LibCST`
- LibCST (Concrete Syntax Tree) preserves formatting and comments, unlike AST-based approaches
- The tool has composable transformers: RenameFunction, ChangeMethodCall, RenameKeywordArg, UpdateTypeAnnotation, AddImport, etc.
- Edit `create_transformer()` in the script to configure which transformations to apply
- Run with `--dry-run` first to preview changes before applying
- Avoid sed for refactoring; it introduces errors and doesn't understand Python syntax