# Beast Wilds Walkthrough

## Setup

**Entry assumption:** Player arrives from Meridian Nexus. Has basic equipment (light source, some gold). No special skills yet. Health 100.

**Key NPCs and their timers:**
- Hunter Sira: ~8 turns before death from bleeding
- Bear Cubs: ~30 turns before death from wasting sickness
- Wolf Pack: No timer, but hostile until fed

**Branch structure:**
```
TRUNK: Entry and exploration of Forest Edge
├── A: Wolf encounter first (east)
│   ├── A1: Feed wolves (diplomatic)
│   │   └── A1a: Full domestication path
│   ├── A2: Fight wolves (violent)
│   └── A3: Flee wolves
├── B: Bear den first (south)
│   ├── B1: Promise to help cubs
│   │   └── B1a: Return with herbs (cross-region)
│   ├── B2: Attack bear
│   └── B3: Flee and avoid
├── C: Bee grove first (west)
│   ├── C1: Trade approach
│   ├── C2: Take honey (triggers attack)
│   └── C3: Observe and leave
├── D: Find Sira (south through bear den)
│   ├── D1: Help Sira immediately
│   ├── D2: Promise to help, leave
│   └── D3: Ignore Sira
└── E: Spider nest (through wolf clearing)
```

---

## TRUNK: Entry and Forest Edge Exploration

### Turn 1
[Location: Nexus Chamber]
[Player state: Health 100, no conditions, basic inventory]

> go south

You leave the shimmering unreality of the Nexus and follow a path that descends into dense woodland. The air changes - warmer, humid, alive with sounds. You emerge at the Forest Edge.

[Location changed: Forest Edge]

---

### Turn 2
[Location: Forest Edge]

> look

The forest presses close here, trees ancient and gnarled. Claw marks score the bark at regular intervals - territorial markings. Game trails thread through the undergrowth, and a watchful silence hangs over everything.

Exits: North (back to Nexus), East (deeper into forest), South (darker, denser growth), West (faint humming sound).

You notice several items nearby: a haunch of venison hanging from a branch, some tracking equipment scattered near a tree, and a leather-bound journal.

