"""Behavior management system for entity events."""

from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
import importlib
import os
from pathlib import Path

# Import EventResult from state_accessor to avoid duplication
from src.state_accessor import EventResult


class BehaviorManager:
    """
    Manages loading and invoking entity behaviors.

    Also handles vocabulary extensions and protocol handler registration.
    """

    def __init__(self):
        self._behavior_cache: Dict[str, Callable] = {}
        # Handler storage: verb -> list of (handler, module_name) tuples (in load order)
        self._handlers: Dict[str, List[tuple]] = {}
        # Track module sources for conflict detection
        self._module_sources: Dict[str, str] = {}  # module_name -> source_type
        # Track verb-to-event mappings for conflict detection
        self._verb_event_map: Dict[str, str] = {}  # verb/synonym -> event_name
        # Track which module registered which verb (for error messages)
        self._verb_sources: Dict[str, str] = {}  # verb/synonym -> module_name
        # Track handler position for delegation (used by invoke_previous_handler)
        self._handler_position_list: List[int] = []
        # Store loaded modules for entity behavior invocation
        self._modules: Dict[str, Any] = {}  # module_name -> module object

    def _register_vocabulary(self, vocabulary: dict, module_name: str) -> None:
        """
        Register vocabulary from a module.

        Args:
            vocabulary: The vocabulary dict
            module_name: Module name (for error messages)

        Raises:
            ValueError: If vocabulary conflicts detected
        """
        if "verbs" not in vocabulary:
            return

        for verb_spec in vocabulary["verbs"]:
            word = verb_spec["word"]
            event = verb_spec.get("event")  # Event is optional

            # Register main word
            if event:
                self._register_verb_mapping(word, event, module_name)

            # Register synonyms
            if "synonyms" in verb_spec:
                for synonym in verb_spec["synonyms"]:
                    if event:
                        self._register_verb_mapping(synonym, event, module_name)

    def _register_verb_mapping(self, verb: str, event: str, module_name: str) -> None:
        """
        Register a verb/synonym -> event mapping.

        Args:
            verb: The verb or synonym
            event: The event name
            module_name: Module name (for error messages)

        Raises:
            ValueError: If verb already maps to different event
        """
        if verb in self._verb_event_map:
            existing_event = self._verb_event_map[verb]
            if existing_event != event:
                existing_module = self._verb_sources[verb]
                raise ValueError(
                    f"Vocabulary conflict: verb '{verb}' already maps to '{existing_event}' "
                    f"(from {existing_module}), cannot map to '{event}' (from {module_name})"
                )
            # Same event - allowed (no error)
        else:
            # New mapping - register it
            self._verb_event_map[verb] = event
            self._verb_sources[verb] = module_name

    def _register_handler(self, verb: str, handler: Callable, module_name: str, source_type: str) -> None:
        """
        Register a handler function.

        Args:
            verb: The verb to handle
            handler: The handler function
            module_name: Module name (for error messages)
            source_type: "regular" or "symlink"

        Raises:
            ValueError: If handler conflict detected (same verb, same source type)
        """
        if verb not in self._handlers:
            self._handlers[verb] = []

        # Check for conflicts: same verb from same source type
        for existing_handler, existing_module in self._handlers[verb]:
            existing_source_type = self._module_sources.get(existing_module)

            if existing_source_type == source_type:
                # Conflict: two modules of same source type both define this handler
                raise ValueError(
                    f"Handler conflict: verb '{verb}' already has a handler from {existing_module} "
                    f"(source_type: {existing_source_type}), cannot add handler from {module_name} "
                    f"(source_type: {source_type}). Handlers from the same source type cannot coexist."
                )

        # Add handler to list (in load order) as tuple (handler, module_name)
        self._handlers[verb].append((handler, module_name))

    def _validate_vocabulary(self, vocabulary: Any, module_name: str) -> None:
        """
        Validate vocabulary structure.

        Args:
            vocabulary: The vocabulary dict to validate
            module_name: Module name (for error messages)

        Raises:
            ValueError: If vocabulary structure is invalid
        """
        if not isinstance(vocabulary, dict):
            raise ValueError(f"Module {module_name}: vocabulary must be a dict, got {type(vocabulary).__name__}")

        if "verbs" in vocabulary:
            verbs = vocabulary["verbs"]
            if not isinstance(verbs, list):
                raise ValueError(f"Module {module_name}: vocabulary['verbs'] must be a list, got {type(verbs).__name__}")

            for i, verb_spec in enumerate(verbs):
                if not isinstance(verb_spec, dict):
                    raise ValueError(f"Module {module_name}: verb spec {i} must be a dict, got {type(verb_spec).__name__}")

                # Check required field 'word'
                if "word" not in verb_spec:
                    raise ValueError(f"Module {module_name}: verb spec {i} missing required field 'word'")

                word = verb_spec["word"]
                if not isinstance(word, str) or not word:
                    raise ValueError(f"Module {module_name}: verb spec {i} 'word' must be a non-empty string")

                # Check optional field 'event'
                if "event" in verb_spec:
                    event = verb_spec["event"]
                    if not isinstance(event, str) or not event:
                        raise ValueError(f"Module {module_name}: verb spec {i} 'event' must be a non-empty string")

                # Check optional field 'synonyms'
                if "synonyms" in verb_spec:
                    synonyms = verb_spec["synonyms"]
                    if not isinstance(synonyms, list):
                        raise ValueError(f"Module {module_name}: verb spec {i} 'synonyms' must be a list")

                    for j, synonym in enumerate(synonyms):
                        if not isinstance(synonym, str) or not synonym:
                            raise ValueError(f"Module {module_name}: verb spec {i} synonym {j} must be a non-empty string")

                # Check optional field 'object_required'
                # Accepts: bool, None, or string values like "optional"
                if "object_required" in verb_spec:
                    obj_required = verb_spec["object_required"]
                    if obj_required is not None and not isinstance(obj_required, (bool, str)):
                        raise ValueError(f"Module {module_name}: verb spec {i} 'object_required' must be a bool, str, or None")

    def discover_modules(self, behaviors_dir: str) -> List[tuple]:
        """
        Auto-discover behavior modules in a directory.

        Detects symlinked directories and marks modules found within them
        as source_type="symlink". This allows game-specific handlers to
        override core handlers without conflict errors.

        Args:
            behaviors_dir: Path to behaviors directory

        Returns:
            List of (module_path, source_type) tuples where source_type is
            "symlink" for modules found via symlinked directories, "regular" otherwise.
        """
        path = Path(behaviors_dir)
        if not path.exists():
            return []

        # First, identify which immediate subdirectories are symlinks
        symlinked_dirs = set()
        for item in path.iterdir():
            if item.is_symlink() and item.is_dir():
                symlinked_dirs.add(item.name)

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

                    # Determine source_type based on whether path goes through a symlink
                    # Check if any path component after behaviors_dir is a symlinked dir
                    relative_to_behaviors = py_file.relative_to(path)
                    first_component = relative_to_behaviors.parts[0] if relative_to_behaviors.parts else None
                    source_type = "symlink" if first_component in symlinked_dirs else "regular"

                    modules.append((module_path, source_type))

        return modules

    def load_module(self, module_or_path, source_type: str = "regular") -> None:
        """
        Load a behavior module and register its vocabulary and handlers.

        Args:
            module_or_path: Either an already-imported module object or a module path string
            source_type: "regular" (game-specific code) or "symlink" (core/library code)

        Raises:
            ValueError: If conflicts detected (duplicate handlers/vocabulary in same source type)
        """
        if isinstance(module_or_path, str):
            try:
                module = importlib.import_module(module_or_path)
            except ImportError as e:
                print(f"Warning: Could not load behavior module {module_or_path}: {e}")
                return
            module_name = module_or_path
        else:
            module = module_or_path
            module_name = module.__name__

        # Track module source
        self._module_sources[module_name] = source_type

        # Store module for entity behavior invocation
        self._modules[module_name] = module

        # Validate and register vocabulary
        if hasattr(module, 'vocabulary') and module.vocabulary:
            vocabulary = module.vocabulary
            self._validate_vocabulary(vocabulary, module_name)
            if isinstance(vocabulary, dict):
                self._register_vocabulary(vocabulary, module_name)

        # Register protocol handlers
        for name in dir(module):
            if name.startswith('handle_'):
                verb = name[7:]  # Remove 'handle_' prefix
                handler = getattr(module, name)
                self._register_handler(verb, handler, module_name, source_type)

    def load_modules(self, module_info: List[tuple]) -> None:
        """Load multiple behavior modules.

        Args:
            module_info: List of (module_path, source_type) tuples from discover_modules()
        """
        for module_path, source_type in module_info:
            self.load_module(module_path, source_type)

    def get_loaded_modules(self) -> set:
        """Return set of loaded module names for validation."""
        return set(self._modules.keys())

    def get_merged_vocabulary(self, base_vocab: Dict) -> Dict:
        """
        Merge base vocabulary with vocabulary from all loaded modules.

        Args:
            base_vocab: Base vocabulary dict from vocabulary.json

        Returns:
            Merged vocabulary dict
        """
        result = {
            "verbs": list(base_vocab.get("verbs", [])),
            "nouns": list(base_vocab.get("nouns", [])),
            "adjectives": list(base_vocab.get("adjectives", [])),
            "directions": list(base_vocab.get("directions", [])),
            "prepositions": list(base_vocab.get("prepositions", [])),
            "articles": list(base_vocab.get("articles", []))
        }

        for module in self._modules.values():
            if not hasattr(module, 'vocabulary') or not module.vocabulary:
                continue
            ext = module.vocabulary
            if not isinstance(ext, dict):
                continue

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

        Returns first loaded handler (first in list).

        Args:
            verb: The verb to handle

        Returns:
            Handler function or None
        """
        handlers = self._handlers.get(verb)
        if not handlers or len(handlers) == 0:
            return None

        return handlers[0][0]  # First element of tuple is the handler

    def get_event_for_verb(self, verb: str) -> Optional[str]:
        """
        Get event name for a verb or synonym.

        Args:
            verb: The verb or synonym to look up

        Returns:
            Event name (e.g., "on_take") or None if not registered
        """
        return self._verb_event_map.get(verb)

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
        accessor: Any,
        context: Dict[str, Any]
    ) -> Optional[EventResult]:
        """
        Invoke entity behaviors for an event.

        Invokes all behaviors attached to the entity that define the event handler.
        Multiple behaviors are combined with AND logic (all must allow) and
        messages are concatenated.

        Args:
            entity: Entity object with 'behaviors' field (list or dict)
            event_name: Event name (e.g., "on_take")
            accessor: StateAccessor instance
            context: Event context dict with actor_id, changes, verb

        Returns:
            EventResult with combined allow/message, or None if no behaviors
        """
        if not hasattr(entity, 'behaviors') or not entity.behaviors:
            return None

        # Handle both old (dict) and new (list) behaviors formats
        if isinstance(entity.behaviors, dict):
            # Old format: behaviors = {"on_event": "module:function"}
            behavior_path = entity.behaviors.get(event_name)
            if not behavior_path:
                return None

            behavior_func = self.load_behavior(behavior_path)
            if not behavior_func:
                return None

            try:
                # Old format uses state parameter instead of accessor
                # For backward compatibility, try to get state from accessor
                state = accessor.game_state if hasattr(accessor, 'game_state') else accessor
                result = behavior_func(entity, state, context)

                if not isinstance(result, EventResult):
                    return None

                return result

            except Exception as e:
                import traceback
                traceback.print_exc()
                return None

        elif isinstance(entity.behaviors, list):
            # New format: behaviors = ["module1", "module2"]
            results = []

            for behavior_module_name in entity.behaviors:
                # Look up loaded module
                module = self._modules.get(behavior_module_name)
                if not module:
                    # Module not loaded, skip
                    continue

                # Check if module has event handler function
                if not hasattr(module, event_name):
                    # This module doesn't handle this event, skip
                    continue

                # Get handler function
                handler = getattr(module, event_name)

                try:
                    # Call handler with entity, accessor, context
                    result = handler(entity, accessor, context)

                    if isinstance(result, EventResult):
                        results.append(result)

                except Exception as e:
                    import traceback
                    import sys
                    print(f"Error invoking behavior {behavior_module_name}.{event_name}:", file=sys.stderr)
                    traceback.print_exc()
                    # Continue with other behaviors

            # If no behaviors were invoked, return None
            if not results:
                return None

            # Combine results: AND logic for allow, concatenate messages
            combined_allow = all(r.allow for r in results)
            messages = [r.message for r in results if r.message]
            combined_message = "\n".join(messages) if messages else None

            return EventResult(allow=combined_allow, message=combined_message)

        else:
            # Unknown format
            return None

    def invoke_handler(self, verb: str, accessor, action: Dict[str, Any]):
        """
        Invoke a registered command handler.

        Manages position list lifecycle for handler chaining support.

        Args:
            verb: The verb to handle (e.g., "take", "drop")
            accessor: StateAccessor instance
            action: Action dict with actor_id and other parameters

        Returns:
            HandlerResult from handler, or None if no handler registered
        """
        handlers = self._handlers.get(verb)
        if not handlers or len(handlers) == 0:
            return None

        # Initialize position list
        self._handler_position_list = [0]

        try:
            # Get first handler (tuple of handler, module_name)
            handler = handlers[0][0]
            return handler(accessor, action)

        finally:
            # Always clean up position list
            self._handler_position_list = []

    def invoke_previous_handler(self, verb: str, accessor, action: Dict[str, Any]):
        """
        Invoke the next handler in the chain (delegation).

        Called by handlers to delegate to the next handler in load order.
        Manages position list to track current position in handler chain.

        Args:
            verb: The verb being handled
            accessor: StateAccessor instance
            action: Action dict

        Returns:
            HandlerResult from next handler, or None if at end of chain

        Raises:
            RuntimeError: If position list not initialized (not called from invoke_handler)
        """
        # Check position list is initialized
        if not self._handler_position_list:
            raise RuntimeError(
                "Handler position list not initialized. "
                "invoke_previous_handler() can only be called from within a handler "
                "invoked via invoke_handler()."
            )

        # Get handlers list
        handlers = self._handlers.get(verb)
        if not handlers or not isinstance(handlers, list):
            return None

        # Get current position and calculate next
        current_pos = self._handler_position_list[-1]
        next_pos = current_pos + 1

        # Check if we're at end of chain
        if next_pos >= len(handlers):
            return None

        # Append next position to list
        self._handler_position_list.append(next_pos)

        try:
            # Get next handler (tuple of handler, module_name)
            next_handler = handlers[next_pos][0]
            return next_handler(accessor, action)

        finally:
            # Pop position from list
            self._handler_position_list.pop()

    def clear_cache(self):
        """Clear behavior cache (useful for hot reload)."""
        self._behavior_cache.clear()


# Global instance
_behavior_manager = BehaviorManager()


def get_behavior_manager() -> BehaviorManager:
    """Get the global behavior manager instance."""
    return _behavior_manager
