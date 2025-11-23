"""Combat behaviors - attack.

Vocabulary for combat actions.
"""

from typing import Dict, Any

from src.behavior_manager import EventResult


# Vocabulary extension - adds attack verb
vocabulary = {
    "verbs": [
        {
            "word": "attack",
            "synonyms": ["hit", "strike", "fight", "kill"],
            "object_required": True,
            "llm_context": {
                "traits": ["combat action", "potentially destructive", "may have consequences"],
                "atmosphere": "violent, aggressive",
                "failure_narration": {
                    "no_weapon": "need a weapon",
                    "cannot_attack": "cannot attack that"
                }
            }
        }
    ],
    "nouns": [],
    "adjectives": [],
    "directions": []
}
