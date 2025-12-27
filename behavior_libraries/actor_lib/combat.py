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
from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import load_handler
from src.state_accessor import IGNORE_EVENT


@dataclass
class AttackResult:
    """Result of an attack execution.

    Fields:
        narration: Description of the attack for narration.
                   Semantic type: NarrationText
    """
    success: bool
    damage: int
    conditions_applied: List[str]
    narration: str


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

    # Fire on_damage handler - this applies the damage via the hybrid dispatcher
    # Call directly instead of through behavior_manager (it's an infrastructure handler)
    damage_context = {
        "damage": damage,
        "attacker_id": attacker.id,
        "attack_type": attack.get("type")
    }
    damage_result = on_damage(target, accessor, damage_context)
    # Append on_damage feedback to narration
    if damage_result.feedback:
        messages.append(damage_result.feedback)

    return AttackResult(
        success=True,
        damage=damage,
        conditions_applied=conditions_applied,
        narration="; ".join(messages)
    )


def on_damage(entity, accessor, context):
    """
    Handle damage event with hybrid dispatcher pattern.

    Default implementation:
    - Ignores entities without health property
    - Applies damage = context["damage"] - entity armor
    - Updates health (but doesn't handle death)
    - Returns IGNORE_EVENT (no message)

    Escape hatch:
    - If entity.properties["damage_handler"] is set, delegate to that handler
    - Handler format: "module.path:function_name"
    - Custom handler receives (entity, accessor, context) and returns EventResult

    Args:
        entity: The entity taking damage
        accessor: StateAccessor for state queries
        context: Context dict with:
            - damage: int - raw damage before armor
            - attacker_id: str - ID of attacker (optional)
            - attack_type: str - type of attack (optional)

    Returns:
        EventResult with optional feedback message
    """
    from src.state_accessor import EventResult

    # Check for handler escape hatch
    damage_handler_path = entity.properties.get("damage_handler")
    if damage_handler_path:
        handler = load_handler(damage_handler_path)
        if handler:
            return handler(entity, accessor, context)

    # Auto-ignore entities without health
    if "health" not in entity.properties:
        return IGNORE_EVENT

    # Default damage processing
    raw_damage = context.get("damage", 0)
    armor = entity.properties.get("armor", 0)
    final_damage = max(0, raw_damage - armor)

    # Apply damage
    current_health = entity.properties.get("health", 0)
    entity.properties["health"] = current_health - final_damage

    # Validate health didn't go negative beyond threshold
    if entity.properties["health"] < -100:
        entity.properties["health"] = -100

    # Return IGNORE_EVENT - no message by default
    return IGNORE_EVENT


def on_death(entity, accessor, context):
    """
    Handle death event with hybrid dispatcher pattern.

    Default implementation:
    - Removes actor from game state
    - Drops all inventory items at death location
    - Returns generic death message

    Escape hatch:
    - If entity.properties["death_handler"] is set, delegate to that handler
    - Handler format: "module.path:function_name"
    - Custom handler receives (entity, accessor, context) and returns EventResult

    Args:
        entity: The dying entity
        accessor: StateAccessor for state mutations
        context: Context dict (currently unused)

    Returns:
        EventResult with death message
    """
    from src.state_accessor import EventResult

    # Check for handler escape hatch
    death_handler_path = entity.properties.get("death_handler")
    if death_handler_path:
        handler = load_handler(death_handler_path)
        if handler:
            return handler(entity, accessor, context)

    # Default death processing
    death_location = entity.location

    # Drop all inventory items
    if hasattr(entity, 'inventory') and entity.inventory:
        for item_id in list(entity.inventory):
            item = accessor.get_item(item_id)
            if item:
                item.location = death_location
        entity.inventory.clear()

    # Remove actor from game
    if entity.id in accessor.game_state.actors:
        del accessor.game_state.actors[entity.id]

    return EventResult(
        allow=True,
        feedback=f"{entity.name} has been slain!"
    )


def on_death_check(entity, accessor, context) -> Optional[Any]:
    """
    Check if an actor's health <= 0 and invoke on_death behavior.

    Args:
        entity: The Actor to check
        accessor: StateAccessor for behavior invocation
        context: Context dict (unused)

    Returns:
        EventResult with death message, or IGNORE_EVENT if actor is alive
    """
    from src.state_accessor import EventResult

    health = entity.properties.get("health")
    if health is None:
        return IGNORE_EVENT  # Actor doesn't have health tracking

    if health <= 0:
        # Call on_death handler directly (it's an infrastructure handler)
        result = on_death(entity, accessor, {})
        return result

    return IGNORE_EVENT


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

    # Iterate over list copy to avoid RuntimeError if actor dies and is removed
    for actor_id, actor in list(accessor.game_state.actors.items()):
        result = on_death_check(actor, accessor, context)
        if result and result.feedback:
            all_messages.append(result.feedback)

    if all_messages:
        return EventResult(allow=True, feedback="\n".join(all_messages))
    return EventResult(allow=True, feedback=None)


def on_attack(entity, accessor, context) -> Optional[Any]:
    """
    Handle player attack command with hybrid dispatcher pattern.

    Default implementation:
    - Validates target exists and is in same location
    - Selects and executes appropriate attack from attacker's attacks
    - Returns attack result narration

    Escape hatch:
    - If entity.properties["attack_handler"] is set, delegate to that handler
    - Handler format: "module.path:function_name"
    - Custom handler receives (entity, accessor, context) and returns EventResult

    Args:
        entity: The attacking Actor (typically player)
        accessor: StateAccessor for state queries
        context: Context dict with:
            - target_id: str - the target actor ID

    Returns:
        EventResult with attack message
    """
    from src.state_accessor import EventResult

    # Check for handler escape hatch
    attack_handler_path = entity.properties.get("attack_handler")
    if attack_handler_path:
        handler = load_handler(attack_handler_path)
        if handler:
            return handler(entity, accessor, context)

    # Default attack processing
    target_id = context.get("target_id")
    if not target_id:
        return EventResult(allow=False, feedback="Attack what?")

    target = accessor.get_actor(target_id)
    if not target:
        return EventResult(allow=False, feedback=f"Cannot find target to attack.")

    # Check if target is in same location
    if entity.location != target.location:
        return EventResult(allow=False, feedback=f"{target.name} is not here.")

    # Get attacker's attacks
    attacks = get_attacks(entity)
    if not attacks:
        return EventResult(allow=False, feedback="You don't have any attacks.")

    # Select and execute attack
    attack = select_attack(entity, target, {})
    if not attack:
        return EventResult(allow=False, feedback="No suitable attack available.")

    result = execute_attack(accessor, entity, target, attack)
    return EventResult(allow=result.success, feedback=result.narration)


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
