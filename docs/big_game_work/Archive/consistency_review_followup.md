# Consistency Review Followup - Design Questions

**Date**: 2025-12-11
**Status**: Phase 1 complete. Phase 1.5 complete. Ready for Phase 2.

---

## Completed Fixes

The following critical issues from phase1_inconsistency_report.md have been fixed:

| Issue | Fix Applied |
|-------|-------------|
| I-1: Spore Heart export missing | Added to Fungal Depths Section 2.2 |
| I-3: Cleaning Supplies not in Frozen Reaches 1.3 | Added to Frozen Reaches Section 1.3 |
| G-1: Aldric gossip mechanism missing | Added to Fungal Depths Section 2.3 with explanation |
| G-2: Spore Mother killed not in dependencies | Added to cross_region_dependencies.md gossip table |
| G-3/G-4: Broadcast gossip reception | Added infrastructure note to cross_region_dependencies.md |
| DQ-1: Spore Mother healing scope | Added clarification - healing alone stops spread |
| C-2: Myconid restriction in Frozen Reaches | Added to Frozen Reaches Section 4.3 |

*(I-2 was false positive - already documented. C-1 was already documented at Beast Wilds line 814.)*

---

## DQ-2: Echo Trust Floor

### Current Documentation Conflict

- **meridian_nexus_detailed_design.md:109**: "Refuses at trust ≤ -3"
- **game_wide_rules.md:271-275**: "At trust -6, Echo refuses to manifest at all... Recovery from -6 to -2 is possible"

The ending system table references trust levels from 5+ down to -6, implying a scale that goes that low. But the detailed design says Echo refuses at -3.

### Options

1. **Floor at -3**: Echo stops appearing at -3, scale is -3 to +5 (simpler, more forgiving)

2. **Floor at -6**: Echo stops appearing at -6, but becomes increasingly hostile from -3 onward (harsher, matches ending system)

3. **Tiered floor**: Echo becomes "reluctant" at -3 (reduced appearance chance, e.g. 5%), "refusing" at -6 (no appearance at all)

### Recommendation

Option 3 (Tiered) aligns both documents:
- Trust -3 to -5: Echo reluctant, 5% appearance chance, dialog is cold/disappointed
- Trust -6 or below: Echo refuses entirely, player loses guidance

This preserves the -6 floor from game_wide_rules while explaining why the detailed design mentions -3 as a significant threshold.

---

## DQ-3: Delvan Undercity Access Mechanism

### Current State

- **sunken_district_detailed_design.md:171**: "If rescued... black market connection"
- **civilized_remnants_detailed_design.md:163**: Lists four discovery methods including "Delvan's black market connection"

Player rescues Delvan from drowning in Sunken District. Delvan is a merchant with criminal connections. The question is how the player learns the undercity entrance pattern.

### Options

1. **Auto-flag**: Rescuing Delvan immediately sets `knows_undercity_entrance` - simplest but least interesting

2. **Must ask**: Player must return to rescued Delvan and explicitly ask about black market - more interactive (user leans toward this)

3. **Automatic tell**: Delvan offers information as thank-you during rescue sequence - narratively richer

### For Option 2 (Must Ask)

The player needs a hint to try this. Possibilities:
- Delvan mentions "I have connections in the undercity" during rescue dialog
- Mira mentions "Delvan dealt with smugglers" when asked about survivors
- Setting `delvan_has_undercity_knowledge` flag on rescue, which unlocks the dialog option "Ask about black market"

### Recommendation

Option 2 with hint: During rescue, Delvan says something like "I owe you my life. If you ever need... special services... find me at the camp." This establishes he has something to offer without giving it away for free. Player must return and ask.

---

## DQ-4: Gossip Infrastructure for Broadcasts

### Current Infrastructure

From infrastructure_detailed_design.md:1327-1380:

