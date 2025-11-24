"""
Game State Manager

Provides loading, validation, and serialization for game state JSON files.
"""

from .state_manager import (
    load_game_state,
    game_state_to_dict,
    save_game_state,
    GameState,
    Item,
    Location,
    Door,
    Lock,
    NPC,
    PlayerState,
    Metadata,
    ExitDescriptor,
    ValidationError,
    LoadError,
    ContainerInfo,
)
from .validators import ValidationError, validate_game_state

__all__ = [
    'load_game_state',
    'game_state_to_dict',
    'save_game_state',
    'GameState',
    'Item',
    'Location',
    'Door',
    'Lock',
    'NPC',
    'PlayerState',
    'Metadata',
    'ExitDescriptor',
    'ValidationError',
    'LoadError',
    'validate_game_state',
    'ContainerInfo',
]
