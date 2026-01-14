#!/bin/bash
# Refocus hook - when prompt is exactly "refocus", output instructions to read files from refocus-docs.txt

INPUT=$(cat)
USER_PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty')
TRIMMED=$(echo "$USER_PROMPT" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr '[:upper:]' '[:lower:]')

if [ "$TRIMMED" != "refocus" ]; then
    exit 0
fi

# Read refocus-docs.txt and build file list
REFOCUS_DOCS="/Users/jed/Development/text-game/refocus-docs.txt"
if [ ! -f "$REFOCUS_DOCS" ]; then
    exit 0
fi

# Parse file list (skip comments and empty lines), prepend repo root
FILES=$(grep -v '^#' "$REFOCUS_DOCS" | grep -v '^[[:space:]]*$' | while read -r line; do
    echo "/Users/jed/Development/text-game/$line"
done)

# Output instructions for Claude to read the files
echo "REFOCUS: You must now read ALL of these files in order before responding:"
echo "$FILES" | nl
echo ""
echo "Read each file using the Read tool. After reading ALL files, summarize what you learned and continue work based on current_focus.txt."
exit 0
