"""Telescope Repair for Frozen Reaches.

Handles repairing the frozen telescope with three components:
- crystal_lens (from ice_caves)
- mounting_bracket (from temple_sanctum)
- control_crystal (from ice_caves hidden passage)
"""

from typing import Any, Dict

from src.behavior_manager import EventResult
from src.state_accessor import IGNORE_EVENT

# Vocabulary: wire repair-related verbs
vocabulary: Dict[str, Any] = {
    "events": [
        {
            "event": "on_use",
            "handler": "on_use",
            "description": "Handle using the telescope to observe"
        },
        {
            "event": "on_examine",
            "handler": "on_examine",
            "description": "Handle examining the telescope"
        },
        {
            "event": "on_observe",
            "handler": "on_observe",
            "description": "Handle observe event (uses standard description)"
        }
    ],
    "verbs": [
        {"word": "repair", "synonyms": ["fix", "restore"], "object_required": True},
        {"word": "install", "synonyms": ["attach", "mount"], "object_required": True},
    ]
}

# Required components for telescope repair
REQUIRED_COMPONENTS = {
    "crystal_lens": "lens",
    "mounting_bracket": "mounting",
    "command_crystal": "power_source"
}


def on_use_component_on_telescope(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle installing telescope components.

    Tracks which components have been installed and completes repair
    when all three are present.

    Args:
        entity: The component item being used
        accessor: StateAccessor instance
        context: Context with target

    Returns:
        EventResult with installation result
    """
    # Check if this is a telescope component
    item_id = entity.id if hasattr(entity, "id") else str(entity)

    if item_id not in REQUIRED_COMPONENTS:
        return EventResult(allow=True, feedback=None)

    # Check if target is the frozen telescope
    target = context.get("target")
    if not target:
        return EventResult(allow=True, feedback=None)

    target_id = target.id if hasattr(target, "id") else str(target)
    if target_id != "frozen_telescope":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    telescope = next((item for item in state.items if item.id == "frozen_telescope"), None)
    if not telescope:
        return EventResult(allow=True, feedback=None)

    # Initialize tracking if needed
    if "installed_components" not in telescope.properties:
        telescope.properties["installed_components"] = []

    installed = telescope.properties["installed_components"]
    component_type = REQUIRED_COMPONENTS[item_id]

    # Check if already installed
    if component_type in installed:
        return EventResult(
            allow=False,
            feedback=f"The {entity.name} is already installed in the telescope."
        )

    # Install the component
    installed.append(component_type)

    # Remove the component from player's inventory
    actor_id = context.get("actor_id", "player")
    actor = state.actors.get(actor_id)
    if actor:
        if item_id in actor.inventory:
            actor.inventory.remove(item_id)

    # Build installation message
    messages = {
        "lens": f"You carefully install the {entity.name} into the telescope's housing. The optics gleam with perfect clarity.",
        "mounting": f"You attach the {entity.name} to the telescope, securing the lens assembly. The mechanism clicks into place.",
        "power_source": f"You insert the {entity.name} into the telescope's base. Runes along the brass fittings begin to glow softly."
    }

    feedback = messages.get(component_type, f"You install the {entity.name}.")

    # Check if repair is complete
    if len(installed) >= 3:
        telescope.properties["requires_repair"] = False
        telescope.properties["repaired"] = True

        # Mark synced telescope as enhanced
        ancient_telescope = next((item for item in state.items if item.id == "ancient_telescope"), None)
        if ancient_telescope:
            ancient_telescope.properties["synced_repaired"] = True

        # Set global flag for cold spread prevention
        state.extra["telescope_repaired"] = True

        feedback += (
            "\n\nThe telescope hums to life! All three components are in place. "
            "The twin telescope in the Nexus observatory resonates in sympathy - both "
            "are now fully functional and synced. Through the repaired lens, you can see "
            "the entire fractured world with perfect clarity."
        )

    return EventResult(allow=True, feedback=feedback)


def on_use(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle using the telescope to observe regions.

    Args:
        entity: The telescope
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with observation results
    """
    telescope_id = entity.id if hasattr(entity, "id") else str(entity)

    if telescope_id != "frozen_telescope":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    telescope = next((item for item in state.items if item.id == "frozen_telescope"), None)
    if not telescope:
        return EventResult(allow=True, feedback=None)

    # Check if repaired
    if telescope.properties.get("requires_repair", True):
        return EventResult(
            allow=True,
            feedback=(
                "The telescope is damaged and partially frozen. You can see through it, "
                "but the image is blurry and incomplete. It needs repair.\n\n"
                "Required components: crystal lens, mounting bracket, control crystal."
            )
        )

    # Telescope is repaired - provide detailed view
    feedback = _generate_telescope_view(state)

    return EventResult(allow=True, feedback=feedback)


def on_observe(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle observe event for telescope.

    The telescope doesn't need special observe behavior - it uses
    its standard description.

    Args:
        entity: The telescope
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        IGNORE_EVENT to use standard description
    """
    return IGNORE_EVENT


def on_examine(
    entity: Any,
    accessor: Any,
    context: dict[str, Any],
) -> EventResult:
    """Handle examining the telescope.

    Shows repair status and installed components.

    Args:
        entity: The telescope
        accessor: StateAccessor instance
        context: Context dict

    Returns:
        EventResult with examination details
    """
    telescope_id = entity.id if hasattr(entity, "id") else str(entity)

    if telescope_id != "frozen_telescope":
        return EventResult(allow=True, feedback=None)

    state = accessor.game_state
    telescope = next((item for item in state.items if item.id == "frozen_telescope"), None)
    if not telescope:
        return EventResult(allow=True, feedback=None)

    installed = telescope.properties.get("installed_components", [])
    requires_repair = telescope.properties.get("requires_repair", True)

    if not requires_repair:
        return EventResult(
            allow=True,
            feedback=(
                "The telescope is fully repaired and operational. All three components "
                "are installed: crystal lens, mounting bracket, and control crystal. "
                "Runes glow along its brass fittings, and through the lens you can see "
                "the entire world with perfect clarity."
            )
        )

    # List what's installed and what's needed
    status_parts = []

    if "lens" in installed:
        status_parts.append("✓ Crystal lens installed")
    else:
        status_parts.append("✗ Crystal lens needed (frozen in ice_caves wall - requires heat to extract)")

    if "mounting" in installed:
        status_parts.append("✓ Mounting bracket installed")
    else:
        status_parts.append("✗ Mounting bracket needed (temple_sanctum altar)")

    if "power_source" in installed:
        status_parts.append("✓ Control crystal installed")
    else:
        status_parts.append("✗ Control crystal needed (ice_caves hidden passage)")

    status = "\n".join(status_parts)

    return EventResult(
        allow=True,
        feedback=(
            f"The telescope is partially frozen and damaged. It needs repair.\n\n"
            f"Repair status:\n{status}\n\n"
            f"Use components on the telescope to install them."
        )
    )


def _generate_telescope_view(state: Any) -> str:
    """Generate the view through the repaired telescope.

    Shows NPC states, environmental conditions, and quest progress
    across all regions.

    Args:
        state: Game state

    Returns:
        Description of what's visible through the telescope
    """
    views = []

    views.append(
        "Through the repaired telescope, you see the fractured world with perfect clarity:\n"
    )

    # Fungal Depths
    aldric = state.actors.get("aldric")
    spore_mother = state.actors.get("spore_mother")
    if aldric:
        aldric_state = aldric.properties.get("state_machine", {}).get("current", "unknown")
        if aldric_state == "rescued":
            views.append("• Fungal Depths: Aldric's campfire burns steadily. He's safe.")
        elif aldric_state == "dying":
            views.append("• Fungal Depths: Aldric's campfire flickers weakly. Time is short.")
        else:
            views.append("• Fungal Depths: A dying campfire in the dark.")

    if spore_mother:
        sm_health = spore_mother.properties.get("health", 0)
        if sm_health > 50:
            views.append("  The Spore Mother pulses with vibrant life.")
        elif sm_health > 0:
            views.append("  The Spore Mother is weakened but alive.")

    # Beast Wilds
    sira = state.actors.get("sira")
    if sira:
        sira_state = sira.properties.get("state_machine", {}).get("current", "unknown")
        if sira_state == "rescued":
            views.append("• Beast Wilds: Sira moves among the beast dens, healing.")
        elif sira_state == "injured":
            views.append("• Beast Wilds: Sira lies injured near the overlook.")

    # Waystone progress
    waystone = next((item for item in state.items if item.id == "damaged_waystone"), None)
    if waystone:
        fragments_count = len(waystone.properties.get("installed_fragments", []))
        views.append(f"• Meridian Nexus: The waystone has {fragments_count} of 5 fragments installed.")

    # Cold spread status
    if state.extra.get("cold_spread_active", False):
        views.append("• WARNING: Cold is spreading from the Frozen Reaches!")
    else:
        views.append("• The cold spread has been halted. The world is stabilizing.")

    return "\n".join(views)
