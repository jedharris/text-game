# Walkthrough Simulation Guide

## Purpose

Walkthroughs are **generative design tools**, not just validation exercises. The goal is to:

1. **Discover missing mechanisms** - What verbs, behaviors, and systems does the sketch assume but not define?
2. **Make concrete design decisions** - Where the sketch is vague, the walkthrough forces specific choices
3. **Evaluate gameplay quality** - Is it interesting? Frustrating? Boring? Too hard? Too easy?
4. **Identify gaps and dependencies** - What items/NPCs/paths are missing? What creates dead ends?

A walkthrough is a **design laboratory** where you play both player and game, making reasonable decisions, then evaluating whether those decisions create good gameplay.

---

## Prerequisites

Before starting a walkthrough:

1. **Review the region sketch** (e.g., `fungal_depths_sketch.json`)
   - Understand locations, exits, and connectivity
   - Know the actors, their state machines, and dialog topics
   - Know the items and their properties
   - Understand environmental rules and conditions
   - Review custom behavior specifications

2. **Review resolved questions** in the sketch
   - These are design decisions already made
   - Don't contradict them in the walkthrough

3. **Review previous walkthroughs** if any exist
   - Note design inputs that were generated
   - Note questions that were raised
   - Avoid redundant exploration of already-covered branches

---

## The Branching Tree Structure

### Why Trees, Not Linear Paths

A linear walkthrough forces you through the whole game multiple times to explore different choices. A branching tree lets you:

- Explore a decision point once, then branch
- Avoid redundant travel sequences
- See multiple outcomes from the same starting state
- Insert branches retroactively when you realize an earlier choice mattered

### Branch Points

Create a branch point when:

- Player has a meaningful choice (cure Aldric vs keep silvermoss)
- Player could take actions in different orders (talk first vs explore first)
- A puzzle has success and failure paths
- Combat could go different ways (fight, flee, diplomacy)

**Not** every command is a branch point. Movement, examining, routine inventory management - these are usually linear.

### Branch Naming

Use a consistent naming scheme:
```
TRUNK -> A (first major choice)
      -> A1, A2, A3 (sub-choices from A)
           -> A1a, A1b (sub-sub-choices)
      -> B (second major choice from trunk)
```

### Retroactive Branching

If you realize mid-walkthrough that an earlier choice mattered:
1. Note where the branch point should be
2. Continue current branch to completion (or a stable point)
3. Go back and write the alternative branch

---

## Walkthrough Format

### Turn Structure

Each turn should show:

```
=== Turn N ===
[Location: current_location]
[Player state: health, conditions, key inventory, relevant flags]

> player command

Game response describing what happens.

[State changes in brackets]
[ANNOTATIONS in brackets - see below]
```

### Annotations

Use these consistently:

| Tag | Meaning | Example |
|-----|---------|---------|
| `[MECHANISM: X]` | Requires engine/behavior support | `[MECHANISM: dialog_lib topic prerequisites]` |
| `[DESIGN INPUT: X]` | Decision made that needs review | `[DESIGN INPUT: trust +1 per topic]` |
| `[QUESTION: X]` | Ambiguity needing resolution | `[QUESTION: Where does gift item come from?]` |
| `[OBSERVATION: X]` | Gameplay quality note | `[OBSERVATION: This feels tedious]` |

### Being Generative

When the sketch doesn't specify something, **make a concrete decision** and mark it as `[DESIGN INPUT]`. Examples:

- Sketch says "trust builds through interaction" but doesn't say how much
  - Decision: `[DESIGN INPUT: Trust +1 per meaningful dialog topic]`

- Sketch says combat is "difficult" but doesn't give numbers
  - Decision: `[DESIGN INPUT: Spore Mother deals ~38 damage per round total]`

- Sketch says player needs a "gift" but doesn't list gift items in region
  - Decision: `[DESIGN INPUT: Add research_notes item on dead explorer in Grotto]`

These decisions become inputs to the design process. They may be accepted, modified, or rejected in review.

### Terse Travel, Verbose Interaction

**Compress** routine movement:
```
> go north, north, east
[Arrive at Luminous Grotto]
```

**Expand** meaningful interactions:
```
> ask aldric about infection

Aldric winces. "The spores got into my blood weeks ago..."
[Full dialog response]
[Flag set: knows_aldric_needs_silvermoss]
[Trust +1]
```

### Environmental Effects

Track environmental effects turn by turn:
```
[Infection ticks: severity 20 -> 25, damage 1]
[Player health: 99 -> 98]
```

