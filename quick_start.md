# Quick Start

This guide assumes you have cloned the repository and have Python 3.6+ installed.

## text_game (Parser-based)

The text game uses a command parser to interpret structured commands like `take sword` or `go north`.

```bash
cd text-game
python3 src/text_game.py
```

**Commands:**
- Movement: `go north`, `north`, `n`
- Actions: `take key`, `examine door`, `open chest`
- Special: `look`, `inventory`, `save`, `load`, `quit`

## llm_game (Natural Language)

The LLM game uses Claude to interpret natural language input and narrate results.

**Setup:**
```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

**Run:**
```bash
cd text-game
python3 src/llm_game.py
```

You can type naturally: "pick up the rusty sword", "what's in this room?", "try opening the wooden door".

## Game State

Both games load their initial state from `examples/simple_game_state.json`. Edit this file to create your own adventures.
