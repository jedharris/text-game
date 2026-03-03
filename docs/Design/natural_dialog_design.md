# Natural Dialog Integration Design

## Goal

Make NPC dialog feel more natural by:
1. Allowing conversational phrases to route to dialog topics (not just "ask X about Y")
2. Having the narrator compose dialog responses from structured data (not hard-coded summaries)

## Current State

### Command Parsing (LLM-based)
- `src/llm_command_parser.py` converts natural language to JSON action dicts
- Parser receives context: `location_objects`, `inventory`, `exits`
- Parser knows valid verbs including `ask`, `talk`

### Dialog System
- `behavior_libraries/dialog_lib/handlers.py` handles `ask` and `talk` commands
- Topics defined in NPC's `dialog_topics` property with keywords, prerequisites, effects
- Handler returns hard-coded `summary` string directly to player

### Architecture Principle
**Engine manages state, LLM narrates** - handlers return structured data, narrator composes prose.

## Design

### Part A: Expose Topics to Parser

**Objective**: Let the LLM parser route conversational phrases like "what happened to you?" to the appropriate dialog topic.

#### Changes to Parser Context

Modify the context builder to include available dialog topics for NPCs in the current location.

**File**: Where context is built for parser (likely in narrator or game engine)

```python
def build_parser_context(accessor, actor_id):
    # Existing context
    context = {
        "location_objects": [...],
        "inventory": [...],
        "exits": [...]
    }

    # NEW: Add dialog topics from NPCs in location
    topics = []
    location = accessor.get_actor(actor_id).location
    for actor in accessor.get_actors_at(location):
        if actor.id != actor_id:  # Not self
            dialog_topics = actor.properties.get("dialog_topics", {})
            if isinstance(dialog_topics, dict) and "handler" not in dialog_topics:
                # Data-driven topics - extract available topic names
                available = get_available_topics(dialog_topics, accessor, actor_id)
                topics.extend(available.keys())

    context["topics"] = topics
    return context
```

#### Update Parser System Prompt

**File**: `src/llm_command_parser.py`

Add topics to the user prompt template and add examples showing conversational → ask mapping:

```python
def _build_user_prompt(self, context, command):
    # ... existing ...
    topics = ', '.join(context.get('topics', [])) or 'none'

    return f"""Available objects: {location_objs}
Your inventory: {inventory}
Exits: {exits}
Dialog topics: {topics}

Command: "{command}"
..."""
```

Add examples to system prompt:
```
Dialog topics: injury, tracking, elara
Command: "what happened to you?"
Output: {"type": "command", "action": {"verb": "ask", "indirect_object": "injury"}}

Dialog topics: injury, tracking, elara
Command: "tell me about your injury"
Output: {"type": "command", "action": {"verb": "ask", "indirect_object": "injury"}}

Dialog topics: quest, reward, directions
Command: "what do you want me to do?"
Output: {"type": "command", "action": {"verb": "ask", "indirect_object": "quest"}}
```

Note: When no specific NPC is mentioned, handler already auto-targets the single NPC with dialog_topics.

### Part B: Structured Dialog Responses

**Objective**: Dialog handlers return structured data instead of hard-coded prose, letting narrator compose natural responses.

#### New Topic Data Structure

Replace `summary` with structured `response`:

```json
"injury": {
  "keywords": ["injury", "hurt", "wound", "happened"],
  "trust_delta": 1,
  "response": {
    "content": "beast_attack",
    "tone": "pained",
    "detail_level": "brief"
  }
}
```

The `summary` field is no longer supported.

The `content` key maps to author-defined response content in NPC's `llm_context`:

```json
"llm_context": {
  "traits": ["experienced hunter", "currently injured", ...],
  "dialog_responses": {
    "beast_attack": "attacked by beast while tracking, barely escaped",
    "elara_connection": "knows healer Elara, trusts her completely",
    "tracking_offer": "willing to teach tracking if player helps"
  }
}
```

#### Refactor Dialog Handler

**File**: `behavior_libraries/dialog_lib/handlers.py`

Change `handle_ask` to return structured data:

```python
def handle_ask(accessor, action) -> HandlerResult:
    # ... existing topic matching and state changes ...

    # Get topic response
    topic_config = topics[matched_topic]
    response_data = topic_config["response"]

    # Serialize NPC for narrator context
    npc_data = serialize_for_handler_result(target_npc, accessor, actor_id)

    return HandlerResult(
        success=True,
        primary=f"You ask {target_npc.name} about {matched_topic}.",
        data={
            "dialog": {
                "speaker": npc_data,
                "topic": matched_topic,
                "response": response_data,
                "trust_level": get_trust_level(target_npc),
                "relationship": get_relationship(target_npc, actor_id)
            }
        }
    )
```

