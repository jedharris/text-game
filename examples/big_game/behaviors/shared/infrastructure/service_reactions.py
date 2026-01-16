"""Service Reaction Infrastructure.

Handles NPC service requests (teaching, training, etc.).

Supports handler escape hatch:
    "services": {
        "teach_swimming": {
            "handler": "behaviors.regions.sunken_district.jek_teaching:on_jek_teach",
            "cost": 5,
            "cost_type": "gold_or_food",
            "description": "Learn basic swimming"
        }
    }
"""

from typing import Any

from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import load_handler
from src.behavior_manager import EventResult

# Vocabulary: wire hooks to events
vocabulary = {
    "hook_definitions": [
        {
            "hook_id": "entity_service",
            "invocation": "entity",
            "description": "Called when player requests service from entity"
        }
    ],
    "events": [
        {
            "event": "on_service",
            "hook": "entity_service",
            "description": "Handle service requests",
        },
    ]
}


def on_service(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle service requests for NPCs.

    Checks the entity for services configuration.
    If config has "handler" key, calls that Python function.

    Args:
        entity: The NPC providing service
        accessor: StateAccessor instance
        context: Context with service_type, requester

    Returns:
        EventResult with service response
    """
    if not hasattr(entity, "properties"):
        return EventResult(allow=True, feedback=None)

    # Check for services configuration
    services_config = entity.properties.get("services", {})
    if not services_config:
        return EventResult(allow=True, feedback=None)

    service_type = context.get("service_type", "")

    # Find a service that matches the type
    for service_name, service_config in services_config.items():
        if not isinstance(service_config, dict):
            continue

        # Check handler escape hatch
        handler_path = service_config.get("handler")
        if handler_path:
            handler = load_handler(handler_path)
            if handler:
                return handler(entity, accessor, context)

    # No handler found
    return EventResult(allow=True, feedback=None)
