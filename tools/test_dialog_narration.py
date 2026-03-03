#!/usr/bin/env python3
"""Test framework for dialog parsing and narration with proposed structured data format.

This tool allows testing how the MLX LLM handles dialog:
1. PARSING: Converting natural dialog input to JSON commands (with topic context)
2. NARRATION: Converting structured dialog JSON to natural prose

Usage:
    # Test parsing natural dialog to commands
    python tools/test_dialog_narration.py examples/big_game --parse

    # Test narrating dialog results
    python tools/test_dialog_narration.py examples/big_game --narrate

    # Run all tests (parse + narrate)
    python tools/test_dialog_narration.py examples/big_game --batch

    # Interactive mode
    python tools/test_dialog_narration.py examples/big_game --interactive

    # Single test case
    python tools/test_dialog_narration.py examples/big_game --case standard_topic

The tool tests how well the LLM handles dialog before implementing actual changes.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.game_engine import GameEngine


# Model aliases (same as mlx_game.py)
MODEL_ALIASES = {
    "llama-3b": "mlx-community/Llama-3.2-3B-Instruct-4bit",
    "llama-8b": "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit",
    "mistral-7b": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
    "qwen-3b": "mlx-community/Qwen2.5-3B-Instruct-4bit",
    "qwen-7b": "mlx-community/Qwen2.5-7B-Instruct-4bit",
}


# ============================================================================
# PARSING TEST CASES
# These test converting natural dialog input to JSON commands
# ============================================================================

# ============================================================================
# ENRICHED CONTEXT STRUCTURE
# ============================================================================
# The enriched context adds:
# - npcs: list of NPC names (separate from objects)
# - topic_hints: dict mapping topic -> brief description
# This helps the LLM understand who can be talked to and what topics mean

PARSE_TEST_CASES: Dict[str, Dict[str, Any]] = {
    # Natural questions that should route to topics
    "natural_infection_question": {
        "description": "Natural question about infection routes to 'infection' topic",
        "input": "What happened to you?",
        "context": {
            "location_objects": ["journal", "campfire"],
            "npcs": ["aldric"],
            "inventory": [],
            "exits": ["east", "down"],
            "topics": ["infection", "research", "myconids"],
            "topic_hints": {
                "infection": "his illness and symptoms",
                "research": "his scholarly work",
                "myconids": "the fungal creatures"
            }
        },
        "expected_action": {
            "verb": "ask",
            "object": "aldric",
            "indirect_object": "infection"  # Should map question to topic
        }
    },

    "natural_help_question": {
        "description": "Question about help/cure routes to 'cure' topic",
        "input": "Can you help me cure the blight?",
        "context": {
            "location_objects": [],
            "npcs": ["myconid_elder"],
            "inventory": ["silvermoss"],
            "exits": ["west"],
            "topics": ["cure", "resistance", "spore_mother"],
            "topic_hints": {
                "cure": "healing the infection",
                "resistance": "immunity to spores",
                "spore_mother": "the source of the blight"
            }
        },
        "expected_action": {
            "verb": "ask",
            "object": "myconid_elder",
            "indirect_object": "cure"
        }
    },

    "natural_teaching_question": {
        "description": "Question about learning routes to 'teaching' topic",
        "input": "Can you teach me about plants?",
        "context": {
            "location_objects": ["herbs", "mortar"],
            "npcs": ["elara"],
            "inventory": [],
            "exits": ["west", "south"],
            "topics": ["herbalism", "teaching", "garden"],
            "topic_hints": {
                "herbalism": "knowledge of medicinal plants",
                "teaching": "learning from her",
                "garden": "the healing garden"
            }
        },
        "expected_action": {
            "verb": "ask",
            "object": "elara",
            "indirect_object": "teaching"
        }
    },

    "informal_talk": {
        "description": "Informal talk command with single NPC",
        "input": "hey, let's chat",
        "context": {
            "location_objects": [],
            "npcs": ["sira"],
            "inventory": ["bandages"],
            "exits": ["north"],
            "topics": ["injury", "hunters", "elara"],
            "topic_hints": {
                "injury": "her wounds",
                "hunters": "the hunters who hurt her",
                "elara": "the healer who can help"
            }
        },
        "expected_action": {
            "verb": "talk",
            "object": "sira"
        }
    },

    "question_about_specific_topic": {
        "description": "Explicit topic question",
        "input": "Tell me about the Spore Mother",
        "context": {
            "location_objects": [],
            "npcs": ["aldric"],
            "inventory": [],
            "exits": ["east"],
            "topics": ["infection", "spore_mother", "safe_path"],
            "topic_hints": {
                "infection": "the spreading illness",
                "spore_mother": "the ancient creature spreading spores",
                "safe_path": "how to travel safely"
            }
        },
        "expected_action": {
            "verb": "ask",
            "object": "aldric",
            "indirect_object": "spore_mother"
        }
    },

    "commitment_phrase": {
        "description": "Promise/commitment phrase - ask about help/medicine (NPC interprets as commitment offer)",
        "input": "I'll help you find medicine for your cubs",
        "context": {
            "location_objects": ["cubs"],
            "npcs": ["dire_bear"],
            "inventory": [],
            "exits": ["north", "south"],
            "topics": ["cubs", "medicine", "help"],
            "topic_hints": {
                "cubs": "the sick bear cubs",
                "medicine": "what could heal them",
                "help": "offering assistance"
            }
        },
        "expected_action": {
            # Either ask about medicine/help or talk is acceptable
            # NPC response will interpret the offer as a potential commitment
            "verb": "ask",
            "object": "dire_bear",
            "indirect_object": "help"  # or medicine - both acceptable
        },
        "accept_clarify": True  # Also accept talk or other reasonable interpretations
    },

    "question_without_explicit_npc": {
        "description": "Question when only one NPC present (implicit target)",
        "input": "What's wrong with your leg?",
        "context": {
            "location_objects": ["tree", "trail"],
            "npcs": ["sira"],
            "inventory": [],
            "exits": ["north", "south"],
            "topics": ["injury", "hunters", "elara"],
            "topic_hints": {
                "injury": "her wounds from the attack",
                "hunters": "the hunters who hurt her",
                "elara": "the healer who can help"
            }
        },
        "expected_action": {
            "verb": "ask",
            "object": "sira",
            "indirect_object": "injury"
        }
    },

    "gesture_at_creature": {
        "description": "Non-verbal interaction with creature",
        "input": "gesture toward the temple questioningly",
        "context": {
            "location_objects": ["hot_springs"],
            "npcs": ["steam_salamander"],
            "inventory": ["torch"],
            "exits": ["east", "north"],
            "topics": ["temple", "caves", "fire"],
            "topic_hints": {
                "temple": "the ancient fire temple",
                "caves": "the volcanic tunnels",
                "fire": "their fire magic"
            }
        },
        "expected_action": {
            "verb": "ask",
            "object": "steam_salamander",
            "indirect_object": "temple"
        }
    },

    # Additional tests for edge cases
    "unknown_topic_graceful": {
        "description": "Ask about something not in topics - should clarify or fail gracefully",
        "input": "What do you know about dragons?",
        "context": {
            "location_objects": [],
            "npcs": ["aldric"],
            "inventory": [],
            "exits": ["east"],
            "topics": ["infection", "research", "myconids"],
            "topic_hints": {
                "infection": "his illness",
                "research": "his studies",
                "myconids": "the fungal creatures"
            }
        },
        "expected_action": {
            # Should still attempt ask - handler will respond with "don't know"
            "verb": "ask",
            "object": "aldric",
            "indirect_object": "dragons"  # Pass-through unknown topic
        },
        "accept_clarify": True  # Also accept a clarify response
    },

    "ambiguous_multiple_npcs": {
        "description": "Ambiguous command with multiple NPCs",
        "input": "tell me about the cure",
        "context": {
            "location_objects": [],
            "npcs": ["aldric", "elara"],
            "inventory": [],
            "exits": ["west"],
            "topics": ["cure", "infection"],
            "topic_hints": {
                "cure": "how to cure the blight",
                "infection": "the spreading illness"
            }
        },
        "expected_action": {
            # With multiple NPCs, should either pick one or clarify
            "verb": "ask",
            "indirect_object": "cure"
        },
        "accept_clarify": True
    },

    "very_informal_greeting": {
        "description": "Very informal greeting - should still route to talk",
        "input": "yo",
        "context": {
            "location_objects": [],
            "npcs": ["sira"],
            "inventory": [],
            "exits": ["north"],
            "topics": ["injury", "hunters"],
            "topic_hints": {
                "injury": "her wounds",
                "hunters": "the attackers"
            }
        },
        "expected_action": {
            "verb": "talk",
            "object": "sira"
        },
        "accept_clarify": True  # "yo what?" is reasonable
    }
}


# ============================================================================
# NARRATION TEST CASES
# These test converting structured dialog JSON to natural prose
# ============================================================================

NARRATION_TEST_CASES: Dict[str, Dict[str, Any]] = {
    # Standard topic query - asking about personal suffering
    "standard_topic": {
        "description": "Ask Aldric about his infection (standard topic query)",
        "input": "What happened to you?",
        "mock_result": {
            "success": True,
            "verbosity": "full",
            "narration": {
                "action_summary": "You ask Aldric about his infection.",
                "speaker": {
                    "id": "aldric",
                    "name": "Scholar Aldric",
                    "type": "npc",
                    "traits": ["frail", "scholarly", "infected", "hopeful"]
                },
                "dialog": {
                    "topic": "infection",
                    "response": {
                        "content": "personal_suffering_plea",
                        "tone": "pained_hopeful",
                        "key_info": ["needs silvermoss", "found in Luminous Grotto", "infection spreading"]
                    },
                    "trust_change": {
                        "delta": 1,
                        "reason": "showed concern for personal topic",
                        "new_level": "acquaintance"
                    }
                }
            }
        }
    },

    # Service inquiry - asking about teaching
    "service_inquiry": {
        "description": "Ask Elara about herbalism training (service gated by trust)",
        "input": "Can you teach me about plants?",
        "mock_result": {
            "success": True,
            "verbosity": "full",
            "narration": {
                "action_summary": "You ask Elara about learning herbalism.",
                "speaker": {
                    "id": "elara",
                    "name": "Healer Elara",
                    "type": "npc",
                    "traits": ["healer", "careful", "kind", "busy"]
                },
                "dialog": {
                    "topic": "teaching",
                    "response": {
                        "content": "service_offer_conditional",
                        "tone": "professional_warm",
                        "requirements": {
                            "trust_required": 3,
                            "current_trust": 0,
                            "service_type": "advanced_herbalism"
                        },
                        "key_info": ["represents lifetime of work", "needs trust first", "help patients to build trust"]
                    }
                }
            }
        }
    },

    # Non-verbal creature - salamander pantomime
    "creature_gestural": {
        "description": "Ask salamander about temple (gestural communication)",
        "input": "What about the temple?",
        "mock_result": {
            "success": True,
            "verbosity": "full",
            "narration": {
                "action_summary": "You gesture toward the temple and look at the salamander questioningly.",
                "speaker": {
                    "id": "steam_salamander_1",
                    "name": "Steam Salamander",
                    "type": "creature",
                    "traits": ["intelligent", "warm", "cautious", "fire-aspected"],
                    "communication_mode": "gestural"
                },
                "dialog": {
                    "topic": "temple",
                    "response": {
                        "content": "warning_territorial",
                        "communication_type": "pantomime",
                        "gestures": [
                            {"action": "two fists coming together", "meaning": "guardians/conflict"},
                            {"action": "shakes head", "meaning": "negative/danger"},
                            {"action": "points to own chest, then makes warding sign", "meaning": "won't go there"}
                        ],
                        "interpretation_hint": "Temple has guardians. Salamander won't help there."
                    }
                }
            }
        }
    },

    # Myconid spore communication
    "creature_spore": {
        "description": "Ask Myconid Elder about cure (spore language)",
        "input": "Can you cure the blight?",
        "mock_result": {
            "success": True,
            "verbosity": "full",
            "narration": {
                "action_summary": "You gesture and speak about curing illness.",
                "speaker": {
                    "id": "myconid_elder",
                    "name": "Myconid Elder",
                    "type": "creature",
                    "traits": ["ancient", "wise", "neutral", "patient"],
                    "communication_mode": "spore_language"
                },
                "dialog": {
                    "topic": "cure",
                    "response": {
                        "content": "service_offer_exchange",
                        "communication_type": "spore_puff",
                        "spore_color": "green",
                        "key_info": ["can cure blight-sickness", "requires payment", "crystal from Frozen Reaches or rare minerals"]
                    }
                }
            }
        }
    },

    # Commitment making - bear cubs
    "commitment_made": {
        "description": "Promise to help the dire bear's cubs",
        "input": "I'll help your cubs. I'll find medicine.",
        "mock_result": {
            "success": True,
            "verbosity": "full",
            "narration": {
                "action_summary": "You speak slowly, calmly, making a promise to the bear.",
                "speaker": {
                    "id": "dire_bear",
                    "name": "Dire Bear",
                    "type": "creature",
                    "traits": ["protective", "intelligent", "desperate", "massive"],
                    "communication_mode": "behavioral"
                },
                "dialog": {
                    "topic": "commitment",
                    "commitment_made": {
                        "id": "bear_cubs_commitment",
                        "description": "Find medicine for sick cubs",
                        "timer_remaining": 35
                    },
                    "response": {
                        "content": "commitment_accepted",
                        "communication_type": "behavioral",
                        "behavior_description": "studies you with intelligent eyes, seems to understand your intent, steps back from defensive posture, looks south along the trail",
                        "disposition_change": "hostile -> guarded_pause"
                    }
                }
            }
        }
    },

    # Multi-speaker council dialog
    "council_dilemma": {
        "description": "Discuss quarantine option with the council",
        "input": "What about quarantining them while we search for a cure?",
        "mock_result": {
            "success": True,
            "verbosity": "full",
            "narration": {
                "action_summary": "You ask about the quarantine option.",
                "speakers": [
                    {"id": "asha", "name": "Councilor Asha", "traits": ["idealistic", "compassionate"], "stance": "supportive"},
                    {"id": "hurst", "name": "Councilor Hurst", "traits": ["pragmatic", "harsh"], "stance": "skeptical"}
                ],
                "dialog": {
                    "topic": "quarantine_option",
                    "response": {
                        "content": "dilemma_option_detail",
                        "perspectives": {
                            "asha": "Keep them isolated while seeking cure - they deserve a chance",
                            "hurst": "Who seeks this cure? We can't spare guards. It would require an outsider."
                        },
                        "implications": "Player would commit to finding cure if this option is chosen",
                        "cross_region_link": "Fungal Depths - Spore Mother's blessing or myconid cure"
                    }
                }
            }
        }
    },

    # Confession dialog
    "confession": {
        "description": "Confess to Elara about failing to save Sira",
        "input": "I promised to help Sira, but I couldn't reach her in time. She died.",
        "mock_result": {
            "success": True,
            "verbosity": "full",
            "narration": {
                "action_summary": "You confess your failure to Elara.",
                "speaker": {
                    "id": "elara",
                    "name": "Healer Elara",
                    "type": "npc",
                    "traits": ["healer", "grieving", "conflicted"],
                    "emotional_state": "grief"
                },
                "dialog": {
                    "topic": "confession",
                    "confession": {
                        "about": "sira_death",
                        "context_provided": True,
                        "honesty": True
                    },
                    "response": {
                        "content": "confession_received",
                        "tone": "grief_with_grudging_respect",
                        "key_info": ["appreciates honesty", "relationship damaged but not destroyed", "trust can be rebuilt"]
                    },
                    "trust_change": {
                        "delta": -2,
                        "reason": "broke promise but confessed honestly",
                        "recovery_possible": True
                    }
                }
            }
        }
    },

    # Talk to NPC - list available topics
    "talk_list_topics": {
        "description": "Talk to Aldric to see available topics",
        "input": "talk to aldric",
        "mock_result": {
            "success": True,
            "verbosity": "full",
            "narration": {
                "action_summary": "You approach Aldric to talk.",
                "speaker": {
                    "id": "aldric",
                    "name": "Scholar Aldric",
                    "type": "npc",
                    "traits": ["frail", "scholarly", "infected", "eager_to_share"]
                },
                "dialog": {
                    "available_topics": ["infection", "research", "myconids"],
                    "response": {
                        "content": "greeting_with_topics",
                        "tone": "tired_but_hopeful",
                        "greeting": "Aldric looks up with tired eyes but seems willing to talk."
                    }
                },
                "must_mention": {
                    "dialog_topics": "You could ask about: infection, research, myconids"
                }
            }
        }
    },

    # Topic unlocked by previous dialog
    "unlocked_topic": {
        "description": "Ask about spore mother (requires knowing about infection first)",
        "input": "Tell me about the Spore Mother",
        "mock_result": {
            "success": True,
            "verbosity": "full",
            "narration": {
                "action_summary": "You ask Aldric about the Spore Mother.",
                "speaker": {
                    "id": "aldric",
                    "name": "Scholar Aldric",
                    "type": "npc",
                    "traits": ["frail", "scholarly", "passionate_about_research"]
                },
                "dialog": {
                    "topic": "spore_mother",
                    "unlocked_by": "infection",
                    "response": {
                        "content": "revelation_sympathetic",
                        "tone": "empathetic_urgent",
                        "key_info": [
                            "not evil - dying like Aldric",
                            "spreads spores in desperation seeking cure",
                            "heartmoss in Deep Root Caverns might cure her",
                            "air in Deep Roots is poison"
                        ]
                    },
                    "topics_unlocked": ["safe_path"]
                }
            }
        }
    },

    # Failed dialog - NPC doesn't know about topic
    "unknown_topic": {
        "description": "Ask about something the NPC doesn't know",
        "input": "What do you know about dragons?",
        "mock_result": {
            "success": True,
            "verbosity": "brief",
            "narration": {
                "action_summary": "You ask Aldric about dragons.",
                "speaker": {
                    "id": "aldric",
                    "name": "Scholar Aldric",
                    "type": "npc",
                    "traits": ["frail", "scholarly", "confused"]
                },
                "dialog": {
                    "topic": "dragons",
                    "response": {
                        "content": "topic_unknown",
                        "tone": "puzzled",
                        "fallback_message": "I've never heard of such creatures. Perhaps you're thinking of the beasts in the wilds?"
                    }
                }
            }
        }
    }
}


class EnrichedCommandParser:
    """Wrapper that adds enriched context to command parsing.

    This subclass builds an enhanced user prompt that includes:
    - NPCs separated from objects
    - Topic hints explaining what each topic covers
    - Dialog examples in the system prompt
    """

    def __init__(self, base_parser):
        """Wrap an existing LLMCommandParser."""
        self.base_parser = base_parser
        self.model = base_parser.model
        self.tokenizer = base_parser.tokenizer
        self.verbs = base_parser.verbs
        self.cache = base_parser.cache
        self.system_prompt_length = base_parser.system_prompt_length

    def parse_command(self, player_input: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse with enriched context."""
        # Build enriched user prompt
        user_prompt = self._build_enriched_user_prompt(context, player_input)

        # Call LLM (reusing base parser's cache and call method)
        response = self.base_parser._call_llm(user_prompt)

        # Parse response
        return self.base_parser._parse_response(response)

    def _build_enriched_user_prompt(self, context: Dict[str, Any], command: str) -> str:
        """Build user prompt with enriched dialog context.

        Enrichments:
        - NPCs listed separately from objects
        - Topic hints explaining each topic
        - Clear indication of who can be talked to
        """
        # Extract context fields
        location_objs = ', '.join(context.get('location_objects', [])) or 'none'
        npcs = ', '.join(context.get('npcs', [])) or 'none'
        inventory = ', '.join(context.get('inventory', [])) or 'none'
        exits = ', '.join(context.get('exits', [])) or 'none'
        topics = context.get('topics', [])
        topic_hints = context.get('topic_hints', {})

        # Build topics section with hints
        if topics and topic_hints:
            topics_section = "Dialog topics (you can ask NPCs about these):\n"
            for topic in topics:
                hint = topic_hints.get(topic, "")
                if hint:
                    topics_section += f"  - {topic}: {hint}\n"
                else:
                    topics_section += f"  - {topic}\n"
        elif topics:
            topics_section = f"Dialog topics: {', '.join(topics)}"
        else:
            topics_section = "Dialog topics: none"

        return f"""Available objects: {location_objs}
NPCs present (can talk to): {npcs}
Your inventory: {inventory}
Exits: {exits}
{topics_section}

Command: "{command}"

DIALOG RULES:
- To ask an NPC about a topic, use: {{"verb": "ask", "object": "<npc>", "indirect_object": "<topic>"}}
- To start general conversation, use: {{"verb": "talk", "object": "<npc>"}}
- "tell me about X", "what about X", "explain X" all map to asking about topic X
- If the player's question relates to a topic hint, use that topic
- If only one NPC is present, they are the implicit target for dialog

IMPORTANT: Extract adjectives and prepositions ONLY from the command text above, NOT from the available objects list.

Output JSON:"""


