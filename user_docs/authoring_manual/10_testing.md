# Testing and Debugging

> **Part of the [Authoring Manual](00_start_here.md)**
>
> Previous: [LLM Integration](09_llm.md) | Next: [Advanced Topics](11_advanced.md)

---


## 10.1 Validating Game State

**Validate your game state:**
```bash
python -m src.game_engine my_first_game --validate
```

**Common validation errors:**

1. **"ID not unique"** - Two entities have the same ID
   - Solution: Make all IDs unique (even across types)

2. **"Reference not found"** - Exit points to non-existent location
   - Solution: Check `to` field matches actual location ID

3. **"start_location not found"** - Metadata references non-existent location
   - Solution: Check metadata.start_location matches a location ID

4. **"Player actor not found"** - No actor with id "player"
   - Solution: Add player actor to actors section

5. **"Circular containment"** - Item A in item B in item A
   - Solution: Break the cycle in item locations

6. **"Door has no location"** - Door not attached to exit
   - Solution: Set door location to `"exit:loc_id:direction"`

## 10.2 Testing Behaviors

### Manual Testing

**Test workflow:**
1. Make changes to behavior module
2. Restart game (behaviors load at startup)
3. Test commands manually
4. Use `--debug` flag to see behavior invocations

### Automated Testing

**Write unit tests for behaviors:**

```python
# tests/test_my_behavior.py
import unittest
from src.state_manager import GameState, Item, Actor, Location
from src.state_accessor import StateAccessor
from src.behavior_manager import BehaviorManager
from src.word_entry import WordEntry, WordType

class TestMagicMirror(unittest.TestCase):
    def setUp(self):
        """Set up test state."""
        # Create minimal game state
        self.state = GameState(
            metadata=...,
            locations=[...],
            items=[...],
            actors={"player": Actor(...)},
            locks=[]
        )

        # Load your behavior
        self.manager = BehaviorManager()
        import behaviors.magic_mirror
        self.manager.load_module(behaviors.magic_mirror)

        self.accessor = StateAccessor(self.state, self.manager)

    def test_peer_reveals_key(self):
        """Test that peering at mirror reveals hidden key."""
        from behaviors.magic_mirror import handle_peer

        # Add mirror and hidden key
        mirror = Item(id="item_magic_mirror", name="mirror",
                     description="...", location="loc_room",
                     properties={}, behaviors=["behaviors.magic_mirror"])
        key = Item(id="item_hidden_key", name="key",
                  description="...", location="loc_room",
                  properties={"portable": True, "states": {"hidden": True}},
                  behaviors=[])

        self.state.items.extend([mirror, key])

        # Peer at mirror
        action = {
            "verb": "peer",
            "object": WordEntry("mirror", WordType.NOUN, []),
            "actor_id": "player"
        }

        result = handle_peer(self.accessor, action)

        # Verify key revealed
        self.assertTrue(result.success)
        self.assertFalse(key.states.get("hidden", False))
        self.assertIn("key", result.message.lower())

if __name__ == "__main__":
    unittest.main()
```

**Run tests:**
```bash
python -m unittest tests/test_my_behavior.py
```

## 10.3 Debugging Commands

### Understanding Errors

**"Handler not found"**
```
Error: I don't understand 'cast'.
```
- Behavior module not loaded
- VOCABULARY not exported
- Handler function not at module level

**Check:**
```bash
python -m src.llm_game my_game --debug
```
Look for: `Loaded module: behaviors.magic_spells`

**"Entity not found"**
```
You don't see key here.
```
- Item not in current location
- Name doesn't match vocabulary
- Synonyms missing

**Debug:**
```python
# In behavior handler, add:
import sys
print(f"DEBUG: Looking for {obj_entry.word}", file=sys.stderr)
print(f"DEBUG: Synonyms: {obj_entry.synonyms}", file=sys.stderr)
print(f"DEBUG: Items here: {[i.name for i in items]}", file=sys.stderr)
```

**"State corrupted"**
```
Game state is corrupted. Please save and restart.
```
- Inconsistent state detected
- Usually: invalid references, broken containment

**Solution:** Check error message details, fix game_state.json, restart

### Testing Command Variations

Test different phrasings:
```
> take key
> get the key
> pick up key
> grab key

> examine red key
> look at the red key
> x red key
> inspect red key
```

All should work if synonyms are defined properly.

---


---

> **Next:** [Advanced Topics](11_advanced.md) - Save/load system, handler chaining, creating libraries, tips
