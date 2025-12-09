# Object-Relative Positioning in Room Design (No Zones)  
**Updated Examples for Game Authors**

This document presents **4 worked room examples** that rely **only on spatial relations between entities** (and wall sides), with **no zone system**.

Instead of zones, we use object-relative relations like:

- **NEAR(entity, object)** – the player is close enough to interact normally  
- **BEHIND(entity, object)** – the player is using something as cover or concealment  
- **ON_SIDE(entity, object, side)** – e.g., “at the left side of the desk”  
- **UNDER(entity, object)** – hiding/crawling, or accessing the underside  
- **ATTACHED_TO(object, wall_side)** – for things mounted on walls  
- **IN_FRONT_OF(entity, object)** – facing something directly  

Walls are used as **spatial anchors** (north wall, east wall), but are not directly interacted with as items.

These examples include:

1. A non-combat puzzle room (alchemist’s workshop)  
2. A sensory puzzle (whispering library)  
3. A **combat** example using cover and reach  
4. A **stealth** example using concealment and line-of-sight  

---

## 1. The Alchemist’s Bench – Precision Interactions Without Zones

### 1.1 Room Overview

The alchemist’s workshop has a long bench with three important objects:

- A **mortar and pestle** (left side of bench)  
- A **burner** (center of bench)  
- A **glass alembic** (right side of bench)  

There’s also a **cabinet** on the north wall with rare ingredients.

The player must:

- Stand **at the left side** to grind herbs  
- Stand **at the center** to heat a mixture  
- Stand **at the right** to distill vapors  
- Stand **in front of the cabinet** to unlock it

No zones are used—only positional relations between player and objects.

---

### 1.2 Spatial Relations in Play Terms

We imagine the engine maintaining relations like:

- `ON_SIDE(player, bench, "left")`  
- `ON_SIDE(player, bench, "center")`  
- `ON_SIDE(player, bench, "right")`  
- `IN_FRONT_OF(player, cabinet)`  

The author doesn’t need to think in terms of coordinates—just **which side of which object** the player is at.

When the player types:

- `APPROACH MORTAR` → engine sets `ON_SIDE(player, bench, "left")`  
- `APPROACH BURNER` → engine sets `ON_SIDE(player, bench, "center")`  
- `APPROACH ALEMBIC` → engine sets `ON_SIDE(player, bench, "right")`  
- `APPROACH CABINET` → engine sets `IN_FRONT_OF(player, cabinet)`  

---

### 1.3 Interaction Examples

**A. Grinding herbs**

If player is **not** on the left:

> You’re too far from the mortar to grind anything. Try moving to the left side of the bench.

If `ON_SIDE(player, bench, "left")` holds:

> You crush the dried leaves into a fine, aromatic powder.

**B. Heating the mixture**

Requires `ON_SIDE(player, bench, "center")`:

> Standing at the center of the bench, you hold the flask above the burner and apply heat.

**C. Distilling vapors**

Requires `ON_SIDE(player, bench, "right")`:

> You lean over the alembic and guide the condensed vapors into a waiting vial.

**D. Opening the cabinet**

Requires `IN_FRONT_OF(player, cabinet)`:

> From here you can reach the cabinet door and its intricate lock.

This example shows how object-relative relations let one physical object (the bench) hold multiple spatially distinct interaction points without any notion of “zones.”

---

## 2. The Whispering Library – Sound Puzzle by Shelves

### 2.1 Room Overview

The library has:

- A long line of **shelves along the north wall**  
- A **reading desk** in the center of the room  
- A **whispering tome** on one particular shelf  
- Several **shelf segments** (left, middle, right)

The puzzle:  
The whispers are only intelligible when the player is **near the correct shelf segment**.

---

### 2.2 Spatial Relations

We treat each shelf segment as an object:

- `shelf_left`  
- `shelf_middle`  
- `shelf_right`  

The player can be:

- `NEAR(player, shelf_left)`  
- `NEAR(player, shelf_middle)`  
- `NEAR(player, shelf_right)`  
- Or not near any shelf (e.g., `NEAR(player, desk)`)

The whispering tome is:

- `ATTACHED_TO(tome, north_wall_side)`  
- Conceptually located on `shelf_middle`

---

### 2.3 Interaction Examples

**A. Listening from the desk**

If `NEAR(player, desk)`:

> The murmurs are too faint from here — you can’t make out the words.

**B. Standing by the wrong shelf**

If `NEAR(player, shelf_left)`:

> The whispers grow slightly louder, but the echoes distort them; you still can’t understand.

**C. Standing by the correct shelf**

If `NEAR(player, shelf_middle)`:

> The murmurs sharpen into words: “Third shelf, seventh volume…”

**D. Inspecting the tome**

The engine requires:

- `NEAR(player, shelf_middle)`  
- and the player targeting the correct book

Then:

> You run your fingers along the spines until one gives slightly — the whispering tome.

This example demonstrates **object-relative proximity** as a way to gate information and reveal clues.

---

## 3. Combat Example – The Pillars of the Great Hall

### 3.1 Scenario Overview

The great hall contains:

