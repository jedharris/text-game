"""UC2: Guardian Golems - Custom behaviors for combat with cover and resistances.

These behaviors demonstrate how game-specific code integrates with library modules.
They are NOT part of the library - they are custom behaviors for the test game.

Custom behaviors needed for UC2:
1. take_cover - Move to cover position using cover object
2. leave_cover - Exit cover position
3. apply_weapon_damage - Calculate damage with weapon bonuses
4. golem_counterattack - Golem responds to being attacked

Library modules used:
- combat.py: get_attacks, select_attack, execute_attack, calculate_damage
"""

from typing import Optional, Dict, List


def take_cover(accessor, actor, cover_item) -> str:
    """
    Have actor take cover behind an object.

    Sets actor's posture to 'cover' and records the cover object.
    Cover reduces incoming damage based on cover_value property.

    Args:
        accessor: StateAccessor for state queries
        actor: The Actor taking cover
        cover_item: The Item providing cover

    Returns:
        Message describing the action
    """
    if not actor or not cover_item:
        return "Cannot take cover."

    cover_value = cover_item.properties.get("cover_value", 0)
    if cover_value <= 0:
        return f"The {cover_item.name} doesn't provide cover."

    # Set posture to cover
    actor.properties["posture"] = "cover"
    actor.properties["focused_on"] = cover_item.id

    return f"{actor.name} takes cover behind the {cover_item.name}."


def leave_cover(accessor, actor) -> str:
    """
    Have actor leave cover position.

    Clears cover posture and focused_on object.

    Args:
        accessor: StateAccessor for state queries
        actor: The Actor leaving cover

    Returns:
        Message describing the action
    """
    if not actor:
        return "No one to leave cover."

    posture = actor.properties.get("posture")
    if posture != "cover":
        return f"{actor.name} is not in cover."

    actor.properties["posture"] = None
    actor.properties["focused_on"] = None

    return f"{actor.name} leaves cover."


def get_cover_item(accessor, actor):
    """
    Get the item actor is using for cover.

    Args:
        accessor: StateAccessor for state queries
        actor: The Actor in cover

    Returns:
        Item used for cover, or None
    """
    if not actor:
        return None

    if actor.properties.get("posture") != "cover":
        return None

    cover_item_id = actor.properties.get("focused_on")
    if not cover_item_id:
        return None

    return accessor.get_item(cover_item_id)


def calculate_weapon_damage(accessor, attacker, weapon_item) -> int:
    """
    Calculate damage from weapon item.

    Args:
        accessor: StateAccessor for state queries
        attacker: The attacking Actor
        weapon_item: The weapon Item

    Returns:
        Weapon damage value
    """
    if not weapon_item:
        return 0

    return weapon_item.properties.get("damage", 0)


def apply_damage_resistance(damage: int, target, damage_type: str = "physical") -> int:
    """
    Apply target's resistances to incoming damage.

    Args:
        damage: Base damage
        target: The target Actor
        damage_type: Type of damage (physical, fire, lightning, etc.)

    Returns:
        Damage after resistance applied
    """
    if not target:
        return damage

    resistances = target.properties.get("resistances", {})
    resistance_pct = resistances.get(damage_type, 0)

    if resistance_pct > 0:
        damage = int(damage * (1 - resistance_pct / 100))

    return max(0, damage)


def apply_damage_weakness(damage: int, target, damage_type: str) -> int:
    """
    Apply target's weaknesses to incoming damage.

    Args:
        damage: Base damage
        target: The target Actor
        damage_type: Type of damage

    Returns:
        Damage after weakness multiplier
    """
    if not target:
        return damage

    weaknesses = target.properties.get("weaknesses", {})
    weakness_pct = weaknesses.get(damage_type, 0)

    if weakness_pct > 0:
        damage = int(damage * (1 + weakness_pct / 100))

    return damage


def golem_select_attack(golem, target) -> Optional[Dict]:
    """
    Select an attack for a golem based on situation.

    Selection logic:
    1. If multiple targets (area attack available): use area attack
    2. Otherwise: use highest damage attack

    Args:
        golem: The attacking golem Actor
        target: The primary target Actor

    Returns:
        Selected attack dict, or None
    """
    from behaviors.actors.combat import get_attacks

    attacks = get_attacks(golem)
    if not attacks:
        return None

    # Check for area attack (ground_slam type)
    area_attacks = [a for a in attacks if a.get("area")]
    if area_attacks:
        return area_attacks[0]

    # Default to highest damage
    return max(attacks, key=lambda a: a.get("damage", 0))


def golem_counterattack(accessor, golem, attacker) -> Optional[str]:
    """
    Golem automatically counterattacks when damaged.

    Called from on_damage handler when golem takes damage.

    Args:
        accessor: StateAccessor for state queries
        golem: The golem that was attacked
        attacker: The attacker that damaged the golem

    Returns:
        Message describing counterattack, or None
    """
    from behaviors.actors.combat import execute_attack

    # Only counterattack if not dead
    if golem.properties.get("health", 0) <= 0:
        return None

    # Select attack
    attack = golem_select_attack(golem, attacker)
    if not attack:
        return None

    # Execute counterattack
    result = execute_attack(accessor, golem, attacker, attack)
    return f"The golem counterattacks! {result.message}"


def on_golem_damaged(entity, accessor, context) -> Optional:
    """
    Handle golem being damaged - triggers counterattack.

    Args:
        entity: The golem that was damaged
        accessor: StateAccessor for state queries
        context: Context with damage info

    Returns:
        EventResult with counterattack message
    """
    from src.state_accessor import EventResult

    # Check if this is a construct
    body = entity.properties.get("body", {})
    if body.get("form") != "construct":
        return None

    attacker_id = context.get("attacker_id")
    if not attacker_id:
        return None

    attacker = accessor.get_actor(attacker_id)
    if not attacker:
        return None

    # Only counterattack hostile constructs
    if entity.properties.get("disposition") != "hostile":
        return None

    message = golem_counterattack(accessor, entity, attacker)
    if message:
        return EventResult(allow=True, message=message)

    return None


def check_golem_defeated(golem) -> bool:
    """
    Check if golem is defeated (health <= 0).

    Args:
        golem: The golem Actor

    Returns:
        True if defeated, False otherwise
    """
    if not golem:
        return False

    return golem.properties.get("health", 0) <= 0


def get_all_golems_in_location(accessor, location_id: str) -> List:
    """
    Get all golem actors in a location.

    Args:
        accessor: StateAccessor for state queries
        location_id: ID of the location

    Returns:
        List of golem Actors
    """
    golems = []
    for actor_id, actor in accessor.game_state.actors.items():
        if actor.location == location_id:
            body = actor.properties.get("body", {})
            if body.get("form") == "construct":
                golems.append(actor)
    return golems


# Vocabulary extension for UC2-specific events
vocabulary = {
    "events": [
        {
            "event": "on_golem_damaged",
            "description": "Handle golem taking damage (UC2 custom behavior)"
        }
    ]
}