This reveals whether pacing is appropriate - is the player taking too much damage? Not enough pressure?

---

## What to Explore

### Core Paths

Every region should have walkthroughs covering:

1. **Optimal peaceful path** - Player makes smart, diplomatic choices
2. **Optimal violent path** - Player fights everything possible
3. **Ignorant/rushing path** - Player skips dialog, misses hints
4. **Failure/recovery paths** - Player makes mistakes, how do they recover?

### Specific Things to Test

- **Information chains**: Can player learn what they need? In what order?
- **Item dependencies**: Does player have what they need when they need it?
- **Timing pressure**: Are time-limited elements (dying NPCs, spreading conditions) fair?
- **Combat viability**: Is violence a real option or effectively forbidden?
- **Dead ends**: Can player get stuck with no way forward?
- **Relationship thresholds**: Can player realistically reach trust/gratitude requirements?

### Cross-Region Interactions

For later walkthroughs, test:
- Items from Region A needed in Region B
- NPCs who move between regions
- Global flags affecting multiple regions
- Companions following across regions

---

## After the Walkthrough

### Summary Tables

Create summary tables for:

**Design Inputs Generated**
| ID | Input | Value | Notes |
|----|-------|-------|-------|
| DI-1 | Trust per dialog topic | +1 | ... |

**Questions Raised**
| ID | Question | Proposed Resolution |
|----|----------|---------------------|
| Q-1 | Where does gift item come from? | Add to Grotto |

**Mechanisms Required**
| Mechanism | Status | Notes |
|-----------|--------|-------|
| dialog_lib topic prerequisites | Exists | Works as expected |
| pour verb for liquids | Needed | Not yet implemented |

### Gameplay Observations

Categorize observations:

**Positive** - Things that work well, feel satisfying, create good tension

**Concerns** - Things that might be problems: too hard, too easy, confusing, tedious

**Boring Sections** - Repetitive or low-interest sequences that could be streamlined

**Frustrating Sections** - Places where player might feel stuck or unfairly punished

### Update the Sketch

After walkthrough review, update the sketch with:
- Resolved questions (move from open to resolved)
- New items/NPCs/dialog topics that were invented
- Adjusted numbers (damage, trust thresholds, etc.)
- New custom behavior requirements discovered

---

## Example Workflow

1. **Preparation** (5-10 min)
   - Read region sketch
   - Note key decision points to explore
   - Identify what previous walkthroughs have covered

2. **Trunk + First Branch** (20-30 min)
   - Write the main entry sequence
   - Reach first major decision point
   - Explore one branch to completion or stable point

3. **Additional Branches** (15-20 min each)
   - Return to decision points
   - Explore alternative choices
   - Note where branches converge or diverge permanently

4. **Summary and Tables** (10-15 min)
   - Compile design inputs
   - List questions raised
   - Note observations

5. **Sketch Update** (10-15 min)
   - Incorporate accepted design inputs
   - Add new items/NPCs/behaviors discovered
   - Update resolved questions

---

## Checklist for Each Region

Before considering a region "walked through":

- [ ] All locations visited at least once
- [ ] All NPCs interacted with (dialog, services, combat as appropriate)
- [ ] All items examined and used
- [ ] All puzzles solved (and failed)
- [ ] Environmental hazards experienced
- [ ] Key decision points branched
- [ ] Peaceful path completed
- [ ] Violent path attempted (even if it fails)
- [ ] Failure/recovery tested
- [ ] Cross-region dependencies identified
- [ ] Summary tables completed
- [ ] Sketch updated with findings

---

## Tips

- **Don't skip "obvious" commands** - They may reveal missing mechanisms
- **Play devil's advocate** - Try commands the designer didn't anticipate
- **Note boredom honestly** - If writing the walkthrough feels tedious, playing will too
- **Track turn count** - It reveals pacing issues
- **Simulate player confusion** - What if they don't read the hint carefully?
- **Test edge cases** - What if they try to give an item they don't have? Attack a friendly NPC?

---

## Design Patterns Established

Through completed walkthroughs, these design patterns have been established and should be followed:

### Difficulty Philosophy

- **Per-region difficulty**: Most regions should take 2+ playthroughs to succeed with all challenges
- **Cross-region difficulty**: Challenges spanning multiple regions should take 3-5 playthroughs to succeed with all
- **First playthrough experience**: Near-impossible optimal outcomes on first playthrough is good design, not bad. Otherwise the game is too easy.
- **Foreknowledge value**: Players who replay should be able to optimize and achieve better outcomes

