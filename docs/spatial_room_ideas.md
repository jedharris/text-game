# Spatial Room Ideas - Leveraging Part Entities for Enhanced Gameplay

This document identifies room ideas from the brainstorming list that would substantially benefit from the game engine's spatial features. For each selected room, we explain how Part entities and the spatial positioning system would enhance gameplay.

## Selection Criteria

Rooms were selected when they would benefit from:
- **Multiple items at specific locations** - Walls, surfaces, or areas with 2+ items
- **Position-dependent interactions** - Player position matters for puzzle mechanics
- **Multi-sided objects** - Different features on different sides of an entity
- **Spatial zones within rooms** - Distinct areas with different properties
- **Cover/stealth mechanics** - Tactical positioning behind entities
- **Climbing/verticality** - Height-based interactions
- **Blocked access** - Obstacles preventing approach to specific parts

---

## Classic Dungeon / Crypt

### 2. Guardian Statue Hall (Conditional Combat)

**Spatial Enhancement:** Room parts for entrance area vs. statue area; cover mechanics behind pillars

```json
{
  "id": "part_hall_entrance",
  "entity_type": "part",
  "name": "entrance area",
  "part_of": "loc_statue_hall",
  "properties": {
    "description": "Near the main entrance doors.",
    "safe_distance": true
  }
}
```

```json
{
  "id": "part_hall_center",
  "entity_type": "part",
  "name": "center of hall",
  "part_of": "loc_statue_hall",
  "properties": {
    "description": "The open center where suits of armor stand.",
    "exposed": true
  }
}
```

```json
{
  "id": "item_pillar",
  "name": "pillar",
  "location": "loc_statue_hall",
  "properties": {
    "portable": false,
    "provides_cover": true,
    "interaction_distance": "near"
  }
}
```

**Gameplay:** Player can take cover behind pillars, affecting whether animated armor can reach them. Position in entrance area vs. center affects trigger conditions.

**Why This Works:**
- Parts define distinct spatial zones with different combat properties
- `provides_cover` property enables tactical positioning
- `posture: "cover"` tracks player taking cover behind pillars
- Behaviors can check `focused_on` to determine if player is in safe zone

---

### 4. Runic Floor Grid (Path Logic)

**Spatial Enhancement:** Floor part with multiple tile sub-areas; position tracking for puzzle

```json
{
  "id": "part_chamber_floor",
  "entity_type": "part",
  "name": "floor",
  "part_of": "loc_rune_chamber",
  "properties": {
    "description": "A grid of ancient rune tiles covers the floor."
  }
}
```

```json
{
  "id": "part_floor_center",
  "entity_type": "part",
  "name": "center of floor",
  "part_of": "loc_rune_chamber",
  "properties": {
    "rune": "sun",
    "description": "A tile carved with a sun rune."
  }
}
```

```json
{
  "id": "part_floor_north",
  "entity_type": "part",
  "name": "north side of floor",
  "part_of": "loc_rune_chamber",
  "properties": {
    "rune": "moon",
    "description": "A tile carved with a moon rune."
  }
}
```

**Gameplay:** Player must step on tiles in correct sequence. Behavior tracks which tiles have been stepped on by checking `focused_on` changes.

**Why This Works:**
- Each significant tile is a Part with properties (rune type, activation state)
- Player movement via `approach north side of floor` triggers tile logic
- Sequence tracking via behavior monitoring `focused_on` property changes
- Wrong sequence can trigger trap by checking tile properties

---

### 6. Spider Web Gallery (Environmental Hazard)

**Spatial Enhancement:** Wall parts with webs; careful positioning required

```json
{
  "id": "part_gallery_north_wall",
  "entity_type": "part",
  "name": "north wall",
  "part_of": "loc_web_gallery",
  "properties": {
    "covered_in_webs": true,
    "web_integrity": 100
  }
}
```

```json
{
  "id": "item_webs",
  "name": "webs",
  "location": "part_gallery_north_wall",
  "properties": {
    "portable": false,
    "burnable": true,
    "interaction_distance": "near"
  }
}
```

**Gameplay:** Player must approach walls carefully. Examining webs automatically positions near them. Actions like "burn webs" require being at specific wall parts.

**Why This Works:**
- Wall parts track web coverage and integrity per wall
- `interaction_distance: "near"` forces implicit positioning
- Different walls can have different web states
- Behaviors check if player is at web-covered part before allowing safe passage

