"""Main parser implementation."""

from typing import List, Optional, Dict
import json

from src.word_entry import WordEntry, WordType
from src.parsed_command import ParsedCommand


class Parser:
    """
    Parser for text adventure game commands.

    Loads vocabulary from JSON file and parses user commands into
    structured ParsedCommand objects.
    """

    def __init__(self, vocabulary_file: str):
        """
        Initialize parser with vocabulary file.

        Args:
            vocabulary_file: Path to JSON vocabulary file

        Raises:
            FileNotFoundError: If vocabulary file doesn't exist
            json.JSONDecodeError: If vocabulary file is invalid JSON
        """
        self.word_table: List[WordEntry] = []
        self.word_lookup: Dict[str, WordEntry] = {}
        self._load_vocabulary(vocabulary_file)
        self._build_lookup_table()

    def _load_vocabulary(self, filename: str):
        """
        Load and parse the vocabulary JSON file.

        Args:
            filename: Path to vocabulary JSON file

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is malformed
        """
        with open(filename, 'r', encoding='utf-8') as f:
            vocab = json.load(f)

        # Process verbs
        for verb_data in vocab.get('verbs', []):
            entry = WordEntry(
                word=verb_data['word'],
                word_type=WordType.VERB,
                synonyms=verb_data.get('synonyms', []),
                value=verb_data.get('value'),
                object_required=verb_data.get('object_required', True)
            )
            self.word_table.append(entry)

        # Process nouns
        for noun_data in vocab.get('nouns', []):
            entry = WordEntry(
                word=noun_data['word'],
                word_type=WordType.NOUN,
                synonyms=noun_data.get('synonyms', []),
                value=noun_data.get('value')
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

        # Process directions
        for dir_data in vocab.get('directions', []):
            entry = WordEntry(
                word=dir_data['word'],
                word_type=WordType.DIRECTION,
                synonyms=dir_data.get('synonyms', []),
                value=dir_data.get('value')
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

    def _build_lookup_table(self):
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

        tokens = normalized.lower().split()
        if not tokens:
            return None

        entries: List[WordEntry] = []
        for token in tokens:
            entry = self._lookup_word(token)
            if entry is None:
                # Treat unknown words as potential adjectives
                entry = WordEntry(
                    word=token,
                    word_type=WordType.ADJECTIVE
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
        types = [e.word_type for e in entries]

        # Single word patterns
        if length == 1:
            # DIRECTION
            if types == [WordType.DIRECTION]:
                return ParsedCommand(direction=entries[0])

            # VERB (only if object not required)
            if types == [WordType.VERB]:
                verb = entries[0]
                if verb.object_required == False:
                    return ParsedCommand(verb=verb)
                elif verb.object_required == "optional":
                    return ParsedCommand(verb=verb, object_missing=True)
                # If object_required == True, return None (current behavior)

        # Two word patterns
        if length == 2:
            # VERB + NOUN
            if types == [WordType.VERB, WordType.NOUN]:
                return ParsedCommand(
                    verb=entries[0],
                    direct_object=entries[1]
                )

            # VERB + DIRECTION
            if types == [WordType.VERB, WordType.DIRECTION]:
                return ParsedCommand(
                    verb=entries[0],
                    direction=entries[1]
                )

        # Three word patterns
        if length == 3:
            # VERB + ADJECTIVE + NOUN
            if types == [WordType.VERB, WordType.ADJECTIVE, WordType.NOUN]:
                return ParsedCommand(
                    verb=entries[0],
                    direct_adjective=entries[1],
                    direct_object=entries[2]
                )

            # VERB + NOUN + NOUN (implicit preposition)
            if types == [WordType.VERB, WordType.NOUN, WordType.NOUN]:
                return ParsedCommand(
                    verb=entries[0],
                    direct_object=entries[1],
                    indirect_object=entries[2]
                )

            # VERB + PREPOSITION + NOUN
            if types == [WordType.VERB, WordType.PREPOSITION, WordType.NOUN]:
                return ParsedCommand(
                    verb=entries[0],
                    preposition=entries[1],
                    direct_object=entries[2]
                )

        # Four word patterns
        if length == 4:
            # VERB + ADJECTIVE + NOUN + NOUN
            if types == [WordType.VERB, WordType.ADJECTIVE, WordType.NOUN, WordType.NOUN]:
                return ParsedCommand(
                    verb=entries[0],
                    direct_adjective=entries[1],
                    direct_object=entries[2],
                    indirect_object=entries[3]
                )

            # VERB + NOUN + PREPOSITION + NOUN
            if types == [WordType.VERB, WordType.NOUN, WordType.PREPOSITION, WordType.NOUN]:
                return ParsedCommand(
                    verb=entries[0],
                    direct_object=entries[1],
                    preposition=entries[2],
                    indirect_object=entries[3]
                )

            # VERB + PREPOSITION + ADJECTIVE + NOUN
            if types == [WordType.VERB, WordType.PREPOSITION, WordType.ADJECTIVE, WordType.NOUN]:
                return ParsedCommand(
                    verb=entries[0],
                    preposition=entries[1],
                    direct_adjective=entries[2],
                    direct_object=entries[3]
                )

        # Five word patterns
        if length == 5:
            # VERB + ADJECTIVE + NOUN + PREPOSITION + NOUN
            if types == [WordType.VERB, WordType.ADJECTIVE, WordType.NOUN,
                        WordType.PREPOSITION, WordType.NOUN]:
                return ParsedCommand(
                    verb=entries[0],
                    direct_adjective=entries[1],
                    direct_object=entries[2],
                    preposition=entries[3],
                    indirect_object=entries[4]
                )

            # VERB + NOUN + PREPOSITION + ADJECTIVE + NOUN
            if types == [WordType.VERB, WordType.NOUN, WordType.PREPOSITION,
                        WordType.ADJECTIVE, WordType.NOUN]:
                return ParsedCommand(
                    verb=entries[0],
                    direct_object=entries[1],
                    preposition=entries[2],
                    indirect_adjective=entries[3],
                    indirect_object=entries[4]
                )

        # Six word patterns
        if length == 6:
            # VERB + ADJECTIVE + NOUN + PREPOSITION + ADJECTIVE + NOUN
            if types == [WordType.VERB, WordType.ADJECTIVE, WordType.NOUN,
                        WordType.PREPOSITION, WordType.ADJECTIVE, WordType.NOUN]:
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
            if entries[i].word_type == WordType.ADJECTIVE:
                # Collect consecutive adjectives
                adj_words = [entries[i].word]
                j = i + 1
                while j < len(entries) and entries[j].word_type == WordType.ADJECTIVE:
                    adj_words.append(entries[j].word)
                    j += 1

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
