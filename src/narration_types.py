"""
Narration Types - Type definitions for the Narration-Oriented Engine API.

This module defines the TypedDict structures used to communicate narration plans
from the game engine to the LLM narrator. These types eliminate conditional
reasoning in the narrator by having the engine pre-compute all narration decisions.

See docs/game_engine_narration_api_design.md for full specification.
"""

from typing import TypedDict, Literal, Optional


class ViewpointInfo(TypedDict, total=False):
    """
    Mechanical data about the player's perspective.

    The narrator uses this to frame descriptions appropriately:
    - ground: Normal standing position
    - elevated: Player is above ground level
    - concealed: Player is hidden

    Fields:
        mode: General perspective category
        posture: Specific positioning state (None = normal standing)
        focus_name: Human-readable name of the entity player is positioned at/on/in
    """
    mode: Literal["ground", "elevated", "concealed"]
    posture: Optional[Literal["climbing", "on_surface", "behind_cover"]]
    focus_name: Optional[str]


class ScopeInfo(TypedDict):
    """
    Defines what kind of narration this is using mechanical classifications.

    Fields:
        scene_kind: Determined by verb type
            - location_entry: Movement commands (go, directions)
            - look: Observation commands (look, examine)
            - action_result: All other commands
        outcome: Direct mapping from success field
        familiarity: Based on visit/examination tracking
    """
    scene_kind: Literal["location_entry", "look", "action_result"]
    outcome: Literal["success", "failure"]
    familiarity: Literal["new", "familiar"]


class EntityState(TypedDict, total=False):
    """
    Relevant state flags for an entity.

    Only includes fields that affect narration.
    """
    open: bool
    locked: bool
    lit: bool


class EntityRef(TypedDict, total=False):
    """
    Narration-ready data for a relevant entity in the scene.

    Fields:
        name: Display name for the entity
        type: Entity type category
        traits: Sensory/descriptive phrases from llm_context (randomized, limited)
        spatial_relation: Position relative to player (for elevated/concealed viewpoints)
        state: Relevant state flags
        salience: How prominently to mention in narration
    """
    name: str
    type: Literal["item", "container", "door", "actor", "exit", "location"]
    traits: list[str]
    spatial_relation: Literal["within_reach", "below", "above", "nearby"]
    state: EntityState
    salience: Literal["high", "medium", "low"]


class MustMention(TypedDict, total=False):
    """
    Pre-formatted text that must appear in narration when relevant.

    Fields:
        exits_text: Complete exits description for location scenes
    """
    exits_text: str


class NarrationPlan(TypedDict, total=False):
    """
    The complete narration plan - sole authoritative input for prose rendering.

    Fields:
        primary_text: The core statement of what occurred (from handler's primary field)
        secondary_beats: Supplemental sentences (from handler beats + selected traits)
        viewpoint: Mechanical perspective data
        scope: Scene type classification
        entity_refs: Relevant entities with narration-ready data
        must_mention: Required text that must appear
    """
    primary_text: str
    secondary_beats: list[str]
    viewpoint: ViewpointInfo
    scope: ScopeInfo
    entity_refs: dict[str, EntityRef]
    must_mention: MustMention


class NarrationResult(TypedDict):
    """
    Top-level turn result returned by the protocol handler.

    Fields:
        success: Whether the action succeeded
        verbosity: Brief or full narration mode
        narration: The authoritative narration plan
        data: Raw engine data for debugging/UI (narrator does not rely on this)
    """
    success: bool
    verbosity: Literal["brief", "full"]
    narration: NarrationPlan
    data: dict[str, object]  # Raw engine data for debugging/UI
