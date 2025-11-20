# LLM Frontend Design for Text Adventure Engine

## Core Architecture

```
Player Input (natural language)
    ↓
LLM Agent (function calling)
    ↓
Game Engine API (existing state manager + operations)
    ↓
Structured Results
    ↓
LLM Narrator (with context from game state)
    ↓
Rich Description (to player)
```

## Key Principles

1. **LLM as Interface, Not Engine**: LLM interprets intent and renders output, but never modifies game state directly through gameplay logic
2. **Function Calling Pattern**: LLM calls game engine functions with structured parameters
3. **Constrained Context**: LLM receives only current-state information to prevent hallucination
4. **Canonical Resources**: Game state stores the "source of truth" for descriptions
5. **Guided Augmentation**: LLM can propose new descriptive resources that are validated for consistency before being added to game state

## Extended Game State Schema

Add new fields to existing entities:

```json
{
  "locations": [{
    "id": "loc_1",
    "name": "Crypt Entrance",
    "description": "A marble archway...",  // Existing base description
    
    // NEW: LLM context resources
    "llm_context": {
      "canonical_traits": [
        "marble archway",
        "darkness beyond",
        "weathered stone"
      ],
      "atmosphere": "foreboding, ancient, abandoned",
      "sensory_details": {
        "sight": "dust motes in dim light",
        "sound": "distant water dripping",
        "smell": "damp stone and earth"
      },
      "variation_seeds": [
        "mention ravens circling overhead",
        "note cold draft from within",
        "describe moss on stones"
      ]
    }
  }],
  
  "items": [{
    "id": "item_1",
    "name": "Silver Key",
    "description": "A key with a raven-shaped bow.",
    
    "llm_context": {
      "canonical_traits": [
        "raven-shaped bow",
        "tarnished silver",
        "surprisingly heavy"
      ],
      "history_hints": "ancient, ceremonial, important",
      "state_variants": {
        "in_location": "gleams dully in the shadows",
        "in_inventory": "cold weight in your pocket",
        "being_examined": "intricate engravings visible up close"
      }
    }
  }],
  
  "npcs": [{
    "id": "npc_1",
    "name": "Ghostly Guard",
    
    "llm_context": {
      "canonical_traits": [
        "translucent armor",
        "hollow eyes",
        "silent vigil"
      ],
      "personality": "stern but not hostile, bound by duty",
      "speech_style": "archaic, formal, cryptic",
      "emotional_states": {
        "default": "watching, waiting",
        "approached": "alert, questioning",
        "given_key": "relieved, grateful"
      }
    }
  }]
}
```

## LLM Resource Augmentation System

### Overview

The LLM can propose new descriptive resources to enhance game entities. All proposals are validated for consistency before being added to game state. This serves two purposes:

1. **Authoring Aid**: Help game authors rapidly flesh out sparse descriptions
2. **Gameplay Enrichment**: Reveal new details as players interact with the world

### Augmentation Modes

#### Authoring Mode
- LLM aggressively proposes enrichments
- Lower consistency threshold (allow creative additions)
- Author reviews and approves proposals
- Batch operations for efficiency

#### Gameplay Mode
- LLM conservatively proposes enrichments
- Higher consistency threshold (strict validation)
- Optional auto-approval for minor additions
- Rate-limited to prevent spam

### Resource Proposal Schema

When LLM wants to add descriptive resources, it generates a proposal:

```json
{
  "proposal_id": "prop_001",
  "target_entity": {
    "type": "item",
    "id": "item_1"
  },
  "augmentation_type": "add_canonical_trait",
  "proposed_content": {
    "canonical_trait": "bears maker's mark: three intertwined circles",
    "category": "detail",
    "context": "revealed upon close examination"
  },
  "justification": "Player examined key 3 times, warrants additional detail",
  "consistency_check": {
    "conflicts_with": [],
    "compatible_with": ["raven-shaped bow", "tarnished silver"],
    "confidence": 0.95
  }
}
```

### Consistency Validation Rules

Before accepting a proposal, validate against existing resources:

