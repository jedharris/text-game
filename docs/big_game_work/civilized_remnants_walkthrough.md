# Civilized Remnants Walkthrough

## Purpose

This walkthrough explores a region with:
- **Social hazards** instead of environmental dangers - reputation damage, guard hostility, NPC distrust
- **Moral complexity** - council dilemmas with no clear "right" answers
- **Dual reputation tracks** - surface town vs undercity, can conflict
- **Skill gating** - herbalism required for garden access, affects multiple systems
- **Cross-region consequences** - this is where broken promises from elsewhere manifest

This contrasts with all other regions: no combat threats, no environmental dangers, no dying NPCs requiring rescue.

## Notation

- `[MECHANISM: X]` - Requires engine/behavior support
- `[DESIGN INPUT: X]` - Decision made during simulation
- `[QUESTION: X]` - Ambiguity needing resolution
- `[OBSERVATION: X]` - Gameplay quality note

## Initial State

- Player arrives from Beast Wilds (southern_trail)
- Health 100, no conditions
- Has: rusty_sword, torch, 25 gold
- No companions (wolves must be left outside)
- No town reputation yet

---

## TRUNK: Entry and Initial Exploration

### Turn 1
[Location: Southern Trail (Beast Wilds)]

> go south

You follow the trail toward a wooden palisade. Smoke rises from within. This must be the settlement - the Civilized Remnants.

A gatehouse blocks entry. Two guards watch your approach.

[Location: Town Gate]

Gate Guard stands at the entrance, hand near weapon. "Hold. State your business and submit to inspection."

A second Guard watches from the wall above.

[OBSERVATION: Immediately establishes different tone - social gatekeeping, not environmental danger]

---

### Turn 2

> submit to inspection

The guard looks you over carefully, checking your skin for fungal marks, examining your gear.

"No visible infection. No contraband that I can see." He relaxes slightly. "You may enter. Welcome to the Remnants. Cause trouble and you'll leave feet first."

[Town reputation: 0 (neutral)]
[Access granted: market_square]
[Flag set: passed_gate_inspection]

---

### Turn 3

> go south

You pass through the gate into the settlement.

[Location: Market Square]

The Market Square bustles with cautious life. Vendor stalls ring a dry fountain. You see:
- Herbalist Maren tending a small stall of plants and potions
- Weaponsmith Toran at a portable forge
- Curiosity Dealer Vex in a shadowy corner booth
- A few militia members watching the crowd

Exits: North (gate), East (building with herb symbol), West (large official building), South (hall with broken statue visible), Down (you notice nothing obvious)

[DESIGN INPUT: Undercity entrance is hidden - "down" shows nothing until discovered]

---

### Turn 4

> talk to herbalist

Herbalist Maren looks up from sorting dried plants. "A customer? Or just looking?"

She has healing potions (15 gold), antidotes (20 gold), and bandages (5 gold) visible on her stall.

[OBSERVATION: Commerce is immediately available. Sets economic tone.]

---

### Turn 5

> ask about herbalism

"Herbalism? It's knowing plants - which heal, which kill, and how close those two things are." She eyes you appraisingly. "I could teach you the basics, for a price. Fifty gold, or bring me a rare plant worth my time."

[Service available: Basic herbalism (50 gold or rare plant)]
[Requires: Trust 2 (currently 0)]

"Of course, I'd need to know you a bit better first. Trust matters when teaching someone to handle poisons."

[OBSERVATION: Service gating through trust, not just money. Creates relationship arc.]

---

### Turn 6

> ask how to earn trust

"Simple enough. Be a good customer. Don't cause trouble in town. Help folks when you can." She shrugs. "The usual ways people prove themselves."

[MECHANISM: Trust increases through: purchases (small), completing helpful actions (medium), major quests (large)]

---

### Turn 7

> buy healing potion

You pay 15 gold. Maren hands over a small vial of reddish liquid.

[Gold: 25 -> 10]
[Inventory: healing_potion added]
[Maren trust: 0 -> 0.5]

"Pleasure doing business."

---

### Turn 8

> go east

You walk toward the building marked with the herb symbol.

