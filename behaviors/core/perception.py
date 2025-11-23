"""Perception behaviors - examine/look.

Vocabulary and handlers for examining objects and surroundings.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult


# Vocabulary extension - adds examine verb
vocabulary = {
    "verbs": [
        {
            "word": "examine",
            "synonyms": ["look", "inspect", "x"],
            "object_required": "optional",
            "llm_context": {
                "traits": ["reveals details", "non-destructive", "provides information"],
                "without_object": "describes current surroundings",
                "state_variants": {
                    "detailed": "close inspection reveals hidden details",
                    "quick": "brief glance"
                }
            }
        }
    ],
    "nouns": [],
    "adjectives": [],
    "directions": []
}
