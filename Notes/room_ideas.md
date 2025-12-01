# 100 Adventure Game Room Ideas (Full Detailed Version)

---

## A. Classic Dungeon / Crypt (1–15)

### 1. Echoing Antechamber (Sound Puzzle)
Stone chamber with three archways and a dry fountain. Each arch has a carved face. Speaking different words causes different echoes; only one echo reveals a hidden niche with a key. The engine needs: *say* actions, per-arch echo responses, and a stateful “correct phrase spoken” flag to open the niche.

### 2. Guardian Statue Hall (Conditional Combat)
Long hall lined with suits of armor. One armor animates only if the player is carrying a forbidden item (e.g., cursed gem). If they drop or consecrate it, the statue becomes an ally instead of an enemy. Tracks: inventory flag, alternate combat vs. companion behaviors, and a tiny altar as the “fix.”

### 3. Collapsing Bridge Cavern (Timed Escape)
Rope bridge over a chasm. Crossing triggers rumbling; on each turn, support ropes fray. Player can reinforce with spare rope or a spell, or dash across under a strict turn limit. Failure drops them into a lower “Broken Bones Grotto” with different loot and injuries.

### 4. Runic Floor Grid (Path Logic)
Square room with a grid of rune tiles. Some runes react to specific inventory (e.g., glowing when holding a sun medallion). Stepping on wrong tiles triggers lightning. Puzzle: walk a path spelling a hidden word found elsewhere. Implement as a sequence check of stepped tiles.

### 5. Crypt of False Names (Lore Puzzle)
Sarcophagi line the walls, each carved with wrong names. A ghost whispers clues about the “true” names (from prior NPC dialogue or documents). Typing the correct name at the right coffin causes it to open, yielding a relic. Track: in-game documents as hint sources, name parser, coffin-open states.

### 6. Spider Web Gallery (Environmental Hazard)
Narrow corridor thick with webs. Moving too quickly or swinging a weapon disturbs a giant spider. Careful actions (burning a small section with a torch, gently cutting webs) let the player pass without combat. The room stresses “gentle vs. reckless” variants of the same verbs.

### 7. Well of Reflections (Choice / Alignment)
Circular chamber with a deep, glowing well. Looking in shows a vision of the protagonist committing mercy or cruelty, depending on their past choices. Tossing different items in (weapon vs. flower vs. coin) applies a moral alignment tag that later affects NPC reactions and certain spells.

### 8. Skeleton Orchestra (Pattern Puzzle)
Abandoned hall with skeletal musicians posed mid-performance. Each skeletal instrument has a clue (scratched notes, broken strings). Player must arrange them on a stage in a specific order to match a melody heard in another area. Success opens a hidden backstage door.

### 9. Blood-Runes Sacristy (Resource Trade-off)
Small room with an altar and a rune circle. Player can pay HP (or a rare blood reagent) to charge a powerful sigil that will disarm traps for the next N rooms. Good for testing persistent status effects and “trade HP for safety” mechanics.

### 10. Coffin Maze (Spatial / Mapping)
Cluster of stone coffins that act as teleporters. Climbing into one and closing the lid transports the player to another coffin. Insides are marked with faint sigils giving orientation clues. The puzzle is a graph of teleports; good for testing your framework’s room graph and mapping.

### 11. Mushroom Grotto (Light / Growth)
Underground garden of bioluminescent fungi. Some mushrooms glow brighter if given water; others shrink from light. Player manipulates brightness to reveal a hidden sigil on the ceiling and to lure a shy creature out of a hole. Needs dynamic room description based on “light level” variable.

### 12. Whispering Door (Password via Eavesdropping)
Ancient door with ear-shaped carvings. It will not open until it “hears” a phrase spoken *by another NPC*. Player must lure, frighten, or charm an NPC into shouting that phrase nearby. Tests multi-room NPC pathing and overheard speech.

### 13. Weighted Idol Chamber (Physics-ish)
Pedestal holding a golden idol, surrounded by pressure plates. Removing idol collapses ceiling unless weight is replaced closely enough. The player can experiment with objects of different weights; text feedback hints at plates being “almost” satisfied. Good for testing numeric thresholds.

### 14. Ossuary of Borrowed Bones (Crafting / Body Parts)
Stacks of labeled bones. A skeletal guardian is missing specific bones (femur, jaw, rib). Assembling the correct set from random piles grants safe passage. Using wrong bones yields a malformed, hostile skeleton. You track items by type tags and assemble a “recipe.”

