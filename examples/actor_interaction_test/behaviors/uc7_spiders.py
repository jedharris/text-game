"""UC7: Spider Swarm - Custom behaviors for alert propagation and web mechanics.

These behaviors demonstrate how game-specific code integrates with library modules.
They are NOT part of the library - they are custom behaviors for the test game.

Custom behaviors needed for UC7:
1. alert_propagation - Alert pack when trigger fires
2. web_burning - Reduce web_density when using fire item
3. web_bonus - Apply web_bonus_attacks damage modifier

Library modules used:
- packs.py: get_pack_members, sync_pack_disposition
- combat.py: get_attacks, execute_attack
- conditions.py: apply_condition
"""

from typing import Any, Optional, List


def is_spider_pack_member(actor, pack_id: str = "spider_swarm") -> bool:
    """
    Check if actor is part of spider swarm pack.

    Args:
        actor: The Actor to check
        pack_id: ID of the spider pack

    Returns:
        True if actor is in spider pack
    """
    if not actor:
        return False

    return actor.properties.get("pack_id") == pack_id


def alert_spider(spider) -> str:
    """
    Alert a single spider.

    Args:
        spider: The spider Actor to alert

    Returns:
        Message describing the alert
    """
    if not spider:
        return ""

    spider.properties["alerted"] = True
    return f"{spider.name} becomes alert!"


def alert_swarm(accessor, pack_id: str = "spider_swarm") -> List[str]:
    """
    Alert all spiders in the swarm.

    Args:
        accessor: StateAccessor for state queries
        pack_id: ID of the spider pack

    Returns:
        List of alert messages
    """
    messages = []

    for actor_id, actor in accessor.game_state.actors.items():
        if is_spider_pack_member(actor, pack_id):
            if not actor.properties.get("alerted"):
                msg = alert_spider(actor)
                if msg:
                    messages.append(msg)

    return messages


def is_alerted(spider) -> bool:
    """
    Check if spider is alerted.

    Args:
        spider: The spider Actor

    Returns:
        True if alerted
    """
    if not spider:
        return False

    return spider.properties.get("alerted", False)


def get_web_density(accessor, part_id: str) -> int:
    """
    Get web density for a part.

    Args:
        accessor: StateAccessor for state queries
        part_id: ID of the part

    Returns:
        Web density value (0-100)
    """
    part = accessor.get_part(part_id)
    if not part:
        return 0

    return part.properties.get("web_density", 0)


def reduce_web_density(accessor, part_id: str, amount: int) -> str:
    """
    Reduce web density in a part.

    Args:
        accessor: StateAccessor for state queries
        part_id: ID of the part
        amount: Amount to reduce

    Returns:
        Message describing the change
    """
    part = accessor.get_part(part_id)
    if not part:
        return "No webs here to burn."

    current = part.properties.get("web_density", 0)
    if current <= 0:
        return "The webs here have already been cleared."

    new_density = max(0, current - amount)
    part.properties["web_density"] = new_density

    if new_density == 0:
        return "The webs burn away completely!"
    elif new_density < current // 2:
        return "The webs are mostly cleared!"
    else:
        return "Some of the webs burn away."


def burn_webs_with_torch(accessor, torch, part_id: str) -> str:
    """
    Use torch to burn webs in a part.

    Args:
        accessor: StateAccessor for state queries
        torch: The torch Item
        part_id: ID of the part with webs

    Returns:
        Message describing the result
    """
    if not torch:
        return "You need a fire source to burn webs."

    if not torch.properties.get("burns_webs"):
        return f"The {torch.name} can't burn webs."

    burn_amount = torch.properties.get("web_burn_amount", 20)
    return reduce_web_density(accessor, part_id, burn_amount)


def get_web_attack_bonus(accessor, part_id: str) -> int:
    """
    Get attack bonus from webs in a part.

    Spiders get bonus damage when fighting in their webs.

    Args:
        accessor: StateAccessor for state queries
        part_id: ID of the part

    Returns:
        Bonus damage value
    """
    part = accessor.get_part(part_id)
    if not part:
        return 0

    # Only apply bonus if web density is high enough
    web_density = part.properties.get("web_density", 0)
    if web_density < 50:
        return 0

    return part.properties.get("web_bonus_attacks", 0)


def apply_venom_from_attack(accessor, attacker, target, attack) -> Optional[str]:
    """
    Apply venom condition from spider attack.

    Args:
        accessor: StateAccessor for state queries
        attacker: The attacking spider
        target: The target Actor
        attack: The attack dict

    Returns:
        Message if venom applied, None otherwise
    """
    from behaviors.actor_lib.conditions import apply_condition, has_condition

    applies_condition = attack.get("applies_condition")
    if not applies_condition:
        return None

    condition_name = applies_condition.get("name")
    if not condition_name:
        return None

    # Don't stack venom
    if has_condition(target, condition_name):
        return None

    msg = apply_condition(target, condition_name, applies_condition)
    return f"Venom courses through your veins! {msg}"


def on_enter_spider_territory(entity, accessor, context) -> Optional[Any]:
    """
    Handle entering spider territory - alerts swarm.

    Called when an actor enters spider gallery.

    Args:
        entity: The Actor entering
        accessor: StateAccessor for state queries
        context: Context dict

    Returns:
        EventResult with alert messages
    """
    from src.state_accessor import EventResult

    # Check if entering spider gallery
    new_location = context.get("new_location")
    if new_location != "loc_spider_gallery":
        return None

    # Only alert if not already alerted
    alerts = alert_swarm(accessor)
    if alerts:
        messages = ["The spiders sense your presence!"] + alerts
        return EventResult(allow=True, feedback="\n".join(messages))

    return None


def on_use_torch_on_webs(entity, accessor, context) -> Optional[Any]:
    """
    Handle using torch on webs.

    Args:
        entity: The Actor using torch
        accessor: StateAccessor for state queries
        context: Context with item_id and part_id

    Returns:
        EventResult with burn message
    """
    from src.state_accessor import EventResult

    item_id = context.get("item_id")
    part_id = context.get("part_id")

    if not item_id:
        return None

    item = accessor.get_item(item_id)
    if not item:
        return None

    if not item.properties.get("burns_webs"):
        return None

    # Default to current part if not specified
    if not part_id:
        # Try to find a webbed part in current location
        location = accessor.get_location(entity.location)
        if location:
            part_ids = getattr(location, 'parts', [])
            for pid in part_ids:
                if get_web_density(accessor, pid) > 0:
                    part_id = pid
                    break

    if not part_id:
        return EventResult(allow=True, feedback="No webs to burn here.")

    msg = burn_webs_with_torch(accessor, item, part_id)
    return EventResult(allow=True, feedback=msg)


# Vocabulary extension for UC7-specific events
vocabulary = {
    "events": [
        {
            "event": "on_enter_spider_territory",
            "description": "Handle entering spider territory (UC7 custom behavior)"
        },
        {
            "event": "on_use_torch_on_webs",
            "description": "Handle burning webs with torch (UC7 custom behavior)"
        }
    ]
}
