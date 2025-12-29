"""Turn phase execution with dependency-based ordering.

This module handles turn phase hook discovery, dependency resolution via
topological sort, and execution in the correct order.

Key features:
- Bidirectional dependencies: hooks can declare both 'after' and 'before'
- Topological sort using Kahn's algorithm
- Circular dependency detection with clear error messages
- Cached execution order (computed once at load time)
"""

from typing import Dict, List, Set, Tuple
from src.behavior_manager import HookDefinition
from src.state_manager import GameState
from src.types import TurnHookId, EventName, ActorId
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.state_accessor import StateAccessor
    from src.behavior_manager import BehaviorManager

# Global cached turn phase execution order
_ordered_turn_phases: List[str] = []


def initialize(hook_definitions: Dict[str, HookDefinition]) -> None:
    """Sort and cache turn phases once at game load.

    Filters to turn_phase hooks only, builds dependency graph from both
    'after' and 'before' constraints, and performs topological sort.

    Args:
        hook_definitions: All hook definitions from BehaviorManager

    Raises:
        ValueError: If circular dependencies detected
        ValueError: If dependencies reference undefined hooks
    """
    global _ordered_turn_phases

    # Filter to turn phases only
    turn_phases = {
        name: defn for name, defn in hook_definitions.items()
        if defn.invocation == "turn_phase"
    }

    # Topological sort by dependencies
    sorted_phases = _topological_sort(turn_phases)
    _ordered_turn_phases = sorted_phases


def _topological_sort(phases: Dict[str, HookDefinition]) -> List[str]:
    """Sort turn phases by dependencies using Kahn's algorithm.

    Handles both `after` and `before` constraints by building a unified
    dependency graph:
    - A.after=[B] creates edge B→A (A depends on B, so B must run first)
    - A.before=[C] creates edge A→C (C depends on A, so A must run first)

    Args:
        phases: Dict mapping hook name to HookDefinition

    Returns:
        List of hook names in execution order

    Raises:
        ValueError: If circular dependencies detected (authoring error)
        ValueError: If impossible constraints detected (authoring error)
    """
    if not phases:
        return []

    # Build adjacency list and in-degree count
    # graph[A] = [B, C] means A must run before B and C (A→B, A→C edges)
    graph: Dict[str, List[str]] = {name: [] for name in phases}
    in_degree: Dict[str, int] = {name: 0 for name in phases}

    # Process all dependencies
    for name, defn in phases.items():
        # A.after = [B] means B→A edge (A depends on B)
        for dep_id in defn.after:
            dep_name = str(dep_id)  # Convert TurnHookId to string
            if dep_name not in phases:
                raise ValueError(
                    f"Turn phase '{name}' declares dependency 'after: [\"{dep_name}\"]' "
                    f"but '{dep_name}' is not a defined turn phase hook.\n"
                    f"Defined by: {defn.defined_by}"
                )
            # Add edge: dep_name → name (dep_name must run before name)
            graph[dep_name].append(name)
            in_degree[name] += 1

        # A.before = [C] means A→C edge (C depends on A)
        for dep_id in defn.before:
            dep_name = str(dep_id)  # Convert TurnHookId to string
            if dep_name not in phases:
                raise ValueError(
                    f"Turn phase '{name}' declares dependency 'before: [\"{dep_name}\"]' "
                    f"but '{dep_name}' is not a defined turn phase hook.\n"
                    f"Defined by: {defn.defined_by}"
                )
            # Add edge: name → dep_name (name must run before dep_name)
            graph[name].append(dep_name)
            in_degree[dep_name] += 1

    # Kahn's algorithm: start with nodes that have no dependencies
    queue: List[str] = [name for name, degree in in_degree.items() if degree == 0]
    sorted_order: List[str] = []

    while queue:
        # Process node with no remaining dependencies
        # Sort queue for deterministic ordering when multiple nodes have in-degree 0
        queue.sort()
        current = queue.pop(0)
        sorted_order.append(current)

        # Remove edges from current node
        for neighbor in graph[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Check for cycles
    if len(sorted_order) != len(phases):
        # Find nodes involved in cycle
        remaining = [name for name in phases if name not in sorted_order]
        cycle_info = _find_cycle(graph, remaining)

        raise ValueError(
            f"Circular dependency detected in turn phase hooks.\n"
            f"Cycle involves: {', '.join(remaining)}\n"
            f"Example cycle path: {cycle_info}\n\n"
            f"This is an authoring error. Turn phases cannot have circular dependencies.\n"
            f"Check 'after' and 'before' constraints in hook definitions."
        )

    return sorted_order


def _find_cycle(graph: Dict[str, List[str]], nodes: List[str]) -> str:
    """Find and format a cycle path for error messages.

    Args:
        graph: Adjacency list representation
        nodes: Nodes known to be in a cycle

    Returns:
        String representation of cycle path (e.g., "A → B → C → A")
    """
    # Start from first node and follow edges until we return to it
    if not nodes:
        return "(unable to determine cycle path)"

    visited: Set[str] = set()
    path: List[str] = []

    def dfs(node: str) -> bool:
        """DFS to find cycle. Returns True if cycle found."""
        if node in path:
            # Found cycle - build path from cycle start
            cycle_start = path.index(node)
            cycle_path = path[cycle_start:] + [node]
            path.clear()
            path.extend(cycle_path)
            return True

        if node in visited:
            return False

        visited.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            if dfs(neighbor):
                return True

        path.pop()
        return False

    # Try to find cycle starting from each node
    for start_node in nodes:
        visited.clear()
        path.clear()
        if dfs(start_node):
            return " → ".join(path)

    return " → ".join(nodes) + " (cycle)"


def execute_turn_phases(
    state: GameState,
    behavior_manager: "BehaviorManager",
    accessor: "StateAccessor",
    action: Dict
) -> List[str]:
    """Execute all turn phases in dependency order.

    Invokes each turn phase hook via behavior_manager, collecting narration
    messages from each phase.

    Args:
        state: Current game state
        behavior_manager: BehaviorManager for invoking hooks
        accessor: StateAccessor for state queries
        action: The action dict from the command

    Returns:
        List of narration strings from each phase
    """
    messages: List[str] = []

    # Increment turn counter before processing phases
    state.increment_turn()

    # Build context for turn phases
    actor_id: ActorId = action.get("actor_id") or ActorId("player")

    for hook_name in _ordered_turn_phases:
        # Get event for this hook
        from src.types import HookName
        event_name = behavior_manager.get_event_for_hook(HookName(hook_name))
        if not event_name:
            # No event registered for this hook - skip
            continue

        # Build context
        context = {
            "hook": hook_name,
            "actor_id": actor_id,
            "current_turn": state.turn_count,
        }

        # Invoke turn phase behavior (entity=None for turn phases)
        result = behavior_manager.invoke_behavior(
            None, event_name, accessor, context
        )

        if result and result.feedback:
            messages.append(result.feedback)

    return messages
