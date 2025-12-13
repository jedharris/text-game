# Ollama API Reference for Game Narrator Integration

## Overview
Ollama runs locally at `http://localhost:11434`. The game should use the `/api/generate` endpoint for narrator responses.

## Model
Using `mistral:7b-instruct-q8_0` — fast, good narrative quality.

## Generate Endpoint

**POST** `http://localhost:11434/api/generate`

### Request (non-streaming)
```json
{
  "model": "mistral:7b-instruct-q8_0",
  "prompt": "Your full prompt here including system instructions and player action",
  "stream": false,
  "keep_alive": -1,
  "options": {
    "temperature": 0.8,
    "num_predict": 150
  }
}
```

### Request (streaming)
```json
{
  "model": "mistral:7b-instruct-q8_0",
  "prompt": "...",
  "stream": true,
  "keep_alive": -1
}
```

### Response (non-streaming)
```json
{
  "model": "mistral:7b-instruct-q8_0",
  "created_at": "2024-01-01T00:00:00.000000Z",
  "response": "The narrator's response text here",
  "done": true,
  "total_duration": 1234567890,
  "prompt_eval_count": 42,
  "eval_count": 28
}
```

### Response (streaming)
Each chunk is a JSON object:
```json
{"model":"mistral:7b-instruct-q8_0","response":"The","done":false}
{"model":"mistral:7b-instruct-q8_0","response":" torch","done":false}
{"model":"mistral:7b-instruct-q8_0","response":" flickers","done":false}
...
{"model":"mistral:7b-instruct-q8_0","response":"","done":true,"total_duration":...}
```

## Key Parameters

| Parameter | Description |
|-----------|-------------|
| `model` | Model name with tag |
| `prompt` | Full prompt text (system + context + player action) |
| `stream` | `true` for streaming, `false` for complete response |
| `keep_alive` | `-1` keeps model in memory indefinitely |
| `system` | System prompt (alternative to embedding in prompt) |
| `raw` | `true` to skip chat template formatting |

### Options (in `options` object)
| Option | Default | Description |
|--------|---------|-------------|
| `temperature` | 0.8 | Creativity (0.0-2.0, lower = more deterministic) |
| `num_predict` | 128 | Max tokens to generate |
| `top_p` | 0.9 | Nucleus sampling threshold |
| `top_k` | 40 | Top-k sampling |
| `repeat_penalty` | 1.1 | Penalize repetition |

## Prompt Caching Behavior
Ollama automatically caches the KV state when:
1. The model stays loaded (`keep_alive: -1`)
2. The prompt prefix is identical between requests

**For narrator use:** Structure prompts so the system instructions and world state are a stable prefix, with only the player action changing at the end.

## Example: JavaScript/TypeScript

```javascript
async function getNarration(playerAction) {
  const systemPrompt = `You are the narrator of a fantasy adventure game. 
Describe outcomes vividly but briefly (2-3 sentences max).
Current location: ${gameState.location}
Inventory: ${gameState.inventory.join(', ')}`;

  const response = await fetch('http://localhost:11434/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'mistral:7b-instruct-q8_0',
      prompt: `${systemPrompt}\n\nPlayer action: ${playerAction}\n\nNarrator:`,
      stream: false,
      keep_alive: -1,
      options: { temperature: 0.8, num_predict: 100 }
    })
  });
  
  const data = await response.json();
  return data.response;
}
```

## Example: Streaming with JavaScript

```javascript
async function streamNarration(playerAction, onChunk) {
  const response = await fetch('http://localhost:11434/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'mistral:7b-instruct-q8_0',
      prompt: `${systemPrompt}\n\nPlayer action: ${playerAction}\n\nNarrator:`,
      stream: true,
      keep_alive: -1
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n').filter(line => line.trim());
    
    for (const line of lines) {
      const data = JSON.parse(line);
      if (data.response) {
        onChunk(data.response);
      }
    }
  }
}
```

## Health Check
```bash
curl http://localhost:11434/api/tags
```
Returns list of available models. Use to verify Ollama is running.

## Error Handling
- Connection refused: Ollama not running (`ollama serve`)
- Model not found: Need to pull model (`ollama pull mistral:7b-instruct-q8_0`)
- Timeout: Model loading (first request after idle may be slow)