---

### 10. Coffin Maze (Spatial / Mapping)

**Spatial Enhancement:** Each coffin as positioned entity; interior as climbable space

```json
{
  "id": "item_coffin_a",
  "name": "stone coffin",
  "location": "loc_crypt",
  "properties": {
    "portable": false,
    "openable": true,
    "states": {"open": false},
    "teleport_to": "item_coffin_d",
    "sigil": "circle"
  }
}
```

```json
{
  "id": "part_coffin_a_interior",
  "entity_type": "part",
  "name": "inside of coffin",
  "part_of": "item_coffin_a",
  "properties": {
    "description": "The coffin interior is marked with a circle sigil.",
    "allows_concealment": true
  }
}
```

**Gameplay:** Player climbs into coffins using spatial positioning. Each coffin's interior is a Part with orientation clues.

**Why This Works:**
- Each coffin is an entity with teleport destination property
- Interior parts provide distinct examination targets with clues
- `posture: "concealed"` tracks player inside coffin
- Behavior triggers teleport when player is concealed in coffin and closes lid

---

### 13. Weighted Idol Chamber (Physics-ish)

**Spatial Enhancement:** Pedestal with pressure plates as parts around it

```json
{
  "id": "item_pedestal",
  "name": "pedestal",
  "location": "loc_idol_chamber",
  "properties": {
    "portable": false,
    "interaction_distance": "near"
  }
}
```

```json
{
  "id": "part_pedestal_top",
  "entity_type": "part",
  "name": "top of pedestal",
  "part_of": "item_pedestal",
  "properties": {
    "current_weight": 500,
    "required_weight": 500
  }
}
```

```json
{
  "id": "part_chamber_floor",
  "entity_type": "part",
  "name": "floor",
  "part_of": "loc_idol_chamber",
  "properties": {
    "has_pressure_plates": true
  }
}
```

```json
{
  "id": "item_pressure_plate_north",
  "name": "pressure plate",
  "location": "part_chamber_floor",
  "properties": {
    "portable": false,
    "current_weight": 0,
    "description": "A stone pressure plate built into the floor."
  }
}
```

**Gameplay:** Player must approach pedestal, take idol, then place objects on pressure plates. Position matters for placing items.

**Why This Works:**
- Pedestal top is Part tracking weight
- Multiple pressure plates are items at floor part
- Player must be near pedestal to take idol
- Behaviors check weight on pedestal top and pressure plates
- Taking idol without replacing weight triggers trap behavior

---

## Mansion / Urban Mystery

### 16. Clockmaker's Workshop (Temporal Gating)

**Spatial Enhancement:** Multi-sided workbench with different tools/clocks per side

```json
{
  "id": "item_workbench",
  "name": "workbench",
  "location": "loc_workshop",
  "properties": {
    "portable": false,
    "interaction_distance": "near"
  }
}
```

```json
{
  "id": "part_bench_left",
  "entity_type": "part",
  "name": "left side of workbench",
  "part_of": "item_workbench",
  "properties": {
    "description": "Small clock pieces and delicate tools.",
    "tools": "repair"
  }
}
```

```json
{
  "id": "part_bench_center",
  "entity_type": "part",
  "name": "center of workbench",
  "part_of": "item_workbench",
  "properties": {
    "description": "The master clock with time control mechanism.",
    "tools": "time_control"
  }
}
```

```json
{
  "id": "item_master_clock",
  "name": "master clock",
  "location": "part_bench_center",
  "properties": {
    "portable": false,
    "windable": true,
    "current_time": 12
  }
}
```

**Gameplay:** Different workbench sides have different functions. Player must be at center to wind master clock, affecting game state.

**Why This Works:**
- Multi-sided object pattern with distinct tools per side
- Position-dependent actions: winding clock requires `focused_on == part_bench_center`
- Items organized by which part they're attached to
- Natural spatial organization matches physical workbench layout

---

### 17. Portrait Gallery (Social / Perception)

**Spatial Enhancement:** Wall parts with multiple portraits per wall

```json
{
  "id": "part_gallery_north_wall",
  "entity_type": "part",
  "name": "north wall",
  "part_of": "loc_portrait_gallery",
  "properties": {
    "description": "Several family portraits hang on this wall."
  }
}
```