[Location: Healer's Sanctuary]

The air smells of clean medicine and dried herbs. Bundles hang from every beam. Mortar and pestle sounds come from a back room.

Healer Elara emerges, wiping her hands. "A visitor. Are you injured, or seeking something else?"

A door leads to a garden behind the building.

---

### Turn 9

> talk to elara

Elara studies you with tired but kind eyes. "I'm the healer here. I treat wounds, cure diseases, train those who want to learn. My prices are fair - I turn no one away, but supplies are scarce."

[Services available: Heal wounds (10 gold), Cure poison (20 gold or rare herbs), Cure disease (30 gold), Advanced herbalism teaching (trust 3 required)]

---

### Turn 10

> ask about garden

"My garden is behind the sanctuary. It contains everything I need for healing - and some things that could kill if mishandled." She looks at you seriously. "Without proper knowledge, I can't let you wander in there. One wrong touch and..." She makes a dying gesture.

[Garden access: Requires herbalism skill OR Elara's supervision]
[DESIGN INPUT: Garden is skill-gated. Creates meaningful progression.]

---

### Turn 11

> ask about herbalism training

"True herbalism goes beyond what Maren teaches. She knows identification and basic handling. I can teach you the full art - safe harvest of deadly plants, preparation of complex cures, reading a plant's properties by touch and smell."

She pauses. "But I only teach those I trust. Help me. Help my patients. Prove you understand that healing matters."

[Advanced herbalism: Trust 3 required (currently 0)]
[OBSERVATION: Two herbalism tiers - Maren's basic (trust 2), Elara's advanced (trust 3). Creates clear progression.]

---

### Turn 12

> go west

[Location: Market Square]

> go west

[Location: Council Hall]

The hall is dim, lit by oil lamps. Three people sit at a raised table, debating intensely. They fall silent as you enter.

Councilor Hurst (pragmatic expression), Councilor Asha (idealistic fire in her eyes), and Councilor Varn (calculating gaze) watch you.

"A newcomer," Hurst says. "Looking for something, or just observing our difficulties?"

---

### Turn 13

> ask about council

Varn speaks. "We govern what remains. Three voices, three philosophies. We debate, we compromise, we somehow keep this town alive."

Asha adds, "The town faces decisions every day. We could use capable hands."

Hurst nods. "If you're willing to help, speak up. We have problems that need solving."

[Council quests available - will present dilemmas when examined]

---

### Turn 14

> ask about problems

Hurst slides forward a sheaf of notes. "Pick your poison. We have:

**Infected Refugees**: People arrived from the wilds with fungal infection. Medicine is scarce. We need someone to decide their fate - or find another solution.

**Dangerous Traders**: Outsiders are camped near town. Good goods, but something feels wrong. We need assessment.

**Criminal Punishment**: A thief was caught. First offense. Resources are tight. What do we do with him?"

[OBSERVATION: All three dilemmas have no clear right answer - this is the design intent.]

---

### Turn 15

> ask about infected refugees

Asha leans forward. "A family. Parents, two children. They walked through the Fungal Depths to get here. They're showing early infection symptoms."

Hurst cuts in. "We have limited medicine. Using it on outsiders means our own people may suffer later."

Varn adds, "They have trade goods. If they survive, they could contribute."

[Dilemma: Infected Refugees]
[Options visible: Exile, Treat, Investigate/Quarantine]

---

### Turn 16

> ask about quarantine option

"We could quarantine them," Asha says carefully. "Keep them isolated while someone seeks a better solution. But that requires finding a cure, not just managing the symptoms."

Hurst frowns. "Who would seek this cure? We can't spare guards. It would have to be an outsider willing to venture to the Fungal Depths and find... something."

[DESIGN INPUT: "Investigate" option requires player to actually solve the problem, not just vote. Makes it more than a dialog choice.]

[MECHANISM: If player chooses quarantine, they're committing to finding a cure - links to Fungal Depths content]

---

### Turn 17

> what would cure fungal infection?

The councilors look at each other. Elara's voice comes from the doorway - she's been listening.

"The Spore Mother's blessing could cure them. Or her spore-song could strengthen their resistance. But reaching her..." She shakes her head. "The Fungal Depths are deadly."

[Flag set: knows_spore_mother_cure]
[Cross-region connection established]

---

### Turn 18

> I'll investigate. Quarantine them while I search for a cure.

The councilors exchange glances. Asha looks relieved. Hurst looks skeptical. Varn calculates.

"Very well," Hurst says. "We'll quarantine them for thirty days. After that, if no cure arrives..." He doesn't finish.

Asha stands. "Thank you. This family deserves a chance."

[Council quest accepted: Infected Refugees - Quarantine Path]
[Time limit: 30 turns to return with cure (spore_mother_blessing OR myconid_cure)]
[Commitment registered: to council AND to refugee family]
[DESIGN INPUT: This creates time pressure, but it's player-chosen, not thrust upon them. Important distinction from Sunken District.]

---

## BRANCH POINT A: Player Leaves vs Continues Exploring

The player has committed to finding a cure. They could:
- Leave immediately for Fungal Depths
- Continue exploring town first (time allows)
- Take on additional quests

---

### Turn 19

> go south

[Location: Market Square]

> go south

[Location: Broken Statue Hall]

A stone figure stands in the center of the hall - or what remains of one. A humanoid construct, similar to the Temple Guardians in Frozen Reaches, but shattered. One arm is missing. Cracks run through its torso. Its rune-eyes are dark.

On its base: "PROTECTOR. TO GUARD IS TO SERVE."

A stone chisel lies nearby.

Damaged Guardian is here. (non-functional)

---

### Turn 20

> examine guardian

The construct is ancient, built from the same enchanted stone as the Frozen Reaches guardians. It was clearly powerful once - the damage patterns suggest it fought something massive.

The runes are intact but dormant. You sense it could be repaired with the right components.

[Examination reveals: Needs stone_chisel (present), animator_crystal (Nexus), ritual_knowledge (Frozen Reaches lore or Echo's guidance)]

---

### Turn 21

> take stone chisel

You pick up the specialized chisel. It's designed for working enchanted stone.

[Inventory: stone_chisel added]

---

### Turn 22

> talk to guardian

The construct doesn't respond. Its eyes remain dark.

But... you could swear you saw a faint flicker in the runes. Patient. Waiting.

[OBSERVATION: Guardian repair is a long-term goal, not immediate. No time pressure - creates different emotional register than rescues.]

---

### Turn 23

> go north, go north

[Location: Town Gate]

The guards watch you leave.

> go north

[Location: Southern Trail (Beast Wilds)]

You're back in the Beast Wilds. The town feels distant already.

[Note: If player had wolf companion, it would be waiting here]

---

## BRANCH B: Cross-Region Cure Search

[Abbreviated - player travels to Fungal Depths]

### Turns 24-50 (Summarized)

Player navigates to Fungal Depths, establishes relationship with Spore Mother or Myconids, obtains cure (spore blessing or myconid treatment).

[See Fungal Depths walkthrough for details]

---

### Turn 51

[Location: Town Gate]

You return to the Remnants carrying a sealed vial - the Spore Mother's blessing, distilled into portable form.

The guards recognize you. "You're back. The refugees still live. Barely."

[Time elapsed: 27 turns (3 remaining)]
[OBSERVATION: Tight but successful timing creates tension without frustration]

---

### Turn 52

> go to healer's sanctuary

[Location: Healer's Sanctuary]

Elara looks up, hope flashing in her eyes. "You found something?"

---

### Turn 53

> give spore blessing to elara

You hand over the vial. Elara examines it, smells it, nods slowly.

"Spore Mother's blessing. This will work." She looks at you with new respect. "You actually did it. You went into the Depths and came back with a cure."

[Spore blessing transferred]
[Elara trust: 0 -> 2]
[DESIGN INPUT: Major trust boost for completing difficult cross-region task]

---

### Turn 54

> go to council hall

[Location: Council Hall]

The councilors are in session. Elara has clearly sent word - they're expecting you.

"The refugees," Asha says breathlessly. "They're being treated. You saved them."

Hurst looks grudgingly impressed. "You delivered. I didn't expect that."

Varn calculates. "A productive new resident. The town benefits."

[Quest complete: Infected Refugees - Quarantine Path]
[Town reputation: 0 -> +3]
[Asha: Very favorable]
[Hurst: Impressed]
[Varn: Sees value]
[Commitment fulfilled: +2 reputation bonus on top of base reward]

---

### Turn 55

> ask about town seal

Varn's eyes narrow. "The town seal? Our symbol of authority. Why do you ask?"

[DESIGN INPUT: Town seal is the region's waystone component. Must be earned.]

---

### Turn 56

> explain about waystone repair

You explain the damaged waystone in the Nexus, the need for components from each region.

The councilors confer quietly.

Hurst speaks. "The seal is not given lightly. It represents our people's authority, their will to survive. You've helped us once. Help us more substantially, and we may consider it."

[Requirement revealed: Hero reputation (5+) OR complete all three council dilemmas OR special service]

---

## BRANCH C: Garden Access and Herbalism

[Returning to earlier state to explore herbalism path]

### Turn 57

[Location: Healer's Sanctuary]
[Elara trust: 2 from cure delivery]

> ask elara about garden access

"You've proven yourself capable. And you came to understand the value of healing." She gestures toward the back door. "Come. I'll show you my garden - and begin teaching you true herbalism."

[Garden access granted (supervised)]
[MECHANISM: Trust 2 unlocks supervised access, Trust 3 unlocks unsupervised access + full teaching]

---

### Turn 58

> go to garden

[Location: Healer's Garden]

The garden is orderly, beautiful, and deadly. Rows of plants stretch before you, some flowering sweetly, others with warning markers.

Elara walks beside you. "The healing plants are along this path. The dangerous ones are marked." She points to red-flagged beds. "Nightshade. Deathcap. Widow's tears. Without knowledge, touching them means pain or death."

You see: healing_herbs (accessible), moonpetal (glowing softly), nightshade (red-flagged, Elara watching)

---

### Turn 59

> take healing herbs

You carefully harvest some healing herbs under Elara's guidance.

[Inventory: healing_herbs added]
[Note: These cure bear cubs' wasting sickness in Beast Wilds]

---

### Turn 60

> take moonpetal

You reach for the luminescent flower-

"Carefully," Elara says. "Moonpetal is safe to touch, but the root will give you a rash. Harvest from the stem."

She guides your hands. The flower comes free.

[Inventory: moonpetal added]
[Note: Trade item for Bee Queen in Beast Wilds]

---

### Turn 61

> take nightshade

You reach toward the red-flagged bed-

Elara's hand catches your wrist. "No. Not without proper training. Nightshade kills through skin contact for the untrained. Come back when you've earned my full teaching."

[Nightshade: Requires advanced herbalism (Trust 3)]
[DESIGN INPUT: Clear skill gate with narrative justification]

---

### Turn 62

> how do I earn your full teaching?

"Continue helping. Help my patients when you can. Show me you understand that healing is about more than knowledge - it's about care."

She thinks. "The refugees you saved will need follow-up care. There's also..." She hesitates. "An old friend of mine. Sira. She's a hunter in the Beast Wilds. I heard she was injured. If you encounter her..."

[Flag set: elara_knows_sira]
[Connection revealed: Elara -> Sira (Beast Wilds)]
[DESIGN INPUT: Cross-region NPC connections create web of relationships]

---

### Turn 63

> what do you know about sira?

"We grew up together. She chose the wilds; I chose healing. We haven't spoken in years, but..." Elara's voice softens. "If she's hurt, and you could help her... that would mean something to me."

[Implicit commitment opportunity: Help Sira, tell Elara]
[Reward if fulfilled: +2 trust with Elara, unlocks advanced herbalism]

---

## BRANCH D: Undercity Discovery and Moral Complexity

[Exploring the criminal element]

### Turn 64

[Location: Market Square, evening]

The market is quieter now. Shadows lengthen. Curiosity Dealer Vex is still at their booth, watching the crowd with knowing eyes.

> talk to vex

Vex smiles - a thin expression that doesn't reach their eyes. "Evening. Looking for something... unusual?"

---

### Turn 65

> what do you sell?

"Curiosities. Oddities. Things that fell off carts or out of pockets." Their voice drops. "And for the right customer... access to things the surface doesn't acknowledge."

[Vex trust: 0]
[Services visible: Basic trades only]

---

### Turn 66

> what do you mean?

Vex leans back. "Let's get to know each other first. Trade with me. Prove you're... flexible. Then we can discuss the deeper market."

[MECHANISM: Vex trust increases through trading rare items (spider_silk, venom_sacs, ice_crystals, etc.)]

---

### Turn 67

> sell ice crystals

[Assuming player has ice_crystals from Frozen Reaches]

You produce the ice crystals. Vex's eyes light up.

"Now that's interesting. Where did you... no, don't tell me." They slide coins across. "Forty gold. And my interest."

[Inventory: ice_crystals removed]
[Gold: +40]
[Vex trust: 0 -> 1]

---

### Turn 68

> sell spider silk

[Assuming player has spider_silk from Beast Wilds]

"Spider silk from the giant ones. Valuable. Fifty gold."

[Inventory: spider_silk removed]
[Gold: +50]
[Vex trust: 1 -> 2]

"You travel interesting places. Perhaps we should talk more... privately."

---

### Turn 69

> what do you mean privately?

Vex glances around, then leans close. "There's a market beneath the market. For those who need things the council doesn't approve of. Interested?"

[Undercity access: Trust 2 offers hint, Trust 3 grants access]

---

### Turn 70

> yes

"Come back at midnight. The trapdoor is under the dry fountain. Knock three times, wait, knock twice." Vex smiles. "Welcome to the real economy."

[Flag set: knows_undercity_entrance]
[Undercity access unlocked]

---

### Turn 71

[Later, midnight]

> go down

You find the trapdoor under the fountain where Vex indicated. Three knocks, pause, two knocks.

A bolt slides. The trapdoor opens. You descend.

[Location: Undercity]

Dim lanterns illuminate a network of tunnels. Several figures lurk in alcoves. The air smells of secrets and desperation.

You see: The Fence (buying/selling booth), Whisper (information), Shadow (dangerous corner).

---

### Turn 72

> talk to fence

A figure in shadows speaks without turning. "Buying or selling?"

"I take anything, no questions. Pay fifty percent of value. Or I sell things you can't get above - lockpicks, poisons, disguise kits."

[Services: Buy stolen goods (50% value), Sell contraband]

---

### Turn 73

> talk to whisper

A nondescript person materializes beside you. "Information. Everyone has it. Everyone wants it. I facilitate the exchange."

"Secrets about people - twenty gold. Secrets about places - thirty. Really valuable secrets..." They smile. "We negotiate."

---

### Turn 74

> buy information about council

"The council? Let's see..." Whisper considers. "Forty gold, and I'll tell you something useful."

> pay 40 gold

[Gold: -40]

"Councilor Varn has undercity connections. He profits from trades he publicly condemns. Councilor Hurst lost his family to beast attacks - that's why he's so harsh. Councilor Asha is genuinely idealistic, which makes her dangerous in a different way."

[Flags set: knows_varn_corruption, knows_hurst_tragedy, knows_asha_idealism]
[OBSERVATION: Information creates manipulation options or empathy options - player choice]

---

### Turn 75

> talk to shadow

You approach the dark corner. A voice speaks from somewhere you can't locate.

"I solve problems. Permanently. If you have a problem that won't go away, name them. I'll quote a price."

[Services: Assassination contracts (100-500 gold)]
[DESIGN INPUT: This is the darkest option in the game. Using it has massive consequences.]

---

### Turn 76

> ask about consequences

"Everyone dies eventually. I just... adjust the schedule." The voice pauses. "But murder is murder. If it's discovered, you're implicated. The town will know. Other regions may hear. The Echo sees everything."

[MECHANISM: Assassination contracts have 20% discovery chance. Discovery = exile from town, reputation damage everywhere, Echo confrontation]

---

## BRANCH E: Council Dilemma - Dangerous Traders

[Player returns to surface, takes second council quest]

### Turn 77

[Location: Council Hall]

> ask about dangerous traders

Hurst nods. "Outsiders camped a mile from the walls. They have goods we need - medicine, tools, preserved food. But something's wrong. They won't say where they came from. Their stories don't match."

Asha frowns. "We can't turn away help. But we can't ignore danger either."

Varn speaks carefully. "The trade value is significant. But if they're bandits, or worse..."

[Quest available: Dangerous Traders]
[Options: Trade (risk), Refuse (safety), Investigate (information)]

---

### Turn 78

> I'll investigate them

"Wise," Hurst says. "Find out who they really are. Report back."

[Quest accepted: Dangerous Traders - Investigation]
[No time limit - investigation pace is flexible]

---

### Turn 79

[At trader camp, outside town]

You approach the outsider camp. Half a dozen people, well-equipped, guarded expressions.

A woman steps forward. "Looking to trade? Or just looking?"

---

### Turn 80

> just looking

She shrugs. "Look all you want. We have nothing to hide."

But her eyes say differently.

> examine camp carefully

[Skill check or careful observation]

You notice: The weapons are too uniform - military issue, not scavenged. The preserved food containers have scratched-off labels. One tent flap reveals medical equipment far better than anything in town.

These aren't traders. They're... something else.

---

### Turn 81

> ask where they came from

"North," the woman says. "Small settlement that didn't make it. We salvaged what we could."

But earlier, you overheard one of them mention "eastern roads." The stories don't match.

[Flag set: trader_inconsistencies_noted]

---

### Turn 82

> confront about inconsistencies

You point out the contradictions. The woman's expression hardens.

"Fine. You're clever." She drops the pretense. "We're refugees, yes. But from an infected settlement. We escaped before full quarantine. If your council knew..."

[Truth revealed: Traders fled infected settlement without completing quarantine. May or may not be infected themselves.]

---

### Turn 83

> what do you want?

"To survive. To trade. To find somewhere safe." Her voice breaks slightly. "We're not bandits. We're not monsters. We're just... scared. The infection hadn't reached our group when we left. We've been healthy for weeks."

[DILEMMA DEEPENS: They broke quarantine but may be safe. Trade goods are valuable. Refusing them condemns them. Accepting them might risk town.]

[OBSERVATION: No clear right answer. This is intentional design.]

---

### Turn 84

> return to council and report

[Location: Council Hall]

You explain what you found. The councilors react differently.

Hurst: "Quarantine breakers. They could be carrying infection right now. Exile them."

Asha: "They've been healthy for weeks. They're just scared people. We should test them properly and consider admission."

Varn: "Their goods are valuable regardless. Trade at distance, don't admit them, let them move on."

[Decision required: Exile / Admit with testing / Trade at distance]

---

### Turn 85

> recommend testing and admission

Asha looks relieved. Hurst looks skeptical. Varn shrugs.

"Very well," Hurst says. "We'll test them. If they're clean, they can stay. If not..." He doesn't finish.

[Decision made: Test and potential admission]
[Asha: Very favorable (+2)]
[Hurst: Skeptical (-1)]
[Varn: Neutral]

[Outcome determined later: 80% chance clean, 20% chance one infected individual discovered during testing. If infected found, Hurst blames player.]

[DESIGN INPUT: Decisions have probabilistic consequences - player doesn't know exact outcome when deciding]

---

## BRANCH F: Criminal Punishment Dilemma

### Turn 86

> ask about the thief

Varn sighs. "A young man. Caught stealing food. First offense. He claims his family was starving."

Asha: "Hunger isn't a crime. The circumstances matter."

Hurst: "Theft is theft. If we don't punish it, everyone steals. Then we all starve."

[Dilemma: Criminal Punishment]
[Options: Harsh punishment (deterrence), Mercy (understanding), Labor (productive)]

---

### Turn 87

> what are the specific options?

"Harsh punishment," Hurst says. "Public flogging. A week in the stocks. He'll never steal again, and neither will anyone watching."

"Mercy," Asha counters. "Return him to his family with a warning. Address the underlying hunger - clearly our distribution system is failing someone."

"Labor," Varn suggests. "Put him to work for the community. Repayment through service. He pays his debt and contributes."

---

### Turn 88

> what happens to his family while he does labor?

Varn hesitates. "They... would need to manage without him for a period. A few weeks."

Asha cuts in. "Which means his family starves anyway. Labor sounds fair but punishes innocents."

Hurst: "Then give the family extra rations while he works. The labor option with support."

[OBSERVATION: Dilemma evolves through discussion. Initial options become more nuanced.]

---

### Turn 89

> recommend labor with family support

All three councilors nod.

"A compromise," Hurst says. "Not my first choice, but workable."

"Fair," Asha agrees. "He pays a debt, his family survives."

"Productive," Varn adds. "The town gains labor, maintains order, shows mercy."

[Decision made: Labor with family support]
[All councilors: Acceptable outcome]
[Town reputation: +1]
[DESIGN INPUT: Some compromises satisfy everyone. These should be discoverable through dialog, not obvious initially.]

---

## BRANCH G: Guardian Repair (Long-term Quest)

### Turn 90

[Location: Broken Statue Hall]
[Player has stone_chisel, has visited Frozen Reaches and read lore tablets]

> examine guardian runes

The runes are similar to the Temple Guardians' runes, but the pattern is different - more protective, less aggressive.

From your reading of the Frozen Reaches lore tablets, you recognize the activation sequence. But the runes need power.

[Knowledge check passed: Knows ritual from Frozen Reaches]
[Still needed: Animator crystal from Nexus]

---

### Turn 91

[Later, after obtaining animator_crystal from Nexus Crystal Garden]

> use animator crystal on guardian

You place the crystal in the guardian's chest cavity. The runes flare with light.

Nothing happens for a long moment.

Then - a grinding sound. The guardian's head turns. Its eyes flicker, dim but present.

"...awakening... incomplete... damage... sustained..."

[Guardian: Non-functional -> Partially awakened]
[DESIGN INPUT: Repair is multi-stage, not instant]

---

### Turn 92

> use stone chisel to repair

You carefully work with the enchanted chisel, reshaping cracked stone, reinforcing damaged areas.

[Skill check or time investment: Several turns of careful work]

The guardian's form stabilizes. Missing arm remains missing, but the core structure is sound.

"...repairs... accepted... purpose... restored..."

The guardian stands. It's smaller than the Frozen Reaches guardians, but unmistakably alive.

"TO GUARD IS TO SERVE. AWAITING... DESIGNATION."

[Guardian: Partially awakened -> Functional (one-armed)]
[DESIGN INPUT: Guardian is repaired but imperfect - consequence of damage. Still effective but visually marked by its history.]

---

### Turn 93

> designate purpose: protect the town

"ACKNOWLEDGED. CIVILIZED REMNANTS DESIGNATED AS PROTECTION TARGET. PATROL PARAMETERS... AWAITING."

The guardian waits for further instructions.

[Guardian: Functional -> Active]
[Town defense improved]
[Quest complete: Guardian Repair]
[Town reputation: +3]
[Council very favorable]

---

### Turn 94

[Location: Council Hall]

"You... actually repaired it," Hurst says, genuinely impressed. "We thought it was lost forever."

Asha: "The guardian will protect us. This is a gift beyond price."

Varn calculates. "The town's defensive value has increased significantly. Trade partners will feel safer."

[All councilors: Very favorable]
[Town reputation: +3 (now 7+)]
[Hero status achieved]

---

### Turn 95

> ask about town seal

This time, the response is different.

Hurst stands. "You've earned this." He retrieves an ornate seal from a locked box. "The Town Seal of the Civilized Remnants. Our authority, our will to survive. You've become part of that."

[Received: town_seal]
[Quest item for Nexus waystone repair]

---

## Summary Tables

### Design Inputs Generated

| ID | Input | Value | Notes |
|----|-------|-------|-------|
| DI-CR-1 | Two herbalism tiers | Basic (Maren, trust 2) + Advanced (Elara, trust 3) | Clear progression |
| DI-CR-2 | Garden skill gate | Supervised access at trust 2, full at trust 3 | Narrative justification via nightshade danger |
| DI-CR-3 | Quarantine quest creates time pressure | 30 turns to find cure | Player-chosen commitment, not forced |
| DI-CR-4 | Undercity discovery requires trust | Trade rare items to Vex | Prevents immediate access |
| DI-CR-5 | Council dilemmas evolve through dialog | Initial options can be refined | Compromise solutions discoverable |
| DI-CR-6 | Trader dilemma has probabilistic outcome | 80% clean, 20% one infected | Uncertainty in decisions |
| DI-CR-7 | Guardian repair is multi-stage | Crystal + knowledge + chisel + time | Not instant fix |
| DI-CR-8 | Repaired guardian is imperfect | One-armed, marked by history | Consequence of damage |
| DI-CR-9 | Town seal requires hero status (5+) OR special service | Guardian repair counts as special | Multiple paths to same goal |
| DI-CR-10 | Assassination contracts have discovery chance | 20% chance, massive consequences | Ultimate dark path |
| DI-CR-11 | Elara-Sira connection | Cross-region relationship bonus | Help Sira, gain Elara trust |
| DI-CR-12 | Whisper sells NPC information | Creates manipulation OR empathy options | Player decides how to use |

### Questions Raised

| ID | Question | Proposed Resolution |
|----|----------|---------------------|
| Q-CR-1 | Can player become a council member? | No, but hero status grants advisor influence |
| Q-CR-2 | What happens if player is exiled? | Can only enter through undercity. Surface hostile. Can restore reputation through undercity quests |
| Q-CR-3 | How does undercity discovery work? | 5% per use. Discovery = -2 town reputation. Multiple discoveries = exile |
| Q-CR-4 | What if player uses assassin on a councilor? | Major consequences. Remaining councilors hostile. Town destabilized. Echo confronts player directly. |
| Q-CR-5 | Can salamander companion enter town? | Yes, with hesitation. Guards nervous but allow if player vouches. -1 reputation until salamander proves harmless. |
| Q-CR-6 | What if player fails quarantine quest (time runs out)? | Refugees die. -3 reputation. Asha refuses to speak to player. Elara disappointed. |
| Q-CR-7 | What if infected trader is discovered after admission? | Hurst blames player (-2 with Hurst). Town must use scarce medicine. Net reputation depends on how player handles follow-up. |

### Mechanisms Required

| Mechanism | Status | Notes |
|-----------|--------|-------|
| Dual reputation tracking (town vs undercity) | Needed | Separate scales, can conflict |
| Trust-gated services | Needed | Different thresholds unlock different services |
| Probabilistic quest outcomes | Needed | Some decisions have uncertain results |
| Cross-region NPC connections | Needed | Elara-Sira, Delvan-undercity |
| Time-limited quests | Existing | Apply to quarantine commitment |
| Discovery chance for illegal actions | Needed | Undercity use, assassination |
| Multi-stage repairs | Needed | Guardian repair progression |

### Gameplay Observations

**Positive:**
- Social hazards create tension without combat
- Dilemmas genuinely have no clear "right" answer
- Undercity provides dark path without forcing it
- Cross-region connections create web of relationships
- Guardian repair feels earned and meaningful
- Town reputation creates tangible consequences

**Concerns:**
- Player might miss undercity entirely (hidden)
- Dilemmas might feel arbitrary without enough context
- Assassination option might feel too dark for some players
- Trust grinding could feel tedious

**Potentially Boring Sections:**
- Building trust through purchases (but can be accelerated through quests)
- Waiting for quarantine quest timer (but player can do other things)

**Frustrating Sections:**
- Getting exiled without clear path back (but undercity provides one)
- Nightshade poison without warning (but Elara warns explicitly)
- Missing Elara-Sira connection if not asking right questions

---

## Paths Not Yet Explored

- [ ] Player uses assassination service - full consequences
- [ ] Player gets exiled - undercity-only playthrough
- [ ] Player brings wolf companion to gate - full confrontation
- [ ] Player tells Elara about saving/failing Sira
- [ ] Infected trader discovered - follow-up choices
- [ ] Player plays councilors against each other using Whisper info
- [ ] Guardian used in actual defense scenario
- [ ] Player completes all three dilemmas with optimal outcomes
