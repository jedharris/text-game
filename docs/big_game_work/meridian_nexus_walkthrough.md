# Meridian Nexus Walkthrough

## Purpose

This walkthrough explores the **central hub region** - fundamentally different from all others:
- **Absolutely safe** - no combat, no environmental hazards, no time pressure
- **Information hub** - The Echo provides guidance, telescope shows region states
- **Progress tracking** - Crystal garden shows restoration progress
- **Moral mirror** - Echo comments on player's actions throughout game
- **Endgame location** - Waystone repair is the culmination

The Nexus is where the player starts, returns repeatedly, and ultimately completes their journey.

## Notation

- `[MECHANISM: X]` - Requires engine/behavior support
- `[DESIGN INPUT: X]` - Decision made during simulation
- `[QUESTION: X]` - Ambiguity needing resolution
- `[OBSERVATION: X]` - Gameplay quality note

## Initial State (First Visit)

- Player has just entered the game
- No items, no companions, no knowledge
- Health 100, no conditions
- The world is broken and player knows nothing

---

## TRUNK A: First Entry and Orientation

### Turn 1
[Location: Nexus Chamber]

You awaken in a place that feels... wrong. Right. Both.

The air shimmers. Stone platforms float at impossible angles. Geometric patterns cover every surface, some glowing faintly, others dark and cracked.

In the center stands a stone pedestal - cracked, its runes flickering weakly.

The Damaged Waystone is here.

Exits: North (cold air), South (green scent), East (water sounds), West (strange spores), Up (stairs).

