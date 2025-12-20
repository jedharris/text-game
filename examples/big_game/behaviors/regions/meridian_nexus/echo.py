"""Echo Guardian for Meridian Nexus.

Implements Echo's commentary on player choices and
guidance functionality.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_utils import modify_trust

# Vocabulary: wire hooks to events
# Note: Dialog reactions are handled by infrastructure/dialog_reactions.py
# Note: Gossip reactions are handled by infrastructure/gossip_reactions.py
# Echo must have appropriate reaction configurations
vocabulary: Dict[str, Any] = {
    "events": []
}


def on_echo_gossip(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Echo comments on gossip about player actions.

    Echo receives gossip instantly from major events and
    provides feedback on player choices.

    Args:
        entity: Echo
        accessor: StateAccessor instance
        context: Context with gossip content

    Returns:
        EventResult with Echo's commentary
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if "echo" not in (actor_id or "").lower():
        return EventResult(allow=True, feedback=None)

    gossip_content = context.get("content", "").lower()
    state = accessor.state

    # Track Echo's trust changes
    echo = state.actors.get("the_echo") or state.actors.get("echo")
    if not echo:
        return EventResult(allow=True, feedback=None)

    trust_state = echo.properties.get("trust_state", {"current": 0})

    # Respond to different events
    if "spore_mother" in gossip_content and "healed" in gossip_content:
        trust_state["current"] = modify_trust(
            trust_state.get("current", 0), delta=2, ceiling=5
        )
        return EventResult(
            allow=True,
            feedback=(
                "Echo's form brightens. 'You chose healing over violence. "
                "The world is grateful, even if it cannot say so.'"
            ),
        )

    if "spore_mother" in gossip_content and "killed" in gossip_content:
        trust_state["current"] = modify_trust(
            trust_state.get("current", 0), delta=-2, floor=-5
        )
        return EventResult(
            allow=True,
            feedback=(
                "Echo's form dims. 'Violence was the easy path. "
                "The spores will spread now, and the Myconids grieve.'"
            ),
        )

    if "salamander" in gossip_content and ("killed" in gossip_content or "died" in gossip_content):
        trust_state["current"] = modify_trust(
            trust_state.get("current", 0), delta=-1, floor=-5
        )
        return EventResult(
            allow=True,
            feedback=(
                "Echo sighs. 'The fire elementals meant no harm. "
                "Was their death necessary?'"
            ),
        )

    if "sira" in gossip_content and "died" in gossip_content:
        return EventResult(
            allow=True,
            feedback=(
                "Echo's voice is heavy. 'Hunter Sira is gone. "
                "Elara will mourn her deeply.'"
            ),
        )

    if "aldric" in gossip_content and "died" in gossip_content:
        return EventResult(
            allow=True,
            feedback=(
                "'Scholar Aldric's knowledge is lost,' Echo murmurs. "
                "'So much wisdom, gone to the dark.'"
            ),
        )

    if "cubs" in gossip_content and "died" in gossip_content:
        trust_state["current"] = modify_trust(
            trust_state.get("current", 0), delta=-1, floor=-5
        )
        return EventResult(
            allow=True,
            feedback=(
                "Echo's form flickers with sadness. 'The mother bear's cubs... "
                "Promises broken have consequences that echo.'"
            ),
        )

    echo.properties["trust_state"] = trust_state
    return EventResult(allow=True, feedback=None)


def on_echo_dialog(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle player conversations with Echo.

    Echo provides guidance and hints based on player progress.

    Args:
        entity: Echo
        accessor: StateAccessor instance
        context: Context with keyword

    Returns:
        EventResult with Echo's response
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if "echo" not in (actor_id or "").lower():
        return EventResult(allow=True, feedback=None)

    keyword = context.get("keyword", "").lower()
    state = accessor.state
    extra = state.extra

    # Guidance about waystone
    if "waystone" in keyword or "repair" in keyword:
        fragments = extra.get("waystone_fragments", [])
        remaining = 5 - len(fragments)
        if remaining == 0:
            return EventResult(
                allow=True,
                feedback="'The waystone is complete. Your journey here ends... or begins anew.'",
            )
        return EventResult(
            allow=True,
            feedback=(
                f"'{remaining} fragments remain to restore the waystone. "
                "Each region holds one, earned through deeds, not taken by force.'"
            ),
        )

    # Hints about regions
    if "help" in keyword or "hint" in keyword or "advice" in keyword:
        hints = []
        if not extra.get("sira_healed") and not extra.get("sira_died"):
            hints.append("'A hunter bleeds in the Beast Wilds. Time is short.'")
        if not extra.get("aldric_helped") and not extra.get("aldric_died"):
            hints.append("'A scholar fades in the Fungal Depths. Knowledge slips away.'")
        if not extra.get("spore_mother_healed") and not extra.get("spore_mother_dead"):
            hints.append("'The Spore Mother suffers. She can be healed... or ended.'")

        if hints:
            return EventResult(allow=True, feedback=hints[0])

        return EventResult(
            allow=True,
            feedback="'Explore. Learn. Choose wisely. The world responds to your actions.'",
        )

    # Status check
    if "status" in keyword or "progress" in keyword:
        saved = sum(1 for k in ["sira_healed", "aldric_helped", "delvan_rescued",
                                "garrett_rescued", "spore_mother_healed", "cubs_healed"]
                    if extra.get(k))
        lost = sum(1 for k in ["sira_died", "aldric_died", "delvan_died",
                               "garrett_died", "spore_mother_dead", "cubs_died"]
                   if extra.get(k))

        return EventResult(
            allow=True,
            feedback=(
                f"'You have saved {saved} souls. {lost} have been lost. "
                f"The waystone holds {len(extra.get('waystone_fragments', []))} of 5 fragments.'"
            ),
        )

    return EventResult(allow=True, feedback=None)
