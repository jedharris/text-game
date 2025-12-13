# MLX-LM API Reference for Game Narrator Integration

## Overview
MLX-LM is Apple's native framework for running LLMs on Apple Silicon. It offers explicit prompt caching and is optimized for Metal GPU acceleration.

## Installation
```bash
pip install mlx-lm
```

Requires macOS 13.5+ and Apple Silicon (M1/M2/M3/M4).

## Recommended Models

| Model | Size | Speed | Notes |
|-------|------|-------|-------|
| `mlx-community/Llama-3.2-1B-Instruct-4bit` | ~0.8GB | Fastest | Minimal, may be sufficient |
| `mlx-community/Llama-3.2-3B-Instruct-4bit` | ~1.5GB | Very fast | Good balance (default) |
| `mlx-community/Mistral-7B-Instruct-v0.3-4bit` | ~4GB | Fast | Strong narrative quality |
| `mlx-community/Qwen2.5-7B-Instruct-4bit` | ~4GB | Fast | Good instruction following |

With 128GB RAM, you can also use 8-bit versions for better quality.

## Quick Test (CLI)
```bash
# Interactive chat
mlx_lm.chat --model mlx-community/Llama-3.2-3B-Instruct-4bit

# Single generation
mlx_lm.generate --model mlx-community/Llama-3.2-3B-Instruct-4bit \
  --prompt "You enter a dark dungeon. Describe what you see."
```

---

## Python API

### Basic Generation

```python
from mlx_lm import load, generate

# Load model (downloads automatically on first use)
model, tokenizer = load("mlx-community/Mistral-7B-Instruct-v0.3-4bit")

# Simple generation
response = generate(
    model, 
    tokenizer, 
    prompt="You enter a dark dungeon. Describe what you see.",
    max_tokens=100,
    temp=0.8,
    verbose=False
)
print(response)
```

### With Chat Template (Recommended for Instruct Models)

```python
from mlx_lm import load, generate

model, tokenizer = load("mlx-community/Mistral-7B-Instruct-v0.3-4bit")

messages = [
    {"role": "system", "content": "You are a fantasy game narrator. Be vivid but brief."},
    {"role": "user", "content": "Player opens the chest."}
]

# Apply chat template
prompt = tokenizer.apply_chat_template(
    messages, 
    add_generation_prompt=True,
    tokenize=False
)

response = generate(model, tokenizer, prompt=prompt, max_tokens=100)
print(response)
```

### Streaming Generation

```python
from mlx_lm import load, stream_generate

model, tokenizer = load("mlx-community/Mistral-7B-Instruct-v0.3-4bit")

prompt = "Describe the ancient temple entrance."

for response in stream_generate(model, tokenizer, prompt=prompt, max_tokens=100):
    print(response.text, end="", flush=True)
print()
```

---

## Prompt Caching (Explicit, Persistent)

MLX-LM supports saving the KV cache to disk for reuse across sessions. This is ideal for your fixed narrator system prompt.

### Cache the System Prompt (CLI)

```bash
# Create cache file from your narrator prompt
echo "You are the narrator of a fantasy adventure game. 
The player is a brave adventurer exploring ancient ruins.
Current location: The Crystal Caverns
Inventory: torch, rope, dagger
Always respond in second person, present tense.
Keep responses to 2-3 sentences." | mlx_lm.cache_prompt \
  --model mlx-community/Mistral-7B-Instruct-v0.3-4bit \
  --prompt - \
  --prompt-cache-file narrator_cache.safetensors
```

### Use Cached Prompt (CLI)

```bash
# The cached prompt is automatically prefixed
mlx_lm.generate \
  --prompt-cache-file narrator_cache.safetensors \
  --prompt "\n\nPlayer action: open the wooden door\n\nNarrator:"
```

### Python API with Cache

```python
from mlx_lm import load, generate
from mlx_lm.utils import make_kv_caches, save_prompt_cache, load_prompt_cache
import mlx.core as mx

model, tokenizer = load("mlx-community/Mistral-7B-Instruct-v0.3-4bit")

# Your long, fixed narrator system prompt
system_prompt = """You are the narrator of a fantasy adventure game.
The player is a brave adventurer exploring ancient ruins.
Current location: The Crystal Caverns
Inventory: torch, rope, dagger
Always respond in second person, present tense.
Keep responses to 2-3 sentences."""

# First time: generate and save cache
tokens = tokenizer.encode(system_prompt)
prompt_tokens = mx.array([tokens])

# Create KV caches
cache = make_kv_caches(model, len(tokens))

# Process prompt to fill cache (this is the slow part, only done once)
# ... then save with save_prompt_cache()

# Subsequent runs: load the cached prompt
# cache = load_prompt_cache("narrator_cache.safetensors")
```

### Simpler: In-Memory Cache Reuse

For game integration where the server stays running, just keep the model and cache in memory:

