# Undercity Detailed Design

**Version**: 1.0
**Last Updated**: 2026-01-10
**Status**: Deferred - Complete specification for future implementation

---

## 0. Overview

The Undercity is a criminal network beneath the Civilized Remnants town. It provides:
- Dark path gameplay options
- Alternative economy for stolen goods
- Information shortcuts via payment
- Assassination contracts (darkest path)

This document consolidates all undercity-related design from across the codebase to enable clean future implementation.

---

## 1. Locations

### 1.1 undercity_entrance

```json
{
  "id": "undercity_entrance",
  "name": "Undercity Entrance",
  "description": "A hidden trapdoor leading to tunnels beneath the town. The air smells of secrets and desperation.",
  "region": "civilized_remnants",
  "properties": {
    "lighting": "dark",
    "hidden": true,
    "illegal": false
  },
  "exits": {
    "up": "market_square",
    "down": "undercity"
  },
  "discovery_methods": [
    "Vex trust 3+ reveals location",
    "Rescued Delvan provides black market connection",
    "Whisper information purchase (if already in undercity via other means)",
    "Overhear conversation in market at night (5% chance per night visit)"
  ],
  "access_method": "Trapdoor under dry fountain in market_square. Knock pattern: 3 knocks, pause, 2 knocks",
  "traits": ["concealed trapdoor", "worn stone steps", "smell of secrets"]
}
```

### 1.2 undercity

```json
{
  "id": "undercity",
  "name": "The Undercity",
  "description": "A network of tunnels and chambers beneath the town. Dim lanterns cast wavering shadows. Whispered negotiations echo off damp stone walls.",
  "region": "civilized_remnants",
  "properties": {
    "lighting": "dim",
    "illegal": true,
    "discovery_risk": true
  },
  "exits": {
    "up": "undercity_entrance"
  },
  "actors": ["the_fence", "whisper", "shadow"],
  "discovery_risk": {
    "per_service": 0.05,
    "effect": "Town reputation -2",
    "branding_threshold": 3
  },
  "traits": ["dim lantern light", "whispered negotiations", "dangerous competence", "damp stone walls"]
}
```

---

## 2. NPCs

### 2.1 the_fence

```json
{
  "id": "the_fence",
  "name": "The Fence",
  "type": "human_npc",
  "description": "A figure in shadows who deals in items of questionable origin. You never see their face clearly, but their hands move with practiced efficiency.",
  "location": "undercity",
  "properties": {
    "role": "criminal_vendor",
    "disposition": "neutral",
    "speaks": true
  },
  "services": {
    "buy_stolen": {
      "description": "Buys any item at 50% market value, no questions asked",
      "accepts": "any_item",
      "price_multiplier": 0.5
    },
    "sell_contraband": {
      "lockpicks": {"price": 30, "description": "Set of lockpicks for bypassing locks"},
      "poison": {"price": 50, "description": "Colorless, odorless poison"},
      "disguise_kit": {"price": 40, "description": "Materials for changing appearance"}
    }
  },
  "dialog_topics": {
    "business": "I don't ask where things come from. You don't ask where they go.",
    "guards": "The militia thinks they control this town. They control the surface.",
    "varn": "Councilor Varn? A businessman. We understand each other."
  },
  "trust_system": {
    "initial": 0,
    "sources": {
      "sell_item": 0.5,
      "buy_item": 0.25,
      "repeat_customer": 0.1
    },
    "effects": {
      "trust_2": "Better prices (60% instead of 50%)",
      "trust_3": "Access to rarer contraband",
      "trust_4": "Information about other criminals"
    }
  }
}
```

### 2.2 whisper

```json
{
  "id": "whisper",
  "name": "Whisper",
  "type": "human_npc",
  "description": "A nondescript person who seems to know everything about everyone. Their voice is barely audible, forcing you to lean close.",
  "location": "undercity",
  "properties": {
    "role": "information_seller",
    "disposition": "neutral",
    "speaks": true
  },
  "services": {
    "sell_npc_secrets": {
      "price": 20,
      "provides": "Weaknesses, backstories, hidden motivations of named NPCs",
      "examples": [
        "Hurst lost his family to beasts - he'll never forgive anything beast-related",
        "Asha believes in redemption - she's the one to approach if branded",
        "Maren cheated a customer once - she's terrified of exposure"
      ]
    },
    "sell_location_secrets": {
      "price": 30,
      "provides": "Hidden paths, treasure locations, dangers",
      "examples": [
        "Back tunnel from broken_statue_hall to undercity",
        "Secret cache behind market stall",
        "Guardian's weakness to cold iron"
      ]
    },
    "sell_valuable_secrets": {
      "price_range": [40, 100],
      "provides": "Major NPC secrets, plot-relevant information",
      "examples": [
        "Varn's undercity profits (40g) - blackmail material",
        "Hurst's family tragedy details (60g) - manipulation or empathy",
        "Hidden entrance to council vault (100g)"
      ]
    }
  },
  "dialog_topics": {
    "business": "Information has value. I trade in value.",
    "undercity": "Everyone has secrets. The undercity simply... acknowledges this.",
    "echo": "The Echo knows things even I don't. Be careful what you promise."
  },
  "design_note": "Information can be used for manipulation OR empathy - player decides intent"
}
```

