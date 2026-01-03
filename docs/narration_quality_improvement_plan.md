# Narration Quality Improvement Plan

**Created**: 2026-01-02
**Issue**: #370 - Narration quality regression after exit migration
**Status**: Planning

---

## Executive Summary

Spatial_game playthrough analysis revealed that while game mechanics work perfectly, narration quality has degraded. The LLM narrator (Qwen2.5-7B-Instruct) produces:
- Material hallucinations ("wooden mat" when authoring says fabric, "rusty key" when golden)
- Word duplications ("ball ball", "hall hall", "swirls swirl")
- Perspective inconsistency (mixing "I" and "You" despite first-person requirement)
- Field name leakage ("Must mention: Exits lead...")
- Language switching (broke into Chinese mid-sentence once)
- Cross-contamination (borrowing traits from one entity to describe another)

**Root causes identified**:
1. **Missing entity_refs**: Handlers don't serialize entity data for action_result scenes
2. **Incomplete trait authoring**: Many entities have descriptions but not structured traits
3. **Narrator prompt ambiguities**: 7B model misinterprets instructions
4. **must_mention over-use**: Appears on every scene, even when redundant

**Good news**:
- Exit perspective variants work excellently ("look at down" perfectly describes stairs from top)
- When traits ARE present, narrator uses them well
- Core architecture is sound

---

## Root Cause Analysis

### 1. Missing entity_refs in action_result Scenes

**Evidence**: "stand on bench" (log lines 47-64)
```json
{
  "action_verb": "stand",
  "primary_text": "You stand on the bench.",
  "entity_refs": {},  // EMPTY!
}
```

**Result**: LLM has no information about bench traits, hallucinates "wood is rough under your feet" when bench is actually weathered stone.

**Why**: Spatial handlers (and others) don't call `serialize_for_handler_result()` to populate HandlerResult.data.

**Contrast**: "climb tree" works perfectly because handler serializes tree data → entity_refs includes traits → narrator uses them correctly.

---

### 2. Incomplete Trait Authoring

**Evidence from transcript**:
- Garden bench: Description says "weathered stone bench" but entity lacks llm_context.traits
- Welcome mat: No traits → narrator invents "wooden mat"
- Golden key: Materializes as "golden" but later described as "rusty"
- Storage door: Description says "wooden door" but actually should be iron with runes

**Pattern**: Original authoring put descriptive text in `description` field. Narrator authoring initiative (docs/narrator_authoring_implementation_plan.md) added llm_context.traits to many entities, but spatial_game wasn't fully converted.

**Solution**: Extract descriptive details from `description` fields into structured `llm_context.traits`.

**Example transformation**:
```json
// BEFORE
{
  "id": "item_welcome_mat",
  "name": "mat",
  "description": "A worn welcome mat with faded lettering lies near the entrance."
}

// AFTER
{
  "id": "item_welcome_mat",
  "name": "mat",
  "description": "A worn welcome mat with faded lettering lies near the entrance.",
  "llm_context": {
    "traits": [
      "woven fabric",
      "faded welcome lettering",
      "worn from years of use",
      "dusty surface"
    ]
  }
}
```

---

### 3. Narrator Prompt Ambiguities

**Issue 3a: must_mention Leakage**

Evidence (log lines 353-396):
```
Must mention: Exits lead south (garden archway to Overgrown Garden)...
```

The narrator literally outputs the field name!

Current prompt says: "Include any text in `must_mention` verbatim"

7B model interprets this as "print the field name AND the text."

**Issue 3b: Weak Perspective Instruction**

Narrator switches between "I" and "You" randomly despite spatial_game requiring consistent first person.

Current prompt mentions perspective only briefly. 7B models need explicit, emphatic instructions.

**Issue 3c: No Negative Examples**

7B models benefit from "DON'T do this" examples. Current prompt only shows positive examples.

---

### 4. must_mention Over-use

**Evidence**: Every narration ends with exits text, even:
- Brief actions ("take key")
- Examining objects ("examine ball")
- Familiar location revisits

