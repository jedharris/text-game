"""Manipulation behaviors - take and drop.

Vocabulary and handlers for basic item manipulation.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult


# Vocabulary extension - adds take and drop verbs
vocabulary = {
    "verbs": [
        {
            "word": "take",
            "synonyms": ["get", "grab", "pick"],
            "object_required": True,
            "llm_context": {
                "traits": ["physical action", "transfers possession", "requires reachable object"],
                "failure_narration": {
                    "not_found": "cannot find the object",
                    "too_heavy": "too heavy to lift",
                    "fixed": "firmly attached"
                }
            }
        },
        {
            "word": "drop",
            "synonyms": ["put", "place"],
            "object_required": True,
            "llm_context": {
                "traits": ["releases held object", "places in current location"],
                "failure_narration": {
                    "not_holding": "not carrying that"
                }
            }
        }
    ],
    "nouns": [],
    "adjectives": [],
    "directions": []
}
