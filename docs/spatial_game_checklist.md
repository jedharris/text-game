# Spatial Game Implementation Checklist

Quick reference for implementing examples/spatial_game.

## Pre-Implementation Review
- [x] Design document reviewed: [docs/spatial_game_design.md](spatial_game_design.md)
- [x] Implementation notes created: [docs/spatial_game_implementation_notes.md](spatial_game_implementation_notes.md)
- [x] Ready status confirmed: [docs/spatial_game_ready_to_implement.md](spatial_game_ready_to_implement.md)
- [x] Existing code patterns identified
- [x] No design issues remaining

## Phase 1: Setup and Structure
- [ ] Copy examples/extended_game to examples/spatial_game
- [ ] Create behaviors/lib/spatial/ directory
- [ ] Create behaviors/lib/core/ symlink → ../../../../behaviors/core/
- [ ] Move behaviors/core symlink if it exists at root level
- [ ] Verify all existing behaviors copied (crystal_ball.py, magic_mat.py, magic_wand.py, spellbook.py)
- [ ] Test: Run game, verify it loads without errors

## Phase 2: Vocabulary Updates
- [ ] Add "of" to src/vocabulary.json prepositions
- [ ] Add "out" to src/vocabulary.json prepositions
- [ ] Test: Verify parser accepts "out of" compound preposition

## Phase 3: Magic Star Behavior (Tier 1)
- [ ] Create behaviors/magic_star.py
- [ ] Implement on_climb(entity, accessor, context)
  - [ ] Check actor posture == "on_surface"
  - [ ] Check actor focused_on == "item_garden_bench"
  - [ ] Return failure if not on bench
  - [ ] Return success with appropriate message
- [ ] Implement on_take(entity, accessor, context)
  - [ ] Check actor posture == "climbing"
  - [ ] Check actor focused_on == "item_tree"
  - [ ] Return failure if not climbing
  - [ ] Return success (allow taking)
- [ ] Write unit tests:
  - [ ] Test climb tree without bench position (should fail)
  - [ ] Test climb tree from bench (should succeed)
  - [ ] Test take star without climbing (should fail)
  - [ ] Test take star while climbing (should succeed)

## Phase 4: Stand/Sit Library (Tier 2)
- [ ] Create behaviors/lib/spatial/__init__.py
- [ ] Create behaviors/lib/spatial/stand_sit.py
- [ ] Add vocabulary (stand, sit verbs with indirect_object_required)
- [ ] Implement handle_stand_on(accessor, action)
  - [ ] Get actor and surface name
  - [ ] Find surface using find_accessible_item()
  - [ ] Check container.is_surface property
  - [ ] Set actor.properties["focused_on"] = surface.id
  - [ ] Set actor.properties["posture"] = "on_surface"
  - [ ] Return success message
- [ ] Implement handle_sit_on(accessor, action)
  - [ ] Use same logic as handle_stand_on
- [ ] Write unit tests:
  - [ ] Test stand on surface (should succeed)
  - [ ] Test stand on non-surface (should fail)
  - [ ] Test posture set correctly
  - [ ] Test focused_on set correctly
  - [ ] Test sit on surface (should succeed)

## Phase 5: Look Out Library (Tier 2)
- [ ] Create behaviors/lib/spatial/look_out.py
- [ ] Add vocabulary (look verb with indirect_object_required)
- [ ] Implement handle_look_out_of(accessor, action)
  - [ ] Positive test: Check preposition is "out of" or "out"
  - [ ] Return failure (empty message) if wrong preposition
  - [ ] Get indirect_object (window name)
  - [ ] Try find_and_position_part() first
  - [ ] Try find_and_position_item() if part not found
  - [ ] Get entity's description property
  - [ ] Return success with description
- [ ] Write unit tests:
  - [ ] Test look out of window (should succeed)
  - [ ] Test with wrong preposition (should fail gracefully)
  - [ ] Test description displayed correctly
  - [ ] Test no positioning movement occurs

## Phase 6: Crystal Ball Modification (Tier 1)
- [ ] Modify behaviors/crystal_ball.py handle_peer()
- [ ] Add proximity check after finding item:
  - [ ] Get interaction_distance property
  - [ ] If "near", check actor's focused_on property
  - [ ] Check focused_on == item.id OR focused_on == item.location
  - [ ] Return failure with helpful message if not positioned
