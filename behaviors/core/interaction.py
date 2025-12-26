"""Interaction behaviors - use, pull, push, climb, read.

Vocabulary for general object interactions.
"""

from typing import Dict, Any, Optional, cast, Union

from src.behavior_manager import EventResult
from src.state_accessor import HandlerResult
from src.state_manager import Item, Actor
from src.types import ActorId
from utilities.utils import find_accessible_item
from utilities.handler_utils import (
    find_action_target,
    find_openable_target,
    _handle_door_or_container_state_change
)
from utilities.entity_serializer import serialize_for_handler_result
from utilities.positioning import try_implicit_positioning


# Vocabulary extension - adds interaction verbs
vocabulary = {
    "verbs": [
        {
            "word": "open",
            "event": "on_open",
            "synonyms": [],
            "object_required": True,
            "llm_context": {
                "traits": ["physical action", "changes state", "requires openable object"],
                "failure_narration": {
                    "not_found": "cannot find the object",
                    "already_open": "already open",
                    "locked": "locked"
                }
            }
        },
        {
            "word": "close",
            "event": "on_close",
            "synonyms": ["shut"],
            "object_required": True,
            "narration_mode": "brief",
            "llm_context": {
                "traits": ["physical action", "changes state", "requires closeable object"],
                "failure_narration": {
                    "not_found": "cannot find the object",
                    "already_closed": "already closed"
                }
            }
        },
        {
            "word": "use",
            "event": "on_use",
            "synonyms": [],
            "object_required": True,
            "llm_context": {
                "traits": ["activates object function", "context-dependent"],
                "failure_narration": {
                    "no_effect": "nothing happens",
                    "cannot_use": "cannot use that"
                }
            }
        },
        {
            "word": "read",
            "event": "on_read",
            "synonyms": [],
            "object_required": True,
            "llm_context": {
                "traits": ["reveals written content", "requires readable object"],
                "failure_narration": {
                    "not_readable": "nothing to read",
                    "too_dark": "too dark to read"
                }
            }
        },
        {
            "word": "pull",
            "event": "on_pull",
            "synonyms": ["yank"],
            "object_required": True,
            "llm_context": {
                "traits": ["applies force toward self", "may trigger mechanisms"],
                "failure_narration": {
                    "stuck": "won't budge",
                    "nothing_happens": "nothing happens"
                }
            }
        },
        {
            "word": "push",
            "event": "on_push",
            "synonyms": ["press"],
            "object_required": True,
            "llm_context": {
                "traits": ["applies force away from self", "may trigger mechanisms"],
                "failure_narration": {
                    "stuck": "won't move",
                    "nothing_happens": "nothing happens"
                }
            }
        }
    ],
    "nouns": [],
    "adjectives": [
        # "open" as adjective (e.g., "open door")
        {"word": "open", "synonyms": []}
    ]
}


