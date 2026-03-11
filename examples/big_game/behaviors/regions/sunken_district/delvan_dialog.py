"""Merchant Delvan - Post-Rescue Dialog System.

Delvan reveals contacts, trade services, and undercity access
as the player builds trust through conversation after rescue.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.infrastructure_utils import (
    apply_trust_change,
)

# Vocabulary: wire hooks to events
vocabulary: Dict[str, Any] = {
    "events": []
}

# Dialog topic keywords
TRADE_KEYWORDS = ["trade", "buy", "sell", "goods", "supplies", "inventory", "merchant"]
CONTACTS_KEYWORDS = ["contacts", "network", "connections", "people", "know"]
UNDERCITY_KEYWORDS = [
    "undercity", "underground", "black market", "smuggler", "criminal",
    "entrance", "way in", "access",
]
GRATITUDE_KEYWORDS = ["thank", "grateful", "saved", "rescue"]

# Trust threshold for contacts knowledge fragment
CONTACTS_TRUST_THRESHOLD = 4


def on_delvan_dialog(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle dialog with Delvan based on rescue state and trust.

    Args:
        entity: Delvan NPC
        accessor: StateAccessor instance
        context: Context with keyword

    Returns:
        EventResult with dialog response
    """
    if not hasattr(entity, "id") or entity.id != "merchant_delvan":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    extra = state.extra
    keyword = context.get("keyword", "").lower()

    # Get Delvan's current state
    sm = entity.properties.get("state_machine", {})
    current_state = sm.get("current", sm.get("initial", "trapped"))
    trust_state = entity.properties.get("trust_state", {"current": 0})
    trust = trust_state.get("current", 0)

    # Not rescued yet - limited dialog
    if current_state == "trapped":
        return EventResult(
            allow=True,
            feedback=(
                "Delvan gasps between breaths. 'Talk later - help now! "
                "I'm bleeding out here!'"
            )
        )

    if current_state == "dead":
        return EventResult(allow=True, feedback=None)

    # Post-rescue dialog topics
    if any(kw in keyword for kw in UNDERCITY_KEYWORDS):
        return _handle_undercity_dialog(entity, extra, trust)

    if any(kw in keyword for kw in CONTACTS_KEYWORDS):
        return _handle_contacts_dialog(entity, extra, trust)

    if any(kw in keyword for kw in TRADE_KEYWORDS):
        return _handle_trade_dialog(entity, extra, trust)

    if any(kw in keyword for kw in GRATITUDE_KEYWORDS):
        apply_trust_change(entity=entity, delta=1)
        return EventResult(
            allow=True,
            feedback=(
                "Delvan's calculating demeanor softens. 'I owe you my life. "
                "That's not something a merchant forgets. When you need "
                "something - and you will - come to me first.'"
            )
        )

    # Default response based on state
    if current_state == "freed":
        return EventResult(
            allow=True,
            feedback=(
                "Delvan shivers, still recovering from the ordeal. 'Give me "
                "a moment. Once I've caught my breath, we can talk properly. "
                "A merchant always has something to offer.'"
            )
        )

    # Mobile state - general conversation
    return EventResult(
        allow=True,
        feedback=(
            "Delvan adjusts his sodden collar with practiced dignity. "
            "'I'm a man who knows things and knows people. Ask me about "
            "trade, contacts, or... less official channels.'"
        )
    )


def _handle_trade_dialog(
    entity: Any, extra: dict[str, Any], trust: int
) -> EventResult:
    """Delvan offers trading services post-rescue."""
    extra["delvan_trade_offered"] = True

    if trust >= 2:
        return EventResult(
            allow=True,
            feedback=(
                "Delvan's eyes light up with professional interest. "
                "'Ah, trade! Now you're speaking my language. I may have "
                "lost my warehouse, but not my connections. I can get you "
                "supplies, rare goods, things you won't find lying around. "
                "Bring me items of value and we'll deal.'"
            )
        )

    return EventResult(
        allow=True,
        feedback=(
            "Delvan nods cautiously. 'I deal in goods and information. "
            "Once I've recovered properly, I can offer you supplies. "
            "Help me out a bit more and I'll make it worth your while.'"
        )
    )


def _handle_contacts_dialog(
    entity: Any, extra: dict[str, Any], trust: int
) -> EventResult:
    """Delvan reveals his contact network at high trust."""
    if trust < CONTACTS_TRUST_THRESHOLD:
        return EventResult(
            allow=True,
            feedback=(
                "Delvan's expression becomes guarded. 'I know people, yes. "
                "But that kind of information... it's valuable. And dangerous. "
                "I need to know I can trust you completely before I share names.'"
            )
        )

    # High trust - reveal contacts
    if "knowledge_fragments" not in extra:
        extra["knowledge_fragments"] = {}
    extra["knowledge_fragments"]["delvan_contacts"] = True
    extra["knows_delvan_contacts"] = True

    return EventResult(
        allow=True,
        feedback=(
            "Delvan leans close, voice dropping to a whisper. 'You've earned this. "
            "I know people throughout this place - traders, fixers, people who "
            "move things that aren't supposed to move. There's a network down "
            "below, in the undercity. I can introduce you, vouch for you. "
            "That's worth more than gold down here.'"
        )
    )


def _handle_undercity_dialog(
    entity: Any, extra: dict[str, Any], trust: int
) -> EventResult:
    """Delvan reveals undercity entrance as alternative to Vex."""
    if trust < 2:
        return EventResult(
            allow=True,
            feedback=(
                "Delvan's face goes carefully blank. 'The undercity? "
                "I don't know what you're talking about.' His eyes "
                "betray him - he knows exactly what you mean."
            )
        )

    extra["knows_undercity_entrance"] = True

    return EventResult(
        allow=True,
        feedback=(
            "Delvan glances around before speaking. 'There's an entrance "
            "to the undercity - not the one Vex controls. A merchant's "
            "passage, used for moving goods without... oversight. "
            "Through the old drainage tunnels, past the flooded plaza. "
            "I'll mark it for you. Consider it repayment for my life.'"
        )
    )
