"""Lock behaviors - unlock and lock.

Vocabulary for lock-related actions.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult


# Vocabulary extension - adds unlock and lock verbs
vocabulary = {
    "verbs": [
        {
            "word": "unlock",
            "synonyms": [],
            "object_required": True,
            "llm_context": {
                "traits": ["requires correct key", "changes locked state"],
                "failure_narration": {
                    "no_key": "need the right key",
                    "wrong_key": "key doesn't fit",
                    "not_locked": "not locked"
                }
            }
        },
        {
            "word": "lock",
            "synonyms": [],
            "object_required": True,
            "llm_context": {
                "traits": ["secures object", "requires correct key"],
                "failure_narration": {
                    "no_key": "need the right key",
                    "already_locked": "already locked",
                    "must_close_first": "must close it first"
                }
            }
        }
    ],
    "nouns": [],
    "adjectives": [],
    "directions": []
}
