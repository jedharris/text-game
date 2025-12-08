# Big Game Implementation Coordination

Implementation coordination for "The Shattered Meridian" game.

**Main tracking issue:** TBD (create after this doc)

---

## Work Streams

| Stream | Scope | Session | Status |
|--------|-------|---------|--------|
| A | Fungal Depths region | VS Code Session 2 | Not started |
| B | Beast Wilds region | VS Code Session 3 | Not started |
| C | Frozen Reaches + Sunken District | VS Code Session 4 | Not started |
| D | Core systems + Hub + Integration | Main session | Not started |

---

## Shared Conventions

### Directory Structure

```
big_game/
├── data/
│   ├── locations/
│   │   ├── fungal_depths.json      # Stream A
│   │   ├── beast_wilds.json        # Stream B
│   │   ├── frozen_reaches.json     # Stream C
│   │   ├── sunken_district.json    # Stream C
│   │   ├── meridian_nexus.json     # Stream D
│   │   └── civilized_remnants.json # Stream D
│   ├── actors/
│   │   ├── fungal_actors.json      # Stream A
│   │   ├── beast_actors.json       # Stream B
│   │   ├── frozen_actors.json      # Stream C
│   │   ├── sunken_actors.json      # Stream C
│   │   ├── nexus_actors.json       # Stream D
│   │   └── town_actors.json        # Stream D
│   ├── items/
│   │   ├── fungal_items.json       # Stream A
│   │   ├── beast_items.json        # Stream B
│   │   ├── frozen_items.json       # Stream C
│   │   ├── sunken_items.json       # Stream C
│   │   ├── nexus_items.json        # Stream D
│   │   └── town_items.json         # Stream D
│   └── game_state.json             # Stream D (assembles all)
├── behaviors/
│   ├── regions.py                  # Stream D
│   ├── factions.py                 # Stream D
│   ├── world_events.py             # Stream D
│   └── npc_specifics/
│       ├── the_echo.py             # Stream D
│       └── scholar_aldric.py       # Stream A (condition logic)
└── narrator_style.txt              # Stream D
```

### ID Conventions

**Locations:**
- `loc_fd_*` - Fungal Depths (Stream A)
- `loc_bw_*` - Beast Wilds (Stream B)
- `loc_fr_*` - Frozen Reaches (Stream C)
- `loc_sd_*` - Sunken District (Stream C)
- `loc_mn_*` - Meridian Nexus (Stream D)
- `loc_cr_*` - Civilized Remnants/Town (Stream D)

**Actors:**
- `npc_fd_*` - Fungal Depths NPCs
- `npc_bw_*` - Beast Wilds NPCs
- `npc_fr_*` - Frozen Reaches NPCs
- `npc_sd_*` - Sunken District NPCs
- `npc_mn_*` - Meridian Nexus NPCs
- `npc_cr_*` - Town NPCs
- `creature_*` - Non-speaking creatures
- `faction_*` - Virtual faction actors

**Items:**
- `item_fd_*` - Fungal Depths items
- `item_bw_*` - Beast Wilds items
- `item_fr_*` - Frozen Reaches items
- `item_sd_*` - Sunken District items
- `item_mn_*` - Meridian Nexus items
- `item_cr_*` - Town items
- `item_key_*` - Key items (quest critical)

### Property Conventions

**Actors with dialog:**
```json
{
  "dialog_topics": {
    "topic_name": {
      "keywords": ["word1", "word2"],
      "summary": "What they say about this.",
      "unlocks_topics": [],
      "sets_flags": {},
      "requires_flags": {},
      "one_time": false
    }
  }
}
```

**Actors with conditions:**
```json
{
  "conditions": {
    "condition_name": {
      "severity": 0-100,
      "tick_rate": 1,
      "effects": {}
    }
  }
}
```

**Locations with environmental effects:**
```json
{
  "properties": {
    "region": "fungal_depths",
    "spore_level": "none|low|medium|high",
    "temperature": "normal|cold|freezing",
    "light_level": "bright|dim|dark",
    "terrain": "underground|forest|water|ice"
  }
}
```

