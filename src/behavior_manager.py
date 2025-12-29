"""Behavior management system for entity events."""

from typing import Optional, Dict, Any, List, Callable, TYPE_CHECKING, Tuple, Protocol, Literal
from dataclasses import dataclass, field
import importlib
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Import EventResult from state_accessor to avoid duplication
from src.state_accessor import EventResult, HandlerResult, NO_HANDLER, IGNORE_EVENT
from src.types import EventName, HookName, TurnHookId, EntityHookId, HookId
from src.action_types import ActionDict, HandlerCallable

if TYPE_CHECKING:
    from src.state_accessor import StateAccessor
    from src.state_manager import Entity, GameState


class EventCallable(Protocol):
    """Signature for entity behavior callbacks."""

    def __call__(self, entity: "Entity", accessor: "StateAccessor", context: Dict[str, Any]) -> EventResult:
        ...


@dataclass
class EventInfo:
    """Metadata about a registered event type."""
    event_name: str                              # e.g., "on_damage"
    registered_by: List[str] = field(default_factory=list)  # Module names that register this event
    description: Optional[str] = None            # Optional documentation
    hook: Optional[str] = None                   # Engine hook name (string - lookup in _hook_definitions for typed ID)


@dataclass
class HookDefinition:
    """Definition of a hook from a behavior module vocabulary (Phase 7: bidirectional dependencies)."""
    hook_id: HookId                              # Hook identifier (typed)
    invocation: Literal["turn_phase", "entity"]  # Invocation type
    after: List[TurnHookId]                      # Runs after these hooks (turn phases only, typed)
    before: List[TurnHookId]                     # Runs before these hooks (turn phases only, typed)
    description: str                             # Human-readable description
    defined_by: str                              # Module that defined it (for error messages)