**Why**: narration_assembler.py includes must_mention.exits_text for ALL location_entry and look scenes.

**User feedback**: "not every time - player can always look"

---

### 5. Redundant Context in primary_text

**Evidence** (log line 357):
```json
"primary_text": "You go north stone path to Tower Entrance.\n\nTower Entrance\n...
                 Exits: garden archway (south), wooden door (east), spiral staircase (up)",
"must_mention": {
  "exits_text": "Exits lead south (garden archway to Overgrown Garden), east (wooden door), and up (spiral staircase to Wizard's Library)."
}
```

The exits appear TWICE - once in primary_text (engine-generated room description) and again in must_mention. This confuses the narrator.

---

## Phase 1: Critical Fixes (High Impact)

### 1.1 Fix Missing entity_refs in Handlers

**Goal**: Ensure all command handlers serialize entity data so narration_assembler can populate entity_refs.

**Changes**:

1. **Spatial handlers** (behaviors/core/spatial.py or similar):
```python
# Current (BROKEN)
def handle_stand(accessor, action):
    # ... state changes ...
    return HandlerResult(success=True, primary="You stand on the bench.")

# Fixed
def handle_stand(accessor, action):
    # ... state changes ...
    target_data = serialize_for_handler_result(bench_item, accessor, actor_id)
    return HandlerResult(
        success=True,
        primary="You stand on the bench.",
        data=target_data
    )
```

2. **Review all handlers** in behaviors/core/ for similar issues:
   - stand, sit, climb, descend
   - Any handler that manipulates specific entities

**Testing**:
- Run "stand on bench" → verify entity_refs contains bench with traits
- Run "climb tree" → verify still works (regression test)

**Estimated effort**: 2-4 handlers to fix, ~30 minutes each

---

### 1.2 Fix must_mention Field Leakage

**Problem**: Narrator outputs "Must mention: Exits lead..." literally.

**Solution A** (Preferred): Reword narrator prompt

```markdown
// BEFORE (unified_narrator_prompt_revised_api.md line 39)
5. Include any text in `must_mention` verbatim

// AFTER
5. Weave the information from `must_mention` naturally into your narration.
   - Do NOT output field names like "must_mention:" or "exits_text:"
   - Integrate the content smoothly as part of your description
```

**Solution B** (Complementary): Add negative example

```markdown
## COMMON ERRORS TO AVOID

❌ WRONG: "Must mention: Exits lead north to the garden."
✅ RIGHT: "Exits lead north to the garden." (integrated naturally)
```

**Testing**:
- Run "north" command → verify no "Must mention:" in output
- Verify exits are still mentioned naturally

**Files**: docs/Narration/unified_narrator_prompt_revised_api.md

---

### 1.3 Reduce must_mention Frequency

**Problem**: Exits mentioned on every action, even examining objects.

**Solution**: Only include must_mention.exits_text when player wants orientation:

```python
# In narration_assembler.py _build_must_mention()

# Include exits_text for location-related scenes
if scene_kind in ("location_entry", "look"):
    # For location_entry, only on first visit OR if explicitly moving
    if scene_kind == "location_entry":
        include_exits = (familiarity == "new")  # First visit only
    else:  # look
        include_exits = True  # Player explicitly looking around

    if include_exits:
        actor = self.accessor.get_actor(self.actor_id)
        if actor:
            location = self.accessor.get_location(actor.location)
            if location:
                visible_exits = self.accessor.get_visible_exits(location.id, self.actor_id)
                if visible_exits:
                    exits_text = self._format_exits_text(visible_exits)
                    if exits_text:
                        result["exits_text"] = exits_text
```

**Alternative**: Keep current behavior but skip for action_result entirely.

**Testing**:
- "north" (first visit) → exits shown
- "north" (return visit) → no exits (player knows them)
- "look" → exits always shown
- "take key" → no exits

**Files**: src/narration_assembler.py lines 395-435

---

### 1.4 Remove Exits from primary_text for location_entry

**Problem**: Exits appear in both primary_text (engine-generated) and must_mention, causing duplication.