```python
class ConsistencyValidator:
    """Validates proposed augmentations don't contradict existing state."""
    
    def validate_proposal(self, proposal, entity, game_state):
        """
        Checks:
        1. No direct contradictions with canonical_traits
        2. Compatible with atmosphere/personality
        3. Doesn't invalidate previous descriptions
        4. Fits within game world logic
        5. Appropriate level of detail
        """
        
        checks = [
            self.check_trait_compatibility(proposal, entity),
            self.check_logical_consistency(proposal, game_state),
            self.check_detail_appropriateness(proposal, entity),
            self.check_no_contradictions(proposal, entity)
        ]
        
        return ValidationResult(
            approved=all(checks),
            issues=[c for c in checks if not c.passed],
            confidence=min(c.confidence for c in checks)
        )
```

### Validation Examples

#### ✅ Valid Augmentation
**Existing traits:** `["raven-shaped bow", "tarnished silver"]`  
**Proposal:** `"three small scratches on the shaft"`  
**Validation:** Compatible - adds detail without contradicting  
**Result:** APPROVED

#### ❌ Invalid Augmentation - Contradiction
**Existing traits:** `["tarnished silver", "surprisingly heavy"]`  
**Proposal:** `"lightweight aluminum construction"`  
**Validation:** Contradicts "tarnished silver" (aluminum doesn't tarnish the same way) and "surprisingly heavy"  
**Result:** REJECTED - Material contradiction

#### ⚠️ Questionable Augmentation - Review
**Existing traits:** `["ancient", "ceremonial"]`  
**Proposal:** `"battery-powered LED embedded in handle"`  
**Validation:** Anachronistic for setting  
**Result:** FLAG FOR REVIEW - Violates world logic

### Augmentation Categories

Proposals are categorized by type and impact:

```json
{
  "augmentation_categories": {
    "canonical_trait": {
      "impact": "high",
      "requires_approval": true,
      "examples": ["physical features", "material properties"]
    },
    "sensory_detail": {
      "impact": "medium", 
      "requires_approval": "authoring_only",
      "examples": ["sounds", "smells", "textures"]
    },
    "variation_seed": {
      "impact": "low",
      "requires_approval": false,
      "examples": ["alternate phrasings", "contextual mentions"]
    },
    "history_hint": {
      "impact": "medium",
      "requires_approval": true,
      "examples": ["background story", "origin clues"]
    }
  }
}
```

### Augmentation Workflow

#### During Authoring

```python
class AuthoringAssistant:
    """Helps authors enrich game content."""
    
    async def enrich_entity(self, entity_id, depth="full"):
        """
        Generate comprehensive enrichments for entity.
        
        depth options:
        - "minimal": Just fill missing canonical_traits
        - "standard": Add sensory details and variations
        - "full": Complete LLM context with history/personality
        """
        
        # Get entity and existing context
        entity = self.game_state.get_entity(entity_id)
        existing = entity.llm_context
        
        # Generate proposals
        proposals = await self.llm.propose_enrichments(
            entity=entity,
            existing_context=existing,
            depth=depth
        )
        
        # Validate each proposal
        validated = [
            (p, self.validator.validate_proposal(p, entity, self.game_state))
            for p in proposals
        ]
        
        # Present to author for review
        return self.create_review_ui(validated)
```

**Example Authoring Session:**

```
Author: enrich item_1 --depth=full

LLM Analysis:
Current traits: ["raven-shaped bow", "tarnished silver"]
Gaps identified: sensory details, history, state variants

Proposals:
✅ Canonical trait: "cold to the touch" [APPROVED]
✅ Sensory (touch): "smooth despite age" [APPROVED]
✅ History hint: "forged in the old kingdom" [APPROVED]
⚠️  Canonical trait: "glows faintly in moonlight" [REVIEW - magical property]

Review required for 1 proposal. Accept? (y/n/edit)
```

#### During Gameplay

```python
class GameplayEnricher:
    """Enriches descriptions based on player interactions."""
    
    def __init__(self, auto_approve_threshold=0.90):
        self.auto_approve_threshold = auto_approve_threshold
        self.enrichment_cooldown = {}  # Rate limiting
        
    async def consider_enrichment(self, entity, interaction_count):
        """
        Consider adding detail based on player attention.
        
        Triggers:
        - Entity examined multiple times (3+)
        - Entity central to current puzzle
        - Player explicitly seeks more detail
        """
        
        # Check if enrichment warranted
        if not self.should_enrich(entity, interaction_count):
            return None
            
        # Generate conservative proposal
        proposal = await self.llm.propose_detail(
            entity=entity,
            context="player_repeated_examination",
            conservativeness="high"
        )
        
        # Validate strictly
        validation = self.validator.validate_proposal(
            proposal, entity, self.game_state
        )
        
        if validation.confidence >= self.auto_approve_threshold:
            # Auto-approve high-confidence additions
            self.apply_enrichment(proposal)
            return proposal
        else:
            # Log for game author review
            self.log_for_review(proposal, validation)
            return None
```

**Example Gameplay Enrichment:**

```
Player: > examine key
You see a tarnished silver key with a raven-shaped bow.

Player: > examine key closely
[LLM detects repeated examination - considers enrichment]
[Proposes: "notice intricate feather details on raven"]
[Validates: Compatible with "raven-shaped bow", no contradictions]
[Confidence: 0.95 - AUTO APPROVED]
[Augmentation applied to game state]

You look more closely at the key. The raven-shaped bow reveals intricate 
feather details you hadn't noticed before, each one delicately etched into 
the tarnished silver.

[New canonical trait added: "intricate feather details on raven"]
```

### Provenance Tracking

Track when and why resources were added:

```json
{
  "llm_context": {
    "canonical_traits": [
      {
        "trait": "raven-shaped bow",
        "source": "authored",
        "added": "2024-01-15T10:00:00Z",
        "author": "game_designer"
      },
      {
        "trait": "intricate feather details",
        "source": "llm_enrichment",
        "added": "2024-01-20T15:30:00Z",
        "trigger": "player_repeated_examination",
        "confidence": 0.95,
        "review_status": "auto_approved"
      }
    ]
  }
}
```

### Rollback and Review

Authors can review and rollback LLM additions:

```python
class AugmentationManager:
    """Manages LLM-added content."""
    
    def list_llm_additions(self, entity_id=None, since=None):
        """List all LLM-added content with filters."""
        
    def review_addition(self, addition_id):
        """Review a specific addition with context."""
        
    def rollback_addition(self, addition_id):
        """Remove an LLM addition and its consequences."""
        
    def approve_pending(self, addition_id):
        """Approve a pending addition (moves to permanent)."""
        
    def export_additions(self, format="json"):
        """Export LLM additions for backup/migration."""
```

### Configuration

Game-wide settings for augmentation behavior:

```json
{
  "augmentation_config": {
    "authoring_mode": {
      "enabled": true,
      "auto_approve_threshold": 0.70,
      "allow_creative_additions": true,
      "batch_operations": true
    },
    "gameplay_mode": {
      "enabled": true,
      "auto_approve_threshold": 0.95,
      "max_enrichments_per_entity": 3,
      "cooldown_per_entity": "30_minutes",
      "require_player_attention": true
    },
    "validation": {
      "strict_consistency": true,
      "check_world_logic": true,
      "flag_anachronisms": true
    }
  }
}
```

## Two-Phase LLM Architecture

### Phase 1: Intent Parser (Function Calling)

**System Prompt:**
```
You are the command interpreter for a text adventure game. 
Parse player intent and call game engine functions.

Available functions:
- move_player(direction: str)
- examine_object(object_name: str)
- take_item(item_name: str)
- talk_to_npc(npc_name: str)
- use_item(item_name: str, target: str)

CRITICAL: You MUST call exactly one function. Never simulate game state.
If unclear, call clarify_intent() and ask the player.
```

**Input:** "I want to pick up that silver thing and check out the door"

**LLM Output:** 
```json
{
  "functions": [
    {"name": "take_item", "args": {"item_name": "silver key"}},
    {"name": "examine_object", "args": {"object_name": "door"}}
  ]
}
```

### Phase 2: Narrator (Response Generation)

**System Prompt:**
```
You are the narrator for a text adventure game.
Generate rich, immersive descriptions based on game state and context.

RULES:
1. Use ONLY information from canonical_traits - never invent details
2. Vary language but keep facts consistent
3. Reflect current game state in descriptions
4. Use atmosphere/sensory details to enrich output
5. Never contradict previous descriptions
```

**Input Context:**
```json
{
  "action_taken": "take_item",
  "result": {
    "success": true,
    "item": {
      "name": "Silver Key",
      "canonical_traits": ["raven-shaped bow", "tarnished silver"],
      "state_variants": {"in_inventory": "cold weight in your pocket"}
    }
  },
  "current_location": {
    "name": "Crypt Entrance",
    "atmosphere": "foreboding, ancient"
  }
}
```

**LLM Output:**
```
You pick up the tarnished silver key. Its raven-shaped bow is cold against 
your palm, and you feel the unexpected weight of it as you slip it into 
your pocket. In the gloom of the crypt entrance, you sense this is no 
ordinary key.
```

## Implementation Components

### 1. Context Builder
```python
class LLMContextBuilder:
    """Builds constrained context for LLM from current game state."""
    
    def build_narrator_context(self, game_state, action_result):
        """
        Extracts only relevant context for narration:
        - Current location's llm_context
        - Visible items' llm_context  
        - Nearby NPCs' llm_context
        - Action result details
        """
        
    def build_intent_context(self, game_state):
        """
        Context for intent parser:
        - Available actions at current location
        - Visible/accessible objects
        - Current inventory
        """
        
    def build_enrichment_context(self, entity, game_state):
        """
        Context for resource augmentation:
        - Entity's existing llm_context
        - Related entities (container, location, etc.)
        - Player interaction history with entity
        - World constraints and tone
        """
```

### 2. LLM Agent Controller
```python
class LLMGameController:
    """Mediates between LLM and game engine."""
    
    def __init__(self, game_state, llm_client, mode="gameplay"):
        self.state = game_state
        self.llm = llm_client
        self.context_builder = LLMContextBuilder()
        self.enricher = GameplayEnricher() if mode == "gameplay" else AuthoringAssistant()
        
    async def process_player_input(self, player_text):
        # Phase 1: Parse intent → functions
        intent_context = self.context_builder.build_intent_context(self.state)
        functions = await self.llm.parse_intent(player_text, intent_context)
        
        # Execute on game engine
        results = []
        for func in functions:
            result = self.execute_game_function(func)
            results.append(result)
            
            # Check if enrichment warranted
            if func.name == "examine_object":
                enrichment = await self.enricher.consider_enrichment(
                    entity=func.target,
                    interaction_count=self.state.get_interaction_count(func.target)
                )
                if enrichment:
                    results.append(enrichment)
        
        # Phase 2: Narrate results (using potentially enriched context)
        narrator_context = self.context_builder.build_narrator_context(
            self.state, results
        )
        response = await self.llm.narrate(narrator_context)
        
        return response
```

### 3. Consistency Validator
```python
class ConsistencyValidator:
    """Validates LLM output doesn't contradict canonical facts."""
    
    def validate_narration(self, llm_output, canonical_context):
        """
        Check that LLM description:
        - Uses only canonical_traits
        - Doesn't introduce new facts
        - Reflects current game state correctly
        """
        
    def validate_proposal(self, proposal, entity, game_state):
        """
        Validate proposed resource augmentation:
        - No contradictions with existing traits
        - Compatible with entity's nature
        - Fits world logic and tone
        - Appropriate detail level
        Returns ValidationResult with confidence score
        """
        
    def check_trait_compatibility(self, new_trait, existing_traits):
        """Ensure new trait doesn't contradict existing ones."""
        
    def check_logical_consistency(self, proposal, game_state):
        """Ensure proposal fits world logic (no anachronisms, etc.)."""
```

### 4. Augmentation Manager
```python
class AugmentationManager:
    """Manages LLM-added content and reviews."""
    
    def apply_enrichment(self, proposal, entity_id):
        """
        Apply validated enrichment to game state.
        Tracks provenance and allows rollback.
        """
        
    def list_llm_additions(self, filters=None):
        """List all LLM-added content for review."""
        
    def rollback_addition(self, addition_id):
        """Remove an LLM addition from game state."""
        
    def export_augmentations(self, entity_id=None):
        """Export LLM additions for version control."""
```

## Example Flow

**Player:** "I want to unlock the ornate door with that key I found"

**Intent Parser LLM:**
```json
{"function": "use_item", "args": {"item": "silver key", "target": "door"}}
```

**Game Engine:**
```python
result = {
    "success": True,
    "door_unlocked": True,
    "message": "The lock clicks open"
}
```

**Narrator Context:**
```json
{
  "action": "use_item_on_door",
  "success": true,
  "item_context": {
    "canonical_traits": ["raven-shaped bow", "fits lock perfectly"]
  },
  "door_context": {
    "canonical_traits": ["raven sigil on lock", "heavy iron gate"],
    "state_change": "locked → unlocked"
  }
}
```

**Narrator LLM Output:**
```
You slide the silver key into the lock, and the raven-shaped bow aligns 
perfectly with the raven sigil. With a satisfying click, the ancient 
mechanism surrenders, and the heavy iron gate stands ready to open.
```

## Benefits

✅ **Consistency**: Canonical traits prevent contradictions  
✅ **Variability**: LLM can vary language while preserving facts  
✅ **Control**: Game engine maintains authority over state  
✅ **Richness**: Context resources enable detailed descriptions  
✅ **Debuggable**: Structured function calls are auditable  
✅ **Extensible**: Easy to add new context types  
✅ **Authoring Aid**: LLM rapidly enriches sparse content with validation  
✅ **Living World**: Descriptions deepen naturally as players explore  
✅ **Reversible**: All LLM additions tracked and can be rolled back  
✅ **Provenance**: Clear tracking of authored vs. LLM-generated content  

## Migration Path

### Phase 1: Foundation
1. Add `llm_context` fields to existing game state schema
2. Build context extractor for current game state
3. Implement consistency validator core logic
4. Create augmentation tracking schema

### Phase 2: Core LLM Integration
1. Implement intent parser with function calling
2. Implement narrator with constrained context
3. Test basic LLM gameplay loop
4. Add validator to catch hallucinations

### Phase 3: Augmentation System
1. Implement resource proposal schema
2. Build consistency validation rules
3. Create authoring mode with review UI
4. Implement gameplay mode with auto-approval
5. Add provenance tracking

### Phase 4: Enrichment & Testing
1. Use authoring mode to enrich existing game content
2. Test gameplay enrichments with real players
3. Tune auto-approval thresholds
4. Build rollback and review tools

### Phase 5: Production
1. Set appropriate rate limits
2. Configure per-game augmentation policies
3. Add monitoring for bad augmentations
4. Document best practices for authors

## Practical Authoring Workflows

### Workflow 1: Bootstrap New Entity

**Starting Point:** Minimal JSON entry
```json
{
  "id": "item_5",
  "name": "Ancient Compass",
  "description": "An old brass compass.",
  "type": "tool",
  "portable": true
}
```

**Authoring Session:**
```
Author: enrich item_5 --mode=interactive

AI: Analyzing "Ancient Compass"...
    Base description: "An old brass compass."
    Type: tool, portable
    
    Suggested canonical traits:
    ✓ brass casing, tarnished
    ✓ glass face, slightly cracked
    ✓ needle oscillates strangely
    
    Accept all? (y/n/review): review
    
Author: accept 1,2 reject 3

AI: Accepted. Additional suggestions?
    
    Sensory details:
    ✓ cool metal weight
    ✓ faint clicking sound when moved
    
    Accept? y
    
AI: History hints?

Author: yes - it belonged to a famous explorer

AI: Generated:
    ✓ "carried by Captain Thorne on his final voyage"
    
    Validate against world: PASS (Captain Thorne exists in game lore)
    Accept? y
    
AI: Final review:
    Canonical traits (3): brass casing, glass face cracked, cool weight
    Sensory details (2): metal coolness, clicking sound  
    History (1): Captain Thorne's compass
    
    Save to game state? y
    
    ✅ item_5 enriched! Preview:
    [The old brass compass rests cool and heavy in your palm, its 
     cracked glass face revealing the needle that once guided 
     Captain Thorne. A faint clicking accompanies its movements.]
```

### Workflow 2: Enrich Existing Sparse World

**Batch Mode:**
```
Author: enrich all --filter=missing_llm_context --auto-approve=0.9

AI: Scanning game state...
    Found 47 entities missing LLM context
    
    Processing locations (12)...
    ✓ loc_1: Added atmosphere + sensory details [auto]
    ✓ loc_2: Added atmosphere + sensory details [auto]
    ⚠ loc_3: Proposed magical trait [REVIEW REQUIRED]
    
    Processing items (23)...
    ✓ item_1-5: Added traits + state variants [auto]
    ✓ item_6: Added sensory details [auto]
    ⚠ item_7: Anachronistic detail detected [REVIEW]
    
    Processing NPCs (12)...
    ✓ npc_1-8: Added personality + speech style [auto]
    ✓ npc_9-12: Added emotional states [auto]
    
    Summary:
    - Auto-approved: 44 entities
    - Require review: 3 entities
    - Estimated time saved: 6 hours
    
    Review flagged items? y
```

### Workflow 3: Iterative Refinement

**Refine Existing Context:**
```
Author: refine item_1 --aspect=atmosphere

AI: Current atmosphere: "ancient, mysterious"
    Seems generic. Suggestions:
    
    Option A: "laden with untold secrets"
    Option B: "whispers of forgotten power"  
    Option C: "cold indifference of ages"
    
Author: B

AI: Updated. Related adjustments needed:
    - Sensory details could reference "whispers"
    - History hints could mention "power"
    
    Apply related changes? y
    
    ✅ item_1 refined with thematic consistency
```

### Workflow 4: Consistency Check Across World

**Cross-Entity Validation:**
```
Author: validate-consistency --scope=all

AI: Checking consistency across 87 entities...
    
    ✓ All canonical traits validated
    ✓ No contradictory atmospheres
    ⚠ Potential inconsistencies found (2):
    
    1. item_3 "silver key" vs door_1 "golden lock"
       Metals don't match but both are "raven themed"
       Suggestion: Change key to gold OR note key is special
       
    2. npc_2 personality "jovial" in location with
       atmosphere "oppressive, dark"
       Suggestion: Adjust NPC emotional state in this location
       
    Fix automatically? (y/n/review): review
```

## Design Rationale

### Why Two-Phase Architecture?

**Separation of Concerns:**
- Intent parsing requires understanding player goals
- Narration requires creative storytelling
- Different prompts optimize for different tasks

**Error Isolation:**
- Intent parser errors are caught before state changes
- Narrator hallucinations don't affect game state
- Easier to debug and improve each component

**Flexibility:**
- Can swap LLM models per phase (fast for intent, creative for narration)
- Can add validation between phases
- Can log and analyze each phase independently

### Why Canonical Traits?

**Consistency Problem:**
Without constraints, LLMs will describe the "silver key" differently each time:
- First time: "ornate silver key with intricate engravings"
- Second time: "simple tarnished key with a raven design"
- Third time: "heavy iron key shaped like a bird"

**Solution:**
Canonical traits in game state ensure the LLM always has the same facts:
```json
"canonical_traits": ["raven-shaped bow", "tarnished silver", "surprisingly heavy"]
```

LLM can vary *language* but not *facts*:
- "The tarnished silver key feels heavy in your hand, its raven-shaped bow gleaming..."
- "You examine the heavy key, noting the raven design on its silver surface..."

### Why Not Let LLM Manage State?

**Problems with LLM State Management:**
- LLMs hallucinate and forget
- No transaction guarantees
- Can't enforce game rules consistently
- Difficult to save/load
- Hard to debug

**Game Engine State Management:**
- Deterministic
- Validates all operations
- Easy to save/load
- Clear audit trail
- Enforces game rules

## Future Enhancements

### Collaborative Authoring
Multiple LLM passes to refine content:
```python
# First pass: Generate initial enrichment
# Second pass: Review for consistency
# Third pass: Suggest improvements
```

### Player-Driven Discovery
Track what players find interesting and enrich accordingly:
```json
"player_attention_metrics": {
  "item_1": {
    "examinations": 5,
    "last_examined": "2024-01-20T15:30:00Z",
    "enrichment_potential": "high"
  }
}
```

### Cross-Entity Consistency
Ensure related entities have compatible descriptions:
```python
# If key has "raven-shaped bow"
# And door has "raven sigil"
# LLM should maintain this connection in descriptions
```

### Procedural Content Generation
Use validated augmentation system to generate new content:
```python
# Generate new location with full LLM context
# Each trait validated before acceptance
# Author reviews and approves final result
```

### Learning from Player Feedback
Track player reactions to enriched descriptions:
```json
"enrichment_feedback": {
  "addition_id": "enrich_042",
  "player_responses": ["examine again", "take item"],
  "engagement_score": 0.85
}
```

## Technical Considerations

### Latency
- Intent parsing: ~500ms
- Game engine operations: <50ms
- Narration: ~1000ms
- **Total: ~1.5s per action**

Optimizations:
- Cache common intent patterns
- Pre-generate narrative templates
- Stream narrator output to player

### Cost
- Intent parser: Small prompt, cheap model (GPT-4-mini)
- Narrator: Larger context, premium model (GPT-4)
- **Estimated: $0.01-0.05 per player action**

### Offline Mode
- Fallback to template-based descriptions when LLM unavailable
- Use base `description` field from game state
- Alert player that "enhanced narration unavailable"

## Related Documents

- [game_state_spec.md](game_state_spec.md) - Base schema to be extended
- [state_manager_plan.md](state_manager_plan.md) - State management implementation
- [entity_behaviors.md](entity_behaviors.md) - Event system that LLM will trigger
- [command_design.md](command_design.md) - Parser that LLM replaces

## Open Questions

### Core System Questions

1. **How much context to include?**
   - Just current location? Entire game history?
   - Balance: More context = better narration but slower/costlier

2. **How to handle ambiguity?**
   - Player: "use it" - which item?
   - LLM clarifies or game engine requires explicit reference?

3. **How to version canonical traits?**
   - Player discovers new information about item
   - Add to canonical_traits or separate "known_facts"?

4. **How to handle player creativity?**
   - Player: "I light the torch using the magic ring"
   - LLM should recognize intent but game engine validates possibility

5. **Multi-action commands?**
   - Player: "take the key, unlock the door, and go through"
   - Execute sequentially? Confirm before executing?

### Augmentation System Questions

6. **What's the right auto-approval threshold?**
   - 0.95 seems safe but might be too conservative
   - Could vary by augmentation category?

7. **How to handle conflicting proposals?**
   - LLM proposes "glowing" but existing atmosphere is "dark and foreboding"
   - Reject or try to reconcile ("faintly glowing")?

8. **Should players know about enrichments?**
   - Transparent: "You notice new details..." 
   - Seamless: Just integrate naturally
   - Player preference setting?

9. **How to limit enrichment spam?**
   - Max 3 additions per entity seems reasonable
   - But what if player really wants more detail?
   - Progressive detail reveal system?

10. **How to handle rollbacks in multiplayer?**
    - If one player's actions cause enrichment
    - And another player sees it
    - Rollback affects both experiences?

11. **What's the enrichment lifecycle?**
    - Temporary (session only)?
    - Persistent (saved to game state)?
    - Graduated (temporary → reviewed → permanent)?

12. **How to credit LLM additions?**
    - Attribution in game credits?
    - "Enhanced by AI" notice?
    - Completely transparent to player?

## Success Criteria

The LLM integration is successful when:

### Core Functionality
1. ✅ Players can use natural language instead of rigid commands
2. ✅ Descriptions are rich and varied but factually consistent
3. ✅ Game state remains authoritative and debuggable
4. ✅ No hallucinated game mechanics or items
5. ✅ Response time acceptable (<2s per action)
6. ✅ System degrades gracefully when LLM unavailable

### Augmentation System
7. ✅ Authors can rapidly enrich content with LLM assistance
8. ✅ Gameplay enrichments feel natural, not forced
9. ✅ Consistency validation catches >95% of contradictions
10. ✅ Rollback system works reliably
11. ✅ Provenance tracking is complete and auditable
12. ✅ Auto-approval threshold produces <1% bad additions

### Authoring Experience
13. ✅ Authoring mode reduces content creation time by >50%
14. ✅ Review UI is intuitive and efficient
15. ✅ Batch operations speed up enrichment of large worlds

### Player Experience
16. ✅ Enrichments feel organic, not "tacked on"
17. ✅ Repeated examinations reveal appropriate new details
18. ✅ No player confusion from inconsistent descriptions
19. ✅ Players express delight at discovering new details

### Technical Metrics
20. ✅ Easy to author new content with LLM context
21. ✅ Existing game engine remains functional
22. ✅ Cost per enrichment <$0.01
23. ✅ Enrichment latency <500ms

## Conclusion

This design leverages LLM strengths (natural language understanding, creative narration, content generation) while maintaining game engine strengths (state management, rule enforcement, consistency). The two-phase architecture with canonical traits ensures rich, immersive gameplay without sacrificing the reliability and debuggability of traditional game engines.

The resource augmentation system provides a powerful tool for both game authoring and gameplay enrichment. By validating all LLM-proposed additions for consistency before accepting them, we can harness the LLM's creative power while preventing hallucinations and contradictions. This creates a living world that deepens naturally as players explore, while remaining under the author's control.

Key innovations:
- **Validated creativity**: LLM generates, validator ensures consistency
- **Dual-mode operation**: Aggressive enrichment for authoring, conservative for gameplay
- **Provenance tracking**: Complete audit trail of all additions
- **Reversibility**: Any LLM addition can be reviewed and rolled back
- **Gradual enrichment**: World becomes richer over time without overwhelming players

This approach makes the game world feel alive and responsive while maintaining the deterministic behavior and debuggability that make traditional game engines reliable.
