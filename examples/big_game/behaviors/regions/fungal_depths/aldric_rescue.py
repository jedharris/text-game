"""Aldric Rescue Mechanics for Fungal Depths.

Implements the commitment to save Scholar Aldric and
his teaching service when stabilized.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_utils import (
    create_commitment,
    get_current_turn,
    modify_trust,
    transition_state,
)

# Vocabulary: wire hooks to events
# Note: Dialog reactions are handled by infrastructure/dialog_reactions.py
# Note: Item use reactions are handled by infrastructure/item_use_reactions.py
# Aldric must have dialog_reactions and item_use_reactions configuration
vocabulary: Dict[str, Any] = {
    "events": []
}

def on_aldric_commitment(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Create Aldric commitment when player promises to help.

    Timer starts on commitment, not on first encounter.
    Called by per-topic handler when player asks about help/promise.

    Args:
        entity: The actor being spoken to (Aldric)
        accessor: StateAccessor instance
        context: Context with keyword, topic_name, dialog_text

    Returns:
        EventResult with commitment creation result
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "npc_aldric":
        return EventResult(allow=True, feedback=None)

    state = accessor.state
    extra = state.extra

    # Check if commitment already exists
    if extra.get("aldric_commitment_created"):
        return EventResult(
            allow=True,
            feedback="'You've already promised to help. Please... hurry.'",
        )

    # Create the commitment (config must exist in game state)
    current_turn = get_current_turn(state)
    create_commitment(
        state=state,
        config_id="commit_aldric_help",
        current_turn=current_turn,
    )

    extra["aldric_commitment_created"] = True
    extra["aldric_commitment_turn"] = current_turn

    # Give hope bonus hint
    aldric = state.actors.get("npc_aldric")
    if aldric:
        # Aldric becomes slightly more hopeful
        trust_state = aldric.properties.get("trust_state", {"current": 0})
        new_trust = modify_trust(
            current=trust_state.get("current", 0),
            delta=1,
            ceiling=5,
        )
        trust_state["current"] = new_trust
        aldric.properties["trust_state"] = trust_state

    return EventResult(
        allow=True,
        feedback=(
            "Aldric's eyes brighten with hope. 'The silvermoss grows in the "
            "Luminous Grotto below. Be careful - the spores are thicker there.' "
            "His hope seems to strengthen him slightly."
        ),
    )


def on_aldric_heal(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle healing Aldric with silvermoss.

    First silvermoss stabilizes, second (or Myconid cure) fully heals.

    Args:
        entity: The item being used
        accessor: StateAccessor instance
        context: Context with target

    Returns:
        EventResult with healing result
    """
    item_id = entity.id if hasattr(entity, "id") else str(entity)
    if "silvermoss" not in item_id.lower():
        return EventResult(allow=True, feedback=None)

    target = context.get("target")
    target_id = target.id if target and hasattr(target, "id") else str(target) if target else ""
    if target_id != "npc_aldric":
        return EventResult(allow=True, feedback=None)

    state = accessor.state
    aldric = state.actors.get("npc_aldric")
    if not aldric:
        return EventResult(allow=True, feedback=None)

    # Get current state
    sm = aldric.properties.get("state_machine", {})
    current_state = sm.get("current", sm.get("initial", "critical"))

    if current_state == "critical":
        # First silvermoss - stabilize
        transition_state(sm, "stabilized")
        state.extra["aldric_stabilized"] = True

        # Reduce infection severity
        conditions = aldric.properties.get("conditions", {})
        infection = conditions.get("fungal_infection", {})
        if infection:
            old_severity = infection.get("severity", 80)
            infection["severity"] = max(0, old_severity - 40)
            infection["progression_rate"] = 0  # Stops progression

        return EventResult(
            allow=True,
            feedback=(
                "Color returns to Aldric's cheeks as the silvermoss takes effect. "
                "He can sit up now, breathing easier. 'Thank you... but I'm not "
                "fully cured. One more dose, or the Myconid's remedy, would heal me completely.'"
            ),
        )

    if current_state == "stabilized":
        # Second silvermoss - fully recover
        transition_state(sm, "recovering")
        state.extra["aldric_helped"] = True
        state.extra["aldric_fully_healed"] = True

        # Clear infection
        conditions = aldric.properties.get("conditions", {})
        if "fungal_infection" in conditions:
            del conditions["fungal_infection"]

        # Increase trust for teaching
        trust_state = aldric.properties.get("trust_state", {"current": 0})
        new_trust = modify_trust(
            current=trust_state.get("current", 0),
            delta=2,
            ceiling=5,
        )
        trust_state["current"] = new_trust
        aldric.properties["trust_state"] = trust_state

        return EventResult(
            allow=True,
            feedback=(
                "Aldric stands straighter, his strength returning. 'I feel... whole again. "
                "You've done more than save my life - you've given me hope.' "
                "He looks at you with gratitude. 'If you wish, I could teach you "
                "what I know of these depths.'"
            ),
        )

    if current_state == "recovering":
        return EventResult(
            allow=True,
            feedback="Aldric is already fully recovered. He doesn't need more silvermoss.",
        )

    return EventResult(allow=True, feedback=None)


