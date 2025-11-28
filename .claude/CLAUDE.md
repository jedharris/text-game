## Design priorities
- Always maximize author capability and player agency, especially when they don't conflict
- When adding features, do all the work necessary to make all relevant entities first-class citizens, participating fully in game narration and action. 

## Coding guidelines
- NEVER add local heuristics for word matching or special vocabulary
- ALWAYS rely on the merged vocabulary and WordEntry
- Vocabulary handling rules apply to testing as well as normal code

## Codebase exploration
- Use `mcp__claude-context__search_code` as the first step when exploring unfamiliar parts of the codebase or answering conceptual questions
- This finds relevant code chunks via semantic search, reducing the need to read entire files speculatively
- Use traditional tools (Glob/Grep/Read) for specific lookups when exact file/function names are known
- Re-index with `mcp__claude-context__index_codebase` if significant structural changes have been made

## Role of game engine vs. LLM  
- in any LLM augmented game, the game engine must be responsible for all state management, including all state changes caused by user commands.
- The LLM should never cause state changes, it should only narrate state changes.

## Testing
- use unitest, do not use pytest

## Breaking changes
- For the current development phase, we will continue to change the code base in ways that make a new version of the game unable to run old game save files. Right now such changes are are fine if they lead to cleaner designs.
- Going forward, when changes make incompatible changes to the game save format, do not provide backward compatibility within the code base. Instead create a separate tool that migrates the previous format game save files to the new format files. 
