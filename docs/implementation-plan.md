# Parser Implementation Plan

## Overview

This document provides a detailed, step-by-step implementation plan for the text adventure game parser as described in [initial-design.md](initial-design.md) and tested according to [../tests/test-plan.md](../tests/test-plan.md).

## Project Structure

```
text-game/
├── docs/
│   ├── initial-design.md           # Design specification
│   └── implementation-plan.md      # This file
├── tests/
│   ├── test-plan.md               # Test specification
│   ├── __init__.py
│   ├── test_word_entry.py         # WordEntry tests
│   ├── test_vocabulary_loading.py # Vocabulary loading tests
│   ├── test_parser.py             # Main parser tests
│   ├── test_pattern_matching.py   # Pattern matching tests
│   ├── test_edge_cases.py         # Edge cases & error tests
│   ├── test_performance.py        # Performance benchmarks
│   ├── test_regression.py         # Regression tests
│   ├── test_helpers.py            # Test utilities
│   └── fixtures/
│       ├── test_vocabulary.json
│       ├── minimal_vocabulary.json
│       ├── empty_vocabulary.json
│       ├── invalid_vocabulary.json
│       ├── large_vocabulary.json
│       └── test_commands.json
├── src/
│   ├── __init__.py
│   ├── word_entry.py              # WordEntry and WordType classes
│   ├── parsed_command.py          # ParsedCommand dataclass
│   └── parser.py                  # Main Parser class
├── data/
│   └── vocabulary.json            # Production vocabulary
├── examples/
│   ├── simple_game.py             # Example usage
│   └── interactive_parser.py      # Interactive testing tool
├── vocabulary.json                # Default vocabulary (symlink to data/)
├── requirements.txt               # Python dependencies
├── setup.py                       # Package setup
└── README.md                      # Project documentation
```

## Implementation Phases

### Phase 0: Project Setup (Day 1)

#### Tasks
1. Create directory structure
2. Set up Python virtual environment
3. Create requirements.txt
4. Initialize git repository (if not done)
5. Create placeholder files

#### Deliverables
- [ ] Complete project directory structure
- [ ] `requirements.txt` with dependencies
- [ ] Virtual environment activated
- [ ] All `__init__.py` files created

#### Requirements File

**File**: `requirements.txt`

```txt
# No external dependencies for core parser
# Development dependencies (optional)
coverage>=7.0.0
```

---

### Phase 1: Core Data Structures (Day 1-2)

Implement the fundamental data structures before any logic.

#### Step 1.1: WordType Enum

**File**: `src/word_entry.py`

```python
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
```

**Tests to Pass**: WE-004

#### Step 1.2: WordEntry Dataclass

**File**: `src/word_entry.py` (continued)

```python
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
```

**Tests to Pass**: WE-001, WE-002, WE-003, WE-005, WE-006

**Validation**:
- Run `python -m unittest tests.test_word_entry -v`
- All WE-* tests should pass

#### Step 1.3: ParsedCommand Dataclass

**File**: `src/parsed_command.py`

```python
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
        direct_object: Primary noun being acted upon
        direct_adjective: Adjective modifying direct_object
        preposition: Relational word (with, to, in, etc.)
        indirect_object: Secondary noun
        indirect_adjective: Adjective modifying indirect_object
        direction: Movement direction (if present)
        raw: Original input string (preserved exactly as entered)
    """
    verb: Optional[WordEntry] = None
    direct_object: Optional[WordEntry] = None
    direct_adjective: Optional[WordEntry] = None
    preposition: Optional[WordEntry] = None
    indirect_object: Optional[WordEntry] = None
    indirect_adjective: Optional[WordEntry] = None
    direction: Optional[WordEntry] = None
    raw: str = ""
```

**Tests to Pass**: PM-* tests will validate this structure

**Deliverables**:
- [ ] `src/word_entry.py` with WordType and WordEntry
- [ ] `src/parsed_command.py` with ParsedCommand
- [ ] All Phase 1 tests passing

