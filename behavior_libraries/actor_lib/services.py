"""Services framework for actor interaction.

Handles NPCs offering services in exchange for payment:
- Cure services: Remove conditions
- Teaching services: Grant knowledge
- Healing services: Restore health

Service configuration in NPC properties:
{
    "services": {
        "cure": {
            "accepts": ["gold", "rare_herb"],   # Payment types accepted
            "amount_required": 5,               # Base cost
            "cure_amount": 100                  # How much to cure
        },
        "teach_herbalism": {
            "accepts": ["gold"],
            "amount_required": 10,
            "grants": "herbalism"               # Knowledge to grant
        },
        "heal": {
            "accepts": ["gold"],
            "amount_required": 3,
            "restore_amount": 50                # Health to restore
        }
    }
}

Usage:
    from behavior_libraries.actor_lib.services import (
        get_available_services, get_service_cost,
        can_afford_service, execute_service
    )
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from behavior_libraries.actor_lib.conditions import remove_condition


# Trust level required for 50% discount
TRUST_DISCOUNT_THRESHOLD = 3


@dataclass
class ServiceResult:
    """Result of a service transaction."""
    success: bool
    service_provided: Optional[str]
    message: str


def get_available_services(actor) -> Dict[str, Dict]:
    """
    Get all services an NPC offers.

    Args:
        actor: The NPC Actor

    Returns:
        Dict of service_name -> service_config, or empty dict
    """
    if not actor:
        return {}
    return actor.properties.get("services", {})


def get_service_cost(npc, service_name: str, customer) -> int:
    """
    Get effective cost of a service, accounting for trust discounts.

    Trust >= 3 gives 50% discount.

    Args:
        npc: The NPC offering the service
        service_name: Name of the service
        customer: The customer Actor

    Returns:
        Effective cost (integer)
    """
    services = get_available_services(npc)
    service = services.get(service_name, {})
    base_cost = service.get("amount_required", 0)

    if base_cost == 0:
        return 0

    # Check trust level for discount
    relationships = npc.properties.get("relationships", {})
    customer_rel = relationships.get(customer.id, {})
    trust = customer_rel.get("trust", 0)

    if trust >= TRUST_DISCOUNT_THRESHOLD:
        return base_cost // 2  # 50% discount

    return base_cost


def can_afford_service(
    accessor,
    customer,
    service_name: str,
    npc
) -> Tuple[bool, Optional[str]]:
    """
    Check if customer can afford a service.

    Args:
        accessor: StateAccessor for state queries
        customer: The customer Actor
        service_name: Name of the service
        npc: The NPC offering the service

    Returns:
        Tuple of (can_afford: bool, reason: Optional[str])
    """
    services = get_available_services(npc)
    service = services.get(service_name)

    if not service:
        return False, f"{npc.name} doesn't offer {service_name}"

    accepts = service.get("accepts", [])
    required_amount = get_service_cost(npc, service_name, customer)

    # Check customer's inventory for acceptable payment
    for item_id in customer.inventory:
        item = accessor.get_item(item_id)
        if not item:
            continue

        item_type = item.properties.get("type", item.name)
        if item_type in accepts or item.name in accepts:
            amount = item.properties.get("amount", 1)
            if amount >= required_amount:
                return True, None
            else:
                return False, f"Not enough - {npc.name} requires {required_amount}"

    return False, f"You don't have anything {npc.name} accepts for {service_name}"


def execute_service(
    accessor,
    customer,
    npc,
    service_name: str,
    payment_item
) -> ServiceResult:
    """
    Execute a service transaction.

    Args:
        accessor: StateAccessor for state queries
        customer: The customer Actor
        npc: The NPC providing the service
        service_name: Name of the service
        payment_item: The Item being used as payment

    Returns:
        ServiceResult with outcome details
    """
    services = get_available_services(npc)
    service = services.get(service_name)

    if not service:
        return ServiceResult(
            success=False,
            service_provided=None,
            message=f"{npc.name} doesn't offer {service_name}"
        )

    # Verify payment type
    accepts = service.get("accepts", [])
    item_type = payment_item.properties.get("type", payment_item.name)
    if item_type not in accepts and payment_item.name not in accepts:
        return ServiceResult(
            success=False,
            service_provided=None,
            message=f"{npc.name} doesn't accept that for {service_name}"
        )

    # Verify payment amount
    required = get_service_cost(npc, service_name, customer)
    amount = payment_item.properties.get("amount", 1)
    if amount < required:
        return ServiceResult(
            success=False,
            service_provided=None,
            message=f"Not enough - {npc.name} requires {required}"
        )

    # Execute service effects
    messages = [f"{npc.name} provides {service_name}"]

    # Cure service
    if "cure_amount" in service:
        cure_amount = service["cure_amount"]
        conditions = list(customer.properties.get("conditions", {}).keys())
        for condition_name in conditions:
            remove_condition(customer, condition_name)
        if conditions:
            messages.append("conditions treated")

    # Teaching service
    if "grants" in service:
        knowledge = service["grants"]
        knows = customer.properties.setdefault("knows", [])
        if knowledge not in knows:
            knows.append(knowledge)
        messages.append(f"learned {knowledge}")

    # Healing service
    if "restore_amount" in service:
        restore = service["restore_amount"]
        health = customer.properties.get("health", 100)
        max_health = customer.properties.get("max_health", 100)
        customer.properties["health"] = min(max_health, health + restore)
        messages.append("health restored")

    # Consume payment (remove from inventory)
    if payment_item.id in customer.inventory:
        customer.inventory.remove(payment_item.id)

    # Increment trust relationship (simple inline, Phase 7 will expand)
    relationships = npc.properties.setdefault("relationships", {})
    customer_rel = relationships.setdefault(customer.id, {"trust": 0})
    customer_rel["trust"] = customer_rel.get("trust", 0) + 1

    return ServiceResult(
        success=True,
        service_provided=service_name,
        message="; ".join(messages)
    )


def on_receive_for_service(entity, accessor, context) -> Optional[Any]:
    """
    Check if received item is payment for a service.

    Called when an NPC receives an item. If the item matches payment for
    any of the NPC's services, automatically execute that service.

    Args:
        entity: The NPC receiving the item
        accessor: StateAccessor for state queries
        context: Context dict with:
            - item_id: str - the received item
            - giver_id: str - the actor giving the item

    Returns:
        EventResult with service message, or None if not a service payment
    """
    from src.state_accessor import EventResult

    item_id = context.get("item_id")
    giver_id = context.get("giver_id")

    if not item_id or not giver_id:
        return None

    item = accessor.get_item(item_id)
    giver = accessor.get_actor(giver_id)
    if not item or not giver:
        return None

    services = get_available_services(entity)
    if not services:
        return None

    # Check if item matches any service payment
    item_type = item.properties.get("type", item.name)
    item_amount = item.properties.get("amount", 1)

    for service_name, service_config in services.items():
        accepts = service_config.get("accepts", [])
        if item_type not in accepts and item.name not in accepts:
            continue

        # Found a matching service - check amount
        required = get_service_cost(entity, service_name, giver)
        if item_amount < required:
            return EventResult(
                allow=True,
                message=f"{entity.name} needs {required} for {service_name}, but you only offered {item_amount}."
            )

        # Execute the service
        result = execute_service(accessor, giver, entity, service_name, item)
        return EventResult(allow=result.success, message=result.message)

    # Item not accepted for any service
    return None


# Vocabulary extension - registers service events
vocabulary = {
    "events": [
        {
            "event": "on_service_request",
            "description": "Called when a customer requests a service from an NPC"
        },
        {
            "event": "on_service_complete",
            "description": "Called when a service transaction completes successfully"
        },
        {
            "event": "on_receive_for_service",
            "description": "Called when an NPC receives an item that may be payment for a service. "
                          "Auto-executes matching service if payment is sufficient."
        }
    ]
}
