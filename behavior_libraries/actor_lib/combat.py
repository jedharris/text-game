"""Combat system for actor interaction.

Provides combat mechanics including:
- Multi-attack actors
- Damage calculation with armor and cover
- Attack selection logic
- Condition application via attacks
- Death checking

Attack data structure (in actor.properties["attacks"]):
{
    "name": str,                   # Attack name for display
    "damage": int,                 # Base damage
    "type": str,                   # "melee", "ranged", etc.
    "effect": str,                 # Effect like "knockdown" (optional)
    "applies_condition": {         # Condition to apply (optional)
        "name": str,               # Condition name
        "severity": int,           # Starting severity
        ...                        # Other condition fields
    }
}

Usage:
    from behavior_libraries.actor_lib.combat import (
        get_attacks, select_attack, execute_attack,
        calculate_damage, on_death_check
    )
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from behavior_libraries.actor_lib.conditions import has_condition, apply_condition


@dataclass
class AttackResult:
    """Result of an attack execution."""
    success: bool
    damage: int
    conditions_applied: List[str]
    message: str


def get_attacks(actor) -> List[Dict]:
    """
    Get all attacks available to an actor.

    Args:
        actor: The Actor object

    Returns:
        List of attack dicts, or empty list if none
    """
    if not actor:
        return []
    return actor.properties.get("attacks", [])


def select_attack(attacker, target, context: Dict) -> Optional[Dict]:
    """
    Select an appropriate attack based on situation.

    Selection logic:
    1. If target is healthy (>50% health) and attack has knockdown effect: prefer that
    2. If attack applies condition target doesn't have: prefer that
    3. Otherwise: select highest damage attack

    Args:
        attacker: The attacking Actor
        target: The target Actor
        context: Additional context (unused currently)

    Returns:
        Selected attack dict, or None if no attacks available
    """
    attacks = get_attacks(attacker)
    if not attacks:
        return None

    # Calculate target health percentage
    target_health = target.properties.get("health", 100)
    target_max_health = target.properties.get("max_health", 100)
    target_health_pct = target_health / target_max_health if target_max_health > 0 else 0

    # Prefer control effects when target is healthy
    if target_health_pct > 0.5:
        for attack in attacks:
            if attack.get("effect") == "knockdown":
                return attack

    # Prefer condition attacks if target doesn't have condition
    for attack in attacks:
        applies_condition = attack.get("applies_condition")
        if applies_condition:
            condition_name = applies_condition.get("name")
            if condition_name and not has_condition(target, condition_name):
                return attack

    # Default: highest damage
    return max(attacks, key=lambda a: a.get("damage", 0))


def calculate_damage(attack: Dict, attacker, target, context: Dict) -> int:
    """
    Calculate final damage after armor and cover.

    Calculation:
    1. Start with base damage from attack
    2. Subtract armor from target.properties["armor"]
    3. Apply cover percentage reduction from context["cover_value"]
    4. Ensure damage is at least 0

    Args:
        attack: The attack dict
        attacker: The attacking Actor (unused currently)
        target: The target Actor
        context: Additional context, may include "cover_value"

    Returns:
        Final damage value (integer, >= 0)
    """
    base_damage = attack.get("damage", 0)

    # Apply armor reduction
    armor = target.properties.get("armor", 0)
    damage = max(0, base_damage - armor)

    # Apply cover reduction if target is in cover
    if target.properties.get("posture") == "cover":
        cover_value = context.get("cover_value", 0)
        if cover_value > 0:
            damage = int(damage * (1 - cover_value / 100))

    return max(0, damage)


def execute_attack(accessor, attacker, target, attack: Dict) -> AttackResult:
    """
    Execute an attack against a target.

    Applies damage, conditions, and fires on_damage behavior.

    Args:
        accessor: StateAccessor for state queries and behavior invocation
        attacker: The attacking Actor
        target: The target Actor
        attack: The attack dict to execute

    Returns:
        AttackResult with damage, conditions, and message
    """
    # Build context for damage calculation
    context = {}

    # Check if target is in cover
    if target.properties.get("posture") == "cover":
        cover_obj_id = target.properties.get("focused_on")
        if cover_obj_id and accessor:
            cover_obj = accessor.get_item(cover_obj_id)
            if cover_obj:
                context["cover_value"] = cover_obj.properties.get("cover_value", 0)

    # Calculate damage
    damage = calculate_damage(attack, attacker, target, context)

    # Apply damage
    health = target.properties.get("health", 100)
    target.properties["health"] = health - damage

    attack_name = attack.get("name", "attack")
    messages = [f"{attacker.name} hits {target.name} with {attack_name} for {damage} damage"]
    conditions_applied = []

    # Apply condition if attack has one
    applies_condition_data = attack.get("applies_condition")
    if applies_condition_data:
        condition_name = applies_condition_data.get("name")
        if condition_name:
            # Apply the condition using the condition system
            msg = apply_condition(target, condition_name, applies_condition_data)
            conditions_applied.append(condition_name)
            messages.append(f"{target.name} is affected by {condition_name}")

    # Fire on_damage behavior on target
    if accessor and accessor.behavior_manager:
        damage_context = {
            "damage": damage,
            "attacker_id": attacker.id,
            "attack_type": attack.get("type")
        }
        accessor.behavior_manager.invoke_behavior(
            target, "on_damage", accessor, damage_context
        )

    return AttackResult(
        success=True,
        damage=damage,
        conditions_applied=conditions_applied,
        message="; ".join(messages)
    )


def on_death_check(entity, accessor, context) -> Optional[Any]:
    """
    Check if an actor's health <= 0 and invoke on_death behavior.

    Args:
        entity: The Actor to check
        accessor: StateAccessor for behavior invocation
        context: Context dict (unused)

    Returns:
        EventResult with death message, or None if actor is alive
    """
    from src.state_accessor import EventResult

    health = entity.properties.get("health")
    if health is None:
        return None  # Actor doesn't have health tracking

    if health <= 0:
        # Invoke on_death behavior - author implements death handling
        if accessor and accessor.behavior_manager:
            result = accessor.behavior_manager.invoke_behavior(
                entity, "on_death", accessor, {}
            )
            if result and result.message:
                return result

        return EventResult(allow=True, message=f"{entity.name} has died")

    return None


def on_death_check_all(entity, accessor, context):
    """
    Turn phase handler for death checking all actors.

    This is called by the DEATH_CHECK hook after each successful command.
    It checks all actors for death (health <= 0).

    Args:
        entity: Not used (turn phase has no specific entity)
        accessor: StateAccessor for querying actors
        context: Context dict with hook info

    Returns:
        EventResult with combined death messages
    """
    from src.state_accessor import EventResult

    all_messages = []

    for actor_id, actor in accessor.game_state.actors.items():
        result = on_death_check(actor, accessor, context)
        if result and result.message:
            all_messages.append(result.message)

    if all_messages:
        return EventResult(allow=True, message="\n".join(all_messages))
    return EventResult(allow=True, message=None)


def on_attack(entity, accessor, context) -> Optional[Any]:
    """
    Handle player attack command.

    Called for "attack X" commands. The attacking actor must have attacks
    defined in their properties, and the target must be in the same location.

    Args:
        entity: The attacking Actor (typically player)
        accessor: StateAccessor for state queries
        context: Context dict with:
            - target_id: str - the target actor ID

    Returns:
        EventResult with attack message
    """
    from src.state_accessor import EventResult

    target_id = context.get("target_id")
    if not target_id:
        return EventResult(allow=False, message="Attack what?")

    target = accessor.get_actor(target_id)
    if not target:
        return EventResult(allow=False, message=f"Cannot find target to attack.")

    # Check if target is in same location
    if entity.location != target.location:
        return EventResult(allow=False, message=f"{target.name} is not here.")

    # Get attacker's attacks
    attacks = get_attacks(entity)
    if not attacks:
        return EventResult(allow=False, message="You don't have any attacks.")

    # Select and execute attack
    attack = select_attack(entity, target, {})
    if not attack:
        return EventResult(allow=False, message="No suitable attack available.")

    result = execute_attack(accessor, entity, target, attack)
    return EventResult(allow=result.success, message=result.message)


# Vocabulary extension - registers combat events
vocabulary = {
    "verbs": [
        {
            "word": "attack",
            "event": "on_attack",
            "synonyms": ["hit", "strike", "fight"],
            "object_required": True
        }
    ],
    "events": [
        {
            "event": "on_attack",
            "description": "Called when an actor attacks another"
        },
        {
            "event": "on_damage",
            "description": "Called when an actor takes damage"
        },
        {
            "event": "on_death",
            "description": "Called when an actor's health reaches 0, author implements death handling"
        },
        {
            "event": "on_death_check_all",
            "hook": "death_check",
            "description": "Called each turn to check all actors for death (health <= 0)"
        }
    ]
}
