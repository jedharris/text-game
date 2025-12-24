"""Word entry data structures for the parser."""

from enum import Enum
from typing import Optional, List, Set, Union
from dataclasses import dataclass, field

# Alias for single or multi-valued word types
WordTypeLike = Union["WordType", Set["WordType"]]


class WordType(Enum):
    """Enumeration of word types recognized by the parser."""
    VERB = "VERB"
    NOUN = "NOUN"
    ADJECTIVE = "ADJECTIVE"
    PREPOSITION = "PREPOSITION"
    ARTICLE = "ARTICLE"
    FILENAME = "FILENAME"
    QUOTED_LITERAL = "QUOTED_LITERAL"  # Quoted strings that bypass parsing


@dataclass
class WordEntry:
    """
    Represents a single word in the vocabulary.

    Attributes:
        word: The actual word string
        word_type: The grammatical type(s) of the word (single WordType or Set[WordType])
        synonyms: List of alternative words with same meaning
        value: Optional numeric ID for game logic
        object_required: For verbs, whether direct object is required (True/False/"optional")
    """
    word: str
    word_type: WordTypeLike  # Single type or set of types
    synonyms: List[str] = field(default_factory=list)
    value: Optional[int] = None
    object_required: bool | str = True  # True, False, or "optional"

    def __post_init__(self):
        """Initialize default values after dataclass construction."""
        if self.synonyms is None:
            self.synonyms = []
