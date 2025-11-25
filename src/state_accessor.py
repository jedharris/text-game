"""
StateAccessor - Clean API for state queries and mutations with automatic behavior invocation.

This module provides the core abstraction for accessing and modifying game state.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class EventResult:
    """
    Result from an entity behavior event handler.

    Behaviors return this to indicate whether an action should be allowed.
    """
    allow: bool
    message: Optional[str] = None


@dataclass
class UpdateResult:
    """
    Result from a state update operation.

    Returned by StateAccessor.update() to indicate success or failure.
    """
    success: bool
    message: Optional[str] = None


@dataclass
class HandlerResult:
    """
    Result from a command handler.

    Command handlers return this to indicate success/failure and provide
    a message for the user.
    """
    success: bool
    message: str


class StateAccessor:
    """
    Clean API for state queries and mutations.

    Provides generic state operations with automatic behavior invocation.
    All state changes should go through this accessor to ensure behaviors
    are properly invoked.
    """

    def __init__(self, game_state, behavior_manager):
        """
        Initialize StateAccessor.

        Args:
            game_state: The GameState instance to operate on
            behavior_manager: The BehaviorManager instance for invoking behaviors
        """
        self.game_state = game_state
        self.behavior_manager = behavior_manager