### 2.3 shadow

```json
{
  "id": "shadow",
  "name": "Shadow",
  "type": "human_npc",
  "description": "You're not sure you've ever seen their face clearly. They move without sound, and their presence makes the air feel colder.",
  "location": "undercity",
  "properties": {
    "role": "assassin",
    "disposition": "neutral",
    "speaks": true,
    "dangerous": true
  },
  "services": {
    "assassination_contracts": {
      "description": "Kill any named NPC in the game",
      "price_range": [100, 500],
      "price_factors": {
        "commoner": 100,
        "merchant": 150,
        "guard": 200,
        "councilor": 300,
        "major_npc": 500
      },
      "delay_turns": 3,
      "discovery_chance": 0.20,
      "irreversible_after_payment": true
    }
  },
  "assassination_consequences": {
    "if_discovered": {
      "reputation": -5,
      "flags_set": ["assassination_discovered", "branded"],
      "unbranding_blocked": true,
      "echo_knows": true,
      "target_faction_hostile": true
    },
    "if_undiscovered": {
      "flags_set": ["has_killed"],
      "echo_knows": true,
      "triumphant_ending_blocked": true,
      "npcs_sense_wrongness": true
    }
  },
  "dialog_topics": {
    "business": "Everyone dies. I simply... expedite the process. For a fee.",
    "warning": "Once paid, the contract cannot be cancelled. Be certain.",
    "echo": "The Echo knows all debts. Even the unpaid ones. Especially those."
  },
  "dialog_before_contract": {
    "first_meeting": "Shadow regards you silently. 'You found your way here. That takes... initiative.'",
    "inquiry": "'Names have prices. Prices have consequences. Do you understand consequences?'",
    "confirmation": "'Three days. The name will be... resolved. There is no going back.'"
  },
  "design_note": "Darkest option in game. Available but NEVER encouraged. Massive consequences. Warning signs before commitment."
}
```

---

## 3. Access Methods

### 3.1 Vex Trust Path

```
Trigger: curiosity_dealer_vex trust reaches 3
Dialog: "You've proven... reliable. There's more to this town than the surface.
        The fountain in the square - it's been dry for years.
        Knock three times, pause, knock twice. Tell them Vex sent you."
Flag set: knows_undercity_entrance = true
Hidden exit revealed: market_square -> down -> undercity_entrance
```

### 3.2 Delvan Connection Path

```
Prerequisite: extra.delvan_rescued = true
Prerequisite: merchant_delvan trust >= 2
Dialog topic: "connections" or "black market"
Dialog: "Before the flood, I knew people. The kind who operate beneath notice.
        There's an entrance in the market square - the dry fountain.
        Three knocks, pause, two knocks. My name still means something down there."
Flag set: knows_undercity_entrance = true
Hidden exit revealed: market_square -> down -> undercity_entrance
```

### 3.3 Night Market Overhear

```
Trigger: Player in market_square at night (turn % 24 > 18 or < 6)
Chance: 5% per qualifying visit
Event: "You overhear two figures whispering near the dry fountain.
        '...three and two, like always...'
        They notice you watching and melt into the shadows."
Flag set: knows_undercity_entrance = true
Hidden exit revealed: market_square -> down -> undercity_entrance
```

### 3.4 Back Tunnel (Branded Players)

```
Location: broken_statue_hall
Requirement: player is branded (cannot use normal entrance due to risk)
Discovery: Examine walls, find hidden passage
Exit: broken_statue_hall -> hidden -> undercity
Note: Allows branded players to access undercity for Guardian repair path
```

---

## 4. Discovery and Risk System

### 4.1 Discovery Mechanics

```python
DiscoveryConfig = {
    "base_chance_per_service": 0.05,  # 5%
    "cumulative": False,  # Each service is independent roll
    "services_tracked": [
        "fence_buy", "fence_sell",
        "whisper_buy",
        "shadow_contract"  # Higher discovery chance (20%)
    ],
    "shadow_discovery_chance": 0.20  # Assassination has higher risk
}
```

### 4.2 Discovery Consequences

