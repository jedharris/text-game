# Text Adventure Game Parser - Initial Design

## Overview

This document describes the design for a simple, configurable parser for a text adventure game written in Python that handles 2-4 word commands. The parser is table-driven with vocabulary stored in a JSON file, allowing for easy configuration and extension of recognized words without modifying code.

## Core Components

### 1. Word Table (Dictionary)

The word table is the central configuration mechanism that defines all recognized vocabulary. Each entry maps a word to its grammatical type and optional metadata.

#### Word Types

- **VERB**: Action words (e.g., "take", "drop", "examine", "go")
- **NOUN**: Objects and entities (e.g., "sword", "door", "key")
- **ADJECTIVE**: Descriptive words that modify nouns (e.g., "red", "rusty", "wooden")
- **PREPOSITION**: Relational words (e.g., "with", "to", "in", "on")
- **DIRECTION**: Movement directions (e.g., "north", "south", "east", "west")
- **ARTICLE**: Ignored words (e.g., "the", "a", "an")

#### Word Table Structure

The word table is stored in a JSON file (`vocabulary.json`) with the following structure:

```json
{
  "verbs": [
    {
      "word": "take",
      "synonyms": ["get", "grab", "pick"],
      "value": 1
    }
  ],
  "nouns": [
    {
      "word": "key",
      "value": 101
    }
  ],
  "adjectives": [
    {
      "word": "rusty",
      "value": 201
    }
  ],
  "prepositions": ["with", "to", "in", "on"],
  "directions": [
    {
      "word": "north",
      "synonyms": ["n"],
      "value": 1
    }
  ],
  "articles": ["the", "a", "an"]
}
```

In Python, each word entry is represented as a dictionary:

```python
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

class WordType(Enum):
    VERB = "VERB"
    NOUN = "NOUN"
    ADJECTIVE = "ADJECTIVE"
    PREPOSITION = "PREPOSITION"
    DIRECTION = "DIRECTION"
    ARTICLE = "ARTICLE"

@dataclass
class WordEntry:
    word: str                      # The actual word
    word_type: WordType            # Grammatical type
    synonyms: List[str] = None     # Alternative words with same meaning
    value: Optional[int] = None    # Optional numeric ID for game logic

    def __post_init__(self):
        if self.synonyms is None:
            self.synonyms = []
```

#### Example Configuration File (vocabulary.json)

```json
{
  "verbs": [
    { "word": "take", "synonyms": ["get", "grab", "pick"], "value": 1 },
    { "word": "drop", "synonyms": ["put", "place"], "value": 2 },
    { "word": "examine", "synonyms": ["look", "inspect", "x"], "value": 3 },
    { "word": "go", "synonyms": [], "value": 4 },
    { "word": "open", "synonyms": [], "value": 5 },
    { "word": "unlock", "synonyms": [], "value": 6 },
    { "word": "attack", "synonyms": ["hit", "strike"], "value": 7 }
  ],
  "nouns": [
    { "word": "door", "value": 101 },
    { "word": "key", "value": 102 },
    { "word": "sword", "value": 103 },
    { "word": "chest", "value": 104 },
    { "word": "goblin", "value": 105 },
    { "word": "flask", "value": 106 }
  ],
  "adjectives": [
    { "word": "red", "value": 201 },
    { "word": "blue", "value": 202 },
    { "word": "rusty", "value": 203 },
    { "word": "wooden", "value": 204 },
    { "word": "iron", "value": 205 },
    { "word": "small", "value": 206 },
    { "word": "large", "value": 207 }
  ],
  "prepositions": ["with", "to", "in", "on", "under", "behind"],
  "directions": [
    { "word": "north", "synonyms": ["n"], "value": 1 },
    { "word": "south", "synonyms": ["s"], "value": 2 },
    { "word": "east", "synonyms": ["e"], "value": 3 },
    { "word": "west", "synonyms": ["w"], "value": 4 },
    { "word": "up", "synonyms": ["u"], "value": 5 },
    { "word": "down", "synonyms": ["d"], "value": 6 }
  ],
  "articles": ["the", "a", "an"]
}
```

