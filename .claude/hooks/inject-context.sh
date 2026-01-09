#!/bin/bash
# Refocus hook - instructs Claude to reload context after compaction

# Read stdin (the prompt submission JSON)
INPUT=$(cat)

# Extract the user's prompt from JSON
USER_PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty')

# Only trigger if prompt contains "refocus" (case insensitive)
if ! echo "$USER_PROMPT" | grep -qi "refocus"; then
    # Not a refocus command, pass through unchanged
    echo "$INPUT"
    exit 0
fi

# Replace prompt with instruction to read refocus-docs.txt and listed files
NEW_PROMPT="The session has been compacted. Read refocus-docs.txt and then read all the files listed in it. Acknowledge when done and continue working based on current_focus.txt."

# Output modified JSON with replacement prompt
echo "$INPUT" | jq --arg newprompt "$NEW_PROMPT" '.prompt = $newprompt'
exit 0