def run_parse_tests(command_parser, test_cases: Dict[str, Dict], pause: bool = True) -> None:
    """Run parsing test cases.

    Args:
        command_parser: The LLMCommandParser instance (or EnrichedCommandParser)
        test_cases: Dict of test case name -> test case data
        pause: If True, pause between tests for user review
    """
    print("\n" + "=" * 70)
    print("DIALOG PARSING TEST RESULTS")
    print("=" * 70)
    print("Testing: Natural language -> JSON action mapping")
    print("Focus: Can the LLM route conversational phrases to correct topics?")

    passed = 0
    failed = 0

    for name, test in test_cases.items():
        print(f"\n{'─' * 70}")
        print(f"TEST: {name}")
        print(f"Description: {test['description']}")
        print(f"Input: \"{test['input']}\"")
        print(f"Context topics: {test['context'].get('topics', [])}")
        print(f"Expected: verb={test['expected_action'].get('verb')}, " +
              f"object={test['expected_action'].get('object')}, " +
              f"indirect={test['expected_action'].get('indirect_object')}")
        print(f"{'─' * 70}")

        try:
            result = command_parser.parse_command(test['input'], test['context'])

            if result is None:
                # Check if test accepts clarify/error as valid
                if test.get('accept_clarify'):
                    print("RESULT: Parse returned None (acceptable for clarify test)")
                    print("✓ PASS (clarification/error is acceptable)")
                    passed += 1
                else:
                    print("RESULT: Parse failed (returned None)")
                    failed += 1
            else:
                result_type = result.get('type', 'command')
                action = result.get('action', {})
                print(f"RESULT: {json.dumps(result, indent=2)}")

                # Check for clarify response
                if result_type == 'clarify' and test.get('accept_clarify'):
                    print("✓ PASS (clarification response)")
                    passed += 1
                    continue

                # Check if it matches expected
                expected = test['expected_action']
                verb_match = action.get('verb') == expected.get('verb')

                # Object match: if expected object is None, any NPC is acceptable
                expected_obj = expected.get('object')
                actual_obj = action.get('object')
                if expected_obj is None:
                    # No specific object expected - just check verb and indirect
                    obj_match = actual_obj in test['context'].get('npcs', []) or actual_obj in test['context'].get('location_objects', [])
                else:
                    obj_match = actual_obj == expected_obj

                indirect_match = (action.get('indirect_object') == expected.get('indirect_object') or
                                  action.get('indirect_object') in test['context'].get('topics', []))

                if verb_match and obj_match:
                    if expected.get('indirect_object'):
                        if indirect_match:
                            print("✓ PASS (verb, object, and topic match)")
                            passed += 1
                        else:
                            print(f"✗ PARTIAL: verb/object correct, but topic mismatch")
                            print(f"  Expected indirect: {expected.get('indirect_object')}")
                            print(f"  Got indirect: {action.get('indirect_object')}")
                            failed += 1
                    else:
                        print("✓ PASS")
                        passed += 1
                elif test.get('accept_clarify'):
                    # Give partial credit if result is reasonable but different
                    print(f"? ACCEPTABLE: verb_match={verb_match}, obj_match={obj_match}")
                    print(f"  (accept_clarify=True allows alternative interpretations)")
                    passed += 1
                else:
                    print(f"✗ FAIL: verb_match={verb_match}, obj_match={obj_match}")
                    failed += 1

        except Exception as e:
            print(f"ERROR: {e}")
            failed += 1

        if pause:
            input("\nPress Enter for next test...")

    print(f"\n{'=' * 70}")
    print(f"PARSING SUMMARY: {passed} passed, {failed} failed")
    print(f"{'=' * 70}")


