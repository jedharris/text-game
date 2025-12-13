# Narration State Changes Catalog

**Date**: 2025-12-11
**Purpose**: Document all state changes visible to players, for LLM narrator interface design

---

## Overview

This catalog lists every state mutation that should produce player-visible narrative output.
Each entry documents:
- **Trigger**: What causes the state change
- **State Mutations**: What actually changes in game state
- **Output for Narration**: What information the LLM needs to narrate
- **Context Needed**: Additional state the narrator may query

---

## 1. Player Action Results

State changes triggered directly by player commands.

### 1.1 make_commitment
```
Trigger: Player says trigger phrase to commitment-target NPC
State Mutations:
  - New ActiveCommitment added to state.extra["active_commitments"]
  - commitment.state = ACTIVE
  - commitment.made_at_turn = current_turn
  - commitment.deadline_turn = current_turn + base_timer
  - commitment.hope_applied may become True
  - If hope_extends_survival: NPC condition severity reduced
Output for Narration:
  - Which NPC the commitment is to
  - What the player promised to do
  - Urgency/deadline (if any)
  - NPC's reaction (hope, gratitude, skepticism)
Context Needed:
  - NPC personality for reaction tone
  - Player's history with this NPC
  - Whether this is first commitment or pattern
```

### 1.2 fulfill_commitment
```
Trigger: Player completes commitment requirements
State Mutations:
  - commitment.state = FULFILLED
  - Trust bonus applied to NPC
  - Flags set (fulfilled_promise_{id})
  - May trigger positive gossip
Output for Narration:
  - Which commitment was fulfilled
  - NPC's grateful reaction
  - Trust improvement indication
  - Any rewards or consequences
Context Needed:
  - How close to deadline it was
  - NPC's current state
  - Whether NPC survives because of this
```

### 1.3 withdraw_commitment
```
Trigger: Player explicitly withdraws before deadline
State Mutations:
  - commitment.state = WITHDRAWN
  - No trust penalty (clean withdrawal)
Output for Narration:
  - Which commitment was withdrawn
  - NPC's disappointed but understanding reaction
  - Acknowledgment that player was honest about limits
Context Needed:
  - NPC personality
  - How long the commitment was active
```

### 1.4 confess_action
```
Trigger: Player confesses wrongdoing before gossip arrives
State Mutations:
  - Gossip removed from queue
  - Reduced trust penalty applied (vs being found out)
  - confession_flag set
Output for Narration:
  - What the player confessed
  - NPC's reaction (hurt but respects honesty)
  - Indication that trust impact is reduced
Context Needed:
  - Relationship history with NPC
  - What the original action was
  - How much time remained before gossip arrived
```

### 1.5 add_companion
```
Trigger: Player befriends/recruits companion
State Mutations:
  - New CompanionState added to companions list
  - companion.following = True
  - companion.comfort_in_current set
Output for Narration:
  - Who joined the party
  - Companion's demeanor/excitement
  - Any warnings about restrictions
Context Needed:
  - How the befriending happened
  - Companion's personality
  - Current party composition
```

### 1.6 remove_companion
```
Trigger: Player dismisses companion
State Mutations:
  - Companion removed from list
Output for Narration:
  - Who left the party
  - Companion's reaction (sad, understanding)
  - Where companion will go
Context Needed:
  - Relationship history
  - Reason for dismissal
  - Companion's home region
```

### 1.7 Trust Changes (direct player action)
```
Trigger: Player action that affects NPC trust
State Mutations:
  - trust_state["current"] modified
  - May cross tier threshold
Output for Narration:
  - What action caused the change (implicit in action result)
  - NPC's visible reaction
  - Tier change effects (if crossing threshold)
Context Needed:
  - Previous trust level
  - Whether tier threshold crossed
  - NPC personality
```

### 1.8 Condition Applied (player action)
```
Trigger: Player enters hazardous area or makes risky choice
State Mutations:
  - New condition added to actor.properties["conditions"]
  - condition.severity set to initial value
Output for Narration:
  - What condition was acquired
  - Initial severity description
  - Warning about progression
Context Needed:
  - What caused the condition
  - Player's current protection
  - Location hazards
```

### 1.9 Condition Cured (player action)
```
Trigger: Player uses cure item or reaches safe zone
State Mutations:
  - Condition severity reduced or condition removed
Output for Narration:
  - Relief from the condition
  - How much better player feels
  - Whether fully cured or partially
Context Needed:
  - Previous severity
  - What cured it
  - Whether condition can return
```

### 1.10 Puzzle Contribution Added
```
Trigger: Player activates element for cumulative puzzle
State Mutations:
  - puzzle["contributions"][source_id] = amount
  - puzzle["current_value"] recalculated
  - May trigger puzzle["solved"] = True
Output for Narration:
  - What the player activated
  - Effect description (light brightens, weight increases)
  - Progress toward goal
  - Completion celebration if solved
Context Needed:
  - Current vs target value
  - What other contributions exist
  - Puzzle narrative theme
```

