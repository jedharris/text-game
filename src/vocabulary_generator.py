"""Vocabulary generation from game state.

Extracts nouns from game state entities and merges them with
base vocabulary for parser initialization.
"""

from typing import List, Dict, Any, Optional

from .state_manager import GameState


# Type alias for merged vocabulary structure
# Structure: {
#   "verbs": List[Dict[str, Any]],      # Each verb: {word, synonyms, object_required, value}
#   "nouns": List[Dict[str, Any]],      # Each noun: {word, synonyms, value?}
#   "adjectives": List[Dict[str, Any]], # Each adjective: {word, synonyms}
#   "prepositions": List[str],          # Simple strings
#   "articles": List[str]               # Simple strings
# }
MergedVocabulary = Dict[str, Any]


def _make_plural(word: str) -> str:
    """Generate simple plural form of a word."""
    if word.endswith('s') or word.endswith('x') or word.endswith('z'):
        return word + 'es'
    elif word.endswith('y') and len(word) > 1 and word[-2] not in 'aeiou':
        return word[:-1] + 'ies'
    else:
        return word + 's'


def extract_adjectives_from_state(state: GameState) -> List[Dict[str, Any]]:
    """
    Extract adjective entries from game state entities.

    Collects adjectives from items and exits that have explicit adjectives fields.
    These adjectives are used for disambiguation (e.g., "red spellbook" vs "blue spellbook").

    Args:
        state: GameState object

    Returns:
        List of adjective dicts with 'word' key
    """
    seen_adjectives: set[str] = set()
    adjectives: List[Dict[str, Any]] = []

    # Extract adjectives from items
    for item in state.items:
        item_adjectives = getattr(item, 'adjectives', None) or []
        for adj in item_adjectives:
            if adj and adj not in seen_adjectives:
                adjectives.append({"word": adj})
                seen_adjectives.add(adj)

    # Extract adjectives from exits
    for exit_entity in state.exits:
        exit_adjectives = getattr(exit_entity, 'adjectives', None) or []
        for adj in exit_adjectives:
            if adj and adj not in seen_adjectives:
                adjectives.append({"word": adj})
                seen_adjectives.add(adj)

    return adjectives


def extract_nouns_from_state(state: GameState) -> List[Dict[str, Any]]:
    """
    Extract noun entries from game state entities.

    Collects item names, NPC names, and door-related nouns from the game state
    to be used as nouns in the parser vocabulary.

    Also extracts individual words from multi-word names and adds plural
    synonyms so "examine journals" matches items like "Keeper's Journal".

    Args:
        state: GameState object

    Returns:
        List of noun dicts with 'word' key and optional 'synonyms'
    """
    seen_words: set[str] = set()
    nouns: List[Dict[str, Any]] = []
    component_words: set[str] = set()  # Track individual words for plural expansion

    # Extract item names
    for item in state.items:
        name = item.name
        if name and name not in seen_words:
            nouns.append({"word": name})
            seen_words.add(name)
            # Collect individual words for plural expansion
            for word in name.split():
                # Skip possessives and short words
                clean_word = word.lower().rstrip("'s").rstrip("'")
                if len(clean_word) >= 3:
                    component_words.add(clean_word)

    # Extract NPC names (actors that aren't the player)
    for actor_id, actor in state.actors.items():
        if actor_id != "player":
            name = actor.name
            if name and name not in seen_words:
                nouns.append({"word": name})
                seen_words.add(name)

    # Add "door" noun if there are any door items in the game
    has_doors = any(item.is_door for item in state.items)
    if has_doors and "door" not in seen_words:
        nouns.append({"word": "door"})
        seen_words.add("door")

    # Extract lock names
    for lock in state.locks:
        name = getattr(lock, 'name', None) or 'lock'
        if name and name not in seen_words:
            nouns.append({"word": name})
            seen_words.add(name)

    # Extract exit names and synonyms
    # Exits are first-class entities like items and should be in vocabulary
    for exit_entity in state.exits:
        exit_name: Optional[str] = getattr(exit_entity, 'name', None)
        if exit_name and exit_name not in seen_words:
            noun_entry = {"word": exit_name}
            # Add synonyms if present
            synonyms = getattr(exit_entity, 'synonyms', None)
            if synonyms:
                noun_entry["synonyms"] = synonyms
                # Also collect words from synonyms for plural expansion
                for syn in synonyms:
                    for word in syn.split():
                        clean_word = word.lower().rstrip("'s").rstrip("'")
                        if len(clean_word) >= 3:
                            component_words.add(clean_word)
            nouns.append(noun_entry)
            seen_words.add(exit_name)
            # Collect individual words for plural expansion
            for word in exit_name.split():
                clean_word = word.lower().rstrip("'s").rstrip("'")
                if len(clean_word) >= 3:
                    component_words.add(clean_word)

    # Add component words with plural synonyms
    # This allows "examine journals" to match items like "Keeper's Journal"
    seen_words_lower = {w.lower() for w in seen_words}
    for word in component_words:
        if word not in seen_words_lower:
            plural = _make_plural(word)
            nouns.append({"word": word, "synonyms": [plural]})
            seen_words_lower.add(word)

    return nouns


def merge_vocabulary(base_vocab: Dict[str, Any], extracted_nouns: List[Dict[str, Any]],
                     extracted_adjectives: List[Dict[str, Any]]) -> MergedVocabulary:
    """
    Merge base vocabulary with extracted nouns and adjectives from game state.

    Args:
        base_vocab: Base vocabulary dict from vocabulary.json
        extracted_nouns: List of noun dicts extracted from game state
        extracted_adjectives: List of adjective dicts extracted from game state

    Returns:
        Merged vocabulary dict with proper structure
    """
    # Copy base vocabulary
    merged = {
        "verbs": list(base_vocab.get("verbs", [])),
        "nouns": list(base_vocab.get("nouns", [])),
        "adjectives": list(base_vocab.get("adjectives", [])),
        "prepositions": list(base_vocab.get("prepositions", [])),
        "articles": list(base_vocab.get("articles", []))
    }

    # Get existing noun words
    existing_noun_words = {n["word"] for n in merged["nouns"]}

    # Add extracted nouns that aren't already present
    for noun in extracted_nouns:
        if noun["word"] not in existing_noun_words:
            merged["nouns"].append(noun)
            existing_noun_words.add(noun["word"])

    # Get existing adjective words
    existing_adj_words = {a["word"] for a in merged["adjectives"]}

    # Add extracted adjectives that aren't already present
    for adj in extracted_adjectives:
        if adj["word"] not in existing_adj_words:
            merged["adjectives"].append(adj)
            existing_adj_words.add(adj["word"])

    return merged