### 15. Singing Stalactites Cavern (Musical Code)
Cavern where stalactites resonate different notes when struck. A score carved on the wall shows a short melody. Correct sequence causes stalactites to shatter, revealing crystal shards or freeing an imprisoned spirit. Needs turn-ordered actions and a reset if the player makes noise out of order.

---

## B. Mansion / Urban Mystery (16–30)

### 16. Clockmaker’s Workshop (Temporal Gating)
Room cluttered with half-disassembled clocks. Central clock controls local time-of-day variable. Winding it advances time, changing NPC schedules and opening/closing other rooms (e.g., guards off shift at “night”). The player must set a specific time to reveal a secret hatch.

### 17. Portrait Gallery (Social / Perception)
Wall of family portraits, some eyes following the player. Examining reveals tiny mechanisms; moving portraits in the right sequence opens a panel. Sequence clue hidden in gossip: which relatives despised one another. Tests your framework’s ability to store NPC relationship hints and apply them to puzzles.

### 18. Locked Study with Listening Tube (Audio Clue)
Study door locked from inside. A brass listening tube leads under the door. Using it you hear an NPC muttering numbers or words that form a combination. If the player disturbs them elsewhere, they mutter a *different* combination leading to an “incorrect but interesting” outcome.

### 19. Greenhouse of Exotic Poison (Stealth / Mitigation)
Glasshouse full of toxic pollen. Entering unprotected slowly applies a “poisoned” condition each turn. Clue: gardener’s notes about safe paths or protective masks. Pollen also affects enemies, so the player can kite them in. Good for lingering environmental hazards.

### 20. Ballroom with Ghostly Waltz (Pattern / Timing)
Empty ballroom where spectral dancers appear at intervals. Crossing the room requires moving in step with a ghostly waltz pattern (N, N, E, S, etc.). Missteps cause cold damage or teleportation back to entrance. The pattern may be hinted in music notation or an old dance manual.

### 21. Servant Passage Network (Secret Shortcuts)
Narrow, dusty corridors behind walls. Certain push-panels in other rooms open into this network. Within, player finds eavesdropping peepholes (view descriptions of other rooms), quick shortcuts, and hidden stashes. Good for stress-testing viewpoint and cross-room descriptions.

### 22. Kitchen of Infinite Leftovers (Looping Room)
Kitchen resets every time you leave and re-enter: pots move, NPC cook repeats a routine, leftovers regenerate. Exploit: take advantage of infinite food or repeated events to create stackable items (e.g., empty bottles) or to set up a “Groundhog Day” style puzzle that needs multiple runs.

### 23. Household Shrine (Boon or Curse)
Small household altar. Offering different items yields randomized blessings or curses: temporary stat buffs, extra luck, or haunting. The shrine “remembers” how respectful the player was earlier (e.g., if they vandalized religious objects, results skew negative).

### 24. Stuffed Trophy Room (Mimic / Ambush)
Room filled with animal trophies. One mount is a living predator playing dead. If the player examines too closely or takes its teeth/trophy, it attacks. If they bring it something (raw meat, special scent), it becomes a secret ally or mount.

### 25. Sealed Panic Room (Constrained Escape)
Small metal-lined room, only one door, reinforced. Once the player enters and door locks, they must find a way out using limited in-room resources: ventilation duct, emergency codes scratched on wall, hidden mechanism behind painting. Great to test “single-room mini-escape” logic.

### 26. Auction Hall (Social / Economics)
NPCs bidding on items. Player can bid, bluff, or sabotage rivals. Items later serve as puzzle pieces elsewhere. Implement timed auction rounds, NPC bidding logic, and consequences if the player cheats or refuses to pay.

### 27. Nursery of Forgotten Toys (Emotion + Secret)
Child’s room with broken toys, tiny chairs. Interacting with toys triggers ghost-child responses: giggles, tantrums, or clues. Arranging three specific toys in a circle “starts a game” that reveals a hidden compartment. Tests subtle, emotional feedback and multi-object configuration.

### 28. Tailor’s Fitting Room (Disguise Mechanics)
Mirrors, mannequins, racks of clothes. Player can assemble disguises by combining clothing pieces to pass as different factions or social classes. A guard at the next area checks for specific uniform features (badge, color). Good for testing composite gear and conditional access.

