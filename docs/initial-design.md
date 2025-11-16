# Text Adventure Game Parser - Initial Design

## Overview

This document describes the design for a simple, configurable parser for a text adventure game that handles 2-4 word commands. The parser is table-driven, allowing for easy configuration and extension of recognized vocabulary.

## Core Components

### 1. Word Table (Dictionary)

The word table is the central configuration mechanism that defines all recognized vocabulary. Each entry maps a word to its grammatical type and optional metadata.

#### Word Types

- **VERB**: Action words (e.g., "take", "drop", "examine", "go")
- **NOUN**: Objects and entities (e.g., "sword", "door", "key")
- **PREPOSITION**: Relational words (e.g., "with", "to", "in", "on")
- **DIRECTION**: Movement directions (e.g., "north", "south", "east", "west")
- **ARTICLE**: Ignored words (e.g., "the", "a", "an")

#### Word Table Structure

```typescript
interface WordEntry {
  word: string;           // The actual word
  type: WordType;         // Grammatical type
  synonyms?: string[];    // Alternative words with same meaning
  value?: number;         // Optional numeric ID for game logic
}
```

#### Example Configuration

```typescript
const wordTable: WordEntry[] = [
  // Verbs
  { word: "take", type: "VERB", synonyms: ["get", "grab", "pick"], value: 1 },
  { word: "drop", type: "VERB", synonyms: ["put", "place"], value: 2 },
  { word: "examine", type: "VERB", synonyms: ["look", "inspect", "x"], value: 3 },
  { word: "go", type: "VERB", value: 4 },
  { word: "open", type: "VERB", value: 5 },
  { word: "unlock", type: "VERB", value: 6 },

  // Nouns
  { word: "door", type: "NOUN", value: 101 },
  { word: "key", type: "NOUN", value: 102 },
  { word: "sword", type: "NOUN", value: 103 },
  { word: "chest", type: "NOUN", value: 104 },

  // Prepositions
  { word: "with", type: "PREPOSITION" },
  { word: "to", type: "PREPOSITION" },
  { word: "in", type: "PREPOSITION" },
  { word: "on", type: "PREPOSITION" },

  // Directions
  { word: "north", type: "DIRECTION", synonyms: ["n"], value: 1 },
  { word: "south", type: "DIRECTION", synonyms: ["s"], value: 2 },
  { word: "east", type: "DIRECTION", synonyms: ["e"], value: 3 },
  { word: "west", type: "DIRECTION", synonyms: ["w"], value: 4 },

  // Articles (filtered out)
  { word: "the", type: "ARTICLE" },
  { word: "a", type: "ARTICLE" },
  { word: "an", type: "ARTICLE" }
];
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

```typescript
interface ParsedCommand {
  verb: WordEntry;              // The action verb
  directObject?: WordEntry;     // Primary noun (what)
  preposition?: WordEntry;      // Relational word (how/where)
  indirectObject?: WordEntry;   // Secondary noun (with what)
  direction?: WordEntry;        // Movement direction
  raw: string;                  // Original input
}
```

#### Supported Command Patterns

The parser recognizes these patterns:

1. **Two Words**
   - `VERB + NOUN` → "take sword", "examine door"
   - `VERB + DIRECTION` → "go north", "walk east"
   - `DIRECTION` (alone) → "north", "south"

2. **Three Words**
   - `VERB + NOUN + NOUN` → "unlock door key" (implicit "with")
   - `VERB + PREPOSITION + NOUN` → "look in chest"
   - `VERB + NOUN + PREPOSITION` → "go door to"

3. **Four Words**
   - `VERB + NOUN + PREPOSITION + NOUN` → "unlock door with key"
   - `VERB + PREPOSITION + NOUN + NOUN` → "put sword in chest"

#### Error Handling

The parser should provide clear error messages:

- **Unknown word**: "I don't understand the word 'xyz'"
- **Invalid pattern**: "I don't understand that command"
- **Ambiguous command**: "What do you want to [verb]?"
- **Missing object**: "What do you want to [verb] it with?"

### 3. Parser Algorithm

```
function parseCommand(input: string): ParsedCommand | Error {
  // 1. Tokenize
  tokens = input.toLowerCase().split(/\s+/)

  // 2. Look up each word
  wordEntries = []
  for each token in tokens:
    entry = lookupWord(token)  // Checks word and synonyms
    if entry is null:
      return Error("Unknown word: " + token)
    wordEntries.push(entry)

  // 3. Filter articles
  filteredEntries = wordEntries.filter(e => e.type != ARTICLE)

  // 4. Match pattern and build command
  command = matchPattern(filteredEntries)
  if command is null:
    return Error("Invalid command pattern")

  command.raw = input
  return command
}

