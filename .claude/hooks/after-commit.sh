#!/bin/bash
# After git commit, remind to update current_focus.txt

# Read stdin (PostToolUse JSON)
INPUT=$(cat)

# Check if this was a git commit
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only trigger for Bash tool with git commit
if [ "$TOOL_NAME" != "Bash" ]; then
    exit 0
fi

if ! echo "$COMMAND" | grep -q "git commit"; then
    exit 0
fi

# Git commit just happened - remind to update focus
echo ""
echo "=== Commit Complete ==="
echo "If focus changed, copy/paste this command:"
echo ""
echo "Update current_focus.txt with: [describe new status/phase]"
echo ""
