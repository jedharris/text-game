#!/bin/bash
# SessionStart hook - isolates pycache per session for parallel work

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id')

# Clean stale caches (older than 1 day)
find /tmp -maxdepth 1 -name "pycache-*" -type d -mtime +1 -exec rm -rf {} + 2>/dev/null

# Set this session's isolated pycache
if [ -n "$CLAUDE_ENV_FILE" ] && [ -n "$SESSION_ID" ]; then
    echo "export PYTHONPYCACHEPREFIX=/tmp/pycache-${SESSION_ID}" >> "$CLAUDE_ENV_FILE"
fi

# Pass through unchanged
echo "$INPUT"
exit 0
