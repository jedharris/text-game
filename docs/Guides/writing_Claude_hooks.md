# Writing Claude Code Hooks - Practical Guide

## Overview

Claude Code hooks are shell scripts that intercept events in the Claude VS Code extension. This guide covers what actually works, not what you might assume.

## Hook Configuration Format

In `.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/absolute/path/to/script.sh"
          }
        ]
      }
    ]
  }
}
```

**Key points:**
- `"UserPromptSubmit"`: Hook type (when it fires)
- `"matcher": ""`: Empty string = match all prompts. Can filter with regex/glob patterns.
- `"command"`: **Use absolute path**, not relative. The configurator sometimes generates broken paths - verify manually.
- Script must be executable: `chmod +x script.sh`

## Available Hook Types

From Claude Code documentation:
1. `PreToolUse` - Before tool execution
2. `PostToolUse` - After tool execution
3. `PostToolUseFailure` - After tool execution fails
4. `Notification` - When notifications are sent
5. `UserPromptSubmit` - When user submits a prompt (presses enter)

**NO post-compaction hook exists** - use `UserPromptSubmit` with a keyword trigger instead.

## Hook Input/Output Model

### Input (stdin)
Hook receives JSON on stdin with event-specific fields. For `UserPromptSubmit`:

```json
{
  "session_id": "...",
  "transcript_path": "...",
  "cwd": "/path/to/project",
  "permission_mode": "acceptEdits",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "<ide_opened_file>...</ide_opened_file>\nUser's actual message"
}
```

**Important:** The `prompt` field includes IDE metadata tags (like `<ide_opened_file>`), not just the user's text.

### Output (stdout)
- **For passthrough:** Echo the input JSON unchanged, exit 0
- **For modification:** Echo modified JSON (e.g., change `.prompt` field), exit 0
- **For blocking:** Exit 2 (but stderr output may not reach Claude in VS Code)

### Stderr
- Goes to VS Code logs, **NOT visible to Claude**
- Don't rely on stderr for injecting context
- Use for debugging only

### Exit Codes
- `0` = Success, allow prompt/action to continue
- `2` = Block the prompt/action (but output lost in VS Code)
- Other codes = Error

## Common Patterns

### Pattern 1: Keyword-Triggered Context Injection

**Use case:** Load documents after compaction when user types "refocus"

```bash
#!/bin/bash

INPUT=$(cat)
USER_PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty')

# Only trigger on keyword
if ! echo "$USER_PROMPT" | grep -qi "refocus"; then
    echo "$INPUT"
    exit 0
fi

# Build new prompt with loaded files
NEW_PROMPT="=== Context Loaded ===\n\n"
NEW_PROMPT="${NEW_PROMPT}$(cat current_focus.txt)\n\n"
NEW_PROMPT="${NEW_PROMPT}=== End Context ===\n\nAcknowledge context loaded."

# Output modified JSON
echo "$INPUT" | jq --arg newprompt "$NEW_PROMPT" '.prompt = $newprompt'
exit 0
```

**Why this works:**
- Checks for keyword in prompt
- Replaces prompt text with loaded file contents
- Exit 0 sends modified prompt to Claude
- Claude sees the files as part of your message

**Why NOT to use exit 2 + stderr:**
- Exit 2 blocks the prompt entirely
- Stderr output doesn't reach Claude in VS Code
- You get log references instead of injected context

### Pattern 2: Debugging Hook Behavior

```bash
#!/bin/bash

INPUT=$(cat)

# Save JSON to inspect format
echo "$INPUT" > /tmp/hook-debug.json

# Pass through unchanged
echo "$INPUT"
exit 0
```

Then check `/tmp/hook-debug.json` to see actual JSON structure.

### Pattern 3: Conditional Passthrough

```bash
#!/bin/bash

INPUT=$(cat)
USER_PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty')

# Only process certain commands
if ! echo "$USER_PROMPT" | grep -qE "^/(commit|refocus)"; then
    echo "$INPUT"
    exit 0
fi

# ... do processing ...
echo "$INPUT" | jq '.prompt = "modified"'
exit 0
```

## Pitfalls to Avoid

