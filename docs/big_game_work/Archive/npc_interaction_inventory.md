# NPC Interaction Inventory

Extracted from walkthroughs to validate against game_state.json implementation.

**Last validated**: 2025-12-21

**Phase 1 Complete**: Alpha Wolf pack, Hunter Sira, Healer Elara, Myconid Elder, Curiosity Dealer Vex

## Summary by Region

| Region | NPCs | Dialog-based | Item-based | Combat | Status |
|--------|------|--------------|------------|--------|--------|
| Fungal Depths | 4 | Aldric, Myconid Elder, Spore Mother | Spore Mother (heartmoss) | Sporelings | **PHASE 1 DONE** - Aldric + Elder complete, Spore Mother has llm_context |
| Beast Wilds | 5 | Sira, Bee Queen | Alpha Wolf (venison), Bee Queen (flowers) | Wolf Pack, Spiders, Bear | **PHASE 1 DONE** - Sira + Wolf Pack complete, Bee Queen pending |
| Frozen Reaches | 2 | Salamanders | Salamanders (fire gifts) | Stone Guardians | MISSING - custom handler needed |
| Sunken District | 4 | Mira, Jek, Archivist | Rescue items | Predatory fish | MISSING - no dialog_topics |
| Civilized Remnants | 10+ | Many merchants/council | Guardian repair | None | **PHASE 1 PARTIAL** - Elara + Vex complete, others missing |
| Meridian Nexus | 2 | The Echo, Waystone | Waystone (fragments) | None | PARTIAL - Echo has custom handler |

---

## Fungal Depths

### Scholar Aldric (`npc_aldric`)
**Location**: Cavern Entrance
**Walkthrough references**: fungal_depths_walkthrough.md, cross_region_walkthrough_A

**Dialog interactions**:
| Command | Expected Response | Topic/Handler |
|---------|------------------|---------------|
| `talk to aldric` | Lists available topics | dialog_topics |
| `ask aldric about infection` | Explains fungal infection | dialog_topics.infection |
| `ask aldric about research` | Discusses his studies | dialog_topics.research |
| `ask aldric about spore mother` | (requires flag) Explains her situation | dialog_topics.spore_mother |
| `ask aldric about help` | (requires commitment state) Teaching offer | dialog_topics.help_commitment |

**Item interactions**:
| Command | Expected Response |
|---------|------------------|
| `give silvermoss to aldric` | Healing, gratitude, commitment fulfilled |

**State requirements**:
- Has `dialog_topics` with conditional topics
- Has `state_machine` (healthy, recovering, critical)
- Timer-based survival mechanic

---

### Spore Mother (`npc_spore_mother`)
**Location**: Spore Heart
**Walkthrough references**: fungal_depths_walkthrough.md lines 462-496, 640-663

**Dialog interactions**:
| Command | Expected Response | Notes |
|---------|------------------|-------|
| `talk to spore mother` | Spore-based communication, senses pain/plea | NON-VERBAL |
| | Creates temporary peace, sporelings don't attack | Custom handler needed |

**Walkthrough quote** (line 462):
> The Spore Mother's massive cap turns toward you. A wave of spores washes over you - not an attack, but... communication? You sense pain, desperation, a plea for help.

**Item interactions**:
| Command | Expected Response |
|---------|------------------|
| `give heartmoss to spore mother` | Major healing event, region-wide effect |

**Implementation notes**:
- Does NOT use standard dialog_topics
- Needs custom `talk` handler for spore communication
- Currently has `item_use_reactions.healing` (heartmoss works)
- Missing: talk/dialog handler

---

### Myconid Elder (`npc_myconid_elder`)
**Location**: Myconid Sanctuary
**Walkthrough references**: fungal_depths_walkthrough.md lines 686-792

**Dialog interactions**:
| Command | Expected Response | Notes |
|---------|------------------|-------|
| `talk to myconid elder` | Blue spores, asks why player came | dialog_topics |
| `ask elder about cure` | Green spores, explains cure cost | dialog_topics.cure |
| `ask elder about resistance` | Explains spore resistance teaching | dialog_topics.resistance |
| `ask elder about spore mother` | Information about her | dialog_topics.spore_mother |

