"""Behavior management system for entity events."""

from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
import importlib
import os
from pathlib import Path

# Import EventResult from state_accessor to avoid duplication
from src.state_accessor import EventResult
from src.types import EventName, HookName


@dataclass
class EventInfo:
    """Metadata about a registered event type."""
    event_name: str                              # e.g., "on_damage"
    registered_by: List[str] = field(default_factory=list)  # Module names that register this event
    description: Optional[str] = None            # Optional documentation
    hook: Optional[str] = None                   # Engine hook name, if any


class BehaviorManager:
    """
    Manages loading and invoking entity behaviors.

    Also handles vocabulary extensions and protocol handler registration.
    """

    def __init__(self):
        self._behavior_cache: Dict[str, Callable] = {}
        # Handler storage: verb -> list of (tier, handler, module_name) tuples (sorted by tier)
        self._handlers: Dict[str, List[tuple]] = {}
        # Track verb-to-event mappings with tiers: verb -> list of (tier, event_name) tuples
        self._verb_event_map: Dict[str, List[tuple]] = {}  # verb/synonym -> [(tier, event_name)]
        # Track which module registered which verb+tier (for error messages)
        self._verb_tier_sources: Dict[tuple, str] = {}  # (verb, tier) -> module_name
        # Store loaded modules for entity behavior invocation
        self._modules: Dict[str, Any] = {}  # module_name -> module object
        # Event registry: event_name -> EventInfo
        self._event_registry: Dict[str, EventInfo] = {}
        # Hook to event mapping: hook_name -> (event_name, tier)
        self._hook_to_event: Dict[str, tuple] = {}
        # Event fallbacks: event_name -> fallback_event_name
        self._fallback_events: Dict[str, str] = {}

    def _calculate_tier(self, behavior_file_path: str, base_behavior_dir: str) -> int:
        """
        Calculate tier (precedence level) based on directory depth.

        Args:
            behavior_file_path: Absolute path to behavior file
            base_behavior_dir: Absolute path to base behaviors directory

        Returns:
            Tier number (1 = highest precedence, 2 = next, etc.)
            Tier = depth + 1, where depth is subdirectory levels below base
        """
        from pathlib import Path

        behavior_path = Path(behavior_file_path)
        base_path = Path(base_behavior_dir)

        # Get relative path from base to behavior file
        try:
            relative_path = behavior_path.relative_to(base_path)
        except ValueError:
            # behavior_file_path is not relative to base_behavior_dir
            raise ValueError(
                f"Behavior file {behavior_file_path} is not under base directory {base_behavior_dir}"
            )

        # Calculate depth: number of directory levels (excluding the file itself)
        # e.g., "consumables.py" -> 0 levels (Tier 1)
        #       "library/examine.py" -> 1 level (Tier 2)
        #       "library/core/basic.py" -> 2 levels (Tier 3)
        depth = len(relative_path.parts) - 1  # -1 to exclude filename

        # Tier = depth + 1 (so Tier 1 is highest precedence)
        return depth + 1

    def _register_vocabulary(self, vocabulary: dict, module_name: str, tier: int) -> None:
        """
        Register vocabulary from a module.

        Args:
            vocabulary: The vocabulary dict
            module_name: Module name (for error messages)
            tier: Tier number (1 = highest precedence)

        Raises:
            ValueError: If vocabulary conflicts detected
        """
        # Register verbs and their events
        for verb_spec in vocabulary.get("verbs", []):
            word = verb_spec["word"]
            event = verb_spec.get("event")  # Event is optional

            # Register main word
            if event:
                self._register_verb_mapping(word, event, module_name, tier)
                # Also register the event in the event registry
                self._register_event(event, module_name, tier)
                # Register fallback relationship if specified
                if fallback := verb_spec.get("fallback_event"):
                    self._fallback_events[event] = fallback

            # Register synonyms
            if "synonyms" in verb_spec:
                for synonym in verb_spec["synonyms"]:
                    if event:
                        self._register_verb_mapping(synonym, event, module_name, tier)

        # Register explicit events (with optional hooks)
        for event_spec in vocabulary.get("events", []):
            event_name = event_spec["event"]
            self._register_event(
                event_name,
                module_name,
                tier,
                description=event_spec.get("description"),
                hook=event_spec.get("hook")
            )

    def _register_event(
        self,
        event_name: str,
        module_name: str,
        tier: int,
        description: Optional[str] = None,
        hook: Optional[str] = None
    ) -> None:
        """
        Register an event in the event registry.

        Args:
            event_name: The event name (e.g., "on_take")
            module_name: Module name registering this event
            tier: Tier number (1 = highest precedence)
            description: Optional documentation for the event
            hook: Optional engine hook name

        Raises:
            ValueError: If hook conflict detected at same tier
        """
        if event_name not in self._event_registry:
            self._event_registry[event_name] = EventInfo(
                event_name=event_name,
                registered_by=[module_name],
                description=description,
                hook=hook
            )
        else:
            info = self._event_registry[event_name]
            if module_name not in info.registered_by:
                info.registered_by.append(module_name)
            # First description wins
            if description and not info.description:
                info.description = description

        # Register hook mapping with tier-based precedence
        if hook:
            if hook in self._hook_to_event:
                existing_event, existing_tier = self._hook_to_event[hook]
                if existing_event != event_name:
                    if existing_tier == tier:
                        # Same tier, different events = conflict
                        raise ValueError(
                            f"Hook '{hook}' conflict at tier {tier}: "
                            f"already mapped to '{existing_event}', "
                            f"cannot also map to '{event_name}'"
                        )
                    elif tier < existing_tier:
                        # New registration has higher precedence (lower tier)
                        self._hook_to_event[hook] = (event_name, tier)
                    # else: existing has higher precedence, keep it
            else:
                self._hook_to_event[hook] = (event_name, tier)

    def _register_verb_mapping(self, verb: str, event: str, module_name: str, tier: int) -> None:
        """
        Register a verb/synonym -> event mapping with tier.

        Args:
            verb: The verb or synonym
            event: The event name
            module_name: Module name (for error messages)
            tier: Tier number (1 = highest precedence)

        Raises:
            ValueError: If verb+tier already maps to different event (within-tier conflict)
        """
        # Initialize list if needed
        if verb not in self._verb_event_map:
            self._verb_event_map[verb] = []

        # Check for within-tier conflict
        existing_events = self._verb_event_map[verb]
        for existing_tier, existing_event in existing_events:
            if existing_tier == tier and existing_event != event:
                # Conflict: same verb+tier, different event
                existing_module = self._verb_tier_sources.get((verb, tier), "unknown")
                raise ValueError(
                    f"Vocabulary conflict: verb '{verb}' in Tier {tier} already maps to '{existing_event}' "
                    f"(from {existing_module}), cannot map to '{event}' (from {module_name})"
                )
            elif existing_tier == tier and existing_event == event:
                # Same verb+tier+event - allowed, but don't add duplicate
                return

        # No conflict - add the mapping
        self._verb_event_map[verb].append((tier, event))
        self._verb_tier_sources[(verb, tier)] = module_name

        # Keep list sorted by tier (lowest/highest precedence first)
        self._verb_event_map[verb].sort(key=lambda x: x[0])

    def _register_handler(self, verb: str, handler: Callable, module_name: str, tier: int) -> None:
        """
        Register a protocol handler with tier-based conflict detection.

        Args:
            verb: The verb to handle
            handler: The handler function
            module_name: Module name (for error messages)
            tier: Tier number (1 = highest precedence)

        """
        if verb not in self._handlers:
            self._handlers[verb] = []

        # Check for duplicate registration (same verb+tier+module)
        for existing_tier, existing_handler, existing_module in self._handlers[verb]:
            if existing_tier == tier and existing_module == module_name:
                # Same verb+tier+module - don't add duplicate
                return

        # Add the handler - multiple handlers per verb per tier are allowed
        # Handlers are tried in order and the first successful one is used
        self._handlers[verb].append((tier, handler, module_name))

        # Keep list sorted by tier (lowest/highest precedence first)
        # Within a tier, handlers are tried in registration order (deterministic based on module load order)
        self._handlers[verb].sort(key=lambda x: x[0])

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

        Calculates tier based on directory depth.

        Args:
            behaviors_dir: Path to behaviors directory

        Returns:
            List of (module_path, tier) tuples where tier is precedence level
            (1 = highest, based on directory depth)
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

                    # Calculate tier from directory depth
                    tier = self._calculate_tier(str(py_file), str(path))

                    modules.append((module_path, tier))

        return modules

    def load_module(self, module_or_path, tier: int = 1) -> None:
        """
        Load a behavior module and register its vocabulary and handlers.

        Args:
            module_or_path: Either an already-imported module object or a module path string
            tier: Tier number (1 = highest precedence, based on directory depth)

        Raises:
            ValueError: If conflicts detected (duplicate handlers/vocabulary within same tier)
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

        # Store module for entity behavior invocation
        self._modules[module_name] = module

        # Validate and register vocabulary
        if hasattr(module, 'vocabulary') and module.vocabulary:
            vocabulary = module.vocabulary
            self._validate_vocabulary(vocabulary, module_name)
            if isinstance(vocabulary, dict):
                self._register_vocabulary(vocabulary, module_name, tier)

        # Register protocol handlers
        for name in dir(module):
            if name.startswith('handle_'):
                verb = name[7:]  # Remove 'handle_' prefix
                handler = getattr(module, name)
                self._register_handler(verb, handler, module_name, tier)

    def load_modules(self, module_info: List[tuple]) -> None:
        """Load multiple behavior modules.

        Args:
            module_info: List of (module_path, tier) tuples from discover_modules()
        """
        for module_path, tier in module_info:
            self.load_module(module_path, tier=tier)

    def get_loaded_modules(self) -> set:
        """Return set of loaded module names for validation."""
        return set(self._modules.keys())

    def _merge_types(self, type1, type2) -> list:
        """
        Merge two word_type values into a multi-type list.

        Args:
            type1, type2: Can be strings, lists, or None

        Returns:
            Sorted list of unique types
        """
        types = set()

        # Add type1
        if isinstance(type1, list):
            types.update(type1)
        elif type1:
            types.add(type1)

        # Add type2
        if isinstance(type2, list):
            types.update(type2)
        elif type2:
            types.add(type2)

        return sorted(list(types))

    def _section_to_type(self, section: str) -> str:
        """
        Map vocabulary section name to type string.

        Args:
            section: Section name (verbs, nouns, adjectives)

        Returns:
            Type string (verb, noun, adjective)
        """
        mapping = {
            "verbs": "verb",
            "nouns": "noun",
            "adjectives": "adjective",
        }
        return mapping.get(section, "noun")

    def _rebuild_vocab_from_map(self, word_map: Dict) -> Dict:
        """
        Rebuild vocabulary dict from word map.

        For multi-type words, uses the first type encountered in the original
        vocabulary (stored in _original_section) to determine placement.
        For single-type words, uses the word_type field.

        Args:
            word_map: Dict mapping word -> entry dict

        Returns:
            Vocabulary dict with verbs, nouns, adjectives sections
        """
        vocab: Dict[str, List[Dict[str, Any]]] = {
            "verbs": [],
            "nouns": [],
            "adjectives": [],
            "prepositions": [],
            "articles": []
        }

        for word, entry in word_map.items():
            word_type = entry.get("word_type")
            original_section = entry.get("_original_section", None)

            # Use original section if available (for multi-type words)
            if original_section:
                vocab[original_section].append(entry)
            else:
                # Determine section from type
                if isinstance(word_type, list):
                    # Multi-type without original section - shouldn't happen, but handle it
                    primary_type = word_type[0]
                else:
                    primary_type = word_type

                # Map type to section
                if primary_type == "verb":
                    vocab["verbs"].append(entry)
                elif primary_type == "noun":
                    vocab["nouns"].append(entry)
                elif primary_type == "adjective":
                    vocab["adjectives"].append(entry)

        return vocab

    def get_merged_vocabulary(self, base_vocab: Dict) -> Dict:
        """
        Merge base vocabulary with vocabulary from all loaded modules.

        Automatically creates multi-type entries when the same word appears
        with different types from different modules.

        Args:
            base_vocab: Base vocabulary dict from vocabulary.json

        Returns:
            Merged vocabulary dict
        """
        # Build word -> entry map
        word_map = {}

        # Add base vocab
        for section in ["verbs", "nouns", "adjectives"]:
            for entry in base_vocab.get(section, []):
                word = entry["word"]
                entry_copy = entry.copy()
                # Set word_type if not present
                if "word_type" not in entry_copy:
                    entry_copy["word_type"] = self._section_to_type(section)
                # Track original section for placement
                entry_copy["_original_section"] = section
                word_map[word] = entry_copy

        # Merge module vocabularies
        for module in self._modules.values():
            if not hasattr(module, 'vocabulary') or not module.vocabulary:
                continue
            ext = module.vocabulary
            if not isinstance(ext, dict):
                continue

            for section in ["verbs", "nouns", "adjectives"]:
                for entry in ext.get(section, []):
                    word = entry["word"]
                    entry_copy = entry.copy()

                    # Set word_type if not present
                    if "word_type" not in entry_copy:
                        entry_copy["word_type"] = self._section_to_type(section)

                    if word in word_map:
                        # Merge types
                        existing_entry = word_map[word]
                        existing_type = existing_entry.get("word_type")
                        new_type = entry_copy.get("word_type")

                        # Only merge if types are different
                        if existing_type != new_type:
                            merged_type = self._merge_types(existing_type, new_type)
                            existing_entry["word_type"] = merged_type

                        # Merge synonyms
                        existing_syns = set(existing_entry.get("synonyms", []))
                        new_syns = set(entry_copy.get("synonyms", []))
                        existing_entry["synonyms"] = list(existing_syns | new_syns)

                        # Copy other properties from new entry if not present
                        for key, value in entry_copy.items():
                            if key not in existing_entry and key not in ["word", "word_type", "synonyms", "_original_section"]:
                                existing_entry[key] = value
                    else:
                        # Track original section for placement
                        entry_copy["_original_section"] = section
                        word_map[word] = entry_copy

        # Rebuild vocabulary sections
        result = self._rebuild_vocab_from_map(word_map)

        # Clean up internal tracking fields
        for section in ["verbs", "nouns", "adjectives"]:
            for entry in result[section]:
                if "_original_section" in entry:
                    del entry["_original_section"]

        # Add prepositions and articles (no merging needed)
        result["prepositions"] = list(base_vocab.get("prepositions", []))
        result["articles"] = list(base_vocab.get("articles", []))

        return result

    def get_handler(self, verb: str) -> Optional[Callable]:
        """
        Get registered handler for a verb.

        Returns highest precedence handler (Tier 1 = lowest tier number).

        Args:
            verb: The verb to handle

        Returns:
            Handler function or None
        """
        handlers = self._handlers.get(verb)
        if not handlers or len(handlers) == 0:
            return None

        # Return handler from first tuple: (tier, handler, module)
        return handlers[0][1]  # Second element is the handler

    def get_events_for_verb(self, verb: str) -> Optional[List[tuple]]:
        """
        Get list of (tier, event_name) tuples for a verb or synonym.

        Returns events sorted by tier (lowest/highest precedence first).

        Args:
            verb: The verb or synonym to look up

        Returns:
            List of (tier, event_name) tuples, or None if not registered
        """
        events = self._verb_event_map.get(verb)
        if not events:
            return None
        # Return copy to prevent external modification
        return list(events)

    def get_event_for_verb(self, verb: str) -> Optional[str]:
        """
        Get event name for a verb or synonym (backward compatibility).

        Returns the highest precedence (lowest tier) event.

        Args:
            verb: The verb or synonym to look up

        Returns:
            Event name (e.g., "on_take") or None if not registered
        """
        events = self.get_events_for_verb(verb)
        if not events:
            return None
        # Return first event (highest precedence)
        return events[0][1]  # Return event name from (tier, event_name) tuple

    def has_handler(self, verb: str) -> bool:
        """Check if a handler is registered for this verb."""
        return verb in self._handlers

    # Event registry query methods

    def get_registered_events(self) -> List[str]:
        """Return list of all registered event names."""
        return list(self._event_registry.keys())

    def get_event_info(self, event_name: str) -> Optional[EventInfo]:
        """Get metadata for a registered event."""
        return self._event_registry.get(event_name)

    def has_event(self, event_name: EventName) -> bool:
        """Check if an event is registered."""
        return event_name in self._event_registry

    def get_event_for_hook(self, hook_name: HookName) -> Optional[EventName]:
        """Get event name for an engine hook. Returns None if hook not registered."""
        entry = self._hook_to_event.get(hook_name)
        return EventName(entry[0]) if entry else None

    def get_fallback_event(self, event_name: EventName) -> Optional[EventName]:
        """Get fallback event for an event. Returns None if no fallback."""
        fallback = self._fallback_events.get(event_name)
        return EventName(fallback) if fallback else None

    def get_hooks(self) -> List[HookName]:
        """Return list of all registered hook names."""
        return [HookName(k) for k in self._hook_to_event.keys()]

    def validate_on_prefix_usage(self) -> None:
        """
        Ensure all on_* functions correspond to registered events.

        Validates that behavior modules don't define on_* functions without
        registering the corresponding event. This catches:
        - Typos: on_tke instead of on_take
        - Misunderstanding: Using on_ for non-event helpers
        - Missing event registration: Forgot to add event to vocabulary

        Raises:
            ValueError: If any on_* function is not a registered event.
                       Fail fast - this is a load-time error.
        """
        registered = set(self.get_registered_events())

        for module_name, module in self._modules.items():
            for name in dir(module):
                if name.startswith("on_") and callable(getattr(module, name)):
                    if name not in registered:
                        raise ValueError(
                            f"Module '{module_name}' defines '{name}' but this event "
                            f"is not registered. Either register the event in vocabulary "
                            f"or rename the function to not use 'on_' prefix."
                        )

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
        event_name: EventName,
        accessor: Any,
        context: Dict[str, Any]
    ) -> Optional[EventResult]:
        """
        Invoke entity behaviors for an event, with fallback support.

        Invokes all behaviors attached to the entity that define the event handler.
        Multiple behaviors are combined with AND logic (all must allow) and
        messages are concatenated.

        If no behavior responds to event_name and a fallback is registered,
        tries the fallback event (recursively, supporting fallback chains).

        Args:
            entity: Entity object with 'behaviors' field (list or dict)
            event_name: Event name (e.g., "on_take")
            accessor: StateAccessor instance
            context: Event context dict with actor_id, changes, verb

        Returns:
            EventResult with combined allow/message, or None if no behaviors
        """
        # Try primary event
        result = self._invoke_behavior_internal(entity, event_name, accessor, context)

        # If no result and fallback exists, try fallback (recursive for chains)
        if result is None:
            fallback = self.get_fallback_event(event_name)
            if fallback:
                result = self.invoke_behavior(entity, fallback, accessor, context)

        return result

    def _invoke_behavior_internal(
        self,
        entity: Any,
        event_name: EventName,
        accessor: Any,
        context: Dict[str, Any]
    ) -> Optional[EventResult]:
        """
        Internal implementation of behavior invocation (no fallback handling).

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
        Invoke protocol handlers in tier order until one succeeds.

        Tries handlers in tier order (Tier 1 first, highest precedence).
        Stops at first successful handler (result.success == True).

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

        # Try handlers in tier order
        result = None
        last_message_result = None  # Track last result with a non-empty message
        for tier, handler, module in handlers:
            result = handler(accessor, action)
            if result and result.success:
                return result  # Success, stop trying deeper tiers
            # Track last failure with a message for better error reporting
            if result and not result.success and result.message:
                last_message_result = result
            # Continue to next tier on failure

        # All tiers failed - return last result with message, or last result if all empty
        return last_message_result if last_message_result else result

    def clear_cache(self):
        """Clear behavior cache (useful for hot reload)."""
        self._behavior_cache.clear()


# Global instance
_behavior_manager = BehaviorManager()


def get_behavior_manager() -> BehaviorManager:
    """Get the global behavior manager instance."""
    return _behavior_manager
