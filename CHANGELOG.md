# Changelog

All notable changes to this text adventure engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added - Spatial Positioning System

A comprehensive spatial awareness and positioning system that enables position-dependent gameplay, tactical mechanics, and rich spatial interactions.

#### Part Entity System (Phase 1)
- **Part entity type** for spatial components of locations and items
- Parts can represent walls, sides of objects, room areas, etc.
- Parts support all standard entity features (descriptions, properties, behaviors, LLM context)
- Items can be placed at specific parts using `location: "part_id"`
- Full vocabulary integration with three-tier name matching (exact/synonym → phrase → case-insensitive)

#### Implicit Positioning (Phase 2)
- **`interaction_distance` property** controls proximity requirements
  - `"any"` (default) - Can interact from anywhere in location
  - `"near"` - Must be close to interact, triggers automatic movement
- **`focused_on` property** tracks actor's current position
- **Automatic positioning** in core commands:
  - `examine` - Moves to entity if `interaction_distance: "near"`
  - `look at <object>` - Redirects to examine (same positioning behavior)
  - `take` - Moves before taking
  - `open` - Moves before opening
  - `close` - Moves before closing
- **Helper functions** in `utilities/positioning.py`:
  - `try_implicit_positioning()` - Core positioning logic
  - `find_and_position_item()` - Combined find + position
  - `find_and_position_part()` - Part-specific positioning
  - `build_message_with_positioning()` - Message assembly
- Movement messages only appear when actually moving (not when re-examining focused entity)
- Posture cleared automatically when moving to different entity

#### Explicit Positioning (Phase 3)
- **`approach` command** for explicit player movement
  - Synonyms: "go to", "move to", "walk to"
  - Always sets focus and moves to target entity
  - Works with items, parts, and actors
  - Usage: `approach <object>`

#### Universal Surface Fallback (Phase 4)
- **Built-in universal surfaces** that exist in every location without requiring parts:
  - `ceiling` - "Nothing remarkable about the ceiling."
  - `floor` / `ground` - "Nothing remarkable about the floor."
  - `sky` - "The sky stretches above you."
  - `walls` - "The walls surround you."
- Explicit Part entities always override universal surface fallback
- Reduces Part entity overhead for simple rooms
- Helper functions in `behaviors/core/spatial.py`:
  - `get_universal_surface_nouns()` - List of surface words
  - `is_universal_surface()` - Check if word is universal surface
  - `get_default_description()` - Get default description

#### Posture System (Phase 5)
- **`posture` property** tracks special positioning modes
  - Values: `null` (default), `"cover"`, `"concealed"`, `"climbing"`, or custom
  - Automatically cleared when moving (only on actual movement)
  - Preserved when examining "any" distance items (no movement)
- **`take cover` command** for tactical positioning
  - Requires `provides_cover: true` on target entity
  - Sets `posture: "cover"` and `focused_on`
  - Synonyms: "hide behind"
  - Usage: `take cover behind <object>`
- **`hide` command** for concealment
  - Requires `allows_concealment: true` on target entity
  - Sets `posture: "concealed"` and `focused_on`
  - Synonym: "conceal"
  - Usage: `hide in <object>`
- **`climb` command** for vertical positioning and navigation
  - Requires `climbable: true` on target entity for positioning
  - Sets `posture: "climbing"` and `focused_on` when climbing items
  - Falls through to exit navigation if item not found or not climbable
  - Usage: `climb <object>`
  - Implementation: `behaviors/core/spatial.py` (items) and `behaviors/core/exits.py` (exits)

#### Documentation
- Complete authoring guide: `user_docs/authoring_spatial_rooms.md`
- Quick reference: `user_docs/spatial_quick_reference.md`
- Implementation patterns: `docs/implicit_positioning_patterns.md`
- Design documentation: `docs/spatial_implementation_v2.md`

#### Testing
- Comprehensive test coverage (60+ new tests)
- All phases implemented using Test-Driven Development (TDD)
- Zero regressions throughout implementation
- Total test count: 1,396 tests passing

### Changed
- `handle_examine` now redirects to positioning system when appropriate
- `handle_look` with object parameter redirects to `handle_examine`
- Movement only occurs for `interaction_distance: "near"` entities
- Posture clearing logic refined to only clear on actual movement

### Technical Details
- New module: `behaviors/core/spatial.py` - Spatial commands, universal surfaces, and climb posture
- Enhanced: `utilities/positioning.py` - Positioning helper functions
- Enhanced: `behaviors/core/perception.py` - Examine with universal surface fallback
- Enhanced: `behaviors/core/interaction.py` - Open/close with implicit positioning
- Enhanced: `behaviors/core/manipulation.py` - Take with implicit positioning
- Enhanced: `behaviors/core/exits.py` - Climb command for exit navigation
- Enhanced: `src/behavior_manager.py` - Removed within-tier conflict detection to allow multiple handlers per verb

---

## [Previous Versions]

Previous changes not yet documented. This CHANGELOG was created as part of the spatial positioning system implementation.
