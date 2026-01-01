"""Vocabulary loading and merging helpers shared across entrypoints."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from src.vocabulary_generator import extract_nouns_from_state, merge_vocabulary, MergedVocabulary
from src.state_manager import GameState
from src.behavior_manager import BehaviorManager


def load_base_vocabulary(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the base vocabulary JSON."""
    vocab_path = path or Path(__file__).parent / "vocabulary.json"
    with open(vocab_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_merged_vocabulary(
    game_state: GameState,
    behavior_manager: BehaviorManager,
    base_vocab: Optional[Dict[str, Any]] = None,
    base_vocab_path: Optional[Path] = None,
) -> MergedVocabulary:
    """
    Build merged vocabulary: base + extracted nouns + behavior extensions.

    Args:
        game_state: Current GameState for noun extraction.
        behavior_manager: BehaviorManager providing behavior vocabulary.
        base_vocab: Optional preloaded base vocabulary dict.
        base_vocab_path: Optional path to base vocabulary JSON (used if base_vocab not provided).

    Returns:
        Properly structured merged vocabulary with verbs, nouns, adjectives, prepositions, articles.
    """
    vocab = base_vocab or load_base_vocabulary(base_vocab_path)
    extracted_nouns = extract_nouns_from_state(game_state)
    vocab_with_nouns = merge_vocabulary(vocab, extracted_nouns)
    return behavior_manager.get_merged_vocabulary(vocab_with_nouns)
