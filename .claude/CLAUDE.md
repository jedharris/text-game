## Role of game engine vs. supporting LLM  
- in any LLM augmented game, the game engine should be responsible for all state management, including all state changes caused by user commands.
- The LLM should never cause state changes, it should only narrate state changes.

## Error Handling Philosophy
- Errors that game developers can and should find during development (e.g., missing core behaviors, invalid module paths) should fail loudly and early. No graceful degradation needed.
- Silent errors must be avoided since they might not be discovered and fixed. If something fails, it should be visible. 

## Breaking changes
- For the current development phase, breaking changes are fine if they lead to cleaner designs
- A breaking change that requires changes to types or data structures used pervasively throughout the game should start by changing those types or data structures, and only then go on to local code changes

## Complex changes broken into phases
- Any complex change should be broken into fairly small phases with TDD for each phase, and the phasing plan should be written up and maintained throughout the process
- Progress, issues encountered and any work deferred should be recorded in the phasing plan at the end of each phase.
- Work deferred should be re-entered into the plan at a later phase. 
- If managing the phasing becomes complex or confusing the plan should be discussed and thoroughly revised or rewritten. 