#!/usr/bin/env python3
"""Validate game state reaction configurations.

Runs comprehensive validation checks on game_state.json:
1. Handler path resolution
2. Schema validation
3. Cross-reference validation
4. Entity capability validation
5. Effect compatibility validation

Usage:
    python tools/validate_game_state.py examples/big_game
"""

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from behaviors.shared.infrastructure.reaction_effects import EFFECT_REGISTRY
from behaviors.shared.infrastructure.reaction_conditions import CONDITION_REGISTRY
from behaviors.shared.infrastructure.reaction_specs import REACTION_SPECS


class ValidationError:
    """Represents a validation error."""
    def __init__(self, category: str, entity_id: str, message: str, severity: str = "error"):
        self.category = category
        self.entity_id = entity_id
        self.message = message
        self.severity = severity

    def __str__(self):
        symbol = "✗" if self.severity == "error" else "⚠"
        return f"{symbol} [{self.category}] {self.entity_id}: {self.message}"


class GameStateValidator:
    """Validates game state reaction configurations."""

    def __init__(self, game_dir: Path):
        self.game_dir = game_dir
        self.game_state_path = game_dir / "game_state.json"
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

        with open(self.game_state_path) as f:
            self.game_state = json.load(f)

    def validate_all(self) -> bool:
        """Run all validation checks. Returns True if no errors."""
        print(f"Validating {self.game_state_path}...")
        print()

        self.validate_handler_paths()
        self.validate_schemas()
        self.validate_cross_references()
        self.validate_entity_capabilities()
        self.validate_effect_compatibility()

        return self.report_results()

    def validate_handler_paths(self):
        """Validation 1: Verify all handler paths can be imported."""
        print("1. Handler Path Resolution...")

        for entity_type in ['actors', 'items']:
            entities = self.game_state.get(entity_type, {} if entity_type == 'actors' else [])
            if entity_type == 'actors':
                entities = entities.values()

            for entity in entities:
                entity_id = entity.get('id')
                props = entity.get('properties', {})

                for reaction_type in REACTION_SPECS.keys():
                    config = props.get(reaction_type, {})
                    handler_path = config.get('handler')

                    if handler_path:
                        self._validate_handler_import(entity_id, reaction_type, handler_path)

    def _validate_handler_import(self, entity_id: str, reaction_type: str, handler_path: str):
        """Try to import and load a handler function."""
        try:
            if ':' not in handler_path:
                self.errors.append(ValidationError(
                    "handler_path",
                    entity_id,
                    f"{reaction_type}.handler '{handler_path}' invalid format (needs module:function)"
                ))
                return

            module_path, func_name = handler_path.rsplit(':', 1)
            module = importlib.import_module(module_path)

            if not hasattr(module, func_name):
                self.errors.append(ValidationError(
                    "handler_path",
                    entity_id,
                    f"{reaction_type}.handler function '{func_name}' not found in {module_path}"
                ))
        except Exception as e:
            self.errors.append(ValidationError(
                "handler_path",
                entity_id,
                f"{reaction_type}.handler import failed: {e}"
            ))

    def validate_schemas(self):
        """Validation 2: Validate configs against effect/condition schemas."""
        print("2. Schema Validation...")

        # Build valid keys from registries
        valid_effect_keys = set(EFFECT_REGISTRY.keys())
        valid_condition_keys = set(CONDITION_REGISTRY.keys())
        valid_keys = valid_effect_keys | valid_condition_keys | {
            'handler', 'message', 'response', 'accept_message', 'reject_message',
            'encounter_message', 'death_message', 'summary', 'accepted_items',
            'keywords', 'requires_state', 'requires_trust', 'requires_items',
            'requires_flags', 'requires_not_flags', 'failure_message',
            'progressive_reveals', 'default_response', 'consequence_message',
            'tick_message', 'entry_message', 'reveal_message'
        }

        for entity_type in ['actors', 'items']:
            entities = self.game_state.get(entity_type, {} if entity_type == 'actors' else [])
            if entity_type == 'actors':
                entities = entities.values()

            for entity in entities:
                entity_id = entity.get('id')
                props = entity.get('properties', {})

                for reaction_type, config in props.items():
                    if reaction_type not in REACTION_SPECS:
                        continue

                    if isinstance(config, dict):
                        self._validate_config_keys(entity_id, reaction_type, config, valid_keys)

    def _validate_config_keys(self, entity_id: str, reaction_type: str, config: Dict, valid_keys: set):
        """Check for invalid keys in config."""
        # Skip if handler-only
        if 'handler' in config and len(config) == 1:
            return

        for key in config.keys():
            if key not in valid_keys and not key.startswith('_'):
                self.warnings.append(ValidationError(
                    "schema",
                    entity_id,
                    f"{reaction_type}.{key} is not a recognized effect/condition",
                    severity="warning"
                ))

    def validate_cross_references(self):
        """Validation 3: Verify referenced items/states/commitments exist."""
        print("3. Cross-Reference Validation...")

        # Build lookup tables
        all_items = {item['id'] for item in self.game_state.get('items', [])}

        for entity_type in ['actors', 'items']:
            entities = self.game_state.get(entity_type, {} if entity_type == 'actors' else [])
            if entity_type == 'actors':
                entities = entities.values()

            for entity in entities:
                entity_id = entity.get('id')
                props = entity.get('properties', {})

                for reaction_type, config in props.items():
                    if reaction_type not in REACTION_SPECS:
                        continue

                    if isinstance(config, dict):
                        self._validate_item_references(entity_id, reaction_type, config, all_items)

    def _validate_item_references(self, entity_id: str, reaction_type: str, config: Dict, all_items: set):
        """Check that referenced items exist."""
        # Check accepted_items
        accepted = config.get('accepted_items', [])
        for item_ref in accepted:
            # Item refs can be substrings, so we check if ANY item contains the ref
            if not any(item_ref.lower() in item_id.lower() for item_id in all_items):
                self.warnings.append(ValidationError(
                    "cross_ref",
                    entity_id,
                    f"{reaction_type}.accepted_items references '{item_ref}' which matches no items",
                    severity="warning"
                ))

        # Check grant_items
        granted = config.get('grant_items', [])
        for item_id in granted:
            if item_id not in all_items:
                self.errors.append(ValidationError(
                    "cross_ref",
                    entity_id,
                    f"{reaction_type}.grant_items references non-existent item '{item_id}'"
                ))

    def validate_entity_capabilities(self):
        """Validation 4: Check entities have appropriate reaction types."""
        print("4. Entity Capability Validation...")

        # Note: item_use_reactions can be on BOTH items (self-use) AND actors (as targets)
        # take_reactions can be on items to detect theft
        # So capability validation is informational only

        valid_actor_reactions = {
            'gift_reactions', 'encounter_reactions', 'death_reactions',
            'dialog_reactions', 'combat_reactions', 'commitment_reactions',
            'item_use_reactions'  # Actors as targets
        }
        valid_item_reactions = {
            'item_use_reactions', 'take_reactions', 'examine_reactions'
        }
        valid_location_reactions = {
            'entry_reactions', 'turn_environmental'
        }

        # Validate actors
        for actor in self.game_state.get('actors', {}).values():
            entity_id = actor.get('id')
            props = actor.get('properties', {})

            for reaction_type in props.keys():
                if reaction_type in REACTION_SPECS and reaction_type not in valid_actor_reactions:
                    self.warnings.append(ValidationError(
                        "capability",
                        entity_id,
                        f"Actor has {reaction_type} (unusual for actors)",
                        severity="warning"
                    ))

        # Validate items
        for item in self.game_state.get('items', []):
            entity_id = item.get('id')
            props = item.get('properties', {})

            for reaction_type in props.keys():
                if reaction_type in REACTION_SPECS and reaction_type not in valid_item_reactions:
                    self.warnings.append(ValidationError(
                        "capability",
                        entity_id,
                        f"Item has {reaction_type} (unusual for items)",
                        severity="warning"
                    ))

    def validate_effect_compatibility(self):
        """Validation 5: Check effects have required properties."""
        print("5. Effect Compatibility Validation...")

        for entity_type in ['actors', 'items']:
            entities = self.game_state.get(entity_type, {} if entity_type == 'actors' else [])
            if entity_type == 'actors':
                entities = entities.values()

            for entity in entities:
                entity_id = entity.get('id')
                props = entity.get('properties', {})

                # Check for trust_delta without trust_state
                for reaction_type, config in props.items():
                    if reaction_type not in REACTION_SPECS or not isinstance(config, dict):
                        continue

                    if 'trust_delta' in config or 'trust_transitions' in config:
                        if 'trust_state' not in props:
                            self.errors.append(ValidationError(
                                "compatibility",
                                entity_id,
                                f"{reaction_type} uses trust effects but entity has no trust_state property"
                            ))

                    if 'transition_to' in config or 'requires_state' in config:
                        if 'state_machine' not in props:
                            self.warnings.append(ValidationError(
                                "compatibility",
                                entity_id,
                                f"{reaction_type} uses state effects but entity has no state_machine property",
                                severity="warning"
                            ))

    def report_results(self) -> bool:
        """Print validation results and return success status."""
        print()
        print("=" * 70)

        if self.errors:
            print(f"\n❌ {len(self.errors)} ERRORS FOUND:\n")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print(f"\n⚠️  {len(self.warnings)} WARNINGS:\n")
            for warning in self.warnings:
                print(f"  {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ All validations passed!")
        elif not self.errors:
            print(f"\n✅ No errors (but {len(self.warnings)} warnings)")

        print()
        return len(self.errors) == 0


def main():
    parser = argparse.ArgumentParser(description="Validate game state reaction configurations")
    parser.add_argument("game_dir", help="Path to game directory containing game_state.json")
    args = parser.parse_args()

    game_dir = Path(args.game_dir)
    if not game_dir.exists():
        print(f"Error: Directory {game_dir} does not exist")
        sys.exit(1)

    if not (game_dir / "game_state.json").exists():
        print(f"Error: {game_dir}/game_state.json not found")
        sys.exit(1)

    validator = GameStateValidator(game_dir)
    success = validator.validate_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