def handle_open(accessor, action):
    """
    Handle open command.

    Allows an actor to open a container or door item.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item/door to open (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    item, actor_id, error = find_openable_target(accessor, action, "open")
    if error:
        return error

    # Check if it's a valid openable item
    is_door = hasattr(item, 'is_door') and item.is_door
    is_container = item.container is not None

    if not is_door and not is_container:
        return HandlerResult(
            success=False,
            primary=f"You can't open the {item.name}."
        )

    # Apply implicit positioning
    moved, move_msg = try_implicit_positioning(accessor, actor_id, item)

    # Use unified state change logic
    return _handle_door_or_container_state_change(
        accessor, item, actor_id,
        target_state=True,
        verb="open",
        move_msg=move_msg
    )


def handle_close(accessor, action):
    """
    Handle close command.

    Allows an actor to close a container or door item.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (required)
            - object: Name of item/door to close (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    item, actor_id, error = find_openable_target(accessor, action, "close")
    if error:
        return error

    # Check if it's a valid closeable item
    is_door = hasattr(item, 'is_door') and item.is_door
    is_container = item.container is not None

    if not is_door and not is_container:
        return HandlerResult(
            success=False,
            primary=f"You can't close the {item.name}."
        )

    # Apply implicit positioning
    moved, move_msg = try_implicit_positioning(accessor, actor_id, item)

    # Use unified state change logic
    return _handle_door_or_container_state_change(
        accessor, item, actor_id,
        target_state=False,
        verb="close",
        move_msg=move_msg
    )


def _handle_generic_interaction(accessor, action, required_property: Optional[str] = None, base_message_builder=None) -> HandlerResult:
    """
    Generic interaction handler for use, pull, push, read, and similar verbs.

    Args:
        accessor: StateAccessor instance
        action: Action dict with actor_id, object, adjective, verb
        required_property: Optional property to validate (e.g., "readable")
        base_message_builder: Optional function(item, verb) to build custom message

    Returns:
        HandlerResult with success flag and message
    """
    item, error = find_action_target(accessor, action)
    if error:
        return error

    # Type narrowing: if no error, item must be set
    assert item is not None

    verb = action.get("verb")
    if not verb:
        return HandlerResult(
            success=False,
            primary="INCONSISTENT STATE: verb not provided in action"
        )

    # Convert WordEntry to string if necessary
    from src.word_entry import WordEntry
    verb_str = verb.word if isinstance(verb, WordEntry) else str(verb)

    actor_id = cast(ActorId, action.get("actor_id") or ActorId("player"))

    # Property validation if required
    if required_property and not item.properties.get(required_property, False):
        return HandlerResult(
            success=False,
            primary=f"You can't {verb_str} the {item.name}."
        )

    # Invoke entity behaviors
    result = accessor.update(item, {}, verb=verb_str, actor_id=actor_id)

    # Build base message
    if base_message_builder:
        base_message = base_message_builder(item, verb_str)
    else:
        base_message = f"You {verb_str} the {item.name}."

    data = serialize_for_handler_result(item, accessor, actor_id)
    if result.detail:
        return HandlerResult(success=True, primary=f"{base_message} {result.detail}", data=data)

    return HandlerResult(success=True, primary=base_message, data=data)


def handle_use(accessor, action):
    """
    Handle use command.

    Allows an actor to use an item in a generic way.
    Entity behaviors (on_use) can provide specific functionality.

    If an indirect_object is specified (e.g., "use X on Y"), checks
    the target's item_use_reactions to see if it accepts this item.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of item to use (required)
            - adjective: Optional adjective for disambiguation
            - indirect_object: Optional target to use item on

    Returns:
        HandlerResult with success flag and message
    """
    # Check if there's an indirect object (target)
    target_name = action.get("indirect_object")
    if target_name:
        return _handle_use_on_target(accessor, action)

    # No target - use generic interaction
    return _handle_generic_interaction(accessor, action)


def _handle_use_on_target(accessor, action) -> HandlerResult:
    """Handle 'use X on Y' - check target's item_use_reactions.

    Args:
        accessor: StateAccessor instance
        action: Action dict with object, indirect_object, etc.

    Returns:
        HandlerResult with success flag and message
    """
    from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import load_handler

    # Find the item being used
    item, error = find_action_target(accessor, action)
    if error:
        return error
    assert item is not None

    actor_id = cast(ActorId, action.get("actor_id") or ActorId("player"))
    target_name = action.get("indirect_object")

    # Convert WordEntry to string if necessary
    from src.word_entry import WordEntry
    if isinstance(target_name, WordEntry):
        target_word = target_name.word
    else:
        target_word = str(target_name) if target_name else ""

    # Get adjective for matching multi-word names like "spore mother"
    indirect_adj = action.get("indirect_adjective")
    if isinstance(indirect_adj, WordEntry):
        indirect_adj_word = indirect_adj.word
    else:
        indirect_adj_word = str(indirect_adj) if indirect_adj else ""

    # Build full display name for error messages
    display_name = f"{indirect_adj_word} {target_word}".strip() if indirect_adj_word else target_word

    # Find the target - could be item or actor
    target: Union[Item, Actor, None] = find_accessible_item(accessor, target_name, actor_id, action.get("indirect_adjective"))
    if not target:
        # Try finding as actor
        from utilities.utils import find_actor_by_name
        target = find_actor_by_name(accessor, target_name, actor_id)

    if not target:
        return HandlerResult(
            success=False,
            primary=f"You don't see any {display_name} here."
        )

    # Check if target has item_use_reactions
    if hasattr(target, "properties"):
        item_reactions = target.properties.get("item_use_reactions", {})
        item_id = item.id if hasattr(item, "id") else str(item)
        item_lower = item_id.lower()

        # Check for direct handler
        handler_path = item_reactions.get("handler")
        if handler_path:
            handler = load_handler(handler_path)
            if handler:
                context = {"target": target}
                result = handler(item, accessor, context)
                if result.feedback:
                    return HandlerResult(
                        success=result.allow,
                        primary=result.feedback
                    )

        # Check nested reactions (e.g., healing: {accepted_items: [...], handler: ...})
        for reaction_name, reaction_config in item_reactions.items():
            if reaction_name in ("handler", "_metadata"):
                continue
            if not isinstance(reaction_config, dict):
                continue

            accepted_items = reaction_config.get("accepted_items", [])
            if any(accepted.lower() in item_lower for accepted in accepted_items):
                # Found matching reaction
                handler_path = reaction_config.get("handler")
                if handler_path:
                    handler = load_handler(handler_path)
                    if handler:
                        context = {"target": target}
                        result = handler(item, accessor, context)
                        if result.feedback:
                            return HandlerResult(
                                success=result.allow,
                                primary=result.feedback
                            )

    # No special reaction - generic message
    target_name_str = target.name if hasattr(target, "name") else target_word
    return HandlerResult(
        success=True,
        primary=f"You use the {item.name} on the {target_name_str}. Nothing special happens."
    )


def handle_read(accessor, action):
    """
    Handle read command.

    Allows an actor to read a readable item.

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of item to read (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    def build_read_message(item, verb):
        """Custom message builder that includes text content."""
        text = item.properties.get("text", "")
        if text:
            return f"You {verb} the {item.name}: {text}"
        else:
            return f"You {verb} the {item.name}."

    return _handle_generic_interaction(accessor, action, required_property="readable", base_message_builder=build_read_message)


def handle_pull(accessor, action):
    """
    Handle pull command.

    Allows an actor to pull an object (e.g., lever).

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of item to pull (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    return _handle_generic_interaction(accessor, action)


def handle_push(accessor, action):
    """
    Handle push command.

    Allows an actor to push an object (e.g., button).

    Args:
        accessor: StateAccessor instance
        action: Action dict with keys:
            - actor_id: ID of actor performing action (default: "player")
            - object: Name of item to push (required)
            - adjective: Optional adjective for disambiguation

    Returns:
        HandlerResult with success flag and message
    """
    return _handle_generic_interaction(accessor, action)
