"""Shared helpers for command parsing and JSON protocol conversion."""

from typing import Any, Dict

from src.types import ActorId
from src.action_types import ActionDict
from src.parsed_command import ParsedCommand


def parsed_to_json(result: ParsedCommand) -> Dict[str, Any]:
    """Convert ParsedCommand to JSON protocol format.

    WordEntry objects are preserved for objects so synonym matching keeps working.
    Verbs, adjectives, and prepositions use their .word string.
    """
    assert result.verb is not None, "parsed_to_json requires a verb"
    action: ActionDict = {"verb": result.verb.word, "actor_id": ActorId("player")}

    if result.direct_object:
        action["object"] = result.direct_object
    if result.direct_adjective:
        action["adjective"] = result.direct_adjective.word
    if result.preposition:
        action["preposition"] = result.preposition.word
    if result.indirect_object:
        action["indirect_object"] = result.indirect_object
    if result.indirect_adjective:
        action["indirect_adjective"] = result.indirect_adjective.word

    return {"type": "command", "action": action}