[OBSERVATION: The game begins here. Player is disoriented by design - mirrors their character's confusion.]

---

### Turn 2

> look

The Nexus Chamber is the heart of something vast and broken. Five pathways lead outward - you can sense different atmospheres from each.

North: Cold wind, snow glimpsed through the arch.
South: Forest smells, distant animal sounds.
East: Water lapping, humid air.
West: An odd sweetness, faintly luminescent air.
Up: Stairs spiral toward a platform above.

The damaged waystone pulses weakly. You feel drawn to it but don't know why.

[DESIGN INPUT: Each exit hints at its region's nature - sensory foreshadowing]

---

### Turn 3

> examine waystone

The waystone is a pedestal of dark stone, perhaps three feet tall. Cracks run through its surface. Runes that once glowed brightly are now dim, some completely dark.

It has five mounting points around its rim - empty sockets that seem to wait for something.

[Flag set: has_seen_waystone]
[Implicit goal established: player should intuit these sockets need filling]

---

### Turn 4

> go up

You climb the spiral stairs. Reality feels thinner as you ascend - you catch glimpses of other places through the shimmering air.

[Location: Observatory Platform]

A platform overlooking the broken landscape. The sky is perpetual twilight here - neither day nor night. In the distance, fragments of land float at wrong angles.

An ancient telescope points toward the horizon.

To the east, a doorway leads to what looks like living quarters.

[OBSERVATION: Beautiful and unsettling. Establishes the scope of the disaster.]

---

### Turn 5

> use telescope

You put your eye to the ancient telescope. The view is extraordinary - you can see all five regions from here, though distantly.

**North (Frozen)**: Snow-covered peaks. A temple structure. Steam rising from somewhere.

**South (Forest)**: Dense woods. Movement among the trees. Something large near a clearing.

**East (Water)**: Flooded buildings. Parts above water, parts below. Flickering lights beneath the surface.

**West (Fungal)**: Glowing vegetation in cave mouths. Spore clouds drifting.

**Further South (Settlement)**: Smoke from chimneys. Walls. Signs of human life.

[Flags set: telescope_overview_seen]
[DESIGN INPUT: Telescope provides initial overview without details - orientation, not spoilers]

---

### Turn 6

> go east

[Location: Keeper's Quarters]

Time seems frozen here. Dust motes hang motionless in the air. A meal sits on a table, half-eaten, as if the occupant just stepped away - but the food shows no decay.

Books lie open. A journal rests on a desk. Everything preserved in the moment of disaster.

You sense... something. A presence. Watching, but not threatening.

[Flag set: entered_keepers_quarters]
[Echo appearance chance: 30%]

---

### Turn 7

[Echo manifests - first appearance]

The air shimmers more intensely. A shape coalesces - humanoid, translucent, features unclear. It watches you with eyes that aren't quite there.

"...you came..." The voice is like an echo of an echo. "...finally... someone came..."

The Echo is here. (manifesting)

[OBSERVATION: First Echo encounter is significant. Establishes the tone of guidance.]

---

### Turn 8

> talk to echo

The Echo's form flickers, stabilizing slightly.

"I am... was... the Keeper's child. I was here when it happened. When the meridian shattered." The voice carries infinite weariness. "Now I am... this. Unable to act. Only to watch. To remember."

It looks at you. "You can move freely. You can touch things. You can... help. If you choose."

[Echo trust: 0 (initial)]
[Dialog topic unlocked: disaster]

---

### Turn 9

> ask about disaster

"The meridian was where five ley lines met. A convergence of magical power beyond measure." The Echo's form wavers with the memory. "My parent tried to contain it when something went wrong. They failed. I was... caught. Between."

"The blast shattered everything. Each region now suffers differently. The ice spreads. The water rose. The spores grow. The beasts changed. Only the human settlement survives, barely."

[Flag set: knows_disaster_cause]
[Dialog topics unlocked: regions, restoration]

---

### Turn 10

> ask about restoration

"I cannot act directly. I can only guide." The Echo's voice strengthens slightly. "But the waystone can be repaired. The crystals can be restored. Each healing in the broken world strengthens what remains of order."

"If you choose to help... I will share what I know."

[Dialog topics unlocked: waystone, crystals]

---

### Turn 11

> ask about waystone

"The waystone once connected all the ley points. Instant travel across the shattered lands." The Echo gestures toward the center of the Nexus below. "To repair it requires a fragment from each region's heart."

"A spore heart from the depths. An ice shard from the frozen peaks. A water pearl from the drowned archive. A fang freely given by the beast alpha. A seal granted by the human council."

[Flag set: knows_waystone_repair]
[Quest goal established: Gather 5 waystone components]

---

### Turn 12

> ask about crystals

"The crystal garden below once provided strength to travelers. Now it lies shattered." The Echo's form dims. "But each crystal can be restored - when healing occurs in the regions, the crystals respond. They remember what restoration feels like."

[Flag set: knows_crystal_purpose]

---

### Turn 13

The Echo's form begins to fade.

"I cannot maintain this form long. But I will appear again. In the quarters. Sometimes... elsewhere, when it matters."

The shape dissolves into shimmering air.

[Echo: communicating -> fading -> dormant]
[Cooldown: 5 turns before next possible appearance]

---

### Turn 14

> read journal

You open the Keeper's journal. The handwriting is neat, methodical.

*"Day 1,247: The readings are concerning. The convergence harmonics are off by 0.3%. Minor, but I've never seen drift before."*

*"Day 1,251: 0.7% now. I'm implementing containment protocols."*

*"Day 1,253: My child asked why I seem worried. I told them everything is fine. I lied."*

*"Day 1,254: 2.3%. This is beyond anything in the records. I've sent word to the other stations but the ley lines are disrupted. Messages may not arrive."*

*"Day 1,255: 8%. I'm activating the emergency dampeners. If this doesn't work..."*

The journal ends there. A partial phrase is scrawled on the next page: "Fire-that-gives-life and water-that-cleanses, un-"

[Flag set: has_temple_password_partial]
[Inventory: keepers_journal available to take]
[DESIGN INPUT: Journal provides backstory AND partial password - functional lore]

---

### Turn 15

> take journal

You carefully take the journal. It feels important.

[Inventory: keepers_journal added]

---

### Turn 16

> take cleaning supplies

You find preserved cloths and optical solutions - still usable despite the frozen time.

[Inventory: cleaning_supplies added]

---

### Turn 17

> go down

[Location: Crystal Garden]

You descend into a chamber of broken beauty. Crystal formations rise from the floor and hang from the ceiling - but most are shattered, dark, inert.

Five larger crystals form a rough circle in the center. Each is cracked, lightless. But you sense potential in them - a waiting.

One smaller crystal near the entrance glows faintly.

The Animator Crystal is here.
The Shattered Crystals are here. (0/5 restored)

---

### Turn 18

> examine shattered crystals

Five major crystals, each corresponding to a region:
- A blue-white crystal (Frozen Reaches) - dark
- A green crystal with internal movement (Fungal Depths) - dark
- A blue crystal that seems to ripple (Sunken District) - dark
- A tawny crystal with amber striations (Beast Wilds) - dark
- A warm golden crystal (Civilized Remnants) - dark

[DESIGN INPUT: Visual connection between crystals and regions. Player can track progress visually.]

---

### Turn 19

> take animator crystal

The small glowing crystal comes free easily. It pulses warmly in your hand.

[Inventory: animator_crystal added]
[Note: Required for Guardian repair in Civilized Remnants]

---

### Turn 20

> go west

[Location: Nexus Chamber]

You return to the central hub. The waystone's weak pulse seems almost... hopeful? No, that's projection. Isn't it?

---

## TRUNK B: Returning After Progress

[Time skip - player has explored regions, made progress]

### Turn 100 (approx)

[Location: Nexus Chamber]

You return to the Nexus after much travel. The waystone's pulse seems slightly stronger - or maybe you're imagining it.

[Player state: Has spore_heart (cured Spore Mother), beast_fang (Alpha Wolf gift). Has NOT completed other regions.]

---

### Turn 101

> go up, go east

[Location: Keeper's Quarters]

[Echo appearance chance: 50% (base 20% + trust bonus)]
[Roll: Success]

The air shimmers. The Echo appears, its form clearer than before.

"You have returned. And you carry... fragments of healing." Its voice is stronger. "I felt it. When you helped the Spore Mother. When the Alpha gave you trust. The meridian remembers kindness."

[Echo: dormant -> manifesting -> communicating]

---

### Turn 102

> ask about my progress

The Echo's form brightens slightly.

"Two fragments gathered. Two regions touched by your compassion." It pauses. "The ice still spreads unchecked. The waters hold secrets. The town struggles."

"But you have done more than most would. The crystals respond."

[DESIGN INPUT: Echo provides progress summary dynamically]

---

### Turn 103

> go to crystal garden

[Location: Crystal Garden]

The chamber is different now. Two of the five major crystals glow faintly.

The green crystal (Fungal Depths) pulses with soft bioluminescence.
The tawny crystal (Beast Wilds) gleams with warm amber light.

The other three remain dark.

[Crystal Garden progress: 2/5]

---

### Turn 104

> touch green crystal

The crystal responds to your touch. Warmth flows through you.

[Buff received: Slow poison/infection progression]
[Message: "The Spore Mother's blessing echoes through the ley lines. Your body resists corruption more easily."]

---

### Turn 105

> touch tawny crystal

Warmth again. A sense of connection.

[Buff received: +10 max health]
[Message: "The trust of beasts strengthens you. Your spirit can endure more."]

---

## BRANCH A: Echo Commitment Tracking

[Demonstrating Echo's awareness of commitments]

### Turn 110

[Location: Keeper's Quarters]
[Echo manifests]

> ask echo about my promises

The Echo's form shifts, as if consulting something unseen.

"The meridian remembers your words."

"You promised the scholar Aldric aid in the depths. This word was kept. He lives because you returned."

"You promised the wolf pack you would not harm their kin. This word holds."

"You promised the hunter Sira you would find help. This word... stands unfulfilled. She waits still, though her strength fades."

[OBSERVATION: Echo provides commitment summary - player guidance AND accountability]

---

### Turn 111

> I need to help Sira

The Echo nods slowly.

"Then go. The forest path awaits. But know - time grows short for those who bleed alone."

[Flag set: echo_reminded_sira_commitment]
[DESIGN INPUT: Echo can remind without nagging - guidance, not pressure]

---

## BRANCH B: Echo Response to Abandonment

[What happens when player breaks promises]

### Turn 150 (alternate)

[Player abandoned Sira - she died waiting]

[Location: Keeper's Quarters]
[Echo manifests]

The Echo's form is dimmer. Its voice carries sorrow.

"You have returned." A pause. "The hunter... Sira... she waited. Called out. No one came."

"Her friend in the settlement - the healer Elara - has heard. The grief spreads like ripples in still water."

[Echo trust: -1 for abandoned commitment]
[Flag set: sira_died_abandoned, elara_learned_of_sira_death]

---

### Turn 151

> I couldn't... there wasn't time

"There is always choice. Perhaps not time for everything, but choice in what we prioritize."

The Echo's form flickers.

"I do not judge. I only... remember. The meridian records all. What you do with that knowledge is yours."

[OBSERVATION: Echo is sad, not angry. Moral weight without moralizing.]

---

## BRANCH C: Waystone Repair Sequence

[Endgame - player has all five fragments]

### Turn 200 (approx)

[Location: Nexus Chamber]
[Player inventory: spore_heart, beast_fang, water_pearl, ice_shard, town_seal]

You stand before the damaged waystone, all five fragments in your possession.

> examine waystone

The waystone's pulse is stronger now, as if sensing what you carry. The five empty sockets seem to pull at you.

---

### Turn 201

> place spore heart

You set the spore heart - a crystallized fragment of the Spore Mother's essence - into the first socket.

The waystone hums. The socket glows green. Fungal patterns trace themselves along the stone for a moment before settling.

[Waystone: 1/5 fragments placed]

"The depths remember healing," the waystone seems to whisper.

---

### Turn 202

> place beast fang

The Alpha's fang - given freely in trust - slides into the second socket.

The waystone's hum deepens. Amber light joins the green. You hear, for just a moment, a distant howl of approval.

[Waystone: 2/5 fragments placed]

"The wild remembers trust."

---

### Turn 203

> place water pearl

The water pearl - retrieved from the drowned archive - clicks into place.

Blue light ripples across the waystone. You smell salt and ink and ancient paper.

[Waystone: 3/5 fragments placed]

"The deep remembers preservation."

---

### Turn 204

> place ice shard

The ice shard - extracted from the frozen caves - settles into its socket without melting.

White-blue light joins the others. Cold, but not hostile. The kind of cold that preserves rather than kills.

[Waystone: 4/5 fragments placed]

"The heights remember endurance."

---

### Turn 205

> place town seal

The town seal - earned through service to the Council - completes the circle.

Golden warmth joins the other lights. You hear distant voices - not words, but the sound of community.

[Waystone: 5/5 fragments placed]

"The remnants remember civilization."

The waystone flares with light. All five colors merge into something greater.

[Waystone: REPAIRED]

---

### Turn 206

The light fades. The waystone stands whole - cracks sealed, runes blazing with steady power.

And beside it...

The Echo stands. Not translucent. Not flickering. Solid. Present.

"It is... done." The voice is real now, not an echo of itself. "The meridian is not restored - the disaster cannot be undone - but the worst of the damage is healed. The ley lines flow again, weakly but truly."

The Echo looks at you with eyes that finally have color - amber, like their parent's must have been.

"I can exist now. Truly. Because of you."

[Echo: dormant -> permanent]
[Echo trust: +2 (waystone completion bonus)]
[Global effect: Fast travel between regions enabled]
[Global effect: Environmental spreads halted]
[Player buff: Meridian Blessing - minor protection in all regions]

---

### Turn 207

> talk to echo

The Echo smiles - the first genuine expression you've seen on that face.

"The waystone will carry you now. Touch it and think of a place - it will take you there."

"The work is not finished, of course. The Spore Mother still heals. The pack still protects. The town still struggles. But the bleeding has stopped. The world can mend, slowly, as worlds do."

"And I... I can help now. Not just watch. Not just remember. Act."

[OBSERVATION: Satisfying conclusion. Echo's transformation feels earned.]

---

## BRANCH D: Echo Trust Extremes

### High Trust Path (Trust 6+)

[Location: Keeper's Quarters]
[Echo trust: 6 (through extensive healing, saving NPCs, fulfilled commitments)]

The Echo appears. Its form is clearer than ever.

"There is something I have not told you." Its voice is quiet but steady. "I was not just the Keeper's child. I was... being trained. To take over. To be the next Keeper."

"My parent knew the convergence was unstable. They were trying to fix it. I was supposed to help but I was too young, too untrained. When it happened..."

The Echo's form wavers with emotion.

"I was caught between. Not quite dead. Not quite alive. Able to see but not touch. For years. Decades. Until you."

[Flag set: knows_echo_full_backstory]

---

### Low/Negative Trust Path (Trust -2 or below)

[Location: Keeper's Quarters]
[Echo trust: -2 (through cruelty, abandoned commitments, violence)]

[Echo appearance chance: 5% - barely manifests]

The air barely shimmers. For a moment you think you see a shape, but it doesn't coalesce.

A whisper, almost inaudible: "...I have nothing more to say to you..."

Then nothing.

[Echo: refusing to manifest]
[DESIGN INPUT: Echo doesn't lecture or condemn - it simply withdraws. More impactful than anger.]

---

### Recovering from Low Trust

[Trust: -2 -> attempting recovery]

Over time, through genuine healing (not just words), the Echo may appear again.

If player saves a major NPC or completes a significant restoration:

The air shimmers reluctantly. The Echo's form is faint, guarded.

"You have... done something good. The meridian noticed."

A pause.

"I noticed."

[Echo trust: -2 -> -1 (one act of healing)]
[OBSERVATION: Recovery is possible but slow. Actions matter more than apologies.]

---

## BRANCH E: Telescope Deep Use

### Using Telescope for Strategic Information

[After Frozen Reaches telescope is repaired, Nexus telescope gains detail]

### Turn X

> use telescope on fungal depths

The telescope focuses. With the Frozen Observatory repaired, the connection strengthens.

**Fungal Depths status:**
- Spore Mother: Healthy and spreading beneficial spores
- Aldric: Relocated to Civilized Remnants (if saved)
- Myconid colony: Thriving
- Infection spread: Contained to deep caves

"The depths heal," the Echo says softly from behind you.

---

### Turn X+1

> use telescope on sunken district

**Sunken District status:**
- Water levels: Stable
- Delvan: Alive, working in town undercity (if rescued)
- Archivist: Fading but peaceful, archive preserved
- Garrett: Survived, left the region (if rescued)

"Some survived. Not all. But some. That matters."

---

## Summary Tables

### Design Inputs Generated

| ID | Input | Value | Notes |
|----|-------|-------|-------|
| DI-NX-1 | Nexus is absolutely safe | No combat, no hazards, no time pressure | Sanctuary design |
| DI-NX-2 | Echo appearance is trust-gated | Base 20% + 10% per trust level | Rewards relationship building |
| DI-NX-3 | Echo provides commitment summaries | Lists all active/fulfilled/broken commitments | Player guidance and accountability |
| DI-NX-4 | Crystal restoration is visual | Each crystal lights up when region healed | Progress tracking |
| DI-NX-5 | Crystal buffs are cumulative | Each restored crystal provides permanent buff | Rewards exploration |
| DI-NX-6 | Waystone repair is ceremonial | Each fragment placed with narrative moment | Endgame weight |
| DI-NX-7 | Echo becomes permanent on waystone repair | Transformation from spectral to solid | Earned reward |
| DI-NX-8 | Journal contains partial password | "Fire-that-gives-life and water-that-cleanses, un-" | Functional lore |
| DI-NX-9 | Echo withdraws at very low trust | Doesn't lecture, simply stops appearing | Impactful consequence |
| DI-NX-10 | Trust recovery through actions only | Words don't restore trust, healing deeds do | Consistent with themes |
| DI-NX-11 | Telescope syncs with Frozen Observatory | More detail available when both functional | Cross-region reward |
| DI-NX-12 | Echo reveals full backstory at trust 6 | Was training to be next Keeper | Deep lore reward |

### Questions Raised

| ID | Question | Proposed Resolution |
|----|----------|---------------------|
| Q-NX-1 | Should Nexus have any combat? | No - guaranteed safe zone. Magical wards repel hostile creatures. |
| Q-NX-2 | Can Echo appear outside Nexus? | Rarely, at critical moments (player about to make irreversible choice, major NPC dying). Brief, cryptic guidance. |
| Q-NX-3 | What if player loses all Echo trust? | Echo stops appearing. Guidance lost but game completable. Some endings locked (Echo-dependent). |
| Q-NX-4 | What happens to Echo if player never repairs waystone? | Echo remains spectral, trapped. Sad ending. Environmental spreads continue. |
| Q-NX-5 | Can player store items in Nexus safely? | Yes - nothing despawns. Frozen time preserves everything. |
| Q-NX-6 | Does Echo know about assassination in Civilized Remnants? | Yes - always knows, even if undiscovered by NPCs. Trust penalty even without discovery. |

### Mechanisms Required

| Mechanism | Status | Notes |
|-----------|--------|-------|
| Echo appearance probability | Needed | Base + trust modifier |
| Commitment tracking storage | Needed | Global flags for all commitments |
| Crystal restoration tracking | Needed | 5 boolean flags + visual state |
| Crystal buff application | Needed | Permanent player buffs |
| Waystone repair ceremony | Needed | Multi-step ritual with narrative |
| Echo trust tracking | Needed | -5 to +10 scale |
| Telescope region queries | Needed | Dynamic information based on game state |
| Fast travel (when waystone repaired) | Needed | Destination selection UI |

### Gameplay Observations

**Positive:**
- Safe hub provides genuine rest from other regions' pressures
- Echo relationship is engaging without being demanding
- Crystal visual progress is satisfying
- Waystone repair ceremony feels appropriately climactic
- Trust system creates meaningful long-term consequences
- Journal and partial password are functional lore (not just flavor)

**Concerns:**
- Hub might feel empty early game (few reasons to stay)
- Echo appearance RNG might frustrate players wanting guidance
- Very low trust player might feel punished (but that's intentional consequence)

**Potentially Boring Sections:**
- Early visits before much progress (but brief)
- Waiting for Echo to appear (but not required)

**Frustrating Sections:**
- None identified - Nexus is designed as relief from frustration

---

## Paths Not Yet Explored

- [ ] Player tries to attack Echo (nothing happens - incorporeal)
- [ ] All five crystals restored - full buff suite
- [ ] Echo appearances at critical moments in other regions
- [ ] What happens if player brings hostile creature to Nexus (wards repel)
- [ ] Saved NPCs relocating to Nexus (Aldric, potentially others)
- [ ] Game ending variations based on waystone state
- [ ] Echo dialog for every possible combination of commitment states