def run_narrate_tests(narrator, test_cases: Dict[str, Dict], pause: bool = True) -> None:
    """Run narration test cases.

    Args:
        narrator: The MLX narrator instance
        test_cases: Dict of test case name -> test case data
        pause: If True, pause between tests for user review
    """
    print("\n" + "=" * 70)
    print("DIALOG NARRATION TEST RESULTS")
    print("=" * 70)
    print("Testing: Structured JSON -> Natural prose narration")
    print("Focus: Can the LLM produce natural dialog from structured data?")

    for name, test in test_cases.items():
        print(f"\n{'─' * 70}")
        print(f"TEST: {name}")
        print(f"Description: {test['description']}")
        print(f"Player input: \"{test['input']}\"")
        print(f"{'─' * 70}")

        # Convert mock result to narration format
        mock_result = test["mock_result"]
        narration_dict = {
            "success": mock_result.get("success", True),
            "verbosity": mock_result.get("verbosity", "full"),
        }
        if "narration" in mock_result:
            narration_dict.update(mock_result["narration"])

        # Call the narrator
        narration_input = f"Narrate this dialog result:\n{json.dumps(narration_dict, indent=2)}"

        print("\nJSON sent to narrator:")
        json_str = json.dumps(narration_dict, indent=2)
        if len(json_str) > 600:
            print(json_str[:600] + "\n... (truncated)")
        else:
            print(json_str)

        print("\n--- NARRATOR OUTPUT ---")
        try:
            response = narrator._call_llm(narration_input)
            print(response)
        except Exception as e:
            print(f"[ERROR: {e}]")
        print("--- END OUTPUT ---")

        if pause:
            input("\nPress Enter for next test...")


