"""Type definitions for the text adventure game engine.

This module defines NewType aliases for entity IDs to enable type checking
and prevent accidental mixing of different ID types.

Usage:
    from src.types import LocationId, ActorId, ItemId

    def get_actor(actor_id: ActorId) -> Actor:
        ...

    # Type checkers will catch this error:
    location_id: LocationId = "loc_room1"
    get_actor(location_id)  # Error: expected ActorId, got LocationId
"""

from typing import NewType


# Entity ID types
# These are all strings at runtime, but NewType enables static type checking
# to catch bugs where the wrong ID type is passed to a function.

LocationId = NewType('LocationId', str)
"""ID for Location entities (e.g., 'loc_entrance', 'loc_cave')."""

ActorId = NewType('ActorId', str)
"""ID for Actor entities including player (e.g., 'player', 'npc_guard')."""

ItemId = NewType('ItemId', str)
"""ID for Item entities including doors (e.g., 'item_sword', 'door_north')."""

LockId = NewType('LockId', str)
"""ID for Lock entities (e.g., 'lock_chest', 'lock_door')."""

PartId = NewType('PartId', str)
"""ID for Part entities in spatial systems (e.g., 'part_top_shelf')."""

ExitId = NewType('ExitId', str)
"""Synthesized ID for exits (e.g., 'exit:loc_room1:north')."""


# Type alias for any entity ID
EntityId = LocationId | ActorId | ItemId | LockId | PartId | ExitId
"""Union type for any entity ID."""


# Secondary types for behavior system
BehaviorModulePath = NewType('BehaviorModulePath', str)
"""Path to a behavior module (e.g., 'behaviors.core.manipulation')."""

EventName = NewType('EventName', str)
"""Name of a behavior event (e.g., 'on_take', 'on_examine')."""

HookName = NewType('HookName', str)
"""Name of a hook (e.g., 'visibility_check', 'on_save')."""


# Semantic text types for Result fields
# These distinguish different kinds of text used in result types,
# enabling stronger type checking and clearer documentation.

FeedbackText = NewType('FeedbackText', str)
"""Text from entity behaviors describing their response (EventResult.feedback).
Examples: "The door creaks open.", "The sword is stuck to the altar."
"""

DetailText = NewType('DetailText', str)
"""Text describing operation details or errors (UpdateResult.detail).
Examples: "Item moved to inventory.", "Field 'location' not found."
"""

PrimaryText = NewType('PrimaryText', str)
"""Primary narration text from command handlers (HandlerResult.primary).
Examples: "You pick up the sword.", "You can't go that way."
"""

NarrationText = NewType('NarrationText', str)
"""Narrative description of actions (AttackResult.narration, FleeResult.narration).
Examples: "The wolf lunges at you, fangs bared.", "You flee to the north."
"""

DescriptionText = NewType('DescriptionText', str)
"""Description of crafted items or processes (CraftResult.description).
Examples: "You combine the herbs into a healing poultice."
"""

ResponseText = NewType('ResponseText', str)
"""NPC dialog response text (DialogResult.response).
Examples: "The merchant nods. 'I've heard tales of that sword.'"
"""

OutcomeText = NewType('OutcomeText', str)
"""Description of service outcomes (ServiceResult.outcome).
Examples: "The healer tends to your wounds, and you feel refreshed."
"""

EffectText = NewType('EffectText', str)
"""Description of treatment effects (TreatmentResult.effect).
Examples: "The antidote neutralizes the poison in your veins."
"""