### 1.11 Puzzle Solved
```
Trigger: Puzzle requirements met
State Mutations:
  - puzzle["solved"] = True
  - puzzle["solved_via"] = solution_id (for multi-solution)
  - on_solve_flag may be set
Output for Narration:
  - Success description
  - What was unlocked/achieved
  - Reward or narrative consequence
Context Needed:
  - Which solution was used
  - How player figured it out
  - What's now accessible
```

---

## 2. Turn Phase Results

State changes from automatic per-turn processing.

### 2.1 on_scheduled_event_check (events fire)
```
Trigger: Scheduled event's trigger_turn <= current_turn
State Mutations:
  - Event removed from scheduled_events
  - Event-specific effects applied (game-specific)
Output for Narration:
  - Event description
  - Consequences
  - Time-based framing ("After waiting...")
Context Needed:
  - What event was scheduled
  - Why it matters now
  - Player's location relative to event
```

### 2.2 on_commitment_check (deadline passed)
```
Trigger: Commitment deadline_turn <= current_turn
State Mutations:
  - commitment.state = ABANDONED
  - Trust penalty applied to NPC
  - Gossip may be created
  - broke_promise_{id} flag set
Output for Narration:
  - Which commitment was broken
  - NPC's hurt/angry reaction
  - Consequences described
  - Echo's disappointment (if relevant)
Context Needed:
  - NPC personality for reaction
  - Whether NPC is still alive
  - How badly this affects things
```

### 2.3 on_gossip_propagate (gossip arrives)
```
Trigger: Gossip arrives_turn <= current_turn
State Mutations:
  - Gossip removed from queue
  - Target NPCs get knows_{gossip_id} flag
  - Trust may be affected
Output for Narration:
  - NO DIRECT OUTPUT (gossip is background)
  - Affects future NPC dialog
  - May show in NPC behavior changes
Context Needed:
  - NPCs may now reference knowledge in conversation
  - Trust changes reflected in attitude
```

### 2.4 on_spread_check (milestone reached)
```
Trigger: Spread milestone turn == current_turn
State Mutations:
  - Location properties modified per spread effects
  - spread["current_milestone"] updated
Output for Narration:
  - Environmental change description
  - Affected areas named
  - Urgency/warning about progression
Context Needed:
  - Player's location (are they affected?)
  - What the spread represents
  - How to stop it
```

### 2.5 on_spread_check (spread halted)
```
Trigger: Spread halt_flag becomes True
State Mutations:
  - spread["active"] = False
Output for Narration:
  - Victory/relief description
  - What stopped the spread
  - Areas that were saved
Context Needed:
  - How player achieved this
  - What the threat was
  - Long-term consequences
```

### 2.6 on_environment_tick (hazard exposure)
```
Trigger: Actor in hazardous location
State Mutations:
  - Condition severity increased
  - May trigger threshold messages
Output for Narration:
  - Progressive discomfort description
  - Threshold warnings
  - Urgency about finding safety
Context Needed:
  - Current severity
  - Protection level
  - Nearby safe zones
```

### 2.7 on_condition_tick (severity progression)
```
Trigger: Per-turn condition tick
State Mutations:
  - Condition severity changed
  - May cross threshold
  - May trigger death
Output for Narration:
  - Worsening or improving description
  - Threshold milestone messages
  - Death warning if critical
Context Needed:
  - Rate of change
  - Available cures
  - Time until critical
```

---

## 3. Threshold Crossings

State changes when values cross significant thresholds.

### 3.1 Condition Severity Threshold
```
Trigger: Severity crosses 30/60/80/100 boundary
State Mutations:
  - Severity at new level
  - Gameplay effects may activate
Output for Narration:
  - Threshold-specific message
  - New symptoms described
  - Warning about consequences
Context Needed:
  - Which condition
  - Specific threshold effects
  - Treatment options
```

**Hypothermia Thresholds**:
| Threshold | Output |
|-----------|--------|
| 30 | "You're getting very cold. Your breath fogs." |
| 60 | "Your fingers are going numb. Fine manipulation difficult." |
| 80 | "Shivering uncontrollably. Movement slowed." |
| 100 | Death |

**Fungal Infection Thresholds**:
| Threshold | Output |
|-----------|--------|
| 20 | "A persistent cough develops." |
| 40 | "Fungal growth visible on your skin." |
| 60 | "Breathing becomes difficult." |
| 80 | "The spores whisper to you. Spore-speech possible." |
| 100 | Death or transformation |

### 3.2 Trust Tier Threshold (Echo)
```
Trigger: Echo trust crosses tier boundary
State Mutations:
  - Trust at new value
  - Echo behavior tier changes
Output for Narration:
  - Echo's tone shift
  - Appearance chance change
  - At +5: "Echo speaks your name for the first time"
Context Needed:
  - Direction of change (improving/worsening)
  - What caused the change
  - New tier behavior
```