### 29. City Rooftop Garden (Verticality / Risk)
Open rooftop with precarious edges. Player can attempt risky jumps to adjacent roofs, climb trellises, or drop into a skylight. Failed jumps cause injuries or landing in a lower, unwanted area. Wind or weather modifiers increase difficulty, giving your engine excuses for conditional text.

### 30. Printing Press Basement (Info Manipulation)
Underground printing press running off counterfeit pamphlets. Player can rewrite a leaflet to change public opinion, altering NPC crowd behavior in a later plaza scene. Needs persistent “city sentiment” flags that unlock or block routes.

---

## C. Wilderness / Travel (31–45)

### 31. Foggy Forest Crossroads (Direction Confusion)
Four-way junction in dense fog. Directions loop unless player uses a landmark (tie ribbons, carve tree) or uses wind/sun clues. Implement as dynamic exits that change until a hidden “orientation” condition is satisfied.

### 32. Riverside Ford (Variable Depth)
Shallow river crossing with slippery rocks. Depth changes with previous weather; if recent rain, dangerous current. Player can build a makeshift bridge, use rope, or wait for weather to change. Tests global environmental variables and delayed consequences.

### 33. Abandoned Campsite (Story Clues)
Old camp: cold firepit, tattered tents, some personal belongings. Player can reconstruct what happened by examining items, getting partial story fragments. If they perform a small ritual (burying remains, fixing a memorial), a grateful spirit appears with travel shortcuts.

### 34. Cliffside Nest (Vertical Challenge)
Narrow ledge high above sea. Rare eggs sit in a nest. Retrieving them safely requires secure climbing gear or a wind-calming spell. Disturbing nest attracts a flying predator. The room focuses on equipment gating and risk vs. reward.

### 35. Fairy Circle Clearing (Teleport Network)
Ring of mushrooms that teleports player to other fairy circles scattered around the map with some pattern (moon phase, direction of entry). Misuse may drop them in a dangerous “wrong circle” with hostile fey.

### 36. Ancient Standing Stones (Constellation Puzzle)
Stone ring carved with star symbols. At night, aligning the stones to match the sky opens a portal or cache. During day, puzzle impossible unless you find a star chart. Needs time-of-day gating and multi-step alignment states.

### 37. Hunter’s Blind (Ambush / Stealth)
Concealed hideout overlooking animal path or patrol road. Player can wait in ambush, set snares, or observe NPC routines. Great for testing long “wait” actions and scheduled events.

### 38. Glacial Crevasse (Ice Hazard)
Narrow ice bridge over deep crack. Heat sources weaken bridge; cold spells strengthen it. Player chooses between riskier direct crossing or detour through icy tunnels with different enemies.

### 39. Bee-Hive Tree (Diplomacy vs. Violence)
Huge tree with a giant hive. Honey is potent healing or magic reagent. Smoke, special herbs, or a druidic song calm the bees. Attacking hive unleashes a damaging swarm and possibly burns the forest.

### 40. Abandoned Watchtower (Multi-Level)
Crumbling tower with several floors. Interior stairs partially collapsed; climbing outside is perilous. Each floor has different vantage points and loot. The tower can serve as a fast-travel anchor once repaired.

### 41. Haunted Waystone (Navigation Aid)
Weathered monolith at crossroads. Touching it reveals ghostly arrows indicating distant key locations, updated as player acquires new map intelligence. A hostile spirit may attack if the waystone is defiled (e.g., player chisels pieces off).

### 42. Flooded Tunnel (Breath / Time Limit)
Short underwater passage connecting two shore caves. Player must manage breath or use potions/gills. Underwater objects behave differently: can’t use fire; some items float away.

### 43. Desert Mirage Caravan (Illusion)
Apparent hospitable caravan appears in the dunes. Close inspection reveals inconsistencies. If player treats it as real (eating food, resting), they wake later with lost items or displaced on map. If they break the illusion, they get a real relic hiding inside.

### 44. Lightning-Struck Oak (Random Event)
Ancient tree frequently hit by lightning; metal items attract bolts in storms. Tying a conductive rod here can power a magic device elsewhere. Entering during storm risks damage but can supercharge an artifact.

### 45. Ravine Ropeway (Mechanical Transport)
Makeshift cable with a hanging basket crossing a ravine. Mechanism requires counterweight; player can use stones or bodies. Mid-crossing, enemies may cut rope unless previously negotiated or neutralized. Good for multi-turn traversal events.

---

## D. Magical / Surreal (46–60)