**Walkthrough quote** (line 686):
> The Myconid releases a cloud of blue spores. Somehow, you understand: "Soft-flesh comes to the Still Place. Why?"
> You could ask the Elder about: cure, resistance, spore mother

**Services**:
- `cure_infection` - requires payment (ice_crystal, rare_mineral, gold)
- `teach_spore_resistance` - requires trust

**Implementation notes**:
- Currently has `services` but NO `dialog_topics`
- Dialog is how player learns about services
- Missing: dialog_topics for cure, resistance, spore_mother

---

### Sporelings
**Location**: Various in Fungal Depths
**Walkthrough references**: fungal_depths_walkthrough.md

**Interactions**: Combat only, controlled by Spore Mother's pack_behavior

---

## Sunken District

*Note: No walkthrough exists for this region. Data extracted from sunken_district_detailed_design.md*

### Camp Leader Mira (`camp_leader_mira`)
**Location**: Survivor Camp
**Source**: sunken_district_detailed_design.md

**Dialog interactions**:
| Command | Expected Response |
|---------|------------------|
| `talk to mira` | Explains survivor situation |
| `ask mira about district` | History of the flooding |
| `ask mira about safe paths` | Directions through flooded areas |

**game_state.json status**: Actor exists, NO `dialog_topics` configured

---

### Old Swimmer Jek (`old_swimmer_jek`)
**Location**: Survivor Camp
**Source**: sunken_district_detailed_design.md

**Services**: `teaches: basic_swimming` (cost: 5 gold)

**Dialog interactions** (expected):
| Command | Expected Response |
|---------|------------------|
| `talk to jek` | Introduces himself, mentions swimming |
| `ask jek about swimming` | Offers to teach |

**game_state.json status**: Actor exists, NO `dialog_topics` configured

---

### The Archivist (`the_archivist`)
**Location**: Deep Archive
**Source**: sunken_district_detailed_design.md

**Dialog interactions** (expected):
| Command | Expected Response |
|---------|------------------|
| `talk to archivist` | Spectral guardian, explains archive |
| `ask about water pearl` | Quest details |

**game_state.json status**: Actor exists, NO `dialog_topics` configured

---

### Sailor Garrett (`sailor_garrett`)
**Location**: Sea Caves
**Source**: sunken_district_detailed_design.md

**Interactions**: Rescue scenario (drowning), commitment-based
- No dialog needed - immediate action situation

**game_state.json status**: Actor exists with rescue mechanics

---

### Merchant Delvan (`merchant_delvan`)
**Location**: Merchant Warehouse
**Source**: sunken_district_detailed_design.md

**Interactions**: Rescue scenario (trapped/bleeding), commitment-based
- Dialog after rescue possible

**game_state.json status**: Actor exists with rescue mechanics

---

## Beast Wilds

### Alpha Wolf / Wolf Pack (`alpha_wolf`)
**Location**: Wolf Den (note: walkthrough says "Wolf Clearing" but game_state.json has `wolf_den`)
**Walkthrough references**: beast_wilds_walkthrough.md lines 117-189

**Interactions**: Item-based trust building, NOT dialog
| Command | Expected Response |
|---------|------------------|
| `give venison to alpha` | Trust increases, pack calms |
| `wait` (non-threatening) | Relationship stabilizes |

