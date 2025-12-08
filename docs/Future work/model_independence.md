# Model Independence for LLM Game

## Overview

This document captures the analysis and design for making the LLM-powered text adventure game model-agnostic, allowing it to work with different LLM providers beyond Claude/Anthropic.

## Current State

### Architecture

The system has a clean separation between the game engine and LLM integration:

- **Game Engine** ([llm_protocol.py](../src/llm_protocol.py)) - Processes JSON commands/queries, manages game state, completely LLM-agnostic
- **LLM Integration** - Two modules that currently depend on Claude:
  1. **[llm_game.py](../src/llm_game.py)** - Entry point/CLI wrapper with minimal Claude dependency
  2. **[llm_narrator.py](../src/llm_narrator.py)** - Core LLM integration with heavy Claude dependency

The game engine communicates via a well-defined JSON protocol, which is already model-agnostic. All LLM-specific code is isolated to the two LLM integration modules.

### Claude-Specific Dependencies

#### In llm_game.py (minimal)
- **Lines 44-48**: Environment variable `ANTHROPIC_API_KEY`
- Easy to generalize to provider-specific or generic API key handling

#### In llm_narrator.py (substantial)
- **Line 18**: `import anthropic` with availability check
- **Line 94**: `self.client = anthropic.Anthropic(api_key=api_key)` - client initialization
- **Lines 376-401**: `_call_llm()` method with Claude-specific features:
  - `client.messages.create()` API call format
  - `system` parameter with `cache_control` (Claude's prompt caching feature)
  - Response format: `response.content[0].text`
  - Error types: `anthropic.RateLimitError`, `anthropic.APIError`
  - Usage tracking: `cache_read_input_tokens`, `cache_creation_input_tokens`
  - Retry logic for rate limits

### Provider-Specific Features

Different LLM providers have varying capabilities:

**Claude (Anthropic)**:
- Prompt caching via `cache_control` (reduces cost/latency for repeated system prompts)
- Specific message format with system/user separation
- Token usage tracking with cache statistics

**OpenAI (GPT-4, etc.)**:
- Different API format (`ChatCompletion.create()`)
- No prompt caching (as of current knowledge)
- Different token limit patterns
- Different error types

**Other Providers** (Gemini, local models via Ollama, etc.):
- Varying API formats
- Different feature sets
- Different performance characteristics

## Requirements for Model Independence

### Goals

1. **Support multiple LLM providers** with minimal code changes when adding new providers
2. **Preserve provider-specific optimizations** (e.g., prompt caching) where available
3. **Graceful feature degradation** when features aren't available (e.g., no caching)
4. **Configuration-driven** provider selection without code changes
5. **Maintain current functionality** - existing Claude integration should continue to work

### Non-Goals

- Supporting all possible LLM providers immediately (start with Claude + OpenAI)
- Abstracting away all provider differences (some differences are acceptable)
- Backwards compatibility for saved game files (out of scope per project guidelines)

## Required Changes

### 1. Abstract LLM Client Interface

Create a base class or protocol defining the LLM client interface:
- `generate(prompt, system_prompt) -> str` - Core generation method
- `get_model_name() -> str` - Model identifier
- Provider-specific initialization

### 2. Provider Adapters

Implement concrete adapters for each provider:
- **ClaudeAdapter** - Wraps anthropic client, supports prompt caching
- **OpenAIAdapter** - Wraps openai client
- Additional adapters as needed

Each adapter handles:
- API client initialization
- Request formatting
- Response parsing
- Error handling and retry logic
- Provider-specific optimizations

### 3. Configuration

Determine provider/model via:
- Environment variables (e.g., `LLM_PROVIDER`, `LLM_MODEL`, provider-specific API keys)
- Configuration file (optional, for more complex setups)
- Command-line arguments (optional override)

### 4. Feature Handling

**Prompt Caching** (Claude-specific):
- Enable when available
- Fall back to regular prompts when not available
- Log when optimizations are used vs. unavailable

**Token Limits**:
- Provider-specific max_tokens configuration
- May need per-provider tuning

**Rate Limiting**:
- Provider-specific retry strategies
- Configurable backoff

### 5. Modified Files

Primary changes in:
- **[llm_narrator.py](../src/llm_narrator.py)** - Refactor to use adapter pattern
  - Replace direct `anthropic.Anthropic` usage with adapter
  - Refactor `_call_llm()` to delegate to adapter
  - Update initialization to accept/create appropriate adapter
- **[llm_game.py](../src/llm_game.py)** - Update API key handling
  - Support multiple provider API keys
  - Instantiate appropriate adapter based on config

New files:
- `src/llm_adapters/` - Directory for adapter implementations
  - `base.py` - Base adapter interface
  - `claude.py` - Claude/Anthropic adapter
  - `openai.py` - OpenAI adapter
  - `__init__.py` - Factory function for creating adapters

## Scope

This is a refactoring task localized to the LLM integration modules. **No changes required** to:
- Game engine ([llm_protocol.py](../src/llm_protocol.py))
- State management
- Behavior system
- Parser
- Any game-specific code

The JSON protocol already provides clean separation between game logic and LLM narration.

## Open Questions

(To be addressed during detailed design)

1. **Configuration approach** - Environment variables only, or add config file?
2. **Adapter factory pattern** - Where should adapter selection logic live?
3. **Error handling strategy** - How much should we unify vs. expose provider-specific errors?
4. **Testing strategy** - Mock adapters? Real API integration tests?
5. **Model selection** - Hard-coded per provider or user-configurable?
6. **Streaming support** - Should adapters support streaming responses for future use?
7. **Logging/debugging** - How to expose provider-specific diagnostics (cache hits, token usage)?

## Implementation Phases

(To be detailed during implementation planning)

## Progress

(To be updated as implementation proceeds)

## Issues Encountered

(To be documented during implementation)

## Work Deferred

(To be tracked during implementation)
