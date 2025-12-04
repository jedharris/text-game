"""Meta/system commands - quit, save, load.

These commands control the game session rather than game state.
They return signals that the game loop processes for session-level operations
like file I/O, state reload, and loop control.
"""

from src.state_accessor import HandlerResult
from src.word_entry import WordEntry

# Vocabulary extension - adds meta/system command verbs
vocabulary = {
    "verbs": [
        {
            "word": "quit",
            "synonyms": ["exit"],
            "object_required": False,
            "llm_context": {
                "traits": ["ends game session", "meta-command"]
            }
        },
        {
            "word": "save",
            "synonyms": [],
            "object_required": "optional",
            "llm_context": {
                "traits": ["saves current progress", "meta-command"]
            }
        },
        {
            "word": "load",
            "synonyms": ["restore"],
            "object_required": "optional",
            "llm_context": {
                "traits": ["restores saved game", "meta-command"]
            }
        }
    ],
    "nouns": [],
    "adjectives": [],
    "directions": []
}


def handle_quit(accessor, action):
    """
    Handle quit command - signals game should exit.

    Args:
        accessor: StateAccessor instance (not used)
        action: Action dict (not used)

    Returns:
        HandlerResult with quit signal in data field
    """
    return HandlerResult(
        success=True,
        message="Thanks for playing!",
        data={
            "signal": "quit"
        }
    )


def handle_save(accessor, action):
    """
    Handle save command - signals save needed.

    Extracts filename from action object or raw input for the game loop
    to process. The game loop will invoke file dialogs if no filename provided.

    Args:
        accessor: StateAccessor instance (not used)
        action: Action dict with keys:
            - object: Optional WordEntry or string with filename
            - raw_input: Original command string for fallback parsing

    Returns:
        HandlerResult with save signal and optional filename in data field
    """
    filename = None

    # Extract filename from object (either WordEntry or string)
    if action.get("object"):
        obj = action["object"]
        if isinstance(obj, WordEntry):
            filename = obj.word
        elif isinstance(obj, str):
            filename = obj

    return HandlerResult(
        success=True,
        message="Saving game...",
        data={
            "signal": "save",
            "filename": filename,
            "raw_input": action.get("raw_input", "")
        }
    )


def handle_load(accessor, action):
    """
    Handle load command - signals load needed.

    Extracts filename from action object or raw input for the game loop
    to process. The game loop will invoke file dialogs if no filename provided,
    and handle state reload after successful load.

    Args:
        accessor: StateAccessor instance (not used)
        action: Action dict with keys:
            - object: Optional WordEntry or string with filename
            - raw_input: Original command string for fallback parsing

    Returns:
        HandlerResult with load signal and optional filename in data field
    """
    filename = None

    # Extract filename from object (either WordEntry or string)
    if action.get("object"):
        obj = action["object"]
        if isinstance(obj, WordEntry):
            filename = obj.word
        elif isinstance(obj, str):
            filename = obj

    return HandlerResult(
        success=True,
        message="Loading game...",
        data={
            "signal": "load",
            "filename": filename,
            "raw_input": action.get("raw_input", "")
        }
    )
