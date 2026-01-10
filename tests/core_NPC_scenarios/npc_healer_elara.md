# NPC: healer_elara (npc_healer_elara)

## Core Mechanics
- gossip_reactions: Receives gossip about player actions (Sira's death)
- dialog_reactions: Confession mechanics reduce gossip penalty
- Service NPC: Provides healing with trust gate (trust < -2 blocks service)
- trust_state: Modified by gossip (-2), confession (-1), player actions
- Confession timing: Pre-gossip confession reduces penalty

## Required Scenarios

### Success Path
1. **Confession Before Gossip (Reduced Penalty)**
   - Trigger Sira's death (see hunter_sira scenario 2)
   - Within 12-turn confession window, talk to Elara
   - Use confession keywords: "confess", "admit", "tell you", "must know", "truth"
   - Verify: extra.player_confessed_sira = true
   - Verify: Trust penalty applied immediately: -1
   - Verify: Confession feedback "told me yourself", "takes courage"
   - Wait for gossip to arrive (turn 12+)
   - Verify: Gossip handler sees confession flag
   - Verify: Total trust penalty remains -1 (not additional)
   - Verify: Elara still provides services (trust = -1, threshold is -2)

### Failure Paths
2. **Gossip Arrives Without Confession (Full Penalty)**
   - Trigger Sira's death
   - Do NOT talk to Elara about Sira
   - Wait 12+ turns for gossip to arrive
   - Verify: Gossip delivered via gossip_reactions
   - Verify: extra.player_confessed_sira = false or unset
   - Verify: Trust penalty: -2 (full penalty)
   - Verify: Gossip feedback "didn't tell me", anger/betrayal
   - Verify: Elara still provides services (trust = -2, at threshold)

3. **Services Blocked by Low Trust**
   - Accumulate trust penalties (multiple gossips or other negative actions)
   - Reduce trust below -2 (e.g., trust = -3)
   - Ask Elara for healing
   - Verify: Service refused
   - Verify: Feedback "can't help someone I don't trust"

### Edge Cases
4. **Confession After Gossip (Too Late)**
   - Trigger Sira's death
   - Wait 12+ turns (gossip arrives first)
   - Verify: Trust penalty -2 applied
   - Then try to confess
   - Verify: Confession may not apply or has no effect (gossip already processed)
   - Verify: Trust remains -2

5. **Multiple Gossip Types**
   - Receive Sira death gossip (scenario 2)
   - Trigger other negative gossip (e.g., abandonment gossip from other NPCs)
   - Verify: Trust accumulates multiple penalties
   - Verify: Services blocked when trust < -2

6. **Healing Service Success**
   - Maintain neutral or positive trust
   - Acquire negative conditions (bleeding, fungal_infection, poison)
   - Ask Elara for healing
   - Verify: Conditions removed from player.properties.conditions
   - Verify: Healing feedback lists treated conditions
   - Verify: Trust requirement checked before healing

7. **Healing When Already Healthy**
   - Maintain neutral/positive trust
   - Have no negative conditions
   - Ask Elara for healing
   - Verify: Feedback "You seem well"
   - Verify: No errors, graceful handling

### Skill Teaching Paths
8. **Basic Herbalism Teaching (Trust 2+)**
   - Build trust to 2+ (positive actions, no gossip penalties)
   - Pay 50g OR provide rare herb
   - Verify: basic_herbalism skill granted
   - Verify: Can identify dangerous plants
   - Verify: Supervised garden access unlocked

9. **Advanced Herbalism Teaching (Trust 3+)**
   - Build trust to 3+
   - Complete basic herbalism first
   - Pay 100g OR provide rare herb
   - Verify: advanced_herbalism skill granted
   - Verify: Can safely handle all herbs including nightshade
   - Verify: Can create healing items (potions, salves)
   - Verify: Unsupervised garden access

10. **Garden Access**
    - Basic herbalism OR trust 2+ with Maren
    - Verify: Can enter healer's garden (supervised)
    - Advanced herbalism OR trust 3+
    - Verify: Can harvest garden freely

### Trust Recovery
11. **Recovery from Gossip Penalty**
    - Have trust penalty from gossip
    - Perform positive actions (help NPCs, bring rare herbs)
    - Verify: Trust can recover over time
    - Verify: Rate limited (not instant)

12. **Aldric Rescue Bonus**
    - Save npc_aldric from Fungal Depths
    - Return to Civilized Remnants
    - Verify: Elara trust +1 (saved_aldric flag)
    - Verify: Dialog acknowledges rescue

## Dependencies
- **Items**:
  - Rare herbs (payment for teaching)
  - Gold (alternative payment)
- **NPCs**:
  - hunter_sira (gossip source about death)
  - npc_aldric (trust bonus if saved)
  - herbalist_maren (alternative basic herbalism source)
  - Potentially other NPCs that generate gossip to Elara
- **Mechanics**:
  - gossip_reactions infrastructure
  - gossip_delivery infrastructure (delayed gossip arrival)
  - dialog_reactions infrastructure (confession detection)
  - trust_state tracking with thresholds
  - Service gating based on trust
  - Condition removal (healing mechanic)
  - Skill teaching system (basic → advanced herbalism)
  - Garden access control

## Walkthrough Files
- `test_elara_gossip.txt` (scenario 2) - ✅ EXISTS, PASSING (gossip without confession)
- `test_elara_confession.txt` (scenario 1) - ✅ EXISTS, PASSING (confession before gossip)
- `test_healer_elara.txt` - ✅ EXISTS, PASSING (general dialog)
- `test_elara_healing.txt` (scenarios 6-7) - COULD ADD (healing service edge cases)
- `test_elara_trust_gate.txt` (scenario 3) - COULD ADD (service blocked, not critical)

## Implementation Status
- [x] Gossip reactions handler (services.py:61-123)
- [x] Gossip checks confession flag (services.py:98-103)
- [x] Confession handler (services.py:126-175)
- [x] Confession sets flag and applies -1 penalty
- [x] Trust-gated healing service (services.py:267-313)
- [x] Condition removal (healable list: bleeding, fungal_infection, poison)
- [x] Gossip penalty tested (-2 trust)
- [x] Confession timing walkthrough (VERIFIED - test_elara_confession.txt)
- [x] Core gossip/confession mechanics complete
- [ ] Basic herbalism teaching (trust 2+)
- [ ] Advanced herbalism teaching (trust 3+)
- [ ] Garden access control
- [ ] Aldric rescue trust bonus

## Reference Implementation

**See:** [npc_reaction_system_guide.md](../../docs/Guides/npc_reaction_system_guide.md#healer-elara-gossip--confession) for config examples and flow diagrams.

This NPC demonstrates:
- **gossip_reactions**: Delayed gossip delivery with confession checks
- **dialog_reactions**: Confession keywords trigger trust-modifying handlers
- **Trust-based service gating**: Healing available only at trust >= 0
- **Confession mechanics**: Early confession mitigates (but doesn't prevent) trust penalty