**Solution**: For location_entry scenes, the engine-generated primary_text should NOT include the exits list - that's what must_mention.exits_text is for.

**Investigation needed**:
- Where is primary_text generated for location_entry?
- Is it in the "go" handler or somewhere in location serialization?

**Files**: TBD after investigation

---

## Phase 2: Authoring - Extract Traits from Descriptions

### 2.1 Audit spatial_game Entities

**Goal**: Find entities with descriptions but no llm_context.traits.

**Method**:
```bash
cd examples/spatial_game
# Find items with description but no llm_context
jq '.items[] | select(.description != null and .llm_context == null) | .id' game_state.json

# Find items with llm_context but no traits
jq '.items[] | select(.llm_context != null and .llm_context.traits == null) | .id' game_state.json
```

**Expected entities needing work** (from transcript):
- item_welcome_mat
- item_garden_bench (may have traits for look but not action_result - investigate)
- door_storage (wooden door)
- item_golden_key (or whatever the crystal ball produces)
- item_umbrella_stand
- item_old_umbrella

---

### 2.2 Extract Traits Systematically

**Process for each entity**:

1. Read current description
2. Extract descriptive phrases into traits list
3. Keep description (useful for engine logic)
4. Add llm_context.traits

**Example - item_welcome_mat**:

Assuming current description: "A worn welcome mat with faded lettering lies near the entrance."

```json
{
  "id": "item_welcome_mat",
  "name": "mat",
  "description": "A worn welcome mat with faded lettering lies near the entrance.",
  "llm_context": {
    "traits": [
      "woven fabric",
      "faded welcome lettering",
      "worn edges",
      "dusty from foot traffic"
    ]
  }
}
```

**Quality criteria for traits**:
- **Specific and sensory**: "woven fabric" not "made of material"
- **Visual details**: Colors, textures, wear patterns
- **No redundancy**: Don't repeat the name ("mat-like texture")
- **4-6 traits per entity**: Enough for variety, not overwhelming

---

### 2.3 Priority Entities (from transcript failures)

**Critical path** (caused visible errors):
1. **item_welcome_mat** → "wooden mat" hallucination
2. **item_golden_key** → "rusty key" hallucination
3. **item_garden_bench** → "wooden bench" when standing (but has traits for look?)
4. **door_storage** → "wooden door" when should be iron with runes

**Secondary** (entities mentioned without traits):
5. item_umbrella_stand
6. item_old_umbrella
7. item_rusty_trowel (may already have traits)

**Investigation needed**:
- Why does bench have traits for "look" but not "stand"?
- Is this a handler issue or authoring issue?

---

### 2.4 Document Pattern for Future Authoring

**Create**: docs/authoring_patterns.md section on trait extraction

```markdown
## Converting Descriptions to Traits

When authoring new entities or updating old ones:

1. **Keep the description** - used by engine for logic
2. **Extract traits** - used by narrator for prose

### Good Traits
✅ "weathered stone" (material + condition)
✅ "moss-covered surface" (visual detail)
✅ "cool to the touch" (sensory)
✅ "sturdy construction" (quality)

### Bad Traits
❌ "bench-like" (redundant with entity type)
❌ "very old" (vague)
❌ "can be sat upon" (mechanical, not descriptive)

### Example Conversion
Description: "A weathered stone bench covered in moss sits in the garden."

Traits:
- "weathered stone"
- "moss-covered surface"
- "cool to the touch"
- "sturdy construction"
```

---

## Phase 3: Narrator Prompt Improvements

### 3.1 Strengthen Perspective Requirement

**Problem**: Narrator mixes "I" and "You" despite first-person requirement.

**Solution**: Add emphatic section to unified_narrator_prompt_revised_api.md