**game_state.json status**:
- ✅ Actor exists with trust_state, pack_behavior, gift_reactions handler
- ✅ No dialog_topics needed (wolves don't speak)

---

### Hunter Sira (`hunter_sira`)
**Location**: Hunter's Camp (walkthrough says "Southern Trail")
**Walkthrough references**: beast_wilds_walkthrough.md lines 320-467

**Dialog interactions**:
| Command | Expected Response |
|---------|------------------|
| `talk to sira` | Explains injury, asks for help |
| `ask sira about injury` | Describes what happened |
| `ask sira about tracking` | (after healing) Offers to teach |

**Walkthrough quote** (line 345):
> "Another one," she rasps. "Come to finish what the beasts started?"

**Item interactions**:
| Command | Expected Response |
|---------|------------------|
| `use bandages on sira` | Stabilizes bleeding |
| `give bloodmoss tincture to sira` | Stops bleeding |
| `use splint on sira` | Fixes leg |

**Commitment trigger**: "I'll find a healer for you" -> commitment to find Elara

**game_state.json status**:
- ✅ Actor exists with state_machine, conditions, commitment_target, item_use_reactions
- ❌ NO `dialog_topics` configured - player cannot talk to her
- Connection to healer_elara configured

---

### Bee Queen (`bee_queen`)
**Location**: Bee Queen's Clearing
**Walkthrough references**: beast_wilds_walkthrough.md lines 191-223

**Dialog interactions**:
| Command | Expected Response | Notes |
|---------|------------------|-------|
| `talk to queen` | Antennae wave, expectation | NON-VERBAL |
| | She seems to be waiting for something | Needs flowers to trade |

**Walkthrough quote** (line 218):
> The queen's antennae wave. She doesn't speak, but there's... expectation? She seems to be waiting for something.

**Item interactions**:
| Command | Expected Response |
|---------|------------------|
| `give [flower] to queen` | Trade for royal honey |

**game_state.json status**:
- ✅ Actor exists with state_machine, trust_state, trades_for, gift_reactions
- ❌ NO `dialog_topics` or talk handler - needs custom non-verbal handler

---

### Dire Bear
**Location**: Predator's Den
**Walkthrough references**: beast_wilds_walkthrough.md lines 236-310

**Interactions**: Commitment-based ("I'll help your cubs"), item giving (healing_herbs to cubs)
- No standard dialog - bear understands intent

**game_state.json status**: ❌ Actor NOT in game_state.json - needs to be added

---

### Spider Matriarch (`spider_matriarch`)
**Location**: Spider Matriarch's Lair
**Walkthrough references**: beast_wilds_walkthrough.md

**Interactions**: Combat primarily
- No standard dialog

**game_state.json status**:
- ✅ Actor exists with state_machine, pack_role, death_reactions
- ✅ No dialog_topics needed

---

## Frozen Reaches

### Fire Salamander (`salamander`)
**Location**: Hot Springs
**Walkthrough references**: frozen_reaches_walkthrough.md lines 149-225, 853-1173

**Dialog interactions**:
| Command | Expected Response | Notes |
|---------|------------------|-------|
| `talk to salamander` | Gestures toward torch, then itself | NON-VERBAL |
| `ask salamander about temple` | Gesture: two fists, warding sign | NON-VERBAL |
| `ask salamander about caves` | Shivering gesture, mimes finding | NON-VERBAL |
| `ask salamander for fire` | Can make fire, won't leave warm zone | NON-VERBAL |
| `ask salamander to come with me` | Shakes head, needs warmth | NON-VERBAL |

**Walkthrough quote** (line 191):
> The salamander tilts its head. It doesn't speak, but its eyes track your movements, your torch, your hands. It makes a gesture toward your unlit torch, then toward itself.

**Item interactions**:
| Command | Expected Response |
|---------|------------------|
| `give torch to salamander` | Salamander inhales fire, trust +1 |
| `give fire crystal to salamander` | Major trust boost, companion-ready |

**game_state.json status**:
- ✅ Actor exists with state_machine, trust_state, fire_creature, gift_reactions handler
- ❌ NO talk/dialog handler - needs custom gesture-based communication handler

---

### Stone Guardians
**Location**: Temple Sanctum (not in current game_state.json locations)
**Walkthrough references**: frozen_reaches_walkthrough.md lines 498-724

**Interactions**: Combat OR password OR control crystal
| Command | Expected Response |
|---------|------------------|
| `say "fire-that-gives-life and water-that-cleanses, united in purpose"` | Guardians become passive |
| `use control crystal` | Full control of guardians |

**game_state.json status**: ❌ Actor NOT in game_state.json - Temple Sanctum location also missing

---

## Civilized Remnants

### Gate Guard (`gate_guard`)
**Location**: Town Gate
**Walkthrough references**: civilized_remnants_walkthrough.md lines 40-65

**Dialog interactions**:
| Command | Expected Response |
|---------|------------------|
| `talk to guard` | "State your business and submit to inspection" |
| `submit to inspection` | Checked for infection, allowed in |

**game_state.json status**:
- ✅ Actor exists with state_machine
- ❌ NO `dialog_topics` configured

---

### Herbalist Maren (`herbalist_maren`)
**Location**: Market Square
**Walkthrough references**: civilized_remnants_walkthrough.md lines 86-135

**Dialog interactions**:
| Command | Expected Response |
|---------|------------------|
| `talk to herbalist` | "A customer? Or just looking?" |
| `ask about herbalism` | Teaching available for 50 gold, requires trust 2 |
| `ask how to earn trust` | "Be a good customer. Don't cause trouble." |
| `buy healing potion` | 15 gold, trust +0.5 |

**Services**: Basic herbalism teaching

**game_state.json status**:
- ✅ Actor exists with trust, services
- ❌ NO `dialog_topics` configured - player cannot learn about services

---

### Healer Elara (`healer_elara`)
**Location**: Healer's Sanctuary
**Walkthrough references**: civilized_remnants_walkthrough.md lines 140-185, beast_wilds_walkthrough lines 386-416

**Dialog interactions**:
| Command | Expected Response |
|---------|------------------|
| `talk to elara` | "Are you injured, or seeking something else?" |
| `ask about garden` | Can't enter without herbalism skill |
| `ask about herbalism training` | Requires trust 3 |
| `ask elara about sira` | (connection) "If she's hurt..." - implicit commitment |

**Services**: Heal wounds, cure poison/disease, advanced herbalism teaching

**Cross-region connection**: Elara knows Sira from childhood

**game_state.json status**:
- ✅ Actor exists with trust, services, connected_to hunter_sira
- ❌ NO `dialog_topics` - **BLOCKER**: player cannot access services or trigger Sira connection

---

### Weaponsmith Toran (`weaponsmith_toran`)
**Location**: Market Square
**Walkthrough references**: civilized_remnants_walkthrough.md (mentioned)

**Services**: sell_weapons, sell_armor, repair_weapons

**game_state.json status**:
- ✅ Actor exists with services
- ❌ NO `dialog_topics` - player cannot learn about services

---

### Curiosity Dealer Vex (`curiosity_dealer_vex`)
**Location**: Market Square
**Walkthrough references**: civilized_remnants_walkthrough.md lines 575-653

**Dialog interactions**:
| Command | Expected Response |
|---------|------------------|
| `talk to vex` | "Looking for something... unusual?" |
| `sell ice crystals` | 40 gold, trust +1 |
| `sell spider silk` | 50 gold, trust +1 |

At trust 2+:
| Command | Expected Response |
|---------|------------------|
| `what do you mean privately?` | Hints at undercity |
| `yes` (to undercity) | Trapdoor location revealed |

**game_state.json status**:
- ✅ Actor exists with trust, services (trade_rare_items, reveal_undercity)
- ❌ NO `dialog_topics` - **BLOCKER**: player cannot discover undercity

---

### The Council (`councilor_hurst`, `councilor_asha`, `councilor_varn`)
**Location**: Council Hall
**Walkthrough references**: civilized_remnants_walkthrough.md lines 196-270, 737-928

**Dialog interactions**:
| Command | Expected Response |
|---------|------------------|
| `talk to council` | "Looking for something, or just observing?" |
| `ask about council` | Explanation of governance |
| `ask about problems` | Three dilemmas presented |
| `ask about infected refugees` | Dilemma details |
| `ask about dangerous traders` | Dilemma details |
| `ask about criminal punishment` | Dilemma details |

**game_state.json status**:
- ✅ All three actors exist with philosophy, trust
- Asha has `can_perform_unbranding`, Varn has `has_undercity_connections`
- ❌ NO `dialog_topics` - **BLOCKER**: player cannot learn about dilemmas or governance

---

### Damaged Guardian (`damaged_guardian`)
**Location**: Broken Statue Hall
**Walkthrough references**: civilized_remnants_walkthrough.md lines 318-354, 932-1034

**Dialog interactions**:
| Command | Expected Response |
|---------|------------------|
| `talk to guardian` | No response (dormant) |
| `designate purpose: protect the town` | (after repair) Guardian accepts orders |

**Repair requirements**: stone_chisel, animator_crystal, ritual_knowledge

**game_state.json status**:
- ✅ Actor exists with state_machine, is_construct, repair_requirements
- No dialog_topics needed (construct, not conversational)

---

### Undercity NPCs (`the_fence`, `whisper`, `shadow`)
**Location**: Undercity
**Walkthrough references**: civilized_remnants_walkthrough.md lines 667-735

**Dialog interactions**:
| Command | Expected Response |
|---------|------------------|
| `talk to fence` | "Buying or selling?" |
| `talk to whisper` | Information for sale |
| `buy information about council` | 40 gold, reveals secrets |
| `talk to shadow` | Assassination services |

**game_state.json status**:
- ✅ All three actors exist with services
- Shadow has discovery_chance and delay_turns for assassination mechanic
- ❌ NO `dialog_topics` - **BLOCKER**: player cannot access undercity services

---

## Meridian Nexus

### The Echo (`the_echo`)
**Location**: Keeper's Quarters
**Walkthrough references**: meridian_nexus_walkthrough.md lines 136-221, 407-666

**Dialog interactions**:
| Command | Expected Response |
|---------|------------------|
| `talk to echo` | "I am... was... the Keeper's child..." |
| `ask about disaster` | Explains meridian shattering |
| `ask about restoration` | Guidance on healing regions |
| `ask about waystone` | Lists five required fragments |
| `ask about crystals` | Explains crystal garden |
| `ask about my promises` | Lists all commitments (kept, pending, broken) |

**Trust-gated content**:
- Trust 6+: Full backstory revealed
- Trust ≤-6: Echo refuses to appear

**game_state.json status**:
- ✅ Actor exists with state_machine, trust_state, is_spectral
- ✅ Has `dialog_topics` with custom handler path
- ✅ Has `gossip_reactions` with custom handler
- Custom handler: `examples.big_game.behaviors.regions.meridian_nexus.echo:on_echo_dialog`

### The Waystone (`waystone_spirit`)
**Location**: Nexus Chamber
**Source**: meridian_nexus_detailed_design.md

**Interactions**: Commitment target, receives waystone fragments
- Minimal NPC for commitment system

**game_state.json status**:
- ✅ Actor exists with state_machine, is_object, commitment_target, fragments_placed
- No dialog needed (object, not character)

---

## Companion NPCs (Can Follow Player)

| NPC | Acquired In | Requirements | Movement Restrictions |
|-----|-------------|--------------|----------------------|
| Wolf Pack | Beast Wilds | Trust 3 | Won't enter: Nexus, Spider Gallery, Deep Roots, Observatory |
| Steam Salamander | Frozen Reaches | Trust 3 + fire crystal gift | Won't enter: Sunken District (water) |
| Hunter Sira | Beast Wilds | Heal her injuries | Conflict with wolves (until reconciliation) |
| Scholar Aldric | Fungal Depths | Heal him | Too weak for combat/extreme environments |

---

## Implementation Status Summary

### ✅ NPCs with dialog_topics configured (WORKING):
| NPC | Actor ID | Notes |
|-----|----------|-------|
| Scholar Aldric | `npc_aldric` | Full dialog_topics with conditional unlocks, handlers, llm_context |
| The Echo | `the_echo` | Has custom handler for complex dialog |
| Hunter Sira | `hunter_sira` | **PHASE 1** - 4 dialog_topics (injury, tracking, beasts, elara) + llm_context |
| Healer Elara | `healer_elara` | **PHASE 1** - 4 dialog_topics (healing, garden, herbalism, sira) + llm_context |
| Myconid Elder | `npc_myconid_elder` | **PHASE 1** - 5 dialog_topics (greeting, cure, resistance, spore_mother, cold) + llm_context |
| Curiosity Dealer Vex | `curiosity_dealer_vex` | **PHASE 1** - 4 dialog_topics (wares, crystals, private, undercity) + llm_context |

### ✅ NPCs with llm_context (for rich narration):
| NPC | Actor ID | Notes |
|-----|----------|-------|
| Alpha Wolf | `alpha_wolf` | **PHASE 1** - 6 traits, 5 states (hostile→allied) with 6 fragments each |
| Frost Wolves | `frost_wolf_1`, `frost_wolf_2` | **PHASE 1** - 4 traits, 5 states with 3 fragments each |
| Spore Mother | `npc_spore_mother` | Has llm_context with state_fragments |

### ❌ NPCs MISSING dialog_topics (BLOCKERS):

**High Priority (blocks core gameplay):**
| NPC | Actor ID | Impact |
|-----|----------|--------|
| Council (all 3) | `councilor_*` | Cannot learn about dilemmas |

**Medium Priority (blocks side content):**
| NPC | Actor ID | Impact |
|-----|----------|--------|
| Herbalist Maren | `herbalist_maren` | Cannot learn about herbalism teaching |
| Weaponsmith Toran | `weaponsmith_toran` | Cannot access weapon services |
| Gate Guard | `gate_guard` | Cannot complete inspection dialog |
| Undercity NPCs (3) | `the_fence`, `whisper`, `shadow` | Cannot access undercity services |
| Camp Leader Mira | `camp_leader_mira` | Cannot learn about sunken district |
| Old Swimmer Jek | `old_swimmer_jek` | Cannot access swimming lessons |
| The Archivist | `the_archivist` | Cannot access archive quest |

### ⚠️ NPCs needing CUSTOM HANDLERS (non-verbal communication):
| NPC | Actor ID | Communication Type |
|-----|----------|-------------------|
| Spore Mother | `npc_spore_mother` | Spore-based emotion sensing |
| Bee Queen | `bee_queen` | Antenna gestures, expectation |
| Fire Salamander | `salamander` | Gesture-based, non-verbal |

### ✅ NPCs that DON'T need dialog_topics:
| NPC | Actor ID | Reason |
|-----|----------|--------|
| Alpha Wolf | `alpha_wolf` | Behavior/gift-based (wolves don't speak) |
| Spider Matriarch | `spider_matriarch` | Combat only |
| Damaged Guardian | `damaged_guardian` | Construct, command-based |
| Waystone Spirit | `waystone_spirit` | Object, receives fragments |
| Sporelings | `npc_sporeling_*` | Combat only, pack followers |
| Frost Wolves | `frost_wolf_*` | Pack followers |
| Sailor Garrett | `sailor_garrett` | Rescue scenario, immediate action |
| Merchant Delvan | `merchant_delvan` | Rescue scenario, immediate action |
| Predatory Fish | `predatory_fish` | Environmental hazard |

### ❌ NPCs/Locations MISSING from game_state.json:
| Entity | Type | Walkthrough Reference |
|--------|------|----------------------|
| Dire Bear | Actor | beast_wilds_walkthrough.md |
| Stone Guardians | Actor | frozen_reaches_walkthrough.md |
| Temple Sanctum | Location | frozen_reaches_walkthrough.md |
| Bear Cubs | Actors | beast_wilds_walkthrough.md |
| Predator's Den | Location | beast_wilds_walkthrough.md |

---

## Priority Action Items

### Critical (Game Not Playable Without These):
1. Add `dialog_topics` to Hunter Sira - enables Sira rescue storyline
2. Add `dialog_topics` to Healer Elara - enables healing and Sira connection
3. Add `dialog_topics` to Curiosity Dealer Vex - enables undercity access
4. Add custom spore handler to Spore Mother - enables fungal healing path

### High Priority:
5. Add `dialog_topics` to Myconid Elder - enables cure/resistance services
6. Add `dialog_topics` to Council members - enables political dilemmas
7. Add custom gesture handler to Salamander - enables companion acquisition
8. Add `dialog_topics` to Camp Leader Mira - enables sunken district guidance

### Medium Priority:
9. Add `dialog_topics` to merchant NPCs (Maren, Toran)
10. Add `dialog_topics` to undercity NPCs
11. Add custom handler to Bee Queen
12. Add missing actors (Dire Bear, Stone Guardians)
13. Add missing locations (Temple Sanctum, Predator's Den)

---

## Design Coverage Analysis

This section maps which gaps can be addressed using existing detailed designs vs requiring new design work.

### Existing Design Documents

| Document | Coverage |
|----------|----------|
| `unified_dialog_system.md` | System architecture for dialog_topics |
| `dialog_system_design.md` | Per-topic handlers, trust_delta, requires_state |
| `beast_wilds_detailed_design.md` | Sira, Bee Queen, Dire Bear, wolves |
| `civilized_remnants_detailed_design.md` | Elara, Maren, Toran, Vex, Council, undercity |
| `fungal_depths_detailed_design.md` | Spore Mother, Myconid Elder, Aldric |
| `frozen_reaches_detailed_design.md` | Salamanders, Stone Golems |
| `sunken_district_detailed_design.md` | Mira, Jek, Archivist, Garrett, Delvan |
| `meridian_nexus_detailed_design.md` | Echo (already implemented) |

---

### Gap-by-Gap Coverage

#### ✅ FULLY COVERED by existing designs (can implement directly):

| NPC | Gap | Design Source | Section |
|-----|-----|---------------|---------|
| Hunter Sira | Missing dialog_topics | `beast_wilds_detailed_design.md` | Section 1.2 (Dialog Topics table), Section 3.3 |
| Healer Elara | Missing dialog_topics | `civilized_remnants_detailed_design.md` | Section 1.2 (full NPC spec) |
| Myconid Elder | Missing dialog_topics | `fungal_depths_detailed_design.md` | Section 1.2 (dialog_topics: greeting, cure, cold, resistance, equipment, spore_mother, heartmoss) |
| Herbalist Maren | Missing dialog_topics | `civilized_remnants_detailed_design.md` | Section 1.2, Section 3.1 (Services) |
| Weaponsmith Toran | Missing dialog_topics | `civilized_remnants_detailed_design.md` | Section 1.2 |
| Curiosity Dealer Vex | Missing dialog_topics | `civilized_remnants_detailed_design.md` | Section 1.2 (undercity gatekeeper) |
| Gate Guard | Missing dialog_topics | `civilized_remnants_detailed_design.md` | Section 1.2 (checkpoint, companion filter) |
| Council members | Missing dialog_topics | `civilized_remnants_detailed_design.md` | Section 1.2, Appendix B (dilemma data) |
| Undercity NPCs | Missing dialog_topics | `civilized_remnants_detailed_design.md` | Section 1.2 (the_fence, whisper, shadow) |
| Camp Leader Mira | Missing dialog_topics | `sunken_district_detailed_design.md` | Section 1.2 (dialog_topics: camp, help, garrett, delvan) |
| Old Swimmer Jek | Missing dialog_topics | `sunken_district_detailed_design.md` | Section 1.2 (dialog_topics: swimming, price, favor) |
| The Archivist | Missing dialog_topics | `sunken_district_detailed_design.md` | Section 1.2 (dialog_topics: identity, disaster, water_pearl, knowledge_quest) |
| Dire Bear + Cubs | Actor missing from game_state | `beast_wilds_detailed_design.md` | Section 1.2 (full spec), Section 1.1 (Predator's Den) |
| Stone Guardians | Actor missing from game_state | `frozen_reaches_detailed_design.md` | Section 1.2, Appendix B |
| Temple Sanctum | Location missing | `frozen_reaches_detailed_design.md` | Section 1.1 |
| Predator's Den | Location missing | `beast_wilds_detailed_design.md` | Section 1.1 |

#### ⚠️ PARTIALLY COVERED (design exists, requires handler implementation):

| NPC | Gap | Design Source | Work Required |
|-----|-----|---------------|---------------|
| Spore Mother | Custom talk handler needed | `fungal_depths_detailed_design.md` Section 1.5 | Implement empathic spore communication vocabulary |
| Bee Queen | Custom talk handler needed | `beast_wilds_detailed_design.md` Section 1.5 | Implement antenna/expectation gesture handler |
| Fire Salamander | Custom gesture handler | `frozen_reaches_detailed_design.md` Section 1.5 | Implement gesture/flame communication handler |

**Implementation Notes for Non-Verbal NPCs:**

1. **Spore Mother** (Fungal Depths):
   - Design specifies communication vocabulary in Section 1.5
   - Empathic spores: pain spike, waves of need, gentle probing, warmth flood, pressure surge
   - Handler should respond to `talk to spore mother` with empathic descriptions
   - No topic selection - communication is sensory/emotional

2. **Bee Queen** (Beast Wilds):
   - Design specifies communication in Section 1.5
   - Antennae, wings, positioning signals
   - Handler should show "expectation" and "waiting for something"
   - Trade is item-based, not dialog-based (gift_reactions handler exists)

3. **Fire Salamander** (Frozen Reaches):
   - Design specifies gesture vocabulary in Section 1.5
   - Points at torch → wants fire; shakes head at ice → dislikes cold
   - Two fists apart → warning about golems; shivering + holding close → treasure hint
   - Flame behavior (brightens, dims, flickers) indicates emotional state

---

### Dialog System Implementation Path

The `dialog_system_design.md` document provides the implementation approach:

**Phase 1**: Implement `requires_state` checking in `get_available_topics()`
- Allows topics to be gated by NPC state machine state
- Example: Aldric's teaching topic requires `stabilized` or `recovering` state

**Phase 2**: Implement `trust_delta` in `handle_ask_about()`
- Topics can modify NPC trust on discussion
- Example: Asking Aldric about infection grants +1 trust

**Phase 3**: Implement per-topic handlers
- Individual topics can route to Python handlers
- Example: `help_commitment` topic routes to commitment creation handler

**Phase 4**: Update game_state.json
- Add dialog_topics to each NPC following designs
- Format from `unified_dialog_system.md`:
```json
"dialog_topics": {
  "topic_name": {
    "keywords": ["keyword1", "keyword2"],
    "response": "NPC's response text",
    "requires_flags": {"flag_name": true},
    "sets_flags": {"new_flag": true},
    "trust_delta": 1,
    "unlocks_topics": ["next_topic"]
  }
}
```

---

### Gaps Requiring NEW Design Work

| Gap | Nature | Notes |
|-----|--------|-------|
| None identified | - | All major gaps are covered by existing designs |

**Note**: All NPC interaction gaps identified in this inventory have corresponding detailed designs. The work is implementation, not design.

---

### Recommended Implementation Order

**Phase 1: Dialog System Enhancements** (pre-requisite)
- Implement `requires_state`, `trust_delta`, per-topic handlers per `dialog_system_design.md`
- This enables all subsequent NPC dialog_topics additions

**Phase 2: Critical NPCs** (blockers for core gameplay)
1. Hunter Sira - from `beast_wilds_detailed_design.md`
2. Healer Elara - from `civilized_remnants_detailed_design.md`
3. Myconid Elder - from `fungal_depths_detailed_design.md`

**Phase 3: Non-Verbal Handlers** (special communication)
1. Spore Mother empathic handler
2. Salamander gesture handler
3. Bee Queen expectation handler

**Phase 4: Civilized Remnants NPCs** (extensive)
- Maren, Toran, Vex, Council, Guard, Undercity

**Phase 5: Sunken District NPCs**
- Mira, Jek, Archivist

**Phase 6: Missing Entities**
- Add Dire Bear, Bear Cubs, Stone Guardians actors
- Add Temple Sanctum, Predator's Den locations
