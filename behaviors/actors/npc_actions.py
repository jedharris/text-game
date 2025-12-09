"""NPC action system for actor interaction.

Handles NPC actions that fire after player commands:
- Hostile NPCs attack player if in same location
- Alphas are processed before followers (pack hierarchy)
- All NPCs in all locations are processed

NPC AI properties (in actor.properties["ai"]):
{
    "disposition": str,       # "hostile", "neutral", "friendly"
    "pack_role": str,         # "alpha", "follower", etc.
}

Usage:
    # The turn phase handler is registered automatically via vocabulary
    # Individual NPC behavior can be customized by registering npc_take_action
    # behaviors on specific actors or actor types
"""

from typing import List, Optional

from behaviors.actors.combat import get_attacks, select_attack, execute_attack
from behaviors.actors.packs import sync_follower_disposition


def npc_take_action(entity, accessor, context) -> Optional:
    """
    Default NPC action behavior.

    Hostile NPCs attack the player if:
    - NPC has hostile disposition
    - Player is in same location
    - NPC has attacks defined

    Args:
        entity: The NPC Actor
        accessor: StateAccessor for state queries
        context: Context dict (unused)

    Returns:
        EventResult with attack message, or None if no action taken
    """
    from src.state_accessor import EventResult

    if not entity:
        return None

    ai = entity.properties.get("ai", {})
    disposition = ai.get("disposition", "neutral")

    # Early out: not hostile, nothing to do
    if disposition != "hostile":
        return None

    # Check if player is in same location
    player = accessor.get_actor("player")
    if not player or entity.location != player.location:
        return None

    # Check for attacks
    attacks = get_attacks(entity)
    if not attacks:
        return None

    # Select and execute attack
    attack = select_attack(entity, player, {})
    if attack:
        result = execute_attack(accessor, entity, player, attack)
        return EventResult(allow=True, message=result.message)

    return None


def fire_npc_actions(entity, accessor, context):
    """
    Turn phase handler for NPC actions.

    This is called by the NPC_ACTION hook after each successful command.
    It fires npc_take_action on all NPCs, with alphas processed first.

    For each NPC, this first tries to invoke the npc_take_action behavior
    on the entity (allowing custom behaviors like The Echo's appearance).
    If no entity behavior handles it, falls back to the default hostile attack.

    Args:
        entity: Not used (turn phase has no specific entity)
        accessor: StateAccessor for querying actors
        context: Context dict with hook info

    Returns:
        EventResult with combined messages from all NPC actions
    """
    from src.state_accessor import EventResult

    messages = []

    # Get all actors except player
    all_npcs = []
    for actor_id, actor in accessor.game_state.actors.items():
        if actor_id != "player":
            all_npcs.append(actor)

    # Sort: alphas before followers
    def pack_sort_key(actor):
        role = actor.properties.get("ai", {}).get("pack_role", "")
        return 0 if role == "alpha" else 1

    all_npcs.sort(key=pack_sort_key)

    # Fire action for each NPC
    for npc in all_npcs:
        # Sync follower disposition to alpha before acting
        # (alphas already processed first due to sorting)
        sync_follower_disposition(accessor, npc)

        # First try entity-specific behavior via behavior manager
        # This allows NPCs like The Echo to have custom action behaviors
        result = accessor.behavior_manager.invoke_behavior(
            npc, "npc_take_action", accessor, context
        )

        # If no entity behavior handled it, use default hostile attack logic
        if not result or not result.message:
            result = npc_take_action(npc, accessor, context)

        if result and result.message:
            messages.append(result.message)

    if messages:
        return EventResult(allow=True, message="\n".join(messages))
    return EventResult(allow=True, message=None)


# Vocabulary extension - registers the NPC action event
vocabulary = {
    "events": [
        {
            "event": "on_npc_action",
            "hook": "npc_action",
            "description": "Called each turn to give NPCs a chance to act. "
                          "Alphas are processed before followers."
        },
        {
            "event": "npc_take_action",
            "description": "Called for each individual NPC during their turn. "
                          "Default implementation attacks player if hostile."
        }
    ]
}
