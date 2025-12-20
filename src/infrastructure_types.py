"""
Infrastructure Type Definitions

This module defines semantic types for the game infrastructure systems.
These types are separate from core engine types in src/types.py.

See: docs/big_game_work/detailed_designs/infrastructure_detailed_design.md Part 1
"""

from enum import Enum
from typing import Literal, NewType, TypedDict

from typing_extensions import NotRequired


# StrEnum backport for Python 3.10 (native StrEnum added in 3.11)
class StrEnum(str, Enum):
    """String enumeration compatible with Python 3.10+."""

    def __str__(self) -> str:
        return self.value

from src.types import ActorId, LocationId

# =============================================================================
# 1.1 ID Types
# =============================================================================

TurnNumber = NewType("TurnNumber", int)
"""Turn count value. Used consistently for deadlines, durations, timestamps."""

CommitmentId = NewType("CommitmentId", str)
"""Unique identifier for a commitment (e.g., 'commit_save_garrett')."""

GossipId = NewType("GossipId", str)
"""Unique identifier for a gossip entry (e.g., 'gossip_player_abandoned_sira')."""

ScheduledEventId = NewType("ScheduledEventId", str)
"""Unique identifier for a scheduled event (e.g., 'event_cold_spread_75')."""


# =============================================================================
# 1.2 Enumerated Types
# =============================================================================


class TemperatureZone(StrEnum):
    """Temperature classification for locations."""

    NORMAL = "normal"
    COLD = "cold"
    FREEZING = "freezing"
    EXTREME_COLD = "extreme_cold"


class WaterLevel(StrEnum):
    """Water depth classification for locations."""

    DRY = "dry"
    ANKLE = "ankle"
    WAIST = "waist"
    CHEST = "chest"
    SUBMERGED = "submerged"


class ConditionType(StrEnum):
    """Types of conditions that can affect actors."""

    HYPOTHERMIA = "hypothermia"
    DROWNING = "drowning"
    BLEEDING = "bleeding"
    INFECTION = "infection"
    EXHAUSTION = "exhaustion"
    POISON = "poison"


class CommitmentState(StrEnum):
    """State of a commitment."""

    ACTIVE = "active"
    FULFILLED = "fulfilled"
    WITHDRAWN = "withdrawn"
    ABANDONED = "abandoned"


class CompanionComfort(StrEnum):
    """How comfortable a companion is in a region/location."""

    COMFORTABLE = "comfortable"
    UNCOMFORTABLE = "uncomfortable"
    IMPOSSIBLE = "impossible"


class GossipType(StrEnum):
    """Type of gossip propagation."""

    POINT_TO_POINT = "point_to_point"  # Specific source to specific targets
    BROADCAST = "broadcast"  # Source to all NPCs in target regions
    NETWORK = "network"  # Source to all members of a network


# =============================================================================
# 1.3 Typed Dictionaries - Core
# =============================================================================


class StateMachineConfig(TypedDict):
    """Configuration for an NPC state machine."""

    states: list[str]
    initial: str
    current: NotRequired[str]  # Runtime state, defaults to initial


class ConditionInstance(TypedDict):
    """An active condition on an actor."""

    type: ConditionType
    severity: int  # 0-100 typically
    source: NotRequired[str]  # What caused it (location, item, etc.)
    progression_rate: NotRequired[int]  # Severity change per turn (game-specific)
    paused: NotRequired[bool]  # Whether progression is paused


class TrustState(TypedDict):
    """Trust tracking for an NPC or the Echo."""

    current: int
    floor: NotRequired[int]  # Minimum from negative actions
    ceiling: NotRequired[int]  # Maximum trust value
    recovery_cap: NotRequired[int]  # Max recoverable per visit
    recovered_this_visit: NotRequired[int]  # Amount recovered in current visit
    last_recovery_turn: NotRequired[TurnNumber]  # Turn of last recovery action


