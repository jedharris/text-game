"""Main parser implementation."""

from typing import List, Optional, Dict, Union
import json
from pathlib import Path

from src.word_entry import WordEntry, WordType


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
                value=verb_data.get('value')
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
