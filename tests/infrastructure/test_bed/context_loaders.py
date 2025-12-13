"""
Context Loaders for Test Bed

Load game state from various sources for region testing.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.types import ActorId, ItemId, LocationId

if TYPE_CHECKING:
    from src.state_manager import GameState


class ContextLoader(ABC):
    """Abstract base for context loaders."""

    @abstractmethod
    def load(self) -> "GameState":
        """Load and return a GameState."""
        ...

    @abstractmethod
    def get_description(self) -> str:
        """Return a description of this context."""
        ...


class FreshContextLoader(ContextLoader):
    """Load fresh game state from a JSON file."""

    def __init__(self, game_state_path: str | Path) -> None:
        """Initialize with path to game_state.json."""
        self.path = Path(game_state_path)
        if not self.path.exists():
            raise FileNotFoundError(f"Game state file not found: {self.path}")

    def load(self) -> "GameState":
        """Load fresh game state from file."""
        from src.state_manager import load_game_state

        return load_game_state(str(self.path))

    def get_description(self) -> str:
        """Return description of this context."""
        return f"Fresh context from {self.path.name}"


class CustomContextLoader(ContextLoader):
    """Load game state with custom modifications."""

    def __init__(
        self,
        base_loader: ContextLoader,
        flags: dict[str, bool | int] | None = None,
        trust_values: dict[str, int] | None = None,
        actor_locations: dict[str, str] | None = None,
        item_locations: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Initialize with base loader and modifications.

        Args:
            base_loader: Base context to modify
            flags: Global flags to set
            trust_values: Actor ID -> trust value
            actor_locations: Actor ID -> location ID
            item_locations: Item ID -> location ID or holder
            extra: Additional extra dict values
        """
        self.base_loader = base_loader
        self.flags = flags or {}
        self.trust_values = trust_values or {}
        self.actor_locations = actor_locations or {}
        self.item_locations = item_locations or {}
        self.extra = extra or {}

    def load(self) -> "GameState":
        """Load base state and apply modifications."""
        state = self.base_loader.load()

        # Apply flags
        if "flags" not in state.extra:
            state.extra["flags"] = {}
        for flag_name, value in self.flags.items():
            state.extra["flags"][flag_name] = value

        # Apply trust values
        for actor_id_str, trust in self.trust_values.items():
            actor_id = ActorId(actor_id_str)
            if actor_id in state.actors:
                actor = state.actors[actor_id]
                if "trust" not in actor.properties:
                    actor.properties["trust"] = {}
                actor.properties["trust"]["current"] = trust

        # Apply actor locations
        for actor_id_str, location in self.actor_locations.items():
            actor_id = ActorId(actor_id_str)
            if actor_id in state.actors:
                state.actors[actor_id].location = LocationId(location)

        # Apply item locations
        for item_id_str, location in self.item_locations.items():
            item_id = ItemId(item_id_str)
            for item in state.items:
                if item.id == item_id:
                    if location.startswith("actor:"):
                        # Move to actor's inventory
                        holder_id = ActorId(location[6:])
                        item.location = None  # type: ignore[assignment]
                        if holder_id in state.actors:
                            if item_id not in state.actors[holder_id].inventory:
                                state.actors[holder_id].inventory.append(item_id)
                    else:
                        # Move to location
                        item.location = LocationId(location)
                        # Remove from any inventory
                        for actor in state.actors.values():
                            if item_id in actor.inventory:
                                actor.inventory.remove(item_id)
                    break

        # Apply extra values
        for key, value in self.extra.items():
            state.extra[key] = value

        return state

    def get_description(self) -> str:
        """Return description of this context."""
        mods = []
        if self.flags:
            mods.append(f"{len(self.flags)} flags")
        if self.trust_values:
            mods.append(f"{len(self.trust_values)} trust values")
        if self.actor_locations:
            mods.append(f"{len(self.actor_locations)} actor locations")
        if self.item_locations:
            mods.append(f"{len(self.item_locations)} item locations")

        base = self.base_loader.get_description()
        if mods:
            return f"{base} + {', '.join(mods)}"
        return base


class InMemoryContextLoader(ContextLoader):
    """Load game state from in-memory dict (for testing)."""

    def __init__(self, state_dict: dict[str, Any], description: str = "In-memory") -> None:
        """Initialize with state dictionary."""
        self.state_dict = state_dict
        self._description = description

    def load(self) -> "GameState":
        """Load game state from dict."""
        from src.state_manager import load_game_state

        return load_game_state(self.state_dict)

    def get_description(self) -> str:
        """Return description of this context."""
        return self._description
