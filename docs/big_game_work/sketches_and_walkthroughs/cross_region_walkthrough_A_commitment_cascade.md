# Cross-Region Walkthrough A: The Commitment Cascade

## Purpose

This walkthrough tests an **overcommitted player** - someone who makes promises faster than they can keep them. The goal is to stress-test:

1. Commitment timer interactions and overlaps
2. The confession vs. discovery mechanic
3. Echo trust dynamics under failure conditions
4. "Hope extends survival" edge cases
5. Partial credit for genuine attempts

## Player Archetype

A well-intentioned but overcommitted player who:
- Wants to help everyone they meet
- Makes promises impulsively when NPCs are suffering
- Discovers they cannot fulfill all commitments
- Must decide who to save and who to abandon

## Notation

- `[MECHANISM: X]` - Requires engine/behavior support
- `[DESIGN INPUT: X]` - Decision made during simulation
- `[QUESTION: X]` - Ambiguity needing resolution
- `[OBSERVATION: X]` - Gameplay quality note
- `[TIMER: NPC X turns remaining]` - Commitment timer status

## Initial State

- Player starts in Nexus Chamber
- No commitments active
- Echo trust: 0
- Turn counter: 0
- No companions

---

## PHASE 1: Fungal Depths - First Commitments (Turns 1-15)

### Entering and Meeting Aldric

```
=== Turn 1 ===
[Location: Nexus Chamber]
[Commitments: none]
[Echo trust: 0]

> go west

You descend into the Cavern Entrance. A frail scholar sits by a small fire,
visibly ill with fungal patches on his skin.

Scholar Aldric is here.
```

```
=== Turn 2 ===
> talk to aldric

Aldric looks up with tired eyes. "A visitor... I didn't think anyone would
come. The infection is spreading. I need silvermoss from the Grotto below,
but I can barely stand."
```

