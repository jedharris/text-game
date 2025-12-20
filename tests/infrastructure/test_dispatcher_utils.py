"""Tests for infrastructure dispatcher utilities."""

import unittest
from unittest.mock import MagicMock, patch

from examples.big_game.behaviors.infrastructure.dispatcher_utils import (
    clear_handler_cache,
    dispatch_or_process,
    load_handler,
)
from src.behavior_manager import EventResult


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
        result = load_handler("examples.big_game.behaviors.infrastructure.dispatcher_utils:nonexistent_func")
        self.assertIsNone(result)

    def test_load_handler_valid_path(self) -> None:
        """Valid handler path returns function."""
        result = load_handler("examples.big_game.behaviors.infrastructure.dispatcher_utils:load_handler")
        self.assertIsNotNone(result)
        self.assertEqual(result, load_handler)

    def test_load_handler_caching(self) -> None:
        """Handler is cached after first load."""
        path = "examples.big_game.behaviors.infrastructure.dispatcher_utils:load_handler"
        result1 = load_handler(path)
        result2 = load_handler(path)
        self.assertIs(result1, result2)

    def test_clear_handler_cache(self) -> None:
        """clear_handler_cache removes cached handlers."""
        path = "examples.big_game.behaviors.infrastructure.dispatcher_utils:load_handler"
        load_handler(path)
        clear_handler_cache()
        # After clear, handler should be reloaded (still works, just not cached)
        result = load_handler(path)
        self.assertIsNotNone(result)


class TestDispatchOrProcess(unittest.TestCase):
    """Tests for dispatch_or_process function."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        clear_handler_cache()
        self.entity = MagicMock()
        self.accessor = MagicMock()
        self.context = {"test": "context"}

    def test_dispatch_to_handler(self) -> None:
        """When handler is specified and valid, it is called."""
        handler_result = EventResult(allow=True, feedback="Handler called")
        mock_handler = MagicMock(return_value=handler_result)

        with patch(
            "examples.big_game.behaviors.infrastructure.dispatcher_utils.load_handler",
            return_value=mock_handler,
        ):
            config = {"handler": "some.module:handler_func"}

            def process_func(e: object, a: object, c: dict, cfg: dict) -> EventResult:
                return EventResult(allow=True, feedback="Process called")

            result = dispatch_or_process(
                entity=self.entity,
                accessor=self.accessor,
                context=self.context,
                config=config,
                config_key="test_reactions",
                process_func=process_func,
            )

        self.assertEqual(result.feedback, "Handler called")
        mock_handler.assert_called_once_with(self.entity, self.accessor, self.context)

    def test_fallback_to_process_func(self) -> None:
        """When no handler specified, process_func is called."""
        config = {"some_key": "some_value"}

        def process_func(e: object, a: object, c: dict, cfg: dict) -> EventResult:
            return EventResult(allow=True, feedback="Process called")

        result = dispatch_or_process(
            entity=self.entity,
            accessor=self.accessor,
            context=self.context,
            config=config,
            config_key="test_reactions",
            process_func=process_func,
        )

        self.assertEqual(result.feedback, "Process called")

    def test_fallback_on_handler_load_failure(self) -> None:
        """When handler fails to load, process_func is called."""
        config = {"handler": "invalid.module:nonexistent"}

        def process_func(e: object, a: object, c: dict, cfg: dict) -> EventResult:
            return EventResult(allow=True, feedback="Process called")

        result = dispatch_or_process(
            entity=self.entity,
            accessor=self.accessor,
            context=self.context,
            config=config,
            config_key="test_reactions",
            process_func=process_func,
        )

        self.assertEqual(result.feedback, "Process called")


if __name__ == "__main__":
    unittest.main()
