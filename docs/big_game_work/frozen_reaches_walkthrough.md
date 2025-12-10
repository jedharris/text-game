# Frozen Reaches Walkthrough

## Purpose

This walkthrough explores a region with:
- **Environmental challenge focus** (cold/hypothermia) rather than time-sensitive NPC rescue
- **Puzzle vs combat choice** for the golem encounters
- **No dying NPCs** - salamanders are fine without player help
- **Methodical exploration** rewarded rather than rushed play

This contrasts with Sunken District's frantic dual-rescue and Beast Wilds' commitment-driven urgency.

## Notation

- `[MECHANISM: X]` - Requires engine/behavior support
- `[DESIGN INPUT: X]` - Decision made during simulation
- `[QUESTION: X]` - Ambiguity needing resolution
- `[OBSERVATION: X]` - Gameplay quality note

## Initial State

- Player arrives from Nexus with basic equipment
- No cold protection beyond basic clothing
- Health 100, no conditions
- Has: rusty_sword, torch, 10 gold

---

## TRUNK: Entry and Initial Exploration

### Turn 1
[Location: Nexus Chamber]

> go north

You climb stone steps that grow colder with each stride. The air bites at exposed skin. Snow swirls through a gap in the ancient stonework ahead.

You emerge into the Frozen Pass.

[Location: Frozen Pass]

The wind hits you like a physical force. Snow blankets everything - the path, the rocks, the shapes that might once have been travelers. An abandoned camp lies half-buried nearby.

The cold seeps into your bones immediately.

[Hypothermia begins: +5 severity per turn in cold zone]
[Current severity: 5]

Exits: South (Nexus), North (structure visible through snow), East (cave mouths), West (steam rising)

---

### Turn 2

> look

The Frozen Pass cuts between towering peaks. To the north, you can make out a stone structure - a temple of some kind. To the east, dark openings in the cliff face promise shelter from the wind. To the west, impossible in this cold, steam rises from somewhere beyond the rocks.

Near you: an abandoned camp with scattered supplies, frozen bodies of previous travelers, and snow that hasn't melted in years.

[Hypothermia: 5 -> 10]

---

### Turn 3

> examine camp

The camp is long abandoned. Frozen corpses sit around a fire pit that holds no warmth. Their faces are peaceful - they died in their sleep as the cold took them.

Among the remains you find: cold weather gear (heavy furs), preserved supplies (dried meat, bandages, a torch), and a partial map showing this region.

[OBSERVATION: Environmental storytelling - these people tried to survive and failed. Sets tone.]

---

### Turn 4

> take cold weather gear

You pull the heavy furs from beneath the snow and shake them out. They're stiff but intact.

[Inventory: cold_weather_gear added]

---

### Turn 5

> wear cold weather gear

You bundle yourself in the furs. The wind still bites, but the cold's grip loosens somewhat.

[Cold weather gear equipped]
[Hypothermia progression halved: +2.5 per turn instead of +5]
[Current severity: 12.5 -> 15 (rounded)]

---

### Turn 6

> take supplies

You gather the preserved supplies - dried meat, bandages, and an unlit torch.

[Inventory: dried_meat, bandages, torch added]

---

### Turn 7

> read map

The partial map shows:
- A temple to the north, marked "DANGER - GUARDIANS"
- Hot springs to the west, marked "SAFE - WARM"
- Ice caves to the east, marked "TREASURE - CAREFUL"
- An observatory above the temple, marked "EXTREME COLD"

Someone has written: "The springs saved my life. The temple took my partner's."

[Flags set: knows_temple_danger, knows_springs_safe, knows_caves_treasure]
[DESIGN INPUT: Map provides basic guidance without solving puzzles]

---

### Turn 8

> take map

You fold the map and pocket it.

[Inventory: partial_map added]
[Hypothermia: 15 -> 17.5 -> 18]

---

## BRANCH POINT A: First Direction Choice

The player can go:
- **North** to Temple (danger, but shelter from wind)
- **East** to Ice Caves (treasure, colder inside)
- **West** to Hot Springs (safety, warmth, salamanders)

This is a meaningful choice about preparation vs. exploration.

---

### Branch A1: West to Hot Springs First (Cautious Path)

### Turn 9

> go west

You follow the steam. The path winds between rocks that gradually grow warmer to the touch. The snow thins, then disappears entirely.

You emerge into a steaming paradise.

[Location: Hot Springs Refuge]
[Temperature: Normal - hypothermia recovery begins]
[Hypothermia: 18 -> 0 (hot springs cure)]

The Hot Springs Refuge is a volcanic pocket of warmth amid the frozen wasteland. Steam rises from mineral-rich pools. The air smells of sulfur but feels like an embrace after the biting cold.