### 46. Library of Unwritten Books (Generative Clues)
Shelves full of blank books that fill with text describing the reader’s possible futures. Reading too much can create a “prophecy lock” that restricts choices, but allows meta-hints. Destroying a book severs a future branch. Great for testing conditional text and future-prediction flavor.

### 47. Mirror Labyrinth (Self-Interaction)
Hall of mirrors that reflect slightly different versions of the PC. One reflection acts independently, mimicking earlier decisions. Player can trade items or info with own reflection, or trap an enemy reflection instead.

### 48. Colorless Garden (Color as Resource)
Garden drained of color. Player can “carry” hues in a prism or paintbrush; applying color to objects animates them. Coloring a statue makes it talk; coloring a door sigil unlocks it. Track “color charges” as a resource.

### 49. Gravity-Inverted Chamber (Movement Twists)
Entering flips gravity: ceiling becomes floor. Exits that were inaccessible now reachable. Items not anchored fall to previous “ceiling.” Toggling gravity repeatedly rearranges the room state; some puzzles require stacking objects in both orientations.

### 50. Dreaming Inn Room (Meta Save/Load)
Room at a magical inn. Sleeping here lets the player revisit earlier scenes in dream form, replaying events with limited interaction to change flags (e.g., plant an item retroactively). Your framework can treat these as special “flashback” rooms that alter variables.

### 51. Chessboard Hall (Symbolic Combat)
Floor painted as chessboard. Enemies move like chess pieces; player movement restricted similarly while in room. Capturing an “enemy king” opens exit. Good for turn-based, grid-constrained logic.

### 52. Hall of Echoed Commands (Parser Twist)
Room where last N commands repeat as ghostly actions by spectral copies. Player can set up complex sequences (“drop rope”, “pull lever”) and then use echoes to operate mechanisms at a distance.

### 53. Oracle’s Mosaic Pool (Question Economy)
Reflecting pool that answers yes/no questions about the world but charges a cost per question (HP, rare gem, or future curse). Player uses it to solve otherwise opaque riddles. Tests flexible question parser or a curated set of questions.

### 54. Time-Splintered Foyer (Parallel States)
Single room shown in three time snapshots: past (ruined), present (intact), future (overgrown). Player can shift between snapshots; actions in past affect present layout (breaking wall), actions in present affect future (plant grows into climbable vine).

### 55. Living Painting Gallery (Portal / NPCs)
Paintings animate. Stepping into them transports you to small “micro-rooms” encapsulated in paintings (seaside, battlefield, tower). Bringing objects from one painting-space to another yields strange combinations.

### 56. Room of Spoken Spells (Word as Item)
Room where words said aloud become physical scrolls (e.g., SAY “FIRE” generates a fragile fire scroll). Overuse attracts attention of a guardian that punishes careless language. People who lie here generate cursed scrolls.

### 57. Staircase That Counts You (Numerical Condition)
Seemingly endless staircase. The number of steps you’ve taken matters; only on the 13th step performed *while carrying exactly 3 items* does a side door appear. Tests subtle cumulative conditions across turns.

### 58. Hall of Forgotten Names (Identity Puzzle)
Door only opens for someone who “does not know their own name.” Player must temporarily surrender or obscure identity (mask, spell, document burning). While nameless, NPC reactions and some abilities change.

### 59. Tessellated Puzzle Room (Spatial Logic)
Floor composed of sliding tiles forming magical sigils. Player must rearrange tiles into a pattern to route mana flows to the door. Stepping on active lines may buff or debuff. Good for tile-based reconfiguration.

### 60. The Empty Stage (Performance / Emote Puzzle)
Theater stage with invisible audience. Performing certain emotes or actions in sequence (bow, monologue, joke, dramatic death) elicits applause that powers a magical curtain mechanism. NPC hints describe the “right” performance.

---

## E. Technology / Sci-Fi (61–75)

### 61. Airlock Antechamber (Pressurization)
Room with inner and outer doors, pressure controls, and suits. Incorrect sequence decompresses, damaging or ejecting items. Correctly using vents and suits allows access to vacuum exterior.

### 62. Server Core Room (Data Maze)
Cylindrical chamber lined with humming server towers. Plugging in a portable console opens a textual “filesystem dungeon” within your UI. Solving mini-puzzles in directories (passwords, logs) unlocks physical doors or drones.

### 63. Teleport Pad Hub (Routing Puzzles)
Central teleporter with configurable destination markers. Player must repair pad and set coordinates using data logs. Some destinations are unsafe until you toggle environmental controls elsewhere.

