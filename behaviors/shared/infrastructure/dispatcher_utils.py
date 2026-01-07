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