```python
def create_gossip(state, content, source_npc, target_npcs, delay_turns, confession_window)
def deliver_gossip(entry, accessor)  # Fire-and-forget, sets flags on NPCs
def confess_action(state, gossip_id, to_npc)  # Player confession
def get_pending_gossip_about(state, content_substring)  # Search queue
```

Gossip is stored in `state.extra["gossip_queue"]` and delivered automatically by turn processing. The `deliver_gossip` function sets flags in `npc.properties["flags"]`.

### Question

Can infrastructure handle broadcast gossip gracefully? Since this is the same or similar for all regions, it should be abstracted into infrastructure.

### Three Propagation Mechanisms

Cross-region information and effects use three distinct mechanisms:

| Mechanism | Speed | Nature | Implementation |
|-----------|-------|--------|----------------|
| **World State Changes** | Instant | Binary flip, universally perceived | Global flags checked by NPCs/systems |
| **Environmental Spread** | Gradual (turns) | Slow degradation/recovery | Turn-based progression |
| **Gossip** | Variable (turns) | Information traveling between NPCs | Gossip queue with delivery timing |

### World State Changes (Instant, Universally Perceived)

These are fundamental changes to the world that NPCs perceive directly - like the lifting of Sauron's darkness. No gossip needed.

| Event | Trigger | Global Flag | Effects |
|-------|---------|-------------|---------|
| **Waystone repaired** | All 5 fragments placed | `waystone_complete` | Fast travel unlocked, Echo transforms, environmental spreads halt |
| **Telescope repaired** | Observatory functional | `observatory_functional` | Cold spread prevention, crystal garden +1, strategic information available |

NPCs react by checking these flags, not by receiving gossip. They *sense* the change.

### Environmental Spread (Gradual)

Already documented in cross_region_dependencies.md. Gradual degradation or recovery over turns.

| Spread | Source | Timing | Halted By |
|--------|--------|--------|-----------|
| Spore spread | Fungal Depths | Turn 50+ | Healing Spore Mother |
| Cold spread | Frozen Reaches | Turn 75+ | Repairing telescope |

### Gossip (Information Between NPCs)

Gossip is for information that travels between specific NPCs or broadcasts to regions over time.

**Broadcast gossip** (travels to all NPCs in target regions):

| Event | Source Region | Targets | Timing | Trigger Condition |
|-------|---------------|---------|--------|-------------------|
| **Spore Mother healed** | Fungal Depths | All regions | 15 turns | Player heals Spore Mother |
| **Spore Mother killed** | Fungal Depths | All fungal creatures + Echo | 1 turn | Spore Mother dies |
| **Rescue reputation** | Any region | All regions | 20-30 turns | Player rescues NPC (major action) |
| **Violence reputation** | Any region | All regions | 20-30 turns | Player kills friendly NPC (major action) |

**Point-to-point gossip** (travels to specific named NPCs):
- Sira's fate → Elara specifically (personal connection)
- Delvan's fate → Undercity specifically (criminal network)
- Aldric's fate → Civilized Remnants scholars (professional connection)
- Bear cubs' fate → Sira specifically (she notices nearby)

### Gossip Type Distinction

| Type | Targets | Example |
|------|---------|---------|
| **Broadcast** | All NPCs in target regions | Spore Mother healed → everyone learns eventually |
| **Network** | All members of a specific network | Fungal creature killed → all fungal creatures know via spore network |
| **Point-to-Point** | Specific named NPCs | Sira abandoned → Elara learns through travelers |

### Analysis

**Current capability**: Assumes `target_npcs` is a list of specific ActorIds. Works for point-to-point gossip (Sira→Elara) but not broadcasts (Spore Mother healed→All regions).

**Required extension**: Add broadcast capability where target is expanded at delivery time based on current game state.

### Recommended API Addition

