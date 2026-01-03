#!/usr/bin/env python3
"""Test script to examine narration JSON for Phase 1 verification."""

import json
from pathlib import Path
from src.game_engine import GameEngine
from src.llm_protocol import LLMProtocolHandler
from src.command_utils import parsed_to_json

game = GameEngine(Path("examples/spatial_game"))
handler = LLMProtocolHandler(game.game_state, game.behavior_manager)
parser = game.create_parser()

def run_command(cmd_text):
    """Parse and execute a command."""
    parsed = parser.parse_command(cmd_text)
    if not parsed:
        return {"success": False, "error": {"message": f"Failed to parse: {cmd_text}"}}
    message = parsed_to_json(parsed)
    return handler.handle_command(message)

print("=" * 70)
print("PHASE 1 NARRATION JSON VERIFICATION")
print("=" * 70)

# Test 1: Stand on bench - should have entity_refs with traits
print("\n1. STAND ON BENCH")
print("-" * 70)
result1 = run_command("stand on bench")
narration1 = result1.get("narration", {})
print(f"Success: {result1.get('success')}")
print(f"Primary: {narration1.get('primary_text')}")
print(f"\nEntity refs present: {bool(narration1.get('entity_refs'))}")
if narration1.get('entity_refs'):
    for eid, ref in narration1['entity_refs'].items():
        if 'bench' in ref.get('name', '').lower():
            print(f"  Bench: {ref.get('name')}")
            print(f"  Traits: {ref.get('traits', [])}")
print(f"\nMust mention: {narration1.get('must_mention')}")

# Test 2: First north movement - should include must_mention with exits
print("\n\n2. FIRST NORTH (new location)")
print("-" * 70)
result2 = run_command("north")
narration2 = result2.get("narration", {})
print(f"Success: {result2.get('success')}")
print(f"Primary: {narration2.get('primary_text')}")
print(f"Scene kind: {narration2.get('scope', {}).get('scene_kind')}")
print(f"Familiarity: {narration2.get('scope', {}).get('familiarity')}")
must_mention2 = narration2.get('must_mention')
print(f"\nMust mention present: {must_mention2 is not None}")
if must_mention2:
    print(f"  exits_text: {must_mention2.get('exits_text')}")

# Test 3: South (return) - should NOT have must_mention
print("\n\n3. SOUTH (returning to familiar location)")
print("-" * 70)
result3 = run_command("south")
narration3 = result3.get("narration", {})
print(f"Success: {result3.get('success')}")
print(f"Primary: {narration3.get('primary_text')}")
print(f"Scene kind: {narration3.get('scope', {}).get('scene_kind')}")
print(f"Familiarity: {narration3.get('scope', {}).get('familiarity')}")
must_mention3 = narration3.get('must_mention')
print(f"\nMust mention present: {must_mention3 is not None}")
if must_mention3:
    print(f"  ⚠️  UNEXPECTED: {must_mention3}")

# Test 4: North again (familiar) - should NOT have must_mention
print("\n\n4. NORTH AGAIN (familiar location)")
print("-" * 70)
result4 = run_command("north")
narration4 = result4.get("narration", {})
print(f"Success: {result4.get('success')}")
print(f"Primary: {narration4.get('primary_text')}")
print(f"Scene kind: {narration4.get('scope', {}).get('scene_kind')}")
print(f"Familiarity: {narration4.get('scope', {}).get('familiarity')}")
must_mention4 = narration4.get('must_mention')
print(f"\nMust mention present: {must_mention4 is not None}")
if must_mention4:
    print(f"  ⚠️  UNEXPECTED: {must_mention4}")

# Test 5: Look - should ALWAYS have must_mention with exits
print("\n\n5. LOOK (explicit request)")
print("-" * 70)
result5 = run_command("look")
narration5 = result5.get("narration", {})
print(f"Success: {result5.get('success')}")
print(f"Primary: {narration5.get('primary_text')}")
print(f"Scene kind: {narration5.get('scope', {}).get('scene_kind')}")
must_mention5 = narration5.get('must_mention')
print(f"\nMust mention present: {must_mention5 is not None}")
if must_mention5:
    print(f"  exits_text: {must_mention5.get('exits_text')}")

print("\n" + "=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)
