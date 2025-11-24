# Combat Example

This example demonstrates a multi-step combat handler using the StateAccessor pattern. It shows how to handle multiple attacks with incremental feedback.

```python
def handle_attack(accessor, action):
    """Handle attack command with multiple strikes."""
    target_name = action.get("object")

    # Find target NPC
    location = accessor.get_current_location()
    target = None
    for npc in accessor.get_npcs_in_location(location.id):
        if npc.name.lower() == target_name.lower():
            target = npc
            break

    if not target:
        return (False, f"You don't see {target_name} here.")

    actor = accessor.get_actor()
    messages = []

    weapon_id = actor.properties.get("equipped_weapon")
    weapon = accessor.get_item(weapon_id) if weapon_id else None

    num_hits = weapon.properties.get("hits", 1) if weapon else 1

    for i in range(num_hits):
        damage = calculate_damage(accessor, weapon)

        current_health = target.properties.get("health", 100)
        new_health = current_health - damage

        result = accessor.update(
            entity=target,
            changes={"properties.health": new_health},
            event="on_damage"
        )

        if not result.success:
            messages.append(f"Strike {i+1}: Miss!")
            continue

        messages.append(f"Strike {i+1}: {damage} damage!")

        if new_health <= 0:
            messages.append(f"The {target.name} is defeated!")
            break

    return (True, "\n".join(messages))


def calculate_damage(accessor, weapon):
    """Calculate damage for an attack."""
    base_damage = 5
    if weapon:
        base_damage = weapon.properties.get("damage", 5)

    # Could add randomization, actor stats, etc.
    return base_damage
```

## Notes

- This is an advanced example showing multi-step operations with incremental feedback
- Each strike invokes the `on_damage` behavior on the target, which could implement armor, dodge, or special effects
- The handler accumulates messages to report each strike's result
- Combat systems would typically add randomization, stats, and more complex damage calculation