```python
def create_broadcast_gossip(
    state: GameState,
    content: str,
    source_npc: ActorId,
    target_regions: list[str] | Literal["ALL"],  # "beast_wilds", "civilized_remnants", etc.
    delay_turns: int,
    npc_filter: Callable[[Actor], bool] | None = None  # Optional filter for specific NPC types
) -> GossipId:
    """Create gossip that broadcasts to all NPCs in specified regions.

    At delivery time, expands target_regions to all active NPCs in those regions.
    Optional npc_filter can restrict to specific NPC types (e.g., only humans, only service providers).
    """

def create_network_gossip(
    state: GameState,
    content: str,
    source_npc: ActorId,
    network_id: str,  # "spore_network", "criminal_network", etc.
    delay_turns: int
) -> GossipId:
    """Create gossip that broadcasts to all members of a network.

    Networks are defined by actor properties (e.g., 'fungal: true' for spore network).
    """
```

### Benefits

1. Region designs only document gossip they ORIGINATE
2. Infrastructure handles delivery to all relevant NPCs
3. No need to document "receiving" in every region
4. Consistent timing and delivery semantics
5. Network gossip handles spore network elegantly

### Implementation Notes

- Broadcast gossip stored with `target_regions` instead of `target_npcs`
- Network gossip stored with `network_id` instead of `target_npcs`
- At delivery time, iterate actors matching criteria
- Apply optional filter (e.g., exclude animals, only humans who trade information)
- Set flags on matching NPCs
- Networks defined in game state as property filters (e.g., `{"spore_network": {"fungal": true}}`)

---

## DQ-5: Companion Override Mechanism

### Current State

- **cross_region_dependencies.md:155-160**: Mentions three override scenarios:
  1. Wolf exceptional bravery (follows into spider territory)
  2. Salamander foolhardy sacrifice (enters water to save player)
  3. Myconid curious explorer (ventures into Beast Wilds)

- **beast_wilds_detailed_design.md:810**: "Override: Exceptional bravery if player losing fight in gallery (one-time, costs wolves)"

### Context