### Environmental Hazards vs Combat Encounters

Distinguish clearly between:

**Environmental hazards** (predatory fish, spore clouds, cold zones):
- Obstacles that impede progress or cause damage
- NOT combat encounters - no XP, no loot
- Combat against them is penalized or impossible
- Avoidance, escape, or mitigation are the intended solutions
- May have behavioral rules (fish patrol areas, spores drift)

**Combat encounters** (hostile NPCs, aggressive creatures):
- Can be fought with potential victory
- May yield rewards or consequences
- Player has agency in engagement

### NPC Binding and Restrictions

Some NPCs cannot leave their locations. Each case requires **strong narrative justification**:

| NPC | Restriction | Narrative Justification | Related Consequences |
|-----|-------------|------------------------|---------------------|
| Scholar Aldric | Too sick to walk | Infection weakens him | Dies if not helped |
| The Archivist | Spectral, bound to archive | Would retrieve fragments herself if she could leave | Knowledge quest requires player |
| The Echo | Bound to Nexus | Spectral remnant tied to ley lines | Can only observe, not act |

**Key principle**: If an NPC could solve their own problem by leaving, they must be prevented from leaving with strong narrative support.

### Knowledge/Fragment Quest Pattern

When a quest requires gathering scattered pieces:

- Design more pieces than required (e.g., 5 fragments, need 3)
- Some pieces should require rescued/befriended NPCs to access
- This creates value in relationships beyond immediate rewards
- Allows partial completion even with suboptimal playthrough

### Commitment System

Player commitments ("I'll help you") create four states:

| State | Meaning | Effect |
|-------|---------|--------|
| **pending** | Committed, not yet fulfilled | NPC waits, may have extended survival |
| **fulfilled** | Promise kept | Base reward + bonus (typically +2 trust) |
| **withdrawn** | Explicitly returned to apologize | Neutral or small positive; NPC may offer hints |
| **abandoned** | NPC dies or timer expires | Negative spread to related NPCs |

**Withdrawal is valuable**: Coming back to apologize shows courage, often yields helpful information, allows recommitment. No penalty.