def run_interactive(narrator, command_parser=None) -> None:
    """Run interactive mode.

    Args:
        narrator: The MLX narrator instance
        command_parser: Optional LLMCommandParser instance
    """
    print("\n" + "=" * 70)
    print("INTERACTIVE DIALOG TEST")
    print("=" * 70)
    print("\nCommands:")
    print("  list parse     - list parsing test cases")
    print("  list narrate   - list narration test cases")
    print("  parse <name>   - run a parsing test")
    print("  narrate <name> - run a narration test")
    print("  json <json>    - narrate custom JSON (multiline, end with empty line)")
    print("  quit           - exit")

    while True:
        print("\n> ", end="")
        user_input = input().strip()

        if not user_input:
            continue

        if user_input.lower() == "quit":
            break

        elif user_input.lower() == "list parse":
            print("\nParsing test cases:")
            for name, test in PARSE_TEST_CASES.items():
                print(f"  {name}: {test['description']}")

        elif user_input.lower() == "list narrate":
            print("\nNarration test cases:")
            for name, test in NARRATION_TEST_CASES.items():
                print(f"  {name}: {test['description']}")

        elif user_input.lower().startswith("parse "):
            case_name = user_input[6:].strip()
            if case_name in PARSE_TEST_CASES and command_parser:
                test = PARSE_TEST_CASES[case_name]
                print(f"\nTest: {test['description']}")
                print(f"Input: \"{test['input']}\"")
                print(f"Context: {test['context']}")
                try:
                    result = command_parser.parse_command(test['input'], test['context'])
                    print(f"Result: {json.dumps(result, indent=2) if result else 'None'}")
                except Exception as e:
                    print(f"Error: {e}")
            elif not command_parser:
                print("Parser not available (need SharedMLXBackend)")
            else:
                print(f"Unknown test case: {case_name}")

        elif user_input.lower().startswith("narrate "):
            case_name = user_input[8:].strip()
            if case_name in NARRATION_TEST_CASES:
                test = NARRATION_TEST_CASES[case_name]
                mock_result = test["mock_result"]
                narration_dict = {
                    "success": mock_result.get("success", True),
                    "verbosity": mock_result.get("verbosity", "full"),
                }
                if "narration" in mock_result:
                    narration_dict.update(mock_result["narration"])

                print(f"\nTest: {test['description']}")
                narration_input = f"Narrate this dialog result:\n{json.dumps(narration_dict, indent=2)}"

                print("\n--- NARRATOR OUTPUT ---")
                try:
                    response = narrator._call_llm(narration_input)
                    print(response)
                except Exception as e:
                    print(f"[ERROR: {e}]")
                print("--- END OUTPUT ---")
            else:
                print(f"Unknown test case: {case_name}")

        elif user_input.lower().startswith("json"):
            print("Enter JSON (end with empty line):")
            lines = []
            while True:
                line = input()
                if not line:
                    break
                lines.append(line)

            if lines:
                try:
                    narration_dict = json.loads("\n".join(lines))
                    narration_input = f"Narrate this dialog result:\n{json.dumps(narration_dict, indent=2)}"
                    print("\n--- NARRATOR OUTPUT ---")
                    response = narrator._call_llm(narration_input)
                    print(response)
                    print("--- END OUTPUT ---")
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON: {e}")
                except Exception as e:
                    print(f"Error: {e}")

        else:
            print("Unknown command. Type 'quit' to exit.")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test dialog parsing and narration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/test_dialog_narration.py examples/big_game --parse
  python tools/test_dialog_narration.py examples/big_game --narrate
  python tools/test_dialog_narration.py examples/big_game --batch
  python tools/test_dialog_narration.py examples/big_game --interactive
  python tools/test_dialog_narration.py examples/big_game --list
        """
    )
    parser.add_argument("game_dir", help="Game directory (e.g., examples/big_game)")
    parser.add_argument("--parse", "-p", action="store_true",
                        help="Run parsing tests (natural language -> JSON)")
    parser.add_argument("--narrate", "-n", action="store_true",
                        help="Run narration tests (JSON -> prose)")
    parser.add_argument("--batch", "-b", action="store_true",
                        help="Run all tests")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Run in interactive mode")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List available test cases and exit")
    parser.add_argument("--model", "-m", default="llama-3b",
                        help="Model preset (default: llama-3b)")
    parser.add_argument("--temperature", "-t", type=float, default=0.7,
                        help="Temperature for generation (default: 0.7)")
    parser.add_argument("--no-pause", action="store_true",
                        help="Don't pause between tests (for automated runs)")
    parser.add_argument("--enriched", "-e", action="store_true",
                        help="Use enriched context for parsing (NPCs, topic hints)")
    parser.add_argument("--basic", action="store_true",
                        help="Use basic context for parsing (no enrichments)")

    args = parser.parse_args()

    if args.list:
        print("Parsing test cases:")
        for name, test in PARSE_TEST_CASES.items():
            print(f"  {name}: {test['description']}")
        print("\nNarration test cases:")
        for name, test in NARRATION_TEST_CASES.items():
            print(f"  {name}: {test['description']}")
        return 0

    if not any([args.parse, args.narrate, args.batch, args.interactive]):
        parser.error("Must specify --parse, --narrate, --batch, or --interactive")

    # Resolve game path
    game_path = Path(args.game_dir)
    if not game_path.is_absolute() and "/" not in args.game_dir:
        game_path = project_root / "examples" / args.game_dir

    if not game_path.exists():
        print(f"Error: Game directory not found: {game_path}")
        return 1

    # Initialize game engine and narrator
    print(f"Loading game from: {game_path}")
    engine = GameEngine(game_path)

    # Resolve model alias
    model_path = MODEL_ALIASES.get(args.model, args.model)
    print(f"Loading MLX model: {args.model} ({model_path})")
    print("(This may take a moment...)")

    narrator = engine.create_mlx_narrator(
        model=model_path,
        temperature=args.temperature,
        max_tokens=400
    )
    print("Narrator ready.")

    # Try to create command parser using shared backend
    command_parser = None
    try:
        from src.shared_mlx import SharedMLXBackend
        from src.llm_command_parser import LLMCommandParser

        # Get verbs from vocabulary
        verbs = [v["word"] for v in narrator.merged_vocabulary.get("verbs", [])]

        # Create shared backend from narrator's model
        if hasattr(narrator, 'shared_backend') and narrator.shared_backend:
            shared = narrator.shared_backend
        else:
            # Create new shared backend
            shared = SharedMLXBackend(narrator.model_path)

        base_parser = LLMCommandParser(shared, verbs)

        # Use enriched parser by default unless --basic is specified
        # (test cases have enriched context, so enriched parser matches better)
        if args.basic:
            command_parser = base_parser
            print("Command parser ready (basic context).\n")
        else:
            command_parser = EnrichedCommandParser(base_parser)
            print("Command parser ready (enriched context).\n")
    except Exception as e:
        print(f"Note: Command parser not available ({e})")
        print("Parsing tests will be skipped.\n")

    # Run requested mode
    pause = not args.no_pause
    if args.batch:
        if command_parser:
            run_parse_tests(command_parser, PARSE_TEST_CASES, pause)
        run_narrate_tests(narrator, NARRATION_TEST_CASES, pause)
    elif args.parse:
        if command_parser:
            run_parse_tests(command_parser, PARSE_TEST_CASES, pause)
        else:
            print("Parser not available - cannot run parse tests")
    elif args.narrate:
        run_narrate_tests(narrator, NARRATION_TEST_CASES, pause)
    elif args.interactive:
        run_interactive(narrator, command_parser)

    return 0


if __name__ == "__main__":
    sys.exit(main())