```markdown
## CRITICAL: NARRATIVE PERSPECTIVE CONSISTENCY

The game's style prompt specifies narrative person (FIRST PERSON or SECOND PERSON).

**ABSOLUTE REQUIREMENT: Maintain consistent perspective throughout your ENTIRE response.**

### First Person (when style says "Narrative person: FIRST PERSON")
- ✅ Use ONLY: "I", "me", "my", "mine"
- ❌ NEVER use: "you", "your", "yours"
- Example: "I look at the door and reach for the handle."

### Second Person (when style says "Narrative person: SECOND PERSON")
- ✅ Use ONLY: "you", "your", "yours"
- ❌ NEVER use: "I", "me", "my"
- Example: "You look at the door and reach for the handle."

**Mixing perspectives within a single narration is a critical failure.**

---
```

**Placement**: After Section A (API rules), before Section B (Style)

**Testing**:
- Run spatial_game playthrough → count perspective switches
- Target: <5% switches (down from ~40%)

---

### 3.2 Add Negative Examples Section

**Goal**: Give 7B model explicit guardrails.

**Solution**: Add to unified_narrator_prompt_revised_api.md

```markdown
## COMMON ERRORS TO AVOID

These are critical failures that break immersion:

❌ **Word duplication**: "ball ball", "hall hall", "swirls swirl"
   - Check your output before submitting

❌ **Inventing materials not in traits**:
   - If traits say "weathered stone", don't narrate "rough wood"
   - If traits say "woven fabric", don't narrate "wooden surface"
   - Use ONLY materials mentioned in traits or primary_text

❌ **Language switching**:
   - Always respond in English
   - Never switch to another language mid-sentence

❌ **Field name leakage**:
   - Never output: "Must mention:", "entity_refs:", "primary_text:"
   - These are internal field names, not narration content

❌ **Perspective mixing**:
   - Choose first person OR second person based on style
   - Never mix them in the same response

❌ **Cross-contamination**:
   - Don't use traits from one entity to describe another
   - If entity_refs doesn't have traits for an item, describe it generically
```

**Placement**: After Section A, in API rules

---

### 3.3 Clarify Trait Usage

**Problem**: When entity_refs lacks traits, narrator invents materials from other entities.

**Solution**: Add explicit guidance

```markdown
## USING ENTITY REFERENCES

When entity_refs provides traits for an entity:
- ✅ Use those traits to add sensory detail
- ✅ Weave them naturally into prose
- ❌ Don't list them mechanically

When entity_refs LACKS traits for an entity:
- ✅ Describe it generically using the name from entity_refs
- ❌ Don't invent materials or details
- ❌ Don't borrow traits from OTHER entities

Example:
```json
"entity_refs": {
  "item_mat": {"name": "mat"},  // No traits
  "door_storage": {"name": "door", "traits": ["heavy oak", "iron hinges"]}
}
```

✅ Good: "You see a mat on the floor and a heavy oak door with iron hinges."
❌ Bad: "You see an oak mat on the floor..." (borrowed "oak" from door)
```

---

### 3.4 Simplify must_mention Instruction

**Current** (line 39):
```
5. Include any text in `must_mention` verbatim
```

**Improved**:
```
5. Incorporate information from `must_mention` naturally
   - If `exits_text` is present, mention the exits as part of your scene description
   - If `dialog_topics` is present, mention available conversation topics
   - Weave this information smoothly - don't quote field names
```

---

## Phase 4: Diagnostics and Quality Assurance

### 4.1 Add entity_refs Validation

**Goal**: Catch missing entity serialization during development.

**Implementation**: In narration_assembler.py

```python
def _build_entity_refs(self, handler_result: HandlerResult) -> Dict[str, EntityRef]:
    """Build entity_refs from handler result and game state."""
    entity_refs: Dict[str, EntityRef] = {}

    # ... existing code ...

    # DIAGNOSTIC: Warn if entity_refs is empty for full verbosity action scenes
    if not entity_refs:
        # Check if this is a scene that should have entity refs
        if handler_result.data:
            # Handler provided data but entity_refs is still empty
            # This suggests serialization issue
            pass  # entity_refs will be populated below
        else:
            # No data at all - handler didn't serialize
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Empty entity_refs for action. Handler may not be serializing entity data. "
                f"Result: {handler_result.primary[:50]}..."
            )

    return entity_refs
```

