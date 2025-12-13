# State Machine Reference

**Extracted from**: infrastructure_detailed_design.md, game_wide_rules.md
**Date**: 2025-12-11
**Purpose**: Document all state machines with valid transitions for implementation and verification

---

## 1. CommitmentState

**Location**: Section 1.2 (StrEnum), Section 3.5 (Commitment System)

### States
```
ACTIVE      - Commitment is ongoing, deadline not yet passed
FULFILLED   - Player completed the commitment successfully
WITHDRAWN   - Player explicitly withdrew before deadline
ABANDONED   - Deadline passed without fulfillment
```

### Valid Transitions
```
ACTIVE -> FULFILLED   : fulfill_commitment() called, requirements met
ACTIVE -> WITHDRAWN   : withdraw_commitment() called before deadline
ACTIVE -> ABANDONED   : on_commitment_check detects deadline passed
ACTIVE -> ABANDONED   : Target NPC dies before deadline
```

### Invalid Transitions
```
FULFILLED -> any      : Terminal state
WITHDRAWN -> any      : Terminal state
ABANDONED -> any      : Terminal state
any -> ACTIVE         : Commitments cannot be reactivated
```

### Terminal States
```
FULFILLED, WITHDRAWN, ABANDONED
```

### Triggers
| From | To | Trigger |
|------|-----|---------|
| ACTIVE | FULFILLED | `fulfill_commitment(state, commitment_id, accessor)` |
| ACTIVE | WITHDRAWN | `withdraw_commitment(state, commitment_id, accessor)` |
| ACTIVE | ABANDONED | `abandon_commitment(commitment, accessor)` via turn phase |

### Notes
- Once a commitment leaves ACTIVE state, it cannot return
- WITHDRAWN has no trust penalty; ABANDONED has trust penalty and may trigger gossip
- Hope bonus (if any) is applied when commitment becomes ACTIVE, not undone on any outcome

---

## 2. ConditionSeverity

**Location**: Section 2.4 (Condition Operations), Section 3.3 (Condition System)

### States (Numeric Thresholds)
```
0           - No condition (condition removed from actor)
1-29        - MILD (no gameplay effect, warning messages)
30-59       - MODERATE (gameplay effects begin)
60-79       - SEVERE (significant gameplay effects)
80-99       - CRITICAL (imminent danger)
100         - Maximum (death/incapacitation)
```

### Valid Transitions
```
0 -> 1-29         : Condition applied or enters hazardous zone
1-29 -> 30-59     : Severity increases (tick in hazard)
30-59 -> 60-79    : Severity continues increasing
60-79 -> 80-99    : Severity continues increasing
80-99 -> 100      : Severity reaches maximum
100 -> death      : Death check fires

Any -> lower      : Cure/treatment/recovery applied
Any -> 0          : Full cure (condition removed)
```

### Invalid Transitions
```
None              : Severity is numeric, all transitions valid
                    (clamped to [0, 100])
```

### Terminal States
```
0    - Condition removed
100  - Maximum severity (may trigger death)
```

### Per-Condition Thresholds (from game_wide_rules.md)

**Hypothermia**:
| Severity | Effect |
|----------|--------|
| 0-29 | Cold but functional |
| 30 | "You're getting very cold" |
| 60 | "Your fingers are numb" |
| 80 | Movement penalty begins |
| 100 | Death |

**Fungal Infection**:
| Severity | Effect |
|----------|--------|
| 0-19 | Minor symptoms |
| 20 | "Cough develops" |
| 40 | "Fungal growth visible" |
| 60 | "Breathing difficulty" |
| 80 | "Spore-speech possible" |
| 100 | Death or transformation |

**Drowning**:
| Severity | Effect |
|----------|--------|
| 0 | Full breath |
| 50 | "Running out of air" |
| 80 | "Lungs burning" |
| 100 | Death |

### Notes
- Severity changes happen in condition tick handlers
- Rate depends on environment (zone) and protection (equipment, companions)
- Recovery rates are typically -10 per turn in safe zones

---

## 3. TrustTier (Echo)

**Location**: Section 3.4 (Trust System), game_wide_rules.md

### States (Value Ranges)
```
+5 or above   - FULL_COOPERATION: Speaks name, always appears
0 to +4       - NORMAL: Normal guidance
-1 to -2      - DISAPPOINTED: Disappointed tone
-3 to -5      - RELUCTANT: Cold, may refuse
-6 or below   - REFUSES: Will not appear at all
```