---

### Phase 2: Vocabulary Loading (Day 2-3)

Implement JSON vocabulary file loading.

#### Step 2.1: Create Test Fixtures

Create all test vocabulary files as specified in test-plan.md:

**File**: `tests/fixtures/test_vocabulary.json`
- Complete vocabulary with verbs, nouns, adjectives, prepositions, directions, articles
- See test-plan.md for full content

**File**: `tests/fixtures/minimal_vocabulary.json`
- Minimal set for basic tests

**File**: `tests/fixtures/empty_vocabulary.json`
- Empty arrays for all word types

**File**: `tests/fixtures/invalid_vocabulary.json`
```json
{
  "verbs": [
    { "word": "take", "missing_bracket":
  ]
}
```

#### Step 2.2: Vocabulary Loading Method

**File**: `src/parser.py`

```python
"""Main parser implementation."""

from typing import List, Optional, Dict, Union
import json
from pathlib import Path

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
        self._load_vocabulary(vocabulary_file)

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
```

**Tests to Pass**: VL-001 through VL-012

**Validation**:
- Run `python -m unittest tests.test_vocabulary_loading -v`
- All VL-* tests should pass

**Deliverables**:
- [ ] Test fixture files created
- [ ] `_load_vocabulary()` method implemented
- [ ] All vocabulary loading tests passing

---

### Phase 3: Word Lookup (Day 3)

Implement word lookup with synonym support.

#### Step 3.1: Basic Lookup Method

**File**: `src/parser.py` (add to Parser class)

```python
    def _lookup_word(self, word: str) -> Optional[WordEntry]:
        """
        Look up a word in the word table, checking synonyms.

        Args:
            word: The word to look up (should be lowercase)

        Returns:
            WordEntry if found, None otherwise
        """
        for entry in self.word_table:
            # Check exact match
            if entry.word == word:
                return entry
            # Check synonyms
            if word in entry.synonyms:
                return entry
        return None
```

**Tests to Pass**: WL-001 through WL-009

**Validation**:
- Run `python -m unittest tests.test_parser.TestWordLookup -v`

#### Step 3.2: Performance Optimization (Optional)

For better performance with large vocabularies, add hash table:

**File**: `src/parser.py` (modify Parser class)

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

**Tests to Pass**: PF-004, PF-006

**Deliverables**:
- [ ] `_lookup_word()` method implemented
- [ ] All word lookup tests passing
- [ ] Optional: Performance optimization added

---

### Phase 4: Pattern Matching (Day 4-6)

Implement the core pattern matching logic progressively.

#### Step 4.1: One and Two Word Patterns

**File**: `src/parser.py` (add to Parser class)

```python
    def _match_pattern(self, entries: List[WordEntry]) -> Optional[ParsedCommand]:
        """
        Match word entries against valid command patterns.

        Args:
            entries: List of WordEntry objects (after article filtering)

        Returns:
            ParsedCommand if pattern matches, None otherwise
        """
        length = len(entries)

        if length == 0:
            return None

        # Get word types for pattern matching
        types = [e.word_type for e in entries]

        # One word patterns
        if length == 1:
            # DIRECTION only
            if types[0] == WordType.DIRECTION:
                return ParsedCommand(direction=entries[0])

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

        # More patterns to be added...
        return None
```

**Tests to Pass**: PM-001 through PM-006

**Validation**:
- Run `python -m unittest tests.test_pattern_matching.TestPatternMatching12Words -v`

#### Step 4.2: Three Word Patterns

Add to `_match_pattern()`:

```python
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
```

**Tests to Pass**: PM-101 through PM-105

#### Step 4.3: Four Word Patterns

Add to `_match_pattern()`:

```python
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
```

**Tests to Pass**: PM-201 through PM-203

#### Step 4.4: Five and Six Word Patterns

Add to `_match_pattern()`:

