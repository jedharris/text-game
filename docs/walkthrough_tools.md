# Walkthrough Testing Tools

This document describes the three walkthrough tools available for testing game functionality and narration quality.

## Overview

The game has three complementary walkthrough tools:

1. **[tools/walkthrough.py](../tools/walkthrough.py)** - Engine-only testing (fast, existing tool)
2. **[tools/json_walkthrough.py](../tools/json_walkthrough.py)** - JSON structure testing (fast, automated)
3. **[tools/llm_walkthrough.py](../tools/llm_walkthrough.py)** - Full LLM testing (slow, manual review)

## Tool Comparison

| Feature | walkthrough.py | json_walkthrough.py | llm_walkthrough.py |
|---------|---------------|---------------------|-------------------|
| **Speed** | Instant | Instant | ~1-2s per turn |
| **Tests** | Game mechanics | Narration JSON | Full prose |
| **Use case** | CI, rapid iteration | CI, structure tests | Manual review |
| **Assertions** | State assertions | JSON assertions | None (review) |
| **Deterministic** | Yes | Yes | No (LLM variability) |

## 1. Engine-Only Walkthrough (walkthrough.py)

Tests game mechanics without LLM narration.

### Usage

```bash
python tools/walkthrough.py examples/spatial_game --file walkthroughs/test.txt
python tools/walkthrough.py examples/spatial_game --file walkthroughs/test.txt --verbose
```

### What It Tests

- ✅ Command parsing (via Parser)
- ✅ Game state changes (inventory, location, posture)
- ✅ Success/failure outcomes
- ✅ Game mechanics (puzzles, locks, movement)

### What It Does NOT Test

- ❌ LLM parsing (natural language → structured command)
- ❌ LLM narration (structured result → natural language prose)
- ❌ Narration quality (perspective, tone, sentence count)

### Walkthrough Format

```
# Comments start with #
look
take key
go north
# EXPECT_FAIL annotation for commands that should fail
unlock door with spoon  # EXPECT_FAIL
```

### Assertions

State assertions using dotted paths:

```
ASSERT player.location == location_tower_entrance
ASSERT player.inventory contains item_key
ASSERT player.properties.health >= 90
```

See [testing_with_walkthroughs.md](testing_with_walkthroughs.md) for more details.

## 2. JSON Structure Walkthrough (json_walkthrough.py)

Tests narration JSON structure (the "recipe" sent to the LLM narrator). Fast and deterministic, suitable for CI.

### Usage

```bash
python tools/json_walkthrough.py examples/spatial_game \\
    --file walkthroughs/json/phase1_checks.txt

python tools/json_walkthrough.py examples/spatial_game \\
    --file walkthroughs/json/phase1_checks.txt \\
    --show-json
```

### What It Tests

- ✅ Narration JSON structure (NarrationPlan)
- ✅ Entity refs presence and content
- ✅ Must_mention frequency and conditions
- ✅ Scope information (scene_kind, familiarity, outcome)
- ✅ Viewpoint data (mode, posture)
- ✅ Context builder logic

### Walkthrough Format

Commands with JSON assertions:

```
# Execute command
stand on bench

# Assertions check the narration JSON from previous command
assert_json: entity_refs is not empty
assert_json: entity_refs[*bench*] exists
assert_json: entity_refs[*bench*].traits contains weathered stone

# Another command
north
assert_json: scope.scene_kind == location_entry
assert_json: scope.familiarity == new
```

### Assertion Syntax

**Existence checks:**
```
assert_json: field exists
assert_json: field not exists
assert_json: field is empty
assert_json: field is not empty
```

**Comparisons:**
```
assert_json: scope.scene_kind == location_entry
assert_json: scope.familiarity != new
assert_json: entity_refs contains key_word
```

**Path expressions:**
```
# Dotted paths
assert_json: scope.scene_kind == look

# Wildcard matching (finds first key containing pattern)
assert_json: entity_refs[*bench*].traits contains weathered stone
```

### Example Walkthrough

[walkthroughs/json/phase1_checks.txt](../walkthroughs/json/phase1_checks.txt):

```
# Phase 1 JSON Structure Verification

# Test 1: Stand on bench should have entity_refs with bench traits
stand on bench
assert_json: entity_refs is not empty
assert_json: entity_refs[*bench*] exists
assert_json: entity_refs[*bench*].traits is not empty
assert_json: entity_refs[*bench*].traits contains weathered stone

# Test 2: First movement north
north
assert_json: scope.scene_kind == location_entry

# Test 5: Explicit look always includes exits
look
assert_json: scope.scene_kind == look
assert_json: must_mention.exits_text exists
```

## 3. LLM Walkthrough (llm_walkthrough.py)

Tests full end-to-end narration with actual LLM. Generates transcripts for review by humans or large models (Claude, GPT-4).

### Usage

```bash
# Basic usage
python tools/llm_walkthrough.py examples/spatial_game \\
    --file walkthroughs/narration/phase1_quality.txt \\
    --model mlx-community/Qwen2.5-7B-Instruct-4bit

# Save transcript for review
python tools/llm_walkthrough.py examples/spatial_game \\
    --file walkthroughs/narration/phase1_quality.txt \\
    --model mlx-community/Qwen2.5-7B-Instruct-4bit \\
    --save-transcript phase1_output.log
```

### What It Tests

- ✅ Full LLM parsing (natural language → structured command)
- ✅ Full LLM narration (structured result → natural language prose)
- ✅ Narration quality (via manual/model review)
- ✅ Prompt effectiveness
- ✅ Narrator protocol compliance

### Requirements

