# Cross-Region Walkthrough B: The Companion Journey

## Purpose

This walkthrough tests **companion restrictions, boundary behavior, and multi-companion management** across all regions. The goal is to stress-test:

1. Companion waiting and reuniting mechanics at region boundaries
2. Multi-companion interactions (wolf+Sira reconciliation, wolf+salamander coexistence)
3. Companion comfort levels in different environments
4. What happens when player tries to bring wrong companion to wrong place
5. Companion benefits and costs in different situations

## Player Archetype

A companion-focused player who:
- Prioritizes befriending and recruiting all possible companions
- Wants to travel with multiple companions simultaneously
- Tests boundaries by trying to bring companions everywhere
- Values companion utility in different situations

## Notation

- `[MECHANISM: X]` - Requires engine/behavior support
- `[DESIGN INPUT: X]` - Decision made during simulation
- `[QUESTION: X]` - Ambiguity needing resolution
- `[OBSERVATION: X]` - Gameplay quality note
- `[COMPANION: X at Y]` - Companion status and location

## Initial State

- Player starts in Nexus Chamber
- No companions yet
- Turn counter: 0

## Companion Reference Summary

| Companion | Acquired In | Can Enter | Cannot Enter | Comfort Issues |
|-----------|-------------|-----------|--------------|----------------|
| Wolf Pack | Beast Wilds | Fungal (partial), Frozen (partial), Sunken (partial) | Nexus (wards), Deep Roots (toxic), Observatory (extreme cold), Spider Gallery (instinct) | Humid areas |
| Salamander | Frozen Reaches | All except Sunken | Sunken District (extinguishes) | Humid/wet areas |
| Sira | Beast Wilds | All | None | Wolf companion (prejudice) |
| Aldric | Fungal Depths | All | None (too weak for many) | Combat, water, extreme cold |

---

## PHASE 1: Acquiring the Wolf Pack (Turns 1-25)

### Entering Beast Wilds

```
=== Turn 1 ===
[Location: Nexus Chamber]
[Companions: none]

> go south

You enter the Forest Edge. The forest stretches before you, ancient trees
rising like pillars. Territorial markings are visible on the bark.

Exits: north (Nexus), south (Southern Trail), southeast (Wolf Clearing)
```

### Building Wolf Trust

```
=== Turn 2-5 ===
> go southeast (to Wolf Clearing)

You enter the Wolf Clearing. A massive grey wolf watches you from the shadows.
Other wolves are visible behind it. Their eyes track your movements.

Alpha Wolf is here. It radiates authority and caution.

> drop venison (if brought from Forest Edge)

The alpha's ears perk. It approaches the offering, sniffs, then accepts.
The pack's posture relaxes slightly.

[Wolf trust: +1 (offering accepted)]
```

