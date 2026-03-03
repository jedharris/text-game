"""Shared utilities for infrastructure dispatchers.

Provides common functionality for the hybrid data-driven/handler pattern.
"""

import importlib
import logging
from typing import Any, Callable

from src.behavior_manager import EventResult

# Cache for loaded handler functions
_handler_cache: dict[str, Callable[..., EventResult]] = {}

logger = logging.getLogger(__name__)


def load_handler(handler_path: str) -> Callable[..., EventResult] | None:
    """Load a handler function from a module:function path.

    Used by infrastructure dispatchers to implement the handler escape hatch.
    Handler paths use the format "module.path:function_name".

    Args:
        handler_path: Path like "behaviors.regions.beast_wilds.bee_queen:on_flower_offer"

    Returns:
        The handler function, or None if loading fails

    Example:
        handler = load_handler("behaviors.regions.fungal_depths.aldric_rescue:on_aldric_dialog")
        if handler:
            return handler(entity, accessor, context)
    """
    if handler_path in _handler_cache:
        return _handler_cache[handler_path]

    try:
        if ":" not in handler_path:
            logger.warning(f"Invalid handler path (missing ':'): {handler_path}")
            return None

        module_path, func_name = handler_path.rsplit(":", 1)
        module = importlib.import_module(module_path)
        handler = getattr(module, func_name)
        _handler_cache[handler_path] = handler
        return handler
    except ValueError as e:
        logger.warning(f"Invalid handler path format {handler_path}: {e}")
        return None
    except ImportError as e:
        logger.warning(f"Failed to import module for handler {handler_path}: {e}")
        return None
    except AttributeError as e:
        logger.warning(f"Handler function not found {handler_path}: {e}")
        return None


def clear_handler_cache() -> None:
    """Clear the handler cache. Useful for testing."""
    _handler_cache.clear()


def dispatch_or_process(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
    config: dict[str, Any],
    config_key: str,
    process_func: Callable[[Any, Any, dict[str, Any], dict[str, Any]], EventResult],
) -> EventResult:
    """Common dispatch pattern: check for handler, else process config.

    Args:
        entity: The entity triggering the event
        accessor: StateAccessor instance
        context: Event context
        config: The reaction configuration dict
        config_key: Key name for logging (e.g., "gift_reactions")
        process_func: Function to call for data-driven processing

    Returns:
        EventResult from handler or process_func
    """
    # Check for handler escape hatch
    handler_path = config.get("handler")
    if handler_path:
        handler = load_handler(handler_path)
        if handler:
            return handler(entity, accessor, context)
        logger.warning(f"Handler {handler_path} failed to load for {config_key}")

    # Fall through to data-driven processing
    return process_func(entity, accessor, context, config)
