"""
Interaction Logger for Test Bed

Captures and filters interactions for debugging and verification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.state_accessor import HandlerResult


class LogLevel(Enum):
    """Log verbosity levels."""

    ERRORS = "errors"  # Only issues
    CHANGES = "changes"  # State changes and issues
    ALL = "all"  # Everything


@dataclass
class LogEntry:
    """A single interaction log entry."""

    turn: int
    phase: str
    action: str
    state_before: dict[str, Any]
    state_after: dict[str, Any]
    result: "HandlerResult | None"
    issues: list[str] = field(default_factory=list)

    def has_issues(self) -> bool:
        """Check if this entry has any issues."""
        return len(self.issues) > 0

    def has_state_change(self) -> bool:
        """Check if state changed."""
        return self.state_before != self.state_after


class InteractionLogger:
    """Configurable logger for test bed interactions."""

    def __init__(self, level: LogLevel = LogLevel.ERRORS) -> None:
        """Initialize logger with verbosity level."""
        self.level = level
        self._entries: list[LogEntry] = []

    def log(self, entry: LogEntry) -> None:
        """Add an entry to the log."""
        self._entries.append(entry)

    def get_entries(self) -> list[LogEntry]:
        """Get all entries based on current log level."""
        match self.level:
            case LogLevel.ERRORS:
                return [e for e in self._entries if e.has_issues()]
            case LogLevel.CHANGES:
                return [e for e in self._entries if e.has_issues() or e.has_state_change()]
            case LogLevel.ALL:
                return list(self._entries)
        return []

    def get_issues(self) -> list[tuple[int, str]]:
        """Get all issues as (turn, message) tuples."""
        issues: list[tuple[int, str]] = []
        for entry in self._entries:
            for issue in entry.issues:
                issues.append((entry.turn, issue))
        return issues

    def has_issues(self) -> bool:
        """Check if any entries have issues."""
        return any(e.has_issues() for e in self._entries)

    def clear(self) -> None:
        """Clear all log entries."""
        self._entries.clear()

    def __len__(self) -> int:
        """Return total number of entries."""
        return len(self._entries)
