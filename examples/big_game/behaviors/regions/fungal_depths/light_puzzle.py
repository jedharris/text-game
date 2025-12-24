"""Light Puzzle Mechanics for Fungal Depths.

Implements the mushroom watering puzzle in the Luminous Grotto.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult

# Vocabulary: wire hooks to events
# Note: Item use reactions are handled by infrastructure/item_use_reactions.py
# Note: Turn phase events are handled by infrastructure/turn_phase_dispatcher.py
# Note: Examine reactions are handled by infrastructure/examine_reactions.py
# Entities must have appropriate reaction configurations
vocabulary: Dict[str, Any] = {
    "events": []
}

# Mushroom effects when watered
MUSHROOM_EFFECTS = {
    "mushroom_blue": {"light": 1, "infection": 0, "safe": True},
    "mushroom_gold": {"light": 2, "infection": 0, "safe": True},
    "mushroom_violet": {"light": 0, "infection": 15, "safe": False},
    "mushroom_black": {"light": -2, "infection": 0, "safe": False},
}

# Light level needed to read ceiling
REQUIRED_LIGHT = 6

# How long mushrooms glow
GLOW_DURATION = 5


def on_water_mushroom(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle watering a mushroom to change light level.

    Uses bucket charges (max 3) to water mushrooms.
    Different mushrooms have different effects.

    Args:
        entity: The item being used (bucket with water)
        accessor: StateAccessor instance
        context: Context with target

    Returns:
        EventResult with mushroom effect
    """
    item_id = entity.id if hasattr(entity, "id") else str(entity)
    if "bucket" not in item_id.lower() and "water" not in item_id.lower():
        return EventResult(allow=True, feedback=None)

    target = context.get("target")
    target_id = target.id if target and hasattr(target, "id") else str(target) if target else ""

    # Check if target is a mushroom
    mushroom_key = None
    for key in MUSHROOM_EFFECTS:
        if key in target_id.lower():
            mushroom_key = key
            break

    if not mushroom_key:
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state

    # Check bucket has charges
    player = state.actors.get("player")
    if player:
        inventory = player.properties.get("inventory", {})
        # Handle dict or list inventory formats
        if isinstance(inventory, dict):
            bucket = inventory.get("bucket", {})
            if isinstance(bucket, dict) and bucket:
                charges = bucket.get("water_charges", 0)
                if charges <= 0:
                    return EventResult(
                        allow=True,
                        feedback="The bucket is empty. Fill it from the pool first.",
                    )
                bucket["water_charges"] = charges - 1
            else:
                # Fallback to state.extra for water charges
                water_charges = state.extra.get("bucket_water_charges", 0)
                if water_charges <= 0:
                    return EventResult(
                        allow=True,
                        feedback="The bucket is empty. Fill it from the pool first.",
                    )
                state.extra["bucket_water_charges"] = water_charges - 1
        else:
            # Simple inventory (list) - use state.extra for water charges
            water_charges = state.extra.get("bucket_water_charges", 0)
            if water_charges <= 0:
                return EventResult(
                    allow=True,
                    feedback="The bucket is empty. Fill it from the pool first.",
                )
            state.extra["bucket_water_charges"] = water_charges - 1

    effects = MUSHROOM_EFFECTS[mushroom_key]
    light_change = effects["light"]
    infection = effects["infection"]
    is_safe = effects["safe"]

    # Get location light level
    grotto = None
    for loc in getattr(state, "locations", []):
        if hasattr(loc, "id") and loc.id == "luminous_grotto":
            grotto = loc
            break

    if not grotto:
        # Fallback to extra
        current_light = state.extra.get("grotto_light_level", 2)
        state.extra["grotto_light_level"] = max(0, current_light + light_change)
    else:
        current_light = grotto.properties.get("light_level", 2)
        grotto.properties["light_level"] = max(0, current_light + light_change)

    new_light = (grotto.properties.get("light_level", 0) if grotto
                 else state.extra.get("grotto_light_level", 0))

    # Track glowing mushrooms for decay
    glowing = state.extra.get("glowing_mushrooms", {})
    glowing[mushroom_key] = GLOW_DURATION
    state.extra["glowing_mushrooms"] = glowing

    # Apply infection if dangerous
    if infection > 0:
        _apply_infection(state, player, infection)

    # Generate message based on mushroom type
    mushroom_name = mushroom_key.replace("mushroom_", "").capitalize()

    if mushroom_key == "mushroom_blue":
        msg = (
            f"The {mushroom_name} mushroom brightens with a steady blue glow. "
            f"Light level: {new_light}/{REQUIRED_LIGHT}"
        )
    elif mushroom_key == "mushroom_gold":
        msg = (
            f"The {mushroom_name} mushroom flares brilliantly, golden light "
            f"filling the chamber. Light level: {new_light}/{REQUIRED_LIGHT}"
        )
    elif mushroom_key == "mushroom_violet":
        msg = (
            f"The {mushroom_name} mushroom pulses rapidly, releasing a cloud "
            f"of spores! You cough as they fill your lungs. Light level: {new_light}/{REQUIRED_LIGHT}"
        )
    else:  # black
        msg = (
            f"The {mushroom_name} mushroom seems to drink the light, growing darker. "
            f"The chamber dims. Light level: {new_light}/{REQUIRED_LIGHT}"
        )

    # Check if puzzle solved
    if new_light >= REQUIRED_LIGHT and not state.extra.get("safe_path_known"):
        state.extra["ceiling_readable"] = True
        msg += "\n\nThe ceiling is now bright enough to read!"

    return EventResult(allow=True, feedback=msg)


