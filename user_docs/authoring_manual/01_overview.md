# Overview and Quick Start

> **Part of the [Authoring Manual](00_start_here.md)**
>
> Next: [Core Concepts](02_core_concepts.md)

---

## Document Purpose

This guide is for game authors who want to create interactive fiction games using this framework. You'll learn how to:
- Create new games from scratch
- Define locations, items, and characters
- Write custom behaviors and puzzles
- Integrate with the LLM narrator
- Test and debug your game

**Not for engine developers** - If you want to extend the core engine or contribute code, see the [Engine Manual](../engine_manual.md) instead.

---

# 1. Overview

## 1.1 What is This Framework?

This is a text adventure game framework that combines:
- **Traditional parser-based gameplay** - Fast, deterministic command processing
- **LLM-powered narration** - Rich, dynamic storytelling via Claude or other LLMs
- **Behavior-driven extension** - Add new functionality through Python modules
- **JSON-based world definition** - Define your game world in readable JSON files

## 1.2 Design Philosophy

**Core Principles:**

1. **Author Capability** - The framework maximizes what you can create
2. **Player Agency** - Players have rich interactions with your world
3. **Separation of Concerns** - The engine manages state, the LLM narrates
4. **Extension Through Behaviors** - Add new functionality without modifying core code
5. **First-Class Entities** - All entities participate fully in narration and action

**How It Works:**

```
Player: "take the rusty key from the wooden chest"
    ↓
Parser: Understands common commands instantly
    ↓
Game Engine: Updates game state (key moves to inventory)
    ↓
LLM Narrator: Creates vivid prose description
    ↓
Player sees: "You reach into the old chest and carefully lift out the
             rusty key. Its cold metal feels rough against your palm,
             and you notice strange markings etched along its length."
```

**The Key Rule:** The game engine is responsible for ALL state management. The LLM never changes game state - it only narrates what happened.

## 1.3 Extension Model

Your game is built in three tiers:

```
┌─────────────────────────────────────┐
│   Your Game-Specific Behaviors      │  ← Your custom puzzles and mechanics
│   (examples/my_game/behaviors/)     │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Shared Behavior Libraries         │  ← Reusable puzzle mechanics
│   (behavior_libraries/)             │     (optional)
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Core Behaviors                    │  ← Built-in game mechanics
│   (behaviors/core/)                 │     (take, examine, go, etc.)
└─────────────────────────────────────┘
```

Your game combines:
- **Core behaviors** (built-in): Movement, object manipulation, perception
- **Libraries** (optional): Reusable puzzle mechanics from shared libraries
- **Your behaviors** (custom): Unique puzzles and interactions for your game

---

# 2. Quick Start

## 2.1 Your First Game

Let's create a minimal game to understand the structure.

**Step 1: Create game directory**
```bash
mkdir -p my_first_game/behaviors
cd my_first_game
```

**Step 2: Create game_state.json**
```json
{
  "metadata": {
    "title": "My First Adventure",
    "author": "Your Name",
    "version": "1.0",
    "description": "A simple test game",
    "start_location": "loc_start"
  },
  "locations": [
    {
      "id": "loc_start",
      "name": "Starting Room",
      "description": "A small, cozy room with wooden walls.",
      "exits": {
        "north": {
          "type": "open",
          "to": "loc_garden"
        }
      }
    },
    {
      "id": "loc_garden",
      "name": "Garden",
      "description": "A peaceful garden with blooming flowers.",
      "exits": {
        "south": {
          "type": "open",
          "to": "loc_start"
        }
      }
    }
  ],
  "items": [
    {
      "id": "item_key",
      "name": "key",
      "description": "A small brass key.",
      "location": "loc_start",
      "properties": {
        "portable": true
      }
    }
  ],
  "locks": [],
  "actors": {
    "player": {
      "id": "player",
      "name": "Adventurer",
      "description": "That's you!",
      "location": "loc_start",
      "inventory": []
    }
  }
}
```

**Step 3: Create narrator_style.txt**
```
You are narrating a cozy, lighthearted adventure game.

Style Guidelines:
- Use warm, friendly tone
- Keep descriptions concise but evocative
- Emphasize textures and sensory details
- Add gentle humor when appropriate

Example narration:
- "You pick up the brass key. It's surprisingly warm to the touch."
- "The garden welcomes you with the scent of roses and lavender."
```

**Step 4: Create behaviors directory with core symlink**
```bash
# From inside my_first_game/
mkdir behaviors
cd behaviors
ln -s ../../behaviors/core core
cd ../..
```

**Step 5: Run your game**
```bash
# Make sure you have ANTHROPIC_API_KEY set
export ANTHROPIC_API_KEY=your-key-here

python -m src.llm_game my_first_game
```

**Try these commands:**
```
> look
> examine key
> take key
> inventory
> north
> look
> south
```

Congratulations! You've created your first game.

## 2.2 Making Your First Change

Let's add a flower you can pick.

**Edit game_state.json**, add to the items array:
```json
{
  "id": "item_rose",
  "name": "rose",
  "description": "A beautiful red rose.",
  "location": "loc_garden",
  "properties": {
    "portable": true,
    "fragrant": true
  }
}
```

Restart the game and try:
```
> north
> examine rose
> take rose
> smell rose
```

The engine handles taking the rose automatically. The LLM creates unique narration using the description and properties.

---

> **Next:** [Core Concepts](02_core_concepts.md) - Learn about the game world structure, JSON format, and properties
