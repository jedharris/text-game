"""Runtime contract validators for LLM parser integration.

These validators serve as an evolving specification for how the LLM parser
adapter must convert parser output (string IDs) to ActionDict (WordEntry objects).

The contract may change as implementation proceeds - these are not hard constraints
but rather specifications that document and validate the expected structure.
"""

from typing import Any, Dict, Optional
from src.action_types import ActionDict
from src.word_entry import WordEntry, WordType
from src.types import ActorId


class ValidationError(Exception):
    """Raised when contract validation fails."""
    pass


def validate_action_dict(data: Dict[str, Any]) -> None:
    """Validate that data conforms to ActionDict schema.

    This is a runtime check that the adapter produces valid ActionDict structures
    that match the current type definition in src/action_types.py.

    Args:
        data: Dictionary to validate

    Raises:
        ValidationError: If structure doesn't match ActionDict schema
    """
    # Required fields
    if "verb" not in data:
        raise ValidationError("ActionDict missing required field: verb")

    if not isinstance(data["verb"], str):
        raise ValidationError(f"ActionDict.verb must be str, got {type(data['verb'])}")

    # actor_id is typically added by the adapter, check if present
    # Note: ActorId is a NewType (str at runtime), so check for str
    if "actor_id" in data:
        if not isinstance(data["actor_id"], str):
            raise ValidationError(f"ActionDict.actor_id must be ActorId (str), got {type(data['actor_id'])}")

    # Optional WordEntry fields
    word_entry_fields = ["object", "indirect_object"]
    for field in word_entry_fields:
        if field in data and data[field] is not None:
            if not isinstance(data[field], WordEntry):
                raise ValidationError(
                    f"ActionDict.{field} must be WordEntry or None, got {type(data[field])}"
                )

    # Optional string fields
    string_fields = ["adjective", "indirect_adjective", "preposition", "raw_after_preposition", "raw_input"]
    for field in string_fields:
        if field in data and data[field] is not None:
            if not isinstance(data[field], str):
                raise ValidationError(
                    f"ActionDict.{field} must be str or None, got {type(data[field])}"
                )


def validate_word_entry(entry: WordEntry) -> None:
    """Validate that WordEntry structure matches current schema.

    Args:
        entry: WordEntry to validate

    Raises:
        ValidationError: If structure doesn't match schema
    """
    if not isinstance(entry.word, str):
        raise ValidationError(f"WordEntry.word must be str, got {type(entry.word)}")

    if entry.word == "":
        raise ValidationError("WordEntry.word cannot be empty string")

    # word_type can be single WordType or set of WordType
    if isinstance(entry.word_type, set):
        for wt in entry.word_type:
            if not isinstance(wt, WordType):
                raise ValidationError(
                    f"WordEntry.word_type set must contain WordType, got {type(wt)}"
                )
    elif not isinstance(entry.word_type, WordType):
        raise ValidationError(
            f"WordEntry.word_type must be WordType or Set[WordType], got {type(entry.word_type)}"
        )

    if not isinstance(entry.synonyms, list):
        raise ValidationError(f"WordEntry.synonyms must be list, got {type(entry.synonyms)}")

    for syn in entry.synonyms:
        if not isinstance(syn, str):
            raise ValidationError(f"WordEntry.synonyms must be list of str, got {type(syn)}")


def validate_parser_output(output: Dict[str, Any]) -> None:
    """Validate that LLM parser output has expected structure.

    The parser outputs simple dicts with string IDs before adapter conversion.

    Args:
        output: Parser output dict

    Raises:
        ValidationError: If structure is invalid
    """
    if "type" not in output:
        raise ValidationError("Parser output missing 'type' field")

    if output["type"] not in ["command", "error"]:
        raise ValidationError(f"Parser output type must be 'command' or 'error', got {output['type']}")

    if output["type"] == "command":
        if "action" not in output:
            raise ValidationError("Parser command output missing 'action' field")

        action = output["action"]

        if "verb" not in action:
            raise ValidationError("Parser action missing 'verb' field")

        if not isinstance(action["verb"], str):
            raise ValidationError(f"Parser action.verb must be str, got {type(action['verb'])}")

        # Optional string fields in parser output (before conversion to WordEntry)
        optional_string_fields = ["object", "indirect_object", "adjective", "indirect_adjective", "preposition"]
        for field in optional_string_fields:
            if field in action and action[field] is not None:
                if not isinstance(action[field], str):
                    raise ValidationError(
                        f"Parser action.{field} must be str or None, got {type(action[field])}"
                    )

    elif output["type"] == "error":
        if "message" not in output:
            raise ValidationError("Parser error output missing 'message' field")


def validate_adapter_contract(
    parser_output: Dict[str, Any],
    action_dict: Optional[ActionDict]
) -> None:
    """Validate the full adapter contract: parser output → ActionDict conversion.

    This validates that:
    1. Parser output is valid
    2. If adapter returns ActionDict, it's valid
    3. If adapter returns None, parser output should be error type or invalid

    Args:
        parser_output: Raw output from LLM parser
        action_dict: Result from adapter.to_action_dict()

    Raises:
        ValidationError: If contract is violated
    """
    # Validate parser output
    validate_parser_output(parser_output)

    if action_dict is not None:
        # If adapter produced ActionDict, validate it
        validate_action_dict(action_dict)  # type: ignore

        # Ensure parser output was command type
        if parser_output.get("type") != "command":
            raise ValidationError(
                f"Adapter produced ActionDict from non-command parser output: {parser_output['type']}"
            )
    else:
        # If adapter returned None, parser output should be error or invalid
        if parser_output.get("type") == "command":
            # This is allowed - adapter can reject valid parser output
            # (e.g., hallucinated object, invalid verb)
            pass