**Benefit**: Developers see warnings during testing when handlers forget to serialize.

---

### 4.2 Create Narration Quality Test Suite

**Goal**: Automated regression testing for narration quality.

**Implementation**: tools/test_narration_quality.py

```python
"""
Test narration quality against known issues.

Run after changes to narrator prompt or assembler.
"""

test_cases = [
    {
        "name": "stand_on_bench",
        "commands": ["stand on bench"],
        "must_not_contain": ["wood", "wooden"],  # Bench is stone
        "must_contain": ["stone", "bench"],
        "perspective": "first",  # spatial_game uses first person
    },
    {
        "name": "take_golden_key",
        "commands": ["peer into ball", "take key"],
        "must_not_contain": ["rusty", "iron", "Must mention"],
        "must_contain": ["gold", "key"],
        "perspective": "first",
    },
    {
        "name": "examine_mat",
        "commands": ["examine mat"],
        "must_not_contain": ["wood", "wooden"],  # Mat is fabric
        "must_contain": ["mat"],
    },
]

def check_perspective(text: str, expected: str) -> bool:
    """Check if narration maintains expected perspective."""
    if expected == "first":
        has_first = bool(re.search(r'\bI\b|\bme\b|\bmy\b', text))
        has_second = bool(re.search(r'\bYou\b|\byour\b', text))
        return has_first and not has_second
    elif expected == "second":
        has_first = bool(re.search(r'\bI\b|\bme\b|\bmy\b', text))
        has_second = bool(re.search(r'\bYou\b|\byour\b', text))
        return has_second and not has_first
    return True

def check_no_duplication(text: str) -> List[str]:
    """Find word duplications like 'ball ball'."""
    words = re.findall(r'\b(\w+)\s+\1\b', text.lower())
    return words

# Run test suite, report failures
```

**Usage**:
```bash
python tools/test_narration_quality.py examples/spatial_game
```

**Benefit**: Catch regressions before they ship.

---

### 4.3 Add Narrator Evaluation Harness

**Reference**: docs/Narration/narration_recipe_design.md mentions evaluation harness (lines 187-218)

**Implementation**: Expand tools/narrator_eval_harness.py

- Test must_contain / must_not_contain rules
- Check perspective consistency
- Detect word duplication
- Verify no field name leakage
- Report metrics

**Benefit**: Quantitative measurement of narrator quality improvements.

---

## Phase 5: Specific Issues

### 5.1 Fix "gaze" Vocabulary Entry

**Problem**: "gaze into ball" doesn't work, should be handled by crystal ball custom handler.

**Investigation**:
1. Find crystal ball behavior module
2. Check vocabulary definition
3. Verify "gaze" is defined as synonym for "peer"
4. Test vocabulary merging

**Files to check**:
- examples/spatial_game/behaviors/crystal_ball.py (or similar)
- examples/spatial_game/vocabulary.py

---

### 5.2 Investigate "look at door" vs "look at down" Discrepancy

**Evidence**:
- "look at down" works perfectly (describes stairs from top perspective) ✅
- "look at ornate door" gets confused about spatial relationship ❌

**Hypothesis**:
- "look at down" examines the EXIT entity (has perspective variants)
- "look at ornate door" examines the DOOR ITEM entity (lacks spatial context)

**Investigation**:
1. Find how "examine" command maps "door" to entities
2. Check if it resolves to door item vs exit
3. Verify exit entities have proper perspective variants
4. May need to improve door examination to use exit perspective

**Files to check**:
- Command handler for "examine" / "look at"
- Exit serialization logic

---

## Phase 6: Testing and Validation

### 6.1 Regression Testing

**Before implementing changes**:
1. Run full spatial_game walkthrough
2. Capture baseline narration
3. Note current error rate

**After each phase**:
1. Run same walkthrough
2. Compare narration
3. Verify improvements without regressions