[OBSERVATION: Good environmental storytelling. The venison placement feels convenient but acceptable - could be from a previous hunter's camp]

---

### Turn 3

> take venison

You take the venison. It's fresh, still cool.

[Inventory: venison added]

---

### Turn 4

> take journal

You take the hunter's journal.

[Inventory: hunter's journal added]

---

### Turn 5

> read journal

You flip through the worn pages. The handwriting is cramped but legible:

*"Wolf pack claims the clearing to the east. Four wolves, led by a massive alpha. They're hungry - that's key. Hunger makes beasts predictable. Or dangerous."*

*"Don't go south carelessly. Dire bear has a den there. Saw cubs with her, but they looked sickly. She won't let anything near them."*

*"Spider nest beyond the wolf territory. Bad business. Webs everywhere. I avoid it."*

*"The bees to the west are strange. Queen watches but doesn't attack unless you threaten the hive. Saw her accept flowers from a traveler once. Gave honey in return."*

[Flag set: knows_wolf_info, knows_bear_info, knows_spider_warning, knows_bee_trade_hint]
[DESIGN INPUT: Journal serves as hint system. Good placement at entry point.]

---

### Turn 6

> take tracking equipment

You gather the tracking equipment - snares, markers, and a worn compass.

[Inventory: tracking equipment added]
[MECHANISM NOTE: Tracking equipment needs tracking skill to use effectively. Without skill, it's just items.]

---

## BRANCH A: Wolf Encounter (Going East)

### Turn 7

> go east

You push through the undergrowth toward the clearing. The trees thin, and you step into an open space surrounded by dense forest.

Yellow eyes gleam from the shadows. A low growl rolls across the clearing.

A massive winter wolf steps forward - the alpha, easily the size of a pony. Behind it, three grey wolves fan out, cutting off retreat.

[Location: Wolf Clearing]
[Combat warning: Wolves hostile. One turn before attack.]
[MECHANISM: Territorial warning - player has one turn to act]

---

### Turn 8 (Branch A1: Feed wolves)

> give venison to alpha wolf

You slowly extend the venison, keeping your movements deliberate. Non-threatening.

The alpha's nostrils flare. The growling stops. It takes a cautious step forward, then another. The grey wolves hold position, watching their leader.

The alpha snatches the venison from your hand and retreats several paces to eat. The other wolves remain tense but don't attack.

[Venison removed from inventory]
[Alpha Wolf: hostile -> wary]
[Grey wolves: hostile -> wary (following alpha)]
[Alpha Wolf gratitude: 0 -> 1]
[DESIGN INPUT: One feeding moves from hostile to wary. This feels right - not instant friendship, but recognition]

---

### Turn 9

> look

The Wolf Clearing is trampled earth and scattered bones. The alpha wolf tears at the venison while the grey wolves watch you with wary eyes. They're no longer growling, but they haven't relaxed either.

The alpha finishes eating and looks at you. There's intelligence in those yellow eyes. And hunger - still hunger.

[OBSERVATION: The pack needs more than one meal. This creates natural return visits or resource hunting]

---

### Turn 10

> wait

You stand still, making no threatening moves.

The alpha studies you. After a long moment, it sits. The grey wolves follow suit.

Something has shifted. They're not your friends, but they're not hunting you either.

[Pack remains wary]
[DESIGN INPUT: Waiting/non-aggression doesn't advance relationship but doesn't harm it]

---

### Turn 11

> go west

You back away slowly toward the forest edge. The wolves watch but don't follow.

[Location: Forest Edge]

---

### Turn 12

> go west

You follow the humming sound westward. The forest opens into a grove dominated by an enormous structure of wax and honey - a hive the size of a house.

Giant bees move in organized patterns. On a central platform, an enormous queen bee regards you with compound eyes. She doesn't attack.

[Location: Beehive Grove]
[Bee Queen: neutral]

---

### Turn 13

> examine queen

The Bee Queen is magnificent - iridescent wings folded, antennae twitching. She's easily as intelligent as the alpha wolf, maybe more so. She watches your every move but shows no aggression.

You notice a cache of royal honey behind her, glowing faintly gold. Taking it without permission seems unwise.

[OBSERVATION: Player needs to have read journal or experiment to know about flower trade]

---

### Turn 14

> talk to queen

The queen's antennae wave. She doesn't speak, but there's... expectation? She seems to be waiting for something.

[DESIGN INPUT: Without flowers, no trade possible. Player must return from other regions]
[QUESTION: Should there be a way to communicate "I'll bring flowers later"? Commitment to bee queen?]

---

### Turn 15

> go east

You return to the Forest Edge, the humming fading behind you.

[Location: Forest Edge]

---

## BRANCH A1a: Full Wolf Domestication (Continued)

[Resuming from Turn 11, player needs more food]

### Turn 16

> go south

The forest grows darker and denser. You smell musk and decay. This is predator territory.

You emerge near a cave mouth. Massive claw marks score the rocks. From within, you hear a low, threatening rumble.

A dire bear emerges - twice the size of any bear you've seen. Behind her, in the cave mouth, two small shapes lie still. Cubs.

The bear's eyes fix on you. She charges.

[Location: Predator's Den]
[Combat warning: Dire Bear hostile. Attack imminent.]
[OBSERVATION: No warning turn here - bear is protecting cubs, more aggressive than wolves]

---

### Turn 17

> run north

You turn and sprint. The bear roars behind you, but she doesn't pursue far - she won't leave her cubs unprotected.

You burst back into the Forest Edge, heart pounding.

[Location: Forest Edge]
[DESIGN INPUT: Bear won't pursue beyond den. Maternal instinct keeps her close to cubs.]

---

### Turn 18

> go south

[Player can return - let's explore a different approach]

You approach the den again, more cautiously this time.

The dire bear emerges, blocking the cave. She growls but doesn't charge immediately. Her eyes flick to the cave, then back to you.

[Combat warning: Bear hostile. One turn before attack.]
[OBSERVATION: Different behavior on return? Or should it be the same? Probably same aggression - she doesn't know player is different]

---

### Turn 19

> examine cubs

From your distance, you can see the cubs more clearly now. They're thin, fur patchy, breathing labored. Something is wrong with them.

The bear growls louder. You're too close.

[Flag set: knows_cubs_sick]

---

### Turn 20

> I'll help your cubs

[COMMITMENT TRIGGER: "I'll help your cubs"]

You speak slowly, calmly. "I'll help your cubs. I'll find medicine."

The bear's growl falters. She studies you with eyes that hold more understanding than a beast should have.

After a long moment, she takes a step back. Not friendly - but not attacking. She looks at the cubs, then at you, then south toward the trail leading away from her den.

[Commitment created: bear_cubs_commitment, status: pending]
[Hope extends survival: Cubs timer extended +5 turns (30 -> 35)]
[Bear: hostile -> (guarded pause)]
[DESIGN INPUT: Bear understands intent. Doesn't become friendly but gives player chance. Looking south = hint toward herbs.]

---

### Turn 21

> go south

The bear watches but allows you to pass. The trail leads through dense growth to a wider path - the Southern Trail.

A figure lies against a tree. A woman, clutching her leg. Blood seeps through her fingers.

[Location: Southern Trail]
[Actor present: Hunter Sira]

---

### Turn 22

> examine sira

Hunter Sira is in bad shape. A deep gash on her leg bleeds steadily, and the leg itself bends at a wrong angle. Her face is pale, but her eyes are sharp with pain and wariness.

"Another one," she rasps. "Come to finish what the beasts started?"

[Sira conditions: bleeding (damage 3/turn), leg_injury (cannot move)]
[Sira timer: ~8 turns remaining without treatment]

---

### Turn 23

> ask sira about injury

Sira grimaces. "The beasts got my partner. I barely escaped. My leg..." She gestures at the twisted limb. "I can't walk far."

[Flag set: knows_sira_backstory]

---

### Turn 24

> I'll find a healer for you

[COMMITMENT TRIGGER: "I'll find a healer"]

"I'll find a healer for you. There must be someone."

Something shifts in Sira's expression. Hope, carefully guarded.

"There's a healer in the town to the south. Elara. Tell her Sira sent you - she owes me." She winces. "Hurry."

[Commitment created: sira_commitment, status: pending]
[Hope extends survival: Sira timer extended +4 turns (8 -> 12)]
[Flag set: knows_elara_connection]

---

### Turn 25

> go south

You follow the Southern Trail toward the town.

[Travel sequence to Civilized Remnants - abbreviated]

You arrive at the Town Gate. Guards eye you suspiciously but let you pass.

[Location: Town Gate, Civilized Remnants]

---

### Turns 26-30 (Abbreviated: Getting supplies)

> go south (to Market Square)
> go east (to Healer's Sanctuary)

You find Healer Elara among her herbs and patients.

> ask elara about sira

"Sira? Is she hurt?" Elara's concern is immediate. "That stubborn woman. What does she need?"

> tell her about the leg and bleeding

Elara quickly gathers bandages and a splint, plus a small vial. "Bloodmoss tincture for the bleeding. The splint for the leg. I would come myself, but..." She gestures at her patients. "Tell her she still owes me dinner."

[Received: bandages, splint, bloodmoss_tincture]
[DESIGN INPUT: Elara doesn't need payment for Sira - the connection matters]

---

### Turn 31

> ask elara about healing herbs for animals

"Sick animals? What symptoms?"

You describe the bear cubs - the patchy fur, the labored breathing.

"Wasting sickness. I've seen it in livestock since the disaster. Here-" She pulls herbs from a shelf. "These should help. If you can get close enough to treat them."

[Received: healing_herbs]
[DESIGN INPUT: Elara provides both items - this makes the trip efficient. Is this too convenient? Perhaps she should only offer one freely, requiring payment or trust for the other]

---

### Turns 32-35 (Return journey)

[Travel back to Beast Wilds - Southern Trail]

---

### Turn 36
[Location: Southern Trail]

Sira is still alive, but barely. Her face is grey, breathing shallow.

> use bandages on sira

You press the bandages to her wound, applying pressure.

> give bloodmoss tincture to sira

Sira drinks the tincture. Almost immediately, the bleeding slows.

[Sira: bleeding condition removed]
[Sira state: injured -> recovering]

---

### Turn 37

> use splint on sira's leg

Working carefully, you set her leg and bind it with the splint. Sira hisses in pain but holds still.

"You came back," she says. "I wasn't sure you would."

[Sira: leg_injury stabilized]
[Commitment fulfilled: sira_commitment]
[Sira gratitude: +4 (base +2, commitment bonus +2)]
[Sira trust: +2]

---

### Turn 38

> ask sira about tracking

"You want to learn to track?" She studies you appraisingly. "You saved my life. I can teach you. Won't be quick - I can't move much yet - but I can teach."

[Service available: teach_tracking]
[DESIGN INPUT: Teaching happens over time? Or instant? Suggest: requires Sira to be healthy, not just recovering. Creates reason to either wait or return.]

---

### Turn 39

> go north

You return to the Predator's Den. The dire bear is waiting, watching the trail.

[Location: Predator's Den]

---

### Turn 40

> give healing herbs to cubs

You move slowly toward the cave, herbs extended. The bear tenses but doesn't attack.

You reach the cubs. They're weak, barely responsive. You administer the herbs, pressing them to accept the medicine.

Minutes pass. Then one cub stirs. Blinks. Lifts its head.

The bear makes a sound - not a growl. Something else. She moves to her cubs, nuzzling them.

[Commitment fulfilled: bear_cubs_commitment]
[Bear: hostile -> grateful]
[Bear gratitude: +4 (base +2, commitment bonus +2)]
[Cubs: wasting_sickness condition improving]
[OBSERVATION: This feels earned. The cross-region journey, the commitments kept - it's satisfying]

---

### Turn 41

The bear turns to you. Her massive head dips - acknowledgment? Respect?

She steps aside from the cave entrance. You could rest here now, if you needed to.

[Bear den: now safe rest location]
[Bear alliance: intimidates other predators in region]

---

## Branch A2: Fighting the Wolves

[Branching from Turn 8]

### Turn 8-ALT

> attack alpha wolf

You draw your weapon and charge.

The alpha snarls and meets you head-on. The grey wolves circle.

[Combat initiated: Player vs Wolf Pack]

---

### Combat Round 1

Alpha wolf bites: 15 damage.
Grey wolf 1 flanks: 8 damage.
Grey wolf 2 flanks: 7 damage.
Grey wolf 3 circles, looking for opening.

Player attacks alpha: 10 damage.

[Player health: 100 -> 70]
[Alpha health: 60 -> 50]

---

### Combat Round 2

Alpha wolf: 14 damage.
Grey wolves coordinate: 22 damage total.
Player attacks alpha: 12 damage.

[Player health: 70 -> 34]
[Alpha health: 50 -> 38]
[OBSERVATION: This is brutal. Pack tactics are devastating. Player needs to be well-prepared or flee.]

---

### Combat Round 3

> flee west

You break and run. The wolves pursue briefly but don't follow beyond their territory.

[Player health: 34]
[Location: Forest Edge]
[Wolves: remain hostile]
[DESIGN INPUT: Combat is appropriately punishing. Player needs healing or will die to the bear.]

---

## Branch B: Bear Den First (from Turn 6)

### Turn 7-B

> go south

[Same as Turn 16-21 in Branch A, reaching Sira]

---

## Branch D1: Help Sira Immediately (Without Promise)

### Turn 22-D1

[Player finds Sira at Turn 22]

> give bandages to sira

"You... you're helping me?" Sira's surprise is evident. You bind her wound as best you can.

The bleeding slows but doesn't stop completely.

[Sira: bleeding reduced but not cured]
[No commitment made - player acted directly]
[Sira gratitude: +2 (helped without promise)]

---

### Turn 23-D1

> examine sira's leg

The leg is broken. Without a proper splint, she can't walk.

[OBSERVATION: Player without supplies can stabilize but not cure. Creates reason to go to town anyway.]

---

## Branch D3: Ignore Sira

### Turn 22-D3

> go south

You pass the injured hunter without stopping. Her eyes follow you.

"Wait..." she calls weakly. "Please..."

You keep walking.

[Location: approaches Town Gate]
[Flag set: ignored_sira]
[No commitment made - no penalty yet]

---

### Turn 30-D3 (Later)

[If player returns after Sira's timer expires]

The Southern Trail is quiet. Too quiet.

Where the hunter lay, there's only bloodstained earth and drag marks leading into the undergrowth. Something found her.

[Sira status: dead]
[Flag set: sira_died_alone]
[DESIGN INPUT: No commitment means no abandonment penalty, but Sira is still dead. The Echo won't comment on broken promises, but...]

---

## Branch E: Spider Nest

### Turn 45 (After wolf domestication)
[Location: Wolf Clearing]
[Wolf pack: friendly, following player]

> go east

You push deeper into the forest. The wolves follow, but as the trees grow thicker and webs appear, they slow.

The alpha growls softly. The pack won't go further.

[Wolves: will not enter Spider Nest Gallery]
[DESIGN INPUT: Even friendly wolves won't enter spider territory. Creates choice - bring wolves or explore spiders.]

---

### Turn 46

> go east

You leave the wolves behind and push into the web-covered darkness.

Strands of silk catch at your clothes. The light fades. From everywhere and nowhere comes the sound of skittering.

[Location: Spider Nest Gallery]
[Light required - assuming player has light source]

---

### Turn 47

> look

Your light reveals a nightmare of webs. Cocoons hang from the ceiling - some empty, some not. The walls crawl with smaller spiders.

At the center of the gallery, a massive spider crouches - the queen, easily the size of a cart. Her many eyes reflect your light.

She's not waiting to see if you're friendly.

[Combat imminent: Spider Queen + 2 Giant Spiders]
[Environmental: Spiders have combat bonus in webs]

---

### Combat Round 1

Spider Queen spits venom: 12 damage + poison condition applied.
Giant Spider 1 sprays web: Player immobilized for 1 turn.
Giant Spider 2 bites: 7 damage.

Player cannot act (webbed).

[Player health: 100 -> 81]
[Player conditions: poisoned, webbed]

---

### Combat Round 2

Poison tick: 5 damage.
Spider Queen bites: 14 damage.
Giant spiders: 13 damage total.
Player breaks free of web.

Player attacks Spider Queen: 10 damage.

[Player health: 81 -> 49]
[Spider Queen health: 80 -> 70]
[OBSERVATION: Spider combat is very dangerous. Poison + web combo is brutal.]

---

### Turn 48

> flee west

You break and run, trailing webs. The spiders pursue briefly but won't leave their territory.

[Player health: 49, poisoned]
[Location: Wolf Clearing]

The wolves greet you with concern. The alpha sniffs at the webs clinging to you.

[DESIGN INPUT: Spider nest is the "hard combat" option of Beast Wilds. No diplomacy, just fight or avoid.]

---

## Branch C2: Take Honey Without Permission

### Turn 13-C2
[Location: Beehive Grove]

> take honey

You reach for the glowing cache of royal honey.

The queen's wings buzz - a warning.

You grab a honeycomb anyway.

The hive erupts. Thousands of bees swarm toward you, a living cloud of fury.

[Combat initiated: Bee Swarm]
[Bee Queen: neutral -> hostile]
[OBSERVATION: This should be very clear it's a bad idea. The queen's warning is the last chance.]

---

### Combat Round 1

Bee Swarm: 15 area damage + poison condition.
Player attacks swarm: minimal effect (swarm dispersed, hard to damage).

[Player health: 100 -> 85, poisoned]
[Swarm health: 100 -> 95]

---

### Turn 14-C2

> flee east

You run, bees pursuing. They sting relentlessly until you're well away from the grove.

[Player health: 85 -> 55 (ongoing stings during retreat)]
[Location: Forest Edge]
[Bee Queen: permanently hostile]
[Royal honey: player has 1 honeycomb but grove permanently damaged]
[DESIGN INPUT: Violence destroys the renewable resource. Player got one honey but will never get more.]

---

## Summary Tables

### Design Inputs Generated

| ID | Input | Value | Notes |
|----|-------|-------|-------|
| DI-W-1 | One feeding moves wolf from hostile to wary | Yes | Feels right - gradual trust building |
| DI-W-2 | Bear understands commitment intent | Yes | Gives player chance, looks south as hint |
| DI-W-3 | Hope extends bear cubs survival | +5 turns | Allows cross-region trip |
| DI-W-4 | Hope extends Sira survival | +4 turns | Barely enough for town trip |
| DI-W-5 | Sira connection to Elara | "She owes me" | Provides free healing supplies |
| DI-W-6 | Bear den becomes safe rest | After healing cubs | Meaningful reward |
| DI-W-7 | Wolves won't enter spider territory | Yes | Forces choice between companions and exploration |
| DI-W-8 | Spider combat has no diplomatic option | Confirmed | Contrast with wolves/bear |
| DI-W-9 | Bee grove permanently damaged by violence | Yes | Stakes for peaceful approach |
| DI-W-10 | Journal at Forest Edge provides hints | Yes | Critical guidance |

### Questions Raised

| ID | Question | Proposed Resolution |
|----|----------|---------------------|
| Q-NEW-W-1 | How does player get more food for wolves? | Need hunting mechanic OR food from other regions OR multiple venison at Forest Edge |
| Q-NEW-W-2 | Can player make commitment to bee queen? | Probably yes - "I'll bring flowers" should create commitment |
| Q-NEW-W-3 | Should Elara provide both healing_herbs and Sira supplies freely? | Maybe only one free, other requires trust or payment |
| Q-NEW-W-4 | Does Sira teaching require her to be healthy or just recovering? | Suggest healthy - creates reason to wait or return |
| Q-NEW-W-5 | How do wolves + Sira coexist? | Reconciliation dialog when trust >= 2 AND wolves companion |
| Q-NEW-W-6 | What happens to spider territory if queen killed? | Spiders scatter, area becomes safe but no more loot spawns |

### Mechanisms Required

| Mechanism | Status | Notes |
|-----------|--------|-------|
| Pack dynamics (followers mirror alpha) | Needed | Wolves, spiders both use this |
| Territorial warning (one turn before attack) | Needed | Wolves have it, bear doesn't |
| Commitment tracking | Needed | Multiple commitments tested here |
| Hope extends survival | Needed | Different amounts per NPC |
| Cross-region item dependencies | Confirmed working | Herbs from Remnants, flowers from multiple regions |
| Web immobilization | Needed | Spiders use it |
| Swarm damage | Needed | Bees use it |

### Gameplay Observations

**Positive:**
- Commitment system feels meaningful - returning with herbs after promising is satisfying
- Pack dynamics create interesting tactical choices
- Violence has real consequences (bee grove, wolf domestication)
- Hunter Sira provides emotional stakes and useful rewards
- Cross-region dependencies create exploration motivation

**Concerns:**
- Wolf feeding might feel grindy - need enough food sources
- Sira timer (8 turns) very tight for cross-region trip without promise
- Spider combat may be too punishing for unprepared players
- Bear's initial aggression might kill players before they can promise

**Boring Sections:**
- Travel between regions (could use fast travel after first time)

**Frustrating Sections:**
- Finding bear cubs sick but having no way to help yet (cross-region dependency)
- Sira's timer if player doesn't know about Elara connection

---

## Paths Not Yet Explored

- [ ] Full wolf domestication to alpha_fang gift (trust 5+)
- [ ] Wolf pack assisting in combat
- [ ] Sira + wolves reconciliation
- [ ] Bee queen trade completion (requires flowers from 3 regions)
- [ ] Spider nest full clear
- [ ] Bear becoming vengeful (cubs die)
- [ ] Sira withdrawal response (hint about Elara without commitment)