**Note**: The `summary` field is removed entirely. All topics must use the new `response` structure.

#### Narrator Composition

The narrator receives structured dialog data and composes natural speech:

**Input to narrator**:
```json
{
  "action": "ask",
  "primary": "You ask Sira about injury.",
  "data": {
    "dialog": {
      "speaker": {
        "name": "Sira",
        "traits": ["experienced hunter", "currently injured", "grimacing in pain"],
        "dialog_responses": {
          "beast_attack": "attacked by beast while tracking, barely escaped"
        }
      },
      "topic": "injury",
      "response": {
        "content": "beast_attack",
        "tone": "pained",
        "detail_level": "brief"
      },
      "trust_level": "wary",
      "relationship": "stranger"
    }
  }
}
```

**Narrator composes** (example output):
> Sira shifts her weight, wincing. "Beast attack," she manages through gritted teeth. "Caught me off guard while I was tracking. Barely made it back."

The narrator uses:
- NPC traits to inform body language and voice
- Response content as the core information
- Tone to shape delivery
- Trust/relationship to calibrate openness

### Part C: Update Narrator Prompt

Add guidance for dialog composition to narrator system prompt:

```
## Dialog Responses

When the player asks an NPC about a topic, you receive:
- speaker: NPC with traits and dialog_responses
- topic: what was asked about
- response: {content, tone, detail_level}
- trust_level: how much NPC trusts player
- relationship: stranger/acquaintance/friend/etc

Compose the NPC's speech using:
1. The content from dialog_responses[response.content]
2. The tone (pained, cheerful, suspicious, etc.) to shape delivery
3. Trust level to determine how forthcoming they are
4. NPC traits to add characteristic mannerisms

Keep dialog natural - use contractions, interruptions, body language.
```

## Migration Strategy

### Phase 1: Parser Context (Part A)
1. Add topic extraction to parser context builder
2. Update LLM parser prompt with topic examples
3. Test with existing big_game NPCs
4. Verify "what happened?" routes to "ask about injury"

### Phase 2: Structured Responses + Content Migration (Parts B & C)
1. Add `data` field support to dialog handler (already done via EventResult.data)
2. Refactor `handle_ask` to return structured data (require `response` field)
3. Convert ALL big_game NPC dialog topics to new format
4. Add narrator prompt guidance for dialog composition
5. Remove `summary` field support entirely

### Phase 3: Testing & Documentation
1. Run walkthroughs to verify narration quality
2. Update authoring documentation with new format
3. Add validation that warns/fails on missing `response` field

## Testing

### Parser Routing Tests
```
# Input: "what happened to you?" with topics: [injury, tracking]
# Expected: {"verb": "ask", "indirect_object": "injury"}

# Input: "can you teach me to track?" with topics: [injury, tracking]
# Expected: {"verb": "ask", "indirect_object": "tracking"}

# Input: "hello" with topics: [injury, tracking]
# Expected: {"verb": "talk"} or greeting handling
```

### Dialog Response Tests
```python
def test_structured_dialog_response():
    # Setup NPC with new response format
    # Call handle_ask
    # Verify HandlerResult.data contains dialog structure
    # Verify narrator receives and can compose from data
```

### Narration Quality Tests
- Run walkthrough with dialog interactions
- Verify narrator produces natural-sounding speech
- Check trust/tone affects output appropriately

## No Backward Compatibility

Per project guidelines, we do not maintain backward compatibility. The `summary` field is removed entirely:
- All topics must use the new `response` structure
- Handler will fail loudly if `response` field is missing
- Parser gracefully handles locations without dialog NPCs
- All big_game NPCs must be migrated as part of implementation

## Files to Modify

1. `src/llm_command_parser.py` - Add topics to prompt, add examples
2. Context builder (TBD location) - Extract topics from nearby NPCs
3. `behavior_libraries/dialog_lib/handlers.py` - Return structured data
4. `behavior_libraries/dialog_lib/topics.py` - Support new response format
5. Narrator prompt - Add dialog composition guidance
6. `examples/big_game/game_state.json` - Migrate NPC dialog topics (Phase 4)

## Open Questions

1. **Topic discovery**: Should we show available topics in location description, or let players discover through conversation?

2. **Implicit NPC**: When player says "what happened?" without naming NPC, parser returns `indirect_object: "injury"` without `object`. Handler already supports auto-targeting - confirm this works.

3. **Multi-NPC locations**: If multiple NPCs have the same topic keyword, how to disambiguate? Current system auto-targets only when single NPC present.

4. **Response variations**: Should `dialog_responses` support multiple variants per content key for variety? E.g., `"beast_attack": ["attacked by beast...", "beast got me...", ...]`