```python
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

**Tests to Pass**: PM-301 through PM-305

**Deliverables**:
- [ ] All pattern matching implemented
- [ ] All PM-* tests passing

---

### Phase 5: Main Parser Logic (Day 6-7)

Implement the main parsing pipeline.

#### Step 5.1: Parse Command Method

**File**: `src/parser.py` (add to Parser class)

```python
    def parse_command(self, input_text: str) -> Union[ParsedCommand, str]:
        """
        Parse a command string and return a ParsedCommand or error message.

        Args:
            input_text: The raw command string from the user

        Returns:
            ParsedCommand object on success, error string on failure
        """
        # 1. Tokenize - split on whitespace and convert to lowercase
        tokens = input_text.lower().split()

        # Handle empty input
        if not tokens:
            return "I don't understand that command"

        # 2. Look up each word
        word_entries = []
        for token in tokens:
            entry = self._lookup_word(token)
            if entry is None:
                return f"I don't understand the word '{token}'"
            word_entries.append(entry)

        # 3. Filter articles
        filtered_entries = [e for e in word_entries
                           if e.word_type != WordType.ARTICLE]

        # Handle case where only articles remain
        if not filtered_entries:
            return "I don't understand that command"

        # 4. Match pattern and build command
        command = self._match_pattern(filtered_entries)
        if command is None:
            return "I don't understand that command"

        # 5. Preserve original input
        command.raw = input_text

        return command
```

**Tests to Pass**:
- All basic parsing tests
- AF-001 through AF-007 (article filtering)
- EH-001 through EH-012 (error handling)
- EC-001 through EC-012 (edge cases)

**Validation**:
- Run `python -m unittest tests.test_parser -v`
- Run `python -m unittest tests.test_edge_cases -v`

**Deliverables**:
- [ ] `parse_command()` method implemented
- [ ] All parsing tests passing
- [ ] All article filtering tests passing
- [ ] All error handling tests passing
- [ ] All edge case tests passing

---

### Phase 6: Production Vocabulary (Day 7)

Create the production vocabulary file.

#### Step 6.1: Create Production Vocabulary

**File**: `data/vocabulary.json`

Use the example from initial-design.md, expanded as needed:

```json
{
  "verbs": [
    { "word": "take", "synonyms": ["get", "grab", "pick"], "value": 1 },
    { "word": "drop", "synonyms": ["put", "place"], "value": 2 },
    { "word": "examine", "synonyms": ["look", "inspect", "x"], "value": 3 },
    { "word": "go", "synonyms": ["walk", "move"], "value": 4 },
    { "word": "open", "synonyms": [], "value": 5 },
    { "word": "close", "synonyms": ["shut"], "value": 6 },
    { "word": "unlock", "synonyms": [], "value": 7 },
    { "word": "lock", "synonyms": [], "value": 8 },
    { "word": "attack", "synonyms": ["hit", "strike", "fight", "kill"], "value": 9 },
    { "word": "use", "synonyms": [], "value": 10 },
    { "word": "eat", "synonyms": ["consume"], "value": 11 },
    { "word": "drink", "synonyms": [], "value": 12 },
    { "word": "read", "synonyms": [], "value": 13 },
    { "word": "climb", "synonyms": [], "value": 14 },
    { "word": "pull", "synonyms": ["yank"], "value": 15 },
    { "word": "push", "synonyms": ["press"], "value": 16 }
  ],
  "nouns": [
    { "word": "door", "value": 101 },
    { "word": "key", "value": 102 },
    { "word": "sword", "value": 103 },
    { "word": "chest", "value": 104 },
    { "word": "goblin", "value": 105 },
    { "word": "flask", "value": 106 },
    { "word": "potion", "value": 107 },
    { "word": "coin", "value": 108 },
    { "word": "lock", "value": 109 },
    { "word": "table", "value": 110 },
    { "word": "book", "value": 111 },
    { "word": "ladder", "value": 112 },
    { "word": "lever", "value": 113 },
    { "word": "button", "value": 114 }
  ],
  "adjectives": [
    { "word": "red", "value": 201 },
    { "word": "blue", "value": 202 },
    { "word": "rusty", "value": 203 },
    { "word": "wooden", "value": 204 },
    { "word": "iron", "value": 205 },
    { "word": "small", "value": 206 },
    { "word": "large", "value": 207 },
    { "word": "golden", "value": 208 },
    { "word": "silver", "value": 209 },
    { "word": "ancient", "value": 210 },
    { "word": "heavy", "value": 211 },
    { "word": "light", "value": 212 }
  ],
  "prepositions": ["with", "to", "in", "on", "under", "behind", "from", "into", "onto"],
  "directions": [
    { "word": "north", "synonyms": ["n"], "value": 1 },
    { "word": "south", "synonyms": ["s"], "value": 2 },
    { "word": "east", "synonyms": ["e"], "value": 3 },
    { "word": "west", "synonyms": ["w"], "value": 4 },
    { "word": "up", "synonyms": ["u"], "value": 5 },
    { "word": "down", "synonyms": ["d"], "value": 6 },
    { "word": "northeast", "synonyms": ["ne"], "value": 7 },
    { "word": "northwest", "synonyms": ["nw"], "value": 8 },
    { "word": "southeast", "synonyms": ["se"], "value": 9 },
    { "word": "southwest", "synonyms": ["sw"], "value": 10 }
  ],
  "articles": ["the", "a", "an"]
}
```

#### Step 6.2: Create Symlink

```bash
cd /Users/jed/Development/text-game
ln -s data/vocabulary.json vocabulary.json
```

**Deliverables**:
- [ ] Production vocabulary file created
- [ ] Symlink created (optional)

---

### Phase 7: Examples and Documentation (Day 8)

Create example programs and update documentation.

#### Step 7.1: Simple Game Example

**File**: `examples/simple_game.py`

```python
"""Simple game demonstrating parser usage."""

