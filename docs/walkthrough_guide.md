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