---

## GitHub Workflow

Each stream must:

1. **Create a phase issue** at the start:
   ```bash
   gh issue create --title "Big Game Stream X: [Region Name]" --body "..."
   ```

2. **Add comments** documenting work as it progresses

3. **Close the issue** when complete with a summary comment

---

## Session Prompts

### Stream A: Fungal Depths (Copy this to VS Code Session 2)

```
I need you to create the Fungal Depths region for "The Shattered Meridian" game.

FIRST: Create a GitHub issue for this work:
gh issue create --title "Big Game Stream A: Fungal Depths Region" --body "Create all locations, actors, and items for the Fungal Depths region. See docs/big_game_overview.md for design and docs/big_game_coordination.md for conventions."

REFERENCE DOCUMENTS:
- docs/big_game_overview.md - Full game design (read the Fungal Depths section)
- docs/big_game_coordination.md - ID conventions and file structure
- user_docs/authoring_manual/ - How to create game content

YOUR TASK:
Create game data files (NOT behavior code) for the Fungal Depths region:

1. big_game/data/locations/fungal_depths.json
   - 5 locations: cavern_entrance, luminous_grotto, spore_heart, myconid_sanctuary, deep_root_caverns
   - Use loc_fd_* IDs
   - Include exits connecting them
   - Set properties: region, spore_level, light_level

2. big_game/data/actors/fungal_actors.json
   - Scholar Aldric (dying, has dialog_topics about infection, cure)
   - Myconid Elder (faction representative)
   - Myconid guards/healers
   - Spore Mother (corrupted, can be healed)
   - Spore creatures (hostile until region purified)
   - Use npc_fd_* or creature_fd_* IDs

3. big_game/data/items/fungal_items.json
   - Glowing mushrooms (light sources)
   - Spore samples (for cure)
   - Myconid offerings
   - Scholar's notes
   - Use item_fd_* IDs

USE BEHAVIOR LIBRARIES (don't write custom code):
- dialog_lib for NPC conversations
- darkness_lib for cave darkness
- offering_lib for Myconid shrine

For Scholar Aldric's infection timer, just set up the condition data structure - Stream D will wire up the behavior.

When complete:
1. Add a comment to your issue summarizing what you created
2. Close the issue
3. Report back what files you created
```

### Stream B: Beast Wilds (Copy this to VS Code Session 3)

```
I need you to create the Beast Wilds region for "The Shattered Meridian" game.

FIRST: Create a GitHub issue for this work:
gh issue create --title "Big Game Stream B: Beast Wilds Region" --body "Create all locations, actors, and items for the Beast Wilds region. See docs/big_game_overview.md for design and docs/big_game_coordination.md for conventions."

REFERENCE DOCUMENTS:
- docs/big_game_overview.md - Full game design (read the Beast Wilds section)
- docs/big_game_coordination.md - ID conventions and file structure
- user_docs/authoring_manual/ - How to create game content

YOUR TASK:
Create game data files (NOT behavior code) for the Beast Wilds region:

1. big_game/data/locations/beast_wilds.json
   - 5 locations: forest_edge, wolf_clearing, bee_grove, predator_den, spider_nest
   - Use loc_bw_* IDs
   - Include exits connecting them
   - Set properties: region, terrain, light_level

2. big_game/data/actors/beast_actors.json
   - Alpha Wolf (can become companion)
   - Wolf pack members (pack coordination)
   - Giant bees (territorial)
   - Spiders (hostile, swarm behavior)
   - Injured wolf cub (rescue quest)
   - Use creature_bw_* IDs

3. big_game/data/items/beast_items.json
   - Healing herbs
   - Wolf tokens (pack trust)
   - Honey (from bees)
   - Spider silk
   - Beast pelts
   - Use item_bw_* IDs

USE BEHAVIOR LIBRARIES (don't write custom code):
- companion_lib for wolf companion following
- npc_movement_lib for wolf patrol routes

For pack coordination, set up the actor properties - Stream D will wire up coordination behavior if needed.

When complete:
1. Add a comment to your issue summarizing what you created
2. Close the issue
3. Report back what files you created
```

