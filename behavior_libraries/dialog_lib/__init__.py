"""Dialog library - conversation and topic mechanics.

Manages the game state consequences of NPC conversations.
The LLM handles narration; this library handles mechanics.
"""

from .topics import (
    get_available_topics,
    get_topic_hints,
    handle_ask_about,
    handle_talk_to,
)
from .handlers import (
    handle_ask,
    handle_talk,
)

__all__ = [
    'get_available_topics',
    'get_topic_hints',
    'handle_ask_about',
    'handle_talk_to',
    'handle_ask',
    'handle_talk',
]
