#!/bin/bash
# CI check: flag mock.patch() targets using long-path game_behaviors imports.
#
# When GameEngine loads behaviors, it uses the short path (game_behaviors.*).
# If mock.patch() targets the long path (examples.*.game_behaviors.*), the patch
# won't affect the actually-loaded module, causing silent test failures.
#
# Usage: tools/check_mock_patch_paths.sh

found=0
while IFS= read -r match; do
    echo "WARNING: mock.patch with long-path game_behaviors target:"
    echo "  $match"
    echo "  mock.patch targets must use the short path (game_behaviors.*) when"
    echo "  patching modules loaded by GameEngine at runtime."
    echo
    found=1
done < <(grep -rn 'mock\.patch.*examples\.\w\+\.game_behaviors\|@patch.*examples\.\w\+\.game_behaviors' tests/)

if [ "$found" -eq 0 ]; then
    echo "OK: No mock.patch() calls with long-path game_behaviors targets found."
fi

exit $found
