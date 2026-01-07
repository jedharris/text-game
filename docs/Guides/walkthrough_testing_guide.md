# Walkthrough Testing Guide

## Overview

Walkthroughs are automated test scripts that validate game functionality by running sequences of commands and verifying results. They support setup commands, output validation, and state assertions.

## CRITICAL: Verify Command Syntax Before Writing Walkthroughs

**BEFORE writing any walkthrough, you MUST:**

1. **Verify what commands actually exist** - Check which behavior libraries are loaded:
   - Look at `game_state.json` to see what global behaviors are loaded
   - Common libraries: `dialog_lib`, `combat_lib`, etc.
   - Each library defines specific command vocabulary

2. **Test commands manually first** - Run a quick test to verify syntax:
   ```bash
   python tools/walkthrough.py examples/big_game --file /dev/stdin <<'EOF'
   # Try the command you want to use
   ask maren about trade
   EOF
   ```

3. **Check dialog_lib for NPC conversation syntax** - The standard dialog commands are:
   - `ask <npc> about <topic>` - Ask NPC about a specific topic
   - `talk to <npc>` - Show available topics
   - **NOT** `talk to <npc> about <topic>` (this is not valid syntax)

4. **Understand the vocabulary system** - Commands must be defined in loaded behavior modules:
   - Global behaviors in `game_state.json` under `extra.behaviors`
   - Entity-specific behaviors in actor/location `behaviors` arrays
   - Vocabulary is merged from all loaded modules

## Writing Walkthroughs

### File Location
Place walkthrough files in `/walkthroughs/` with `.txt` extension.

### Basic Syntax

**Game Commands:**
```
go north
take sword
ask merchant about trade   # Correct dialog syntax
talk to merchant           # Shows available topics
```

**Comments:**
```
# This is a comment explaining the test
go north  # Comments can also appear inline
```

**Expected Failures:**
```
go south  # EXPECT_FAIL
take locked_item  # EXPECT_FAIL
```

### Setup Commands

**@set - Modify Game State:**
```
@set actors.player.properties.gold = 500
@set actors.npc_id.properties.trust_state.current = 3
@set actors.player.inventory = ["sword", "shield"]
@set extra.quest_completed = true
```

**Important:** Paths must be complete from `game_state` root:
- ✅ `actors.player.properties.gold`
- ❌ `player.properties.gold` (missing `actors.`)

Value types:
- Numbers: `500`, `3.14`
- Booleans: `true`, `false`
- Strings: `"text"` or `'text'`
- None: `none`
- Lists: `["item1", "item2"]`

### Validation Commands

**@expect - Verify Output Text:**
```
ask maren about trade
@expect "shows you her wares"
@expect "healing moss"
```

**@assert - Check Game State:**
```
@assert actors.player.properties.gold < 500
@assert actors.npc_id.properties.state_machine.current == "allied"
@assert extra.quest_flag == true
```

Supported operators:
- Equality: `==`, `!=`
- Comparison: `>`, `<`, `>=`, `<=`
- Containment: `contains`

### Complete Example

```
# Herbalist Maren Trading Test
# Tests: Trust-based pricing, inventory management

# Setup: Give player starting gold
@set actors.player.properties.gold = 500

# Navigate to herbalist location
go south
go east
go south
go south

# Test 1: View available topics
talk to maren
@expect "available topics"

# Test 2: Ask about specific topic
ask maren about trade
@expect "shows you her wares"
@expect "gold"

# Test 3: Purchase item
ask maren about silvermoss
@expect "hands you"

# Verify purchase
inventory
@expect "silvermoss"
@assert actors.player.properties.gold < 500

# Test 4: Trust-based discount
@set actors.herbalist_maren.properties.trust_state.current = 3
ask maren about trade
@expect "discount"
```

## Running Walkthroughs

### Basic Usage

```bash
# Run single walkthrough
python tools/walkthrough.py examples/big_game --file walkthroughs/test_herbalist_maren.txt

# Run with options
python tools/walkthrough.py examples/big_game \
    --file walkthroughs/test_maren.txt \
    --stop-on-error \
    --show-vitals
```

### Options

