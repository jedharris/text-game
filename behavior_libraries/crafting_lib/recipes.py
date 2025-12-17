"""Crafting recipes - recipe matching and execution.

Recipes are stored in GameState.extra['recipes'] as a dict:
{
    "recipe_id": {
        "ingredients": ["item_id1", "item_id2"],
        "creates": "result_item_id",
        "requires_location": "forge",        # Optional
        "requires_skill": "blacksmithing",   # Optional
        "consumes_ingredients": true,        # Default true
        "success_message": "You forge a sword."
    }
}

Item templates for created items are in GameState.extra['item_templates']:
{
    "result_item_id": {
        "name": "Iron Sword",
        "description": "A sturdy iron sword"
    }
}

Usage:
    from behavior_libraries.crafting_lib.recipes import (
        find_recipe, check_requirements, execute_craft
    )
"""
from src.types import ActorId

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from src.state_manager import Item
from behavior_libraries.crafting_lib.storage import (
    get_item_templates,
    get_recipe_catalog,
)

Recipe = Dict[str, Any]


@dataclass
class CraftResult:
    """Result of a crafting operation."""
    success: bool
    message: str
    created_item_id: Optional[str] = None


def find_recipe(accessor, item_ids: List[str]) -> Optional[Recipe]:
    """
    Find a recipe matching the given item IDs.

    Args:
        accessor: StateAccessor instance
        item_ids: List of item IDs to match

    Returns:
        Recipe dict if found, None otherwise
    """
    recipes = get_recipe_catalog(accessor)
    item_set = set(item_ids)

    for recipe_id, recipe in recipes.items():
        ingredients = recipe.get('ingredients', [])
        if set(ingredients) == item_set:
            return recipe

    return None


def check_requirements(accessor, recipe: Recipe) -> Tuple[bool, str]:
    """
    Check if recipe requirements are met.

    Args:
        accessor: StateAccessor instance
        recipe: Recipe dict

    Returns:
        Tuple of (can_craft: bool, message: str)
    """
    player = accessor.get_actor(ActorId('player'))
    if not player:
        return False, "Player is not available."

    # Check location requirement
    requires_location = recipe.get('requires_location')
    if requires_location:
        if player.location != requires_location:
            location = accessor.get_location(requires_location)
            loc_name = location.name if location else requires_location
            return False, f"You need to be at the {loc_name} to craft this."

    # Check skill requirement
    requires_skill = recipe.get('requires_skill')
    if requires_skill:
        skills = player.properties.get('skills', [])
        if requires_skill not in skills:
            return False, f"You need the {requires_skill} skill to craft this."

    return True, ''


def execute_craft(accessor, recipe: Recipe, item_ids: List[str]) -> CraftResult:
    """
    Execute crafting: consume ingredients and create result.

    Args:
        accessor: StateAccessor instance
        recipe: Recipe dict
        item_ids: List of item IDs being used as ingredients

    Returns:
        CraftResult with success/failure and message
    """
    player = accessor.get_actor(ActorId('player'))
    if not player:
        return CraftResult(success=False, message="Player is not available.")
    result_id = recipe.get('creates')
    consumes = recipe.get('consumes_ingredients', True)

    # Consume ingredients if specified
    if consumes:
        for item_id in item_ids:
            if item_id in player.inventory:
                player.inventory.remove(item_id)

    # Create the result item
    if result_id:
        # Check if item already exists in game
        existing_item = accessor.get_item(result_id)
        if not existing_item:
            # Create from template
            templates = get_item_templates(accessor)
            template = templates.get(result_id, {})
            new_item = Item(
                id=result_id,
                name=template.get('name', result_id),
                description=template.get('description', 'A crafted item'),
                location="",  # Will be in inventory
                properties=template.get('properties', {})
            )
            accessor.game_state.items.append(new_item)

        # Add to player inventory
        player.inventory.append(result_id)

    message = recipe.get('success_message', f"You create {result_id}.")

    return CraftResult(
        success=True,
        message=message,
        created_item_id=result_id
    )