```json
{
  "id": "item_portrait_father",
  "name": "father's portrait",
  "location": "part_gallery_north_wall",
  "properties": {
    "portable": false,
    "movable": true,
    "family_position": 1,
    "description": "A stern man in formal attire."
  }
}
```

```json
{
  "id": "item_portrait_mother",
  "name": "mother's portrait",
  "location": "part_gallery_north_wall",
  "properties": {
    "portable": false,
    "movable": true,
    "family_position": 2,
    "description": "A gentle woman with knowing eyes."
  }
}
```

**Gameplay:** Multiple portraits on each wall. Player must rearrange them in correct sequence. Wall parts organize portraits spatially.

**Why This Works:**
- Wall parts enable 2+ portraits per wall (meets part creation threshold)
- Location hierarchy clear: portraits at wall parts
- "On the north wall: father's portrait, mother's portrait" in room description
- Moving portraits stays within same wall part, reordering via properties
- Puzzle checks sequence by examining portraits at each wall part

---

### 21. Servant Passage Network (Secret Shortcuts)

**Spatial Enhancement:** Wall parts with hidden panels; peepholes as positioned features

```json
{
  "id": "part_study_east_wall",
  "entity_type": "part",
  "name": "east wall",
  "part_of": "loc_study",
  "properties": {
    "description": "Wood-paneled wall with elaborate molding."
  }
}
```

```json
{
  "id": "item_panel",
  "name": "panel",
  "location": "part_study_east_wall",
  "properties": {
    "portable": false,
    "openable": true,
    "states": {"open": false, "hidden": true},
    "leads_to": "loc_servant_passage"
  }
}
```

```json
{
  "id": "part_passage_west_wall",
  "entity_type": "part",
  "name": "west wall",
  "part_of": "loc_servant_passage",
  "properties": {
    "description": "The inner side of the wood paneling."
  }
}
```

```json
{
  "id": "item_peephole",
  "name": "peephole",
  "location": "part_passage_west_wall",
  "properties": {
    "portable": false,
    "viewpoint_to": "loc_study",
    "description": "A small hole for observing the study."
  }
}
```

**Gameplay:** Secret panels in wall parts lead to passages. Peepholes allow viewing other rooms.

**Why This Works:**
- Wall parts organize secret panels and peepholes spatially
- Explicit part references enable hidden connections between rooms
- Peephole at passage wall provides positioned viewpoint
- Player must approach wall to discover hidden panel
- Clear spatial relationship: panel on one side, peephole on other

---

### 25. Sealed Panic Room (Constrained Escape)

**Spatial Enhancement:** Wall parts with different escape mechanisms

```json
{
  "id": "part_panic_north_wall",
  "entity_type": "part",
  "name": "north wall",
  "part_of": "loc_panic_room",
  "properties": {
    "material": "reinforced steel",
    "description": "Solid metal plating."
  }
}
```

```json
{
  "id": "part_panic_ceiling",
  "entity_type": "part",
  "name": "ceiling",
  "part_of": "loc_panic_room",
  "properties": {
    "description": "Metal ceiling with ventilation grate."
  }
}
```

```json
{
  "id": "item_vent",
  "name": "ventilation grate",
  "location": "part_panic_ceiling",
  "properties": {
    "portable": false,
    "removable": true,
    "climbable": true,
    "description": "A narrow air vent."
  }
}
```

```json
{
  "id": "item_painting",
  "name": "painting",
  "location": "part_panic_north_wall",
  "properties": {
    "portable": false,
    "removable": true,
    "conceals": "item_panel_mechanism"
  }
}
```

**Gameplay:** Small room where every surface matters. Ceiling vent, wall mechanisms all positioned explicitly.

**Why This Works:**
- Ceiling part needed for vent (2+ items: vent + potentially duct work)
- Wall parts for multiple escape hints (painting + scratched codes + mechanisms)
- Climbing vent requires `posture: "climbing"` and `focused_on: item_vent`
- Explicit positioning emphasizes constrained space
- Each surface is interactive, justifying parts

---

### 29. City Rooftop Garden (Verticality / Risk)

**Spatial Enhancement:** Roof edges as parts; climbable features

