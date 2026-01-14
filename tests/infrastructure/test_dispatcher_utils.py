"""Tests for infrastructure dispatcher utilities."""

import unittest

from examples.big_game.behaviors.shared.infrastructure.dispatcher_utils import (
    clear_handler_cache,
    load_handler,
)


class TestLoadHandler(unittest.TestCase):
    """Tests for load_handler function."""

    def setUp(self) -> None:
        """Clear handler cache before each test."""
        clear_handler_cache()

    def test_load_handler_missing_colon(self) -> None:
        """Handler path without colon returns None."""
        result = load_handler("invalid.path.no.colon")
        self.assertIsNone(result)

    def test_load_handler_invalid_module(self) -> None:
        """Non-existent module returns None."""
        result = load_handler("nonexistent.module:function")
        self.assertIsNone(result)

    def test_load_handler_invalid_function(self) -> None:
        """Non-existent function returns None."""
        result = load_handler("examples.big_game.behaviors.shared.infrastructure.dispatcher_utils:nonexistent_func")
        self.assertIsNone(result)

    def test_load_handler_valid_path(self) -> None:
        """Valid handler path returns function."""
        result = load_handler("examples.big_game.behaviors.shared.infrastructure.dispatcher_utils:load_handler")
        self.assertIsNotNone(result)
        assert result is not None  # Type narrowing for mypy
        # Verify it's the correct function by checking name and module
        self.assertEqual(result.__name__, "load_handler")
        self.assertEqual(result.__module__, "examples.big_game.behaviors.shared.infrastructure.dispatcher_utils")

    def test_load_handler_caching(self) -> None:
        """Handler is cached after first load."""
        path = "examples.big_game.behaviors.shared.infrastructure.dispatcher_utils:load_handler"
        result1 = load_handler(path)
        result2 = load_handler(path)
        self.assertIs(result1, result2)

    def test_clear_handler_cache(self) -> None:
        """clear_handler_cache removes cached handlers."""
        path = "examples.big_game.behaviors.shared.infrastructure.dispatcher_utils:load_handler"
        load_handler(path)
        clear_handler_cache()
        # After clear, handler should be reloaded (still works, just not cached)
        result = load_handler(path)
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