### Valid Transitions
```
Any tier -> adjacent tier : Trust value crosses threshold
Any tier -> any tier      : Multiple trust changes in quick succession
```

### Transition Triggers
| Delta | Cause |
|-------|-------|
| -3 | Abandoned commitment |
| -2 | Killed innocent NPC |
| -1 | Minor betrayal |
| +1 | Fulfilled commitment |
| +1 | Helped NPC in need |
| +2 | Major heroic action |

### Echo Appearance Chance by Trust
| Trust | Base Chance | Formula |
|-------|-------------|---------|
| <= -6 | 0% | Refuses to appear |
| -2 | 15% | 20% + (-2 * 10%) = 0%, min 5% |
| -1 | 15% | 20% + (-1 * 10%) = 10%, min 5% |
| 0 | 20% | Base |
| +1 | 30% | 20% + 10% |
| +2 | 40% | 20% + 20% |
| +5 | 70% | 20% + 50% |
| +8 | 95% | Capped at 95% |

### Bounds
```
Floor: -6 (cannot go below)
Ceiling: None (unbounded positive)
Recovery Cap: +1 per Nexus visit (if below 0)
```

### Notes
- Trust floor means player can always eventually recover
- Recovery cap prevents immediate redemption
- At trust +5, Echo speaks player's name (major narrative moment)

---

## 4. TrustTier (NPC)

**Location**: Section 3.4, game_wide_rules.md

### States (Value Ranges - vary by NPC)
```
Typical NPC ranges: -10 to +10
Some NPCs have custom bounds defined in properties
```

### Common Trust Thresholds
| Trust | Effect |
|-------|--------|
| -5 | Refuses to trade/help |
| 0 | Neutral, basic interaction |
| +3 | Willing to share secrets |
| +5 | Offers special services |

### Transition Triggers (Examples)
| NPC | Action | Delta |
|-----|--------|-------|
| Myconid Elder | Heal fungal creature | +2 |
| Myconid Elder | Kill fungal creature | -3 |
| Wolf Pack | Share food | +1 |
| Wolf Pack | Attack them | -5 |
| Garrett | Save him | +3 |
| Garrett | Let him drown | -3 (if relationship existed) |

### Notes
- NPC trust bounds stored in `actor.properties["trust"]["floor"]` and `["ceiling"]`
- Some NPCs have no recovery (permanent distrust if betrayed)

---

## 5. SpreadState

**Location**: Section 1.6 (Types), Section 3.10 (Environmental Spread System)

### States
```
INACTIVE (active: false)  - Spread has been halted
ACTIVE (active: true)     - Spread is progressing
```

### Valid Transitions
```
ACTIVE -> INACTIVE    : halt_spread() called, OR halt_flag becomes True
```

### Invalid Transitions
```
INACTIVE -> ACTIVE    : Once halted, a spread cannot restart
```

### Terminal States
```
INACTIVE - Spread is permanently halted
```

### Spread Definitions (from game data)

**spore_spread**:
| Turn | Effect |
|------|--------|
| 50 | Beast Wilds gets spore_level: "low" |
| 100 | Civilized Remnants town gate gets infection_check |
| 150 | All Civilized Remnants gets infection_present |
| Halted by: `spore_mother_healed` flag |

**cold_spread**:
| Turn | Effect |
|------|--------|
| 75 | Beast Wilds forest edge becomes "cold" |
| 125 | Nexus chamber becomes "cold" |
| 175 | Sunken District water freezes |
| Halted by: `observatory_functional` flag |