- A series of **stone pillars**  
- An **enemy archer** on a balcony  
- A **melee guard** on the floor  
- The player starting near the entrance

Combat is influenced by whether the player is:

- **IN_FRONT_OF** a pillar  
- **BEHIND** a pillar (relative to the archer’s line of fire)  
- **NEAR** the guard (for melee)

---

### 3.2 Spatial Relations

Key relations:

- `BEHIND(player, pillar_1)` relative to the archer  
- `IN_FRONT_OF(player, pillar_1)` if the player steps around it  
- `NEAR(player, guard_1)` when close enough for melee  
- `FAR_FROM(player, guard_1)` when out of melee range  

The engine might treat “behind a pillar” as:

- `BEHIND(player, pillar_1)` → archer has **no line of sight**  
- `IN_FRONT_OF(player, pillar_1)` → archer has **line of sight**, can shoot

---

### 3.3 Combat Interaction Examples

**A. Taking cover**

Player chooses:

> TAKE COVER BEHIND PILLAR

Engine sets:

- `BEHIND(player, pillar_1)`  

While this holds:

- Archer’s attacks either **miss** or have greatly reduced chance to hit.  
- Narration:

> You press yourself behind the stone pillar. Arrows clatter harmlessly against the far side.

**B. Breaking from cover**

Player decides:

> STEP OUT FROM BEHIND PILLAR

Engine clears `BEHIND(player, pillar_1)` and sets `IN_FRONT_OF(player, pillar_1)`.

Archer can now attack freely:

> You step into the open; an arrow thuds into the stone where your head was a heartbeat ago.

**C. Closing for melee**

Guard’s melee attacks require:

- `NEAR(player, guard_1)`  

When the player moves:

> RUSH GUARD

Engine sets `NEAR(player, guard_1)` (and clears other proximity relations as appropriate).

Now:

- Guard can use sword attacks.  
- Player’s melee attacks are available.

Attempting melee from afar:

> The guard is too far away for that; you’d need to close the distance first.

This example shows combat gameplay shaped by **cover and proximity**, expressed purely through **relations** rather than zones.

---

## 4. Stealth Example – The Gallery of Statues

### 4.1 Scenario Overview

A long gallery with:

- A series of **stone statues** along one side  
- A **patrolling guard** walking the length of the hall  
- A **door at the far end**  
- Sparse lighting, leaving some areas in shadow

The player must slip past the guard using **statues and shadows as cover**.

---

### 4.2 Spatial Relations

Useful relations:

- `BEHIND(player, statue_n)` – player is concealed behind statue n  
- `IN_SHADOW_OF(player, statue_n)` – player stands in its shadow, harder to see  
- `FACING(guard, direction)` – which way the guard looks  
- `IN_FRONT_OF(player, door_gallery)` – player is at the door and can open/lockpick it  
- `NEAR(player, guard)` – if the player blunders too close

We don’t track the whole room; we track **relations that matter** to stealth.

---

### 4.3 Stealth Interaction Examples

**A. Hiding behind a statue**

Player command:

> HIDE BEHIND STATUE

Engine sets:

- `BEHIND(player, nearest_statue)`  
- Optionally `IN_SHADOW_OF(player, nearest_statue)`

Guard’s detection check:

- If guard’s `FACING` is **away from the player** and `BEHIND(player, statue)` holds, detection chance is low.

Narration:

> You slip behind the statue; the guard’s footsteps echo past you as he patrols.

**B. Moving between cover**

Player:

> MOVE TO NEXT STATUE

Engine:

- Clears `BEHIND(player, old_statue)`  
- Sets `BEHIND(player, new_statue)`  

If the guard is facing the wrong way when the player crosses:

> You dart to the next statue while the guard’s back is turned.

If the guard is facing the player’s direction and the player is not behind something:

> The guard turns his head and narrows his eyes. “Who’s there?” He strides toward you.

**C. Approaching the door**

To use the door, the engine requires:

- `IN_FRONT_OF(player, door_gallery)`  
- And optionally **no** `NEAR(guard, player)` if the guard is too close

Attempt to open door from hiding:

> From behind the statue, you can’t reach the door.

Correct positioning:

> You slip to the door and grip the handle, praying it doesn’t creak.

If `NEAR(guard, player)` becomes true:

> The guard grabs your shoulder before you can open the door.

This illustrates stealth gameplay as **managing object-relative relations** rather than absolute positions or zones.

---

## 5. Takeaways for Authors

These updated examples show how you can:

- Use **object-relative relations** (`NEAR`, `BEHIND`, `IN_FRONT_OF`, `ON_SIDE`, `UNDER`, `IN_SHADOW_OF`) to express spatial logic.
- Craft puzzles where being at the **correct side of an object** matters.
- Implement combat where **cover** and **reach** alter what actions succeed.
- Build stealth scenarios where **line of sight** and **hiding spots** are modeled as relations, not coordinates.

No zones are involved.  
You focus entirely on **who is near what, who is behind what, and who is exposed to whom**.

That’s enough to create rich, spatially grounded gameplay that still fits your engine’s uniform, relational design.

---

**End of Document**
