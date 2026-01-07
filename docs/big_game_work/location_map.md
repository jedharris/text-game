# Big Game Location Map

## Summary

- **Total locations**: 45
- **Total exits**: 95
- **Reachable from nexus_chamber**: 45 ✅
- **DISCONNECTED**: 0 ✅

**Status**: All locations fully connected as of 2026-01-03

## Connectivity Fixes Applied

### 1. deep_archive ↔ merchant_warehouse (sunken_district)
- **Fixed**: 2026-01-03
- **Solution**: Added `merchant_warehouse → down → deep_archive` and `deep_archive → up → merchant_warehouse`
- **Rationale**: Connects archive to merchant quarter network via warehouse basement

### 2. healers_garden ↔ healers_sanctuary (civilized_remnants)
- **Fixed**: 2026-01-03
- **Solution**: Connected existing stub exits `healers_sanctuary → back → healers_garden` and `healers_garden → front → healers_sanctuary`
- **Rationale**: Garden is behind sanctuary building

### 3. undercity/undercity_entrance ↔ market_square (civilized_remnants)
- **Fixed**: 2026-01-03
- **Solution**: Added `market_square → down → undercity_entrance` and `undercity_entrance → up → market_square`
- **Rationale**: Connects underground district to surface via market square stairway

## Region Overview

### Meridian Nexus (4 locations)
**Hub region connecting all other regions**

```
nexus_chamber
├── north → frozen_pass (Frozen Reaches)
├── south → forest_edge (Beast Wilds)
├── east → flooded_plaza (Sunken District)
├── west → cavern_entrance (Fungal Depths)
├── up → observatory_platform
│
observatory_platform
├── down → nexus_chamber
├── east → keepers_quarters
│
keepers_quarters
├── west → observatory_platform
├── down → crystal_garden
│
crystal_garden
├── up → keepers_quarters
├── west → nexus_chamber
```

### Frozen Reaches (10 locations)
**Northern ice region, fully connected**

```
frozen_pass (entry from nexus)
├── north → temple_sanctum
├── east → ice_caves
├── west → ice_field
├── northwest → glacier_approach
│
temple_sanctum
├── south → frozen_pass
├── north → glacier_approach
├── up → frozen_observatory
│
frozen_observatory
├── down → temple_sanctum
├── north → glacier_surface
│
glacier_approach
├── south → temple_sanctum
├── north → glacier_surface
├── southeast → frozen_pass
│
glacier_surface
├── south → glacier_approach
│
ice_field
├── east → frozen_pass
├── north → hot_springs
├── south → ice_caves
│
hot_springs
├── south → ice_field
│
ice_caves
├── west → frozen_pass
├── north → ice_field
│
snow_forest
├── west → ice_field
├── north → wolf_den
│
wolf_den
├── south → snow_forest
```

### Fungal Depths (5 locations)
**Western underground region, fully connected**

```
cavern_entrance (entry from nexus)
├── east → nexus_chamber
├── down → luminous_grotto
│
luminous_grotto
├── up → cavern_entrance
├── down → spore_heart
├── east → myconid_sanctuary
│
myconid_sanctuary
├── west → luminous_grotto
│
spore_heart
├── up → luminous_grotto
├── down → deep_root_caverns
│
deep_root_caverns
├── up → spore_heart
```

### Beast Wilds (10 locations)
**Southern forest region, fully connected**

```
forest_edge (entry from nexus)
├── north → nexus_chamber
├── south → tangled_path
├── east → southern_trail
│
tangled_path (central hub)
├── north → forest_edge
├── south → predators_den
├── east → wolf_clearing
├── west → spider_thicket
├── southwest → ancient_grove
│
ancient_grove
├── northeast → tangled_path
├── east → bee_queen_clearing
│
bee_queen_clearing
├── west → ancient_grove
│
spider_thicket
├── east → tangled_path
├── west → spider_matriarch_lair
│
spider_matriarch_lair
├── east → spider_thicket
│
wolf_clearing
├── west → tangled_path
│
predators_den
├── north → tangled_path
├── south → southern_trail
│
southern_trail
├── west → forest_edge
├── north → predators_den
├── east → hunters_camp
├── south → town_gate (to Civilized Remnants)
│
hunters_camp
├── west → southern_trail
```

### Sunken District (8 locations)
**Eastern flooded region, mostly connected**

```
flooded_plaza (entry from nexus)
├── west → nexus_chamber
├── east → flooded_chambers
├── south → merchant_quarter
├── northwest → survivor_camp
│
survivor_camp
├── southeast → flooded_plaza
│
flooded_chambers
├── west → flooded_plaza
├── east → tidal_passage
│
tidal_passage
├── west → flooded_chambers
├── east → sea_caves
│
sea_caves
├── west → tidal_passage
│
merchant_quarter
├── north → flooded_plaza
├── south → merchant_warehouse
│
merchant_warehouse
├── north → merchant_quarter
├── down → deep_archive
│
deep_archive
├── up → merchant_warehouse
```

### Civilized Remnants (8 locations)
**Southern town region, fully connected**
```
town_gate (entry from Beast Wilds)
├── north → southern_trail (Beast Wilds)
├── south → market_square
│
market_square (central hub)
├── north → town_gate
├── east → healers_sanctuary
├── west → council_hall
├── south → broken_statue_hall
├── down → undercity_entrance
│
healers_sanctuary
├── west → market_square
├── back → healers_garden
│
healers_garden
├── front → healers_sanctuary
│
council_hall
├── east → market_square
│
broken_statue_hall
├── north → market_square
│
undercity_entrance
├── up → market_square
├── down → undercity
│
undercity
├── up → undercity_entrance
```

## Navigation Paths Between Regions

### From Nexus to Each Region

**To Frozen Reaches:**
- nexus_chamber → north → frozen_pass

**To Fungal Depths:**
- nexus_chamber → west → cavern_entrance

**To Beast Wilds:**
- nexus_chamber → south → forest_edge

**To Sunken District:**
- nexus_chamber → east → flooded_plaza

**To Civilized Remnants:**
- nexus_chamber → south → forest_edge → east → southern_trail → south → town_gate

## Files

- **Audit tool**: `tools/location_audit.py`
- **Game state**: `examples/big_game/game_state.json`
- **Exits section**: Line ~6330 in game_state.json
