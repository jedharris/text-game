"""Word entry data structures for the parser."""

from enum import Enum
from typing import Optional, List
from dataclasses import dataclass, field


class WordType(Enum):
    """Enumeration of word types recognized by the parser."""
    VERB = "VERB"
    NOUN = "NOUN"
    ADJECTIVE = "ADJECTIVE"
    PREPOSITION = "PREPOSITION"
    DIRECTION = "DIRECTION"
    ARTICLE = "ARTICLE"


@dataclass
class WordEntry:
    """
    Represents a single word in the vocabulary.

    Attributes:
        word: The actual word string
        word_type: The grammatical type of the word
        synonyms: List of alternative words with same meaning
        value: Optional numeric ID for game logic
    """
    word: str
    word_type: WordType
    synonyms: List[str] = field(default_factory=list)
    value: Optional[int] = None

    def __post_init__(self):
        """Initialize default values after dataclass construction."""
        if self.synonyms is None:
            self.synonyms = []
