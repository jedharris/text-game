"""UC6: Injured Merchant - Custom behaviors for escort missions and rewards.

These behaviors demonstrate how game-specific code integrates with library modules.
They are NOT part of the library - they are custom behaviors for the test game.

Custom behaviors needed for UC6:
1. start_escort - NPC starts following player
2. check_escort_arrival - Check if escort reached destination
3. give_reward - Transfer reward item to player

Library modules used:
- treatment.py: apply_treatment, get_treatable_conditions
- conditions.py: has_condition, remove_condition
- services.py: get_available_services
"""

from typing import Any, Optional, List


def start_escort(accessor, npc, player) -> str:
    """
    Start an escort mission - NPC follows player.

    Sets NPC's following property to player's ID.

    Args:
        accessor: StateAccessor for state queries
        npc: The NPC to escort
        player: The player Actor to follow

    Returns:
        Message describing the escort start
    """
    if not npc or not player:
        return "No one to escort."

    escort_dest = npc.properties.get("escort_destination")
    if not escort_dest:
        return f"{npc.name} doesn't need an escort."

    npc.properties["following"] = player.id
    return f"{npc.name} begins following you."


def stop_escort(accessor, npc) -> str:
    """
    Stop an escort mission.

    Clears NPC's following property.

    Args:
        accessor: StateAccessor for state queries
        npc: The NPC to stop escorting

    Returns:
        Message describing the escort stop
    """
    if not npc:
        return "No one to stop escorting."

    npc.properties["following"] = None
    return f"{npc.name} stops following you."


def is_following(npc, actor_id: str) -> bool:
    """
    Check if NPC is following a specific actor.

    Args:
        npc: The NPC to check
        actor_id: ID of the actor to check for

    Returns:
        True if following, False otherwise
    """
    if not npc:
        return False

    return npc.properties.get("following") == actor_id


def check_escort_arrival(accessor, npc) -> bool:
    """
    Check if escort NPC has arrived at destination.

    Args:
        accessor: StateAccessor for state queries
        npc: The NPC being escorted

    Returns:
        True if at destination, False otherwise
    """
    if not npc:
        return False

    escort_dest = npc.properties.get("escort_destination")
    if not escort_dest:
        return False

    return npc.location == escort_dest


def update_escort_location(accessor, npc, new_location: str) -> Optional[str]:
    """
    Update escort NPC location when following player.

    Args:
        accessor: StateAccessor for state queries
        npc: The NPC following
        new_location: The new location to move to

    Returns:
        Message if escort completed, None otherwise
    """
    if not npc:
        return None

    if not npc.properties.get("following"):
        return None

    # Move NPC to new location
    npc.location = new_location

    # Check if arrived at destination
    if check_escort_arrival(accessor, npc):
        stop_escort(accessor, npc)
        return f"{npc.name} has safely arrived at their destination!"

    return None


def give_reward(accessor, npc, player) -> Optional[str]:
    """
    Transfer reward item from NPC to player.

    Looks for items with type="reward" in NPC's inventory
    and transfers them to player.

    Args:
        accessor: StateAccessor for state queries
        npc: The NPC giving reward
        player: The player receiving reward

    Returns:
        Message describing reward, or None if no reward
    """
    if not npc or not player:
        return None

    # Find reward items in NPC inventory
    rewards_given = []
    for item_id in list(npc.inventory):
        item = accessor.get_item(item_id)
        if item and item.properties.get("type") == "reward":
            # Transfer to player
            npc.inventory.remove(item_id)
            player.inventory.append(item_id)
            rewards_given.append(item.name)

    if rewards_given:
        items = ", ".join(rewards_given)
        return f"{npc.name} gratefully gives you: {items}"

    return None


def complete_escort(accessor, npc, player) -> str:
    """
    Complete escort mission and give reward.

    Args:
        accessor: StateAccessor for state queries
        npc: The escorted NPC
        player: The player who escorted

    Returns:
        Message describing completion and reward
    """
    if not check_escort_arrival(accessor, npc):
        return f"{npc.name} hasn't reached their destination yet."

    messages = [f"{npc.name} thanks you profusely for the safe escort!"]

    # Give reward
    reward_msg = give_reward(accessor, npc, player)
    if reward_msg:
        messages.append(reward_msg)

    # Clear escort status
    npc.properties["escort_destination"] = None

    return " ".join(messages)


def on_player_move(entity, accessor, context) -> Optional[Any]:
    """
    Handle player moving - update following NPCs.

    Called when player moves to a new location. Updates location
    of any NPCs following the player.

    Args:
        entity: The player Actor
        accessor: StateAccessor for state queries
        context: Context dict with new_location

    Returns:
        EventResult with escort messages if any
    """
    from src.state_accessor import EventResult

    new_location = context.get("new_location")
    if not new_location:
        return None

    messages = []

    # Check all NPCs for following state
    for actor_id, actor in accessor.game_state.actors.items():
        if actor_id == entity.id:
            continue

        if is_following(actor, entity.id):
            msg = update_escort_location(accessor, actor, new_location)
            if msg:
                messages.append(msg)
                # If arrived, complete escort
                if check_escort_arrival(accessor, actor):
                    reward_msg = complete_escort(accessor, actor, entity)
                    messages.append(reward_msg)

    if messages:
        return EventResult(allow=True, message="\n".join(messages))

    return None


def on_guide_merchant(entity, accessor, context) -> Optional[Any]:
    """
    Handle 'guide' command for starting escort.

    Args:
        entity: The player Actor
        accessor: StateAccessor for state queries
        context: Context dict with target_id

    Returns:
        EventResult with escort start message
    """
    from src.state_accessor import EventResult

    target_id = context.get("target_id")
    if not target_id:
        return EventResult(allow=False, message="Guide who?")

    npc = accessor.get_actor(target_id)
    if not npc:
        return EventResult(allow=False, message="That person isn't here.")

    # Check if NPC needs escort
    if not npc.properties.get("escort_destination"):
        return EventResult(allow=False, message=f"{npc.name} doesn't need an escort.")

    # Check if already following
    if is_following(npc, entity.id):
        return EventResult(allow=False, message=f"{npc.name} is already following you.")

    # Start escort
    msg = start_escort(accessor, npc, entity)
    return EventResult(allow=True, message=msg)


# Vocabulary extension for UC6-specific events
vocabulary = {
    "events": [
        {
            "event": "on_player_move",
            "description": "Handle player moving (UC6 escort update)"
        },
        {
            "event": "on_guide_merchant",
            "description": "Handle guide command for escort (UC6 custom behavior)"
        }
    ]
}