```python
DiscoveryEffects = {
    "first_discovery": {
        "reputation_change": -2,
        "dialog": "Guards approach you in the market. 'We know where you've been. Consider this a warning.'",
        "flag_set": "undercity_discovered_once"
    },
    "second_discovery": {
        "reputation_change": -2,
        "dialog": "The militia captain pulls you aside. 'Twice now. There won't be a third warning.'",
        "flag_set": "undercity_discovered_twice"
    },
    "third_discovery": {
        "reputation_change": -2,
        "triggers_branding": True,
        "dialog": "Guards seize you. 'Criminal activities. Multiple offenses. The council has ruled.'",
        "flag_set": "branded"
    }
}
```

### 4.3 Undercity Reputation (Separate Track)

```python
UndercityReputationConfig = {
    "id": "undercity_reputation",
    "scale": (-5, 5),
    "initial": 0,
    "sources": {
        "positive": {
            "use_service": 0.5,
            "sell_contraband": 0.5,
            "complete_criminal_task": 1.0,
            "keep_criminal_secret": 0.25
        },
        "negative": {
            "betray_to_guards": -3,
            "refuse_reasonable_service": -0.5,
            "bring_guards": -5
        }
    },
    "effects": {
        "reputation_3+": "Better prices, more services available",
        "reputation_-2": "Criminals suspicious, prices increase",
        "reputation_-4": "Denied service, may be attacked"
    },
    "conflict_with_town": "High undercity rep + discovery = extra town rep damage"
}
```

---

## 5. Items

### 5.1 Contraband Items

```json
{
  "lockpicks": {
    "id": "lockpicks",
    "name": "Lockpicks",
    "description": "A set of slender metal tools for bypassing locks. Possession is illegal in the Civilized Remnants.",
    "properties": {
      "portable": true,
      "contraband": true,
      "tool": true
    },
    "use": "Bypass locked doors and containers",
    "source": "the_fence (30g)",
    "legal_risk": "If discovered by guards, reputation -1"
  },

  "poison": {
    "id": "poison",
    "name": "Poison Vial",
    "description": "A small vial of colorless, odorless liquid. One dose.",
    "properties": {
      "portable": true,
      "contraband": true,
      "consumable": true,
      "dangerous": true
    },
    "use": "Apply to food/drink or weapon. Causes condition: poisoned (10 damage/turn for 5 turns)",
    "source": "the_fence (50g)",
    "legal_risk": "If discovered, immediate branding"
  },

  "disguise_kit": {
    "id": "disguise_kit",
    "name": "Disguise Kit",
    "description": "Makeup, false hair, and clothing modifications. Enough for several disguises.",
    "properties": {
      "portable": true,
      "contraband": true,
      "tool": true,
      "uses": 3
    },
    "use": "Temporarily avoid recognition. Useful if branded or known criminal.",
    "source": "the_fence (40g)",
    "legal_risk": "Possession suspicious but not illegal"
  }
}
```

---

## 6. Integration Points

### 6.1 Civilized Remnants Integration

**market_square changes:**
```json
{
  "hidden_exits": {
    "down": {
      "destination": "undercity_entrance",
      "requires_flag": "knows_undercity_entrance",
      "access_description": "Trapdoor under dry fountain, knock pattern 3-pause-2"
    }
  }
}
```

**broken_statue_hall changes:**
```json
{
  "hidden_exits": {
    "hidden": {
      "destination": "undercity",
      "requires_flag": "branded",
      "discovery": "Search walls reveals hidden passage",
      "description": "A narrow tunnel leading down into darkness"
    }
  }
}
```

### 6.2 NPC Dialog Integration

**curiosity_dealer_vex** - Add dialog_reactions:
```json
{
  "topic": "undercity",
  "trust_required": 3,
  "response": "Vex leans close. 'The fountain. Dry for years. Three knocks, pause, two. My name opens doors.'",
  "sets_flag": "knows_undercity_entrance",
  "reveals_exit": {"location": "market_square", "direction": "down"}
}
```

**merchant_delvan** - Add dialog_reactions:
```json
{
  "topic": "connections",
  "requires": "extra.delvan_rescued",
  "trust_required": 2,
  "response": "Delvan glances around. 'I knew people. The kind who work beneath notice. The dry fountain in the market - three, pause, two. Tell them Delvan sent you.'",
  "sets_flag": "knows_undercity_entrance",
  "reveals_exit": {"location": "market_square", "direction": "down"}
}
```

**councilor_varn** - Secret connection:
```json
{
  "secret": "Has undercity connections, profits from trades he publicly condemns",
  "whisper_information": {
    "price": 40,
    "content": "Varn takes a cut from every undercity transaction. The guards look the other way for a reason.",
    "use": "Blackmail potential, or understanding his motivations"
  }
}
```

### 6.3 Cross-Region Integration

