"""Reaction type specifications for unified interpreter.

Each ReactionSpec parametrizes the interpreter for a specific reaction type,
defining how to match triggers, enrich context, and select messages.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple


@dataclass
class ReactionSpec:
    """Parametrizes interpreter for a reaction type.

    Attributes:
        reaction_type: Type identifier (gift, dialog, etc.)
        message_key: Primary message field name
        fallback_message_key: Secondary message field name
        match_strategy: Strategy for finding applicable reaction config
        context_enrichment: Function to add reaction-specific context vars
    """
    reaction_type: str
    message_key: str
    fallback_message_key: str
    match_strategy: Any  # MatchStrategy instance
    context_enrichment: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]


from .match_strategies import (
    ItemMatchStrategy,
    KeywordMatchStrategy,
    NoMatchStrategy,
    ProgressiveMatchStrategy,
    StateChangeMatchStrategy,
)


# Context enrichment functions for each reaction type
def _gift_context(ctx: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich context for gift reactions."""
    item = ctx.get("item")
    target = ctx.get("target_actor") or ctx.get("target")
    return {
        **ctx,
        "item": item.id if item and hasattr(item, "id") else str(item) if item else "",
        "target": target.id if target and hasattr(target, "id") else str(target) if target else "",
    }


def _dialog_context(ctx: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich context for dialog reactions."""
    entity = ctx.get("entity") or ctx.get("target")
    return {
        **ctx,
        "keyword": ctx.get("keyword", ""),
        "state": entity.properties.get("state_machine", {}).get("current", "") if entity and hasattr(entity, "properties") else "",
    }


def _item_use_context(ctx: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich context for item_use reactions."""
    item = ctx.get("item") or ctx.get("entity")
    target = ctx.get("target")
    # IMPORTANT: Keep item and target objects, add IDs separately
    result = {**ctx}
    if item and hasattr(item, "id"):
        result["item_id"] = item.id
    if target and hasattr(target, "id"):
        result["target_id"] = target.id
    return result


def _encounter_context(ctx: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich context for encounter reactions."""
    location = ctx.get("location")
    return {
        **ctx,
        "actor": ctx.get("actor_id", "player"),
        "location": location.id if location and hasattr(location, "id") else "",
    }


def _death_context(ctx: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich context for death reactions."""
    entity = ctx.get("entity")
    return {
        **ctx,
        "entity": entity.id if entity and hasattr(entity, "id") else "",
        "killer": ctx.get("killer", "unknown"),
    }


def _combat_context(ctx: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich context for combat reactions."""
    return {
        **ctx,
        "damage": ctx.get("damage", 0),
        "attacker": ctx.get("attacker", "unknown"),
        "weapon": ctx.get("weapon", "fists"),
    }


def _entry_context(ctx: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich context for entry reactions."""
    return {
        **ctx,
        "from_direction": ctx.get("from_direction", "unknown"),
        "actor": ctx.get("actor_id", "player"),
    }


def _turn_env_context(ctx: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich context for turn_environmental reactions."""
    location = ctx.get("location")
    return {
        **ctx,
        "turn": ctx.get("turn", 0),
        "location": location.id if location and hasattr(location, "id") else "",
    }


def _commitment_context(ctx: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich context for commitment reactions."""
    return {
        **ctx,
        "commitment_id": ctx.get("commitment_id", ""),
        "state_change": ctx.get("state_change", ""),
    }


def _take_context(ctx: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich context for take reactions."""
    item = ctx.get("item")
    location = ctx.get("location")
    return {
        **ctx,
        "item": item.id if item and hasattr(item, "id") else "",
        "location": location.id if location and hasattr(location, "id") else "",
    }


def _examine_context(ctx: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich context for examine reactions."""
    entity = ctx.get("entity")
    return {
        **ctx,
        "entity": entity.id if entity and hasattr(entity, "id") else "",
        "examine_count": ctx.get("examine_count", 0),
    }


def _trade_context(ctx: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich context for trade reactions."""
    vendor = ctx.get("vendor")
    return {
        **ctx,
        "item": ctx.get("item", ""),
        "vendor": vendor.id if vendor and hasattr(vendor, "id") else "",
        "transaction_type": ctx.get("transaction_type", "buy"),
    }


# All 12 reaction type specifications
GIFT_SPEC = ReactionSpec(
    reaction_type="gift",
    message_key="accept_message",
    fallback_message_key="message",
    match_strategy=ItemMatchStrategy("accepted_items"),
    context_enrichment=_gift_context,
)

DIALOG_SPEC = ReactionSpec(
    reaction_type="dialog",
    message_key="summary",
    fallback_message_key="response",
    match_strategy=KeywordMatchStrategy("keywords"),
    context_enrichment=_dialog_context,
)

ITEM_USE_SPEC = ReactionSpec(
    reaction_type="item_use",
    message_key="response",
    fallback_message_key="message",
    match_strategy=ItemMatchStrategy("accepted_items"),
    context_enrichment=_item_use_context,
)

ENCOUNTER_SPEC = ReactionSpec(
    reaction_type="encounter",
    message_key="encounter_message",
    fallback_message_key="message",
    match_strategy=NoMatchStrategy(),
    context_enrichment=_encounter_context,
)

DEATH_SPEC = ReactionSpec(
    reaction_type="death",
    message_key="death_message",
    fallback_message_key="message",
    match_strategy=NoMatchStrategy(),
    context_enrichment=_death_context,
)

COMBAT_SPEC = ReactionSpec(
    reaction_type="combat",
    message_key="message",
    fallback_message_key="response",
    match_strategy=NoMatchStrategy(),
    context_enrichment=_combat_context,
)

ENTRY_SPEC = ReactionSpec(
    reaction_type="entry",
    message_key="message",
    fallback_message_key="entry_message",
    match_strategy=NoMatchStrategy(),
    context_enrichment=_entry_context,
)

TURN_ENV_SPEC = ReactionSpec(
    reaction_type="turn_environmental",
    message_key="message",
    fallback_message_key="tick_message",
    match_strategy=NoMatchStrategy(),
    context_enrichment=_turn_env_context,
)

COMMITMENT_SPEC = ReactionSpec(
    reaction_type="commitment",
    message_key="message",
    fallback_message_key="consequence_message",
    match_strategy=StateChangeMatchStrategy("state_change"),
    context_enrichment=_commitment_context,
)

TAKE_SPEC = ReactionSpec(
    reaction_type="take",
    message_key="message",
    fallback_message_key="response",
    match_strategy=NoMatchStrategy(),
    context_enrichment=_take_context,
)

EXAMINE_SPEC = ReactionSpec(
    reaction_type="examine",
    message_key="message",
    fallback_message_key="reveal_message",
    match_strategy=ProgressiveMatchStrategy("examine_count"),
    context_enrichment=_examine_context,
)

TRADE_SPEC = ReactionSpec(
    reaction_type="trade",
    message_key="message",
    fallback_message_key="response",
    match_strategy=ItemMatchStrategy("item"),
    context_enrichment=_trade_context,
)

# Registry of all specs
REACTION_SPECS: Dict[str, ReactionSpec] = {
    "gift_reactions": GIFT_SPEC,
    "dialog_reactions": DIALOG_SPEC,
    "item_use_reactions": ITEM_USE_SPEC,
    "encounter_reactions": ENCOUNTER_SPEC,
    "death_reactions": DEATH_SPEC,
    "combat_reactions": COMBAT_SPEC,
    "entry_reactions": ENTRY_SPEC,
    "turn_environmental": TURN_ENV_SPEC,
    "commitment_reactions": COMMITMENT_SPEC,
    "take_reactions": TAKE_SPEC,
    "examine_reactions": EXAMINE_SPEC,
    "trade_reactions": TRADE_SPEC,
}