Three lizard-like creatures lounge near the largest pool. They're wreathed in steam, their scales shimmering with heat. They watch you with glowing eyes but don't move to attack.

Steam Salamander is here. (neutral)
Steam Salamander is here. (neutral)
Steam Salamander is here. (neutral)

[OBSERVATION: Immediate relief after cold pressure. The hot springs feel earned even though player only endured 8 turns of cold.]

---

### Turn 10

> examine salamanders

The steam salamanders are beautiful in an alien way - scales that shift between orange and red, eyes like embers, bodies that radiate warmth you can feel from several feet away. They're clearly intelligent, watching you with curiosity rather than hunger.

One of them - slightly larger than the others - seems to be waiting for something.

[DESIGN INPUT: Salamanders are clearly intelligent and non-hostile. Player should intuit they can be befriended.]

---

### Turn 11

> talk to salamander

The salamander tilts its head. It doesn't speak, but its eyes track your movements, your torch, your hands. It makes a gesture toward your unlit torch, then toward itself.

[MECHANISM: Non-verbal communication through gesture]
[OBSERVATION: Salamander is asking for fire. Good hint without words.]

---

### Turn 12

> light torch

You strike flint and light your torch. The flame catches, casting warm light.

The salamanders all turn to watch. The largest one rises and approaches, drawn to the flame.

[Torch: lit]

---

### Turn 13

> give torch to salamander

You extend the burning torch toward the salamander.

It takes the torch in its claws with surprising delicacy. For a moment it simply holds the flame close, basking in it. Then - impossibly - it *inhales* the fire. The torch goes dark, but the salamander glows brighter.

It makes a sound like crackling embers. The other salamanders echo it.

Something has shifted in how they regard you.

[Torch consumed]
[Steam Salamander 1: neutral -> friendly]
[Steam Salamander 1 gratitude: +1]
[Other salamanders: neutral -> wary-positive (watching how this develops)]
[DESIGN INPUT: Fire gift consumed, not held. Creates need for multiple fire sources for full befriending.]

---

### Turn 14

> look

The Hot Springs Refuge steams gently around you. The largest salamander has moved closer, its warmth a pleasant aura. The other two watch with interest.

The pools offer healing rest. You could stay here indefinitely in safety.

[OBSERVATION: This is a sanctuary. No time pressure. Player can plan their approach to the dangerous areas.]

---

### Turn 15

> rest in hot springs

You ease into one of the warm pools. The heat soaks into your muscles, washing away the memory of cold.

[Resting in hot springs: +5 health per turn]
[One turn passes]
[Health: 100 (already full)]

The friendly salamander curls near the edge of your pool, adding its warmth. It seems content.

---

### Turn 16

> ask salamander about temple

The salamander's eyes flicker. It makes a gesture - two fists coming together, then separating slowly. It shakes its head and points to its own chest, then makes a warding sign.

[INTERPRETATION: Temple guardians. Salamanders won't go there / can't help there.]
[DESIGN INPUT: Salamanders provide hints through pantomime. Limited but useful.]

---

### Turn 17

> ask salamander about caves

The salamander perks up. It makes a shivering gesture - cold, very cold - then mimes finding something and holding it close. It looks at you expectantly.

[INTERPRETATION: Caves are cold but have something valuable.]
[OBSERVATION: Salamander wants player to bring back something from caves? Fire-aspected crystal?]

---

### Turn 18

> go east

The salamander makes a worried sound as you leave the warmth. The largest one follows you to the edge of the refuge, then stops. It won't leave the warm zone.

You return to the Frozen Pass.

[Location: Frozen Pass]
[Hypothermia resumes: severity 0 -> 2.5]

The wind hits you again, but the memory of warmth sustains you.

---

### Turn 19

> go east

You approach the dark openings in the cliff face. The wind dies as you enter the caves, but somehow the cold intensifies.

[Location: Ice Caves]
[Temperature: Freezing (+10 hypothermia per turn, gear halves to +5)]
[Hypothermia: 2.5 -> 7.5]

The Ice Caves are crystalline and beautiful. Blue light refracts through walls of ancient ice. Your breath freezes before your face. The floor is treacherous - smooth ice in places, rough stone in others.

You see: ice crystals (growing from walls), frost lilies (delicate white flowers), something glinting deeper in the cave.

[OBSERVATION: Beauty and danger combined. Classic frozen dungeon.]

---

### Turn 20

> examine ice crystals

The crystals are stunning - clear as glass, cold as death. They seem to contain frozen light. These would be valuable to anyone who prizes rare minerals.

[Flag set: noticed_ice_crystals]
[Hypothermia: 7.5 -> 12.5]

---

### Turn 21

> take ice crystals

You carefully chip several crystals free from the wall. They're cold enough to sting through your gloves.

[Inventory: ice_crystals added]
[DESIGN INPUT: Easy acquisition. The crystals are plentiful. Value is in knowing who wants them (Myconids).]