from src.parser import Parser, ParsedCommand


def main():
    # Initialize parser
    parser = Parser('vocabulary.json')

    # Game state
    inventory = []
    location = "start"

    print("Welcome to the Simple Adventure!")
    print("Type 'quit' to exit.")
    print()

    while True:
        # Get user input
        command_text = input("> ").strip()

        if command_text.lower() == 'quit':
            print("Thanks for playing!")
            break

        # Parse command
        result = parser.parse_command(command_text)

        # Handle errors
        if isinstance(result, str):
            print(result)
            continue

        # Process command
        command: ParsedCommand = result

        if command.direction:
            print(f"You go {command.direction.word}.")
        elif command.verb and command.verb.word == "take":
            if command.direct_object:
                obj_name = command.direct_object.word
                if command.direct_adjective:
                    obj_name = f"{command.direct_adjective.word} {obj_name}"
                inventory.append(obj_name)
                print(f"You take the {obj_name}.")
        elif command.verb and command.verb.word == "examine":
            if command.direct_object:
                print(f"You examine the {command.direct_object.word}.")
        else:
            print("I don't know how to do that.")


if __name__ == '__main__':
    main()
```

#### Step 7.2: Interactive Parser Tool

**File**: `examples/interactive_parser.py`

```python
"""Interactive parser testing tool."""

from src.parser import Parser, ParsedCommand
import json


def format_command(cmd: ParsedCommand) -> str:
    """Format a ParsedCommand for display."""
    parts = []
    if cmd.verb:
        parts.append(f"verb={cmd.verb.word}")
    if cmd.direct_adjective:
        parts.append(f"direct_adj={cmd.direct_adjective.word}")
    if cmd.direct_object:
        parts.append(f"direct_obj={cmd.direct_object.word}")
    if cmd.preposition:
        parts.append(f"prep={cmd.preposition.word}")
    if cmd.indirect_adjective:
        parts.append(f"indirect_adj={cmd.indirect_adjective.word}")
    if cmd.indirect_object:
        parts.append(f"indirect_obj={cmd.indirect_object.word}")
    if cmd.direction:
        parts.append(f"direction={cmd.direction.word}")

    return "ParsedCommand(" + ", ".join(parts) + ")"


