"""Interaction behaviors - use, pull, push, climb, read.

Vocabulary for general object interactions.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult


# Vocabulary extension - adds interaction verbs
vocabulary = {
    "verbs": [
        {
            "word": "use",
            "synonyms": [],
            "object_required": True,
            "llm_context": {
                "traits": ["activates object function", "context-dependent"],
                "failure_narration": {
                    "no_effect": "nothing happens",
                    "cannot_use": "cannot use that"
                }
            }
        },
        {
            "word": "read",
            "synonyms": [],
            "object_required": True,
            "llm_context": {
                "traits": ["reveals written content", "requires readable object"],
                "failure_narration": {
                    "not_readable": "nothing to read",
                    "too_dark": "too dark to read"
                }
            }
        },
        {
            "word": "climb",
            "synonyms": [],
            "object_required": True,
            "llm_context": {
                "traits": ["vertical movement", "requires climbable surface"],
                "failure_narration": {
                    "cannot_climb": "cannot climb that",
                    "too_slippery": "too slippery to climb"
                }
            }
        },
        {
            "word": "pull",
            "synonyms": ["yank"],
            "object_required": True,
            "llm_context": {
                "traits": ["applies force toward self", "may trigger mechanisms"],
                "failure_narration": {
                    "stuck": "won't budge",
                    "nothing_happens": "nothing happens"
                }
            }
        },
        {
            "word": "push",
            "synonyms": ["press"],
            "object_required": True,
            "llm_context": {
                "traits": ["applies force away from self", "may trigger mechanisms"],
                "failure_narration": {
                    "stuck": "won't move",
                    "nothing_happens": "nothing happens"
                }
            }
        }
    ],
    "nouns": [],
    "adjectives": [],
    "directions": []
}
