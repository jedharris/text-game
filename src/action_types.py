"""Type definitions for action dictionaries.

This module defines the ActionDict type that represents the structure of
action dictionaries passed from the parser to handlers.

The parser guarantees that 'object' and 'indirect_object' fields are WordEntry
objects (or absent). Handlers should NOT need to convert strings - if a string
appears, it indicates a bug in the calling code.
"""

from typing import Optional
from typing_extensions import TypedDict

from src.types import ActorId
from src.word_entry import WordEntry


class ActionDict(TypedDict, total=False):
    """
    Type definition for action dictionaries.

    Required fields:
        actor_id: ID of the actor performing the action (defaults to "player")

    Optional fields (set by parser based on command structure):
        verb: The verb string (e.g., "take", "go", "examine")
        object: Direct object as WordEntry (e.g., the "key" in "take key")
        adjective: Adjective for direct object as string (e.g., "brass" in "take brass key")
        indirect_object: Indirect object as WordEntry (e.g., "box" in "put key in box")
        indirect_adjective: Adjective for indirect object as string
        preposition: Preposition string (e.g., "in", "on", "with")
        raw_after_preposition: Raw user input after preposition (for dialog topics)

    Type guarantees:
        - 'object' is always WordEntry or absent (never str)
        - 'indirect_object' is always WordEntry or absent (never str)
        - Adjectives and prepositions remain as str
    """
    actor_id: ActorId
    verb: str
    object: Optional[WordEntry]
    adjective: str
    indirect_object: Optional[WordEntry]
    indirect_adjective: str
    preposition: str
    raw_after_preposition: str