### Stream C: Frozen Reaches + Sunken District (Copy this to VS Code Session 4)

```
I need you to create the Frozen Reaches and Sunken District regions for "The Shattered Meridian" game.

FIRST: Create a GitHub issue for this work:
gh issue create --title "Big Game Stream C: Frozen Reaches + Sunken District" --body "Create all locations, actors, and items for Frozen Reaches and Sunken District regions. See docs/big_game_overview.md for design and docs/big_game_coordination.md for conventions."

REFERENCE DOCUMENTS:
- docs/big_game_overview.md - Full game design (read both region sections)
- docs/big_game_coordination.md - ID conventions and file structure
- user_docs/authoring_manual/ - How to create game content

YOUR TASK:
Create game data files (NOT behavior code) for both regions:

FROZEN REACHES:
1. big_game/data/locations/frozen_reaches.json
   - 5 locations: frozen_pass, temple_sanctum, ice_caves, hot_springs, frozen_observatory
   - Use loc_fr_* IDs
   - Set properties: region, temperature, light_level

2. big_game/data/actors/frozen_actors.json
   - Ice elemental guardian
   - Frozen scholars (can be thawed)
   - Temple keepers
   - Use npc_fr_* or creature_fr_* IDs

3. big_game/data/items/frozen_items.json
   - Heat sources
   - Frozen artifacts
   - Observatory repair parts
   - Use item_fr_* IDs

SUNKEN DISTRICT:
4. big_game/data/locations/sunken_district.json
   - 5 locations: flooded_streets, submerged_library, air_pocket_chamber, drainage_controls, sunken_shrine
   - Use loc_sd_* IDs
   - Set properties: region, water_level, light_level

5. big_game/data/actors/sunken_actors.json
   - Drowning sailor (time-limited rescue)
   - Water spirits
   - Undead scholars
   - Use npc_sd_* or creature_sd_* IDs

6. big_game/data/items/sunken_items.json
   - Waterproof containers
   - Diving equipment
   - Waterlogged books
   - Drainage keys
   - Use item_sd_* IDs

USE BEHAVIOR LIBRARIES:
- timing_lib for drowning sailor countdown
- darkness_lib for underwater visibility
- puzzle_lib for drainage puzzle

When complete:
1. Add a comment to your issue summarizing what you created
2. Close the issue
3. Report back what files you created
```

---

## Stream D: Core Systems (Main Session)

Stream D work (this session):
1. Create directory structure
2. Create main GitHub issue
3. Implement regions.py, factions.py, world_events.py
4. Create Meridian Nexus and Civilized Remnants data
5. Implement The Echo behavior
6. Create game_state.json that assembles all regions
7. Integration testing

---

## Progress Checklist

### Stream A: Fungal Depths
- [ ] Issue created
- [ ] Locations file created
- [ ] Actors file created
- [ ] Items file created
- [ ] Issue closed with summary

### Stream B: Beast Wilds
- [ ] Issue created
- [ ] Locations file created
- [ ] Actors file created
- [ ] Items file created
- [ ] Issue closed with summary

### Stream C: Frozen + Sunken
- [ ] Issue created
- [ ] Frozen locations file created
- [ ] Frozen actors file created
- [ ] Frozen items file created
- [ ] Sunken locations file created
- [ ] Sunken actors file created
- [ ] Sunken items file created
- [ ] Issue closed with summary

### Stream D: Core + Hub
- [ ] Issue created
- [ ] Directory structure created
- [ ] regions.py implemented
- [ ] factions.py implemented
- [ ] world_events.py implemented
- [ ] Nexus locations created
- [ ] Town locations created
- [ ] The Echo behavior implemented
- [ ] game_state.json assembled
- [ ] Integration tests pass
- [ ] Issue closed with summary

---

## Merge Order

1. Streams A, B, C complete their data files (can be parallel)
2. Stream D creates game_state.json importing all region data
3. Stream D runs integration tests
4. All issues closed, main issue closed
