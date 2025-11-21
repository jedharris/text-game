"""Interactive parser testing tool with JSON protocol support."""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.parser import Parser
from src.parsed_command import ParsedCommand
from src.state_manager import load_game_state
from src.json_protocol import JSONProtocolHandler


def format_command(cmd: ParsedCommand) -> str:
    """Format a ParsedCommand for display."""
    parts = []
    if cmd.verb:
        parts.append(f"verb={cmd.verb.word}({cmd.verb.value})")
    if cmd.direct_adjective:
        parts.append(f"direct_adj={cmd.direct_adjective.word}({cmd.direct_adjective.value})")
    if cmd.direct_object:
        parts.append(f"direct_obj={cmd.direct_object.word}({cmd.direct_object.value})")
    if cmd.preposition:
        parts.append(f"prep={cmd.preposition.word}")
    if cmd.indirect_adjective:
        parts.append(f"indirect_adj={cmd.indirect_adjective.word}({cmd.indirect_adjective.value})")
    if cmd.indirect_object:
        parts.append(f"indirect_obj={cmd.indirect_object.word}({cmd.indirect_object.value})")
    if cmd.direction:
        parts.append(f"direction={cmd.direction.word}({cmd.direction.value})")

    return "ParsedCommand(" + ", ".join(parts) + ")"


def print_word_types(parser: Parser):
    """Print vocabulary statistics by word type."""
    from collections import defaultdict
    from src.word_entry import WordType

    type_counts = defaultdict(int)
    synonym_counts = defaultdict(int)

    for entry in parser.word_table:
        type_counts[entry.word_type] += 1
        synonym_counts[entry.word_type] += len(entry.synonyms)

    print("\nVocabulary Statistics:")
    print("-" * 40)
    for word_type in WordType:
        count = type_counts[word_type]
        synonyms = synonym_counts[word_type]
        print(f"{word_type.value:12} : {count:3} words, {synonyms:3} synonyms")
    print("-" * 40)
    total_words = sum(type_counts.values())
    total_synonyms = sum(synonym_counts.values())
    print(f"{'TOTAL':12} : {total_words:3} words, {total_synonyms:3} synonyms")
    print(f"{'Lookup table':12} : {len(parser.word_lookup):3} entries")
    print()


def main():
    parser = Parser('data/vocabulary.json')

    # Load game state for JSON protocol testing
    script_dir = Path(__file__).parent
    state_file = script_dir / "simple_game_state.json"
    state = load_game_state(str(state_file))
    json_handler = JSONProtocolHandler(state)

    print("=" * 60)
    print("Interactive Parser Testing Tool")
    print("=" * 60)
    print("\nCommands:")
    print("  <command>  - Parse a text command")
    print("  {json}     - Process JSON protocol message")
    print("  stats      - Show vocabulary statistics")
    print("  help       - Show this help message")
    print("  quit       - Exit the tool")
    print()

    # Show initial stats
    print_word_types(parser)

    while True:
        try:
            command_text = input("\n> ").strip()

            if not command_text:
                continue

            if command_text.lower() == 'quit':
                print("Goodbye!")
                break

            if command_text.lower() == 'stats':
                print_word_types(parser)
                continue

            if command_text.lower() == 'help':
                print("\nCommands:")
                print("  <command>  - Parse a text command (e.g., 'take sword')")
                print("  {json}     - Process JSON protocol message")
                print("  stats      - Show vocabulary statistics")
                print("  help       - Show this help message")
                print("  quit       - Exit the tool")
                continue

            # Check if input is JSON (per spec: starts with '{')
            if command_text.startswith("{"):
                try:
                    message = json.loads(command_text)
                    result_json = json_handler.handle_message(message)
                    print("\nJSON Response:")
                    print(json.dumps(result_json, indent=2))
                except json.JSONDecodeError as e:
                    print(f"\nJSON ERROR: {e}")
                continue

            # Parse the text command
            result = parser.parse_command(command_text)

            if result is None:
                print("ERROR: Failed to parse (returned None)")
            else:
                print("\nParsed successfully:")
                print(format_command(result))
                print(f"Raw: '{result.raw}'")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nERROR: {e}")


if __name__ == '__main__':
    main()