### 2. Parser

The parser processes user input and produces structured command objects.

#### Parsing Process

1. **Tokenization**: Split input into lowercase words
2. **Word Lookup**: Match each word against the word table (including synonyms)
3. **Article Filtering**: Remove articles from the token stream
4. **Pattern Matching**: Match remaining tokens against valid command patterns
5. **Command Construction**: Build a structured command object

#### Command Structure

```python
@dataclass
class ParsedCommand:
    verb: Optional[WordEntry] = None              # The action verb
    direct_object: Optional[WordEntry] = None     # Primary noun (what)
    direct_adjective: Optional[WordEntry] = None  # Adjective modifying direct object
    preposition: Optional[WordEntry] = None       # Relational word (how/where)
    indirect_object: Optional[WordEntry] = None   # Secondary noun (with what)
    indirect_adjective: Optional[WordEntry] = None # Adjective modifying indirect object
    direction: Optional[WordEntry] = None         # Movement direction
    raw: str = ""                                 # Original input
```

#### Supported Command Patterns

The parser recognizes these patterns (with adjective support):

1. **One Word**
   - `DIRECTION` → "north", "south", "n"

2. **Two Words**
   - `VERB + NOUN` → "take sword", "examine door"
   - `VERB + DIRECTION` → "go north", "walk east"
   - `VERB + ADJECTIVE NOUN` → "take red" (noun implied from context)

3. **Three Words**
   - `VERB + ADJECTIVE + NOUN` → "take rusty key", "examine wooden door"
   - `VERB + NOUN + NOUN` → "unlock door key" (implicit "with")
   - `VERB + PREPOSITION + NOUN` → "look in chest"

4. **Four Words**
   - `VERB + ADJECTIVE + NOUN + PREPOSITION` → "take red key from"
   - `VERB + NOUN + PREPOSITION + NOUN` → "unlock door with key"
   - `VERB + PREPOSITION + ADJECTIVE + NOUN` → "look in wooden chest"
   - `VERB + ADJECTIVE + NOUN + NOUN` → "unlock rusty door key" (implicit "with")

5. **Five+ Words** (maximum complexity)
   - `VERB + ADJECTIVE + NOUN + PREPOSITION + NOUN` → "unlock rusty door with key"
   - `VERB + NOUN + PREPOSITION + ADJECTIVE + NOUN` → "unlock door with rusty key"
   - `VERB + ADJECTIVE + NOUN + PREPOSITION + ADJECTIVE + NOUN` → "unlock rusty door with iron key"

#### Error Handling

The parser should provide clear error messages:

- **Unknown word**: "I don't understand the word 'xyz'"
- **Invalid pattern**: "I don't understand that command"
- **Ambiguous command**: "What do you want to [verb]?"
- **Missing object**: "What do you want to [verb] it with?"

### 3. Parser Algorithm

