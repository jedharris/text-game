# Fungal Depths Walkthrough Tree

## Purpose
This document simulates gameplay through the Fungal Depths region to:
1. Discover missing mechanisms and design gaps
2. Evaluate gameplay quality (pacing, difficulty, interest)
3. Generate concrete design inputs for review

## Notation
- `[MECHANISM: X]` - Requires engine/behavior support for X
- `[DESIGN INPUT: X]` - Decision made during simulation, needs review
- `[QUESTION: X]` - Ambiguity that needs resolution
- `[OBSERVATION: X]` - Gameplay quality note

## Initial State
- Player starts in Nexus Chamber with basic equipment
- No fungal infection
- No special skills or knowledge
- Turn counter: 0

---

## TRUNK: Enter Fungal Depths

```
=== Turn 1 ===
[Location: Nexus Chamber]
[Player state: health=100, infection=none, inventory=[rusty_sword]]

> go west

You descend stone steps into a damp passage. Cool air rises from below,
carrying a faint musty smell. A faint phosphorescent glow illuminates
the darkness ahead.

You are in the Cavern Entrance.

A small campfire burns near a worn bedroll. A frail scholar sits beside
it, pale and visibly ill. Fungal patches are visible on his neck and arms.

Scholar Aldric is here.
You see a journal here.

Exits: east (to Nexus), down (to Luminous Grotto)
```
[OBSERVATION: Good atmospheric entry. Player immediately sees Aldric is sick - clear hook.]

```
=== Turn 2 ===
> look at aldric

Scholar Aldric is a frail man with pale skin and dark circles under
his eyes. Fungal patches are visible on his neck and arms. He coughs
occasionally and seems weakened by illness. Despite his condition,
his eyes are alert and intelligent.
```
[MECHANISM: examine actor shows description + visible conditions]

```
=== Turn 3 ===
> talk to aldric

Aldric looks up with tired but hopeful eyes.

You could ask Aldric about: infection, research, myconids
```
[MECHANISM: dialog_lib.handle_talk_to returns available topic hints]
[DESIGN INPUT: These are the initially available topics. "spore_mother" and "safe_path" require flags.]

---

## BRANCH POINT A: First Aldric Interaction

### Branch A1: Ask about infection first

```
=== Turn 4a ===
> ask aldric about infection

Aldric winces. "The spores got into my blood weeks ago. I've been
treating myself with what little silvermoss I can find, but it's not
enough. If you could find more silvermoss - it grows in the Luminous
Grotto below - I might have a chance."

[Flag set: knows_aldric_needs_silvermoss = true]
[Aldric trust +1]
```
[DESIGN INPUT: Asking about a personal topic (their suffering) builds trust +1]
[MECHANISM: dialog topic sets flags and modifies relationships]

```
=== Turn 5a ===
> ask aldric about research

His eyes light up despite his illness. "I've spent years studying
these fungi. The spores aren't just a disease - they're communication.
The Spore Mother sends them to find hosts, yes, but also to... share?
If I survive this, I can teach you what I know about navigating the depths."

[Aldric trust +1, now at 2]
```
[DESIGN INPUT: Trust +1 per meaningful topic. After 2 topics, trust = 2 (teaching threshold)]
[OBSERVATION: This feels right - genuine conversation builds relationship]

```
=== Turn 6a ===
> ask aldric about spore mother

"She's not evil, you know. She's dying too - the same infection that's
killing me is killing her. She spreads spores in desperation, trying
to find a cure. There's a rare moss in the Deep Root Caverns - heartmoss
- that might cure her. But the air down there is poison."

[Flag set: knows_about_heartmoss = true]
[Topic unlocked: safe_path]
```
[MECHANISM: Topic requires knows_aldric_needs_silvermoss flag, which we have]
[OBSERVATION: Good information chain - must ask about infection before learning about cure]

