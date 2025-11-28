"""
Tests for file rename (Phase C-6).

Verifies that llm_protocol.py exists and json_protocol.py is removed.
"""

import unittest
import sys


class TestFileRename(unittest.TestCase):
    """Test that file rename was done correctly."""

    def test_llm_protocol_importable(self):
        """Test that llm_protocol.py can be imported."""
        from src.llm_protocol import LLMProtocolHandler
        self.assertTrue(callable(LLMProtocolHandler))

    def test_llm_protocol_handler_exists(self):
        """Test that LLMProtocolHandler class exists and is functional."""
        from src.llm_protocol import LLMProtocolHandler
        from src.state_manager import GameState, Location, Actor, Metadata

        # Create minimal state
        state = GameState(
            metadata=Metadata(title="Test"),
            locations=[Location(id="loc1", name="Room", description="A room")],
            actors={"player": Actor(id="player", name="Adventurer", description="You", location="loc1")}
        )

        handler = LLMProtocolHandler(state)
        self.assertIsNotNone(handler)

    def test_json_protocol_import_fails(self):
        """Test that old json_protocol.py no longer exists."""
        # Remove from cache if present
        if 'src.json_protocol' in sys.modules:
            del sys.modules['src.json_protocol']

        with self.assertRaises(ImportError):
            from src.json_protocol import JSONProtocolHandler

    def test_backward_compat_alias_works(self):
        """Test that JSONProtocolHandler alias still works for backward compatibility."""
        # This allows existing code to gradually migrate
        from src.llm_protocol import JSONProtocolHandler
        self.assertTrue(callable(JSONProtocolHandler))


if __name__ == '__main__':
    unittest.main()
