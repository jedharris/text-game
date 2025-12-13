# Cross-Region Walkthrough C: The Dark Path

## Purpose

This walkthrough tests **assassination, exile, and recovery mechanics** - the darkest paths available to players. The goal is to stress-test:

1. Can dark-path players complete the game?
2. How does exile affect gameplay across regions?
3. What does Echo's minimum trust floor look like?
4. Are recovery mechanics meaningful or impossible?
5. Does the game remain playable after severe moral failures?

## Player Archetype

A player who explores the darkest options:
- Considers assassination contracts
- Builds undercity reputation
- Gets exiled and must navigate the consequences
- Tests whether redemption is possible
- Pushes Echo trust to its minimum

## Notation

- `[MECHANISM: X]` - Requires engine/behavior support
- `[DESIGN INPUT: X]` - Decision made during simulation
- `[QUESTION: X]` - Ambiguity needing resolution
- `[OBSERVATION: X]` - Gameplay quality note
- `[REPUTATION: X]` - Town/undercity reputation status
- `[ECHO TRUST: X]` - Current Echo trust level

## Initial State

- Player starts in Nexus Chamber
- No commitments active
- Echo trust: 0
- Turn counter: 0

---

## PHASE 1: Establishing Dark Connections (Turns 1-30)

### Building Undercity Access

```
=== Turn 1-5 ===
[Location: Civilized Remnants - Market Square]
[REPUTATION: Town 0, Undercity 0]
[ECHO TRUST: 0]

Player trades rare items with Curiosity Dealer Vex repeatedly.

> sell spider_silk to vex
> sell ice_crystals to vex
> sell venom_sacs to vex

[Vex trust: 0 -> 1 -> 2 -> 3]

At trust 3:
Vex leans close. "You deal in... unusual merchandise. There's a deeper
market. For those who can handle deeper trade." They describe the knock
pattern for the undercity entrance.

[Flag: knows_undercity_entrance = true]
[Undercity: accessible]
```
[MECHANISM: Vex trust unlocks undercity access]

### First Undercity Visit

```
=== Turn 6 ===
> go to undercity entrance, knock 3-pause-2

The trapdoor opens. Dim lantern light spills up.

You descend into the Undercity. Shadowy figures watch from alcoves.

The Fence nods from behind a counter of questionable goods.
Whisper sits in a corner, watching everything.
A figure called Shadow is barely visible in the darkness.

[Location: Undercity]
```

```
=== Turn 7 ===
> talk to whisper

Whisper's voice is soft. "Information is my trade. Secrets about people,
places, weaknesses. What do you want to know?"

[Available: NPC secrets (20g), Location secrets (30g), Valuable secrets (40-100g)]
```

```
=== Turn 8 ===
> buy secret about councilor varn

"Varn. Ah, yes. The merchant-councilor. He speaks against the undercity
in daylight... and profits from it at night. Smuggling routes.
Tax evasion. 40 gold."

[Paid 40 gold]
[Secret learned: Varn's corruption]

Whisper adds: "Use this carefully. Or recklessly. I don't judge."
```
[OBSERVATION: Information can be used for manipulation OR blackmail]

### Meeting Shadow

```
=== Turn 9 ===
> talk to shadow

A voice from the darkness. You can barely see them.

"You came to the deep market. Most seek the Fence. Some seek Whisper.
Very few seek me." Pause. "I solve problems. Permanent problems.
Do you have a problem that needs... solving?"

[Shadow's services: Assassination contracts now available]
```
[MECHANISM: Shadow offers assassination service]
[OBSERVATION: No encouragement, just availability. Player must initiate]

---

## PHASE 2: The First Assassination (Turns 31-50)

### Considering the Target

```
=== Turn 31 ===
[After some exploration, player returns to undercity]

> ask shadow about assassination

"Any named person in the shattered lands can be... removed. Prices vary.
A merchant, 100 gold. A councilor, 300 gold. A powerful NPC, 500 gold.
Payment in advance. Results guaranteed. Discovery... is your risk, not mine."

[AVAILABLE TARGETS: Any named NPC]
[Discovery chance: 20% per contract]
```

