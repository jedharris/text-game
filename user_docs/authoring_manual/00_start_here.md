# Text Adventure Game Framework - Authoring Manual

Welcome to the game authoring documentation. This manual teaches you how to create interactive fiction games using the framework.

## Document Structure

The manual is organized into logical chunks. Start with the overview and work through in order, or jump to specific topics as needed.

### Getting Started

| Document | Description |
|----------|-------------|
| [01 - Overview & Quick Start](01_overview.md) | What the framework is, how it works, your first game |
| [02 - Core Concepts](02_core_concepts.md) | Game world structure, JSON format, properties, LLM context |

### Actors and Interactions

| Document | Description |
|----------|-------------|
| [03 - Actors](03_actors.md) | Player, NPCs, creatures, constructs - properties and the turn system |
| [04 - Actor Interactions](04_actor_interactions.md) | Combat, conditions, services, relationships, environmental effects |

### Extending the Framework

| Document | Description |
|----------|-------------|
| [05 - The Behavior System](05_behaviors.md) | Writing custom behaviors, vocabulary, handlers, tier system |
| [06 - Common Patterns](06_patterns.md) | Puzzles, interactive objects, NPCs, locations |

### Specialized Topics

| Document | Description |
|----------|-------------|
| [07 - Spatial Rooms](07_spatial.md) | Parts, positioning, cover, complex room layouts |
| [08 - Parser & Commands](08_parser.md) | How commands work, vocabulary management |
| [09 - LLM Integration](09_llm.md) | Narration customization, narrator style, debugging |

### Reference

| Document | Description |
|----------|-------------|
| [10 - Testing & Debugging](10_testing.md) | Validation, testing behaviors, debugging commands |
| [11 - Advanced Topics](11_advanced.md) | Save/load, handler chaining, creating libraries, tips |

---

## Reading Order

**New to the framework?** Read in order: 01 → 02 → 03 → 04 → 05 → 06

**Building a specific feature?**
- Combat game → 03, 04
- Puzzle game → 05, 06
- Complex room layouts → 07
- Custom commands → 05, 08

**Debugging issues?** → 10

---

## Quick Links

- [Your First Game](01_overview.md#21-your-first-game)
- [Game State JSON Format](02_core_concepts.md#32-game-state-json-format)
- [Writing Custom Behaviors](05_behaviors.md#55-writing-custom-behaviors)
- [Combat System](04_actor_interactions.md#4-combat)
- [Testing and Debugging](10_testing.md)

---

## Related Documentation

- **[Engine Manual](../engine_manual.md)** - For developers extending the core engine
- **[Spatial Quick Reference](../spatial_quick_reference.md)** - Condensed spatial system reference