```python
from typing import List, Optional, Dict, Union
import json

class Parser:
    def __init__(self, vocabulary_file: str):
        """Load vocabulary from JSON file and build lookup tables."""
        self.word_table: List[WordEntry] = []
        self._load_vocabulary(vocabulary_file)

    def _load_vocabulary(self, filename: str):
        """Load and parse the vocabulary JSON file."""
        with open(filename, 'r') as f:
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
                value=noun_data.get('value')
            )
            self.word_table.append(entry)

        # Process adjectives
        for adj_data in vocab.get('adjectives', []):
            entry = WordEntry(
                word=adj_data['word'],
                word_type=WordType.ADJECTIVE,
                value=adj_data.get('value')
            )
            self.word_table.append(entry)

        # Process prepositions (simple strings)
        for prep in vocab.get('prepositions', []):
            entry = WordEntry(word=prep, word_type=WordType.PREPOSITION)
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

        # Process articles (simple strings)
        for article in vocab.get('articles', []):
            entry = WordEntry(word=article, word_type=WordType.ARTICLE)
            self.word_table.append(entry)

    def parse_command(self, input_text: str) -> Union[ParsedCommand, str]:
        """
        Parse a command string and return a ParsedCommand or error message.

        Args:
            input_text: The raw command string from the user

        Returns:
            ParsedCommand object on success, error string on failure
        """
        # 1. Tokenize
        tokens = input_text.lower().split()

        # 2. Look up each word
        word_entries = []
        for token in tokens:
            entry = self._lookup_word(token)
            if entry is None:
                return f"I don't understand the word '{token}'"
            word_entries.append(entry)

        # 3. Filter articles
        filtered_entries = [e for e in word_entries if e.word_type != WordType.ARTICLE]

        # 4. Match pattern and build command
        command = self._match_pattern(filtered_entries)
        if command is None:
            return "I don't understand that command"

        command.raw = input_text
        return command

    def _lookup_word(self, word: str) -> Optional[WordEntry]:
        """Look up a word in the word table, checking synonyms."""
        for entry in self.word_table:
            if entry.word == word:
                return entry
            if word in entry.synonyms:
                return entry
        return None

    def _match_pattern(self, entries: List[WordEntry]) -> Optional[ParsedCommand]:
        """Match word entries against valid command patterns."""
        length = len(entries)

        if length == 0:
            return None

        # Helper function to get word types
        types = [e.word_type for e in entries]

        # One word patterns
        if length == 1:
            if types[0] == WordType.DIRECTION:
                return ParsedCommand(direction=entries[0])

        # Two word patterns
        if length == 2:
            if types == [WordType.VERB, WordType.NOUN]:
                return ParsedCommand(verb=entries[0], direct_object=entries[1])

            if types == [WordType.VERB, WordType.DIRECTION]:
                return ParsedCommand(verb=entries[0], direction=entries[1])

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
```

## Configuration and Extensibility

### Adding New Words

To add vocabulary, simply edit the `vocabulary.json` file:

```json
{
  "verbs": [
    { "word": "climb", "synonyms": [], "value": 8 }
  ],
  "nouns": [
    { "word": "ladder", "value": 107 }
  ],
  "adjectives": [
    { "word": "tall", "value": 208 }
  ]
}
```

After editing the file, restart the parser or reload the vocabulary:

```python
parser = Parser('vocabulary.json')
```

### Adding New Command Patterns

To support additional patterns, extend the `_match_pattern` method in the `Parser` class with new conditional branches. For example, to add support for "VERB + VERB" patterns:

```python
def _match_pattern(self, entries: List[WordEntry]) -> Optional[ParsedCommand]:
    # ... existing patterns ...

    # Two word patterns
    if length == 2:
        # Add new pattern
        if types == [WordType.VERB, WordType.VERB]:
            return ParsedCommand(
                verb=entries[0],
                # Custom handling for second verb
            )
```

### Vocabulary File Location

The vocabulary file should be stored in a standard location:

```
project_root/
├── parser.py           # Parser implementation
├── vocabulary.json     # Main vocabulary file
├── game.py            # Main game logic
└── data/
    └── custom_vocab.json  # Optional custom vocabulary
```

## Usage Example

```python
# Initialize parser with vocabulary file
parser = Parser('vocabulary.json')

# Parse simple command
cmd1 = parser.parse_command("take sword")
# Result: ParsedCommand(verb=<take>, direct_object=<sword>)

# Parse with articles (filtered)
cmd2 = parser.parse_command("take the sword")
# Result: ParsedCommand(verb=<take>, direct_object=<sword>)

# Parse command with adjective
cmd3 = parser.parse_command("take rusty key")
# Result: ParsedCommand(verb=<take>, direct_adjective=<rusty>, direct_object=<key>)

# Parse complex command
cmd4 = parser.parse_command("unlock door with key")
# Result: ParsedCommand(
#     verb=<unlock>,
#     direct_object=<door>,
#     preposition=<with>,
#     indirect_object=<key>
# )

# Parse command with two adjectives
cmd5 = parser.parse_command("unlock rusty door with iron key")
# Result: ParsedCommand(
#     verb=<unlock>,
#     direct_adjective=<rusty>,
#     direct_object=<door>,
#     preposition=<with>,
#     indirect_adjective=<iron>,
#     indirect_object=<key>
# )

# Parse with synonym
cmd6 = parser.parse_command("grab the sword")
# Result: ParsedCommand(verb=<take>, direct_object=<sword>)

# Parse direction
cmd7 = parser.parse_command("north")
# Result: ParsedCommand(direction=<north>)

# Parse with direction synonym
cmd8 = parser.parse_command("n")
# Result: ParsedCommand(direction=<north>)

# Error handling
cmd9 = parser.parse_command("frobulate the widget")
# Result: "I don't understand the word 'frobulate'"

# Using the command in game logic
command = parser.parse_command("take red key")
if isinstance(command, str):
    print(command)  # Error message
else:
    # Process command
    if command.verb and command.verb.value == 1:  # TAKE
        obj_name = command.direct_object.word
        if command.direct_adjective:
            obj_name = f"{command.direct_adjective.word} {obj_name}"
        print(f"You take the {obj_name}")
```

