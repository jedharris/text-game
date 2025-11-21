# LLM Front End Infrastructure

This document describes the minimal infrastructure needed to connect an LLM to the text game engine, enabling natural language interaction with narrative response generation.

## Architecture Overview

```
┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Player │ ──► │ LLM Narrator│ ──► │ JSON Protocol│ ──► │ Game Engine │
│  Input  │     │             │     │   Handler    │     │   (State)   │
└─────────┘     └─────────────┘     └──────────────┘     └─────────────┘
     ▲                 │                                        │
     │                 │                                        │
     │                 ▼                                        │
     │          ┌─────────────┐     ┌──────────────┐            │
     └───────── │  Narrative  │ ◄── │ JSON Result  │ ◄──────────┘
               │   Output    │     │  + Context   │
               └─────────────┘     └──────────────┘
```

## Design Philosophy

The game engine already provides:
- Complete state management
- Command processing and validation
- Coherent responses via JSON protocol
- Rich context via `llm_context` fields

The LLM front end only needs to:
1. **Translate** natural language → JSON command
2. **Narrate** JSON result → prose

This is a thin layer, not a complex orchestration system.

## Components

### 1. LLM Narrator Module

**File:** `src/llm_narrator.py`

A single module that wraps LLM API calls and processes game turns.

```python
import json
import anthropic
from src.json_protocol import JSONProtocolHandler

class LLMNarrator:
    """Translates between natural language and the JSON protocol."""

    def __init__(self, api_key: str, json_handler: JSONProtocolHandler,
                 model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.handler = json_handler
        self.model = model
        self.system_prompt = self._build_system_prompt()

    def process_turn(self, player_input: str) -> str:
        """Process one turn: input -> command -> result -> narrative."""
        # 1. Get JSON command from LLM
        command_response = self._call_llm(
            f"Player says: {player_input}\n\nRespond with a JSON command."
        )
        json_cmd = self._extract_json(command_response)

        if json_cmd is None:
            return "I don't understand what you want to do."

        # 2. Execute command via game engine
        result = self.handler.handle_message(json_cmd)

        # 3. Get narrative from LLM
        narrative = self._call_llm(
            f"Narrate this result:\n{json.dumps(result, indent=2)}"
        )

        return narrative

    def get_opening(self) -> str:
        """Get opening narrative for game start."""
        # Query current location
        result = self.handler.handle_message({
            "type": "query",
            "query_type": "location",
            "include": ["items", "doors", "npcs"]
        })

        return self._call_llm(
            f"Narrate the opening scene:\n{json.dumps(result, indent=2)}"
        )

    def _call_llm(self, user_message: str) -> str:
        """Make an API call to the LLM."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text

    def _extract_json(self, response: str) -> dict | None:
        """Extract JSON from LLM response."""
        # Look for JSON in code blocks
        import re
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try parsing the whole response
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            return None

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the narrator."""
        return """You are the narrator for an interactive text adventure game.

When asked to generate a command, respond with ONLY a JSON block:
```json
{"type": "command", "action": {"verb": "take", "object": "sword"}}
```

Available verbs: take, drop, examine, go, open, close, unlock, lock, look, inventory
For movement: {"type": "command", "action": {"verb": "go", "direction": "north"}}

When asked to narrate a result, use the llm_context to create 2-4 sentences of
atmospheric prose. Use traits for physical details and state_variants for
context-specific phrasing.

Keep the tone consistent with a classic text adventure - evocative but concise."""
```

### 2. Main Entry Point

**File:** `examples/llm_game.py`

```python
#!/usr/bin/env python3
"""LLM-powered text adventure game."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.state_manager import load_game_state
from src.json_protocol import JSONProtocolHandler
from src.llm_narrator import LLMNarrator

def main():
    # Load API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        return

    # Load game state and create handler
    script_dir = Path(__file__).parent
    state_file = script_dir / "simple_game_state.json"
    state = load_game_state(str(state_file))
    json_handler = JSONProtocolHandler(state)

    # Create narrator
    narrator = LLMNarrator(api_key, json_handler)

    # Show opening
    print(f"\n{state.metadata.title}")
    print("=" * len(state.metadata.title))
    print(narrator.get_opening())

    # Game loop
    while True:
        try:
            player_input = input("\n> ").strip()
            if not player_input:
                continue
            if player_input.lower() == "quit":
                print("\nThanks for playing!")
                break

            response = narrator.process_turn(player_input)
            print(f"\n{response}")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break

if __name__ == "__main__":
    main()
```

