"""Vocabulary generation from game state.

Extracts nouns from game state entities and merges them with
base vocabulary for parser initialization.
"""

from typing import List, Dict, Any

from .state_manager import GameState


def extract_nouns_from_state(state: GameState) -> List[Dict[str, Any]]:
    """
    Extract noun entries from game state entities.

    Collects item names, NPC names, and door-related nouns from the game state
    to be used as nouns in the parser vocabulary.

    Args:
        state: GameState object

    Returns:
        List of noun dicts with 'word' key
    """
    seen_words = set()
    nouns = []

    # Extract item names
    for item in state.items:
        name = item.name
        if name and name not in seen_words:
            nouns.append({"word": name})
            seen_words.add(name)

    # Extract NPC names
    for npc in state.npcs:
        name = npc.name
        if name and name not in seen_words:
            nouns.append({"word": name})
            seen_words.add(name)

    # Add "door" noun if there are any door items in the game
    has_doors = any(item.is_door for item in state.items)
    if has_doors and "door" not in seen_words:
        nouns.append({"word": "door"})
        seen_words.add("door")

    return nouns


def merge_vocabulary(base_vocab: Dict[str, Any], extracted_nouns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge base vocabulary with extracted nouns from game state.

    Args:
        base_vocab: Base vocabulary dict from vocabulary.json
        extracted_nouns: List of noun dicts extracted from game state

    Returns:
        Merged vocabulary dict
    """
    # Copy base vocabulary
    merged = {
        "verbs": list(base_vocab.get("verbs", [])),
        "nouns": list(base_vocab.get("nouns", [])),
        "adjectives": list(base_vocab.get("adjectives", [])),
        "directions": list(base_vocab.get("directions", [])),
        "prepositions": list(base_vocab.get("prepositions", [])),
        "articles": list(base_vocab.get("articles", []))
    }

    # Get existing noun words
    existing_words = {n["word"] for n in merged["nouns"]}

    # Add extracted nouns that aren't already present
    for noun in extracted_nouns:
        if noun["word"] not in existing_words:
            merged["nouns"].append(noun)
            existing_words.add(noun["word"])

    return merged
