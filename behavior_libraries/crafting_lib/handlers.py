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

from typing import Dict

from src.state_accessor import HandlerResult
from behavior_libraries.crafting_lib.recipes import (
    find_recipe, check_requirements, execute_craft
)


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
    actor_id = action.get('actor_id', 'player')
    item1_name = action.get('object')
    item2_name = action.get('target')

    if not item1_name:
        return HandlerResult(success=False, message="Combine what?")

    if not item2_name:
        return HandlerResult(success=False, message=f"Combine {item1_name} with what?")

    player = accessor.get_actor(actor_id)
    if not player:
        return HandlerResult(success=False, message="No player found.")

    # Find items in inventory by name/id
    item1_id = _find_item_in_inventory(accessor, player, item1_name)
    item2_id = _find_item_in_inventory(accessor, player, item2_name)

    if not item1_id:
        return HandlerResult(success=False, message=f"You don't have any {item1_name}.")

    if not item2_id:
        return HandlerResult(success=False, message=f"You don't have any {item2_name}.")

    # Find matching recipe
    recipe = find_recipe(accessor, [item1_id, item2_id])

    if not recipe:
        return HandlerResult(
            success=False,
            message=f"You can't combine {item1_name} and {item2_name}."
        )

    # Check requirements
    can_craft, req_message = check_requirements(accessor, recipe)
    if not can_craft:
        return HandlerResult(success=False, message=req_message)

    # Execute the craft
    result = execute_craft(accessor, recipe, [item1_id, item2_id])

    return HandlerResult(success=result.success, message=result.message)


def handle_craft(accessor, action: Dict) -> HandlerResult:
    """
    Handle 'craft X' command (by recipe name).

    Args:
        accessor: StateAccessor instance
        action: Action dict with verb, object, actor_id

    Returns:
        HandlerResult with success and message
    """
    actor_id = action.get('actor_id', 'player')
    recipe_name = action.get('object')

    if not recipe_name:
        return HandlerResult(success=False, message="Craft what?")

    player = accessor.get_actor(actor_id)
    if not player:
        return HandlerResult(success=False, message="No player found.")

    # Find recipe by name
    recipes = accessor.game_state.extra.get('recipes', {})
    recipe = recipes.get(recipe_name)

    if not recipe:
        return HandlerResult(
            success=False,
            message=f"You don't know how to craft {recipe_name}."
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
            message=f"You need: {', '.join(missing)}"
        )

    # Check requirements
    can_craft, req_message = check_requirements(accessor, recipe)
    if not can_craft:
        return HandlerResult(success=False, message=req_message)

    # Execute the craft
    result = execute_craft(accessor, recipe, ingredients)

    return HandlerResult(success=result.success, message=result.message)


def _find_item_in_inventory(accessor, actor, name: str) -> str:
    """
    Find an item in actor's inventory by name or ID.

    Returns item ID if found, None otherwise.
    """
    # First try exact ID match
    if name in actor.inventory:
        return name

    # Then try name match
    for item_id in actor.inventory:
        item = accessor.get_item(item_id)
        if item and item.name.lower() == name.lower():
            return item_id

    return None