def on_examine_ceiling(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Check if player can read the ceiling inscription.

    Only readable when light level >= 6.

    Args:
        entity: The thing being examined
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with examination result
    """
    entity_id = entity.id if hasattr(entity, "id") else str(entity)
    if "ceiling" not in entity_id.lower() and "inscription" not in entity_id.lower():
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state

    # Get light level
    grotto = None
    for loc in getattr(state, "locations", []):
        if hasattr(loc, "id") and loc.id == "luminous_grotto":
            grotto = loc
            break

    light_level = (grotto.properties.get("light_level", 2) if grotto
                   else state.extra.get("grotto_light_level", 2))

    if light_level < REQUIRED_LIGHT:
        return EventResult(
            allow=True,
            feedback=(
                "You can make out shapes on the high ceiling, but the light "
                "is too dim to read the ancient inscription."
            ),
        )

    # Readable - grant safe path knowledge
    state.extra["safe_path_known"] = True

    return EventResult(
        allow=True,
        feedback=(
            "In the bright light, ancient symbols become clear on the ceiling. "
            "They describe a path through the Spore Heart - where the air "
            "currents create pockets of clean breathing. You memorize the route. "
            "The way through the spores will be safer now."
        ),
    )


def on_light_decay(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Decay mushroom light over time.

    Glowing mushrooms dim after GLOW_DURATION turns.

    Args:
        entity: None (regional check)
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult (silent)
    """
    state = accessor.game_state
    glowing = state.extra.get("glowing_mushrooms", {})

    if not glowing:
        return EventResult(allow=True, feedback=None)

    # Decrement all glowing mushrooms
    expired = []
    for mushroom, turns_left in glowing.items():
        new_turns = turns_left - 1
        if new_turns <= 0:
            expired.append(mushroom)
        else:
            glowing[mushroom] = new_turns

    # Remove expired and reduce light
    if expired:
        total_light_loss = 0
        for mushroom in expired:
            del glowing[mushroom]
            effects = MUSHROOM_EFFECTS.get(mushroom, {})
            # Reverse the light gain when it expires
            total_light_loss += effects.get("light", 0)

        # Update light level
        grotto = None
        for loc in getattr(state, "locations", []):
            if hasattr(loc, "id") and loc.id == "luminous_grotto":
                grotto = loc
                break

        if grotto:
            current = grotto.properties.get("light_level", 2)
            grotto.properties["light_level"] = max(2, current - total_light_loss)
        else:
            current = state.extra.get("grotto_light_level", 2)
            state.extra["grotto_light_level"] = max(2, current - total_light_loss)

    state.extra["glowing_mushrooms"] = glowing
    return EventResult(allow=True, feedback=None)


def _apply_infection(state: Any, player: Any, amount: int) -> None:
    """Apply infection to player from dangerous mushroom."""
    if not player:
        return

    conditions = player.properties.get("conditions", [])
    infection = None
    for cond in conditions:
        if cond.get("type") == "fungal_infection":
            infection = cond
            break

    if not infection:
        infection = {"type": "fungal_infection", "severity": 0}
        conditions.append(infection)
        player.properties["conditions"] = conditions

    infection["severity"] = min(100, infection.get("severity", 0) + amount)