def main():
    parser = Parser('vocabulary.json')

    print("Interactive Parser Testing Tool")
    print("Enter commands to see how they're parsed.")
    print("Type 'quit' to exit, 'stats' for parser statistics.")
    print()

    while True:
        command_text = input("> ").strip()

        if command_text.lower() == 'quit':
            break

        if command_text.lower() == 'stats':
            print(f"Vocabulary size: {len(parser.word_table)} words")
            continue

        result = parser.parse_command(command_text)

        if isinstance(result, str):
            print(f"ERROR: {result}")
        else:
            print(format_command(result))
            print(f"Raw: {result.raw}")
        print()


if __name__ == '__main__':
    main()
```

#### Step 7.3: Update README

**File**: `README.md`

```markdown
# Text Adventure Game Parser

A simple, configurable parser for text adventure games written in Python. Handles 1-6 word commands with support for verbs, nouns, adjectives, prepositions, and directions.

## Features

- **Table-driven**: All vocabulary in editable JSON file
- **Adjective support**: Handle descriptive words ("take rusty key")
- **Synonym support**: Multiple words for same action ("take" = "get" = "grab")
- **Article filtering**: Automatically ignores "the", "a", "an"
- **Type-safe**: Uses Python dataclasses and type hints
- **Well-tested**: 95%+ code coverage

## Installation

```bash
# Clone repository
git clone <repository-url>
cd text-game

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install (no dependencies for core parser)
pip install -e .
```

## Quick Start

```python
from src.parser import Parser

# Initialize parser with vocabulary
parser = Parser('vocabulary.json')

# Parse a command
command = parser.parse_command("take rusty key")

# Check for errors
if isinstance(command, str):
    print(f"Error: {command}")
else:
    # Access parsed components
    print(f"Verb: {command.verb.word}")
    print(f"Adjective: {command.direct_adjective.word}")
    print(f"Object: {command.direct_object.word}")
```

## Examples

See `examples/` directory:
- `simple_game.py` - Basic adventure game
- `interactive_parser.py` - Test parser interactively

## Testing

```bash
# Run all tests
python -m unittest discover tests

# Run with coverage
pip install coverage
coverage run -m unittest discover tests
coverage report
```

## Documentation

- [Design Document](docs/initial-design.md)
- [Implementation Plan](docs/implementation-plan.md)
- [Test Plan](tests/test-plan.md)

## License