### ❌ Recursive Loading
```bash
# BAD - triggers on EVERY prompt, including hook's own output
if true; then
    cat docs/guide.md >&2
fi
```

**Fix:** Use keyword trigger, only fire when user explicitly requests it.

### ❌ Relative Paths in Config
```json
// BAD - may not resolve correctly
"command": ".claude/hooks/script.sh"

// GOOD - always use absolute paths
"command": "/Users/jed/project/.claude/hooks/script.sh"
```

### ❌ Relying on Stderr for Context
```bash
# BAD - stderr doesn't reach Claude in VS Code
cat important_context.md >&2
exit 2
```

**Fix:** Inject into `.prompt` field via stdout JSON modification.

### ❌ Forgetting to Passthrough
```bash
# BAD - consumes input but produces no output
INPUT=$(cat)
# ... forgot to echo ...
exit 0
```

**Fix:** Always `echo "$INPUT"` for passthrough cases.

### ❌ Not Testing Hook Independently
Hooks fail silently. **Always test:**
```bash
echo '{"prompt": "test"}' | .claude/hooks/script.sh
```

Verify output is valid JSON before deploying.

## Debugging Hooks

1. **Check if hook is running:**
   ```bash
   # Add to script
   echo "$INPUT" > /tmp/hook-debug.json
   ```

2. **Check VS Code logs:**
   - View → Output → Select "Claude Code" from dropdown
   - Help → Toggle Developer Tools → Console tab

3. **Test independently:**
   ```bash
   echo '{"prompt": "refocus"}' | .claude/hooks/inject-context.sh
   ```

4. **Verify JSON output:**
   ```bash
   echo '{"prompt": "test"}' | .claude/hooks/script.sh | jq .
   ```

## Complete Working Example: Refocus Hook

**`.claude/refocus-docs.txt`:**
```
# Files to load after compaction
current_focus.txt
docs/Guides/claude_session_guide.md
```

**`.claude/hooks/inject-context.sh`:**
```bash
#!/bin/bash
# Refocus hook - loads documents when user types "refocus"

INPUT=$(cat)
USER_PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty')

# Only trigger if prompt contains "refocus"
if ! echo "$USER_PROMPT" | grep -qi "refocus"; then
    echo "$INPUT"
    exit 0
fi

# Build augmented prompt with loaded files
CONFIG_FILE=".claude/refocus-docs.txt"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "$INPUT"
    exit 0
fi

NEW_PROMPT="=== Context Loaded After Compaction ===\n\n"

while IFS= read -r filepath || [ -n "$filepath" ]; do
    [[ "$filepath" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${filepath// }" ]] && continue

    filepath=$(echo "$filepath" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

    if [ -f "$filepath" ]; then
        NEW_PROMPT="${NEW_PROMPT}--- File: $filepath ---\n"
        NEW_PROMPT="${NEW_PROMPT}$(cat "$filepath")\n\n"
    fi
done < "$CONFIG_FILE"

NEW_PROMPT="${NEW_PROMPT}=== End Context Load ===\n\nI have reloaded the context files listed above. Please acknowledge and continue working."

echo "$INPUT" | jq --arg newprompt "$NEW_PROMPT" '.prompt = $newprompt'
exit 0
```

**`.claude/settings.json`:**
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/Users/jed/Development/text-game/.claude/hooks/inject-context.sh"
          }
        ]
      }
    ]
  }
}
```

**Usage:**
1. After compaction, type: `refocus`
2. Hook loads files from refocus-docs.txt
3. Claude receives files as part of your message
4. Edit refocus-docs.txt to customize loaded files

## Summary

**What works:**
- Modifying `.prompt` field in JSON via stdout
- Exit 0 for passthrough or modified output
- Keyword triggers to avoid recursion
- Absolute paths in configuration

**What doesn't work (in VS Code):**
- Exit 2 + stderr for context injection (output lost)
- Relative paths in hook configuration
- Assuming stderr reaches Claude
- Running on every prompt without filtering

**Golden rule:** Test hooks independently with sample JSON before deploying. Hooks fail silently, so verify behavior outside VS Code first.
