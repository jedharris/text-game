"""Behavior management system for entity events."""

from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
import importlib
import os
from pathlib import Path


@dataclass
class EventResult:
    """Result from an event handler."""
    allow: bool = True
    message: Optional[str] = None


class BehaviorManager:
    """
    Manages loading and invoking entity behaviors.

    Also handles vocabulary extensions and protocol handler registration.
    """

    def __init__(self):
        self._behavior_cache: Dict[str, Callable] = {}
        self._handlers: Dict[str, Callable] = {}  # verb -> handler function
        self._vocabulary_extensions: List[Dict] = []

    def discover_modules(self, behaviors_dir: str) -> List[str]:
        """
        Auto-discover behavior modules in a directory.

        Args:
            behaviors_dir: Path to behaviors directory

        Returns:
            List of module paths (e.g., ["behaviors.core.consumables"])
        """
        path = Path(behaviors_dir)
        if not path.exists():
            return []

        modules = []

        # Walk through directory, following symlinks
        for root, dirs, files in os.walk(str(path), followlinks=True):
            for filename in files:
                if filename.endswith('.py') and filename != '__init__.py':
                    # Convert path to module name
                    # e.g., behaviors/core/consumables.py -> behaviors.core.consumables
                    py_file = Path(root) / filename
                    relative = py_file.relative_to(path.parent)
                    module_path = str(relative.with_suffix("")).replace("/", ".").replace("\\", ".")
                    modules.append(module_path)

        return modules

    def load_module(self, module_path: str) -> None:
        """
        Load a behavior module and register its extensions.

        Args:
            module_path: Python module path (e.g., "behaviors.core.consumables")
        """
        try:
            module = importlib.import_module(module_path)
        except ImportError as e:
            print(f"Warning: Could not load behavior module {module_path}: {e}")
            return

        # Register vocabulary extensions
        if hasattr(module, 'vocabulary') and module.vocabulary:
            self._vocabulary_extensions.append(module.vocabulary)

        # Register protocol handlers
        for name in dir(module):
            if name.startswith('handle_'):
                verb = name[7:]  # Remove 'handle_' prefix
                handler = getattr(module, name)
                self._handlers[verb] = handler

    def load_modules(self, module_paths: List[str]) -> None:
        """Load multiple behavior modules."""
        for path in module_paths:
            self.load_module(path)

    def get_merged_vocabulary(self, base_vocab: Dict) -> Dict:
        """
        Merge base vocabulary with all extensions.

        Args:
            base_vocab: Base vocabulary dict from vocabulary.json

        Returns:
            Merged vocabulary dict
        """
        result = {
            "verbs": list(base_vocab.get("verbs", [])),
            "nouns": list(base_vocab.get("nouns", [])),
            "adjectives": list(base_vocab.get("adjectives", [])),
            "directions": list(base_vocab.get("directions", []))
        }

        for ext in self._vocabulary_extensions:
            # Merge verbs (avoid duplicates by word)
            existing_words = {v["word"] for v in result["verbs"]}
            for verb in ext.get("verbs", []):
                if verb["word"] not in existing_words:
                    result["verbs"].append(verb)
                    existing_words.add(verb["word"])

            # Merge nouns
            existing_nouns = {n["word"] for n in result["nouns"]}
            for noun in ext.get("nouns", []):
                if noun["word"] not in existing_nouns:
                    result["nouns"].append(noun)
                    existing_nouns.add(noun["word"])

            # Merge adjectives
            existing_adjs = {a["word"] for a in result["adjectives"]}
            for adj in ext.get("adjectives", []):
                if adj["word"] not in existing_adjs:
                    result["adjectives"].append(adj)
                    existing_adjs.add(adj["word"])

            # Merge directions
            existing_dirs = {d["word"] for d in result["directions"]}
            for direction in ext.get("directions", []):
                if direction["word"] not in existing_dirs:
                    result["directions"].append(direction)
                    existing_dirs.add(direction["word"])

        return result

    def get_handler(self, verb: str) -> Optional[Callable]:
        """
        Get registered handler for a verb.

        Args:
            verb: The verb to handle

        Returns:
            Handler function or None
        """
        return self._handlers.get(verb)

    def has_handler(self, verb: str) -> bool:
        """Check if a handler is registered for this verb."""
        return verb in self._handlers

    def load_behavior(self, behavior_path: str) -> Optional[Callable]:
        """
        Load a behavior function from module path.

        Args:
            behavior_path: "module.path:function_name"

        Returns:
            Callable behavior function or None
        """
        if behavior_path in self._behavior_cache:
            return self._behavior_cache[behavior_path]

        try:
            module_path, function_name = behavior_path.split(':')
            module = importlib.import_module(module_path)
            behavior_func = getattr(module, function_name)
            self._behavior_cache[behavior_path] = behavior_func
            return behavior_func

        except (ValueError, ImportError, AttributeError) as e:
            print(f"Warning: Could not load behavior {behavior_path}: {e}")
            return None

    def invoke_behavior(
        self,
        entity: Any,
        event_name: str,
        state: Any,
        context: Dict[str, Any]
    ) -> Optional[EventResult]:
        """
        Invoke a behavior for an entity event.

        Args:
            entity: Entity object with 'behaviors' dict
            event_name: Event name (e.g., "on_drink")
            state: Current GameState
            context: Event context dict

        Returns:
            EventResult or None if no behavior attached
        """
        if not hasattr(entity, 'behaviors') or not entity.behaviors:
            return None

        # Handle both old (dict) and new (list) behaviors formats
        if isinstance(entity.behaviors, dict):
            # Old format: behaviors = {"on_event": "module:function"}
            behavior_path = entity.behaviors.get(event_name)
            if not behavior_path:
                return None
        elif isinstance(entity.behaviors, list):
            # New format: behaviors = ["module1", "module2"]
            # For now, we can't map events to specific modules in list format
            # This is handled by the new BehaviorManager (not yet implemented)
            # Return None for now - the new system will handle this
            return None
        else:
            return None

        behavior_func = self.load_behavior(behavior_path)
        if not behavior_func:
            return None

        try:
            result = behavior_func(entity, state, context)

            if not isinstance(result, EventResult):
                return None

            return result

        except Exception as e:
            import traceback
            traceback.print_exc()
            return None

    def clear_cache(self):
        """Clear behavior cache (useful for hot reload)."""
        self._behavior_cache.clear()


# Global instance
_behavior_manager = BehaviorManager()


def get_behavior_manager() -> BehaviorManager:
    """Get the global behavior manager instance."""
    return _behavior_manager