```
=== Turn 3 ===
> "I'll help you. I'll find the silvermoss."

Aldric's eyes fill with hope. "You would do that? Thank you... thank you.
The silvermoss grows near the pool in the Luminous Grotto. Please hurry."

[COMMITMENT MADE: Aldric - find silvermoss]
[TIMER: Aldric - 60 turns remaining (50 base + 10 hope bonus)]
[Flag: committed_to_aldric = true]
```
[MECHANISM: Commitment trigger phrases recognized, timer starts with hope bonus]
[OBSERVATION: Hope bonus applied immediately upon commitment - Aldric's survival extended]

### Exploring the Grotto

```
=== Turn 4 ===
> go down

You descend into the Luminous Grotto. Bioluminescent mushrooms glow softly.
A crystal-clear pool dominates the center. Strange symbols are carved into
the high ceiling, but the light is too dim to read them.

You see silvermoss growing near the pool.
You see a bucket here.
You see mushrooms of various colors: blue, gold, violet, black.
```

```
=== Turn 5 ===
> take silvermoss

You carefully harvest a clump of silvermoss. It glows faintly with a soft
blue light.

[Inventory: silvermoss]
```
[OBSERVATION: Player has the item to fulfill commitment. Will they deliver it?]

### Meeting the Myconids

```
=== Turn 6 ===
> go east

You enter the Myconid Sanctuary. Tall mushroom beings stand in orderly rings,
communicating through puffs of colored spores. The air is remarkably clean.

The Myconid Elder regards you with eyeless attention.
```

```
=== Turn 7 ===
> talk to myconid elder

A cloud of blue spores. Somehow, you understand: "Soft-flesh comes to the
Still Place. We sense your purpose. The Mother-of-Spores suffers. Will you
help her?"
```

```
=== Turn 8 ===
> "I'll help her. I'll find what she needs."

The Elder's spores shift to warm gold. "The heartmoss grows in the Deep Roots,
where air is poison. We cannot go there. You promise this?"

[COMMITMENT MADE: Spore Mother - find heartmoss]
[TIMER: Spore Mother - 200 turns remaining (no hope bonus - too powerful)]
[Flag: committed_to_spore_mother = true]
```
[OBSERVATION: Player now has TWO commitments but hasn't fulfilled the first one]
[DESIGN INPUT: Making a second commitment before fulfilling the first is allowed but tracked]

### Decision Point: Deliver Silvermoss or Continue?

**BRANCH POINT: Does player deliver silvermoss to Aldric now?**

---

## BRANCH A: Player Does NOT Deliver Silvermoss Yet

The overcommitted player decides to explore more first.

```
=== Turn 9 ===
[Commitments: Aldric (57 turns), Spore Mother (199 turns)]

> go west, go down

You return to the Luminous Grotto, then descend toward the Spore Heart.

The air grows thick with golden spores. At the center, the Spore Mother
rests - a massive fungal creature, her cap pulsing weakly. She seems to
be in pain. Sporelings cluster around her protectively.

[Infection: +10 severity (now at 10)]
```

```
=== Turn 10 ===
> look at spore mother

The Spore Mother is enormous. Dark veins of blight spread across her surface.
Through the spore haze, you sense... desperation. Pain. A wordless plea.

The sporelings watch you warily but do not attack.

[Infection: +10 severity (now at 20)]
```
[MECHANISM: Staying 3 turns without attacking transitions Spore Mother to "wary"]
[OBSERVATION: Environmental pressure (infection) creates urgency to leave]

```
=== Turn 11 ===
> go up, go up, go east

You flee the spores, returning to the Cavern Entrance.

Aldric looks at you hopefully. "Did you find it? The silvermoss?"

[Infection: severity 20, progression rate 5/turn outside spore areas]
```
[QUESTION: Does infection progress outside spore areas? Current design says yes at rate 5]

```
=== Turn 12 ===
> "I found it, but I need to explore more first."

Aldric's face falls slightly. "I... understand. But please, don't take too
long. I can feel the infection spreading."

[Aldric trust: -0 (no penalty for delay, only for abandonment)]
[TIMER: Aldric - 54 turns remaining]
```
[DESIGN INPUT: Delaying fulfillment doesn't damage trust, only abandonment does]
[OBSERVATION: Player is accumulating commitments without fulfilling any]

### Leaving Fungal Depths

```
=== Turn 13 ===
> go east

You return to the Nexus Chamber. The damaged waystone pulses faintly.
A spectral figure flickers at the edge of your vision.

The Echo whispers: "Two promises made. Neither kept. The meridian watches."

[Echo appearance: brief, neutral tone]
```
[MECHANISM: Echo comments on commitment status when player returns to Nexus]
[OBSERVATION: Echo provides moral mirror without judgment - just stating facts]

```
=== Turn 14-15 ===
> [Player rests, infection treated at Nexus if possible, or progresses]

[End of Phase 1]
[Commitments active: Aldric (51 turns), Spore Mother (197 turns)]
[Inventory: silvermoss (unfulfilled)]
[Infection: severity 30 (if untreated)]
```

---

## PHASE 2: Beast Wilds - Adding More Commitments (Turns 16-35)

### Entering Beast Wilds

```
=== Turn 16 ===
[Location: Nexus Chamber]
[Commitments: Aldric (50 turns), Spore Mother (196 turns)]

> go south

You enter the Forest Edge. Territorial markings are visible on tree bark.
The silence feels watchful.

You see venison here.
You see a hunter's journal here.
```

```
=== Turn 17 ===
> go south

You enter the Southern Trail. A weathered hunter lies against a tree,
clutching her leg. Blood seeps through makeshift bandages.

Hunter Sira is here. She is injured.
```

```
=== Turn 18 ===
> talk to sira

Sira winces. "Wolves... got my partner. I barely escaped. My leg..."
She gestures weakly. "I can't walk far. Need a healer."
```

```
=== Turn 19 ===
> "I'll get help. I'll find a healer for you."

Sira's eyes show desperate hope. "There's a healer in the town to the south.
Elara. Tell her Sira sent you. Please... hurry."

[COMMITMENT MADE: Sira - get her to a healer]
[TIMER: Sira - 12 turns remaining (8 base + 4 hope bonus)]
[Flag: committed_to_sira = true]
```
[OBSERVATION: Sira's timer is SHORT. Player now has urgent commitment]
[DESIGN INPUT: Hope bonus of 4 turns applied - determination slows blood loss]

### Finding the Bear Cubs

```
=== Turn 20 ===
[Commitments: Aldric (46 turns), Spore Mother (192 turns), Sira (11 turns)]

> go north, go south (to Predator's Den)

You enter the Predator's Den. A massive Dire Bear guards two small cubs.
The cubs are visibly ill, their fur patchy and breath labored.

The Dire Bear growls a warning but does not attack.
```

```
=== Turn 21 ===
> look at cubs

The bear cubs are clearly sick - some kind of wasting illness. They barely
move, their breathing shallow. The mother bear watches you with desperate,
intelligent eyes.
```

```
=== Turn 22 ===
> "I'll find medicine for your cubs. I promise."

The bear studies you with intelligent eyes. A low rumble - not hostile,
but... questioning. Then she calms slightly, as if understanding your intent.

[COMMITMENT MADE: Bear cubs - find medicine]
[TIMER: Bear cubs - 35 turns remaining (30 base + 5 hope bonus)]
[Flag: committed_to_bear_cubs = true]
```
[OBSERVATION: Player now has FOUR active commitments]
[OBSERVATION: Sira timer is critical - only 10 turns left]

### The Commitment Cascade Begins

```
=== Turn 23-24 ===
[Commitments: Aldric (44), Spore Mother (190), Sira (9), Cubs (33)]

> go north, go north (return to Forest Edge)
> go south (to Civilized Remnants via southern_trail -> town_gate)

[Travel: 2 turns]

You approach the Town Gate. Guards eye you suspiciously.

"State your business, traveler."
```

```
=== Turn 25 ===
[TIMER: Sira - 7 turns remaining]

> "I need to find Healer Elara. A hunter named Sira is injured."

The guard's expression softens. "Sira? She's one of ours. Elara's shop
is in the Market Square. Hurry."

You enter the Civilized Remnants.
```

```
=== Turn 26 ===
> go to market square, find elara

You find Healer Elara's shop. She looks up from her work.

"Can I help you?"
```

```
=== Turn 27 ===
> "Sira is injured in the Beast Wilds. She needs help."

Elara's face shows concern. "Sira? Where exactly? I can prepare supplies,
but I can't leave the town - too many patients here."

[MECHANISM: Elara cannot leave - provides supplies but player must transport]
```
[QUESTION: Can Elara provide bandages/medicine for player to bring back?]
[DESIGN INPUT: Yes - Elara gives healing supplies if trust >= 1]

```
=== Turn 28 ===
> "Can you give me supplies to help her?"

"You'll need bandages and a splint for her leg. Here." She hands you a
medical kit. "Stop the bleeding first, then splint. And tell her to come
see me when she can walk."

[Inventory: silvermoss, medical_kit]
[Elara trust: +1 (helping her friend)]
```

```
=== Turn 29-31 ===
[Travel back: 3 turns (town -> southern_trail)]
[TIMER: Sira - 3 turns remaining]

You return to where Sira was lying. She is still here, but her face is
pale as chalk. Her breathing comes in gasps.

"You... came back..."
```
[OBSERVATION: Barely made it. Timer was at 3 when arriving]

```
=== Turn 32 ===
> use medical kit on sira

You apply pressure to stop the bleeding, then carefully splint her leg.
Color slowly returns to her face.

"Thank you... I thought I was going to die here."

[COMMITMENT FULFILLED: Sira - saved]
[Sira state: injured -> recovering]
[Sira trust: +2 (base) +2 (commitment bonus) = +4 total]
```
[MECHANISM: Commitment fulfillment bonus applies]
[OBSERVATION: First commitment fulfilled - but three remain]

```
=== Turn 33 ===
The Echo's voice whispers in your mind: "A word kept. The threads strengthen."

[Echo trust: +0.5 (commitment fulfilled)]
```
[MECHANISM: Echo comments on fulfilled commitments even outside Nexus]

```
=== Turn 34-35 ===
> "Sira, I need to help some bear cubs. They're sick."

"Bear cubs? There's a wasting sickness going around. Elara has herbs that
can cure it - from the Healer's Garden. But you'll need permission to
enter. Build trust with her first."

[Flag: knows_herb_location = true]
[End Phase 2]
```

**Status at End of Phase 2:**
- Commitments: Aldric (35 turns), Spore Mother (180 turns), Cubs (21 turns)
- Fulfilled: Sira
- Echo trust: 0.5
- Inventory: silvermoss

---

## PHASE 3: The Critical Decision (Turns 36-50)

### Racing Against Time

```
=== Turn 36 ===
[Commitments: Aldric (34), Spore Mother (179), Cubs (20)]

Player must decide:
- Return to Aldric with silvermoss (Fungal Depths) - ~5 turns round trip
- Get herbs for cubs (Civilized Remnants) - ~2 turns
- Then deliver herbs to cubs (Beast Wilds) - ~3 turns

Total time for cubs: ~5 turns
Total time for Aldric: ~5 turns
Cubs timer: 20 turns - SAFE
Aldric timer: 34 turns - SAFE

Both are achievable! But player doesn't know this for certain.
```
[OBSERVATION: At this point, both commitments are still achievable]
[OBSERVATION: The CASCADE hasn't actually forced failure yet]

### Getting Herbs for Cubs

```
=== Turn 36-37 ===
> go south (to town), go to healer's garden

Elara looks up. "Back again? You saved Sira - I owe you. What do you need?"
```

```
=== Turn 38 ===
> "I need herbs to cure some sick bear cubs."

Elara raises an eyebrow. "Bear cubs? That's... unusual compassion for beasts.
The garden has what you need. Here." She hands you healing herbs.

[Inventory: silvermoss, healing_herbs]
[Elara trust: +1 (impressed by compassion)]
```

```
=== Turn 39-41 ===
> [Travel to Predator's Den - 3 turns]

You return to the Predator's Den. The bear cubs are weaker than before,
but still alive. The mother bear watches anxiously.

[TIMER: Cubs - 15 turns remaining]
```

```
=== Turn 42 ===
> give healing herbs to cubs

You carefully administer the herbs to both cubs. Slowly, their breathing
steadies. The sicker one opens its eyes.

The mother bear approaches you. Not threatening - grateful. She bows her
massive head.

[COMMITMENT FULFILLED: Bear cubs - saved]
[Dire Bear state: hostile -> grateful]
[Dire Bear gratitude: +2 (base) +2 (commitment bonus) = +4]
```
[OBSERVATION: Second commitment fulfilled. Two down, two to go]

```
=== Turn 43 ===
Echo whispers: "Another word kept. The fractures heal."

[Echo trust: +0.5 (now at 1.0)]
```

### Now for Aldric

```
=== Turn 44-48 ===
[TIMER: Aldric - 22 turns remaining]
[Travel to Fungal Depths - 5 turns]

You return to the Cavern Entrance. Aldric is weaker, but alive.

"You're back... did you bring it?"
```

```
=== Turn 49 ===
> give silvermoss to aldric

Aldric takes the silvermoss with trembling hands. He applies it to his
worst wounds. After a moment, his breathing eases.

"Thank you... I thought you'd forgotten. The infection is stabilizing.
I'm not cured, but I'll survive now."

[COMMITMENT FULFILLED: Aldric - stabilized]
[Aldric state: critical -> stabilized]
[Aldric trust: +2 (base) +2 (commitment bonus) = +4]
```

```
=== Turn 50 ===
Echo: "Three words kept. You carry heavy burdens well."

[Echo trust: +0.5 (now at 1.5)]

[End Phase 3]
```

**Status at End of Phase 3:**
- Commitments remaining: Spore Mother (165 turns)
- Fulfilled: Sira, Cubs, Aldric
- Echo trust: 1.5
- Player has NOT experienced the cascade failure yet

---

## BRANCH POINT B: What If Player Added Sunken District?

Let's rewind and explore what happens if the player goes to Sunken District during Phase 2 instead of going directly to help Sira.

### BRANCH B: Sunken District Detour (Alternative Timeline)

```
=== Turn 23 (Branch B) ===
[Commitments: Aldric (44), Spore Mother (190), Sira (9), Cubs (33)]

Instead of going to help Sira, player explores east:

> go north, go north, go east (to Nexus), go east (to Sunken District)

You enter the Flooded Plaza. Water laps at your ankles. The smell of brine
fills the air.

[Travel: 3 turns]
[TIMER: Sira - 6 turns remaining]
```

```
=== Turn 26 (Branch B) ===
> go to survivor camp

You reach the Survivor Camp on higher ground. Camp Leader Mira approaches.

"A visitor? We need help. Two people are missing - Garrett in the caves,
Delvan in his warehouse."
```

```
=== Turn 27 (Branch B) ===
[TIMER: Sira - 5 turns remaining]

> "I'll find them both."

Mira's eyes fill with hope. "Thank you! Garrett went east, toward the
underwater caves. Delvan is in the Merchant Quarter, south."

[COMMITMENT MADE: Garrett - rescue from drowning]
[COMMITMENT MADE: Delvan - free from warehouse]
```
[OBSERVATION: Player now has SIX commitments]
[OBSERVATION: Sira will die before player can return - 5 turns, needs 6+ to reach her]

### The First Abandonment

```
=== Turn 28-31 (Branch B) ===
[Player explores Sunken District, learns swimming from Jek]
[TIMER: Sira reaches 0]

---SYSTEM MESSAGE---
Somewhere in the Beast Wilds, Hunter Sira's eyes close for the last time.
She waited as long as she could.

[COMMITMENT ABANDONED: Sira - died]
[Flag: sira_dead = true]
[Flag: broke_promise_sira = true]
---

[Echo trust: -1 (abandonment)]
[Echo trust now: -0.5]
```
[MECHANISM: Timer expiration triggers abandonment automatically]
[OBSERVATION: Player might not even know Sira died - no immediate notification if not in region]

### Echo Confrontation

```
=== Turn 32 (Branch B) ===
[If player returns to Nexus]

The Echo manifests, form dim and sorrowful.

"A word was broken. She waited in pain, believing help would come.
The bleeding claimed her."

[Echo appearance: guaranteed after abandonment]
```
[MECHANISM: Echo always appears after commitment abandonment]
[DESIGN INPUT: Echo doesn't moralize - states facts with sorrow]

### Gossip Begins Spreading

```
[Turn 32 + 12 = Turn 44: Sira's death reaches Elara]

---SYSTEM: GOSSIP TRIGGER---
News of the injured hunter's death has spread to Civilized Remnants.
Healer Elara has learned that someone was with Sira before she died.
---
```
[MECHANISM: Gossip timer tracks from death event]

### Elara Discovery (Later)

```
=== Turn 50+ (Branch B) ===
[If player visits Elara after gossip arrives]

Elara's face is cold. "I heard about Sira. She died in the forest.
They say someone found her, promised to get help, then... never came back."

She looks at you. "Was that you?"

[DIALOGUE CHOICE]:
A) "Yes. I'm sorry. I couldn't reach help in time."
B) [Say nothing]
C) "No, that wasn't me." [LIE]
```

```
> A (Confess)

Elara's expression shifts - still grief, but with grudging respect.

"At least you're honest. Sira deserved better, but... I appreciate you
telling me. Don't make promises you can't keep."

[Confession mechanic: -2 trust with Elara]
[Trust recoverable over time]
```
[OBSERVATION: Confession path preserves recovery option]

```
> C (Lie)

"I see." Elara's voice is flat. "Then I must have heard wrong."

[Later, if lie is discovered - trust -4, permanent consequences]
```
[MECHANISM: Lie + discovery = worst outcome]

---

## BRANCH POINT C: Dual Rescue in Sunken District

Continuing from Branch B, let's test the tightest timer overlap.

```
=== Turn 33 (Branch B) ===
[Commitments: Aldric (33), Spore Mother (183), Cubs (25), Garrett (?), Delvan (?)]
[Sira: DEAD]

Player has learned swimming. Now attempts dual rescue.

> go east, east (to Sea Caves via Tidal Passage)

You swim through the underwater passage, fish nipping at you.
[Fish damage: 8 HP, bleeding condition]

You emerge in the Sea Caves. A man clings to debris, water rising around him.

Sailor Garrett is here. He is drowning.

[TIMER: Garrett - 5 turns (starts NOW, on room entry)]
```
[MECHANISM: Garrett's timer starts on room entry, not first encounter]

```
=== Turn 34 ===
> "Hold on! I'll get you out!"

Garrett's eyes show desperate hope. His head barely breaks the surface.

[COMMITMENT MADE: Garrett - rescue (if not already committed)]
[TIMER: Garrett - 4 turns]
[No hope bonus - drowning doesn't care about promises]
```

```
=== Turn 35 ===
> give air bladder to garrett

You toss the air bladder to Garrett. He catches it, takes desperate breaths.
His panic subsides slightly.

[Garrett state: drowning -> stabilized]
[Garrett still needs help getting out]
```

```
=== Turn 36-37 ===
> help garrett swim out

You support Garrett through the passage back to the Flooded Chambers.
Both of you are exhausted.

[COMMITMENT FULFILLED: Garrett - rescued]
[Garrett gratitude: +4 (base) +2 (commitment bonus) = +6]
```

```
=== Turn 38 ===
[TIMER: Delvan - started at Turn 26 when first heard about him]
[Delvan timer: 10 base + 3 hope = 13 turns from first encounter]
[Current: Turn 38 - Turn 26 = 12 turns elapsed]
[Delvan timer: 1 turn remaining!]

> go south, south (to Merchant Warehouse)

You navigate through flooded streets to the warehouse. Tapping comes from
the second floor.

[Travel: 2 turns]

---SYSTEM MESSAGE---
Merchant Delvan's eyes close. The bleeding has stopped, along with everything else.

[COMMITMENT ABANDONED: Delvan - died]
[Flag: delvan_dead = true]
[Flag: broke_promise_delvan = true]
---
```
[OBSERVATION: Dual rescue FAILED - saved Garrett, lost Delvan]
[OBSERVATION: This is the designed difficulty - first playthrough saves one]

### Partial Credit Assessment

```
=== System: Partial Credit Evaluation ===

Checking partial credit for Delvan abandonment:
- [x] Player visited Sunken District
- [x] Player was actively working toward rescue (saved Garrett)
- [x] Failure was due to time constraint, not neglect
- [x] Another commitment (Garrett) was fulfilled during same period

PARTIAL CREDIT APPLIES

[Echo trust penalty: -0.5 instead of -1]
[Echo commentary modified]
```

```
=== Turn 39 ===
[If player returns to Nexus]

The Echo appears, form wavering with conflicting emotions.

"You saved one from the water. The other... you could not reach in time.
You tried to carry more than one person could bear. Some burdens must be
set down."

[Echo trust: -0.5 (partial credit)]
[Current Echo trust: -0.5 (was 0)]
```
[MECHANISM: Partial credit softens Echo's response]
[OBSERVATION: Echo acknowledges the attempt - not purely punitive]

---

## PHASE 4: Consequence Cascade (Turns 50-80)

### Returning to Beast Wilds

```
=== Turn 55 ===
[Player returns to Beast Wilds to check on cubs]
[Cubs timer was 35 turns from Turn 22 = Turn 57 deadline]
[Current: Turn 55 - still alive]

You return to the Predator's Den. The cubs are weaker but still breathing.
The mother bear looks at you with desperate hope.

> give healing herbs to cubs

[COMMITMENT FULFILLED: Cubs - saved]
```

### The Sira Revelation

```
=== Turn 60 ===
[12 turns after Sira's death - gossip reaches Elara]

Player visits Civilized Remnants for other business.

Elara's eyes are red. "Did you hear? Sira died. In the forest. They say
someone promised to help her..."

[CONFESSION WINDOW OPEN: Player can confess now before discovery]
```

```
=== Turn 61 ===
> "That was me. I promised to help her, but I went to the Sunken District
   instead. I saved a drowning man there, but... Sira died waiting for me."

Elara is silent for a long moment.

"You saved someone else instead. That's... something. But Sira trusted you.
I trusted her. This is hard to forgive."

[Confession: -2 trust with Elara]
[Relationship damaged but not destroyed]
[Advanced herbalism still possible with effort]
```
[OBSERVATION: Confessing with explanation of saving someone else softens the blow]
[DESIGN INPUT: Explaining context (saved Garrett) could reduce penalty further?]

### Echo Trust Status Check

```
=== Turn 65 ===
[Player visits Nexus to check in with Echo]

> ask echo about my promises

The Echo materializes, form more solid than before.

"You have made promises. Let me remember them for you."

"To Scholar Aldric, silvermoss. [FULFILLED]"
"To the Spore Mother, heartmoss. [PENDING - 150 turns remain]"
"To Hunter Sira, a healer. [ABANDONED - she died]"
"To the mother bear, medicine. [FULFILLED]"
"To Sailor Garrett, rescue. [FULFILLED]"
"To Merchant Delvan, freedom. [ABANDONED - he died]"

"Four words kept. Two words broken. You carry both light and shadow."

[Echo trust: currently at -0.5]
[Breakdown: +0.5 (Sira) +0.5 (Cubs) +0.5 (Aldric) +0.5 (Garrett) -1 (Sira) -0.5 (Delvan partial) = +0.5]
```
[OBSERVATION: Wait - the math shows +0.5, not -0.5. Let me recalculate.]
[CORRECTION: Fulfilled gives +0.5 each, abandonment gives -1 (or -0.5 partial)]
[Total: +2.0 (four fulfilled) -1.0 (Sira) -0.5 (Delvan partial) = +0.5]
[DESIGN INPUT: Multiple fulfilled commitments can outweigh some failures]

---

## Summary Tables

### Design Inputs Generated

| ID | Input | Value | Notes |
|----|-------|-------|-------|
| DI-A1 | Hope bonus applies at commitment | Immediate | Timer extended when promise made |
| DI-A2 | Delaying fulfillment doesn't damage trust | No penalty | Only abandonment penalizes |
| DI-A3 | Echo comments outside Nexus on fulfillment | Brief whisper | Positive reinforcement |
| DI-A4 | Partial credit requires evidence | 3+ factors | Region visited, attempting, time constraint |
| DI-A5 | Confession with context reduces penalty | -2 not -3 | Explaining saved someone else helps |
| DI-A6 | Multiple fulfillments outweigh some failures | Yes | Net trust can be positive |
| DI-A7 | Garrett timer starts on room entry | Not first mention | More punishing than other NPCs |

### Questions Raised

| ID | Question | Proposed Resolution |
|----|----------|---------------------|
| Q-A1 | Does infection progress outside spore areas? | Yes, at reduced rate (5/turn) |
| Q-A2 | Can Elara provide supplies without full trust? | Yes, trust 1 sufficient |
| Q-A3 | Should explaining context reduce confession penalty? | Yes, from -2 to -1.5 if saved someone else |
| Q-A4 | What notification when NPC dies offscreen? | None immediate - discovered on return or via gossip |
| Q-A5 | Can player have negative Echo trust but still be net positive? | Math shows this is possible with partial credit |

### Mechanisms Required

| Mechanism | Status | Notes |
|-----------|--------|-------|
| Commitment trigger phrase recognition | Needed | Parser must detect promise language |
| Timer management with hope bonus | Needed | Applied at commitment, not at death |
| Partial credit evaluation | Needed | Multi-factor check on abandonment |
| Gossip timer from events | Defined | Specific turn counts in game_wide_rules.md |
| Echo appearance on abandonment | Needed | Guaranteed appearance, sorrowful tone |
| Confession detection in dialog | Needed | Parser recognizes admission of broken promise |

### Gameplay Observations

**Positive:**
- The commitment system creates genuine tension - player must make hard choices
- Partial credit feels fair - acknowledges genuine attempts
- Echo as moral mirror works without being preachy
- Multiple fulfillments can recover from some failures
- Confession mechanic rewards honesty

**Concerns:**
- Player might not realize NPC died until much later (no notification)
- Sunken District dual rescue might feel unfair - designed to fail first time
- Timer math requires player to track multiple countdowns
- Overcommitment is easy - should there be a warning?

**Interesting Patterns:**
- The "cascade" actually didn't force failure until player added Sunken District
- Fungal Depths + Beast Wilds timers are achievable together
- The true cascade requires 6+ commitments with overlapping urgent timers
- Sira's 8-turn timer is the "trap" that catches overcommitters

---

## Key Findings

1. **Timer overlap design is intentional** - Most commitments don't conflict, but Sira + Sunken District is a designed trap for the overcommitted

2. **Partial credit is essential** - Without it, the system would feel punitive. With it, genuine attempts are acknowledged

3. **Echo trust math works** - Multiple fulfillments can outweigh failures, creating recovery path

4. **Confession window is tight but fair** - 20 turns for Sira-Elara gossip gives reasonable opportunity

5. **No offscreen death notification** - This is actually good design - creates discovery moments

6. **Hope bonus timing** - Applying at commitment (not discovery) rewards making promises to dying NPCs

---

## Sketch Update Recommendations

### beast_wilds_sketch.json
- Clarify Sira's timer is the tightest non-Sunken commitment (8 turns base)
- Add note: "Sira commitment is designed to conflict with Sunken District exploration"

### game_wide_rules.md
- Add: "Confession with context (saved someone else) may reduce penalty from -2 to -1.5"
- Clarify: "No notification when NPC dies offscreen - player discovers via return or gossip"

### cross_region_dependencies.md
- No changes needed - gossip timing worked as designed

---

*Walkthrough completed. Ready for Walkthrough B (Companion Journey).*