### 64. Robot Repair Bay (Ally Construction)
Workbenches, spare parts, diagnostic terminal. Player can build or customize a robot companion by combining parts (stealth chassis, heavy arms, hacking tools). Different builds change solutions to later rooms.

### 65. Grav-Tram Platform (Moving Platform)
Station where a tram arrives on schedule. Hacking the schedule accelerates or slows tram, necessary to time boarding past security sensors or enemies. Good for timed arrival and “wait for train” events.

### 66. Containment Cell Block (Security Puzzle)
Row of sealed cells containing aliens, humans, or test monsters. Console allows releasing selected cells or gas. Player can choose to free allies, create chaos, or extract specific specimens for later barter.

### 67. Holodeck Scenario Room (Configurable Environment)
Room whose walls project different environments. Player changes “programs” to alter physical layout: jungle, city, desert, each with different interactables. Underneath, the exit panel is locked; they must pick a scenario that reveals it.

### 68. Cryosleep Vault (Memory / Identity)
Rows of pods, some occupied. Interacting shows dream logs or past data about the world’s backstory. The PC might find their own frozen body, raising identity questions and toggling special narrative flags.

### 69. Power Relay Junction (Resource Routing)
Grid of switches directing power to shields, doors, and life support. Player must reroute energy from nonessential systems, accepting consequences (dark corridors, weakened shields elsewhere) to open a specific door.

### 70. Observation Deck with Laser Grid (Line-of-Sight)
Transparent floor above a laser security grid. From the deck, player can watch guard patrols and program a drone path. Later, traversing grid area uses that programmed path to auto-move or opens a safe route.

### 71. Drone Swarm Hangar (Command Puzzle)
Room with inactive drone swarm. Issuing simple text commands (“FORM LINE”, “FOLLOW ME”, “BLOCK DOOR”) creates a flexible puzzle tool. Miscommanded drones may block exits or trigger alarms.

### 72. Biohazard Lab (Contamination State)
Lab with clearly marked contamination zones. Crossing zones without suit tags the player as contaminated, changing NPC reactions and locking access to clean areas until decontamination. Good for “status-affects-gating.”

### 73. Zero-G Maintenance Shaft (3D Movement)
Shaft with handholds and spinning fans. In zero-g, directions are non-intuitive; “up/down” is replaced with relative directions. Orienting correctly is required to reach side hatches and to avoid rotating blades.

### 74. AI Core Chamber (Negotiation Boss)
Central AI unit projecting holographic avatar. Defeating it can be via combat (EMP, hacking) or debate (presenting evidence of contradictions, appeals to logic/humanity). Each approach toggles different world-state outcomes.

### 75. Nanotech Fabrication Room (Crafting Sandbox)
Printer that can fabricate small objects if given raw matter and a blueprint file. Player finds or writes blueprints in code-like text; syntax errors create flawed, humorous items. The room is a flexible way to test your crafting mechanics.

---

## F. Social / Political / Civilized (76–90)

### 76. Council Chamber (Multi-NPC Dialogue)
Round table with factions arguing. Player can intervene, present evidence, or bribe members. Outcome sets political alignment flags, affecting guards, merchants, and later quests.

### 77. Guild Recruitment Hall (Build / Progression)
Room where player can formally join organizations. Each guild provides different perks and room access. Joining one closes off another. Good for testing mutually exclusive flags and faction-based gating.

### 78. Tavern Common Room (Rumor Hub)
Busy tavern with multiple NPCs. Player can overhear rumors, play games, start fights, or buy information. Rumors are tagged to future rooms, enabling optional hints and side paths.

### 79. Market Bazaar (Barter / Haggling)
Stalls selling gear, curios, and secrets. Haggling mini-puzzle: choose tone (flatter, threaten, reason) to affect prices based on merchant traits. Also opportunities for pickpocketing or con games.

### 80. Courtroom of Trial by Story (Testimony Puzzle)
Player accused of a crime. They must cross-examine NPCs, highlight contradictions, and present evidence found in other rooms. Failure may lead to imprisonment or execution scenes; success gains prestige or a favor.

### 81. Bank Vault (Heist)
Security-heavy room with combination locks, magical wards, and patrolling guards. Multiple solutions: stealth, hacking, social engineering (impersonate manager), or brute force. Perfect for testing your system’s flexibility.