```
=== Turn 7a ===
> ask aldric about safe path

"There's a safe path through the Spore Heart to the Deep Root Caverns
- pockets of clean air if you know where to find them. The ceiling in
the Luminous Grotto shows the way, but you'd need more light to read it."

[Flag set: knows_safe_path_exists = true]
```
[OBSERVATION: Player now knows: 1) silvermoss in grotto, 2) heartmoss in deep roots, 3) need light to find safe path]
[OBSERVATION: Good breadcrumb trail - doesn't tell player exactly what to do, but gives direction]

```
=== Turn 8a ===
> take journal

You pick up the journal.

[Inventory: rusty_sword, journal]
```

```
=== Turn 9a ===
> read journal

Extensive notes on fungal life cycles. Key insight: "The Spore Mother
is not the source of infection - she is its greatest victim. The
heartmoss in the Deep Root Caverns may be her only hope - and ours."
```
[MECHANISM: "read" verb for items with read_content property]
[OBSERVATION: Journal reinforces what Aldric said - good for players who skip dialog]

---

### Branch A2: Ignore Aldric, go straight down

```
=== Turn 4b ===
> go down

You descend a slippery passage into a soft blue-green glow.

You are in the Luminous Grotto.

Bioluminescent mushrooms cast soft light - blue, red, and green caps
glow dimly. A crystal-clear pool reflects the light. Strange symbols
are carved into the ceiling, but it's too dark to read them clearly.

The air is thick with floating spores. You feel them entering your lungs.

[Fungal infection applied: severity 5]
[MECHANISM: on_enter for medium spore room applies infection]

You see: bucket, blue mushroom, red mushroom, green mushroom, pool, silvermoss

Exits: up (to Cavern Entrance), down (to Spore Heart), east (to Myconid Sanctuary)
```
[OBSERVATION: Immediate consequence for rushing past - infection starts]
[DESIGN INPUT: Medium spore = 5 severity per turn. Is this too aggressive?]

```
=== Turn 5b ===
> take silvermoss

You carefully pluck the silvermoss from where it grows near the pool.
It glows faintly with a soft blue light.

[Inventory: rusty_sword, silvermoss]
[Infection ticks: severity now 10, 0 damage (below damage threshold)]
```
[DESIGN INPUT: Damage starts at severity 20 (1 damage/turn). Severity 10 = uncomfortable but not dangerous yet]
[MECHANISM: condition tick happens at end of turn]

---

## BRANCH POINT B: After Getting Silvermoss

Player has silvermoss. Key decision: cure Aldric or save it?

### Branch B1: Cure Aldric immediately

```
=== Turn 10 (continuing from A1 path) ===
[Location: Cavern Entrance]
[State: knows about heartmoss, safe path, has silvermoss, trust with Aldric = 2]

> give silvermoss to aldric

Aldric's eyes widen with hope. He takes the silvermoss and carefully
applies it to his skin, then consumes the rest.

Color returns to his cheeks almost immediately. The fungal patches
begin to fade. He takes a deep breath - the first clean breath in weeks.

"Thank you. I thought I was going to die down here. You've saved my life."

[Aldric state: infected -> cured]
[Silvermoss consumed]
[Aldric gratitude +3]
[MECHANISM: treatment system auto-applies cure when receiving curative item]
```
[OBSERVATION: Very satisfying moment. Clear cause and effect.]

```
=== Turn 11 ===
> talk to aldric

Aldric stands straighter now, his strength returning.

"I can teach you what I know about these depths - how to recognize
safe paths, how to handle fungal creatures. But such knowledge takes
time to impart. Do you have something to trade for my time? Notes
from your own travels, perhaps, or a rare herb?"

You could ask Aldric about: teaching, myconids, spore mother
```
[MECHANISM: New topics available in cured state]
[DESIGN INPUT: Aldric asks for a gift to teach. Player needs "rare_herb" or "research_notes"]

```
=== Turn 12 ===
> ask aldric about teaching

"My knowledge of mycology - fungal biology, safe navigation, creature
behavior - I can share it with you. But it represents a lifetime of
work. I'd need something in return. Rare herbs, research materials...
something that shows you value what I'm offering."

[Trust requirement: 2 (met), Gift requirement: rare_herb, research_notes, or offering_item]
```
[QUESTION: Where does the player get a gift item for Aldric? Need to add one to the region or require cross-region travel]

---

### Branch B2: Keep silvermoss for self, let Aldric suffer

```
=== Turn 10alt ===
[Location: Luminous Grotto, has silvermoss, infection severity 10]

> use silvermoss on self

You apply the silvermoss to your skin and breathe in its healing essence.
The tightness in your lungs eases. The infection fades.

[Fungal infection cured]
[Silvermoss consumed]
```
[MECHANISM: use curative item on self]
[OBSERVATION: Valid choice but player loses Aldric as resource. Consequence will emerge later.]

```
=== Turn 11alt ===
> go up

You climb back to the Cavern Entrance.

Aldric looks at you hopefully, then notices your healthy complexion.
His expression falls slightly.

"You found silvermoss. I... I see you needed it yourself."

[Aldric trust -1]
```
[DESIGN INPUT: Aldric notices you cured yourself. Trust penalty for not helping when you could have.]
[QUESTION: Is this too punishing? Player may not have known they could cure Aldric.]

---

## BRANCH POINT C: Exploring the Grotto Puzzle

```
=== Turn 13 (from B1 path, Aldric cured) ===
[Location: Luminous Grotto]
[State: infection severity 5 (from brief exposure), knows about ceiling inscription]

> look at ceiling

Strange symbols are carved into the ceiling, but the dim bioluminescent
light isn't bright enough to read them clearly. You'd need more light.
```
[MECHANISM: Examine reveals puzzle hint]

```
=== Turn 14 ===
> take bucket

You pick up the wooden bucket. It's empty.

[Inventory: rusty_sword, journal, bucket]
[Infection ticks: severity 10]
```

```
=== Turn 15 ===
> fill bucket from pool

You dip the bucket into the crystal-clear pool. It fills with water.

[Bucket state: filled = true]
[Infection ticks: severity 15]
```
[MECHANISM: "fill X from Y" verb for containers and water sources]

```
=== Turn 16 ===
> pour water on blue mushroom

You pour water from the bucket onto the blue mushroom. The mushroom
absorbs the water eagerly. After a moment, it begins to glow brightly,
casting blue light across the cavern.

[Blue mushroom: watered = true, glowing = true]
[Bucket: filled = false]
[Grotto light_level: 1 -> 2]
[Puzzle sequence: ["blue"]]
[Infection ticks: severity 20, damage 1]
```
[MECHANISM: pour verb, mushroom watering behavior, room light tracking]
[DESIGN INPUT: First damage at severity 20. Player has taken 5 turns in grotto, now taking damage.]
[OBSERVATION: Good pressure - puzzle has time cost]

```
=== Turn 17 ===
> fill bucket from pool

You refill the bucket with water from the pool.

[Bucket: filled = true]
[Infection ticks: severity 25, damage 1]
[Player health: 99]
```

```
=== Turn 18 ===
> pour water on green mushroom

You pour water onto the green mushroom. It glows brightly with green light.

[Green mushroom: glowing = true]
[Grotto light_level: 2 -> 3]
[Puzzle sequence: ["blue", "green"]]
[Infection ticks: severity 30, damage 1]
[Player health: 98]
```

```
=== Turn 19 ===
> fill bucket

You refill the bucket.
[Infection ticks: severity 35, damage 1]
[Player health: 97]
```

```
=== Turn 20 ===
> pour water on red mushroom

You pour water onto the red mushroom. It glows brightly with crimson light.

The combined glow of all three mushrooms illuminates the ceiling fully!

You can now read the inscription: a winding path is depicted - showing
pockets of clean air through a dangerous area. You commit the route to memory.

[Red mushroom: glowing = true]
[Puzzle COMPLETE]
[Flag set: safe_path_known = true]
[Infection ticks: severity 40, damage 2]
[Player health: 95]
```
[MECHANISM: Puzzle completion triggers flag and message]
[OBSERVATION: Puzzle took 5 turns (15-20). Player took 8 total damage and has severity 40 infection.]
[DESIGN INPUT: Is severity 40 too high? Player needs to seek cure soon or will be in trouble.]

---

### Branch C1: Wrong puzzle sequence

```
=== Turn 16alt ===
> pour water on red mushroom

You pour water onto the red mushroom. It glows brightly with crimson light.

[Red mushroom: glowing = true]
[Puzzle sequence: ["red"]]  -- WRONG ORDER
```

```
=== Turn 17alt ===
> fill bucket
> pour water on blue mushroom

The blue mushroom glows... but suddenly all the mushrooms flash and go dark.
The sequence wasn't right. You'll need to start over.

[All mushrooms: glowing = false, watered = false]
[Puzzle sequence: reset to []]
```
[MECHANISM: Wrong sequence resets puzzle]
[OBSERVATION: Failure costs turns = more infection. Good stakes for puzzle.]

---

## BRANCH POINT D: Entering Spore Heart

```
=== Turn 21 (puzzle complete, severity 40) ===
> go down

[Checking: safe_path_known = true]

You descend carefully, following the route you memorized from the ceiling.
The air grows thick with spores, but you know where the clean pockets are.

You are in the Spore Heart.

Organic walls pulse with a strange rhythm. At the center rests a massive
fungal creature - the Spore Mother. Her cap spreads wide, pulsing weakly.
She seems to be in pain. Smaller fungal creatures - sporelings - cluster
around her protectively.

The air here is extremely spore-heavy, but your knowledge of the safe
path lets you breathe more easily.

Spore Mother is here. (hostile)
Sporeling is here. (hostile)
Sporeling is here. (hostile)
Sporeling is here. (hostile)

[MECHANISM: safe_path_known reduces spore severity gain in this room]
[DESIGN INPUT: With safe path: +5 severity/turn instead of +10]

Exits: up (to Luminous Grotto), down (to Deep Root Caverns - you know the way)
```
[OBSERVATION: Player can now access Deep Root Caverns because they solved the puzzle]

---

### Branch D1: Try to talk to Spore Mother

```
=== Turn 22 ===
> talk to spore mother

The Spore Mother's massive cap turns toward you. A wave of spores
washes over you - not an attack, but... communication? You sense
pain, desperation, a plea for help.

The sporelings tense but don't attack. They're waiting to see what
their mother does.

[Spore Mother: disposition remains hostile, but no_attack_this_turn = true]
[DESIGN INPUT: Attempting communication delays combat for 1 turn]
```
[OBSERVATION: This gives player a chance to realize peaceful solution exists]

```
=== Turn 23 ===
> give heartmoss to spore mother

You don't have any heartmoss.

[Combat begins - sporelings attack]
A sporeling puffs spores at you! [Hit: 5 damage, infection +10]
A sporeling puffs spores at you! [Miss]
A sporeling lunges! [Hit: 3 damage]

[Player health: 87]
[Infection severity: 55]
```
[MECHANISM: Attempted give with missing item triggers combat (patience exhausted)]
[DESIGN INPUT: Trying to give something you don't have breaks the temporary peace]
[OBSERVATION: Player now knows they need heartmoss, but are in combat]

---

### Branch D2: Attack immediately

```
=== Turn 22alt ===
> attack spore mother

You swing your rusty sword at the Spore Mother!
[Hit: 15 damage to Spore Mother (200 -> 185)]

The Spore Mother shrieks - a sound like tearing fungus. The sporelings
swarm to attack!

[Combat initiated]
[Spore Mother counterattacks: tendril lash! Hit: 25 damage]
Sporeling attacks! [5 damage, infection +10]
Sporeling attacks! [5 damage, infection +10]
Sporeling attacks! [3 damage]

[Player health: 62]
[Infection severity: 60]
[Global flag set: has_killed_fungi = false (not dead yet, but marked for potential)]
```
[DESIGN INPUT: Combat is BRUTAL. Player took 38 damage in one round.]
[OBSERVATION: This is meant to discourage pure combat approach. Is it too punishing?]

```
=== Turn 23alt ===
> attack spore mother

[Hit: 15 damage (185 -> 170)]
[Spore Mother regenerates: 170 -> 180]

Spore Mother: tendril lash [Hit: 25 damage]
Sporeling [5 damage]
Sporeling [5 damage]
Sporeling [3 damage]

[Player health: 24]
[Infection severity: 65, damage 3]
[Player health after infection: 21]
```
[OBSERVATION: Player is nearly dead after 2 combat rounds. Regeneration makes this almost unwinnable.]
[DESIGN INPUT: Combat is intentionally very hard to push toward peaceful solution]

```
=== Turn 24alt ===
> flee / go up

You scramble back up the passage, the sporelings snapping at your heels!

[Escape successful]
[Location: Luminous Grotto]
[Player health: 21, infection severity 70]
```
[MECHANISM: Flee/escape from combat]
[OBSERVATION: Player is in critical condition. Must seek cure immediately.]

---

## BRANCH POINT E: Getting Heartmoss (Peaceful Path)

```
=== Turn 22 (didn't attack, going for heartmoss) ===
[Location: Spore Heart, Spore Mother is hostile but not attacking yet]

> go down

[Checking: safe_path_known = true, has_breathing_equipment = false]

You know the safe path, but the Deep Root Caverns have no breathable air.
You'll need breathing equipment to survive down there.

Do you want to proceed anyway? (You will take 15 damage per turn)
```
[MECHANISM: Warning before entering lethal environment]
[DESIGN INPUT: Engine asks for confirmation before suicidal action]

```
=== Turn 22 (alternative - has breathing mask) ===
[Assuming player got mask from Myconids first - see Branch F]

> wear mask

You put on the breathing mask. The woven fungal fibers filter the air.

[Breathing mask: equipped = true]
[Player now has breathing protection]
```

```
=== Turn 23 ===
> go down

You descend into absolute darkness. Your breathing mask filters the
toxic air, but you can't see anything.

You are in the Deep Root Caverns.

Massive roots thicker than trees pierce the ceiling somewhere above.
You can feel them but not see them. The cold seeps into your bones.

[Darkness: cannot see items or navigate effectively without light]
```
[MECHANISM: darkness_lib prevents seeing/taking items without light]
[QUESTION: Can player feel their way to heartmoss? Or is light mandatory?]

```
=== Turn 23 (with spore lantern) ===
[Assuming player has spore lantern from Myconids]

The spore lantern casts a steady glow, revealing the cavern.

Ancient roots twist down from above. On one of them, you spot a
deep-red moss pulsing with faint warmth - heartmoss!

You see: heartmoss

Exits: up (to Spore Heart)
```

```
=== Turn 24 ===
> take heartmoss

You carefully harvest the heartmoss. It pulses warmly in your hands,
as if alive.

[Inventory: ..., heartmoss]
```

```
=== Turn 25 ===
> go up
> go up

[Location: Spore Heart]

The Spore Mother turns toward you. The sporelings tense.
```

```
=== Turn 26 ===
> give heartmoss to spore mother

You approach the Spore Mother carefully, holding out the heartmoss.

She extends a trembling tendril and takes it. The heartmoss dissolves
into her form, spreading healing warmth.

The pulsing of the organic walls steadies. The Spore Mother's
bioluminescence grows stronger, healthier. The pain in her presence fades.

A wave of... gratitude?... washes over you through the spores.

The sporelings relax. They regard you with something like curiosity now.

[Spore Mother: fungal_blight CURED]
[Spore Mother: hostile -> friendly]
[All sporelings: hostile -> friendly]
[Global effect: ALL Fungal Depths rooms - spore_level becomes "none"]
[Flag set: spore_mother_healed = true]
```
[MECHANISM: Region-wide state change on cure]
[OBSERVATION: MAJOR PAYOFF MOMENT. Very satisfying resolution.]

```
=== Turn 27 ===
> look

You are in the Spore Heart.

The organic walls pulse with healthy rhythm. The Spore Mother rests
peacefully, her cap glowing with vibrant bioluminescence. The air is
clean and easy to breathe.

Spore Mother is here. (friendly)
Sporeling is here. (friendly)
Sporeling is here. (friendly)
Sporeling is here. (friendly)

[Infection no longer progressing - no spores in air]
```
[OBSERVATION: Environment completely transformed. Player's actions changed the world.]

---

## BRANCH POINT F: Myconid Sanctuary

```
=== Turn X (branching from Grotto, before or after puzzle) ===
[Location: Luminous Grotto]

> go east

You follow a smooth-walled tunnel into a surprisingly orderly cavern.

You are in the Myconid Sanctuary.

Rings of sentient mushroom beings stand in silent communion,
communicating through puffs of colored spores. The air here is
clean - no wild spores. A tall Myconid with a weathered cap
marked by age-rings regards you.

Myconid Elder is here. (neutral)

You see: spore lantern, breathing mask

Exits: west (to Luminous Grotto)
```

### Branch F1: Player has not killed any fungi

```
=== Turn X+1 ===
> talk to myconid elder

[Checking global flag: has_killed_fungi = false]

The Myconid releases a cloud of blue spores. Somehow, you understand:
"Soft-flesh comes to the Still Place. Why?"

You could ask the Elder about: cure, resistance, spore mother
```

### Branch F2: Player has killed fungi (e.g., attacked sporelings earlier)

```
=== Turn X+1 (killed fungi) ===
> talk to myconid elder

[Checking global flag: has_killed_fungi = true]
[Myconid Elder trust: 0 -> -3]

The spores around you turn dark, accusatory.

"Soft-flesh carries death-smell. You have ended our kin. Trust is... difficult."

The Myconid's posture is closed, wary.

You could ask the Elder about: cure, resistance, spore mother
```
[MECHANISM: First interaction checks kill flag and applies trust penalty]
[DESIGN INPUT: -3 trust means player starts at -3, needs significant effort to reach +2 for teaching]
[OBSERVATION: Real consequence for violence. Player can still interact but starts at disadvantage.]

```
=== Turn X+2 ===
> ask elder about cure

A pulse of green spores. "The blight-sickness, yes. We can draw it
from soft-flesh. But there is cost. Bring us crystal from the Frozen
Reaches, or rare minerals. Then we help."

[Flag set: knows_myconid_cure_cost = true]
```
[DESIGN INPUT: Cure requires item from another region (ice_crystal) OR gold/rare_mineral]
[QUESTION: Should there be a local source of payment? Or force cross-region travel?]

```
=== Turn X+3 ===
> ask elder about resistance

Yellow spores swirl. "We can teach soft-flesh to breathe our air safely.
This knowledge we share... but only with those we trust, and only for
fair exchange."

[Player learns: resistance teaching requires trust >= 2 plus gift]
```

```
=== Turn X+4 ===
> take spore lantern

[Checking: Myconid trust level]

[If trust >= 0]:
The Elder gestures assent with a spore puff. You take the lantern.
[Inventory: ..., spore lantern]

[If trust < 0]:
The Elder's spores flash red. "Not for death-bringer. Earn trust first."
[Cannot take item]
```
[DESIGN INPUT: Items in Myconid sanctuary require non-negative trust to take]
[OBSERVATION: Player who killed fungi can't easily get equipment they need]

```
=== Turn X+5 ===
> take breathing mask

[Same trust check as above]
```

---

## Summary of Branches Explored

1. **Trunk -> A1 (talk to Aldric)** -> Complete Aldric dialog chain, learn about heartmoss and safe path
2. **Trunk -> A2 (ignore Aldric)** -> Rush to grotto, get infected immediately
3. **A1 -> B1 (cure Aldric)** -> Aldric becomes teaching resource, but needs gift
4. **A1 -> B2 (keep silvermoss)** -> Cure self, lose Aldric's trust
5. **B1 -> C (grotto puzzle)** -> Complete puzzle, learn safe path (5 turns, infection buildup)
6. **C -> C1 (wrong sequence)** -> Puzzle reset, costs extra turns
7. **C -> D (enter Spore Heart)** -> With safe path, reduced spore damage
8. **D -> D1 (try diplomacy)** -> Temporary peace, but need heartmoss
9. **D -> D2 (attack)** -> Nearly die in 2 rounds, demonstrates combat is very hard
10. **D -> E (get heartmoss)** -> Requires mask + lantern, then major payoff healing Spore Mother
11. **Trunk/C -> F (Myconids)** -> Equipment source, cure service, trust mechanics

---

## Design Inputs Generated

| ID | Input | Current Value | Notes |
|----|-------|---------------|-------|
| DI-1 | Trust gain per meaningful dialog topic | +1 | 2 topics to reach teaching threshold |
| DI-2 | Medium spore severity per turn | 5 | 8 turns to reach damage threshold |
| DI-3 | High spore severity per turn | 10 | Very aggressive, need protection |
| DI-4 | Infection damage threshold | severity 20 | Below this, uncomfortable but no damage |
| DI-5 | Infection damage formula | severity/20 rounded down | At 40, 2 damage/turn |
| DI-6 | Puzzle turns required | 5 (optimal) | More if wrong sequence |
| DI-7 | Spore Mother combat damage per round | ~38 (all enemies) | Intentionally brutal |
| DI-8 | Spore Mother regeneration | 10 HP/turn | Makes pure combat very hard |
| DI-9 | Trust penalty for killing fungi | -3 | Significant but recoverable |
| DI-10 | Trust to take Myconid items | >= 0 | Killer can't easily get equipment |
| DI-11 | Safe path benefit | Reduces spore gain by 50% | Makes puzzle worthwhile |

---

## Questions Raised

| ID | Question | Proposed Resolution |
|----|----------|---------------------|
| Q-NEW-1 | Where does player get gift for Aldric teaching? | Add "research notes" item in Grotto (on a dead explorer?) |
| Q-NEW-2 | Can player feel heartmoss in darkness? | No, light is mandatory. Forces getting lantern first. |
| Q-NEW-3 | What if player enters Deep Roots without mask? | Confirmation prompt + 15 damage/turn. Can survive ~6 turns. |
| Q-NEW-4 | Can Myconid cure work without cross-region item? | Add gold coins somewhere in Fungal Depths? Or require travel. |
| Q-NEW-5 | How does trust recover after killing fungi? | Healing Spore Mother +5, bringing offerings +1. Recoverable but slow. |
| Q-NEW-6 | Does Aldric die if player takes too long? | Yes, death_turn_threshold = 40. Need to track and show warnings. |

---

## Observations on Gameplay Quality

### Positive
- Clear information breadcrumb trail (Aldric -> silvermoss -> heartmoss -> safe path)
- Meaningful consequences for choices (cure Aldric vs self, violence vs peace)
- Environmental pressure (infection) creates urgency without hard timers
- Puzzle has stakes (each turn costs infection)
- Major payoff moment when curing Spore Mother (transforms entire region)
- Violence path is viable but very hard and has lasting consequences

### Concerns
- **Gift item gap**: Player needs rare_herb/research_notes for Aldric teaching, but none are in the region
- **Equipment dependency**: Without mask+lantern, Deep Root Caverns are inaccessible. Both are in Myconid sanctuary. If player killed fungi, they're stuck.
- **Pacing**: Optimal path is ~26 turns for cure-Spore-Mother ending. Is that too long or too short?
- **Aldric death timer**: 40 turns seems short if player is exploring thoroughly. May need adjustment or clearer warnings.

### Potentially Boring Sections
- Repeated bucket fill/pour for puzzle (5 identical fill/pour cycles)
- Walking back and forth between locations without events

### Potentially Frustrating Sections
- Getting locked out of Myconid equipment due to earlier violence
- Puzzle reset on wrong sequence when already infected
- Entering Deep Roots unprepared and dying to suffocation