class ScheduledEvent(TypedDict):
    """An event scheduled to fire at a specific turn."""

    id: ScheduledEventId
    trigger_turn: TurnNumber
    event_type: str  # Handler looks this up
    data: NotRequired[dict[str, str]]  # Event-specific parameters
    repeating: NotRequired[bool]  # If True, event reschedules after firing
    interval: NotRequired[int]  # For repeating events, turns between fires


# =============================================================================
# 1.3 Typed Dictionaries - Commitment System
# =============================================================================


class CommitmentConfig(TypedDict):
    """A commitment declaration in game state."""

    id: CommitmentId
    target_npc: ActorId
    goal: str
    trigger_phrases: list[str]
    hope_extends_survival: bool
    hope_bonus: NotRequired[int]  # Turns added to NPC survival
    base_timer: NotRequired[int]  # Turns until commitment failure if timed
    fulfillment_flag: NotRequired[str]  # Flag that must be set to fulfill


class ActiveCommitment(TypedDict):
    """Runtime state of an active commitment."""

    id: CommitmentId
    config_id: str  # Reference to CommitmentConfig
    state: CommitmentState
    made_at_turn: TurnNumber
    deadline_turn: NotRequired[TurnNumber]  # If timed
    hope_applied: bool


# =============================================================================
# 1.3 Typed Dictionaries - Gossip System
# =============================================================================


class GossipEntry(TypedDict):
    """A piece of gossip in the propagation queue (point-to-point)."""

    id: GossipId
    content: str  # What happened
    source_npc: ActorId
    target_npcs: list[ActorId]  # Who will eventually know
    created_turn: TurnNumber
    arrives_turn: TurnNumber  # When it reaches targets
    confession_window_until: NotRequired[TurnNumber]  # Turn when confession no longer helps


class BroadcastGossipEntry(TypedDict):
    """Gossip that broadcasts to all NPCs in target regions.

    Note: For property-based targeting (e.g., "all fungal creatures"),
    use NetworkGossipEntry instead. Broadcast gossip delivers to ALL
    NPCs in the target regions without filtering.
    """

    id: GossipId
    type: Literal["broadcast"]
    content: str
    source_npc: ActorId
    target_regions: list[str] | Literal["ALL"]  # Region IDs or "ALL"
    created_turn: TurnNumber
    arrives_turn: TurnNumber


class NetworkGossipEntry(TypedDict):
    """Gossip that broadcasts to all members of a network."""

    id: GossipId
    type: Literal["network"]
    content: str
    source_npc: ActorId
    network_id: str  # "spore_network", "criminal_network", etc.
    created_turn: TurnNumber
    arrives_turn: TurnNumber


class NetworkDefinition(TypedDict):
    """Definition of a gossip network based on actor properties."""

    property_name: str  # Actor property to check (e.g., "fungal")
    property_value: bool | str | int  # Required value (e.g., True)


# =============================================================================
# 1.4 Companion Types
# =============================================================================


class CompanionRestriction(TypedDict):
    """Where a companion can/cannot go."""

    location_patterns: list[str]  # Glob patterns like "sunken_district/*"
    comfort: CompanionComfort
    reason: NotRequired[str]  # For narration


class CompanionState(TypedDict):
    """Runtime state of a companion."""

    actor_id: ActorId
    following: bool
    waiting_at: NotRequired[LocationId]
    comfort_in_current: CompanionComfort


# =============================================================================
# 1.6 Environmental Spread Types
# =============================================================================


class SpreadEffect(TypedDict):
    """An effect applied at a spread milestone."""

    locations: list[str]  # Glob patterns like "beast_wilds/*"
    property_name: str  # Location property to modify
    property_value: str | int | bool  # New value


class SpreadMilestone(TypedDict):
    """A milestone in an environmental spread."""

    turn: TurnNumber
    effects: list[SpreadEffect]


class SpreadState(TypedDict):
    """State of an environmental spread."""

    active: bool
    halt_flag: str  # Global flag that halts this spread when True
    milestones: list[SpreadMilestone]
    current_milestone: NotRequired[TurnNumber]  # Last milestone reached
