"""Gossip Delivery Turn Phase.

Processes gossip queue each turn and delivers arrived gossip to target NPCs.
"""

from typing import Any, Union, cast

from src.behavior_manager import EventResult
from src.infrastructure_types import BroadcastGossipEntry, GossipEntry, NetworkGossipEntry
from src.infrastructure_utils import deliver_due_gossip, get_current_turn
from src.types import HookName

# Vocabulary: wire turn phase hook
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "turn_gossip_delivery",
            "invocation": "turn_phase",
            "description": "Deliver gossip that has arrived this turn",
            "after": [],  # Run early in turn
        }
    ],
    "events": [
        {
            "event": "deliver_gossip_turn_phase",
            "hook": "turn_gossip_delivery",
            "description": "Process and deliver gossip queue",
        },
    ]
}


def deliver_gossip_turn_phase(
    entity: Any,  # None for turn phases
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Deliver arrived gossip to target NPCs.

    Called each turn to process the gossip queue. Delivers gossip that has
    arrived (arrives_turn <= current_turn) and invokes entity_gossip_received
    hook for each target NPC.

    Args:
        entity: None (turn phase has no entity)
        accessor: StateAccessor instance
        context: Turn phase context

    Returns:
        EventResult with delivery messages
    """
    state = accessor.game_state
    current_turn = get_current_turn(state)

    # Get and remove arrived gossip
    delivered = deliver_due_gossip(state, current_turn)

    if not delivered:
        return EventResult(allow=True, feedback=None)

    # Invoke entity_gossip_received hook for each target
    event = accessor.behavior_manager.get_event_for_hook(HookName("entity_gossip_received"))
    if not event:
        # Hook not available - gossip lost
        return EventResult(allow=True, feedback=None)

    messages = []
    for gossip_entry in delivered:
        # Type narrow using isinstance-like check with explicit casts
        entry_dict: dict[str, Any] = gossip_entry  # type: ignore[assignment]
        gossip_union: Union[GossipEntry, BroadcastGossipEntry, NetworkGossipEntry] = gossip_entry

        # Point-to-point gossip (GossipEntry)
        if "target_npcs" in entry_dict:
            point_to_point = cast(GossipEntry, gossip_union)
            for target_id in point_to_point["target_npcs"]:
                target_npc = state.actors.get(target_id)
                if not target_npc:
                    continue

                # Invoke gossip_received hook
                gossip_context = {
                    "content": point_to_point["content"],
                    "source_npc": point_to_point["source_npc"],
                    "gossip_id": point_to_point["id"],
                }
                result = accessor.behavior_manager.invoke_behavior(
                    target_npc, event, accessor, gossip_context
                )
                if result and result.feedback:
                    messages.append(result.feedback)

        # Broadcast gossip (BroadcastGossipEntry)
        elif "target_regions" in entry_dict:
            broadcast = cast(BroadcastGossipEntry, gossip_union)
            target_regions = broadcast["target_regions"]
            regions_list: list[str] = [] if target_regions == "ALL" else target_regions

            for actor in state.actors.values():
                loc = accessor.game_state.get_location(actor.location)
                region = loc.properties.get("region") if loc else None
                if region and (not regions_list or region in regions_list):
                    gossip_context = {
                        "content": broadcast["content"],
                        "source_npc": broadcast["source_npc"],
                        "gossip_id": broadcast["id"],
                    }
                    result = accessor.behavior_manager.invoke_behavior(
                        actor, event, accessor, gossip_context
                    )
                    if result and result.feedback:
                        messages.append(result.feedback)

        # Network gossip (NetworkGossipEntry)
        elif "network_id" in entry_dict:
            # Network delivery not yet implemented
            pass

    if messages:
        return EventResult(allow=True, feedback="\n".join(messages))

    return EventResult(allow=True, feedback=None)