**Metrics to track**:
- Material hallucination count (target: 0)
- Word duplication count (target: 0)
- Perspective switches (target: <5%)
- "Must mention" leaks (target: 0)
- Exit mention frequency (should reduce by ~60%)

---

### 6.2 Create Test Walkthroughs

**Minimal test** (covers transcript issues):
```
stand on bench
climb tree
look
take star
down
north
examine stairs
look
examine door
unlock door
open door
up
examine ball
peer into ball
take key
```

**Expanded test** (add more entities):
```
examine mat
examine stand
take umbrella
examine trowel
south
examine bench
```

---

### 6.3 Quality Criteria for Completion

A phase is complete when:

✅ **No material hallucinations**
   - Bench is always stone (never wood)
   - Mat is always fabric (never wood)
   - Key is always golden (never rusty/iron)
   - Door materials match entity traits

✅ **No word duplication**
   - No "ball ball", "hall hall", "swirls swirl"

✅ **Consistent perspective**
   - <5% perspective switches in spatial_game (first person required)

✅ **No field leakage**
   - Zero occurrences of "Must mention:", "entity_refs:", etc.

✅ **Appropriate exit mentions**
   - Exits on first visit, look command
   - No exits on examine, take, etc.

✅ **No language switching**
   - 100% English output

---

## Success Metrics

### Quantitative Goals

| Metric | Baseline (Current) | Target | Measurement |
|--------|-------------------|--------|-------------|
| Material hallucinations | ~4 per playthrough | 0 | Count wrong materials |
| Word duplications | ~3 per playthrough | 0 | Regex search |
| Perspective switches | ~40% of narrations | <5% | Count "I" vs "You" |
| Field name leaks | ~1-2 per playthrough | 0 | Search for "must_mention" etc |
| Exit over-mention | 100% of scenes | ~40% of scenes | Count exit appearances |
| Language switches | Rare but critical | 0 | Detect non-English |

### Qualitative Goals

- Narration uses authored traits when available
- Generic but reasonable when traits missing
- Natural language flow (not robotic)
- Appropriate detail level (full vs brief)
- Immersive and consistent perspective

---

## Risk Mitigation

### Risk: Breaking Working Cases

**Mitigation**:
- Run regression tests before/after each change
- Git commits after each working phase
- Keep old prompts in docs for comparison

### Risk: 7B Model Limitations

**Observation**: Model sometimes breaks into Chinese, duplicates words.

**Mitigation**:
- Clearer, more explicit prompts with negative examples
- Consider if larger model would help (out of scope for this plan)
- Focus on reducing confusion in input (better entity_refs)

### Risk: Over-engineering

**Mitigation**:
- Implement phases in priority order
- Measure impact of each change
- Stop when quality criteria met

---

## Phased Implementation Schedule

### Phase 1: Critical Fixes (Week 1)
- [x] 1.1: Fix missing entity_refs in handlers
- [x] 1.2: Fix must_mention field leakage
- [x] 1.3: Reduce must_mention frequency
- [ ] 1.4: Investigate primary_text exits duplication

**Deliverable**: Material hallucinations eliminated, field leakage stopped

### Phase 2: Authoring (Week 1-2)
- [ ] 2.1: Audit spatial_game entities
- [ ] 2.2: Extract traits from descriptions
- [ ] 2.3: Priority entities (mat, bench, key, door)
- [ ] 2.4: Document pattern

**Deliverable**: All spatial_game entities have traits

### Phase 3: Narrator Prompt (Week 2)
- [ ] 3.1: Strengthen perspective requirement
- [ ] 3.2: Add negative examples
- [ ] 3.3: Clarify trait usage
- [ ] 3.4: Simplify must_mention instruction

**Deliverable**: Improved narrator compliance

### Phase 4: Diagnostics (Week 2)
- [ ] 4.1: Add entity_refs validation
- [ ] 4.2: Create quality test suite
- [ ] 4.3: Expand evaluation harness

**Deliverable**: Automated quality checks

### Phase 5: Specific Issues (Week 2-3)
- [ ] 5.1: Fix "gaze" vocabulary
- [ ] 5.2: Investigate door examination

