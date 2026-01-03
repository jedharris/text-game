"""Adapter that converts LLM parser output to ParsedCommand objects.

The LLM parser outputs simple dicts with string entity IDs:
    {"verb": "use", "object": "ice_wand", "indirect_object": "frozen_crystal"}

This adapter converts those to ParsedCommand with WordEntry objects by:
1. Validating verbs against vocabulary
2. Looking up entities in merged vocabulary
3. Creating WordEntry objects
4. Building ParsedCommand
"""

from typing import Dict, Any, Optional, List, Union
from src.parsed_command import ParsedCommand
from src.word_entry import WordEntry, WordType
from src.vocabulary_generator import MergedVocabulary


class LLMParserAdapter:
    """Converts LLM parser output (string IDs) to ParsedCommand (WordEntry objects)."""

    def __init__(self, merged_vocabulary: MergedVocabulary):
        """Initialize adapter with merged vocabulary.

        Args:
            merged_vocabulary: Merged vocabulary with verbs, nouns, adjectives, prepositions, articles.
        """
        self.merged_vocabulary = merged_vocabulary

        # Build lookup tables for fast access
        self._build_lookup_tables()

    def _build_lookup_tables(self) -> None:
        """Build fast lookup tables from vocabulary."""
        # Verb lookup: word → WordEntry
        self.verb_lookup: Dict[str, WordEntry] = {}
        for verb_data in self.merged_vocabulary.get('verbs', []):
            word = verb_data['word']
            word_entry = self._dict_to_word_entry(verb_data, WordType.VERB)
            self.verb_lookup[word] = word_entry

            # Also add synonyms
            for synonym in verb_data.get('synonyms', []):
                self.verb_lookup[synonym] = word_entry

        # Also check nouns and adjectives for multi-type words with verb type
        for section in ['nouns', 'adjectives']:
            for entry_data in self.merged_vocabulary.get(section, []):
                word_type = entry_data.get('word_type')
                # Check if this entry has verb type (multi-type word)
                if isinstance(word_type, list) and 'verb' in word_type:
                    word = entry_data['word']
                    # Only add if not already in verb_lookup (verbs section takes precedence)
                    if word not in self.verb_lookup:
                        word_entry = self._dict_to_word_entry(entry_data, WordType.VERB)
                        self.verb_lookup[word] = word_entry

                        # Also add synonyms
                        for synonym in entry_data.get('synonyms', []):
                            if synonym not in self.verb_lookup:
                                self.verb_lookup[synonym] = word_entry

        # Noun lookup: word → WordEntry (includes entity names)
        self.noun_lookup: Dict[str, WordEntry] = {}
        for noun_data in self.merged_vocabulary.get('nouns', []):
            word = noun_data['word']
            word_entry = self._dict_to_word_entry(noun_data, WordType.NOUN)
            self.noun_lookup[word] = word_entry

            # Add synonyms
            for synonym in noun_data.get('synonyms', []):
                self.noun_lookup[synonym] = word_entry

        # Preposition lookup
        # Note: prepositions are just a list of strings in vocabulary
        self.prep_lookup: Dict[str, WordEntry] = {}
        for prep_word in self.merged_vocabulary.get('prepositions', []):
            word_entry = WordEntry(
                word=prep_word,
                word_type=WordType.PREPOSITION,
                synonyms=[],
                object_required=False
            )
            self.prep_lookup[prep_word] = word_entry

    def _dict_to_word_entry(self, data: Dict[str, Any], word_type: WordType) -> WordEntry:
        """Convert vocabulary dict to WordEntry."""
        return WordEntry(
            word=data['word'],
            word_type=word_type,
            synonyms=data.get('synonyms', []),
            value=data.get('value'),
            object_required=data.get('object_required', True)
        )

    def to_parsed_command(
        self,
        parser_output: Optional[Dict[str, Any]],
        raw_input: str
    ) -> Optional[ParsedCommand]:
        """Convert LLM parser output to ParsedCommand.

        Args:
            parser_output: Dict from LLM parser with structure:
                {
                    "type": "command",
                    "action": {
                        "verb": str,
                        "object": Optional[str | list[str]],
                        "indirect_object": Optional[str],
                        "adjective": Optional[str],
                        "indirect_adjective": Optional[str],
                        "preposition": Optional[str]
                    }
                }
            raw_input: Original player input string

        Returns:
            ParsedCommand with WordEntry objects, or None if conversion fails
        """
        if parser_output is None:
            return None

        if parser_output.get('type') != 'command':
            return None

        action = parser_output.get('action', {})

        # Validate and lookup verb
        verb_str = action.get('verb')
        if not verb_str:
            return None

        verb = self.verb_lookup.get(verb_str)
        if not verb:
            # Unknown verb - reject
            return None

        # Lookup objects (these can be None)
        # IMPORTANT: For multi-item commands, object can be a list
        # Convert list[str] to list[WordEntry] by looking up each entity
        # Protocol handler will split this into separate commands
        object_field = action.get('object')
        direct_object: Optional[Union[WordEntry, List[WordEntry]]] = None
        if isinstance(object_field, list):
            # Multi-item command - lookup each entity ID
            word_entries = []
            for entity_id in object_field:
                entry = self._lookup_entity(entity_id)
                if entry:
                    word_entries.append(entry)
            # Pass list of WordEntry objects to protocol handler
            direct_object = word_entries if word_entries else None
        else:
            # Single item - lookup as usual
            direct_object = self._lookup_entity(object_field)

        indirect_object = self._lookup_entity(action.get('indirect_object'))

        # Lookup preposition
        prep_str = action.get('preposition')
        preposition = self.prep_lookup.get(prep_str) if prep_str else None

        # For now, skip adjectives (LLM parser doesn't produce them yet)
        # We could add adjective parsing later if needed

        return ParsedCommand(
            verb=verb,
            direct_object=direct_object,
            indirect_object=indirect_object,
            preposition=preposition,
            raw=raw_input,
            object_missing=False  # LLM parser handles this implicitly
        )

    def _lookup_entity(self, entity_id: Optional[str]) -> Optional[WordEntry]:
        """Lookup entity ID in vocabulary.

        Handles both single-word and multi-word entities:
        - "bucket" → lookup directly
        - "ice_wand" → try as-is, then try with spaces "ice wand"
        - "keepers_journal" → try "Keeper's journal" (with apostrophe and capitals)

        Args:
            entity_id: Entity ID string from parser (e.g., "ice_wand", "bucket")

        Returns:
            WordEntry if found, None otherwise
        """
        if not entity_id:
            return None

        # Filter out "none" - this is used in parser prompts to indicate empty lists
        # and should not be treated as a real object
        if entity_id.lower() == "none":
            return None

        # Try direct lookup (handles single-word entities)
        if entity_id in self.noun_lookup:
            return self.noun_lookup[entity_id]

        # Try with underscores converted to spaces (multi-word entities)
        # "ice_wand" → "ice wand"
        spaced_name = entity_id.replace('_', ' ')
        if spaced_name in self.noun_lookup:
            return self.noun_lookup[spaced_name]

        # Try lowercase variations
        if entity_id.lower() in self.noun_lookup:
            return self.noun_lookup[entity_id.lower()]

        if spaced_name.lower() in self.noun_lookup:
            return self.noun_lookup[spaced_name.lower()]

        # Try case-insensitive search through all nouns
        # This handles cases like "keepers_journal" → "Keeper's journal"
        entity_lower = entity_id.lower()
        spaced_lower = spaced_name.lower()

        # Also try without apostrophes for possessives
        entity_no_apos = entity_lower.replace("'", "")
        spaced_no_apos = spaced_lower.replace("'", "")

        for noun_key in self.noun_lookup.keys():
            noun_key_lower = noun_key.lower()
            noun_key_no_apos = noun_key_lower.replace("'", "")

            if (noun_key_lower == entity_lower or noun_key_lower == spaced_lower or
                noun_key_no_apos == entity_no_apos or noun_key_no_apos == spaced_no_apos):
                return self.noun_lookup[noun_key]

        # Entity not in vocabulary - could be a direction or dialogue topic
        # For directions (north, south, etc.), they might not be in nouns
        if entity_id in ['north', 'south', 'east', 'west', 'up', 'down', 'northeast', 'northwest', 'southeast', 'southwest']:
            return WordEntry(
                word=entity_id,
                word_type=WordType.NOUN,
                synonyms=[],
                object_required=False
            )

        # For dialogue topics (research, infection, etc.) that aren't in vocabulary,
        # create a WordEntry so they can be passed to the game engine for validation
        # The game engine's dialogue handlers will check if the topic is valid
        if entity_id and entity_id.isalpha():  # Simple word, likely a topic
            return WordEntry(
                word=entity_id,
                word_type=WordType.NOUN,
                synonyms=[],
                object_required=False
            )

        # Return None for invalid/hallucinated entities
        return None