### 3.3 NPC Trust Threshold
```
Trigger: NPC trust crosses service threshold
State Mutations:
  - Trust at new value
  - Services may unlock/lock
Output for Narration:
  - NPC attitude change
  - Service availability change
  - Relationship milestone
Context Needed:
  - What services affected
  - NPC personality
  - History with player
```

---

## 4. Scheduled Events

State changes from timer-triggered events.

### 4.1 Commitment Deadline Event
```
Trigger: Commitment deadline reached
State Mutations:
  - commitment.state = ABANDONED (if still ACTIVE)
  - Trust penalty
  - Gossip created
Output for Narration:
  - Time-based framing
  - NPC reaction
  - Consequences
Context Needed:
  - What was promised
  - NPC status
  - How much time passed
```

### 4.2 NPC Death Timer Event
```
Trigger: NPC survival timer expires
State Mutations:
  - NPC state machine -> "dead"
  - NPC actor marked as dead
  - Related commitments may fail
Output for Narration:
  - Death description
  - Emotional weight
  - Failure of any related commitments
Context Needed:
  - How NPC died
  - Player's relationship
  - Whether player tried to help
```

### 4.3 Environmental Milestone Event
```
Trigger: Spread milestone turn reached
State Mutations:
  - Locations modified
  - New hazards active
Output for Narration:
  - World change description
  - Affected areas
  - Increasing urgency
Context Needed:
  - Player's location
  - Progress toward halting
  - Total threat scope
```

---

## 5. Cascading Effects

State changes triggered by other state changes.

### 5.1 Commitment Abandoned -> Gossip Created
```
Trigger: Commitment becomes ABANDONED
Cascade:
  - gossip_on_abandon triggers create_gossip
  - Trust penalty applied
Output for Narration:
  - Immediate: Failure message
  - Later: Gossip arrival effects NPC attitudes
Context Needed:
  - Who will find out
  - When they'll know
  - Long-term reputation impact
```

### 5.2 Commitment Abandoned -> NPC Death
```
Trigger: Abandonment causes NPC to lose hope bonus
Cascade:
  - NPC condition severity increases rapidly
  - NPC may die
Output for Narration:
  - Connection between failure and death
  - Guilt/weight of consequence
Context Needed:
  - How hope bonus was keeping them alive
  - Whether other options existed
```

### 5.3 Location Property Change -> Condition Application
```
Trigger: Spread changes location temperature/hazard
Cascade:
  - Actors in location may gain conditions
  - Environmental effects begin
Output for Narration:
  - Sudden environment shift
  - New dangers
Context Needed:
  - Who's affected
  - Protection status
  - Escape options
```

### 5.4 Trust Threshold -> Service Availability
```
Trigger: Trust crosses service threshold
Cascade:
  - Services unlock or lock
  - Dialog options change
Output for Narration:
  - "The merchant now trusts you enough to..."
  - "The elder turns away, no longer willing to..."
Context Needed:
  - What services changed
  - NPC relationship context
```

### 5.5 Companion Restriction -> Waiting State
```
Trigger: Player moves to IMPOSSIBLE location for companion
Cascade:
  - companion.following = False
  - companion.waiting_at set
  - Player continues alone
Output for Narration:
  - Companion's refusal/inability
  - Where companion waits
  - Sadness/concern
Context Needed:
  - Why companion can't follow
  - How to reunite
  - Danger of proceeding alone
```

---

## EventResult Requirements

For each state change category, the EventResult returned must contain:

### Minimum Fields
```python
class EventResult:
    allow: bool          # Was the action allowed
    message: str | None  # Narration text (may be None for background changes)
```

### Extended Context (via message or separate field)
```python
# Example extended EventResult for commitment abandonment
EventResult(
    allow=True,
    message="You failed to save Sira in time. Elara will hear of this.",
    # Additional context for narrator (could be in message or separate dict):
    # - commitment_id: "commit_save_sira"
    # - npc_affected: "sira"
    # - trust_penalty: -3
    # - gossip_created: True
    # - gossip_targets: ["elara"]
)
```

---

## Narrator Query Interface

The LLM narrator may need to query state beyond what's in EventResult:

### Queries for Context
```python
# NPC personality/history
get_npc_description(npc_id) -> str
get_relationship_history(player, npc_id) -> list[str]

# Environmental context
get_location_description(location_id) -> str
get_active_hazards(location_id) -> list[str]

# Progress tracking
get_commitment_status(commitment_id) -> CommitmentState
get_trust_tier(npc_id) -> str
get_condition_severity(actor_id, condition_type) -> int

# World state
get_spread_progress(spread_id) -> str
get_crystal_restoration_progress() -> int
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-11 | Initial catalog |