def on_aldric_teach(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle Aldric teaching mycology skill.

    Requires: trust >= 2, gift item.
    Note: State checking (stabilized/recovering) is now handled by
    requires_state in the topic config.

    Args:
        entity: The actor being spoken to (Aldric)
        accessor: StateAccessor instance
        context: Context with keyword, topic_name

    Returns:
        EventResult with teaching result
    """
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "npc_aldric":
        return EventResult(allow=True, feedback=None)

    state = accessor.state
    aldric = state.actors.get("npc_aldric")
    if not aldric:
        return EventResult(allow=True, feedback=None)

    # Check state (also enforced by requires_state in topic config,
    # but we check here for robustness when handler is called directly)
    sm = aldric.properties.get("state_machine", {})
    current_state = sm.get("current", sm.get("initial", "critical"))

    if current_state == "critical":
        return EventResult(
            allow=True,
            feedback=(
                "'I wish I could teach you...' Aldric coughs weakly. "
                "'But I can barely breathe, let alone explain the subtleties "
                "of mycology. Help me first.'"
            ),
        )

    # Check trust
    trust_state = aldric.properties.get("trust_state", {"current": 0})
    current_trust = trust_state.get("current", 0)

    if current_trust < 2:
        return EventResult(
            allow=True,
            feedback=(
                "'Teaching mycology is... intimate. I need to trust you more "
                "before I share my life's work. Talk with me, help me understand "
                "who you are.'"
            ),
        )

    # Check if already learned
    player = state.actors.get("player")
    if player and player.properties.get("skills", {}).get("mycology"):
        return EventResult(
            allow=True,
            feedback="'You already know what I can teach. Use it well.'",
        )

    # Check for gift item
    gift = context.get("gift_item")
    if not gift:
        # Check if research notes in context
        gift_id = str(context.get("item", "")).lower()
        if "research_notes" not in gift_id and "rare" not in gift_id:
            return EventResult(
                allow=True,
                feedback=(
                    "'I would gladly teach you, but... tradition demands an exchange. "
                    "Bring me something of scholarly value - research notes, perhaps, "
                    "or a rare herb I haven't catalogued.'"
                ),
            )

    # Grant mycology skill
    if player:
        if "skills" not in player.properties:
            player.properties["skills"] = {}
        player.properties["skills"]["mycology"] = True

    state.extra["learned_mycology"] = True

    return EventResult(
        allow=True,
        feedback=(
            "Aldric spends time teaching you the subtle art of mycology - "
            "how to identify beneficial fungi, understand spore patterns, "
            "and navigate fungal environments safely. 'This knowledge saved "
            "my life many times. May it serve you as well.'"
        ),
    )
