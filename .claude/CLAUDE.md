## Role of game engine vs. supporting LLM  
- in any LLM augmented game, the game engine should be responsible for all state management, including all state changes caused by user commands.
- The LLM should never cause state changes, it should only narrate state changes.

## Breaking changes
- For the current development phase, breaking changes are fine if they lead to cleaner designs