## Advantages of This Design

1. **Configurable**: All vocabulary is defined in a JSON file, editable without code changes
2. **Python-Native**: Uses dataclasses, type hints, and Pythonic patterns
3. **Extensible**: Easy to add new words by editing the JSON file
4. **Synonym Support**: Multiple words can map to the same action/object
5. **Adjective Support**: Built-in support for descriptive words modifying nouns
6. **Clear Structure**: Parsed commands have well-defined components using dataclasses
7. **Error Messages**: Provides helpful feedback for invalid input
8. **Simple Implementation**: Straightforward algorithm, easy to debug and maintain
9. **Type Safety**: Uses Python type hints for better IDE support and error detection
10. **Flexible Patterns**: Handles 1-6 word commands with adjective combinations

## Implementation Notes

### Performance Considerations

For larger vocabularies, consider optimizing word lookup:

```python
class Parser:
    def __init__(self, vocabulary_file: str):
        self.word_table: List[WordEntry] = []
        self.word_lookup: Dict[str, WordEntry] = {}
        self._load_vocabulary(vocabulary_file)
        self._build_lookup_table()

    def _build_lookup_table(self):
        """Build hash table for O(1) word lookup."""
        for entry in self.word_table:
            self.word_lookup[entry.word] = entry
            for synonym in entry.synonyms:
                self.word_lookup[synonym] = entry

    def _lookup_word(self, word: str) -> Optional[WordEntry]:
        """O(1) lookup using dictionary."""
        return self.word_lookup.get(word)
```

### Testing

Example unit tests:

```python
import unittest

class TestParser(unittest.TestCase):
    def setUp(self):
        self.parser = Parser('test_vocabulary.json')

    def test_simple_verb_noun(self):
        cmd = self.parser.parse_command("take sword")
        self.assertIsInstance(cmd, ParsedCommand)
        self.assertEqual(cmd.verb.word, "take")
        self.assertEqual(cmd.direct_object.word, "sword")

    def test_adjective_support(self):
        cmd = self.parser.parse_command("take rusty key")
        self.assertEqual(cmd.direct_adjective.word, "rusty")
        self.assertEqual(cmd.direct_object.word, "key")

    def test_article_filtering(self):
        cmd = self.parser.parse_command("take the sword")
        self.assertEqual(cmd.direct_object.word, "sword")

    def test_synonym_resolution(self):
        cmd = self.parser.parse_command("grab sword")
        self.assertEqual(cmd.verb.word, "take")  # Synonym resolved

    def test_unknown_word(self):
        result = self.parser.parse_command("frobulate widget")
        self.assertIsInstance(result, str)
        self.assertIn("frobulate", result)
```

## Future Enhancements

- **Multiple Adjectives**: "take small red key"
- **Adverb Support**: "open door carefully", "walk north quickly"
- **Pronoun Resolution**: "examine it", "take them" (requires game state)
- **Partial Matching**: "exam" for "examine" (fuzzy matching)
- **Context-Aware Parsing**: Use game state to disambiguate commands
- **Multi-sentence Input**: Handle multiple commands separated by periods/commas
- **Command History**: Track previous commands for "again" or "repeat"
- **Ambiguity Resolution**: "Which key do you mean: the red key or the blue key?"