- `--stop-on-error`: Stop on first failure (recommended during development)
- `--show-vitals`: Display HP, equipment, conditions after each command
- `--show-hp`: Display HP after combat
- `--show-state`: Show detailed player state
- `--verbose`: Show full JSON responses
- `--save-state FILE`: Save final game state to file

### Interpreting Results

**Success Indicators:**
```
[✓] Command succeeded
[✓] Assertion passed
[✓] Found expected text in output
[✓] Set field.path = value
```

**Failure Indicators:**
```
[✗] Command failed unexpectedly
[✗] Expected text not found
[✗] Assertion failed: field == value
  Expected: 500
  Actual: 450
[⚠] Command failed (but expected to fail)
```

**Summary Output:**
```
Summary: 15/17 commands succeeded

⚠️  2 commands failed unexpectedly
  Line 23: talk to merchant
    Category: Parse Error

⚠️  1 assertions failed
  Line 45: @assert player.gold >= 100
    Assertion failed: actors.player.properties.gold >= 100
    Expected: 100
    Actual: 50
```

## Understanding Dialog System Integration

### How Dialog Commands Work

The dialog system has TWO layers:

1. **Command Layer** (`dialog_lib`) - Defines the commands players can type:
   - `ask <npc> about <topic>` - Implemented in `behavior_libraries/dialog_lib/handlers.py`
   - `talk to <npc>` - Shows available topics
   - These commands fire `entity_dialog` hooks on the target NPC

2. **Handler Layer** (NPC behaviors) - Defines how NPCs respond:
   - NPCs can have `dialog_reactions` in their properties
   - Can be data-driven (keyword matching) OR handler-based (Python function)
   - Handlers receive `context` dict with `keyword` extracted from the topic

### Example Flow

```
Player types: "ask maren about trade"
  ↓
dialog_lib parses: npc="maren", topic="trade"
  ↓
dialog_lib fires: entity_dialog hook on herbalist_maren entity
  ↓
dialog_reactions.py receives: context={"keyword": "trade", ...}
  ↓
Handler checks: if "trade" in TRADE_KEYWORDS → call _handle_maren_trading()
  ↓
Response returned to player
```

### Why You Can't Just Make Up Commands

**WRONG thinking:** "I need to test trading, so I'll write `buy item from merchant`"
- ✗ This command doesn't exist in any loaded behavior library
- ✗ Parser will fail with "Could not parse"
- ✗ Your test will never reach the handler

**RIGHT thinking:** "Let me check what commands exist, then write handlers that work with those commands"
- ✓ Check `game_state.json` for loaded libraries
- ✓ Read library code to see defined commands
- ✓ Write handlers that respond to those commands
- ✓ Write tests using verified command syntax

## Common Patterns

### Testing NPC Dialog
```
# First, check what NPC is listening for - look at their dialog_reactions config
# Example: Maren's handler checks for keywords in TRADE_KEYWORDS

# Test dialog with trust gates
@set actors.npc_id.properties.trust_state.current = 0
ask npc about secret
@expect "don't trust you"  # Low trust response

@set actors.npc_id.properties.trust_state.current = 3
ask npc about secret
@expect "reveals information"

# Show available topics
talk to npc
@expect "You could ask about"
```

### Testing State Transitions
```
# Verify state changes
@assert actors.npc_id.properties.state_machine.current == "neutral"

give item to npc
@expect "grateful"

@assert actors.npc_id.properties.state_machine.current == "friendly"
```

### Testing Commitments
```
# Create commitment
talk to mira about help
@expect "20 turns"
@assert extra.mira_quest_active == true

# Test success path
# ... complete quest objectives ...

@assert actors.camp_leader_mira.properties.state_machine.current == "allied"
```

### Testing Pack Behavior
```
# Verify pack mirroring
@set actors.alpha_wolf.properties.state_machine.current = "friendly"
@set actors.alpha_wolf.properties.trust_state.current = 3

# Verify followers mirror leader state
@assert actors.frost_wolf_1.properties.state_machine.current == "friendly"
@assert actors.frost_wolf_2.properties.state_machine.current == "friendly"
```

