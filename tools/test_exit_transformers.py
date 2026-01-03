#!/usr/bin/env python3
"""Test script for Exit migration transformers."""

import libcst as cst
from libcst_transformers import (
    ReplaceExitDescriptorImport,
    ClearLocationExits,
    AddIndexBuildingCalls
)

# Test input
TEST_CODE = """
from src.state_manager import GameState, Location, ExitDescriptor, Metadata
from src.state_accessor import StateAccessor

def test_example():
    game_state = GameState(
        metadata=Metadata(title="Test"),
        locations=[
            Location(
                id="room1",
                name="Room 1",
                exits={
                    "north": ExitDescriptor(
                        type="open",
                        to="room2"
                    )
                }
            ),
            Location(
                id="room2",
                name="Room 2",
                exits={}
            )
        ],
        exits=[],
        actors={}
    )

    accessor = StateAccessor(game_state, None)
"""

def main():
    """Test the transformers."""
    print("Original code:")
    print(TEST_CODE)
    print("\n" + "="*60 + "\n")

    # Parse code
    tree = cst.parse_module(TEST_CODE)

    # Apply transformers
    print("Applying ReplaceExitDescriptorImport...")
    transformer1 = ReplaceExitDescriptorImport()
    tree = tree.visit(transformer1)
    print(f"  Changes: {transformer1.changes}")

    print("\nApplying ClearLocationExits...")
    transformer2 = ClearLocationExits()
    tree = tree.visit(transformer2)
    print(f"  Changes: {transformer2.changes}")

    print("\nApplying AddIndexBuildingCalls...")
    transformer3 = AddIndexBuildingCalls()
    tree = tree.visit(transformer3)
    print(f"  Changes: {transformer3.changes}")

    print("\n" + "="*60 + "\n")
    print("Transformed code:")
    print(tree.code)

if __name__ == "__main__":
    main()