### Notes
- Spreads are checked in `turn_phase_spread`
- When halt flag is set, spread immediately becomes INACTIVE
- Milestone effects are permanent (halting spread doesn't reverse past milestones)

---

## 6. GossipState

**Location**: Section 3.8 (Information Networks)

### States
```
PENDING     - Gossip in queue, not yet arrived
DELIVERED   - Gossip arrived at targets
CONFESSED   - Player confessed before gossip arrived (removed from queue)
```

### Valid Transitions
```
PENDING -> DELIVERED  : arrives_turn <= current_turn, on_gossip_propagate fires
PENDING -> CONFESSED  : confess_action() called within confession window
```

### Invalid Transitions
```
DELIVERED -> any      : Delivered gossip cannot be undone
CONFESSED -> any      : Confessed gossip is removed from queue
```

### Terminal States
```
DELIVERED - NPCs now have knowledge flags
CONFESSED - Gossip removed (reduced trust impact)
```

### Confession Window
```
Valid when: current_turn <= confession_window_until
Effect: Gossip removed from queue, reduced trust penalty vs being found out
```

### Notes
- Gossip entries are removed from queue when delivered or confessed
- DELIVERED gossip sets `knows_{gossip_id}` flag on target NPCs
- Network gossip (spore_network) has 1-turn delay; normal gossip 3-5 turns

---

## 7. CompanionComfort

**Location**: Section 1.2 (StrEnum), Section 3.7 (Companion System)

### States
```
COMFORTABLE    - Companion is happy in this location
UNCOMFORTABLE  - Companion follows but is stressed
IMPOSSIBLE     - Companion cannot enter this location
```

### Transitions
```
COMFORTABLE -> UNCOMFORTABLE : Player moves to uncomfortable location
COMFORTABLE -> IMPOSSIBLE    : Player moves to blocked location (companion waits)
UNCOMFORTABLE -> COMFORTABLE : Player moves to comfortable location
UNCOMFORTABLE -> IMPOSSIBLE  : Player moves to blocked location
IMPOSSIBLE -> COMFORTABLE    : Player returns to companion's waiting location
IMPOSSIBLE -> UNCOMFORTABLE  : Player returns to uncomfortable location near companion
```

### Per-Companion Restrictions (from game_wide_rules.md)

**Wolf Pack**:
| Location | Comfort |
|----------|---------|
| Beast Wilds | COMFORTABLE |
| Civilized Remnants | IMPOSSIBLE (guards attack) |
| Meridian Nexus | IMPOSSIBLE (wards) |
| Sunken District | UNCOMFORTABLE (refuses to swim) |
| Frozen Reaches (bitter cold) | UNCOMFORTABLE (combat debuff) |
| Spider Nest Gallery | IMPOSSIBLE (too dangerous) |

**Salamander**:
| Location | Comfort |
|----------|---------|
| Frozen Reaches | COMFORTABLE (home) |
| Sunken District | IMPOSSIBLE (death) |
| Other regions | COMFORTABLE |

**Myconid**:
| Location | Comfort |
|----------|---------|
| Fungal Depths | COMFORTABLE (home) |
| Frozen Reaches | IMPOSSIBLE (cold damage) |
| Other regions | COMFORTABLE |

### Notes
- IMPOSSIBLE causes companion to wait at last valid location
- companion.following = False when IMPOSSIBLE
- companion.waiting_at set to player's previous location

---

## 8. NPC State Machines (Game-Specific)

Individual NPCs have custom state machines defined in their properties.
These are game-specific, not infrastructure, but follow the infrastructure pattern.

### Example: Garrett (Sunken District)
```
States: drowning, stabilized, rescued, dead
Initial: drowning

Transitions:
  drowning -> stabilized   : Player applies first aid
  drowning -> rescued      : Player brings to safety
  drowning -> dead         : Condition reaches 100
  stabilized -> rescued    : Player brings to safety
  stabilized -> drowning   : Too much time passes
  stabilized -> dead       : Condition reaches 100
```

### Example: Sira (Beast Wilds)
```
States: trapped, rescued, dead
Initial: trapped

Transitions:
  trapped -> rescued : Player frees her within deadline
  trapped -> dead    : Deadline passes (8 turns)
```

### Notes
- NPC state machines use `transition_state(config, new_state)`
- Current state accessed via `get_current_state(config)`
- State machine stored in `actor.properties["state_machine"]`

---

## Extraction Notes

### Issues Found During Extraction

1. **Condition severity thresholds partially specified**: The exact thresholds (30/60/80/100) are mentioned in examples but not formally standardized. Different conditions may use different thresholds.

2. **Trust recovery cap timing**: The "per Nexus visit" cap is mentioned but the mechanism for detecting a "new visit" is not fully specified. Infrastructure uses "10 turns since last recovery" as proxy.

3. **NPC state machine transitions not validated**: The `transition_state` function checks that the new state is valid (in states list) but doesn't validate that the transition itself is valid. This is intentional - transition validity is game logic, not infrastructure.

4. **GossipState is implicit**: Unlike CommitmentState which has explicit enum values, gossip state is determined by queue membership and flag existence. Consider adding explicit state field for clarity.

### Potential Invariants Discovered

- CommitmentState: Once not ACTIVE, stays not ACTIVE
- SpreadState: Once INACTIVE, stays INACTIVE
- Condition severity: Always in [0, 100]
- Trust: Always >= floor (if defined)
- Companions: At most 2 active at once
- Gossip: arrives_turn > created_turn (always positive delay)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-11 | Initial extraction |