## Message Flow

### Turn Sequence

1. **Player Input:** "I want to pick up that rusty sword"

2. **LLM generates command:**
   ```json
   {"type": "command", "action": {"verb": "take", "object": "sword"}}
   ```

3. **Engine executes and returns result:**
   ```json
   {
     "type": "result",
     "success": true,
     "action": "take",
     "entity": {
       "id": "item_sword",
       "name": "sword",
       "llm_context": {
         "traits": ["pitted blade", "leather-wrapped hilt", "still holds an edge"],
         "state_variants": {"in_inventory": "a reassuring weight at your side"}
       }
     }
   }
   ```

4. **LLM narrates:**
   ```
   You reach down and grasp the sword's leather-wrapped hilt. Despite the
   pitted blade showing years of neglect, it still holds an edge—a reassuring
   weight at your side as you consider your next move.
   ```

## Configuration

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional (set in code or add argument parsing)
LLM_MODEL=claude-sonnet-4-20250514
```

### Game Metadata for LLM

The game state can include metadata to guide narrative tone:

```json
{
  "metadata": {
    "title": "The Forgotten Dungeon",
    "author": "Game Author",
    "version": "1.0",
    "description": "A dark fantasy adventure",
    "narrative_style": "atmospheric, slightly foreboding",
    "tone": "serious with moments of dark humor"
  }
}
```

The system prompt can be extended to reference this metadata if desired.

## Error Handling

### LLM Errors

Handle in `_call_llm`:
- **Rate limits:** Retry with exponential backoff
- **API errors:** Return a fallback message

```python
def _call_llm(self, user_message: str) -> str:
    try:
        response = self.client.messages.create(...)
        return response.content[0].text
    except anthropic.RateLimitError:
        time.sleep(1)
        return self._call_llm(user_message)  # Simple retry
    except anthropic.APIError as e:
        return f"[Narrator unavailable: {e}]"
```

### Invalid JSON from LLM

If `_extract_json` returns `None`, the narrator returns a generic "I don't understand" message. The game state remains unchanged.

### Game Engine Errors

When the engine returns `success: false`, the LLM narrates the failure naturally:

```json
{
  "type": "result",
  "success": false,
  "action": "take",
  "error": {"message": "You don't see that here."}
}
```

Becomes:
```
You look around but don't see any diamond here. Perhaps you're thinking
of somewhere else?
```

## Testing

### Unit Tests

```python
# tests/test_llm_narrator.py

class TestLLMNarrator:
    def test_extract_json_from_code_block(self):
        """Test extracting JSON from markdown code block."""
        narrator = LLMNarrator("fake-key", mock_handler)
        response = '```json\n{"type": "command"}\n```'
        result = narrator._extract_json(response)
        assert result == {"type": "command"}

    def test_extract_json_plain(self):
        """Test extracting plain JSON response."""
        narrator = LLMNarrator("fake-key", mock_handler)
        response = '{"type": "command"}'
        result = narrator._extract_json(response)
        assert result == {"type": "command"}

    def test_extract_json_invalid(self):
        """Test handling invalid JSON."""
        narrator = LLMNarrator("fake-key", mock_handler)
        result = narrator._extract_json("not json at all")
        assert result is None
```

### Mock LLM for Testing

```python
class MockLLMNarrator(LLMNarrator):
    """Narrator with mocked LLM responses for testing."""

    def __init__(self, json_handler: JSONProtocolHandler, responses: list):
        self.handler = json_handler
        self.responses = responses
        self.call_count = 0
        self.system_prompt = ""  # Not used in mock

    def _call_llm(self, user_message: str) -> str:
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return response
```

## Dependencies

Add to `requirements.txt`:

```
anthropic>=0.18.0
```

## Implementation Checklist

- [ ] Create `src/llm_narrator.py` with `LLMNarrator` class
- [ ] Create `examples/llm_game.py` entry point
- [ ] Add basic error handling (rate limits, API errors)
- [ ] Write unit tests for JSON extraction
- [ ] Test with actual LLM API
- [ ] Tune system prompt for better narratives

## Future Enhancements

These are optional improvements, not required for a working system:

- **Streaming output:** Stream narrative text as it generates
- **Conversation history:** Remember recent turns for continuity (most games don't need this since the engine tracks state)
- **Multiple LLM providers:** Support OpenAI or local models
- **Voice interface:** Speech-to-text and text-to-speech
- **Web interface:** Browser-based client
