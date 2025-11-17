"""
Custom exception classes for state manager.
"""

from typing import List


class GameStateError(Exception):
    """Base class for all game state errors."""
    pass


class SchemaError(GameStateError):
    """Raised when JSON structure violates schema requirements."""
    pass


class ValidationError(GameStateError):
    """Raised when cross-reference validation fails."""

    def __init__(self, message: str, errors: List[str] = None):
        """
        Initialize validation error.

        Args:
            message: Main error message
            errors: List of individual validation error messages
        """
        super().__init__(message)
        self.errors = errors or []

    def __str__(self):
        if self.errors:
            error_list = '\n  '.join(f"{i+1}. {err}" for i, err in enumerate(self.errors))
            return f"{self.args[0]}\n  {error_list}"
        return self.args[0]


class FileLoadError(GameStateError):
    """Raised when file I/O operations fail."""
    pass