```json
{
  "id": "part_roof_north_edge",
  "entity_type": "part",
  "name": "north edge",
  "part_of": "loc_rooftop",
  "properties": {
    "description": "The roof's edge overlooking the street below.",
    "drop_height": "three stories",
    "jump_difficulty": "hard"
  }
}
```

```json
{
  "id": "item_trellis",
  "name": "trellis",
  "location": "part_roof_north_edge",
  "properties": {
    "portable": false,
    "climbable": true,
    "climb_leads_to": "loc_balcony_below",
    "interaction_distance": "near"
  }
}
```

```json
{
  "id": "part_roof_center",
  "entity_type": "part",
  "name": "center of roof",
  "part_of": "loc_rooftop",
  "properties": {
    "description": "Safe area away from the edges.",
    "safe": true
  }
}
```

**Gameplay:** Player position determines risk. Approaching edges is dangerous. Climbing trellis requires specific positioning.

**Why This Works:**
- Edge parts have risk properties (fall danger, jump difficulty)
- Center area is safe zone
- Trellis at edge requires player to approach edge (risky)
- `posture: "climbing"` tracks climbing state
- Position-based risk: behaviors check if player at edge parts
- Multiple edges with different properties (some have trellises, others don't)

---

## Wilderness / Travel

### 34. Cliffside Nest (Vertical Challenge)

**Spatial Enhancement:** Cliff face with ledges as parts; climbing mechanics

```json
{
  "id": "part_cliff_face",
  "entity_type": "part",
  "name": "cliff face",
  "part_of": "loc_cliff_base",
  "properties": {
    "description": "Sheer rock face rising above you.",
    "climbable": true,
    "height": "50 feet"
  }
}
```

```json
{
  "id": "part_cliff_ledge",
  "entity_type": "part",
  "name": "narrow ledge",
  "part_of": "loc_cliff_base",
  "properties": {
    "description": "A narrow ledge halfway up the cliff.",
    "precarious": true,
    "height": "25 feet"
  }
}
```

```json
{
  "id": "item_nest",
  "name": "nest",
  "location": "part_cliff_ledge",
  "properties": {
    "portable": false,
    "description": "A large bird's nest with speckled eggs."
  }
}
```

**Gameplay:** Player must climb cliff face to reach ledge. Posture tracks climbing state. Position determines fall risk.

**Why This Works:**
- Cliff face and ledge are distinct parts at different heights
- `posture: "climbing"` tracks climbing state vs standing
- Nest at ledge part requires climbing to reach
- Height property enables fall damage calculations
- Position check: can only take eggs if `focused_on == part_cliff_ledge`

---

### 40. Abandoned Watchtower (Multi-Level)

**Spatial Enhancement:** Each floor as room part; climbable stairs/exterior

```json
{
  "id": "part_tower_ground_floor",
  "entity_type": "part",
  "name": "ground floor",
  "part_of": "loc_watchtower",
  "properties": {
    "description": "The crumbling base of the tower.",
    "floor_level": 0
  }
}
```

```json
{
  "id": "part_tower_second_floor",
  "entity_type": "part",
  "name": "second floor",
  "part_of": "loc_watchtower",
  "properties": {
    "description": "A partially collapsed upper level.",
    "floor_level": 1,
    "access_blocked": true
  }
}
```

```json
{
  "id": "item_exterior_stones",
  "name": "exterior wall",
  "location": "loc_watchtower",
  "properties": {
    "portable": false,
    "climbable": true,
    "climb_leads_to": "part_tower_second_floor",
    "interaction_distance": "near"
  }
}
```

**Gameplay:** Tower interior divided into floors as parts. Interior stairs blocked, must climb exterior.

**Why This Works:**
- Floor parts organize multi-level space within single location
- Items placed at specific floor parts
- `posture: "climbing"` when scaling exterior
- Access control: behaviors check if stairs are blocked before allowing approach to upper floors
- Vantage point mechanics: visibility properties per floor level

---

### 42. Flooded Tunnel (Breath / Time Limit)

**Spatial Enhancement:** Tunnel sections as parts; underwater items positioned

```json
{
  "id": "part_tunnel_entrance",
  "entity_type": "part",
  "name": "entrance section",
  "part_of": "loc_flooded_tunnel",
  "properties": {
    "description": "The tunnel entrance where water begins.",
    "water_depth": "ankle",
    "breathable": true
  }
}
```

```json
{
  "id": "part_tunnel_middle",
  "entity_type": "part",
  "name": "middle section",
  "part_of": "loc_flooded_tunnel",
  "properties": {
    "description": "Fully submerged tunnel passage.",
    "water_depth": "full",
    "breathable": false,
    "swim_distance": 3
  }
}
```

```json
{
  "id": "item_skeleton",
  "name": "skeleton",
  "location": "part_tunnel_middle",
  "properties": {
    "portable": false,
    "description": "A drowned adventurer's remains.",
    "underwater": true
  }
}
```

**Gameplay:** Each tunnel section has different water depth. Player must manage breath while traversing sections.

**Why This Works:**
- Parts divide tunnel into sections with varying water depth
- Breath tracking tied to which part player is focused on
- Items at different parts may be unreachable without swimming
- Movement between parts costs turns (breath)
- Clear spatial progression through tunnel sections

---

## Magical / Surreal

### 49. Gravity-Inverted Chamber (Movement Twists)

**Spatial Enhancement:** Floor and ceiling as parts that swap functionality

```json
{
  "id": "part_chamber_floor",
  "entity_type": "part",
  "name": "floor",
  "part_of": "loc_gravity_chamber",
  "properties": {
    "description": "Stone floor with strange engravings.",
    "currently_down": true
  }
}
```

```json
{
  "id": "part_chamber_ceiling",
  "entity_type": "part",
  "name": "ceiling",
  "part_of": "loc_gravity_chamber",
  "properties": {
    "description": "Stone ceiling with strange engravings.",
    "currently_down": false
  }
}
```

```json
{
  "id": "item_key",
  "name": "key",
  "location": "part_chamber_ceiling",
  "properties": {
    "portable": true,
    "states": {"fallen": false}
  }
}
```

**Gameplay:** Toggling gravity swaps which surface is "down". Items at ceiling fall to floor when gravity flips.

**Why This Works:**
- Explicit floor and ceiling parts needed for gravity mechanics
- Properties track which surface is currently "down"
- Items at ceiling become inaccessible until gravity flips
- Behavior swaps `currently_down` properties and moves items between parts
- Clear spatial model supports gravity inversion logic

---

### 51. Chessboard Hall (Symbolic Combat)

**Spatial Enhancement:** Floor grid with positioned squares as parts

```json
{
  "id": "part_floor_a1",
  "entity_type": "part",
  "name": "square a1",
  "part_of": "loc_chess_hall",
  "properties": {
    "chess_position": "a1",
    "color": "black",
    "occupied_by": null
  }
}
```

```json
{
  "id": "part_floor_e5",
  "entity_type": "part",
  "name": "square e5",
  "part_of": "loc_chess_hall",
  "properties": {
    "chess_position": "e5",
    "color": "white",
    "occupied_by": "npc_chess_knight"
  }
}
```

**Gameplay:** Each chess square is a Part. Movement restricted by chess rules based on which part you're focused on.

**Why This Works:**
- Each square is explicit Part with chess position property
- `focused_on` tracks player's current square
- Movement validation checks chess rules: can only approach valid destination squares
- Enemy positions tracked via `occupied_by` property on parts
- Grid-based positioning is natural use case for parts
- Behaviors enforce chess movement rules by checking positions

---

### 54. Time-Splintered Foyer (Parallel States)

**Spatial Enhancement:** Same room parts exist in multiple time states

```json
{
  "id": "part_foyer_north_wall_past",
  "entity_type": "part",
  "name": "north wall",
  "part_of": "loc_foyer_past",
  "properties": {
    "description": "Newly painted wall, pristine white.",
    "time_period": "past",
    "structural_integrity": 100
  }
}
```

```json
{
  "id": "part_foyer_north_wall_present",
  "entity_type": "part",
  "name": "north wall",
  "part_of": "loc_foyer_present",
  "properties": {
    "description": "Faded paint, some cracks visible.",
    "time_period": "present",
    "structural_integrity": 70
  }
}
```

```json
{
  "id": "part_foyer_north_wall_future",
  "entity_type": "part",
  "name": "north wall",
  "part_of": "loc_foyer_future",
  "properties": {
    "description": "Crumbling ruins, vines growing through holes.",
    "time_period": "future",
    "structural_integrity": 30
  }
}
```

**Gameplay:** Same spatial features in different time periods. Actions in one time affect corresponding parts in other times.

**Why This Works:**
- Same wall/floor/feature represented as separate parts in each time period
- Properties track time-specific state (integrity, damage, growth)
- Actions affect corresponding parts across time periods via behaviors
- Breaking wall in past affects present and future versions
- Player position tracked consistently across time shifts

---

## Technology / Sci-Fi

### 61. Airlock Antechamber (Pressurization)

**Spatial Enhancement:** Inner chamber vs. outer chamber as parts; control panels positioned

```json
{
  "id": "part_airlock_inner",
  "entity_type": "part",
  "name": "inner chamber",
  "part_of": "loc_airlock",
  "properties": {
    "description": "Safe pressurized area near ship entrance.",
    "pressurized": true,
    "atmosphere": "normal"
  }
}
```

```json
{
  "id": "part_airlock_outer",
  "entity_type": "part",
  "name": "outer chamber",
  "part_of": "loc_airlock",
  "properties": {
    "description": "Chamber exposed to space.",
    "pressurized": false,
    "atmosphere": "vacuum"
  }
}
```

```json
{
  "id": "item_control_panel_inner",
  "name": "control panel",
  "location": "part_airlock_inner",
  "properties": {
    "portable": false,
    "interaction_distance": "near",
    "controls": "inner_door"
  }
}
```

**Gameplay:** Player position determines survival. Must pressurize outer chamber before entering.

**Why This Works:**
- Inner and outer chambers as distinct parts with atmosphere properties
- Player position determines environmental effects
- Control panels at specific chamber parts
- Movement between parts requires proper pressurization sequence
- Being at outer part without suit is fatal

---

### 64. Robot Repair Bay (Ally Construction)

**Spatial Enhancement:** Multi-sided workbench with different tools per station

```json
{
  "id": "item_repair_station",
  "name": "repair station",
  "location": "loc_robot_bay",
  "properties": {
    "portable": false,
    "interaction_distance": "near"
  }
}
```

```json
{
  "id": "part_station_assembly",
  "entity_type": "part",
  "name": "assembly side",
  "part_of": "item_repair_station",
  "properties": {
    "description": "Robotic arms and assembly tools.",
    "function": "assembly"
  }
}
```

```json
{
  "id": "part_station_diagnostics",
  "entity_type": "part",
  "name": "diagnostics side",
  "part_of": "item_repair_station",
  "properties": {
    "description": "Monitors and scanning equipment.",
    "function": "diagnostics"
  }
}
```

```json
{
  "id": "part_station_programming",
  "entity_type": "part",
  "name": "programming side",
  "part_of": "item_repair_station",
  "properties": {
    "description": "Terminal for uploading robot software.",
    "function": "programming"
  }
}
```

**Gameplay:** Building robot requires going to different sides of station for different tasks.

**Why This Works:**
- Multi-sided object pattern - each side has specific function
- Position-dependent crafting: must be at assembly side to attach parts
- Player must explicitly approach each side for different construction phases
- Natural workflow: assemble → diagnose → program requires spatial movement
- Parts properties track which tools are available at each side

---

### 73. Zero-G Maintenance Shaft (3D Movement)

**Spatial Enhancement:** Shaft sections as parts; handhold positions

```json
{
  "id": "part_shaft_entrance",
  "entity_type": "part",
  "name": "entrance section",
  "part_of": "loc_maintenance_shaft",
  "properties": {
    "description": "The shaft opening with handholds.",
    "relative_position": "bottom",
    "gravity": 0.0
  }
}
```

```json
{
  "id": "part_shaft_middle",
  "entity_type": "part",
  "name": "middle section",
  "part_of": "loc_maintenance_shaft",
  "properties": {
    "description": "Shaft section with spinning fan.",
    "relative_position": "middle",
    "hazard": "rotating_blades"
  }
}
```

```json
{
  "id": "part_shaft_hatch_left",
  "entity_type": "part",
  "name": "left side hatch",
  "part_of": "loc_maintenance_shaft",
  "properties": {
    "description": "Access hatch on the left wall.",
    "relative_position": "middle_left",
    "leads_to": "loc_engineering"
  }
}
```

**Gameplay:** In zero-g, direction is relative. Parts represent 3D positions. Player must navigate using relative directions.

**Why This Works:**
- Parts define 3D positions without arbitrary coordinate system
- Natural language: "approach middle section", "approach left side hatch"
- Relative positioning via part properties
- Hazards at specific parts (fan at middle section)
- Side hatches as parts accessible from main shaft
- Movement between parts represents 3D navigation

---

## Social / Political / Civilized

### 81. Bank Vault (Heist)

**Spatial Enhancement:** Vault sections, guard positions, multiple approach vectors

```json
{
  "id": "part_vault_entrance",
  "entity_type": "part",
  "name": "entrance area",
  "part_of": "loc_bank_vault",
  "properties": {
    "description": "The main entrance with guard station.",
    "visibility": "high",
    "guard_patrol": true
  }
}
```

```json
{
  "id": "part_vault_main",
  "entity_type": "part",
  "name": "main vault floor",
  "part_of": "loc_bank_vault",
  "properties": {
    "description": "The open vault floor with safety deposit boxes.",
    "visibility": "medium"
  }
}
```

```json
{
  "id": "item_pillar",
  "name": "marble pillar",
  "location": "loc_bank_vault",
  "properties": {
    "portable": false,
    "provides_cover": true,
    "interaction_distance": "near"
  }
}
```

```json
{
  "id": "item_vent",
  "name": "ventilation duct",
  "location": "part_vault_ceiling",
  "properties": {
    "portable": false,
    "climbable": true,
    "stealth_entry": true
  }
}
```

**Gameplay:** Multiple approach vectors (entrance, ceiling vent, side door). Cover mechanics for stealth. Position determines visibility to guards.

**Why This Works:**
- Parts define zones with different visibility/patrol properties
- Cover mechanic: `posture: "cover"` behind pillars
- Ceiling part for vent entrance (alternate route)
- Guard behaviors check player position/posture for detection
- Multiple spatial strategies: sneak, social engineer, brute force

---

### 86. Training Dojo (Skill Checks)

**Spatial Enhancement:** Different training areas for different skills

```json
{
  "id": "part_dojo_combat_area",
  "entity_type": "part",
  "name": "combat practice area",
  "part_of": "loc_dojo",
  "properties": {
    "description": "Padded floor with practice dummies.",
    "training_type": "combat"
  }
}
```

```json
{
  "id": "item_practice_dummy",
  "name": "practice dummy",
  "location": "part_dojo_combat_area",
  "properties": {
    "portable": false,
    "interaction_distance": "near",
    "skill_taught": "melee_combat"
  }
}
```

```json
{
  "id": "part_dojo_meditation_area",
  "entity_type": "part",
  "name": "meditation area",
  "part_of": "loc_dojo",
  "properties": {
    "description": "Quiet corner with cushions.",
    "training_type": "focus"
  }
}
```

**Gameplay:** Different training activities require being in specific areas. Spatial organization matches dojo function.

**Why This Works:**
- Parts divide dojo by training type
- Position check: can only train combat at combat area
- Items (dummies, equipment) positioned at appropriate parts
- Natural spatial organization of training facility
- Different instructors positioned at different training areas

---

## Boss / Finale / Set-Piece Rooms

### 91. Multi-Phase Boss Arena (Environment-Driven Fight)

**Spatial Enhancement:** Platforms as parts; elemental vent positioning

```json
{
  "id": "part_arena_center_platform",
  "entity_type": "part",
  "name": "center platform",
  "part_of": "loc_boss_arena",
  "properties": {
    "description": "The main fighting platform.",
    "stable": true,
    "elevation": "medium"
  }
}
```

```json
{
  "id": "part_arena_north_platform",
  "entity_type": "part",
  "name": "north platform",
  "part_of": "loc_boss_arena",
  "properties": {
    "description": "A smaller platform near the fire vent.",
    "stable": false,
    "elevation": "medium"
  }
}
```

```json
{
  "id": "item_fire_vent",
  "name": "fire vent",
  "location": "part_arena_north_platform",
  "properties": {
    "portable": false,
    "activatable": true,
    "element": "fire",
    "affects_area": "part_arena_north_platform"
  }
}
```

```json
{
  "id": "item_pillar",
  "name": "stone pillar",
  "location": "loc_boss_arena",
  "properties": {
    "portable": false,
    "provides_cover": true,
    "interaction_distance": "near"
  }
}
```

**Gameplay:** Player must move between platforms to activate vents. Boss adapts to player position. Cover behind pillars.

**Why This Works:**
- Platform parts define combat zones
- Vent items positioned at specific platforms
- Player position determines which vent they can activate
- Boss behaviors track player's `focused_on` for tactical response
- Cover mechanic for defensive positioning
- Platform properties (stable/unstable) affect available actions

---

### 96. Fractured Reality Nexus (Logical Final Puzzle)

**Spatial Enhancement:** Floating platform parts representing game systems

```json
{
  "id": "part_nexus_combat_platform",
  "entity_type": "part",
  "name": "combat platform",
  "part_of": "loc_reality_nexus",
  "properties": {
    "description": "Platform glowing with violent red energy.",
    "represents": "combat_system",
    "challenge_completed": false,
    "floating": true
  }
}
```

```json
{
  "id": "part_nexus_stealth_platform",
  "entity_type": "part",
  "name": "stealth platform",
  "part_of": "loc_reality_nexus",
  "properties": {
    "description": "Platform shrouded in shadow.",
    "represents": "stealth_system",
    "challenge_completed": false,
    "floating": true
  }
}
```

```json
{
  "id": "part_nexus_social_platform",
  "entity_type": "part",
  "name": "social platform",
  "part_of": "loc_reality_nexus",
  "properties": {
    "description": "Platform with ghostly figures.",
    "represents": "social_system",
    "challenge_completed": false,
    "floating": true
  }
}
```

**Gameplay:** Each platform is a mini-challenge. Player must approach platforms and complete challenges. Final door opens when 2+ completed.

**Why This Works:**
- Platform parts represent abstract game systems spatially
- Player explicitly approaches platforms to engage challenges
- Part properties track completion state
- Natural metaphor: moving through abstract space completing challenges
- Spatial positioning creates memorable final puzzle
- "Approach combat platform" maps mental challenge selection to spatial action

---

## Summary

### Common Spatial Patterns in Selected Rooms

1. **Multi-sided workbenches/stations** - Clockmaker's Workshop, Robot Repair Bay, Training Dojo
   - Different tools/functions per side
   - Position-dependent actions

2. **Wall-mounted items** - Portrait Gallery, Servant Passages, Panic Room
   - 2+ items per wall justifies wall parts
   - Secret panels and features at walls

3. **Cover and stealth** - Guardian Hall, Bank Vault, Boss Arena
   - `provides_cover` property on pillars
   - `posture: "cover"` for tactical positioning

4. **Verticality and climbing** - Cliffside Nest, Rooftop Garden, Watchtower
   - `posture: "climbing"` for climbing state
   - Ledges/floors as parts at different heights

5. **Room zones** - Airlock, Flooded Tunnel, Multi-phase Arena
   - Distinct areas with different properties
   - Position determines environmental effects

6. **Floor/ceiling puzzles** - Runic Floor, Gravity Chamber, Chessboard Hall
   - Grid positions or spatial configuration as parts
   - Movement tracking via `focused_on` changes

### Why These Rooms Need Spatial Features

All selected rooms share these characteristics:
- **Position matters mechanically** - Wrong position = failed action or different outcome
- **Multiple items at locations** - Walls with 2+ items, floors with multiple features
- **Environmental zones** - Areas with different properties (safe/dangerous, pressurized/vacuum)
- **Tactical positioning** - Cover, stealth, height advantage
- **Multi-faceted objects** - Different sides have different tools/features
- **Spatial puzzles** - Configuration, sequence, or positioning is the puzzle

### Architecture Alignment

These rooms align perfectly with the game engine's spatial system:

✅ **Part entities** - All spatial features are first-class entities with IDs, properties, behaviors

✅ **Implicit positioning** - `interaction_distance: "near"` enables automatic movement for natural flow

✅ **Explicit positioning** - `approach` command for puzzle-dependent positioning

✅ **Property-based** - All spatial data in properties dict (height, integrity, gravity, visibility)

✅ **Behavior-driven** - Custom behaviors check `focused_on` for position-dependent logic

✅ **Progressive disclosure** - Simple use cases ignore spatial features, complex games leverage them

✅ **Entity uniformity** - Parser resolves parts through normal vocabulary system, no special cases

The spatial system was designed exactly for these kinds of rich, position-dependent gameplay scenarios.
