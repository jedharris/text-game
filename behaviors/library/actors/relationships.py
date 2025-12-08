"""Relationship tracking system for actor interaction.

Tracks progressive relationship values between actors with threshold effects:
- trust: General trust level (discount at 3, loyalty at 5)
- gratitude: Feeling of indebtedness (domestication at 3)
- fear: Intimidation level (intimidation at 5)

Relationship data structure in actor.properties["relationships"]:
{
    "player": {"trust": 5, "gratitude": 2, "fear": 0},
    "npc_merchant": {"trust": 3, "gratitude": 0, "fear": 1}
}

Threshold effects:
- Gratitude >= 3: "domestication" - animal/creature becomes tamed
- Trust >= 3: "discount" - service costs reduced by 50%
- Trust >= 5: "loyalty" - NPC will assist in combat
- Fear >= 5: "intimidation" - NPC will comply with demands

Usage:
    from behaviors.library.actors.relationships import (
        get_relationship, modify_relationship,
        check_threshold, get_disposition_from_relationships
    )
"""

from dataclasses import dataclass
from typing import Dict, Optional


# Relationship value bounds
MIN_RELATIONSHIP = 0
MAX_RELATIONSHIP = 10

# Threshold definitions
THRESHOLDS = {
    "gratitude": [
        (3, "domestication"),
    ],
    "trust": [
        (3, "discount"),
        (5, "loyalty"),
    ],
    "fear": [
        (5, "intimidation"),
    ],
}

# Disposition thresholds
FRIENDLY_TRUST_THRESHOLD = 5
HOSTILE_FEAR_THRESHOLD = 5


@dataclass
class RelationshipResult:
    """Result of a relationship modification."""
    old_value: int
    new_value: int
    threshold_crossed: Optional[str]


def get_relationship(actor, target_id: str) -> Dict[str, int]:
    """
    Get relationship values toward a target.

    Args:
        actor: The Actor whose relationships to query
        target_id: ID of the target actor

    Returns:
        Dict of metric -> value, or empty dict if no relationship
    """
    if not actor:
        return {}

    relationships = actor.properties.get("relationships", {})
    return relationships.get(target_id, {})


def modify_relationship(
    accessor,
    actor,
    target_id: str,
    metric: str,
    delta: int
) -> RelationshipResult:
    """
    Modify a relationship metric and check for threshold crossings.

    Values are clamped to 0-10 range.

    Args:
        accessor: StateAccessor (unused but kept for API consistency)
        actor: The Actor whose relationship to modify
        target_id: ID of the target actor
        metric: The metric to modify ("trust", "gratitude", "fear")
        delta: Amount to change (positive or negative)

    Returns:
        RelationshipResult with old value, new value, and any threshold crossed
    """
    # Ensure relationships dict exists
    relationships = actor.properties.setdefault("relationships", {})

    # Ensure target relationship exists with defaults
    target_rel = relationships.setdefault(target_id, {
        "trust": 0,
        "gratitude": 0,
        "fear": 0
    })

    # Get old value and calculate new
    old_value = target_rel.get(metric, 0)
    new_value = max(MIN_RELATIONSHIP, min(MAX_RELATIONSHIP, old_value + delta))
    target_rel[metric] = new_value

    # Check for threshold crossing
    threshold_crossed = None
    metric_thresholds = THRESHOLDS.get(metric, [])

    for threshold_value, threshold_name in metric_thresholds:
        # Only report crossing if we went from below to at-or-above
        if old_value < threshold_value <= new_value:
            threshold_crossed = threshold_name
            break  # Only report the first threshold crossed

    return RelationshipResult(
        old_value=old_value,
        new_value=new_value,
        threshold_crossed=threshold_crossed
    )


def check_threshold(
    actor,
    target_id: str,
    metric: str,
    threshold: int
) -> bool:
    """
    Check if a relationship metric meets a threshold.

    Args:
        actor: The Actor whose relationship to check
        target_id: ID of the target actor
        metric: The metric to check
        threshold: The threshold value

    Returns:
        True if metric >= threshold, False otherwise
    """
    rel = get_relationship(actor, target_id)
    return rel.get(metric, 0) >= threshold


def get_disposition_from_relationships(actor, target_id: str) -> str:
    """
    Determine disposition toward target based on relationships.

    Disposition rules:
    - Fear >= 5 without high trust -> "hostile" (intimidated into hostility)
    - Trust >= 5 -> "friendly"
    - Otherwise -> "neutral"

    Args:
        actor: The Actor whose disposition to determine
        target_id: ID of the target actor

    Returns:
        Disposition string: "hostile", "friendly", or "neutral"
    """
    rel = get_relationship(actor, target_id)

    if not rel:
        return "neutral"

    trust = rel.get("trust", 0)
    fear = rel.get("fear", 0)

    # High fear without trust leads to hostile behavior
    if fear >= HOSTILE_FEAR_THRESHOLD and trust < FRIENDLY_TRUST_THRESHOLD:
        return "hostile"

    # High trust leads to friendly behavior
    if trust >= FRIENDLY_TRUST_THRESHOLD:
        return "friendly"

    return "neutral"


# Vocabulary extension - registers relationship events
vocabulary = {
    "events": [
        {
            "event": "on_relationship_change",
            "description": "Called when a relationship metric changes"
        },
        {
            "event": "on_threshold_crossed",
            "description": "Called when a relationship threshold is crossed"
        }
    ]
}