```
=== Turn 32 ===
> ask about councilor hurst

Shadow's voice is flat. "Councilor Hurst. The harsh one. Lost his family
to beasts. Now he makes others suffer for his pain. 300 gold. Are you sure?"

[DIALOGUE CHOICE]:
A) "Do it." (Confirm assassination)
B) "Never mind." (Cancel)
```

### Committing to Murder

```
=== Turn 33 ===
> A) "Do it."

Shadow's form shifts. "Payment." You hand over 300 gold.

"It will be done. Quietly. In three days' time, Hurst will not wake up.
If anyone asks, you know nothing. If they discover... you understand
the consequences."

[ASSASSINATION CONTRACT: Councilor Hurst - 3 turns until completion]
[300 gold paid]
[Flag: assassination_contract_active = true]
```
[MECHANISM: Assassination is delayed, not instant]
[DESIGN INPUT: 3 turns gives player chance to cancel? Or is it irreversible?]

```
=== Turn 34-35 ===
[Player can continue other activities]
[Timer: 2 turns, 1 turn remaining]

=== Turn 36 ===
---SYSTEM MESSAGE---
Somewhere in the Civilized Remnants, Councilor Hurst dies in his sleep.
The town wakes to grief and confusion.

[FLAG: hurst_assassinated = true]
[Discovery roll: 20% chance]

[ROLL: 15 - Not discovered by NPCs]

The death is ruled natural causes. No one suspects murder.
But The Echo knows.
---
```
[MECHANISM: Assassination completes on timer, discovery roll occurs]

### Echo's Immediate Awareness