MIT
```

**Deliverables**:
- [ ] Example programs created
- [ ] README.md updated
- [ ] All documentation cross-referenced

---

### Phase 8: Testing and Validation (Day 9-10)

Run complete test suite and fix any issues.

#### Test Execution Order

1. **Unit Tests - Data Structures**
   ```bash
   python -m unittest tests.test_word_entry -v
   ```

2. **Unit Tests - Vocabulary Loading**
   ```bash
   python -m unittest tests.test_vocabulary_loading -v
   ```

3. **Unit Tests - Word Lookup**
   ```bash
   python -m unittest tests.test_parser.TestWordLookup -v
   ```

4. **Unit Tests - Pattern Matching**
   ```bash
   python -m unittest tests.test_pattern_matching -v
   ```

5. **Unit Tests - Article Filtering**
   ```bash
   python -m unittest tests.test_parser.TestArticleFiltering -v
   ```

6. **Unit Tests - Error Handling**
   ```bash
   python -m unittest tests.test_edge_cases.TestErrorHandling -v
   ```

7. **Unit Tests - Edge Cases**
   ```bash
   python -m unittest tests.test_edge_cases.TestEdgeCases -v
   ```

8. **Integration Tests**
   ```bash
   python -m unittest tests.test_parser.TestParserIntegration -v
   ```

9. **Performance Tests**
   ```bash
   python -m unittest tests.test_performance -v
   ```

10. **Full Suite**
    ```bash
    python -m unittest discover tests -v
    ```

11. **Coverage Analysis**
    ```bash
    coverage run -m unittest discover tests
    coverage report
    coverage html
    open htmlcov/index.html
    ```

#### Acceptance Criteria

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Line coverage ≥ 95%
- [ ] Branch coverage ≥ 90%
- [ ] No critical performance issues
- [ ] Examples run without errors

**Deliverables**:
- [ ] All tests passing
- [ ] Coverage report showing ≥95%
- [ ] Performance benchmarks documented

---

## Corrections to Initial Design

After reviewing both documents, the following corrections should be made:

### Correction 1: Overview Statement

**File**: `docs/initial-design.md`, line 5

**Current**:
> handles 2-4 word commands

**Should be**:
> handles 1-6 word commands

**Reason**: The design actually supports 1-6 word commands (direction alone, plus up to 6-word commands with adjectives).

### Correction 2: Preposition/Article Consistency

**Files**: `docs/initial-design.md` and `tests/test-plan.md`

**Issue**: The JSON format for prepositions and articles is inconsistent. Sometimes they're simple strings, sometimes objects.

**Recommendation**: Support both formats in the loader (already shown in implementation above).

### Correction 3: Missing Nouns Field

**File**: `tests/test-plan.md`, fixture examples

**Issue**: Some test fixtures should include `synonyms` field for nouns for completeness.

**Recommendation**: Add `"synonyms": []` to noun entries for consistency.

---

## Risk Mitigation

### Known Risks

1. **Pattern Matching Ambiguity**
   - Risk: Multiple patterns might match same input
   - Mitigation: Order patterns from most specific to least specific
   - Status: Design already handles this with if-elif chains

2. **Performance with Large Vocabularies**
   - Risk: Linear search slow for 1000+ words
   - Mitigation: Implement hash table optimization in Phase 3.2
   - Status: Optional optimization documented

3. **Unicode and Special Characters**
   - Risk: Non-ASCII input may cause issues
   - Mitigation: Use UTF-8 encoding, test with edge cases
   - Status: Test EC-011 covers this

4. **Empty Input Handling**
   - Risk: Empty strings or whitespace-only input
   - Mitigation: Check for empty token list before processing
   - Status: Tests EH-003, EH-004 cover this

---

## Success Metrics

- [ ] All 100+ test cases passing
- [ ] Code coverage ≥ 95%
- [ ] Parse time < 1ms per command
- [ ] Vocabulary load time < 500ms for 1000 words
- [ ] Zero memory leaks
- [ ] Examples run successfully
- [ ] Documentation complete and accurate

---

## Timeline Summary

| Phase | Days | Description |
|-------|------|-------------|
| 0 | 1 | Project setup |
| 1 | 1-2 | Data structures |
| 2 | 2-3 | Vocabulary loading |
| 3 | 3 | Word lookup |
| 4 | 4-6 | Pattern matching |
| 5 | 6-7 | Main parser logic |
| 6 | 7 | Production vocabulary |
| 7 | 8 | Examples and docs |
| 8 | 9-10 | Testing and validation |

**Total**: 10 days (assumes 4-6 hours per day of focused development)

---

## Next Steps

1. Review and approve this implementation plan
2. Apply corrections to initial-design.md
3. Begin Phase 0: Project Setup
4. Follow phases sequentially
5. Run tests after each phase
6. Document any deviations or issues

---

## Appendix: Command Reference

### Common Commands for Development

```bash
# Run specific test
python -m unittest tests.test_parser.TestBasicParsing.test_verb_noun

# Run test file
python -m unittest tests.test_parser -v

# Run all tests
python -m unittest discover tests -v

# Coverage
coverage run -m unittest discover tests
coverage report --show-missing
coverage html

# Interactive testing
python examples/interactive_parser.py

# Run example game
python examples/simple_game.py
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/parser-implementation

# Commit after each phase
git add .
git commit -m "Phase X: <description>"

# Push to remote
git push origin feature/parser-implementation
```