function lookupWord(word: string): WordEntry | null {
  for entry in wordTable:
    if entry.word == word:
      return entry
    if word in entry.synonyms:
      return entry
  return null
}

function matchPattern(entries: WordEntry[]): ParsedCommand | null {
  length = entries.length

  if length == 1:
    // Single direction
    if entries[0].type == DIRECTION:
      return { direction: entries[0] }

  if length == 2:
    // VERB + NOUN or VERB + DIRECTION
    if entries[0].type == VERB and entries[1].type == NOUN:
      return { verb: entries[0], directObject: entries[1] }
    if entries[0].type == VERB and entries[1].type == DIRECTION:
      return { verb: entries[0], direction: entries[1] }

  if length == 3:
    // VERB + NOUN + NOUN (implicit preposition)
    if all entries are [VERB, NOUN, NOUN]:
      return { verb: entries[0], directObject: entries[1], indirectObject: entries[2] }

    // VERB + PREPOSITION + NOUN
    if all entries are [VERB, PREPOSITION, NOUN]:
      return { verb: entries[0], preposition: entries[1], directObject: entries[2] }

    // VERB + NOUN + PREPOSITION
    if all entries are [VERB, NOUN, PREPOSITION]:
      return { verb: entries[0], directObject: entries[1], preposition: entries[2] }

  if length == 4:
    // VERB + NOUN + PREPOSITION + NOUN
    if all entries are [VERB, NOUN, PREPOSITION, NOUN]:
      return {
        verb: entries[0],
        directObject: entries[1],
        preposition: entries[2],
        indirectObject: entries[3]
      }

    // VERB + PREPOSITION + NOUN + NOUN
    if all entries are [VERB, PREPOSITION, NOUN, NOUN]:
      return {
        verb: entries[0],
        preposition: entries[1],
        directObject: entries[2],
        indirectObject: entries[3]
      }

  return null
}
```

## Configuration and Extensibility

### Adding New Words

To add vocabulary, simply append entries to the word table:

```typescript
wordTable.push(
  { word: "climb", type: "VERB", value: 7 },
  { word: "ladder", type: "NOUN", value: 105 }
);
```

### Adding New Command Patterns

To support additional patterns, extend the `matchPattern` function with new conditional branches.

### External Configuration

For easy modification, the word table can be stored in:

- **JSON file**: Easy to edit, loaded at startup
- **Database**: For persistent, dynamic vocabulary
- **YAML/TOML**: Human-readable configuration format

Example JSON structure:

```json
{
  "verbs": [
    { "word": "take", "synonyms": ["get", "grab"], "value": 1 }
  ],
  "nouns": [
    { "word": "sword", "value": 103 }
  ],
  "prepositions": ["with", "to", "in"],
  "directions": [
    { "word": "north", "synonyms": ["n"], "value": 1 }
  ]
}
```

## Usage Example

```typescript
const parser = new Parser(wordTable);

// Parse simple command
const cmd1 = parser.parse("take sword");
// Result: { verb: "take", directObject: "sword" }

// Parse with articles (filtered)
const cmd2 = parser.parse("take the sword");
// Result: { verb: "take", directObject: "sword" }

// Parse complex command
const cmd3 = parser.parse("unlock door with key");
// Result: {
//   verb: "unlock",
//   directObject: "door",
//   preposition: "with",
//   indirectObject: "key"
// }

// Parse with synonym
const cmd4 = parser.parse("grab the sword");
// Result: { verb: "take", directObject: "sword" }

// Parse direction
const cmd5 = parser.parse("north");
// Result: { direction: "north" }
```

## Advantages of This Design

1. **Configurable**: All vocabulary is defined in a single, editable table
2. **Extensible**: Easy to add new words without changing parser code
3. **Synonym Support**: Multiple words can map to the same action/object
4. **Clear Structure**: Parsed commands have well-defined components
5. **Error Messages**: Provides helpful feedback for invalid input
6. **Simple Implementation**: Straightforward algorithm, easy to debug
7. **Flexible Patterns**: Handles 2-4 word commands naturally

## Future Enhancements

- **Adjective Support**: "take red key" vs "take blue key"
- **Adverb Support**: "open door carefully"
- **Pronoun Resolution**: "examine it", "take them"
- **Partial Matching**: "n" for "north", "exam" for "examine"
- **Context-Aware Parsing**: Use game state to disambiguate commands
- **Multi-sentence Input**: Handle multiple commands separated by periods/commas
