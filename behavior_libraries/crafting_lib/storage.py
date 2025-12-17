"""Typed accessors for crafting state stored in GameState.extra."""

from __future__ import annotations

from typing import Dict, Any, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from src.state_accessor import StateAccessor


RecipeCatalog = Dict[str, Dict[str, Any]]
ItemTemplateCatalog = Dict[str, Dict[str, Any]]


def get_recipe_catalog(accessor: "StateAccessor") -> RecipeCatalog:
    """Return (and initialize) the recipe registry."""
    extra = accessor.game_state.extra
    if "recipes" not in extra:
        extra["recipes"] = {}
    return cast(RecipeCatalog, extra["recipes"])


def get_item_templates(accessor: "StateAccessor") -> ItemTemplateCatalog:
    """Return (and initialize) crafting item templates."""
    extra = accessor.game_state.extra
    if "item_templates" not in extra:
        extra["item_templates"] = {}
    return cast(ItemTemplateCatalog, extra["item_templates"])
