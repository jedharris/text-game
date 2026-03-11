"""Council dialog system for Civilized Remnants.

Three councilors with different philosophies react to topics and each other's
positions via shared flags. No voting system — the "politics" emerges from
flag interactions between independent dialog handlers.

Dilemmas:
- refugees: Accept or reject infected refugees at the gate
- beasts: How to handle beast threats from the wilds
- trade: Whether to trade with dangerous regions

Each councilor sets flags when asked about a dilemma, and checks other
councilors' flags to react to their positions.
"""

from typing import Any, Dict

from src.behavior_manager import EventResult


vocabulary: Dict[str, Any] = {
    "events": []
}


# ============================================================
# Councilor Asha — Idealist ("Ethics over efficiency")
# ============================================================

def on_asha_dialog(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle dialog with Councilor Asha."""
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "councilor_asha":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    keyword = context.get("keyword", "").lower()

    if keyword in ("refugees", "infected", "sick", "gate"):
        return _asha_refugees(state)
    elif keyword in ("beasts", "wolves", "creatures", "wilds", "threat"):
        return _asha_beasts(state)
    elif keyword in ("trade", "commerce", "deal", "exchange"):
        return _asha_trade(state)
    elif keyword in ("hurst", "pragmatist"):
        return _asha_on_hurst(state)
    elif keyword in ("varn", "merchant"):
        return _asha_on_varn(state)
    elif keyword in ("unbrand", "brand", "mark", "redeem", "redemption"):
        return _asha_unbranding(state)
    else:
        return EventResult(
            allow=True,
            feedback=(
                "Asha regards you with measured warmth. 'We must rebuild with "
                "compassion, or what we build won't be worth defending. "
                "Ask me about the refugees, the beasts, or trade — these are "
                "the questions that define us.'"
            ),
        )


def _asha_refugees(state: Any) -> EventResult:
    """Asha's position: accept refugees, help the infected."""
    state.extra["asha_position_refugees"] = "accept"

    # React to Hurst's position if he's already spoken
    hurst_pos = state.extra.get("hurst_position_refugees")
    reaction = ""
    if hurst_pos == "reject":
        reaction = (
            " She frowns. 'Hurst would turn them away to die. That is not "
            "strength — it is cowardice wearing armor.'"
        )

    return EventResult(
        allow=True,
        feedback=(
            "Asha's eyes soften with concern. 'These people are sick, not "
            "dangerous. We have healers. We have walls. What we lack is the "
            "courage to use them for their true purpose — protecting those "
            "who cannot protect themselves.'" + reaction
        ),
    )


def _asha_beasts(state: Any) -> EventResult:
    """Asha's position: coexistence with beasts."""
    state.extra["asha_position_beasts"] = "coexist"
    return EventResult(
        allow=True,
        feedback=(
            "Asha speaks thoughtfully. 'The beasts were here before us. They "
            "hunt because they must, not from malice. If we can find ways to "
            "share these lands... perhaps the killing can stop on both sides.'"
        ),
    )


def _asha_trade(state: Any) -> EventResult:
    """Asha's position: cautious but ethical trade."""
    state.extra["asha_position_trade"] = "ethical"
    return EventResult(
        allow=True,
        feedback=(
            "Asha nods carefully. 'Trade can be a bridge between peoples. But "
            "not at any cost. We must know where our goods come from and who "
            "they serve. Commerce without conscience is just exploitation.'"
        ),
    )


def _asha_on_hurst(state: Any) -> EventResult:
    """Asha's view of Hurst."""
    return EventResult(
        allow=True,
        feedback=(
            "'Hurst means well — he truly does. He lost family to the beasts "
            "and it hardened him. But fear makes poor policy. His walls would "
            "keep out the very people who could help us rebuild.'"
        ),
    )


def _asha_on_varn(state: Any) -> EventResult:
    """Asha's view of Varn."""
    return EventResult(
        allow=True,
        feedback=(
            "'Varn sees the world in transactions. Everything has a price, "
            "everyone has an angle. He's not wrong that we need resources — "
            "but he forgets that some things shouldn't be for sale.'"
        ),
    )


def _asha_unbranding(state: Any) -> EventResult:
    """Asha's un-branding ceremony for redeemed players."""
    player = state.actors.get("player")
    if not player:
        return EventResult(allow=True, feedback=None)

    if not state.extra.get("has_killed_fungi"):
        return EventResult(
            allow=True,
            feedback=(
                "Asha tilts her head. 'You carry no mark that needs lifting. "
                "Your conscience is clear — at least in this regard.'"
            ),
        )

    if state.extra.get("asha_unbranded_player"):
        return EventResult(
            allow=True,
            feedback=(
                "'The ceremony has already been performed. The mark is lifted. "
                "What you do with that second chance is up to you.'"
            ),
        )

    # Perform un-branding
    state.extra["has_killed_fungi"] = False
    state.extra["asha_unbranded_player"] = True

    return EventResult(
        allow=True,
        feedback=(
            "Asha places her hands on your shoulders, her expression grave but "
            "kind. She speaks words in an old tongue, and you feel something "
            "shift — a weight you'd grown used to lifting from your spirit. "
            "'The mark is removed,' she says quietly. 'The fungal network will "
            "no longer sense death upon you. But remember — redemption is not "
            "a single act. It is a choice you make every day.'"
        ),
    )


# ============================================================
# Councilor Hurst — Pragmatist ("Results over methods")
# ============================================================

def on_hurst_dialog(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle dialog with Councilor Hurst."""
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "councilor_hurst":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    keyword = context.get("keyword", "").lower()

    if keyword in ("refugees", "infected", "sick", "gate"):
        return _hurst_refugees(state)
    elif keyword in ("beasts", "wolves", "creatures", "wilds", "threat"):
        return _hurst_beasts(state)
    elif keyword in ("trade", "commerce", "deal", "exchange"):
        return _hurst_trade(state)
    elif keyword in ("asha", "idealist"):
        return _hurst_on_asha(state)
    elif keyword in ("varn", "merchant"):
        return _hurst_on_varn(state)
    else:
        return EventResult(
            allow=True,
            feedback=(
                "Hurst crosses his arms. 'Pretty words don't build walls or "
                "feed mouths. You want to help? Ask me about what actually "
                "matters — the refugees, the beasts, the trade routes.'"
            ),
        )


def _hurst_refugees(state: Any) -> EventResult:
    """Hurst's position: reject infected refugees."""
    state.extra["hurst_position_refugees"] = "reject"

    asha_pos = state.extra.get("asha_position_refugees")
    reaction = ""
    if asha_pos == "accept":
        reaction = (
            " He scowls. 'Asha would open the gates and let infection walk "
            "right in. Compassion is a luxury we cannot afford.'"
        )

    return EventResult(
        allow=True,
        feedback=(
            "Hurst's jaw tightens. 'Every infected person we let in is a risk "
            "to everyone inside these walls. I've buried enough people. The "
            "answer is no — not until we have a reliable cure. It's not "
            "cruelty. It's survival.'" + reaction
        ),
    )


def _hurst_beasts(state: Any) -> EventResult:
    """Hurst's position: eliminate beast threats."""
    state.extra["hurst_position_beasts"] = "eliminate"
    return EventResult(
        allow=True,
        feedback=(
            "Hurst's hand goes to the hilt of his sword. 'I lost my family to "
            "those things. Wolves at the walls, spiders in the passes. You "
            "don't negotiate with predators — you make the area safe. "
            "Permanently.'"
        ),
    )


def _hurst_trade(state: Any) -> EventResult:
    """Hurst's position: controlled, security-first trade."""
    state.extra["hurst_position_trade"] = "controlled"
    return EventResult(
        allow=True,
        feedback=(
            "'Trade means opening routes. Routes mean exposure. Every caravan "
            "path is a path for trouble to walk in on. I'm not against trade "
            "— but every route gets a patrol, and every trader gets searched.'"
        ),
    )


def _hurst_on_asha(state: Any) -> EventResult:
    """Hurst's view of Asha."""
    return EventResult(
        allow=True,
        feedback=(
            "'Asha has a good heart. Too good. She'd shelter every stray and "
            "share our last provisions doing it. When the walls finally "
            "fall — and they will if we're not careful — her compassion won't "
            "stop what comes through.'"
        ),
    )


def _hurst_on_varn(state: Any) -> EventResult:
    """Hurst's view of Varn."""
    return EventResult(
        allow=True,
        feedback=(
            "'Varn is useful. I don't trust him — nobody should — but he keeps "
            "the supplies flowing. Just make sure you count your fingers "
            "after shaking his hand.'"
        ),
    )


# ============================================================
# Councilor Varn — Commerce ("Prosperity through commerce")
# ============================================================

def on_varn_dialog(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle dialog with Councilor Varn."""
    actor_id = entity.id if hasattr(entity, "id") else None
    if actor_id != "councilor_varn":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    keyword = context.get("keyword", "").lower()

    if keyword in ("refugees", "infected", "sick", "gate"):
        return _varn_refugees(state)
    elif keyword in ("beasts", "wolves", "creatures", "wilds", "threat"):
        return _varn_beasts(state)
    elif keyword in ("trade", "commerce", "deal", "exchange"):
        return _varn_trade(state)
    elif keyword in ("asha", "idealist"):
        return _varn_on_asha(state)
    elif keyword in ("hurst", "pragmatist"):
        return _varn_on_hurst(state)
    elif keyword in ("undercity", "underground", "below", "tunnels"):
        return _varn_undercity(state)
    else:
        # Varn checks if other councilors have spoken — offers the "middle path"
        asha_pos = state.extra.get("asha_position_refugees")
        hurst_pos = state.extra.get("hurst_position_refugees")
        if asha_pos and hurst_pos:
            return EventResult(
                allow=True,
                feedback=(
                    "Varn steeples his fingers. 'I see you've spoken to my "
                    "colleagues. Asha wants to save everyone. Hurst wants to "
                    "save no one. As usual, the profitable answer lies somewhere "
                    "in between. Ask me about the refugees — I have a proposal.'"
                ),
            )
        return EventResult(
            allow=True,
            feedback=(
                "Varn looks up from his ledger with a thin smile. 'Everything "
                "has a price, friend. The question is whether you're buying or "
                "selling. Ask about trade, the refugees, or the beasts — "
                "I have opinions on all of them. Informed opinions.'"
            ),
        )


def _varn_refugees(state: Any) -> EventResult:
    """Varn's position: accept refugees who can contribute."""
    state.extra["varn_position_refugees"] = "conditional"

    # React to both positions if available
    asha_pos = state.extra.get("asha_position_refugees")
    hurst_pos = state.extra.get("hurst_position_refugees")
    reaction = ""
    if asha_pos and hurst_pos:
        reaction = (
            " He waves a hand. 'Asha would bankrupt us with charity. Hurst "
            "would turn away useful labor. My way, everyone benefits.'"
        )

    return EventResult(
        allow=True,
        feedback=(
            "Varn speaks in measured, numbered points. 'First: refugees bring "
            "skills. Builders, farmers, scouts. Second: the infected can be "
            "quarantined — separately — until cured. Third: everyone who "
            "enters contributes. No charity. Fair exchange.'" + reaction
        ),
    )


def _varn_beasts(state: Any) -> EventResult:
    """Varn's position: beasts as resources."""
    state.extra["varn_position_beasts"] = "exploit"
    return EventResult(
        allow=True,
        feedback=(
            "Varn's eyes gleam. 'Beasts are resources, not just threats. "
            "Spider silk fetches a premium. Wolf pelts keep people warm. "
            "Even venom has its uses. The trick is managing the harvest "
            "sustainably. Kill them all and you lose a revenue stream.'"
        ),
    )


def _varn_trade(state: Any) -> EventResult:
    """Varn's position: aggressive trade expansion."""
    state.extra["varn_position_trade"] = "expand"
    return EventResult(
        allow=True,
        feedback=(
            "Varn leans forward eagerly. 'Trade is survival. Every route we "
            "open, every contact we make, strengthens our position. The frozen "
            "reaches have minerals. The fungal depths have rare medicines. "
            "Even the sunken district holds salvage worth recovering. We're "
            "sitting on a fortune if we're bold enough to claim it.'"
        ),
    )


def _varn_on_asha(state: Any) -> EventResult:
    """Varn's view of Asha."""
    return EventResult(
        allow=True,
        feedback=(
            "'Asha means well. She'd be a fine leader in a world that didn't "
            "require difficult choices. But we don't live in that world. Her "
            "ideals are admirable — and completely impractical.'"
        ),
    )


def _varn_on_hurst(state: Any) -> EventResult:
    """Varn's view of Hurst."""
    return EventResult(
        allow=True,
        feedback=(
            "'Hurst thinks in terms of walls and swords. Useful, in their way. "
            "But a fortress with no trade routes is just a fancy tomb. He "
            "protects our present at the cost of our future.'"
        ),
    )


def _varn_undercity(state: Any) -> EventResult:
    """Varn's secret undercity connections."""
    state.extra["varn_mentioned_undercity"] = True
    return EventResult(
        allow=True,
        feedback=(
            "Varn's expression becomes carefully neutral. 'The tunnels beneath "
            "the town? Dangerous, of course. Officially, the council has "
            "sealed them.' A pause. 'Unofficially... goods move through "
            "channels that don't appear in any ledger. If you're looking for "
            "something specific, perhaps we could arrange a... private "
            "transaction. Another time.'"
        ),
    )
