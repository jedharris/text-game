"""Actor behaviors - vocabulary for self-reference.

Provides vocabulary for examining actors (self and NPCs).
"""

# Vocabulary extension - adds self-reference noun
vocabulary = {
    "verbs": [],
    "nouns": [
        {
            "word": "self",
            "synonyms": ["me", "myself"],
            "llm_context": {
                "traits": ["self-reference", "the acting character"]
            }
        }
    ],
    "adjectives": [],
    "directions": []
}