class BehaviorManager:
    """
    Manages loading and invoking entity behaviors.

    Also handles vocabulary extensions and protocol handler registration.
    """

    def __init__(self) -> None:
        self._behavior_cache: Dict[str, EventCallable] = {}
        # Handler storage: verb -> list of (tier, handler, module_name) tuples (sorted by tier)
        self._handlers: Dict[str, List[Tuple[int, HandlerCallable, str]]] = {}
        # Track verb-to-event mappings with tiers: verb -> list of (tier, event_name) tuples
        self._verb_event_map: Dict[str, List[Tuple[int, str]]] = {}  # verb/synonym -> [(tier, event_name)]
        # Track which module registered which verb+tier (for error messages)
        self._verb_tier_sources: Dict[Tuple[str, int], str] = {}  # (verb, tier) -> module_name
        # Store loaded modules for entity behavior invocation
        self._modules: Dict[str, Any] = {}  # module_name -> module object
        # Event registry: event_name -> EventInfo
        self._event_registry: Dict[str, EventInfo] = {}
        # Hook to event mapping: hook_name -> (event_name, tier)
        self._hook_to_event: Dict[str, Tuple[str, int]] = {}
        # Event fallbacks: event_name -> fallback_event_name
        self._fallback_events: Dict[str, str] = {}
        # Hook definitions: hook_name -> HookDefinition (Phase 1: Hook System Redesign)
        self._hook_definitions: Dict[str, HookDefinition] = {}

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
        # ValueError here indicates misconfigured behavior paths (authoring error)
        relative_path = behavior_path.relative_to(base_path)

        # Calculate depth: number of directory levels (excluding the file itself)
        # e.g., "consumables.py" -> 0 levels (Tier 1)
        #       "library/examine.py" -> 1 level (Tier 2)
        #       "library/core/basic.py" -> 2 levels (Tier 3)
        depth = len(relative_path.parts) - 1  # -1 to exclude filename

        # Tier = depth + 1 (so Tier 1 is highest precedence)
        return depth + 1

    def _register_hook_definition(self, hook_def: Dict[str, Any], module_path: str) -> None:
        """
        Register a hook definition from a vocabulary (Phase 2.5: with type conversion).

        Args:
            hook_def: Hook definition dict from vocabulary (contains plain strings)
            module_path: Path of module defining this hook (for error messages)

        Raises:
            ValueError: If hook already defined by different module, or prefix doesn't match invocation type
        """
        hook_name_str = hook_def['hook_id']  # Plain string from vocabulary JSON
        invocation = hook_def['invocation']

        # Parse-time validation: Check prefix matches invocation type
        if invocation == "turn_phase":
            if not hook_name_str.startswith("turn_"):
                raise ValueError(
                    f"Hook '{hook_name_str}' has invocation='turn_phase' but doesn't start with 'turn_'\n"
                    f"  Defined in: {module_path}"
                )
            hook_id: HookId = TurnHookId(hook_name_str)
        elif invocation == "entity":
            if not hook_name_str.startswith("entity_"):
                raise ValueError(
                    f"Hook '{hook_name_str}' has invocation='entity' but doesn't start with 'entity_'\n"
                    f"  Defined in: {module_path}"
                )
            hook_id = EntityHookId(hook_name_str)
        else:
            raise ValueError(
                f"Hook '{hook_name_str}' has invalid invocation type '{invocation}'\n"
                f"  Must be 'turn_phase' or 'entity'\n"
                f"  Defined in: {module_path}"
            )

        # Check for duplicates
        if hook_name_str in self._hook_definitions:
            existing = self._hook_definitions[hook_name_str]
            if existing.defined_by != module_path:
                raise ValueError(
                    f"Hook '{hook_name_str}' defined multiple times:\n"
                    f"  1. {existing.defined_by}\n"
                    f"  2. {module_path}"
                )
            # Same module re-defining - idempotent, just return
            return

        # Convert dependency strings to TurnHookIds
        after_list = hook_def.get('after', [])
        after_typed: List[TurnHookId] = [TurnHookId(dep) for dep in after_list]

        before_list = hook_def.get('before', [])
        before_typed: List[TurnHookId] = [TurnHookId(dep) for dep in before_list]

        # Store hook definition with typed IDs
        self._hook_definitions[hook_name_str] = HookDefinition(
            hook_id=hook_id,
            invocation=invocation,
            after=after_typed,
            before=before_typed,
            description=hook_def.get('description', ''),
            defined_by=module_path
        )

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

        # Register hook definitions (Phase 1: Hook System Redesign)
        for hook_def in vocabulary.get("hook_definitions", []):
            self._register_hook_definition(hook_def, module_name)

    def _register_event(
        self,
        event_name: str,
        module_name: str,
        tier: int,
        description: Optional[str] = None,
        hook: Optional[str] = None  # Accepts string from vocabulary JSON
    ) -> None:
        """
        Register an event in the event registry.

        Note: Hook strings from vocabularies are stored temporarily and will be
        converted to typed HookIds during validation (Phase 2.5).

        Args:
            event_name: The event name (e.g., "on_take")
            module_name: Module name registering this event
            tier: Tier number (1 = highest precedence)
            description: Optional documentation for the event
            hook: Optional engine hook name (plain string, converted to typed ID later)

        Raises:
            ValueError: If hook conflict detected at same tier
        """
        if event_name not in self._event_registry:
            self._event_registry[event_name] = EventInfo(
                event_name=event_name,
                registered_by=[module_name],
                description=description,
                hook=hook  # Store as string, typed ID available via _hook_definitions lookup
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

    def _register_handler(self, verb: str, handler: HandlerCallable, module_name: str, tier: int) -> None:
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

    def load_module(self, module_or_path: Any, tier: int = 1) -> None:
        """
        Load a behavior module and register its vocabulary and handlers.

        Args:
            module_or_path: Either an already-imported module object or a module path string
            tier: Tier number (1 = highest precedence, based on directory depth)

        Raises:
            ValueError: If conflicts detected (duplicate handlers/vocabulary within same tier)
        """
        if isinstance(module_or_path, str):
            # ImportError here indicates missing behavior module (authoring error)
            module = importlib.import_module(module_or_path)
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

    def load_modules(self, module_info: List[Tuple[str, int]]) -> None:
        """Load multiple behavior modules.

        Args:
            module_info: List of (module_path, tier) tuples from discover_modules()
        """
        for module_path, tier in module_info:
            self.load_module(module_path, tier=tier)

    def get_loaded_modules(self) -> set[str]:
        """Return set of loaded module names for validation."""
        return set(self._modules.keys())

    def _merge_types(self, type1: Any, type2: Any) -> List[str]:
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

    def get_handler(self, verb: str) -> Optional[HandlerCallable]:
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

    def get_events_for_verb(self, verb: str) -> Optional[List[Tuple[int, str]]]:
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

    def load_behavior(self, behavior_path: str) -> Optional[EventCallable]:
        """
        Load a behavior function from module path.

        Args:
            behavior_path: "module.path:function_name"

        Returns:
            Callable behavior function or None
        """
        if behavior_path in self._behavior_cache:
            return self._behavior_cache[behavior_path]

        # Split behavior path - must be in format "module.path:function_name"
        # Invalid format indicates configuration error and should fail loudly
        module_path, function_name = behavior_path.split(':')

        # ImportError here indicates missing behavior module (authoring error)
        module = importlib.import_module(module_path)
        behavior_func: EventCallable = getattr(module, function_name)
        self._behavior_cache[behavior_path] = behavior_func
        return behavior_func

    def invoke_behavior(
        self,
        entity: Optional["Entity"],
        event_name: EventName,
        accessor: "StateAccessor",
        context: Dict[str, Any]
    ) -> EventResult:
        """
        Invoke entity behaviors for an event, with fallback support.

        Invokes all behaviors attached to the entity that define the event handler.
        Multiple behaviors are combined with AND logic (all must allow) and
        messages are concatenated.

        If no behavior responds to event_name and a fallback is registered,
        tries the fallback event (recursively, supporting fallback chains).

        For global events (entity=None), invokes all modules that register the event.

        Args:
            entity: Entity object with 'behaviors' field, or None for global events
            event_name: Event name (e.g., "on_take", "on_npc_action")
            accessor: StateAccessor instance
            context: Event context dict with actor_id, changes, verb

        Returns:
            EventResult with combined allow/message, or NO_HANDLER if no behaviors

        Raises:
            ValueError: If entity-specific event has no handler (fail-fast for authoring errors)
        """
        # For global events (turn phases, etc.), invoke all modules that register this event
        if entity is None:
            event_info = self._event_registry.get(event_name)
            if not event_info or not event_info.registered_by:
                return NO_HANDLER

            results = []
            for module_name in event_info.registered_by:
                module = self._modules.get(module_name)
                if module and hasattr(module, event_name):
                    handler = getattr(module, event_name)
                    event_result = handler(None, accessor, context)
                    if isinstance(event_result, EventResult):
                        results.append(event_result)

            if not results:
                return NO_HANDLER

            # Combine results
            combined_allow = all(r.allow for r in results)
            combined_feedback = "; ".join(r.feedback for r in results if r.feedback)
            return EventResult(allow=combined_allow, feedback=combined_feedback if combined_feedback else None)

        # Try primary event
        result: EventResult = self._invoke_behavior_internal(entity, event_name, accessor, context)

        # If no handler and fallback exists, try fallback (recursive for chains)
        if result._no_handler:
            fallback = self.get_fallback_event(event_name)
            if fallback:
                result = self.invoke_behavior(entity, fallback, accessor, context)

        # All events are optional - no fail-fast
        # If entity has no handler (even after fallback chain), silently ignore
        if result._no_handler and entity is not None:
            entity_id = getattr(entity, 'id', '<unknown>')
            entity_behaviors = getattr(entity, 'behaviors', [])
            # Log for debugging (can be enabled via logging config)
            logger.debug(
                f"Event '{event_name}' triggered on entity '{entity_id}' "
                f"but no handler found. Entity behaviors: {entity_behaviors}. "
                f"Silently ignoring."
            )
            return IGNORE_EVENT

        return result

    def _invoke_behavior_internal(
        self,
        entity: "Entity",
        event_name: EventName,
        accessor: "StateAccessor",
        context: Dict[str, Any]
    ) -> EventResult:
        """
        Internal implementation of behavior invocation (no fallback handling).

        Args:
            entity: Entity object with 'behaviors' field (list of modules)
            event_name: Event name (e.g., "on_take")
            accessor: StateAccessor instance
            context: Event context dict with actor_id, changes, verb

        Returns:
            EventResult with combined allow/message, or NO_HANDLER sentinel if no behaviors
        """
        if entity is None or not hasattr(entity, 'behaviors') or not entity.behaviors:
            return NO_HANDLER

        if not isinstance(entity.behaviors, list):
            return NO_HANDLER

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

            # Call handler with entity, accessor, context
            # Errors here indicate bugs in behavior code and should fail loudly during development
            event_result = handler(entity, accessor, context)

            if isinstance(event_result, EventResult):
                results.append(event_result)

        # If no behaviors were invoked, return NO_HANDLER sentinel
        if not results:
            return NO_HANDLER

        # Filter out ignored events - they don't participate in combination logic
        # but we collect their feedback for propagation
        non_ignored_results = [r for r in results if not r._ignored]
        ignored_feedback = [r.feedback for r in results if r._ignored and r.feedback]

        # If all handlers ignored the event, return IGNORE_EVENT with combined feedback
        if not non_ignored_results:
            combined_feedback = "\n".join(ignored_feedback) if ignored_feedback else None
            return EventResult(allow=True, feedback=combined_feedback, _ignored=True)

        # Combine non-ignored results: AND logic for allow, concatenate feedback
        combined_allow = all(r.allow for r in non_ignored_results)
        # Include feedback from both non-ignored and ignored results
        all_feedback = [r.feedback for r in non_ignored_results if r.feedback] + ignored_feedback
        combined_message = "\n".join(all_feedback) if all_feedback else None

        return EventResult(allow=combined_allow, feedback=combined_message)

    def invoke_handler(self, verb: str, accessor: "StateAccessor", action: ActionDict) -> Optional[HandlerResult]:
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
        last_message_result = None  # Track last result with a non-empty primary text
        for tier, handler, module in handlers:
            result = handler(accessor, action)
            if result and result.success:
                return result  # Success, stop trying deeper tiers
            # Track last failure with a message for better error reporting
            if result and not result.success and result.primary:
                last_message_result = result
            # Continue to next tier on failure

        # All tiers failed - return last result with message, or last result if all empty
        return last_message_result if last_message_result else result

    # ========== Phase 2: Hook System Validation Methods ==========

    def validate_hook_prefixes(self) -> None:
        """
        Validate all hooks use correct prefixes (turn_* or entity_*).

        Raises:
            ValueError: If hook doesn't use required prefix
        """
        for hook_name, hook_def in self._hook_definitions.items():
            if hook_def.invocation == "turn_phase":
                if not hook_name.startswith("turn_"):
                    raise ValueError(
                        f"Turn phase hook '{hook_name}' must start with 'turn_' prefix\n"
                        f"  Defined in: {hook_def.defined_by}"
                    )
            elif hook_def.invocation == "entity":
                if not hook_name.startswith("entity_"):
                    raise ValueError(
                        f"Entity hook '{hook_name}' must start with 'entity_' prefix\n"
                        f"  Defined in: {hook_def.defined_by}"
                    )
            else:
                raise ValueError(
                    f"Hook '{hook_name}' has invalid invocation type '{hook_def.invocation}'\n"
                    f"  Must be 'turn_phase' or 'entity'\n"
                    f"  Defined in: {hook_def.defined_by}"
                )

    def validate_turn_phase_dependencies(self) -> None:
        """
        Validate turn phase 'after' dependencies reference defined hooks.

        Raises:
            ValueError: If dependency references undefined hook
        """
        for hook_name, hook_def in self._hook_definitions.items():
            if hook_def.invocation != "turn_phase":
                continue

            for dep in hook_def.after:
                if dep not in self._hook_definitions:
                    raise ValueError(
                        f"Turn phase '{hook_name}' depends on undefined hook '{dep}'\n"
                        f"  Defined in: {hook_def.defined_by}"
                    )

                # Dependency must also be a turn phase
                dep_def = self._hook_definitions[dep]
                if dep_def.invocation != "turn_phase":
                    raise ValueError(
                        f"Turn phase '{hook_name}' depends on '{dep}' which is not a turn phase\n"
                        f"  '{dep}' is invocation type: {dep_def.invocation}\n"
                        f"  Defined in: {hook_def.defined_by}"
                    )

    def validate_hooks_are_defined(self) -> None:
        """
        Validate all event hook references point to defined hooks.

        Raises:
            ValueError: If event references undefined hook
        """
        for event_name, event_info in self._event_registry.items():
            hook_name = event_info.hook

            if hook_name and hook_name not in self._hook_definitions:
                modules_str = ", ".join(event_info.registered_by)
                available_hooks = sorted(self._hook_definitions.keys())
                raise ValueError(
                    f"Event '{event_name}' references undefined hook '{hook_name}'\n"
                    f"  Event defined in: {modules_str}\n"
                    f"  Available hooks: {available_hooks}"
                )

    def validate_turn_phase_not_in_entity_behaviors(self, game_state: "GameState") -> None:
        """
        Validate turn phase behaviors not attached to entities.

        Turn phases should only be in global behaviors, not entity behaviors lists.

        Args:
            game_state: Loaded game state to validate

        Raises:
            ValueError: If turn phase behavior attached to entity
        """
        from src.state_manager import GameState

        # Get all turn phase module paths
        turn_phase_modules = set()
        for hook_def in self._hook_definitions.values():
            if hook_def.invocation == "turn_phase":
                turn_phase_modules.add(hook_def.defined_by)

        # Check all entities
        for actor in game_state.actors.values():
            for behavior in actor.behaviors:
                if behavior in turn_phase_modules:
                    raise ValueError(
                        f"Actor '{actor.id}' has turn phase behavior '{behavior}' in behaviors list\n"
                        f"  Turn phases should not be attached to entities"
                    )

        for item in game_state.items:
            for behavior in item.behaviors:
                if behavior in turn_phase_modules:
                    raise ValueError(
                        f"Item '{item.id}' has turn phase behavior '{behavior}' in behaviors list\n"
                        f"  Turn phases should not be attached to entities"
                    )

        for location in game_state.locations:
            for behavior in location.behaviors:
                if behavior in turn_phase_modules:
                    raise ValueError(
                        f"Location '{location.id}' has turn phase behavior '{behavior}' in behaviors list\n"
                        f"  Turn phases should not be attached to entities"
                    )

    def validate_hook_invocation_consistency(self) -> None:
        """
        Validate each hook used consistently (not as both turn_phase and entity).

        Raises:
            ValueError: If hook defined with conflicting invocation types
        """
        # This is already enforced by duplicate detection in _register_hook_definition
        # But we keep this as explicit validation pass for clarity

        hook_invocations: Dict[str, Tuple[str, str]] = {}  # hook -> (invocation, module)

        for hook_name, hook_def in self._hook_definitions.items():
            if hook_name in hook_invocations:
                prev_inv, prev_mod = hook_invocations[hook_name]
                if prev_inv != hook_def.invocation:
                    raise ValueError(
                        f"Hook '{hook_name}' used with conflicting invocation types:\n"
                        f"  1. {prev_mod}: {prev_inv}\n"
                        f"  2. {hook_def.defined_by}: {hook_def.invocation}"
                    )
            else:
                hook_invocations[hook_name] = (hook_def.invocation, hook_def.defined_by)

    def finalize_loading(self, game_state: "GameState") -> None:
        """
        Call after all vocabularies loaded to run validations.

        Args:
            game_state: Loaded game state (for entity behavior validation)

        Raises:
            ValueError: If any validation fails
        """
        self.validate_hook_prefixes()
        self.validate_turn_phase_dependencies()
        self.validate_hooks_are_defined()
        self.validate_hook_invocation_consistency()
        self.validate_turn_phase_not_in_entity_behaviors(game_state)

    # ========== End Phase 2 Validation Methods ==========

    def clear_cache(self) -> None:
        """Clear behavior cache (useful for hot reload)."""
        self._behavior_cache.clear()


# Global instance
_behavior_manager = BehaviorManager()


def get_behavior_manager() -> BehaviorManager:
    """Get the global behavior manager instance."""
    return _behavior_manager
