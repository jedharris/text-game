"""Type definitions for action dictionaries and protocol messages."""

from typing import Optional, TypedDict, Protocol, Literal

from src.types import ActorId
from src.word_entry import WordEntry
from src.state_accessor import HandlerResult


class ActionDict(TypedDict, total=False):
    """Structured action payload passed to handlers."""

    actor_id: ActorId
    verb: str
    object: Optional[WordEntry]
    adjective: str
    indirect_object: Optional[WordEntry]
    indirect_adjective: str
    preposition: str
    raw_after_preposition: str
    raw_input: str


class CommandMessage(TypedDict):
    """Protocol command message."""

    type: Literal["command"]
    action: ActionDict


class ResultError(TypedDict, total=False):
    """Error payload for unsuccessful results."""

    message: str
    fatal: bool


class ResultMessage(TypedDict, total=False):
    """Result payload returned by protocol handler."""

    type: Literal["result", "error"]
    success: bool
    action: str
    message: str
    data: dict
    error: ResultError
    turn_phase_messages: list[str]
    verbosity: str


class HandlerCallable(Protocol):
    """Signature for behavior handlers."""

    def __call__(self, accessor, action: ActionDict) -> HandlerResult:
        ...