```python
from mlx_lm import load, stream_generate

class NarratorEngine:
    def __init__(self, model_path="mlx-community/Mistral-7B-Instruct-v0.3-4bit"):
        self.model, self.tokenizer = load(model_path)
        self.cache = None  # Will hold KV cache
        
        # Your fixed system prompt
        self.system_prompt = """You are a fantasy game narrator.
Location: {location}
Inventory: {inventory}
Respond in 2-3 vivid sentences."""
    
    def narrate(self, player_action, game_state):
        prompt = self.system_prompt.format(
            location=game_state['location'],
            inventory=', '.join(game_state['inventory'])
        )
        prompt += f"\n\nPlayer action: {player_action}\n\nNarrator:"
        
        # Generate with cache reuse
        result = ""
        for response in stream_generate(
            self.model, 
            self.tokenizer, 
            prompt=prompt,
            max_tokens=100,
            temp=0.8
        ):
            result += response.text
        
        return result.strip()

# Usage
engine = NarratorEngine()
game_state = {"location": "Crystal Caverns", "inventory": ["torch", "dagger"]}

response = engine.narrate("examine the glowing crystals", game_state)
print(response)
```

---

## Generation Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_tokens` | 100 | Maximum tokens to generate |
| `temp` | 0.0 | Temperature (0.0-2.0, higher = more creative) |
| `top_p` | 1.0 | Nucleus sampling threshold |
| `repetition_penalty` | None | Penalize repeated tokens |
| `repetition_context_size` | 20 | Window for repetition penalty |

Example:
```python
response = generate(
    model, tokenizer,
    prompt=prompt,
    max_tokens=150,
    temp=0.8,
    top_p=0.95,
    repetition_penalty=1.1
)
```

---

## OpenAI-Compatible Server (Optional)

If you want a REST API similar to Ollama, use `mlx-textgen`:

```bash
pip install mlx-textgen

# Start server
mlx_textgen serve --model-path mlx-community/Mistral-7B-Instruct-v0.3-4bit --port 5001
```

Then use OpenAI-compatible API:

```python
from openai import OpenAI

client = OpenAI(api_key="not-needed", base_url="http://localhost:5001/v1/")

response = client.chat.completions.create(
    model="mlx-community/Mistral-7B-Instruct-v0.3-4bit",
    messages=[
        {"role": "system", "content": "You are a fantasy narrator."},
        {"role": "user", "content": "Player opens the chest."}
    ],
    max_tokens=100,
    temperature=0.8
)

print(response.choices[0].message.content)
```

Or with curl:
```bash
curl http://localhost:5001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
    "messages": [{"role": "user", "content": "Open the door"}],
    "max_tokens": 100
  }'
```

---

## Game Integration Example (Full)

```python
from mlx_lm import load, stream_generate
from typing import Generator

class GameNarrator:
    def __init__(self, model_name="mlx-community/Llama-3.2-3B-Instruct-4bit"):
        print("Loading narrator model...")
        self.model, self.tokenizer = load(model_name)
        print("Narrator ready.")
    
    def _build_prompt(self, action: str, location: str, inventory: list) -> str:
        messages = [
            {
                "role": "system", 
                "content": f"""You are the narrator of a fantasy adventure game.
Current location: {location}
Player inventory: {', '.join(inventory) if inventory else 'empty'}

Rules:
- Respond in second person, present tense
- Keep responses to 2-3 sentences
- Be vivid but concise
- Never break character"""
            },
            {
                "role": "user",
                "content": f"Player action: {action}"
            }
        ]
        
        return self.tokenizer.apply_chat_template(
            messages, 
            add_generation_prompt=True,
            tokenize=False
        )
    
    def narrate(self, action: str, location: str, inventory: list) -> str:
        """Generate narration for a player action (blocking)."""
        prompt = self._build_prompt(action, location, inventory)
        
        result = ""
        for response in stream_generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=100,
            temp=0.7
        ):
            result += response.text
        
        return result.strip()
    
    def narrate_stream(self, action: str, location: str, inventory: list) -> Generator[str, None, None]:
        """Stream narration token by token."""
        prompt = self._build_prompt(action, location, inventory)
        
        for response in stream_generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=100,
            temp=0.7
        ):
            yield response.text


# Example usage
if __name__ == "__main__":
    narrator = GameNarrator()
    
    # Blocking call
    result = narrator.narrate(
        action="examine the ancient statue",
        location="Temple of the Forgotten Gods",
        inventory=["torch", "rope", "golden key"]
    )
    print(result)
    print()
    
    # Streaming call
    print("Streaming: ", end="")
    for token in narrator.narrate_stream(
        action="pull the lever",
        location="Temple of the Forgotten Gods", 
        inventory=["torch", "rope", "golden key"]
    ):
        print(token, end="", flush=True)
    print()
```

---

## Performance Tips

1. **Keep model loaded**: Loading takes a few seconds; keep the model in memory between requests
2. **Use 4-bit quantization**: Best speed/quality tradeoff for real-time
3. **Limit max_tokens**: For narrator responses, 50-100 tokens is usually enough
4. **Use smaller models first**: Try Llama-3.2-1B before stepping up to 7B
5. **Stable prompt prefix**: MLX automatically reuses KV cache when the prompt prefix matches

## Error Handling

```python
try:
    model, tokenizer = load(model_path)
except Exception as e:
    if "not found" in str(e).lower():
        print(f"Model not found. Downloading {model_path}...")
    raise

# Check available memory
import mlx.core as mx
print(f"Metal device: {mx.default_device()}")
```

## Comparison: MLX vs Ollama

| Feature | MLX-LM | Ollama |
|---------|--------|--------|
| Prompt cache | Explicit file-based | Implicit in-memory |
| API style | Python native | REST API |
| Setup | `pip install` | `brew install` |
| Model source | Hugging Face | Ollama library |
| Best for | Python integration | Language-agnostic REST |
