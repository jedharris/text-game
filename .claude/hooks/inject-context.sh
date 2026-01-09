#!/bin/bash
# Refocus hook - loads documents when user types "refocus"

# Read stdin (the prompt submission JSON)
INPUT=$(cat)

# Extract the user's prompt from JSON
USER_PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty')

# Only trigger if prompt contains "refocus" (case insensitive)
if ! echo "$USER_PROMPT" | grep -qi "refocus"; then
    exit 0
fi

# Load documents from refocus-docs.txt
CONFIG_FILE=".claude/refocus-docs.txt"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: $CONFIG_FILE not found"
    exit 1
fi

echo "=== REFOCUSING - Loading Context ==="
echo ""

# Read config file, skip comments and empty lines
while IFS= read -r filepath || [ -n "$filepath" ]; do
    # Skip comments and empty lines
    [[ "$filepath" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${filepath// }" ]] && continue

    # Trim whitespace
    filepath=$(echo "$filepath" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

    if [ -f "$filepath" ]; then
        echo "--- $filepath ---"
        cat "$filepath"
        echo ""
    else
        echo "WARNING: File not found: $filepath"
        echo ""
    fi
done < "$CONFIG_FILE"

echo "=== END REFOCUS ==="