Companions normally have hard restrictions (wolves can't enter Nexus). Override flags allow rare dramatic moments where a companion violates their restriction with narrative consequences.

### Current Wolf Implementation (Beast Wilds)

- **Trigger**: Player health below threshold during combat in spider gallery
- **Cost**: "costs wolves" - implies wolf injury/death
- **Frequency**: "one-time" - only happens once per playthrough

### Options

1. **Automatic trigger** (current wolf design):
   - System monitors player state (health %, combat state)
   - Triggers automatically when threshold met
   - Companion acts on its own volition
   - **Pro**: Dramatic surprise moments
   - **Con**: Player has no agency

2. **Player command**:
   - Player can explicitly ask companion to enter restricted area
   - Companion refuses unless conditions met (high trust, emergency)
   - Player makes conscious choice knowing the cost
   - **Pro**: Player agency
   - **Con**: Less dramatic, requires player to know it's possible

3. **Trust threshold unlock**:
   - At trust 5+, companion volunteers to follow into dangerous area
   - Player can accept or decline
   - **Pro**: Rewards relationship building
   - **Con**: May trivialize restrictions

4. **Hybrid** (recommended):
   - Automatic trigger for emergency rescues (low health, trapped)
   - Player command unlocked at trust 5+ for voluntary entry
   - Both have costs (injury, trust expenditure)

### Implementation Requirements

```python
def check_override_trigger(
    state: GameState,
    companion_id: ActorId,
    location_id: LocationId,
    player_state: PlayerState
) -> bool:
    """Check if automatic override should trigger."""

def attempt_companion_override(
    state: GameState,
    companion_id: ActorId,
    location_id: LocationId
) -> OverrideResult:
    """Player attempts to command companion into restricted area."""
```

Per-companion configuration:
```python
CompanionOverrideConfig = {
    "automatic_triggers": {
        "player_health_below": 20,  # Percentage
        "player_in_combat": True,
        "player_trapped": True
    },
    "command_requirements": {
        "trust_threshold": 5,
        "emergency_only": False  # If True, only works when automatic would trigger
    },
    "costs": {
        "companion_damage": 50,  # Health lost
        "trust_cost": 1,  # Trust reduction for commanding
        "one_time": True  # Can only happen once per playthrough
    }
}
```

### Recommendation

Option 4 (Hybrid):
- Automatic for dramatic emergency moments (player doesn't control, companion chooses)
- Command available at high trust (player agency, but with cost)
- Both are one-time per playthrough to preserve dramatic weight

---

## Summary of Decisions

| Question | Options | Decision |
|----------|---------|----------|
| DQ-2 | (1) Floor -3, (2) Floor -6, (3) Tiered | **Option 3 (Tiered)** - Echo reluctant at -3, refuses at -6 |
| DQ-3 | (1) Auto-flag, (2) Must ask, (3) Automatic tell | **Modified Option 2** - Delvan gives narrative hint while thanking, trust increases, player asks based on trust |
| DQ-4 | Add broadcast gossip to infrastructure? | **Yes** - abstract into infrastructure with broadcast + network APIs (awaiting final approval) |
| DQ-5 | (1) Automatic, (2) Command, (3) Trust unlock, (4) Hybrid | **Option 4 (Hybrid)** - Automatic emergency + player command at trust 5+ |

---

## Next Steps After Decisions

1. ~~Update game_wide_rules.md with DQ-2 resolution (Echo trust tiers)~~ ✓ Done in Phase 1.5
2. Update Sunken District detailed design with DQ-3 mechanism (Delvan hint + ask)
3. Add broadcast gossip API to infrastructure_detailed_design.md (DQ-4)
4. ~~Add companion override specification to infrastructure or cross_region_dependencies (DQ-5)~~ ✓ Done in Phase 1.5 (added to game_wide_rules.md)
5. ~~Proceed to Phase 1.5: Update game_wide_rules.md with timer standardization~~ ✓ Complete

---

## Phase 1.5 Completion Summary

Phase 1.5 updates to game_wide_rules.md (v1.4) completed:

| Update | Status |
|--------|--------|
| Timer format standardization ("base + hope bonus = max") | ✓ Complete |
| Timer Format Reference table | ✓ Added |
| Trust System Overview (Echo vs NPC scales) | ✓ Added |
| Echo Trust tier table (disappointed/reluctant/refuses) | ✓ Added |
| Companion Restrictions Matrix | ✓ Added |
| Companion Override Mechanism (DQ-5) | ✓ Added |
| Companion Death scenarios | ✓ Added |
| Salamander water region behavior | ✓ Added |
| Wolf cold tolerance zones | ✓ Added |
| Partial credit evidence checking mechanics | ✓ Added |
| Confession window clarification (Sira-Elara specific) | ✓ Added |

---

## Phase 2 Completion Summary

Phase 2 work is complete. All consistency issues have been addressed:

| Work Item | Status |
|-----------|--------|
| Sunken District DQ-3 mechanism (Delvan hint + ask) | ✓ Complete |
| Broadcast/network gossip API in infrastructure (DQ-4) | ✓ Complete |
| game_wide_rules.md cross-cutting fixes (CC-2, CC-3, CC-8) | ✓ Complete |
| Beast Wilds fixes (CC-5 moonpetal, BW issues) | ✓ Complete |
| Civilized Remnants fixes (CC-6 bandages, CR issues) | ✓ Complete |
| Sunken District fixes (CC-7 trigger naming, SD issues) | ✓ Complete |
| Meridian Nexus fixes (CC-4 Echo tiers, MN issues) | ✓ Complete |
| Fungal Depths fixes (FD issues) | ✓ Complete |
| Frozen Reaches fixes (FR issues) | ✓ Complete |

See region_internal_consistency.md for the full list of 53 issues identified and addressed.
