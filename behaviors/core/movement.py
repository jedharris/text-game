"""Movement behaviors - go, walk, move.

Vocabulary for movement between locations.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult


# Vocabulary extension - adds movement verbs
vocabulary = {
    "verbs": [
        {
            "word": "go",
            "synonyms": ["walk", "move"],
            "object_required": True,
            "llm_context": {
                "traits": ["movement between locations", "requires direction"],
                "failure_narration": {
                    "no_exit": "can't go that way",
                    "blocked": "something blocks the path",
                    "door_closed": "the door is closed"
                }
            }
        }
    ],
    "nouns": [],
    "adjectives": [],
    "directions": []
}
