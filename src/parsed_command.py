"""Parsed command data structure."""

from dataclasses import dataclass
from typing import Optional
from src.word_entry import WordEntry


@dataclass
class ParsedCommand:
    """
    Represents a parsed user command.

    Attributes:
        verb: The action verb (if present)
        direct_object: Primary noun being acted upon (includes directions)
        direct_adjective: Adjective modifying direct_object (includes directions as adjectives)
        preposition: Relational word (with, to, in, etc.)
        indirect_object: Secondary noun
        indirect_adjective: Adjective modifying indirect_object
        raw: Original input string (preserved exactly as entered)
        object_missing: True if verb accepts optional object but none provided
    """
    verb: Optional[WordEntry] = None
    direct_object: Optional[WordEntry] = None
    direct_adjective: Optional[WordEntry] = None
    preposition: Optional[WordEntry] = None
    indirect_object: Optional[WordEntry] = None
    indirect_adjective: Optional[WordEntry] = None
    raw: str = ""
    object_missing: bool = False