- MLX-LM library: `pip install mlx-lm`
- macOS 13.5+ and Apple Silicon (M1/M2/M3/M4)
- ~7-8GB VRAM for 7B model

### Performance

- Model load: ~30 seconds (first time)
- Per turn: ~1-2 seconds
- 20-command walkthrough: ~30-40 seconds

### Walkthrough Format

Simple command list (no assertions):

```
# Phase 1 Narration Quality Check
# For review by humans or large models

# Test entity_refs preventing hallucinations
stand on bench

# Test must_mention field name leakage
north

# Test familiar location (no exits)
south

# Test look command (always has exits)
look
```

### Output Format

The tool generates a transcript showing:

1. Opening narration
2. Each turn with:
   - Input command
   - Generated prose

### Transcript Review

#### Manual Review

Look for:
- Perspective errors ("I" vs "you")
- Material hallucinations (wood vs stone)
- Field name leakage ("Must mention: Exits...")
- Tone/style violations
- Word duplication bugs
- Sentence count violations

#### Model-Based Review

Use large models (Claude, GPT-4) to review transcripts:

1. Generate transcript:
   ```bash
   python tools/llm_walkthrough.py examples/spatial_game \\
       --file walkthroughs/narration/phase1_quality.txt \\
       --save-transcript phase1.log
   ```

2. Send transcript to large model with prompt:
   ```
   Review this game narration transcript. Check for:
   - Perspective consistency (should use 'you' not 'I')
   - Material accuracy (bench is weathered stone, not wood)
   - Field name leakage (literal 'Must mention:' text)
   - Tone adherence to narrator_style.txt
   - Word duplication bugs

   Report any issues found with specific examples.
   ```

3. Model provides structured feedback:
   - Lists specific errors with turn numbers
   - Identifies patterns
   - Suggests fixes

**Benefits:**
- Faster than manual review
- More consistent
- Can process long transcripts
- Good for regression testing

## Testing Workflow

### Rapid Development (JSON Assertions)

```bash
# 1. Make changes to narration assembly logic
# 2. Test JSON structure instantly
python tools/json_walkthrough.py examples/spatial_game \\
    --file walkthroughs/json/phase1_checks.txt
```

### Narration Quality Check (LLM Review)

```bash
# 1. Generate transcript with actual prose
python tools/llm_walkthrough.py examples/spatial_game \\
    --file walkthroughs/narration/phase1_quality.txt \\
    --save-transcript phase1_test.log

# 2. Review transcript manually or with large model
# Look for perspective errors, hallucinations, field leakage, etc.
```

### CI Integration

**Recommended:**
- ✅ Include `walkthrough.py` in CI (instant, deterministic)
- ✅ Include `json_walkthrough.py` in CI (instant, deterministic)
- ❌ Do NOT include `llm_walkthrough.py` in CI (slow, non-deterministic)

**CI Test Example:**

```bash
# Fast game mechanics tests
python tools/walkthrough.py examples/spatial_game \\
    --file walkthroughs/game_mechanics.txt

# Fast JSON structure tests
python tools/json_walkthrough.py examples/spatial_game \\
    --file walkthroughs/json/narration_structure.txt
```

## File Organization

```
walkthroughs/
  game_mechanics.txt         # Engine-only walkthrough
  json/
    phase1_checks.txt        # JSON structure tests
    entity_refs_tests.txt    # Entity reference verification
  narration/
    phase1_quality.txt       # LLM narration quality tests
    parser_tests.txt         # Parser accuracy tests
    style_compliance.txt     # Style guide adherence
```

## When to Use Each Tool

### Use walkthrough.py when:
- Testing game mechanics and state changes
- Rapid iteration during development
- Running in CI/automated tests
- Don't need to test narration quality

### Use json_walkthrough.py when:
- Testing narration assembly logic
- Verifying entity_refs, must_mention, scope data
- Want fast, deterministic narration tests
- Running in CI/automated tests
- Testing context builder changes

### Use llm_walkthrough.py when:
- Testing actual narration quality
- Investigating bug reports
- Testing prompt or protocol changes
- Generating transcripts for model review
- Want to see what players will actually read

## Tips

### JSON Walkthrough Tips

1. **Use wildcard matching** for entity IDs:
   ```
   # Good - finds any key containing "bench"
   assert_json: entity_refs[*bench*].traits contains weathered stone

   # Bad - requires exact entity ID
   assert_json: entity_refs.item_garden_bench.traits contains weathered stone
   ```

2. **Check emptiness carefully**:
   ```
   # These are different!
   assert_json: must_mention is empty       # Field is None, "", [], or {}
   assert_json: must_mention not exists     # Field is not present in JSON
   ```

3. **Document known bugs**:
   ```
   # NOTE: Familiarity tracking has a bug - always shows "familiar"
   # assert_json: scope.familiarity == new  # DISABLED - bug #XXX
   ```

### LLM Walkthrough Tips

1. **Use temperature=0** for more consistent results (already default)

2. **Keep walkthroughs short** (~5-10 commands) for quick review

3. **Save transcripts** for later comparison:
   ```bash
   python tools/llm_walkthrough.py ... --save-transcript before_fix.log
   # Make changes
   python tools/llm_walkthrough.py ... --save-transcript after_fix.log
   # Compare manually or with diff
   ```

4. **Test specific scenarios** rather than comprehensive coverage

## See Also

- [testing_with_walkthroughs.md](testing_with_walkthroughs.md) - Original walkthrough testing overview
- [llm_walkthrough_proposal.md](llm_walkthrough_proposal.md) - Design proposal for JSON/LLM tools
- [narration_quality_improvement_plan.md](narration_quality_improvement_plan.md) - Phase 1-6 narration work