```
=== Turn 6-10 ===
[Building trust through non-threatening presence, offerings]

[Wolf trust: 0 -> 1 -> 2 -> 3]

At trust 3:
The alpha approaches you directly. It makes eye contact - not a challenge,
but acknowledgment. A younger wolf breaks from the pack and sits beside you.

"The pack accepts you. We will hunt with you, if you wish."

[COMPANION ACQUIRED: Wolf Pack (3 wolves)]
[COMPANION: Wolves at Wolf Clearing]
```
[MECHANISM: Companion acquisition at trust threshold]
[OBSERVATION: Wolf trust building takes time but isn't urgent - good pacing]

### Testing Wolf Boundaries in Beast Wilds

```
=== Turn 11 ===
[Companions: Wolf Pack (following)]

> go northwest (toward Spider Gallery)

The wolves follow you through the forest... but as you approach the Gallery
Approach, they slow. The alpha growls uneasily.

> continue to Spider Gallery

The alpha plants its feet and refuses to advance. The other wolves cluster
behind it. Something ancient in their instincts won't let them enter.

[COMPANION: Wolves waiting at Gallery Approach]

You enter the Spider Gallery alone. The wolves whine from behind you.
```
[MECHANISM: Companion refuses to enter certain areas based on instinct/fear]
[DESIGN INPUT: Wolves won't enter spider territory (territorial instinct, not cowardice)]

```
=== Turn 12-13 ===
[In Spider Gallery alone]

> [Player explores, perhaps gets in trouble with spiders]

=== Turn 14 ===
> flee west (back to Gallery Approach)

You burst out of the Spider Gallery. The wolves are immediately beside you,
checking you for injuries, growling toward the gallery entrance.

[COMPANION: Wolves rejoined automatically]
```
[MECHANISM: Companions rejoin when player returns to waiting location]
[OBSERVATION: Good - seamless reunification]

### Testing Wolf-Sira Conflict

```
=== Turn 15 ===
[Companions: Wolf Pack]

> go west, south (to Southern Trail where Sira is)

You approach the Southern Trail. Hunter Sira lies against a tree, injured.

Sira sees you approach with the wolves. Her hand goes to her weapon.
"Get those things away from me."

The wolves tense, sensing her hostility.

[CONFLICT: Wolf Pack vs Sira]
```
[MECHANISM: Multi-companion conflict detection]

```
=== Turn 16 ===
> "They won't hurt you. Let me help."

Sira's eyes don't leave the wolves. "Wolves killed Tam. My partner.
I don't care if these are 'tame' - I can't trust them."

[DIALOGUE CHOICE]:
A) "Wait here" (leave wolves, help Sira alone)
B) "They're different" (attempt reconciliation - requires trust levels)
C) "Then I'll leave" (abandon Sira)
```

```
> A) "Wait here"

You gesture to the wolves. The alpha understands - it leads the pack
back toward the clearing.

[COMPANION: Wolves waiting at Wolf Clearing]

Sira relaxes visibly. "Thank you. Now... can you help me?"
```
[MECHANISM: Player can temporarily dismiss companions]
[DESIGN INPUT: Dismissal gesture understood by wolves - they return to "home base"]

### Saving Sira (Abbreviated)

```
=== Turn 17-22 ===
[Wolves at Wolf Clearing, player with Sira]

> [Player gets medical supplies from Civilized Remnants, returns]
> use medical kit on sira

Sira's color returns. "Thank you. I thought I was dead."

[Sira trust: +4 (saved her life)]
[COMPANION ACQUIRED: Sira (optional - she offers to join)]
```

```
=== Turn 23 ===
> "Will you travel with me?"

Sira considers. "You saved my life. Yes, I'll come. But..." she glances
toward the forest where the wolves disappeared. "Those things stay away
from me. That's the condition."

[COMPANION: Sira (following)]
[CONFLICT: Sira refuses to travel with wolves - reconciliation required]
```

### Reconciliation Attempt

```
=== Turn 24 ===
[Requirements for reconciliation: Sira trust 2+, Wolf trust 3+, player initiates]
[Current: Sira trust 4, Wolf trust 3 - requirements met]

> go to Wolf Clearing (with Sira)

The wolves are here. Sira freezes. Her hand goes to her weapon again.
The alpha watches, neither advancing nor retreating.

> "Sira, look at them. They're not attacking. They've chosen to trust me."

Sira's jaw tightens. "Trust? They're killers."

The alpha steps forward. Not aggressive - offering itself to examination.
Its pack stays back.

> "The wolves that killed Tam aren't these wolves. Look at them."

Long pause. Sira watches the alpha. It sits, making itself smaller.

"Fine. I'll... try. But if they turn on us, I'm killing them myself."

[RECONCILIATION ACHIEVED]
[Sira prejudice flag: removed]
[Wolf+Sira: can now travel together]
```
[MECHANISM: Reconciliation dialog requires meeting trust thresholds]
[OBSERVATION: This is a meaningful character moment - earns the multi-companion setup]

```
=== Turn 25 ===
[Companions: Wolf Pack + Sira (reconciled)]

You now travel with both the wolf pack and Hunter Sira. The wolves keep
a respectful distance from Sira, and she keeps her hand near her weapon,
but they move together.

[End Phase 1]
```

---

## PHASE 2: Testing Boundaries with Wolf+Sira (Turns 26-50)

### Nexus Boundary

```
=== Turn 26 ===
[Companions: Wolf Pack + Sira]
[Location: Forest Edge]

> go north (to Nexus)

You approach the Nexus Chamber. Sira follows without issue.

The wolves try to follow... but at the threshold, they stop. The alpha
whines, pressing against an invisible barrier. Magical wards push them back.

[COMPANION: Wolves cannot enter Nexus]
[COMPANION: Wolves waiting at Forest Edge]
[COMPANION: Sira enters Nexus normally]

You enter the Nexus Chamber with Sira. The wolves pace at the boundary.
```
[MECHANISM: Nexus wards repel wolf pack specifically]
[OBSERVATION: Sira can enter but wolves cannot - creates interesting tactical decisions]

```
=== Turn 27 ===
[In Nexus, Sira present, wolves outside]

The Echo manifests. It regards Sira with curiosity.

"You bring a companion. The hunter from the wilds. She carries... loss."

Sira stiffens. "What is that thing?"

"I am The Echo. A remnant. I remember what was, and watch what is."

[Sira flag: has_seen_echo = true]
```
[MECHANISM: NPCs react to Echo appearance]

### Fungal Depths with Wolf+Sira

```
=== Turn 28 ===
> go west (to Fungal Depths, retrieving wolves first)

[Player exits Nexus at Forest Edge, wolves rejoin]
[Travel to Fungal Depths via Nexus]

You descend into the Cavern Entrance. The wolves sniff the air uneasily -
something about the spore scent puts them on edge.

Sira wrinkles her nose. "Fungi. I hate fungi."

Scholar Aldric looks up weakly. His eyes widen at the wolf pack.
"You... travel with wolves? Remarkable."

[All companions enter Fungal Depths successfully]
```

```
=== Turn 29 ===
> go down (to Luminous Grotto)

The wolves follow but are clearly uncomfortable. The humid air and strange
smells disturb them. They stick close to you.

Sira examines the bioluminescent mushrooms. "These could be useful. My tracking
skills work here - I can see safe paths through the spore-heavy areas."

[Sira bonus: tracking reduces spore exposure by 2]
[Wolf pack: uncomfortable but functional]
```
[MECHANISM: Companion provides region-specific benefit]

```
=== Turn 30 ===
> go down (toward Spore Heart)

The spore concentration increases. You feel the infection starting.

The wolves STOP. The alpha growls and refuses to advance. The thick
spore air is too much - it would kill them.

"They won't go further," Sira observes. "Smart beasts. This air would
destroy them faster than it'll hurt us."

[COMPANION: Wolves refuse to enter Spore Heart]
[COMPANION: Wolves waiting at Luminous Grotto]
[Sira: follows (uncomfortable but determined)]
```
[MECHANISM: Wolves have no mask option - cannot enter high-spore areas]

```
=== Turn 31-32 ===
[In Spore Heart with Sira only]

The Spore Mother watches you. Sporelings cluster protectively.

[Combat or diplomacy as player chooses]

> go down (toward Deep Root Caverns)

Sira hesitates at the dark passage. "The air down there... I've seen
animals refuse to enter places like that. Usually they're right."

The air grows toxic. Without a breathing mask, Sira cannot survive.

> "Sira, wait here. This is too dangerous."

Sira nods. "Be quick. I don't like this place."

[COMPANION: Sira waiting at Spore Heart]
[Player continues to Deep Roots alone]
```
[MECHANISM: Human companions need mask for toxic areas]
[DESIGN INPUT: Sira doesn't have mask by default - player must provide one or leave her]

```
=== Turn 33-35 ===
[In Deep Root Caverns alone, holding breath]

> [Player retrieves heartmoss, returns before suffocating]

=== Turn 36 ===
> go up (to Spore Heart)

Sira is still here, watching the exit anxiously.

"You're back. Good. These spore things were getting agitated."

[COMPANION: Sira rejoins]
```

```
=== Turn 37 ===
> go up, up (back to Luminous Grotto, then Cavern Entrance)

The wolves are waiting in the Luminous Grotto. They surge toward you
eagerly as you return, sniffing you for injuries.

[COMPANION: Wolves rejoin]
[All companions: now together again]
```
[OBSERVATION: The layered waiting works well - wolves in Grotto, Sira in Heart]

---

## PHASE 3: Acquiring the Salamander (Turns 51-70)

### Frozen Reaches with Wolf+Sira

```
=== Turn 51 ===
[Companions: Wolf Pack + Sira]
[Location: Nexus Chamber (Sira inside, wolves outside)]

> exit, retrieve wolves, go north (to Frozen Reaches)

You enter the Frozen Pass. Biting cold hits immediately.

The wolves shake snow from their fur but seem comfortable - their thick
coats handle the cold well.

Sira pulls her cloak tighter. "This is going to be unpleasant."

[All companions enter Frozen Reaches]
[Wolves: comfortable in cold zones]
[Sira: uncomfortable but functional]
```

```
=== Turn 52 ===
> go west (to Hot Springs Refuge)

Warm air washes over you as you enter the refuge. Steam rises from pools
of heated water.

The wolves immediately relax, settling near the warmth.

Sira sighs with relief. "Now THIS I can appreciate."

Steam salamanders watch you from the pools. Small fire elementals with
curious eyes. They don't seem threatened by the wolves - fire respects
fire, in a sense.

[All companions comfortable in Hot Springs]
```

### Befriending the Salamander

```
=== Turn 53-58 ===
[Building salamander trust through interaction, bringing fire-aspected item]

> give fire crystal to salamander

The salamander accepts the fire crystal with delight. Its flame brightens.
It chirps and dances, then approaches you with clear intent to follow.

"It wants to come with you," Sira observes. "Strange little creature."

[COMPANION ACQUIRED: Salamander]
[COMPANION: Salamander (following)]

The wolves eye the salamander warily. It eyes them back. Neither seems
threatened, just... cautious.

[Multi-companion status: Wolf Pack + Sira + Salamander (3 companions)]
```

### Wolf+Salamander Initial Coexistence

```
=== Turn 59 ===
[First turn with all three companions]

The wolves and salamander maintain distance but don't conflict.
After a few moments, the alpha sniffs toward the salamander curiously.

The salamander's flame flickers - not aggressive, just reactive.

"They're sizing each other up," Sira says. "Give them time."

[Wolf+Salamander: mutual wariness - 3 turns to coexistence]
```

```
=== Turn 60-61 ===
[Turns 2-3 of coexistence timer]

The wolves have stopped watching the salamander constantly.
The salamander seems to understand the pack hierarchy.

=== Turn 62 ===
[Turn 3 complete]

The alpha wolf and the salamander exchange what might be a nod.
Some understanding has been reached. Fire and wolf coexist.

[Wolf+Salamander: coexistence achieved]
[All three companions can now travel together without tension]
```
[MECHANISM: Multi-companion coexistence timer]
[OBSERVATION: This is automatic - just requires time together, no player action needed]

### Testing Salamander in Frozen Reaches

```
=== Turn 63 ===
> go east, east (to Ice Caves)

You enter the Ice Caves. The cold is intense.

The wolves are uncomfortable but tolerate it.
Sira shivers visibly, hypothermia building.

The salamander... thrives. Its warmth radiates outward, and you feel
the cold reduced significantly.

[Salamander benefit: warmth aura - cold immunity for player]
[Wolves: freezing zone uncomfortable]
[Sira: freezing zone dangerous without protection]
```
[MECHANISM: Salamander provides environmental protection]

```
=== Turn 64 ===
> go to deep section (thin ice area)

[Items frozen in ice]

> ask salamander to melt ice around crystal lens

The salamander approaches the frozen lens. It presses against the ice,
flame intensifying. Slowly, carefully, the ice melts away without
damaging the delicate lens.

[Crystal lens: acquired via salamander]
[MECHANISM: Salamander solves ice-extraction puzzle]
```
[OBSERVATION: Salamander is the "right" companion for Frozen Reaches - provides unique utility]

### Frozen Observatory - Extreme Cold

```
=== Turn 65 ===
> go to Frozen Observatory

You approach the observatory. The cold here is beyond natural - magical,
bone-deep, instantly dangerous.

The wolves STOP. Even their thick fur cannot handle this. The alpha
whines and backs away.

Sira is already shivering badly. "I can't... this is too much."

The salamander moves forward eagerly, unaffected.

[COMPANION: Wolves refuse Observatory (extreme cold)]
[COMPANION: Sira cannot survive Observatory]
[COMPANION: Salamander enters normally - provides immunity for player]

Only you and the salamander enter. The others wait at the temple.
```
[MECHANISM: Different companions have different extreme-environment tolerances]
[DESIGN INPUT: Salamander is REQUIRED for Observatory access without cold resistance cloak]

```
=== Turn 66-68 ===
[In Observatory with salamander only]

The salamander's warmth keeps you alive as you repair the telescope.

> [Telescope repair complete]

=== Turn 69 ===
> return to temple

The wolves and Sira are waiting. They seem relieved to see you.

"That place was death," Sira says. "How did you survive?"

The salamander chirps proudly.

[All companions reunited]
```

---

## PHASE 4: The Sunken District Challenge (Turns 71-90)

### Salamander Boundary

```
=== Turn 71 ===
[Companions: Wolf Pack + Sira + Salamander]
[Location: Nexus Chamber approach]

> [Navigate to Nexus, then east toward Sunken District]

You approach the Flooded Plaza. Water laps at the entrance.

Sira: "I can't swim, but I can manage shallow areas."
Wolves: The pack hesitates but follows into ankle-deep water.
Salamander: The salamander STOPS. It backs away from the water, flame
dimming. Distressed chirping sounds.

> continue into Sunken District

The salamander shakes its head firmly. Steam rises from its body as the
humidity increases. It points back toward the Nexus, then turns and
leaves on its own.

[COMPANION: Salamander CANNOT enter Sunken District]
[COMPANION: Salamander returns to Nexus automatically]
[COMPANION: Wolves + Sira enter (with limitations)]
```
[MECHANISM: Salamander auto-returns to safe location when can't follow]
[OBSERVATION: Player doesn't have to manually manage - salamander handles itself]

```
=== Turn 72 ===
[In Flooded Plaza with Wolf Pack + Sira]

Camp Leader Mira eyes the wolves nervously but doesn't object.

"You bring... unusual companions. Can you help us? Two people are missing."

Sira: "I can help with the camp, but I can't swim."

[COMPANION: Sira limited to dry/shallow areas]
[COMPANION: Wolves limited to dry ground]
```

### Wolf Boundaries in Water

```
=== Turn 73 ===
> go east (toward Flooded Chambers)

The water deepens. Chest-high.

The wolves wade in reluctantly, but as the water reaches their chests,
they stop. The alpha growls at the water itself.

[COMPANION: Wolves refuse to swim]
[COMPANION: Wolves waiting at Flooded Plaza]

You continue into the Flooded Chambers alone (or with Sira if shallow enough).
```

```
=== Turn 74 ===
> go east (toward Tidal Passage - underwater)

The passage ahead is fully submerged. Sira shakes her head.

"I can't. I'll drown in there."

[COMPANION: Sira waiting at Flooded Chambers]

You must swim alone.
```
[OBSERVATION: Sunken District systematically strips away companions]
[DESIGN INPUT: This is intentional - the rescue challenges are meant to be solo]

### Rescue Garrett Alone

```
=== Turn 75-79 ===
[Solo in underwater areas]

> [Player navigates to Sea Caves, rescues Garrett]

=== Turn 80 ===
> return to Flooded Chambers (bringing Garrett)

Sira is waiting. "You found him! Is he alive?"

Garrett coughs water. "Barely. Thank you."

[COMPANION: Sira rejoins]
```

```
=== Turn 81 ===
> return to Flooded Plaza

The wolves surge toward you, checking on you eagerly.

[COMPANION: Wolves rejoin]

[All present companions reunited: Wolves + Sira]
[Salamander: still at Nexus]
```

### Retrieving the Salamander

```
=== Turn 82 ===
> go west (to Nexus)

[Wolves wait at boundary, Sira enters]

In the Nexus Chamber, the salamander perks up when it sees you.
It chirps happily and rushes over.

[COMPANION: Salamander rejoins]
[COMPANION: Sira present]
[COMPANION: Wolves outside]
```
[MECHANISM: Salamander remembered player, waited at Nexus]
[OBSERVATION: Good - companion continuity maintained]

---

## PHASE 5: Full Party Management (Turns 91-120)

### Maximum Companion Load

```
=== Turn 91 ===
[Companions: Wolf Pack (3) + Sira (1) + Salamander (1) = 5 entities following]
[Location: Nexus (wolves outside)]

> exit south, collect wolves, travel to Beast Wilds

Full party assembled: Player + 3 wolves + Sira + Salamander

Movement is slower with this many companions. They coordinate but
it takes extra time to move as a group.

[MECHANISM: Large party may have movement penalty?]
[QUESTION: Should there be a party size limit or movement cost?]
```
[DESIGN INPUT: No hard party size limit, but narration should reflect managing many companions]

### Aldric as Fourth Companion Type

```
=== Turn 92-95 ===
[After saving Aldric with silvermoss]

> "Aldric, will you travel with me?"

Aldric struggles to stand. "I'm still weak, but... yes. I want to see
what's become of the world. And I can teach you about the fungi as we go."

[COMPANION ACQUIRED: Aldric (human, weakened)]

[Companions: Wolf Pack + Sira + Salamander + Aldric]

Sira eyes Aldric. "Another one? You're collecting a small army."

Aldric looks at the wolves nervously. "They're... quite large."

The alpha sniffs Aldric, then ignores him. No threat detected.

[Wolf+Aldric: neutral (no conflict)]
```

### Testing Aldric Limitations

```
=== Turn 96 ===
> go down (toward Luminous Grotto with all companions)

Everyone follows. Aldric moves slowly, leaning on walls.

"I know this place," Aldric says. "But I'm too weak to go much further."

In the Grotto, Aldric can provide information but cannot enter dangerous areas.

[Aldric: limited to safe areas]
[Aldric benefit: lore/information in Fungal Depths]
```

```
=== Turn 97 ===
> go down (toward Spore Heart)

Aldric shakes his head. "I can't. The spores would kill me in minutes.
I'll wait here."

[COMPANION: Aldric waiting at Luminous Grotto]
[COMPANION: Wolves also refuse (as established earlier)]
[COMPANION: Sira follows (if has mask)]
[COMPANION: Salamander follows]
```
[OBSERVATION: Different companions drop off at different thresholds]

### Companion Conversation Interactions

```
=== Turn 98 ===
[Multiple companions resting at Hot Springs]

The companions interact with each other:

Sira watches Aldric with sympathy. "You were a scholar? Before?"

Aldric: "Still am. The knowledge didn't leave when my strength did."

The salamander curls near the warmest pool. A wolf pup cautiously
approaches it, then retreats when flame flickers.

The alpha watches everything, ever vigilant.

[MECHANISM: Companion idle dialog when multiple companions present]
```
[DESIGN INPUT: Companions should have interactions with each other when resting]

---

## Summary Tables

### Companion Access Matrix (Confirmed)

| Location | Wolves | Salamander | Sira | Aldric |
|----------|--------|------------|------|--------|
| **Nexus** | NO (wards) | Yes | Yes | Yes |
| **Fungal: Entrance** | Yes | Yes | Yes | Yes |
| **Fungal: Grotto** | Yes (uncomfortable) | Yes | Yes | Yes |
| **Fungal: Spore Heart** | NO | Yes | With mask | NO |
| **Fungal: Deep Roots** | NO | Yes | With mask | NO |
| **Beast: Most areas** | Yes (home) | Yes (uncomfortable) | Yes (home) | Yes |
| **Beast: Spider Gallery** | NO (instinct) | Yes | Yes | Yes |
| **Frozen: Most areas** | Yes (comfortable) | Yes | Yes (cold gear) | Too weak |
| **Frozen: Observatory** | NO (extreme cold) | Yes (provides immunity) | NO | NO |
| **Sunken: Plaza/Camp** | Yes (shallow) | NO | Yes | Yes |
| **Sunken: Flooded areas** | NO (can't swim) | NO | NO (can't swim) | NO |
| **Civilized: All areas** | Yes (but noticed) | Yes | Yes | Yes |

### Waiting Locations

| Companion | Default Wait | Auto-Return Location |
|-----------|--------------|---------------------|
| Wolf Pack | Last safe location before boundary | Wolf Clearing (home base) |
| Salamander | Nexus Chamber | Hot Springs (if in Frozen) |
| Sira | Survivor Camp (if Sunken) or nearest safe | None - stays at boundary |
| Aldric | Cavern Entrance (if Fungal) | None - stays at boundary |

### Design Inputs Generated

| ID | Input | Value | Notes |
|----|-------|-------|-------|
| DI-B1 | Wolf dismissal gesture | Works - wolves return to home | Player can dismiss to avoid conflicts |
| DI-B2 | Reconciliation dialog requirements | Sira trust 2+, Wolf trust 3+, player initiates | Already defined, confirmed working |
| DI-B3 | Wolf+Salamander coexistence | 3 turns automatic | No player action needed |
| DI-B4 | Salamander auto-return | Yes - to Nexus when can't follow | Good QOL - player doesn't manage manually |
| DI-B5 | Human companion mask requirement | Required for toxic areas | Consistent with environmental rules |
| DI-B6 | Aldric combat capability | None - too weak | Only provides information |
| DI-B7 | Party size limit | None proposed | Large parties narrated as slower but functional |
| DI-B8 | Companion idle interaction | Companions talk when resting | Adds life to multi-companion scenes |

### Questions Raised

| ID | Question | Proposed Resolution |
|----|----------|---------------------|
| Q-B1 | Movement penalty for large parties? | No mechanical penalty, but narration reflects coordination time |
| Q-B2 | Can player give mask to companion? | Yes - equipment can be given to human companions |
| Q-B3 | What if wolf dies saving player? | Exceptional bravery: one wolf dies, others survive. Pack trust maintained. |
| Q-B4 | Can salamander die in water? | Yes - 2 turns of submersion kills it. Player warned before this happens. |
| Q-B5 | Do companions need food/rest? | No mechanical requirement. Flavor text only. |
| Q-B6 | Can companions hold items for player? | Human companions: yes (limited). Animal companions: no. |

### Mechanisms Required

| Mechanism | Status | Notes |
|-----------|--------|-------|
| Companion boundary detection | Needed | Check companion can_enter on room transition |
| Automatic waiting | Needed | Companions stay at boundary, rejoin on return |
| Auto-return to safe location | Needed | Salamander returns to Nexus when can't follow |
| Multi-companion conflict detection | Needed | Wolf+Sira hostility on first meeting |
| Reconciliation dialog gating | Needed | Check trust levels before allowing option |
| Coexistence timer | Needed | 3 turns for wolf+salamander |
| Companion environmental benefits | Needed | Salamander warmth, Sira tracking, wolf combat |
| Companion idle dialog | Desired | When multiple companions rest together |

### Gameplay Observations

**Positive:**
- Companion restrictions create meaningful tactical decisions
- Different companions excel in different regions (salamander=Frozen, wolves=Beast, Sira=Beast)
- Automatic waiting/rejoining is good QOL
- Reconciliation is earned through gameplay, not automatic
- Multi-companion interactions add life to the world

**Concerns:**
- Managing 4+ companions could be confusing - need clear status display
- Player might not know companion can't enter until they try (should there be warnings?)
- What happens to companions if player dies? (they survive, player resurrection?)

**Interesting Patterns:**
- Sunken District systematically strips companions - intentional solo challenge
- Salamander is "required" for Observatory access without cloak - creates gear/companion choice
- Wolves are most generally useful but blocked from Nexus (wards) and water
- Human companions are most flexible but need equipment for hazards

---

## Key Findings

1. **Companion boundaries work as designed** - Each companion has logical limitations based on their nature

2. **Automatic management is essential** - Auto-waiting and auto-return prevent tedious micromanagement

3. **Multi-companion conflicts add depth** - Wolf+Sira reconciliation is earned through trust building

4. **Region-companion matching** - Each region has a "best" companion (salamander for cold, wolves for combat)

5. **Sunken District is the solo challenge** - No companion can help with the underwater rescues

6. **Coexistence is time-based** - Wolf+salamander just need time together, not player action

7. **Human companions are versatile but fragile** - Need equipment to survive hazards

---

## Sketch Update Recommendations

### game_wide_rules.md
- Add: Companion status display recommendation for UI
- Add: Warning system before companion can't enter area
- Clarify: Companion death mechanics (can companions die permanently?)

### sunken_district_sketch.json
- Add design note: "This region is designed to strip away companions, making rescues solo challenges"

### frozen_reaches_sketch.json
- Add design note: "Salamander is effectively required for Observatory without cold resistance cloak - creates meaningful gear vs companion choice"

---

*Walkthrough completed. Ready for Walkthrough C (Dark Path).*