**Sunken District (Delvan rescue):**
- Rescuing Delvan enables undercity access dialog
- This is an alternative to Vex trust 3

**The Echo:**
- Echo knows about assassinations regardless of discovery
- Echo trust penalty: -2 per assassination
- Echo confrontation if player uses Shadow's services

---

## 7. Gameplay Implications

### 7.1 What Undercity Enables

| Capability | Surface Alternative | Undercity Advantage |
|------------|---------------------|---------------------|
| Sell stolen goods | None | Monetize theft |
| Buy lockpicks | None | Bypass locks |
| Buy poison | Nightshade (skill-gated) | Ready-to-use |
| Buy information | Earn through gameplay | Pay instead of work |
| Assassination | None | Remove obstacles permanently |

### 7.2 Risk/Reward Balance

| Action | Reward | Risk |
|--------|--------|------|
| Use Fence once | 50% item value | 5% discovery → -2 rep |
| Use Fence repeatedly | Ongoing income | Cumulative discovery risk |
| Buy from Whisper | Information shortcut | 5% discovery |
| Use Shadow | NPC removed | 20% discovery → branding + blocked endings |

### 7.3 Ending Implications

| Ending | Undercity Impact |
|--------|------------------|
| Triumphant | Blocked if assassination used (even undiscovered) |
| Successful | Blocked if assassination discovered |
| Bittersweet | Available regardless |
| Dark | Enhanced by undercity involvement |

---

## 8. Implementation Checklist

When implementing the undercity, complete these tasks:

### 8.1 Locations
- [ ] Add undercity_entrance to game_state.json
- [ ] Add undercity to game_state.json
- [ ] Add hidden exit from market_square
- [ ] Add hidden exit from broken_statue_hall (branded path)

### 8.2 NPCs
- [ ] Add the_fence to game_state.json
- [ ] Add whisper to game_state.json
- [ ] Add shadow to game_state.json
- [ ] Implement NPC behaviors and services

### 8.3 Items
- [ ] Add lockpicks to game_state.json
- [ ] Add poison to game_state.json
- [ ] Add disguise_kit to game_state.json
- [ ] Implement item effects

### 8.4 Mechanics
- [ ] Implement hidden exit system (flag-gated exits)
- [ ] Implement discovery risk system
- [ ] Implement undercity reputation track
- [ ] Implement assassination contract system

### 8.5 NPC Integration
- [ ] Add Vex undercity dialog (trust 3+)
- [ ] Add Delvan undercity dialog (post-rescue)
- [ ] Add Varn secret connection
- [ ] Update Echo to track assassinations

### 8.6 Testing
- [ ] Create walkthrough: undercity_discovery_vex.txt
- [ ] Create walkthrough: undercity_discovery_delvan.txt
- [ ] Create walkthrough: undercity_fence_services.txt
- [ ] Create walkthrough: undercity_assassination.txt
- [ ] Create walkthrough: undercity_discovery_consequences.txt

---

## 9. Design Rationale

### 9.1 Why Defer?

The undercity provides compelling dark-path gameplay but:
- Limited appeal (mainly completionists and dark-path players)
- Significant implementation effort (new mechanics: hidden exits, discovery risk, assassination)
- Not required for main quest completion
- Surface gameplay is complete without it

### 9.2 Why Document Thoroughly?

- Ensures no undercity references remain in active codebase
- Enables clean future implementation
- Preserves design intent and integration points
- Avoids re-discovery of design decisions

### 9.3 Integration Dependencies

When implementing, these systems must exist first:
1. Hidden exit mechanics (flag-gated exits)
2. Service discovery/risk system
3. Assassination contract mechanics
4. Separate reputation track system

---

## Appendix A: Removed Content Tracking

The following content was removed from the active codebase and is preserved here:

### A.1 From civilized_remnants_detailed_design.md
- Section 1.1: undercity_entrance and undercity location specs
- Section 1.2: the_fence, whisper, shadow NPC specs
- Section 3.1: Undercity services table entries
- Section 3.5: Undercity reputation system
- Appendix A.5: Assassination system config

### A.2 From civilized_remnants_sketch.json
- locations.undercity_entrance
- locations.undercity
- actors.the_fence
- actors.whisper
- actors.shadow
- persistent_effects.undercity_reputation

### A.3 From game_state.json
- (None - undercity was never implemented)

### A.4 From NPC scenarios
- npc_the_fence.md (entire file)
- npc_whisper.md (entire file)
- npc_shadow.md (entire file)
- npc_merchant_delvan.md scenario 8 (undercity access)
- npc_curiosity_dealer_vex.md scenario for undercity access

### A.5 From walkthroughs
- test_delvan_undercity_dialog.txt (entire file)

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-10 | Initial version - consolidated from multiple sources for deferral |