### Testing Trading Systems
```
@set actors.player.properties.gold = 1000

ask merchant about rare_item
@expect "200 gold"

# Check insufficient funds
@set actors.player.properties.gold = 50
ask merchant about rare_item
@expect "don't have enough"

# Successful purchase
@set actors.player.properties.gold = 1000
# ... purchase logic ...
@assert actors.player.properties.gold == 800
```

## Debugging Failed Walkthroughs

### 0. Parse Errors - Command Not Recognized
```
PARSE ERROR: Could not parse 'talk to maren about trade'
[⚠] ERROR: Could not parse: talk to maren about trade
```

**This is the MOST CRITICAL error - it means you're using invalid command syntax.**

**Diagnosis:**
1. The command format doesn't match any vocabulary in loaded behaviors
2. You may have invented a command that doesn't exist
3. You may be missing a required behavior library

**Fix:**
1. **Check loaded behaviors:**
   ```bash
   grep -A20 '"behaviors"' examples/big_game/game_state.json | head -30
   ```
   Look for `dialog_lib`, `combat_lib`, etc.

2. **Verify correct syntax:**
   - ✓ `ask <npc> about <topic>` (dialog_lib standard)
   - ✓ `talk to <npc>` (shows topics)
   - ✗ `talk to <npc> about <topic>` (NOT VALID - common mistake!)

3. **Test the command manually:**
   ```bash
   python tools/walkthrough.py examples/big_game --file /dev/stdin <<'EOF'
   go south
   go east
   go south
   go south
   ask maren about trade
   EOF
   ```

4. **If dialog_lib is missing from game_state:**
   - Add `"behavior_libraries.dialog_lib.handlers"` to `extra.behaviors`
   - Or configure the NPC to load it in their behaviors array

**Common cause:** Writing walkthroughs before verifying what commands actually exist in the vocabulary system.

**Prevention:** ALWAYS run a quick manual test of your command syntax BEFORE writing a full walkthrough.

### 1. Path Errors
```
[✗] Failed to set player.properties.gold: Field 'player' not found
```
**Fix:** Use full path from game_state root: `actors.player.properties.gold`

### 2. Missing Entities
```
AttributeError: Dict key 'npc_id' not found
```
**Fix:** Verify entity ID matches game_state.json exactly

### 3. Expected Text Not Found
```
[✗] Expected text not found in last output:
    Expected: shows you her wares
    Last output: The herbalist looks at you...
```
**Fix:**
- Check exact text in handler feedback
- Use partial matches (text is case-insensitive)
- Verify command triggers the right handler

### 4. Type Mismatches
```
[✗] Assertion failed: actors.player.properties.gold >= 100
  Expected: 100
  Actual: "100"
```
**Fix:** Ensure @set uses correct type (number vs string)

## Best Practices

1. **Start with Setup:** Use @set commands to establish test preconditions
2. **Test One Thing:** Each walkthrough should test a specific feature
3. **Use Descriptive Comments:** Explain what each section tests
4. **Verify State Changes:** Use @assert to confirm effects occurred
5. **Test Both Paths:** Include success and failure scenarios
6. **Keep Paths Relative:** Don't hardcode turn numbers or timing-dependent logic
7. **Group Related Tests:** Put related functionality in same walkthrough
8. **Name Descriptively:** `test_herbalist_maren.txt` not `test1.txt`

## Walkthrough Checklist

For each NPC/system, test:
- [ ] Initial state/dialog
- [ ] All dialog keywords
- [ ] Trust gates (low/high trust responses)
- [ ] State transitions
- [ ] Success paths
- [ ] Failure paths (insufficient resources, wrong state, etc.)
- [ ] Integration with other systems (if applicable)

## Advanced Techniques

### Testing Progressive Reveals
```
examine telescope
@expect "strange telescope"

examine telescope
@expect "missing a lens"

examine telescope
@expect "ancient markings"
```

### Testing Conditional Logic
```
# Without required item
use key on door  # EXPECT_FAIL
@expect "don't have"

# With required item
@set actors.player.inventory = ["iron_key"]
use key on door
@expect "unlocks"
```

### Testing Time-Limited Events
```
@set extra.event_started_turn = 10
@set current_turn = 15

# Event should still be active (within deadline)
check event status
@expect "active"

@set current_turn = 35

# Event should have expired
check event status
@expect "expired"
```