- [ ] Keep on_peer() unchanged (sanctum key logic)
- [ ] Write unit tests:
  - [ ] Test peer without positioning (should fail)
  - [ ] Test examine stand then peer (should succeed)
  - [ ] Test examine ball then peer (should succeed)
  - [ ] Test key revelation still works

## Phase 7: Entity Updates (game_state.json)
- [ ] Modify item_garden_bench
  - [ ] Add description: "...It looks sturdy enough to stand on."
  - [ ] Add container.is_surface: true
- [ ] Add item_tree entity
  - [ ] id: "item_tree"
  - [ ] name: "tree"
  - [ ] description: "An old oak tree..."
  - [ ] location: "loc_garden"
  - [ ] properties: climbable: true, interaction_distance: "near"
  - [ ] behaviors: ["behaviors.magic_star"]
- [ ] Add item_magic_star entity
  - [ ] id: "item_magic_star"
  - [ ] name: "star"
  - [ ] description: "A crystalline star..."
  - [ ] location: "item_tree"
  - [ ] properties: portable: true, magical: true
  - [ ] behaviors: ["behaviors.magic_star"]
- [ ] Add part_library_window entity
  - [ ] id: "part_library_window"
  - [ ] name: "window"
  - [ ] part_of: "loc_library"
  - [ ] properties.description: "Through the large arched window..."
  - [ ] properties.interaction_distance: "any"
- [ ] Modify item_crystal_ball
  - [ ] Add interaction_distance: "near" to properties
- [ ] Update loc_garden items array
  - [ ] Ensure "item_tree" in items list (not "item_magic_star" - it's in tree)
- [ ] Validate game state:
  - [ ] Run: python -m src.game_engine examples/spatial_game --validate

## Phase 8: Integration Testing
- [ ] Test full garden puzzle chain:
  - [ ] examine bench → positions at bench
  - [ ] stand on bench → sets posture/focus
  - [ ] climb tree → checks posture/focus, sets climbing
  - [ ] take star → checks posture/focus, allows taking
- [ ] Test crystal ball without auto-position:
  - [ ] peer into ball → fails with message
  - [ ] examine stand → positions at stand
  - [ ] peer into ball → succeeds (checks container)
- [ ] Test crystal ball alternate approach:
  - [ ] examine ball → positions at ball
  - [ ] peer into ball → succeeds
- [ ] Test window viewing:
  - [ ] look out of window → displays view, no movement
- [ ] Test tier precedence:
  - [ ] Use --debug to verify module loading
  - [ ] Check tier assignments (1, 2, 3)
  - [ ] Verify handler precedence (game > library > core)

## Phase 9: Final Verification
- [ ] Run full game playthrough
- [ ] Test all original extended_game features still work
- [ ] Test all new spatial features work
- [ ] Verify no core behavior modifications were needed
- [ ] Check library behaviors are reusable (no game-specific hardcoding)
- [ ] Run with --debug to verify tier structure
- [ ] Run with --show-traits to verify llm_context
- [ ] Update issue with completion report

## Success Criteria
- [ ] All tier assignments correct (Tier 1, 2, 3)
- [ ] Garden puzzle fully functional
- [ ] Crystal ball requires explicit positioning
- [ ] Look out of window works without positioning
- [ ] All game mechanics use clean separation of concerns
- [ ] No core behavior modifications
- [ ] Library behaviors are truly reusable
- [ ] All tests pass
- [ ] Game plays correctly end-to-end

## Reference Documents
- **Design:** [docs/spatial_game_design.md](spatial_game_design.md)
- **Implementation Notes:** [docs/spatial_game_implementation_notes.md](spatial_game_implementation_notes.md)
- **Ready Status:** [docs/spatial_game_ready_to_implement.md](spatial_game_ready_to_implement.md)
- **User Guide Tiers:** [user_docs/game_authors.md](../user_docs/game_authors.md) (lines 722-773)
- **Dev Guide Tiers:** [user_docs/engine_documentation.md](../user_docs/engine_documentation.md) (lines 372-404)
