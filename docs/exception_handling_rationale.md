# Exception Handling Rationale

This document explains the policy for exception handling in the text-game engine and provides rationale for all remaining try/except blocks in the codebase.

## Policy

**Core Principle**: Any coding or authoring errors should fail loudly, so that anyone writing games will know during their testing that there's a problem they should fix. We should only attempt to quietly handle errors that a developer/author can't reasonably prevent during development/authoring.

**What to Handle**:
- External service failures (API errors, network issues)
- External library failures (GUI toolkit issues, missing optional dependencies)
- Runtime I/O errors (disk full, permissions, corrupted files)
- External input errors (invalid JSON from LLM, invalid user input)
- User actions (Ctrl+C interrupts)

**What NOT to Handle**:
- Missing files or modules (authoring error)
- Invalid configuration (authoring error)
- Invalid JSON in game files (authoring error)
- Bugs in behavior code (coding error)
- Bugs in engine code (coding error)
- Invalid data structures (coding error)

## Remaining Try/Except Blocks

### External Library Availability

**file_dialogs.py:19, :60** - wxPython GUI dialogs
```python
try:
    app = wx.App(False)
    # ... dialog operations ...
except Exception as e:
    print(f"Error opening file dialog: {e}")
    return None
```
**Rationale**: wxPython depends on display server availability, window manager behavior, and other system components outside developer control. Failures here are external library issues, not authoring errors.

**llm_narrator.py:20** - Optional Anthropic library import
```python
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
```
**Rationale**: This is an optional dependency pattern. The flag is checked later and a clear error is raised if used without being installed. This allows the code to import without requiring the dependency.

**mlx_narrator.py:20** - Optional MLX library import
```python
try:
    from mlx_lm import load, generate, stream_generate
    # ... more imports ...
    HAS_MLX = True
except ImportError:
    HAS_MLX = False
```
**Rationale**: Same as anthropic - optional dependency pattern for platform-specific library (macOS Apple Silicon only).

### External Service Failures

**llm_narrator.py:247** - Anthropic API calls
```python
try:
    response = self.client.messages.create(...)
    # ... process response ...
except anthropic.RateLimitError:
    time.sleep(1)
    return self._call_llm(user_message)  # Retry
except anthropic.APIError as e:
    return f"[Narrator unavailable: {e}]"
```
**Rationale**: Network failures, API rate limits, and service outages are external to the developer's control. These are runtime issues with external services, not authoring errors.

### External Input Parsing

**llm_narrator.py:291, :297** - Parse JSON from LLM response
```python
try:
    return json.loads(match.group(1))
except json.JSONDecodeError:
    pass  # Try next parsing strategy
```
**Rationale**: The LLM is an external system that may produce malformed JSON despite prompting. This is not a developer error - it's inherent unreliability of external AI systems.

**mlx_narrator.py:376, :382** - Parse JSON from MLX response
```python
try:
    return json.loads(response.strip())
except json.JSONDecodeError:
    return None
```
**Rationale**: Same as llm_narrator - external AI system may produce invalid JSON.

**llm_protocol.py:94** - Parse JSON from external source
```python
try:
    message = json.loads(json_str)
    return self.handle_message(message)
except json.JSONDecodeError as e:
    return {"type": "error", ...}
```
**Rationale**: This handles JSON from the LLM, which is an external source. Invalid JSON from the LLM is not a developer error.

**text_game.py:143** - Parse user-provided JSON
```python
try:
    message = json.loads(command_text)
    result_json = engine.json_handler.handle_message(message)
except json.JSONDecodeError as e:
    print(f"Invalid JSON: {e}")
```
**Rationale**: User input can be malformed. This is a user error, not a developer/authoring error.

### Runtime I/O Errors

**text_game.py:83** - Save game state
```python
try:
    save_game_state(state, filename)
    print(f"Game saved to {filename}")
    return True
except Exception as e:
    print(f"Error saving game: {e}")
    return False
```
**Rationale**: File write operations can fail due to disk full, permissions, read-only filesystem, etc. These are runtime issues outside developer control.

**text_game.py:94** - Load game state
```python
try:
    state = load_game_state(filename)
    print(f"Game loaded from {filename}")
    return state
except Exception as e:
    print(f"Error loading game: {e}")
    return None
```
**Rationale**: File read can fail due to permissions, corrupted save files (user error), file deleted externally, etc. These are runtime issues outside developer control.

### User Actions

**llm_game.py:74, mlx_game.py:134** - Game loop keyboard interrupt
```python
while True:
    try:
        player_input = input("\n> ").strip()
        # ... game loop ...
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        break
```
**Rationale**: Ctrl+C is a normal user action to exit the game, not an error condition. This provides clean exit handling.

## Historical Context

The codebase originally had 32 try/except blocks in `src/`. Through systematic analysis, we removed 17 defensive blocks that were catching coding and authoring errors:

1. **6 defensive blocks masking bugs** (commit: f713fb0)
   - StateAccessor defensive re-raises
   - behavior_manager broad Exception catches
   - mlx_narrator broad Exception catch

2. **6 blocks catching authoring errors** (commit: 5f112ba)
   - GameEngine initialization errors in entry points
   - create_narrator/create_mlx_narrator errors
   - get_opening() errors
   - Main game loop process_turn() errors

3. **5 blocks catching config/parser bugs** (commit: d65f6b5)
   - behavior_manager path validation and imports
   - game_engine JSON parsing
   - parser quoted string placeholder parsing

The remaining 15 blocks handle only truly external failures that developers cannot prevent during development and testing.

## Maintenance Guidelines

When adding new code:

1. **Default to no try/except** - Let errors propagate naturally
2. **Only catch external failures** - Use this document as a reference for what qualifies
3. **Document the rationale** - Add a comment explaining why the exception is caught
4. **Be specific** - Catch specific exceptions (ValueError, ImportError) not broad Exception
5. **Update this document** - If adding a new category of exception handling, explain it here

When encountering errors during development:

1. **Don't add try/except to hide errors** - Fix the root cause instead
2. **Stack traces are your friend** - They show exactly where the problem is
3. **Fail loudly during development** - Silent failures hide bugs
4. **Test without exception handling** - Ensures authors discover issues during testing