**Deliverable**: Edge cases resolved

### Phase 6: Validation (Week 3)
- [ ] 6.1: Regression testing
- [ ] 6.2: Create test walkthroughs
- [ ] 6.3: Verify quality criteria met

**Deliverable**: Documented quality improvement

---

## Open Questions

1. **primary_text exits**: Where is the engine-generated location description created? Need to find code that builds "Tower Entrance\nYou are in...\nExits: ..." string.

2. **Bench traits mystery**: Why does bench have traits for "look" but not "stand"? Is this handler bug or authoring gap?

3. **Exit architecture**: In new exit system, how does "examine door" vs "examine up" map to entities? Need to understand examination routing.

4. **Perspective in brief mode**: Does brief mode need different perspective handling? Observed less switching in brief.

5. **Model limitations**: At what point do we accept 7B model can't do better? Is there a larger model option?

---

## Appendix A: File Reference

### Core Files to Modify

**Narrator Protocol**:
- `docs/Narration/unified_narrator_prompt_revised_api.md` - Main narrator prompt

**Context Building**:
- `src/narration_assembler.py` - Builds narration context from handler results
- `utilities/entity_serializer.py` - Serializes entities for narrator

**Handlers** (investigation needed for exact paths):
- `behaviors/core/spatial.py` - Stand, sit, climb handlers
- `examples/spatial_game/behaviors/crystal_ball.py` - Peer/gaze handler

**Game Data**:
- `examples/spatial_game/game_state.json` - Entity definitions and traits
- `examples/spatial_game/vocabulary.py` - Game vocabulary

**Testing**:
- `tools/narrator_eval_harness.py` - Evaluation framework
- `tools/test_narration_quality.py` - To be created

---

## Appendix B: Example Improvements

### Before (Broken)
```
> stand on bench
You step onto the bench, feeling a bit wobbly as you gain your footing.
The wood is rough under your feet, and you can see the wear from years of use.
```

Issues:
- ❌ Wrong material ("wood" vs stone)
- ❌ Hallucinated details not in traits

### After (Fixed)
```
> stand on bench
I step onto the weathered stone bench, its moss-covered surface cool under my feet.
The sturdy construction holds my weight easily as I gain my footing.
```

Improvements:
- ✅ Correct material (stone)
- ✅ Uses authored traits (weathered, moss-covered, cool, sturdy)
- ✅ Consistent first person

---

### Before (Field Leakage)
```
> north
You step onto the north stone path...

Must mention: Exits lead south (garden archway to Overgrown Garden),
east (wooden door), and up (spiral staircase to Wizard's Library).
```

Issues:
- ❌ Field name leaked ("Must mention:")

### After (Fixed)
```
> north
I follow the stone path north to the tower entrance. The entrance hall
opens before me, dust motes dancing in shafts of light. Exits lead south
to the garden, east through a wooden door, and up a spiral staircase.
```

Improvements:
- ✅ Natural integration of exits
- ✅ No field names
- ✅ Consistent first person

---

## Appendix C: Vocabulary Pattern for "gaze"

**Investigation target** (crystal_ball.py or similar):

```python
vocabulary: Dict[str, Any] = {
    "verbs": [
        {
            "word": "peer",
            "word_type": "verb",
            "event": "on_peer_crystal_ball",
            "object_required": True,
            "synonyms": ["gaze", "look"]  # Is "gaze" here?
        }
    ]
}
```

**Debugging steps**:
1. Check if "gaze" is in synonyms list
2. Verify event name matches handler function name
3. Test vocabulary merging with debug logging
4. Confirm parser recognizes "gaze into ball"

---

## Conclusion

This plan addresses all identified narration quality issues with concrete, testable solutions. The phased approach allows incremental validation and risk mitigation.

**Expected outcome**: Narration quality returns to pre-exit-migration levels (or better), with:
- Zero material hallucinations
- Consistent perspective
- Natural trait usage
- Appropriate exit mentions
- No field leakage

**Timeline**: 2-3 weeks for full implementation and validation.