---

### Turn 22

> take frost lily

You carefully pluck a frost lily. It's surprisingly sturdy for something so delicate-looking.

[Inventory: frost_lily added]
[Hypothermia: 12.5 -> 17.5]

---

### Turn 23

> go deeper

You move deeper into the caves, following the glinting light. The floor becomes more treacherous - you can see dark water beneath thin ice in places.

[Sub-location: Deep Ice Caves]
[Hazard present: thin ice]
[Hypothermia: 17.5 -> 22.5]

The glinting comes from two sources: a shard of magical ice embedded in a frozen pool, and something that looks like a crystal lens frozen into the far wall.

---

### Turn 24

> examine thin ice

The ice over the pool is thin enough to see through. Dark water moves beneath it. Breaking through would mean cold water - potentially fatal.

[MECHANISM: Hazard warning on examination]
[DESIGN INPUT: Player can test ice carefully or risk crossing]

---

### Turn 25

> examine ice shard

The ice shard pulses with cold energy - clearly magical. It's embedded in the frozen pool, reachable if you cross the thin ice or find another way.

[Flag set: located_ice_shard]
[Hypothermia: 22.5 -> 27.5]

---

### Turn 26

> examine crystal lens

The crystal lens is frozen into the ice wall, perfectly preserved. It looks precisely ground, like something from a telescope or other optical instrument. Extracting it without breaking it would require melting the ice carefully.

[Flag set: located_crystal_lens]
[Hypothermia: 27.5 -> 32.5]
[Hypothermia effect: Movement slowed (severity 30+)]

---

### Turn 27

> use torch on wall

Your torch isn't lit.

[OBSERVATION: Player gave torch to salamander. Now needs fire source for extraction. Good resource tension.]

---

### Turn 28

The cold is getting to you. Your movements feel sluggish.

> go west

You retreat from the deep caves, back to the main chamber.

[Location: Ice Caves (main)]
[Hypothermia: 32.5 -> 37.5]

---

### Turn 29

> go west

You leave the caves and return to the pass.

[Location: Frozen Pass]
[Hypothermia: 37.5 -> 40 (cold zone, +2.5)]

---

### Turn 30

> go west

You hurry toward the steam. The warmth hits you like a wave of relief.

[Location: Hot Springs Refuge]
[Hypothermia: 40 -> 0 (cured)]

The salamanders look up as you return. The friendly one makes a crackling sound that might be greeting.

[OBSERVATION: The hot springs serve as a "save point" - a place to recover and plan. This is good pacing.]

---

### Turn 31

> show ice crystals to salamander

You hold out the ice crystals. The salamander recoils slightly - cold is not its friend - but looks at them with interest. It shakes its head. Not what it wants.

