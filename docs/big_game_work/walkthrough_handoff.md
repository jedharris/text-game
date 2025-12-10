# Walkthrough Handoff - The Shattered Meridian

## Current State

All six regions have completed walkthroughs with updated sketches:

| Region | Status | Sketch File |
|--------|--------|-------------|
| Fungal Depths | ✅ Complete | `fungal_depths_sketch.json` (v0.2) |
| Beast Wilds | ✅ Complete | `beast_wilds_sketch.json` (v0.2) |
| Sunken District | ✅ Complete | `sunken_district_sketch.json` (v0.2) |
| Frozen Reaches | ✅ Complete | `frozen_reaches_sketch.json` (v0.2) |
| Civilized Remnants | ✅ Complete | `civilized_remnants_sketch.json` (v0.2) |
| Meridian Nexus | ✅ Complete | `meridian_nexus_sketch.json` (v0.2) |

## Next Phase: Cross-Region Walkthroughs

With all individual regions complete, the next phase is cross-region testing:

### 1. Full Game Playthrough
- Start in Nexus, visit all regions, complete waystone repair
- Test item flow between regions
- Verify cross-region NPC connections work narratively

### 2. Companion Restriction Testing
- Test salamander companion in cold regions (Frozen Reaches)
- Test fungal companion in populated areas (Civilized Remnants)
- Verify companion-gated content is accessible via alternative paths

### 3. Environmental Spread Effects
- Spore infection spreading through items/companions
- Cold effects when leaving Frozen Reaches
- Water effects when leaving Sunken District

### 4. Reputation Spread Mechanics
- How do actions in one region affect reputation in others?
- Echo as reputation carrier between regions
- NPC gossip networks (Elara-Sira, Delvan-undercity)

### 5. Commitment Cascade Testing
- Abandoned commitments in one region affecting NPC attitudes in others
- Echo confrontations based on cross-region behavior
- "Discovery" mechanics (Elara learning about Sira)

## Key Files Reference

| File | Purpose |
|------|---------|
| `walkthrough_guide.md` | Methodology and established patterns |
| `cross_region_dependencies.md` | Item/NPC/skill flows between regions |
| `*_sketch.json` | Region design documents (all v0.2) |
| `*_walkthrough.md` | Completed walkthrough narratives |

## Design Decisions to Preserve

These were explicitly discussed and should not be contradicted:

### Core Mechanics
1. **Archivist cannot leave archive** - spectral binding, would retrieve fragments herself otherwise
2. **Aldric too sick to walk** - infection justifies his inability to help himself
3. **3 of 5 fragments pattern** - more pieces than needed, some require relationships
4. **Hope extends survival is situational** - drowning doesn't care, but despair-based deaths can be delayed
5. **Withdrawal is valuable** - returning to apologize yields hints, no penalty
6. **Environmental hazards ≠ combat** - no XP/loot, avoidance is intended solution

### Frozen Reaches
7. **Salamanders are fine without player** - Frozen Reaches has no time pressure, methodical exploration rewarded
8. **Golem password is three parts** - "Fire-that-gives-life and water-that-cleanses, united in purpose"
9. **Control crystal gives best outcome** - hidden, rewards thorough exploration, golems serve vs merely permit
10. **Hot springs as sanctuary** - instant hypothermia cure, safe planning area, defines region pacing
11. **Telescope reveals NPC states** - general hints ("movement in caves"), not precise locations
12. **Combat is hard mode, not forbidden** - golems CAN be fought (~36 rounds), but puzzle solutions clearly preferable

### Civilized Remnants
13. **Two-tier herbalism** - Maren teaches basic (trust 2), Elara teaches advanced (trust 3)
14. **Garden skill gating** - nightshade requires advanced herbalism, narrative justification via contact poison
15. **Council dilemmas evolve through dialog** - compromise solutions discoverable, not obvious initially
16. **Probabilistic quest outcomes** - some decisions (trader admission) have uncertain results (80/20)
17. **Undercity discovery risk** - 5% per service, repeated discovery leads to exile
18. **Guardian repair is multi-stage** - crystal placement, chisel repairs, purpose designation
19. **Repaired guardian is imperfect** - one-armed, marked by history, still effective
20. **Cross-region NPC connections** - Elara-Sira, Delvan-undercity create relationship web
21. **Town seal requires hero status OR special service** - multiple paths to same goal
22. **Assassination is darkest option** - 20% discovery, massive consequences even if undiscovered (Echo knows)

### Meridian Nexus
23. **Nexus is absolutely safe** - no combat, no environmental hazards, no time pressure, ever
24. **Echo trust ranges -5 to +10** - affects appearance frequency, guidance quality, final ceremony
25. **Echo appearances are probabilistic** - base 20% + 10% per trust level, capped at 80%
26. **Confession vs discovery** - confessing broken commitments costs -2 trust; being discovered costs -3 trust + permanent consequences
27. **Crystal buffs are cumulative** - each restored crystal adds +1 to relevant stat in that region
28. **Waystone repair is ceremony** - each fragment placement has narrative weight, player chooses order
29. **Echo transforms on completion** - spectral to corporeal, gains ability to leave Nexus
30. **Recovery from negative trust is slow** - max +1 per visit, requires genuine good behavior

## Walkthrough Completion Summary

| Walkthrough | Design Inputs | Open Questions | Key Discoveries |
|-------------|---------------|----------------|-----------------|
| Fungal Depths | DI-FD-1 to DI-FD-8 | All resolved | Commitment system, spore mechanics |
| Beast Wilds | DI-BW-1 to DI-BW-12 | All resolved | Alpha trust, territorial behavior |
| Sunken District | DI-SD-1 to DI-SD-10 | All resolved | Water breathing, Archivist binding |
| Frozen Reaches | DI-FROZEN-1 to DI-FROZEN-15 | All resolved | Hot springs sanctuary, golem puzzle/combat |
| Civilized Remnants | DI-CR-1 to DI-CR-18 | All resolved | Social hazards, two-tier skills, council dilemmas |
| Meridian Nexus | DI-NX-1 to DI-NX-12 | All resolved | Echo trust, crystal buffs, waystone ceremony |
