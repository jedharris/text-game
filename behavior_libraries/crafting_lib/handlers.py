"""Crafting command handlers.

Handles 'combine' and 'craft' commands for crafting items.

Commands:
    combine <item1> with <item2>   - Combine two items
    craft <recipe_name>            - Craft by recipe name

Usage:
    from behavior_libraries.crafting_lib.handlers import (
        handle_combine, handle_craft
    )
"""

from typing import Dict, Optional

from src.action_types import ActionDict
from src.state_accessor import HandlerResult
from src.word_entry import WordEntry
from src.types import ActorId
from utilities.utils import name_matches
from utilities.handler_utils import get_display_name
from .recipes import (
    find_recipe, check_requirements, execute_craft
)
from .storage import get_recipe_catalog


# Vocabulary extension
vocabulary = {
    "verbs": [
        {
            "word": "combine",
            "synonyms": ["mix", "merge"],
            "object_required": True,
            "preposition": "with"
        },
        {
            "word": "craft",
            "synonyms": ["create", "make", "build", "assemble"],
            "object_required": True
        }
    ],
    "handlers": {
        "combine": "handle_combine",
        "craft": "handle_craft"
    }
}


def handle_combine(accessor, action: Dict) -> HandlerResult:
    """
    Handle 'combine X with Y' command.

    Args:
        accessor: StateAccessor instance
        action: Action dict with verb, object, target, actor_id

    Returns:
        HandlerResult with success and message
    """
    actor_id = ActorId(action.get('actor_id', ActorId("player")))
    item1_name = action.get('object')
    item2_name = action.get('indirect_object') or action.get('target')

    if not isinstance(item1_name, WordEntry):
        return HandlerResult(success=False, primary="Combine what?")

    if not isinstance(item2_name, WordEntry):
        return HandlerResult(
            success=False,
            primary=f"Combine {get_display_name(item1_name)} with what?"
        )

    player = accessor.get_actor(actor_id)
    if not player:
        return HandlerResult(success=False, primary="No player found.")

    # Find items in inventory by name/id
    item1_id = _find_item_in_inventory(accessor, player, item1_name)
    item2_id = _find_item_in_inventory(accessor, player, item2_name)

    if not item1_id:
        return HandlerResult(success=False, primary=f"You don't have any {get_display_name(item1_name)}.")

    if not item2_id:
        return HandlerResult(success=False, primary=f"You don't have any {get_display_name(item2_name)}.")

    # Find matching recipe
    recipe = find_recipe(accessor, [item1_id, item2_id])

    if not recipe:
        return HandlerResult(
            success=False,
            primary=f"You can't combine {get_display_name(item1_name)} and {get_display_name(item2_name)}."
        )

    # Check requirements
    can_craft, req_message = check_requirements(accessor, recipe)
    if not can_craft:
        return HandlerResult(success=False, primary=req_message)

    # Execute the craft
    result = execute_craft(accessor, recipe, [item1_id, item2_id])

    return HandlerResult(success=result.success, primary=result.description)


def handle_craft(accessor, action: Dict) -> HandlerResult:
    """
    Handle 'craft X' command (by recipe name).

    Args:
        accessor: StateAccessor instance
        action: Action dict with verb, object, actor_id

    Returns:
        HandlerResult with success and message
    """
    actor_id = ActorId(action.get('actor_id', ActorId("player")))
    recipe_name = action.get('object')

    if not isinstance(recipe_name, WordEntry):
        return HandlerResult(success=False, primary="Craft what?")

    player = accessor.get_actor(actor_id)
    if not player:
        return HandlerResult(success=False, primary="No player found.")

    # Find recipe by name - use the word string for lookup
    recipe_name_str = recipe_name.word
    recipes = get_recipe_catalog(accessor)
    recipe = recipes.get(recipe_name_str)

    if not recipe:
        return HandlerResult(
            success=False,
            primary=f"You don't know how to craft {get_display_name(recipe_name)}."
        )

    # Check if player has all ingredients
    ingredients = recipe.get('ingredients', [])
    missing = []
    for item_id in ingredients:
        if item_id not in player.inventory:
            item = accessor.get_item(item_id)
            name = item.name if item else item_id
            missing.append(name)

    if missing:
        return HandlerResult(
            success=False,
            primary=f"You need: {', '.join(missing)}"
        )

    # Check requirements
    can_craft, req_message = check_requirements(accessor, recipe)
    if not can_craft:
        return HandlerResult(success=False, primary=req_message)

    # Execute the craft
    result = execute_craft(accessor, recipe, ingredients)

    return HandlerResult(success=result.success, primary=result.description)


def _find_item_in_inventory(accessor, actor, name: WordEntry) -> Optional[str]:
    """
    Find an item in actor's inventory by name or ID.

    Args:
        accessor: StateAccessor instance
        actor: Actor object
        name: WordEntry for item to find

    Returns:
        Item ID if found, None otherwise
    """
    name_str = name.word

    # First try exact ID match
    if name_str in actor.inventory:
        return name_str

    # Then try name match using name_matches
    for item_id in actor.inventory:
        item = accessor.get_item(item_id)
        if item and name_matches(name, item.name):
            return item_id

    return None