**Hope extends survival**: Some NPCs live longer when player commits (situational - only when narratively appropriate; drowning doesn't care about hope).

### Time-Pressure Analysis

For scenarios with time pressure (dying NPCs, drowning survivors), create explicit timing breakdowns:

```
"timing_breakdown": {
  "learn_basic_swimming": "1 turn",
  "travel_to_garrett": "3 turns (plaza → chambers → passage → caves)",
  "rescue_garrett": "2 turns (find, free)",
  ...
}
"total_minimum_turns": 15
"survivor_turn_limits": {"garrett": 12, "delvan": 18}
"designed_difficulty": "Very difficult on first playthrough, achievable with foreknowledge"
```

This reveals whether the challenge is fair and what tradeoffs players face.

### Companion Restrictions

Companions (wolves, salamanders, myconids, etc.) have region restrictions:

**Hard restrictions**: Cannot enter (magical wards, elemental conflict, instant death)
**Soft restrictions**: Uncomfortable (penalties, complaints, may refuse certain areas)
**Exceptional individuals**: Rare NPCs may ignore specific restrictions with strong narrative motivation

See `cross_region_dependencies.md` for full table.

### Freedom from Time Pressure (Frozen Reaches Pattern)

Not every region needs dying NPCs or urgent situations. Frozen Reaches demonstrated that **methodical exploration** can be satisfying:

- **No dying NPCs**: Salamanders are fine without player help
- **Environmental pressure without urgency**: Cold creates tension and resource management, but player can retreat to hot springs indefinitely
- **Sanctuary locations**: Hot springs serve as safe planning area
- **Reward for preparation**: Telescope provides strategic information about ALL other regions - powerful reward for thorough players

This creates valuable **pacing variety** across the game:
- Sunken District: Frantic dual-rescue with tight timing
- Beast Wilds: Urgent commitments (dying cubs, bleeding hunter)
- Frozen Reaches: Methodical exploration, environmental puzzle
- Fungal Depths: Moderate pressure (infection progresses but manageable)

### Puzzle vs Combat Encounters

Some encounters should offer **both paths** without one being obviously inferior:

**Frozen Reaches Golems** established the pattern:
- **Password solution**: Research (read inscriptions) → passive golems
- **Control crystal solution**: Exploration (find hidden cave passage) → serving golems (best outcome)
- **Ritual offering solution**: Resource gathering (fire item + hot springs water) → passive golems
- **Combat solution**: Very difficult (~36 rounds optimized), resource-intensive, but **possible**

Combat should be:
- Available as "hard mode" for players who insist
- Clearly punishing compared to puzzle solutions
- Not impossible - skilled/prepared players can succeed
- Have consequences (destroyed golems can't later serve/protect)

### Portable Resources with Duration

Items that provide temporary benefits create interesting resource decisions:

**Salamander-heated stone** pattern:
- Provides benefit (cold immunity) for limited duration (~20 turns)
- Creates bond with NPC who provides it
- Returning item increases relationship
- Not returning (or returning cooled) has minor negative effect

This pattern could apply to:
- Borrowed equipment
- Consumable buffs
- Temporary companion effects

### Social Hazards (Civilized Remnants Pattern)

Not all regions need environmental or combat threats. Civilized Remnants demonstrated that **social hazards** create meaningful gameplay:

- **Reputation as health**: Bad reputation locks services, eventually causes exile
- **Dual reputation tracks**: Surface town vs undercity can conflict - high undercity + discovery damages town rep
- **Social gatekeeping**: Guards check for infection, companions, contraband
- **Skill gating with narrative justification**: Garden access requires herbalism because nightshade is contact poison

Social consequences feel earned because they're predictable and explained.

### Moral Complexity in Dilemmas

Council dilemmas established patterns for meaningful choices:

**No clear right answer**: Each option favors different values (pragmatism, idealism, commerce)
**Discoverable compromises**: Initial options can be refined through dialog - "labor with family support" emerges from discussion
**Probabilistic outcomes**: Some decisions (trader admission) have uncertain results (80% clean, 20% infected)
**Different councilors react differently**: Player can optimize for specific councilor or seek universal approval

The key is that **players shouldn't feel tricked** - consequences should flow logically from choices.

### Two-Tier Skill Progression

Civilized Remnants established herbalism progression:

- **Tier 1 (Maren, trust 2)**: Basic identification, safe handling of most plants
- **Tier 2 (Elara, trust 3)**: Full mastery, safe handling of deadly plants

This pattern works because:
- Different NPCs teach different tiers (clear progression)
- Trust gates the teaching (relationship matters)
- Narrative justification exists (nightshade poison is real danger)
- Each tier unlocks meaningful content (garden access, nightshade harvest)

### Cross-Region NPC Connections

NPCs should have relationships that span regions:

**Elara-Sira connection**: Childhood friends who chose different paths. Helping Sira in Beast Wilds earns trust with Elara in Civilized Remnants.

**Delvan-Undercity connection**: If rescued in Sunken District, provides undercity access in Civilized Remnants.

**Aldric relocation**: If saved in Fungal Depths, may appear as teacher in Civilized Remnants.

These connections:
- Reward thorough exploration
- Make the world feel interconnected
- Create meaningful choices (help Sira → Elara trust)
- Allow consequences to spread between regions

### Dark Paths Without Forcing

The Undercity provides criminal options without requiring them:

- **Discovery is hidden**: 5% chance per service used
- **Discovery escalates**: First discovery = -2 reputation, repeated = exile
- **Assassination exists**: 20% discovery chance, massive consequences even if undiscovered
- **Echo always knows**: Even successful assassination marks player's record

Design principle: Dark paths should be **available but not encouraged**, with **clear consequences** that make the choice meaningful.

---

## Walkthrough Progress

### Completed Regions

| Region | Sketch Version | Walkthrough | Key Findings |
|--------|---------------|-------------|--------------|
| Fungal Depths | v0.2 | Complete | Commitment system, state machines, infection mechanics |
| Beast Wilds | v0.2 | Complete | Companion restrictions, trust thresholds, pack dynamics |
| Sunken District | v0.2 | Complete | Environmental hazards, time pressure, NPC binding |
| Frozen Reaches | v0.2 | Complete | Freedom from time pressure, puzzle vs combat choice, telescope strategic reward, salamander befriending without urgency |
| Civilized Remnants | v0.2 | Complete | Social hazards, dual reputation, moral complexity, two-tier herbalism, undercity dark paths, cross-region NPC connections |

### Remaining Regions

| Region | Priority | Notes |
|--------|----------|-------|
| **Meridian Nexus** | Next (last) | Safe hub, The Echo, commitment tracking, waystone repair endgame |

### Cross-Region Walkthroughs

After all individual regions are complete, conduct cross-region walkthroughs to test:
- Item dependencies across regions
- NPC movement and companion restrictions
- Environmental spread effects
- Waystone repair quest (full game)
- Reputation spread mechanics