### 82. Orphanage Playroom (Moral Choice)
Children ask for toys, food, or help. Player can donate, ignore, or exploit. Later, these children may appear as helpers or foes elsewhere. The room is simple but far-reaching in consequences.

### 83. Black Market Back Room (Illegal Goods)
Behind a shop, shady dealers offer contraband items that break rules (lockpicks that open “unpickable” doors, cursed weapons). Buying or using them flags the player as criminal, affecting patrol behaviors.

### 84. Temple Confessional (Secret Channel)
Booth where player can confess crimes or pretend to. Priest’s response depends on sincerity (tracked against player log of deeds). Confession can clear some infamy flags, but might reveal secrets to enemies.

### 85. Town Hall Archive (Search Mechanics)
Stacks of documents and index cards. Player must use search commands (“search for ‘bridge permits’”) to find specific records that unlock hidden routes or expose corruption. Good for testing text search and meta-navigation.

### 86. Training Dojo (Skill Checks)
Instructors offer practice dummies and sparring. Player can learn new combat moves via mini-challenges. The room can be re-entered to test progression: instructors comment differently on novice vs. veteran stats.

### 87. Public Square with Speaker’s Platform (Crowd Logic)
Raised platform where someone gives a speech. Player can heckle, support, or out-argue the speaker. Each choice changes crowd mood and may trigger riot, celebration, or targeted hostility.

### 88. Artist’s Studio (Forgery / Creative Puzzles)
Room with paints, canvases, and unfinished works. Player can forge paintings or documents for use in heists or diplomacy. Quality depends on skill checks or how carefully they followed reference descriptions.

### 89. Embassy Reception Room (Cross-Cultural Etiquette)
Diplomats from various nations. Player must observe or learn etiquette quirks (bow depth, taboo topics) to avoid offense and to gain visas/passports that unlock new regions.

### 90. Prison Visiting Room (One-Shot Interactions)
Glass-separated booths with prisoners. Each prisoner can be visited once; they may give key intel, lies, or side-quests. Player’s reputation determines which prisoner trusts them.

---

## G. Boss, Finale, or Set-Piece Rooms (91–100)

### 91. Multi-Phase Boss Arena (Environment-Driven Fight)
Circular chamber with shifting platforms and elemental vents. Boss changes element based on vents player activates; clever use of vents can weaken or trap boss. Exit only opens when specific environmental conditions are met after its defeat.

### 92. Ritual Circle Chamber (Interruptible Ceremony)
Cultists mid-ritual. Player arrives at different stages depending on timing. Early arrival allows sabotage; late arrival means fighting a summoned demon. Room state snapshot depends on when player enters.

### 93. Hall of Choices (Ending Selector)
Long corridor with branching alcoves, each representing an ideology or faction. Stepping into one locks in a route to a specific endgame path, changing which final rooms are accessible. Good for explicit route selection.

### 94. Memory Theater (Recap and Reinterpret)
Amphitheater where scenes from earlier in the game replay as illusions. Player can step into and slightly alter some of them (small retcons) to finalize how allies and enemies align for the finale.

### 95. Vault of All Trades (Ultimate Loot Puzzle)
Room filled with powerful items, but taking one causes others to vanish. Player must choose one “build-defining” artifact. The vault tracks their playstyle and subtly highlights items that fit or subvert it.

### 96. Fractured Reality Nexus (Logical Final Puzzle)
Room with floating platforms representing core game systems (combat, stealth, magic, social). To stabilize reality and open final door, player must demonstrate mastery by solving a mini-challenge for at least two systems they’ve leaned on.

### 97. Throne Room with Empty Throne (Power Vacuum)
No boss, just an empty throne and gathered NPCs. Player can claim throne, nominate another, or destroy it. Their choice determines epilogue structure and whether the game continues in “post-game governance” mode.

### 98. Last Safe Room (Pre-Finale Hub)
Cozy room with save point, merchant, companions, and a view of impending catastrophe outside. Conversations here lock in personal subplots and endings (who stays, who leaves, who sacrifices themselves).

### 99. Hall of Unanswered Questions (Meta / Secrets)
Walls scroll with questions the game never fully answered. Interacting with them reveals hint trails for hidden endings, secret bosses, or developer commentary. Great for optional deep-dives.

### 100. The Exit Door (Literal End Screen Room)
Bare room with a single door labeled *EXIT*. Opening it triggers the end credits—but the player can also try to dismantle the door, go behind it, or refuse to leave. Your engine can handle multiple “post-credits” branches or looping them back to an earlier chapter.
