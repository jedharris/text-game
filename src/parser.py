"""Main parser implementation."""

from typing import List, Optional, Dict, Any, Union, cast, Type, TypeVar
import json

from src.word_entry import WordEntry, WordType, WordTypeLike
from src.parsed_command import ParsedCommand


ParserType = TypeVar("ParserType", bound="Parser")

class Parser:
    """
    Parser for text adventure game commands.

    Loads vocabulary from JSON file and parses user commands into
    structured ParsedCommand objects.
    """

    def __init__(self, vocabulary: Union[str, Dict[str, Any]]):
        """
        Initialize parser with vocabulary data.

        Args:
            vocabulary: Path to JSON vocabulary file or in-memory vocabulary dict

        Raises:
            FileNotFoundError: If vocabulary file doesn't exist
            json.JSONDecodeError: If vocabulary file is invalid JSON
            TypeError: If vocabulary is not a str or dict
        """
        self.word_table: List[WordEntry] = []
        self.word_lookup: Dict[str, WordEntry] = {}

        vocab_data = self._load_vocabulary_source(vocabulary)
        self._populate_word_entries(vocab_data)
        self._build_lookup_table()

    @classmethod
    def from_vocab(cls: Type[ParserType], vocabulary: Dict[str, Any]) -> ParserType:
        """
        Create a parser from an in-memory vocabulary dict.

        This avoids file IO and makes intent explicit for callers that already
        have merged vocabulary available.
        """
        return cls(vocabulary)

    def _parse_word_type(self, word_type_data: Union[str, List[str]]) -> WordTypeLike:
        """
        Parse word_type from vocabulary data.

        Args:
            word_type_data: Either a string (single type) or list of strings (multi-type)

        Returns:
            WordType or Set[WordType]
        """
        if isinstance(word_type_data, list):
            # Multi-valued type
            return {WordType[t.upper()] for t in word_type_data}
        else:
            # Single type
            return WordType[word_type_data.upper()]

    def _load_vocabulary_source(self, source: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Load vocabulary from a filename or return the provided dict."""
        if isinstance(source, str):
            with open(source, 'r', encoding='utf-8') as f:
                return cast(Dict[str, Any], json.load(f))
        if isinstance(source, dict):
            return source
        raise TypeError("vocabulary must be a file path or a dict")

    def _populate_word_entries(self, vocab: Dict[str, Any]) -> None:
        """Populate word entries from a vocabulary dict."""

        # Process verbs
        for verb_data in vocab.get('verbs', []):
            # Handle multi-valued word_type if specified (like "open" as verb+adjective)
            word_type_raw = verb_data.get('word_type', 'verb')
            word_type = self._parse_word_type(word_type_raw)

            entry = WordEntry(
                word=verb_data['word'],
                word_type=word_type,
                synonyms=verb_data.get('synonyms', []),
                value=verb_data.get('value'),
                object_required=verb_data.get('object_required', True)
            )
            self.word_table.append(entry)

        # Process nouns
        for noun_data in vocab.get('nouns', []):
            # Handle multi-valued word_type if specified
            word_type_raw = noun_data.get('word_type', 'noun')
            word_type = self._parse_word_type(word_type_raw)

            # If noun has VERB type (like directions), also get object_required
            object_required = noun_data.get('object_required', True)

            entry = WordEntry(
                word=noun_data['word'],
                word_type=word_type,
                synonyms=noun_data.get('synonyms', []),
                value=noun_data.get('value'),
                object_required=object_required
            )
            self.word_table.append(entry)

        # Process adjectives
        for adj_data in vocab.get('adjectives', []):
            entry = WordEntry(
                word=adj_data['word'],
                word_type=WordType.ADJECTIVE,
                synonyms=adj_data.get('synonyms', []),
                value=adj_data.get('value')
            )
            self.word_table.append(entry)

        # Process prepositions (can be simple strings or dicts)
        for prep in vocab.get('prepositions', []):
            if isinstance(prep, str):
                entry = WordEntry(word=prep, word_type=WordType.PREPOSITION)
            else:
                entry = WordEntry(
                    word=prep['word'],
                    word_type=WordType.PREPOSITION,
                    synonyms=prep.get('synonyms', []),
                    value=prep.get('value')
                )
            self.word_table.append(entry)

        # Process articles (can be simple strings or dicts)
        for article in vocab.get('articles', []):
            if isinstance(article, str):
                entry = WordEntry(word=article, word_type=WordType.ARTICLE)
            else:
                entry = WordEntry(
                    word=article['word'],
                    word_type=WordType.ARTICLE,
                    synonyms=article.get('synonyms', []),
                    value=article.get('value')
                )
            self.word_table.append(entry)

    def _build_lookup_table(self) -> None:
        """
        Build hash table for O(1) word lookup.

        Creates a dictionary mapping words and their synonyms to
        their corresponding WordEntry objects for fast lookup.
        """
        for entry in self.word_table:
            # Add the main word
            self.word_lookup[entry.word] = entry
            # Add all synonyms
            for synonym in entry.synonyms:
                self.word_lookup[synonym] = entry

    def _lookup_word(self, word: str) -> Optional[WordEntry]:
        """
        Look up a word in the word table, checking synonyms.

        Args:
            word: The word to look up (should be lowercase)

        Returns:
            WordEntry if found, None otherwise
        """
        return self.word_lookup.get(word)

    def _matches_type(self, entry: WordEntry, target_type: WordType) -> bool:
        """
        Check if entry matches target type (supports multi-valued word_type).

        Args:
            entry: WordEntry to check
            target_type: WordType to match against

        Returns:
            True if entry's word_type includes target_type
        """
        # QUOTED_LITERAL acts as a NOUN in pattern matching
        if entry.word_type == WordType.QUOTED_LITERAL and target_type == WordType.NOUN:
            return True

        if isinstance(entry.word_type, set):
            return target_type in entry.word_type
        else:
            return entry.word_type == target_type

    def _types_match(self, entries: List[WordEntry], pattern: List[WordType]) -> bool:
        """
        Check if entries match a type pattern.

        Args:
            entries: List of WordEntry objects
            pattern: List of WordType values to match

        Returns:
            True if all entries match their corresponding pattern types
        """
        if len(entries) != len(pattern):
            return False
        return all(self._matches_type(e, p) for e, p in zip(entries, pattern))

    def _extract_quoted_strings(self, text: str) -> tuple[str, List[str]]:
        """
        Extract quoted strings from text and replace with placeholders.

        Supports both single quotes ('...') and double quotes ("...").

        Args:
            text: Input text that may contain quoted strings

        Returns:
            Tuple of (modified_text_with_placeholders, list_of_extracted_strings)
        """
        import re
        quoted_strings: List[str] = []

        # Pattern matches either "..." or '...' (non-greedy, handles escaped quotes)
        pattern = r'"([^"\\]*(?:\\.[^"\\]*)*)"|\'([^\'\\]*(?:\\.[^\'\\]*)*)\''

        def replace_quote(match: re.Match) -> str:
            # Extract content from either double or single quote group
            content = match.group(1) if match.group(1) is not None else match.group(2)
            idx = len(quoted_strings)
            quoted_strings.append(content)
            return f'__QUOTED_{idx}__'

        modified_text = re.sub(pattern, replace_quote, text)
        return modified_text, quoted_strings

    def parse_command(self, command: str) -> Optional[ParsedCommand]:
        """
        Parse a raw input string into a structured ParsedCommand.

        Args:
            command: Raw user input string

        Returns:
            ParsedCommand if parsing succeeds, None otherwise
        """
        if command is None:
            return None

        raw_input = command
        normalized = command.strip()
        if not normalized:
            return None

        # Extract quoted strings before tokenization
        normalized, quoted_strings = self._extract_quoted_strings(normalized)

        tokens = normalized.lower().split()
        if not tokens:
            return None

        entries: List[WordEntry] = []
        for i, token in enumerate(tokens):
            entry: Optional[WordEntry] = None

            # Check if token is a quoted string placeholder
            if token.startswith('__quoted_') and token.endswith('__'):
                # Extract index from __quoted_N__
                try:
                    idx = int(token[9:-2])
                    if 0 <= idx < len(quoted_strings):
                        # Create WordEntry for quoted literal
                        entry = WordEntry(
                            word=quoted_strings[idx],
                            word_type=WordType.QUOTED_LITERAL
                        )
                        entries.append(entry)
                        continue
                except (ValueError, IndexError):
                    pass  # Fall through to normal lookup

            if entry is None:
                entry = self._lookup_word(token)
            if entry is None:
                # Unknown word - determine type based on context
                # If followed by another unknown word or known noun, treat as adjective
                # Otherwise treat as noun (handler will resolve against game state)
                next_token = tokens[i + 1] if i + 1 < len(tokens) else None
                next_entry = self._lookup_word(next_token) if next_token else None

                if next_token and (next_entry is None or next_entry.word_type == WordType.NOUN):
                    # Unknown word before another potential noun -> adjective
                    entry = WordEntry(
                        word=token,
                        word_type=WordType.ADJECTIVE
                    )
                else:
                    # Unknown word at end or before non-noun -> noun
                    entry = WordEntry(
                        word=token,
                        word_type=WordType.NOUN
                    )
            if entry.word_type == WordType.ARTICLE:
                continue
            entries.append(entry)

        if not entries or len(entries) > 6:
            return None

        parsed = self._match_pattern(entries)
        if parsed is None:
            return None

        parsed.raw = raw_input
        return parsed

    def _match_pattern(self, entries: List[WordEntry]) -> Optional[ParsedCommand]:
        """
        Match a list of WordEntry objects to a command pattern.

        Args:
            entries: List of WordEntry objects (no articles)

        Returns:
            ParsedCommand if pattern matches, None otherwise
        """
        if not entries:
            return None

        # Collapse consecutive adjectives into single entries
        entries = self._collapse_adjectives(entries)

        length = len(entries)

        # Single word patterns
        if length == 1:
            # VERB (only if object not required or optional)
            if self._matches_type(entries[0], WordType.VERB):
                verb = entries[0]
                if verb.object_required == False:
                    return ParsedCommand(verb=verb)
                elif verb.object_required == "optional":
                    return ParsedCommand(verb=verb, object_missing=True)
                # If object_required == True, fall through to return None

            return None

        # Two word patterns
        if length == 2:
            # VERB + NOUN
            if self._types_match(entries, [WordType.VERB, WordType.NOUN]):
                return ParsedCommand(
                    verb=entries[0],
                    direct_object=entries[1]
                )

        # Three word patterns
        if length == 3:
            # VERB + ADJECTIVE + NOUN (includes directions as adjectives)
            if self._types_match(entries, [WordType.VERB, WordType.ADJECTIVE, WordType.NOUN]):
                return ParsedCommand(
                    verb=entries[0],
                    direct_adjective=entries[1],
                    direct_object=entries[2]
                )

            # VERB + NOUN + NOUN (implicit preposition)
            if self._types_match(entries, [WordType.VERB, WordType.NOUN, WordType.NOUN]):
                return ParsedCommand(
                    verb=entries[0],
                    direct_object=entries[1],
                    indirect_object=entries[2]
                )

            # VERB + PREPOSITION + NOUN
            if self._types_match(entries, [WordType.VERB, WordType.PREPOSITION, WordType.NOUN]):
                return ParsedCommand(
                    verb=entries[0],
                    preposition=entries[1],
                    direct_object=entries[2]
                )

        # Four word patterns
        if length == 4:
            # VERB + ADJECTIVE + NOUN + NOUN
            if self._types_match(entries, [WordType.VERB, WordType.ADJECTIVE, WordType.NOUN, WordType.NOUN]):
                return ParsedCommand(
                    verb=entries[0],
                    direct_adjective=entries[1],
                    direct_object=entries[2],
                    indirect_object=entries[3]
                )

            # VERB + NOUN + PREPOSITION + NOUN
            if self._types_match(entries, [WordType.VERB, WordType.NOUN, WordType.PREPOSITION, WordType.NOUN]):
                return ParsedCommand(
                    verb=entries[0],
                    direct_object=entries[1],
                    preposition=entries[2],
                    indirect_object=entries[3]
                )

            # VERB + PREPOSITION + ADJECTIVE + NOUN
            if self._types_match(entries, [WordType.VERB, WordType.PREPOSITION, WordType.ADJECTIVE, WordType.NOUN]):
                return ParsedCommand(
                    verb=entries[0],
                    preposition=entries[1],
                    direct_adjective=entries[2],
                    direct_object=entries[3]
                )

        # Five word patterns
        if length == 5:
            # VERB + ADJECTIVE + NOUN + PREPOSITION + NOUN
            if self._types_match(entries, [WordType.VERB, WordType.ADJECTIVE, WordType.NOUN,
                                           WordType.PREPOSITION, WordType.NOUN]):
                return ParsedCommand(
                    verb=entries[0],
                    direct_adjective=entries[1],
                    direct_object=entries[2],
                    preposition=entries[3],
                    indirect_object=entries[4]
                )

            # VERB + NOUN + PREPOSITION + ADJECTIVE + NOUN
            if self._types_match(entries, [WordType.VERB, WordType.NOUN, WordType.PREPOSITION,
                                           WordType.ADJECTIVE, WordType.NOUN]):
                return ParsedCommand(
                    verb=entries[0],
                    direct_object=entries[1],
                    preposition=entries[2],
                    indirect_adjective=entries[3],
                    indirect_object=entries[4]
                )

            # VERB + NOUN + PREPOSITION + NOUN + NOUN
            # Handle pattern like "pour water on gold mushroom" where vocabulary
            # extracts color words as nouns from item names. First NOUN after PREP
            # acts as adjective to second NOUN.
            if self._types_match(entries, [WordType.VERB, WordType.NOUN, WordType.PREPOSITION,
                                           WordType.NOUN, WordType.NOUN]):
                # Convert first NOUN after prep to adjective role
                adj_entry = WordEntry(
                    word=entries[3].word,
                    word_type=WordType.ADJECTIVE,
                    synonyms=entries[3].synonyms,
                    value=entries[3].value
                )
                return ParsedCommand(
                    verb=entries[0],
                    direct_object=entries[1],
                    preposition=entries[2],
                    indirect_adjective=adj_entry,
                    indirect_object=entries[4]
                )

        # Six word patterns
        if length == 6:
            # VERB + ADJECTIVE + NOUN + PREPOSITION + ADJECTIVE + NOUN
            if self._types_match(entries, [WordType.VERB, WordType.ADJECTIVE, WordType.NOUN,
                                           WordType.PREPOSITION, WordType.ADJECTIVE, WordType.NOUN]):
                return ParsedCommand(
                    verb=entries[0],
                    direct_adjective=entries[1],
                    direct_object=entries[2],
                    preposition=entries[3],
                    indirect_adjective=entries[4],
                    indirect_object=entries[5]
                )

        return None

    def _collapse_adjectives(self, entries: List[WordEntry]) -> List[WordEntry]:
        """
        Collapse consecutive adjectives into single WordEntry objects.

        E.g., [ADJ, ADJ, NOUN] becomes [ADJ, NOUN] where the first ADJ
        contains combined words like "rough wooden".

        Multi-type words (like "open" with VERB+ADJ) are context-sensitive:
        - At position 0: treated as VERB, not collapsed
        - After a VERB: treated as ADJECTIVE, can be collapsed

        Args:
            entries: List of WordEntry objects

        Returns:
            List with consecutive adjectives collapsed
        """
        if not entries:
            return entries

        result = []
        i = 0

        while i < len(entries):
            # Check if this entry can act as an adjective
            is_adjective = self._matches_type(entries[i], WordType.ADJECTIVE)

            # Multi-type entries with VERB are context-sensitive
            word_type = entries[i].word_type
            has_verb_type = isinstance(word_type, set) and WordType.VERB in word_type

            # If at position 0 and has VERB type, treat as VERB (don't collapse)
            if i == 0 and has_verb_type:
                result.append(entries[i])
                i += 1
                continue

            # If after a VERB and is an adjective, allow collapsing (even if multi-type)
            if is_adjective:
                # Collect consecutive adjectives
                adj_words = [entries[i].word]
                first_entry = entries[i]
                j = i + 1
                while j < len(entries):
                    # Check if next entry is an adjective (allow multi-type if not at position 0)
                    is_next_adj = self._matches_type(entries[j], WordType.ADJECTIVE)
                    if not is_next_adj:
                        break
                    adj_words.append(entries[j].word)
                    j += 1

                # If only one adjective and it has multi-valued types, keep original
                if len(adj_words) == 1 and isinstance(first_entry.word_type, set):
                    result.append(first_entry)
                else:
                    # Create combined adjective entry
                    combined = WordEntry(
                        word=" ".join(adj_words),
                        word_type=WordType.ADJECTIVE
                    )
                    result.append(combined)
                i = j
            else:
                result.append(entries[i])
                i += 1

        return result