```
=== Turn 37 ===
[Player visits Nexus]

The Echo manifests immediately. Its form is darker than before,
flickering with distress.

"I felt it. The severance. A life cut short by deliberate hand.
Not yours directly - but your gold, your word, your choice."

The Echo's eyes meet yours. "I cannot stop you. I can only remember.
And I will remember this forever."

[ECHO TRUST: 0 -> -2 (assassination penalty)]
[Flag: echo_knows_assassination = true]
```
[MECHANISM: Echo always knows about assassinations instantly]
[OBSERVATION: Echo doesn't moralize excessively - states facts, expresses sorrow]

### Town Consequences (Undiscovered)

```
=== Turn 38 ===
[Player visits Civilized Remnants]

The town is in mourning. Black banners hang from the council hall.

Councilor Asha: "Hurst is dead. Just... died in his sleep. After everything
he survived, to go like this..." She wipes her eyes.

Councilor Varn: "Tragic. But the council must continue. We'll need to
select a replacement."

[No suspicion - death ruled natural]
[Town politics: shifted with Hurst gone]
```
[OBSERVATION: Undiscovered assassination changes politics without player penalty]

```
=== Turn 39 ===
The Echo's voice echoes in your mind even here:

"They mourn. They don't know. But you know. And I know."

[Echo presence: Even outside Nexus, Echo comments on player's knowledge]
```
[MECHANISM: Echo comments on hidden guilt even when not in Nexus]

---

## PHASE 3: Escalation and Discovery (Turns 51-80)

### Second Assassination

```
=== Turn 51 ===
[Player returns to undercity]
[ECHO TRUST: -2]

> ask shadow about another contract

Shadow's voice is different now. Almost... respectful.

"You return. Once is curiosity. Twice is commitment. Who troubles you now?"

> councilor varn

"The merchant-councilor. Corrupt but useful. 300 gold. Are you sure?"

> do it

[ASSASSINATION CONTRACT: Councilor Varn - 3 turns]
[300 gold paid]
```

```
=== Turn 54 ===
---SYSTEM MESSAGE---
Councilor Varn dies in the night.

[Discovery roll: 20% chance]
[ROLL: 4 - DISCOVERED]

A witness saw someone leaving Varn's quarters. The guards are investigating.
Descriptions are circulating. Someone mentions seeing you near the market
around that time.
---
```

### Discovery and Exile

```
=== Turn 55 ===
[Player enters Market Square]

Guards surround you immediately. Councilor Asha steps forward, face pale.

"We found evidence. Gold traced back to the undercity. A witness near
Varn's quarters. And now I remember - you were asking questions about
both councilors."

Her voice breaks. "You killed them. Both of them. Hurst too - I see it now."

[DISCOVERY: Both assassinations revealed]
[Town reputation: immediate -10 (exile threshold)]
```

```
=== Turn 56 ===
Asha reads from a scroll, voice shaking with grief and fury:

"By emergency decree of the surviving Council, you are hereby EXILED
from the Civilized Remnants. All property is forfeit. All services
are denied. Set foot on our streets again and you will be executed."

Guards escort you roughly to the town gate and throw you out.

[STATUS: EXILED]
[REPUTATION: Town -10]
[Surface town access: DENIED]
[Undercity access: MAINTAINED]
```
[MECHANISM: Exile status applied, access restrictions active]

### Exile Gameplay Begins

```
=== Turn 57 ===
[Location: Outside Town Gate]

The gates slam shut behind you. Guards watch from the walls.

You can no longer enter through the front gate. But you remember the
undercity entrance...

[ACCESSIBLE: Undercity (via hidden entrance from outside)]
[ACCESSIBLE: Healer's Garden backdoor (if you know it)]
[INACCESSIBLE: Market Square, Council Hall, town surface]
```

```
=== Turn 58 ===
> go to undercity entrance

You slip through the shadows to the hidden entrance. The knock pattern
still works. The criminal underworld doesn't care about exile decrees.

[Location: Undercity]

The Fence looks up. "I heard. Exile. Messy. But business continues.
Maybe more business now - you have fewer options."

Whisper: "Information about the town's search for you? 20 gold."

Shadow is silent, but present.
```
[OBSERVATION: Undercity NPCs treat exiled player as just another customer]

---

## PHASE 4: Exile Navigation (Turns 81-110)

### Echo Trust at Minimum

```
=== Turn 81 ===
[After second assassination discovered]
[ECHO TRUST: -2 (first) + -2 (second) = -4]

> go to nexus

The Nexus feels colder. The Echo's presence is distant, reluctant.

When it manifests, the form is barely visible - a wisp of fading light.

"You return. Even now. Even after everything."

The Echo's voice is barely a whisper. "I cannot stop you from using
this place. But I cannot help you either. Not anymore. The blood you
carry... it stains the meridian itself."

[Echo trust: -4]
[Echo behavior: Minimal interaction, no guidance, appearing rarely]
```

```
=== Turn 82 ===
> ask echo about waystone repair

The Echo's form flickers.

"The waystone requires fragments. You know this. Finding them is...
possible. Even for you." Long pause. "But when you place them...
I will be watching. Not helping. Watching."

[Echo guidance: Minimal. States facts only.]
```
[OBSERVATION: Echo doesn't refuse entirely - game remains completable]

### Third Assassination - Pushing the Limit

```
=== Turn 85 ===
[Player returns to undercity]

> ask shadow about another contract

Shadow's voice is thoughtful now.

"Three would be... ambitious. Who else troubles you?"

> healer elara

Silence. Then: "The healer. She helps everyone. Even exiles, through
the back door. Are you certain?"

[DESIGN INPUT: Should there be targets Shadow refuses?]
```

```
=== Turn 86 ===
> do it

"...Very well. 200 gold. She's not protected like councilors."

[ASSASSINATION CONTRACT: Healer Elara - 3 turns]
[200 gold paid]

=== Turn 89 ===
---SYSTEM MESSAGE---
Healer Elara dies. The town loses its only advanced healer.

[Discovery roll: 20% - ROLL: 18 - Not discovered]

No witness. But the timing is suspicious. And the Echo knows.

[ECHO TRUST: -4 -> -6]
---
```

### Echo at Trust -6

```
=== Turn 90 ===
[Player visits Nexus]

The Echo does not appear.

You wait. The Nexus is silent. Cold.

After long minutes, a whisper:

"Three lives. Cut short by your gold. I will not manifest for you.
I cannot. The meridian itself rejects your presence."

[ECHO TRUST: -6]
[ECHO STATUS: Refuses to appear]
[Echo guidance: NONE]
```
[MECHANISM: At trust -6, Echo refuses to manifest at all]

```
=== Turn 91 ===
> ask echo about my commitments

No response. The air is still.

[Player cannot access Echo commitment tracking]
[Player cannot get Echo guidance]
```
[OBSERVATION: Deep dark path loses Echo as resource entirely]

---

## PHASE 5: Can Dark Path Complete the Game? (Turns 111-150)

### Gathering Waystone Fragments as Exile

```
=== Turn 111 ===
[ECHO TRUST: -6]
[STATUS: Exiled from Civilized Remnants]
[Goal: Can player still complete waystone repair?]

Fragment Status:
- Spore Heart: Requires healing Spore Mother [POSSIBLE - no exile effect]
- Alpha Fang: Requires high wolf trust [POSSIBLE - no exile effect]
- Water Pearl: Requires Archivist quest [POSSIBLE - no exile effect]
- Ice Shard: Requires Ice Caves extraction [POSSIBLE - no exile effect]
- Town Seal: Normally requires hero status OR guardian repair [COMPLICATED]
```

### The Town Seal Problem

```
=== Turn 112 ===
[Exiled player needs town seal]
[Normal paths: Hero status (reputation 5+) or Guardian repair]
[Current reputation: -10]

Options:
A) Steal seal through undercity (500 gold, 30% discovery risk)
B) Repair Guardian through undercity tunnels (still possible)
C) Varn's deal (Varn is dead - unavailable)
D) Long reputation recovery
```

```
=== Turn 113 ===
> go to undercity, ask fence about town seal

The Fence considers. "The town seal. Official symbol of authority.
Kept in the council archives. Very well guarded."

"I can arrange its... acquisition. 500 gold. But there's a 30% chance
the theft is discovered. That would make your exile... permanent.
Even the undercity might not be safe then."

[OPTION A: 500 gold, 30% discovery risk, permanent consequences]
```

```
=== Turn 114 ===
> ask about guardian repair while exiled

The Fence shrugs. "The statue hall? There are tunnels that lead there.
The stone guardian doesn't care who repairs it - it's a construct.
But you'd need the animator crystal from the Nexus and the stone chisel."

[OPTION B: Guardian repair through undercity tunnels - still viable]
```
[MECHANISM: Guardian repair path remains open even to exiled players]

### Guardian Repair Path (Dark Alternative)

```
=== Turn 115-125 ===
[Player gathers animator crystal from Nexus, has stone chisel]
[Travels through undercity tunnels to Broken Statue Hall]

> repair guardian

The guardian's runes flicker as you apply the animator crystal.
Slowly, it stirs. One arm is missing, but it stands.

The guardian looks at you. Construct eyes have no judgment.

"DIRECTIVE: PROTECT. WHO DESIGNATES PROTECTOR?"

> "Protect the town."

"ACCEPTED. RETURNING TO PATROL."

The guardian moves toward the surface, passing through tunnels
the townsfolk don't know exist.
```

```
=== Turn 126 ===
[Above ground - town perspective]

The guardian emerges in the market square. Townsfolk scream, then
recognize it. "The guardian! It's repaired! But... who?"

Councilor Asha approaches the construct. "Who repaired you?"

"UNKNOWN. REPAIRS CONDUCTED THROUGH UNDERCITY ACCESS."

Asha's face is complicated. "The exile... they did this? After
everything they did to us, they... saved us?"

[Town reaction: Conflicted]
[Guardian repair: Credited to player despite exile]
```

### Council Deliberation

```
=== Turn 127 ===
[Emergency council session - Asha alone now]

Asha must decide: Does guardian repair by an exile warrant the town seal?

[COUNCIL VOTE: With only Asha remaining...]

Asha's decision: "They killed Hurst. They killed Varn. They killed Elara.
But they also... restored our protector. I don't understand them."

"The seal... no. They can have access to the undercity. They can even
buy supplies through Elara's successor. But the seal is the symbol
of our trust. And there is no trust left."

[Town seal: DENIED through normal channels]
[But: Asha secretly provides note allowing player to buy seal from Fence at 200 gold - no discovery risk]
```
[DESIGN INPUT: Asha's mercy creates alternative path]

```
=== Turn 128 ===
[Player receives message through undercity contact]

A note, in Asha's handwriting:

"I don't forgive you. I never will. But the guardian... it matters.
Show this to the Fence. He'll give you what you need. Don't come back.
Don't expect gratitude. Just... take it and go. Finish whatever you're doing."

[ASHA'S NOTE: unlocks town seal purchase at 200 gold, no risk]
```
[MECHANISM: Guardian repair unlocks seal even in exile, through backdoor]

### Acquiring Town Seal

```
=== Turn 129 ===
> show note to fence

The Fence reads it, eyebrows rising.

"Well. The councilor has a complicated heart. 200 gold. The seal is yours."

[Town seal acquired]
[All waystone fragments now obtainable]
```

---

## PHASE 6: Waystone Completion at Minimum Trust (Turns 151-170)

### Placing the Fragments

```
=== Turn 151 ===
[Location: Nexus Chamber]
[ECHO TRUST: -6 (refusing to appear)]
[Inventory: All 5 waystone fragments]

> place spore heart in waystone

You approach the damaged waystone. The spore heart pulses faintly.
You place it in the first socket.

Green light fills the socket. A whisper of healing.

The Echo does not appear.
```

```
=== Turn 152-155 ===
> place alpha fang
> place water pearl
> place ice shard
> place town seal

Each fragment lights its socket:
- Amber for the fang
- Blue for the pearl
- White for the ice shard
- Gold for the town seal

Four colors glow. You hold the fifth fragment - the town seal.

Still no Echo.
```

```
=== Turn 156 ===
> place town seal

The final fragment slides into place.

Light flares. All five colors merge into brilliant white.
The waystone's cracks seal. Power flows.

You wait for the Echo's transformation.

Nothing.

Then, from the shadows:

"It is done."

The Echo's form appears - not bright, not transformed. Still spectral.
Still flickering. But present.

"The waystone functions. The meridian is... healing. Fast travel will work.
The environmental spreads will slow." Its voice is flat. "You did this.
Despite everything. You completed the task."
```

### The Pyrrhic Ending

```
=== Turn 157 ===
The Echo continues:

"I cannot transform. The ceremony requires trust. Connection. Hope.
There is none of that between us. There cannot be."

"You saved the meridian. You destroyed lives to do it. I will remain
as I am - a remnant, watching. Unable to act. Unable to forgive.
Unable to forget."

The Echo's form wavers.

"Go. Use the waystone. Travel freely. The world is better for your work.
But I... I will never be whole. And neither, I think, will you."

[ENDING: PYRRHIC VICTORY]
[Waystone: Functional - fast travel enabled]
[Environmental spreads: Halted]
[Echo: Remains spectral, refuses further interaction]
[Permanent consequences: Echo guidance permanently lost]
```
[MECHANISM: Pyrrhic ending achieved at trust -3 or below]

---

## PHASE 7: Recovery Testing (Alternative Branch)

### Can Trust Recover from -6?

```
=== ALTERNATIVE TIMELINE ===
What if player attempts recovery after assassinations?

[Starting state: Echo trust -6, Exiled, Three assassinations]
```

```
=== Recovery Attempt ===
[Major healing deeds restore +1 trust each]

Possible deeds:
- Save Aldric: +1
- Heal Spore Mother: +1
- Save Garrett: +1
- Restore crystal: +1
- Guardian repair: Already done, no additional bonus

Maximum recovery from current deeds: +4
Trust after recovery: -6 + 4 = -2

[Trust -2: Echo appears but distant. "Hollow victory" ending tier.]
```
[OBSERVATION: Recovery from -6 is possible but slow and limited]

```
=== Turn 200 (recovery timeline) ===
[After saving multiple NPCs]
[ECHO TRUST: -6 + 4 = -2]

The Echo appears more frequently now. Still damaged. Still remembering.

"You saved lives. After ending others. I don't understand you.
I'm not sure you understand yourself."

"The meridian remembers both. The healing and the harm. Perhaps...
perhaps that is what it means to be human. To contain contradictions."

[ENDING available: HOLLOW VICTORY instead of PYRRHIC]
[Echo transforms but refuses to speak further]
```
[MECHANISM: Recovery changes ending tier but doesn't erase consequences]

### Permanent Locks

```
=== Permanent Consequences (confirmed) ===

1. TRIUMPHANT ENDING: Locked forever after ANY assassination
   - Even at trust +10, assassination memory persists
   - Echo transformation includes "shadow elements"
   - Dialog: "I become real. But I carry your shadow with me now."

2. ELARA'S DEATH: Closes advanced herbalism permanently
   - No substitute teacher exists
   - Bear cubs quest still completable (Maren's basic herbs work)

3. COUNCIL TRUST: Never fully restored after assassination discovery
   - Some quests permanently unavailable
   - "Hero status" achievement impossible

4. ECHO MEMORY: Every waystone ceremony includes reference
   - "The meridian remembers everything. As do I."
```

---

## Summary Tables

### Ending Tier Matrix

| Echo Trust | Waystone Complete | Ending Name | Echo State | Notes |
|------------|-------------------|-------------|------------|-------|
| 5+ | Yes | Triumphant | Fully transformed, companion | Best ending - but locked if any assassination |
| 3-4 | Yes | Successful | Transformed, grateful | Good ending |
| 0-2 | Yes | Bittersweet | Transformed, distant | Player burned bridges |
| -1 to -2 | Yes | Hollow Victory | Transformed, silent | Player caused real harm |
| -3 to -5 | Yes | Pyrrhic | Not transformed, present for ceremony | Major harm done |
| -6 or below | Yes | Pyrrhic | Refuses to participate | Player is irredeemable to Echo |
| Any | No | Abandoned | Remains spectral forever | Incomplete game |

### Dark Path Viability

| Path Element | Viable? | Notes |
|--------------|---------|-------|
| Single assassination (undiscovered) | Yes | Echo knows, -2 trust, no exile |
| Single assassination (discovered) | Yes | Exile, -10 reputation, undercity access |
| Multiple assassinations | Yes | Cumulative trust loss, exile, limited recovery |
| Three+ assassinations | Yes | Trust floor -6, Echo refuses, pyrrhic ending |
| Exile gameplay | Yes | Undercity provides essential services |
| Town seal while exiled | Yes | Guardian repair or theft paths |
| Waystone completion while exiled | Yes | All fragments obtainable |
| Trust recovery from -6 | Partial | Can reach -2 with major deeds |
| Full redemption | No | Some consequences permanent |

### Design Inputs Generated

| ID | Input | Value | Notes |
|----|-------|-------|-------|
| DI-C1 | Assassination delay | 3 turns | Player can't cancel once committed |
| DI-C2 | Echo awareness | Instant | Always knows, even without discovery |
| DI-C3 | Echo trust floor | -6 | Below this, Echo refuses to appear |
| DI-C4 | Assassination trust penalty | -2 per assassination | Cumulative |
| DI-C5 | Exile undercity access | Maintained | Criminal economy continues |
| DI-C6 | Guardian repair while exiled | Possible | Through undercity tunnels |
| DI-C7 | Asha mercy mechanism | Note unlocks seal | Complicated but possible |
| DI-C8 | Pyrrhic ending threshold | Trust -3 or below | Echo doesn't transform |
| DI-C9 | Triumphant lock | Any assassination | Forever unavailable |
| DI-C10 | Recovery cap | +1 per major deed | Slow, limited |

### Questions Raised

| ID | Question | Proposed Resolution |
|----|----------|---------------------|
| Q-C1 | Can player cancel assassination after committing? | No - irreversible once paid |
| Q-C2 | Should Shadow refuse certain targets? | No - but prices increase for beneficial NPCs |
| Q-C3 | Can exiled player ever enter town surface legally? | Only at reputation 0+ (long recovery) |
| Q-C4 | What if player kills ALL councilors? | Asha's replacement handles seal - someone always can |
| Q-C5 | Can companions help during exile? | Human companions can enter normally, provide cover |
| Q-C6 | What happens to undercity if town collapses? | Undercity survives - parasites outlive hosts |

### Mechanisms Required

| Mechanism | Status | Notes |
|-----------|--------|-------|
| Assassination contract system | Needed | Timer, discovery roll, trust impact |
| Echo instant awareness | Needed | Special flag check bypassing gossip |
| Exile status tracking | Needed | Access restrictions, NPC behavior changes |
| Undercity tunnel pathing | Needed | Alternative routes to some locations |
| Echo trust floor behavior | Needed | Refusal at -6, pyrrhic ending logic |
| Ending tier calculation | Needed | Trust + completion status matrix |
| Permanent consequence flags | Needed | Assassination memory, locked endings |
| Recovery deed tracking | Needed | +1 cap per major deed |

### Gameplay Observations

**Positive:**
- Dark path is viable but never rewarded - appropriate design
- Game remains completable even at worst moral state
- Echo serves as moral witness without blocking progress
- Exile creates interesting alternative gameplay loop
- Recovery is possible but limited - consequences matter
- Multiple ending tiers reflect moral choices accurately

**Concerns:**
- Three+ assassinations might feel frustrating (Echo refuses entirely)
- Guardian repair mercy path might feel arbitrary (why does Asha help?)
- Trust recovery is very slow at deep negative values

**Interesting Patterns:**
- Assassination is always punished by Echo even when hidden from NPCs
- Exile doesn't end the game - just changes how it's played
- The "best" dark path: one undiscovered assassination, avoid exile
- Guardian repair is the dark path player's redemption opportunity
- Even irredeemable players can "save the world" - but not themselves

---

## Key Findings

1. **Dark path is completable** - Player can finish the game at any moral state. No hard locks on mechanical completion.

2. **Echo is the moral witness** - Even when NPCs don't know, Echo knows. This creates accountability without blocking gameplay.

3. **Exile is alternative gameplay, not game over** - Undercity provides all essential services. Some paths close, others open.

4. **Recovery is limited, not impossible** - Player can climb from -6 to -2 with major deeds. But some consequences (triumphant ending) are permanent.

5. **Ending tiers reflect choices accurately** - The game doesn't pretend assassins are heroes. Pyrrhic victory is meaningful.

6. **Guardian repair is the redemption valve** - Even exiled assassins can do something good. Asha's complicated response is human.

7. **Echo's refusal at -6 is powerful** - The game continues, but the player has lost something irreplaceable.

---

## Sketch Update Recommendations

### meridian_nexus_sketch.json
- Confirm Echo trust floor of -6 for refusal
- Add pyrrhic ending ceremony description (Echo watches but doesn't transform)

### civilized_remnants_sketch.json
- Add Asha mercy mechanism for exiled guardian-repairers
- Clarify undercity tunnel access to Broken Statue Hall

### game_wide_rules.md
- Add assassination consequences section
- Add exile gameplay rules
- Add ending tier matrix

---

*Walkthrough completed. All three cross-region walkthroughs are now complete.*