[DESIGN INPUT: Salamanders don't want ice crystals. They want fire-aspected items.]

---

### Turn 32

> rest

You rest by the pools, fully recovering.

[One turn passes]
[Health: 100]

[OBSERVATION: Player has explored caves, found treasures, but can't extract crystal lens without fire. Natural puzzle: need fire source.]

---

## BRANCH POINT B: Temple Approach

Player needs fire to extract the lens. Options:
- Find fire source in temple
- Return to Nexus for supplies
- See if salamander can help (it consumed the torch)

### Turn 33

> ask salamander for fire

The salamander tilts its head. It breathes a small puff of flame into the air, then gestures at itself and shakes its head. It can make fire, but... it won't leave the warm zone to help you in the caves.

[DESIGN INPUT: Salamander can provide fire but only in warm areas. Creates need to bring salamander OR find portable fire.]

---

### Turn 34

> go north

You leave the warmth and head toward the temple through the pass.

[Location: Frozen Pass]
[Hypothermia: 0 -> 2.5]

---

### Turn 35

> go north

You approach the stone structure. It's ancient, carved with geometric patterns and faces that might be gods or guardians. The entrance is a dark archway.

As you step inside, you hear grinding stone.

[Location: Temple Sanctum]
[Temperature: Cold (sheltered from wind, but still cold)]
[Hypothermia: 2.5 -> 5]

Two massive stone figures flank the entrance hall. They were still a moment ago. Now they're moving, turning toward you with grinding inevitability.

Stone Guardian is here. (hostile)
Stone Guardian is here. (hostile)

Their eyes glow with runes. They raise stone fists.

[Combat warning: One turn before attack]

---

## BRANCH POINT C: Golem Encounter

This is the key decision point. Player can:
- **Fight** (very difficult)
- **Flee** (resets encounter)
- **Speak password** (if known)
- **Present offering** (if has items)
- **Use control crystal** (if has it)

Player currently has: cold_weather_gear, partial_map, ice_crystals, frost_lily, dried_meat, bandages. No password knowledge, no control crystal, no obvious offering.

---

### Branch C1: Combat Approach

### Turn 36

> attack golem

You charge at the nearest guardian, sword raised.

Your blade strikes stone. The impact jars your arm.

[Player attacks Stone Guardian: 5 damage (halved by armor 10)]
[Stone Guardian health: 150 -> 145]

The guardians respond.

[Stone Guardian 1 attacks: 28 damage]
[Stone Guardian 2 attacks: 31 damage]

Both fists crash into you with devastating force.

[Player health: 100 -> 41]
[Hypothermia: 5 -> 7.5]

[OBSERVATION: BRUTAL. 59 damage in one round. This is meant to discourage direct combat.]

---

### Turn 37

> use pillar for cover

You dive behind one of the stone pillars lining the hall.

[Cover established: 80% damage reduction from guardians]
[Stone Guardian attack: 30 damage -> 6 damage (reduced)]

[Player health: 41 -> 35]
[Hypothermia: 7.5 -> 10]

The guardians lumber toward your pillar. They're slow but relentless.

[DESIGN INPUT: Cover is essential for survival. Hit-and-run is the only viable combat strategy.]

---

### Turn 38

> attack golem then return to cover

You dart out, strike, and retreat.

[Player attacks: 5 damage]
[Stone Guardian 1: 145 -> 140]

The guardian's swing misses as you duck back behind the pillar.

[Cover maintained]
[Hypothermia: 10 -> 12.5]

---

### Turn 39-50 (Combat Summary)

[ABBREVIATED: Combat continues with hit-and-run tactics]

Each round:
- Player deals ~5 damage (armor reduces effectiveness)
- Guardians deal 6 damage through cover (30 * 0.2)
- Hypothermia increases by 2.5 per turn

After 12 rounds:
- Guardian 1: 140 -> 80 (60 damage dealt)
- Player health: 35 -> -37 (dead from combat + cold)

[OBSERVATION: Combat is NOT viable with current equipment. Player needs better weapon or different approach.]

---

### Branch C1-ALT: Flee and Reconsider

### Turn 36-ALT

> run south

You turn and sprint out of the temple. The guardians pursue to the entrance but don't follow into the snow.

[Location: Frozen Pass]
[Combat escaped]
[Hypothermia: 5 -> 7.5]

The guardians return to their positions, waiting.

[DESIGN INPUT: Guardians don't leave temple. Player can escape and try again.]

---

## Branch C2: Research Approach (Finding Password)

[Resetting to Turn 35, player explores rather than attacking]

### Turn 36-ALT2

> look around carefully

You stay near the entrance, examining the temple before the guardians attack.

The guardians are moving, but slowly. You have a moment.

The walls are covered in inscriptions. Stone tablets rest on an altar at the far end. Pillars provide cover. You see: mounting bracket (on altar), cold resistance cloak (in alcove), lore tablets (carved into walls).

[Guardians approaching but not yet in range]

---

### Turn 37

> read wall inscriptions

You quickly scan the inscriptions near the entrance.

Ancient text, partially legible: "...the guardians sleep when spoken true... the words of making... fire and water joined..."

[Partial password hint: something about fire and water]
[Hypothermia: 7.5 -> 10]

The guardians draw closer.

---

### Turn 38

> retreat to entrance

You back up to the temple entrance, ready to flee.

The guardians stop advancing. They watch you, waiting for you to come deeper.

[DESIGN INPUT: Guardians are territorial. They won't attack at the entrance threshold. Player can observe safely from doorway.]

---

### Turn 39

> read more inscriptions from doorway

From the doorway, you can make out more text on the nearer walls:

"Built to guard the path above. The observatory sees all, knows all. The guardians protect the way."

"To pass peacefully: speak the words of joining. Fire-that-gives-life and water-that-cleanses, united."

[Password hint expanded: "fire-that-gives-life" and "water-that-cleanses" must be joined/spoken]
[QUESTION: What exactly is the password phrase?]
[DESIGN INPUT: Password is thematic - fire and water elements combined]

---

### Turn 40

> say "fire and water joined"

You speak the words clearly.

The guardians pause. Their rune-eyes flicker. But after a moment, they resume their vigilant stance.

[Password incorrect - close but not exact]

---

### Turn 41

> say "fire-that-gives-life and water-that-cleanses"

The guardians pause again. The flickering is longer this time.

"...incomplete..." a voice like grinding stone emanates from them. "...the joining word..."

[Password partially correct - missing the joining word]
[DESIGN INPUT: Password has three parts: element, element, joining concept]

---

### Turn 42

> say "fire-that-gives-life and water-that-cleanses, united"

The guardians freeze. Their rune-eyes shift from hostile red to a calm blue.

"...recognized..."

They step aside, returning to their alcoves. They don't deactivate, but they no longer bar your passage.

[Guardians: hostile -> passive]
[Temple accessible]
[Hypothermia: 10 -> 12.5]

[OBSERVATION: Password works but guardians remain watchful. Any hostile action would reactivate them.]

---

### Turn 43

> take mounting bracket

You approach the altar and take the mounting bracket. It's heavy, inscribed with alignment runes.

[Inventory: mounting_bracket added]

---

### Turn 44

> take cold resistance cloak

You find the cloak in an alcove - beautifully woven with protective enchantments. It feels warm to the touch.

[Inventory: cold_resistance_cloak added]
[DESIGN INPUT: Major reward for solving temple peacefully]

---

### Turn 45

> wear cold resistance cloak

You don the enchanted cloak. Warmth suffuses you.

[Cold resistance cloak equipped - replaces cold weather gear for better protection]
[Cold immunity in cold zones, resistance in freezing zones]
[Hypothermia: 12.5 -> 0 (cloak provides warmth)]

---

### Turn 46

> read lore tablets

The tablets tell the story of the Meridian - the magical ley line intersection that powered the civilization. When it shattered, this region froze. The temple was built to guard the observatory above, which could see the state of all regions.

One tablet contains the full password: "Fire-that-gives-life and water-that-cleanses, united in purpose."

Another tablet mentions: "The control crystal sleeps in the eastern ice. With it, the guardians serve rather than merely permit."

[Flag set: knows_full_password, knows_control_crystal_location]
[OBSERVATION: Player already solved password through partial clues. Control crystal would give full control, not just passage.]

---

### Turn 47

> go up

A spiral staircase leads upward from the temple. You climb.

The cold intensifies dramatically as you emerge onto an exposed platform.

[Location: Frozen Observatory]
[Temperature: Extreme cold (+20 hypothermia per turn, cloak reduces to +10)]
[Hypothermia: 0 -> 10]

The wind screams across the peak. Stars are visible despite it being day - the sky is somehow darker here. An ancient telescope frame points at the horizon, but it's incomplete.

You see: ancient telescope frame (damaged), mounting points, spectacular view of all regions

---

### Turn 48

> examine telescope

The telescope frame is intact but missing components:
- Crystal lens (missing)
- Mounting bracket (you have this)
- The optics are fogged with age (need cleaning supplies)

[Telescope repair status: 1/3 components present]
[Hypothermia: 10 -> 20]

---

### Turn 49

> look at view

Even without the telescope, the view is staggering. You can see:
- The Nexus below, a shimmering point of stability
- Dark forests to the south (Beast Wilds)
- Glinting water to the east (Sunken District)
- Distant fungal glow to the west (Fungal Depths)
- Smoke rising from the far south (Civilized Remnants)

[OBSERVATION: The observatory provides perspective on the whole game world. Powerful moment.]
[Hypothermia: 20 -> 30 (movement slowed)]

---

### Turn 50

> go down

You hurry back into the relative warmth of the temple.

[Location: Temple Sanctum]
[Hypothermia: 30 -> 20 (cold zone, but cloak helps)]

---

### Turn 51

> go south

You exit the temple.

[Location: Frozen Pass]
[Hypothermia: 20 -> 10 (cloak provides immunity in cold zones)]

---

### Turn 52

> go west

You return to the hot springs.

[Location: Hot Springs Refuge]
[Hypothermia: 10 -> 0]

The salamanders greet you. The friendly one notices your new cloak and makes an approving sound.

---

## BRANCH POINT D: Getting the Crystal Lens

Player needs to extract the crystal lens from the ice wall. With the cloak, survival in the caves is easier. But extraction requires heat.

### Turn 53

> ask salamander to come with me

You gesture toward the caves, then at the salamander.

The salamander shakes its head. It gestures at the hot springs, then at itself - it needs warmth. It would weaken and die in the ice caves.

[DESIGN INPUT: Salamander won't enter freezing areas. Player needs portable fire.]

---

### Turn 54

> ask salamander for something to carry fire

The salamander considers. It picks up a smooth stone from near the springs and breathes on it. The stone glows with heat.

It offers you the stone. It's warm to the touch.

[Received: salamander-heated stone]
[Properties: Provides warmth aura (cold immunity), lasts ~20 turns before cooling]
[DESIGN INPUT: Salamander can provide portable warmth item. Creates bond.]

---

### Turn 55

> go east, go east

You travel through the pass to the ice caves, the heated stone keeping you warm.

[Location: Ice Caves, deep section]
[Hypothermia: 0 (stone provides immunity)]
[Stone warmth remaining: 18 turns]

The crystal lens gleams in the ice wall.

---

### Turn 56

> use heated stone on ice wall

You press the heated stone against the ice around the lens. The ice melts slowly, running in rivulets.

[Progress: 25%]
[Stone warmth: 17 turns]

---

### Turn 57-59

> continue melting ice

[Three turns of careful work]
[Progress: 100%]
[Stone warmth: 14 turns]

The lens comes free in your hands, perfectly intact.

[Inventory: crystal_lens added]
[OBSERVATION: Satisfying puzzle completion. Salamander friendship paid off.]

---

### Turn 60

> examine ice shard

Now you can approach the ice shard in the frozen pool. The thin ice still bars direct approach.

---

### Turn 61

> test thin ice

You tap the ice with your foot. It creaks ominously.

---

### Turn 62

> use heated stone on thin ice

You melt a path across the thin ice, creating a safe route.

[Stone warmth: 12 turns]
[Path created to ice shard]

---

### Turn 63

> take ice shard

You extract the ice shard from its frozen bed. It pulses with cold magic in your hands.

[Inventory: ice_shard added]
[OBSERVATION: Player now has all major treasures from ice caves.]

---

### Turn 64

> go west, west

You return to the hot springs before the stone cools.

[Location: Hot Springs Refuge]
[Stone warmth: 8 turns remaining]

The salamanders make pleased sounds as you return.

---

### Turn 65

> give heated stone back to salamander

You return the stone to the salamander. It takes it and places it back near the springs.

[Steam Salamander 1 gratitude: +1 (total: 2)]
[DESIGN INPUT: Returning the borrowed item increases gratitude. Good pattern.]

---

## BRANCH POINT E: Completing Telescope vs Befriending Salamanders

Player has: crystal lens, mounting bracket, ice shard, frost lily, ice crystals
Player needs: cleaning supplies (from Nexus)

Player could:
- Return to Nexus for supplies (complete telescope)
- Continue befriending salamanders (need more fire items)
- Explore temple combat path (control crystal)

### Branch E1: Completing Telescope

### Turn 66

> go south

[Travel: Hot Springs -> Frozen Pass -> Nexus]
[Multiple turns abbreviated]

[Location: Nexus Chamber]

You return to the Nexus. The shimmering air feels almost warm after the Frozen Reaches.

---

### Turn 67

> look for cleaning supplies

You search the Keeper's Quarters. Among the personal effects, you find cleaning supplies - cloths and solutions for maintaining the observatory equipment.

[Inventory: cleaning_supplies added]
[DESIGN INPUT: Cleaning supplies are in Nexus as stated in sketch. Easy to find.]

---

### Turn 68-72

[Travel back to Frozen Observatory - abbreviated]

[Location: Frozen Observatory]
[Cloak provides protection]
[Hypothermia: 0 -> 10 per turn (still extreme, but survivable)]

---

### Turn 73

> repair telescope

You work methodically:
- Attach the mounting bracket (aligns the telescope)
- Insert the crystal lens (provides magnification)
- Clean the optics (restores clarity)

The telescope hums with renewed purpose. The runes along its frame glow softly.

[Telescope: repaired]
[Global effect: Cold spread prevented]
[Crystal Garden progress: +1]

---

### Turn 74

> look through telescope

You put your eye to the telescope. The view is extraordinary.

The telescope shows not just distance but *state*:

**Fungal Depths**: The Spore Mother pulses weakly. Infection spreading. Aldric's campfire still burns - he's alive.

**Beast Wilds**: Wolf pack in clearing. A figure lies on the southern trail - injured, not moving much. Bear cubs in den, visible through the trees.

**Sunken District**: Water levels stable. A tapping signal from a building. Movement in the eastern caves.

**Civilized Remnants**: Smoke from chimneys. Guards at the gate. A broken statue in the town square.

[Flags set: telescope_reveals_aldric_alive, telescope_reveals_sira_injured, telescope_reveals_delvan_tapping, telescope_reveals_garrett_movement]

[DESIGN INPUT: Telescope provides strategic information about all regions. Major advantage for methodical player.]

[OBSERVATION: This is a powerful reward. Player who explores Frozen Reaches first and repairs telescope gets hints about time-sensitive situations elsewhere.]

---

### Turn 75

> examine meridian nexus through telescope

You turn the telescope toward the Nexus below.

The telescope reveals ley line patterns invisible to the naked eye - flows of magical energy converging on the waystone. The damaged waystone pulses irregularly. You can see... slots? Five mounting points, each corresponding to a region.

[Flag set: knows_waystone_requirements]
[OBSERVATION: Telescope explains the endgame - player needs items from each region for waystone repair.]

---

## Branch E2: Full Salamander Befriending

[Branching from Turn 65, player focuses on salamanders instead of telescope]

### Turn 66-ALT

To fully befriend the salamanders (gratitude 3 for companion status), player needs:
- Current gratitude: 2 (from torch gift + stone return)
- Need: 1 more fire-aspected gift

> what fire items do I have?

[Inventory check: dried_meat, bandages, ice_crystals, frost_lily, ice_shard, crystal_lens, mounting_bracket, partial_map, cold_weather_gear (in pack), cold_resistance_cloak (worn)]

No fire-aspected items currently.

[QUESTION: Where can player get more fire items in Frozen Reaches?]
[DESIGN INPUT: Fire items available: torches (multiple in preserved supplies), fire crystals (rare, in temple treasure), warm coals (can be created from any fire source)]

---

### Turn 67-ALT

> search temple for fire items

You return to the temple (guardians passive) and search more thoroughly.

In a side chamber, you find: a fire crystal (small, but genuine elemental fire captured in crystal form).

[Inventory: fire_crystal added]

---

### Turn 68-ALT

> return to hot springs

[Location: Hot Springs Refuge]

---

### Turn 69-ALT

> give fire crystal to salamander

You offer the fire crystal to the lead salamander.

Its eyes widen. This is not mere flame - this is elemental fire, kin to its own nature. It takes the crystal reverently and holds it to its chest, where it absorbs slowly.

The salamander glows brighter. All three salamanders make a sound like a crackling chorus.

[Steam Salamander 1: gratitude 2 -> 3]
[Steam Salamander 1: friendly -> companion-ready]
[Other salamanders: friendly (following lead)]

---

### Turn 70-ALT

> ask salamander to join me

You gesture an invitation. Come with me. Help me.

The lead salamander considers. It looks at the other salamanders, then at you. It makes a decision.

It steps forward and presses its warm head against your hand. Agreement.

[Steam Salamander 1: companion status achieved]
[Companion benefits: Warmth aura (cold immunity when nearby), light source, minor fire damage in combat]
[Companion restrictions: Won't enter water areas, uncomfortable outside cold regions]

---

### Turn 71-ALT

> go to ice caves with salamander

You travel to the ice caves with your new companion. The salamander stays close, its warmth a bubble of comfort in the freezing caves.

[Location: Ice Caves]
[Hypothermia: 0 (salamander aura)]
[No time limit - can explore indefinitely with salamander]

[OBSERVATION: Salamander companion trivializes cold hazard. This feels earned - player invested in relationship.]

---

## Branch C3: Control Crystal Path (Full Golem Control)

[Alternate branch - player finds control crystal before confronting golems]

[Assuming player learned about control crystal from temple inscriptions or prior knowledge]

### Turn X

[Location: Ice Caves, deep section]

> search for control crystal

You search the ice walls carefully. In a side passage you missed before, you find it - a crystal that resonates with the same energy as the golem runes, frozen in a wall of ice.

[Located: control_crystal (frozen in wall)]

---

### Turn X+1

> use fire to extract control crystal

[With salamander companion or heated stone]

You melt the ice carefully. The crystal comes free - it hums in your hands.

[Inventory: control_crystal added]

---

### Turn X+2

> go to temple

[Location: Temple Sanctum]

The guardians activate as you enter.

[Combat warning: One turn before attack]

---

### Turn X+3

> use control crystal

You hold up the control crystal. It pulses with light.

The guardians freeze. Their hostile red runes shift to blue, then to a calm white. They turn toward you and bow - a grinding, ancient gesture of service.

"...command recognized... awaiting orders..."

[Guardians: hostile -> serving]
[DESIGN INPUT: Control crystal gives full control, not just passage. Guardians become allies.]

---

### Turn X+4

> order guardians to guard temple entrance

"Guard the temple. Allow me to pass freely."

The guardians resume their positions, but now they recognize you as master.

[Temple status: Safe - guardians will attack intruders but not player]
[OBSERVATION: Control crystal is the "best" solution - provides ongoing benefit. But it's hidden and requires cave exploration first.]

---

## BRANCH F: Combat Victory Path (Optimized)

[For completeness - how COULD a player win combat?]

Requirements for combat victory:
- Better weapon (silver sword from Nexus or other region)
- Healing supplies (multiple)
- Cold resistance (cloak or salamander)
- Understanding of cover mechanics

### Optimized Combat Walkthrough

[Assuming player has: silver_sword (15 damage), 5 healing potions, cold_resistance_cloak]

### Round 1
> attack golem from cover

[Player attacks: 15 damage (armor reduces to ~8)]
[Guardian 1: 150 -> 142]
[Guardians attack: 60 damage -> 12 (cover)]
[Player: 100 -> 88]

### Rounds 2-18
[Continued hit-and-run]

Each round: ~8 damage dealt, ~12 damage received
Player uses healing potion every ~4 rounds

After 18 rounds:
- Guardian 1: 142 -> 0 (destroyed)
- Player: ~40 health, 3 potions remaining, hypothermia building

### Rounds 19-36
[Second guardian]

Guardian 2: 150 -> 0
Player: critical health, no potions, high hypothermia

[OBSERVATION: Combat IS possible but extremely resource-intensive. Not recommended. Puzzle solutions are clearly preferable.]

[DESIGN INPUT: Combat should remain an option but should feel like "hard mode." Players who insist on fighting can win, but at great cost.]

---

## Summary Tables

### Design Inputs Generated

| ID | Input | Value | Notes |
|----|-------|-------|-------|
| DI-FR-1 | Hot springs cure hypothermia instantly | Full cure | Creates safe haven |
| DI-FR-2 | Cold weather gear halves hypothermia gain | 50% reduction | Basic protection |
| DI-FR-3 | Cold resistance cloak provides immunity in cold, resistance in freezing | Full immunity / 50% | Major reward |
| DI-FR-4 | Salamander warmth aura provides cold immunity | While nearby | Companion benefit |
| DI-FR-5 | Password has three parts | Element + element + joining word | "Fire-that-gives-life and water-that-cleanses, united in purpose" |
| DI-FR-6 | Partial password from wall inscriptions | Enough to deduce full | Rewards careful reading |
| DI-FR-7 | Guardians don't leave temple | Territorial | Escape always possible |
| DI-FR-8 | Guardians pause at threshold | Don't attack in doorway | Allows observation |
| DI-FR-9 | Salamander heated stone lasts ~20 turns | Portable warmth | Creates bond, enables cave exploration |
| DI-FR-10 | Fire crystal in temple side chamber | Fire-aspected gift | Enables full salamander befriending |
| DI-FR-11 | Control crystal gives full golem control | Guardians serve player | "Best" solution, hardest to find |
| DI-FR-12 | Telescope reveals NPC states in other regions | Strategic information | Major reward for completion |
| DI-FR-13 | Combat is possible but resource-intensive | ~36 rounds for both guardians | Hard mode only |

### Questions Raised

| ID | Question | Proposed Resolution |
|----|----------|---------------------|
| Q-FR-1 | Where exactly is control crystal in caves? | Side passage, requires thorough exploration. Not on main path. |
| Q-FR-2 | Can player get multiple salamanders as companions? | No - only lead salamander. Others stay at springs. |
| Q-FR-3 | What happens if salamander companion enters water area? | Salamander refuses at boundary, waits for player to return. |
| Q-FR-4 | Does telescope reveal Garrett's exact location or just "movement in caves"? | General hint only - "eastern caves, movement visible." Not exact. |
| Q-FR-5 | Can player use golem servants for combat elsewhere? | No - guardians won't leave temple even with control crystal. |
| Q-FR-6 | What if player destroys guardians AND finds control crystal later? | Crystal is useless - guardians are gone. Consequence of violence. |

### Mechanisms Required

| Mechanism | Status | Notes |
|-----------|--------|-------|
| Hypothermia condition with severity levels | Needed | Progression, effects, recovery |
| Temperature zones (normal/cold/freezing/extreme) | Needed | Different progression rates |
| Cover system for combat | Needed | Pillar cover reduces damage 80% |
| Password/phrase recognition | Needed | Multi-part password matching |
| Item extraction requiring heat | Needed | Melting ice mechanic |
| Portable warmth items with duration | Needed | Heated stone, fire crystal |
| Telescope information reveal | Needed | Shows NPC states across regions |
| Companion warmth aura | Needed | Salamander provides immunity while nearby |

### Gameplay Observations

**Positive:**
- No time pressure creates different feel from Sunken District - methodical, exploratory
- Hot springs as sanctuary is satisfying - clear safe zone
- Multiple golem solutions all feel valid (password, crystal, combat)
- Salamander befriending feels earned and provides meaningful reward
- Telescope reward is powerful and appropriate for completing region
- Environmental challenge (cold) creates tension without frustration

**Concerns:**
- Salamander companion may trivialize cold hazard too much (but feels earned)
- Combat path may be TOO punishing - even optimized, it's brutal
- Fire item scarcity could frustrate players who don't find fire crystal
- Password clues might be too obscure without full inscription reading

**Potentially Boring Sections:**
- Multiple trips between hot springs and other areas (but this is pacing)
- Ice extraction is just "wait N turns"

**Frustrating Sections:**
- Player who gave away only torch might feel stuck
- Combat without preparation is nearly guaranteed death
- Missing side chamber with fire crystal could block salamander path

---

## Paths Not Yet Explored

- [ ] What if player attacks salamanders?
- [ ] Ritual offering path (fire-aspected item + hot springs water)
- [ ] What telescope reveals about each specific region in detail
- [ ] Player entering observatory without any cold protection (5 turn limit)
- [ ] What happens to heated stone if player doesn't return it?
- [ ] Cross-region: bringing ice crystals to Myconids
- [ ] Cross-region: bringing frost lily to Bee Queen
