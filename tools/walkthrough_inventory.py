#!/usr/bin/env python3
"""
Inventory all walkthrough files and categorize them.
"""

import re
from pathlib import Path
from collections import defaultdict

WALKTHROUGH_DIR = Path("walkthroughs")

def extract_metadata(filepath: Path) -> dict:
    """Extract metadata from walkthrough file."""
    with open(filepath) as f:
        lines = f.readlines()

    # Get first few comment lines for description
    description_lines = []
    for line in lines[:10]:
        if line.startswith("#") and not line.startswith("# EXPECT_FAIL"):
            description_lines.append(line[1:].strip())
        elif line.strip() and not line.startswith("#"):
            break

    description = " ".join(description_lines[:3]) if description_lines else ""

    # Count commands (non-comment, non-empty lines)
    commands = [l for l in lines if l.strip() and not l.startswith("#")]
    command_count = len(commands)

    # Count assertions
    assertion_count = sum(1 for l in lines if "ASSERT" in l)

    # Check for EXPECT_FAIL markers
    has_expected_failures = any("EXPECT_FAIL" in l for l in lines)

    # Detect region from filename or description
    region = "unknown"
    name_lower = filepath.stem.lower()
    desc_lower = description.lower()

    if "frozen" in name_lower or "frozen" in desc_lower or "hypothermia" in name_lower:
        region = "frozen_reaches"
    elif "fungal" in name_lower or "fungal" in desc_lower or "spore" in name_lower or "aldric" in name_lower or "silvermoss" in name_lower or "myconid" in name_lower:
        region = "fungal_depths"
    elif "beast" in name_lower or "wolf" in name_lower or "salamander" in name_lower:
        region = "beast_wilds"
    elif "sunken" in name_lower or "flood" in name_lower:
        region = "sunken_district"
    elif "nexus" in name_lower or "meridian" in name_lower:
        region = "meridian_nexus"
    elif "civilized" in name_lower or "town" in name_lower:
        region = "civilized_remnants"

    # Detect if it's a test/demo vs actual walkthrough
    category = "walkthrough"
    if "test_" in name_lower or "demo" in name_lower or "vitals" in name_lower:
        category = "test"
    elif "phase" in name_lower:
        category = "phase_test"
    elif "output" in name_lower:
        category = "output_artifact"

    return {
        "filename": filepath.name,
        "description": description,
        "command_count": command_count,
        "assertion_count": assertion_count,
        "has_expected_failures": has_expected_failures,
        "region": region,
        "category": category,
    }

def is_obsolete(filepath: Path, metadata: dict) -> tuple[bool, str]:
    """Determine if walkthrough is likely obsolete."""
    name = filepath.stem

    # Output artifacts are obsolete
    if metadata["category"] == "output_artifact":
        return True, "Output artifact file"

    # Check for duplicate/versioned files
    if "_v2" in name or "_v3" in name or "_simple" in name:
        # Check if non-versioned equivalent exists
        base_name = name.replace("_v2", "").replace("_v3", "").replace("_simple", "")
        final_name = f"{base_name}_final"

        if (WALKTHROUGH_DIR / f"{base_name}.txt").exists():
            return True, f"Superseded by {base_name}.txt"
        elif (WALKTHROUGH_DIR / f"{final_name}.txt").exists():
            return True, f"Superseded by {final_name}.txt"

    # Check for _final suffix - might mean earlier versions are obsolete
    if "_final" in name:
        base_name = name.replace("_final", "")
        # Don't mark the _final as obsolete, but note it supersedes others
        return False, ""

    # Phase tests might be obsolete if superseded by comprehensive tests
    if "phase" in name:
        return True, "Phase test - likely superseded by comprehensive tests"

    # Some specific known obsolete files based on naming
    if "test_commands" in name or "test_output" in name:
        return True, "Test artifact file"

    return False, ""

def main():
    walkthroughs = []

    for filepath in sorted(WALKTHROUGH_DIR.glob("*.txt")):
        metadata = extract_metadata(filepath)
        is_obs, reason = is_obsolete(filepath, metadata)
        metadata["is_obsolete"] = is_obs
        metadata["obsolete_reason"] = reason
        walkthroughs.append(metadata)

    # Print summary
    print(f"Total walkthrough files: {len(walkthroughs)}\n")

    # Group by category
    by_category = defaultdict(list)
    for wt in walkthroughs:
        by_category[wt["category"]].append(wt)

    print("=== BY CATEGORY ===\n")
    for category, wts in sorted(by_category.items()):
        print(f"{category.upper()}: {len(wts)} files")
        for wt in wts:
            status = "OBSOLETE" if wt["is_obsolete"] else "ACTIVE"
            print(f"  [{status}] {wt['filename']} ({wt['command_count']} cmds, {wt['assertion_count']} asserts)")
            if wt["is_obsolete"]:
                print(f"           → {wt['obsolete_reason']}")
        print()

    # Group by region
    by_region = defaultdict(list)
    for wt in walkthroughs:
        if not wt["is_obsolete"]:
            by_region[wt["region"]].append(wt)

    print("\n=== ACTIVE BY REGION ===\n")
    for region, wts in sorted(by_region.items()):
        print(f"{region.upper()}: {len(wts)} active files")
        for wt in wts:
            print(f"  - {wt['filename']}")
            if wt["description"]:
                print(f"    {wt['description'][:80]}...")
        print()

    # Count obsolete
    obsolete_count = sum(1 for wt in walkthroughs if wt["is_obsolete"])
    print(f"\n=== SUMMARY ===")
    print(f"Total: {len(walkthroughs)}")
    print(f"Active: {len(walkthroughs) - obsolete_count}")
    print(f"Obsolete: {obsolete_count}")

    # List obsolete files for removal
    if obsolete_count > 0:
        print(f"\n=== OBSOLETE FILES (CANDIDATES FOR REMOVAL) ===\n")
        for wt in walkthroughs:
            if wt["is_obsolete"]:
                print(f"  {wt['filename']:<50} - {wt['obsolete_reason']}")

if __name__ == "__main__":
    main()
