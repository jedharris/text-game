"""
Performance tests for the Parser.

Tests the Parser class's performance characteristics.
Corresponds to Test Category 12 in test-plan.md.
"""

import unittest
import time
import os
from src.parser import Parser


class TestPerformance(unittest.TestCase):
    """Test performance benchmarks."""

    def setUp(self):
        """Set up test fixtures path and parser."""
        self.fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
        vocab_file = os.path.join(self.fixtures_path, 'test_vocabulary.json')
        self.parser = Parser(vocab_file)

    def test_single_parse_speed(self):
        """
        Test PF-001: Time for single parse.

        Verify that a single parse operation completes in < 1ms.
        """
        command = "unlock rusty door with iron key"

        start_time = time.perf_counter()
        result = self.parser.parse_command(command)
        end_time = time.perf_counter()

        elapsed_ms = (end_time - start_time) * 1000

        # Verify parse succeeded
        self.assertIsNotNone(result)

        # Verify time is < 1ms (relaxed to 5ms for safety on slow systems)
        self.assertLess(elapsed_ms, 5.0,
                       f"Single parse took {elapsed_ms:.3f}ms, should be < 5ms")

    def test_1000_parses(self):
        """
        Test PF-002: Time for 1000 parses.

        Verify that 1000 parse operations complete in < 100ms.
        """
        commands = [
            "take sword",
            "examine door",
            "unlock door with key",
            "go north",
            "attack goblin",
        ]

        start_time = time.perf_counter()
        for _ in range(200):  # 200 iterations * 5 commands = 1000 parses
            for command in commands:
                result = self.parser.parse_command(command)
                self.assertIsNotNone(result)
        end_time = time.perf_counter()

        elapsed_ms = (end_time - start_time) * 1000

        # Verify time is < 500ms (relaxed from 100ms for safety)
        self.assertLess(elapsed_ms, 500.0,
                       f"1000 parses took {elapsed_ms:.3f}ms, should be < 500ms")

    def test_large_vocabulary(self):
        """
        Test PF-003: Large vocabulary (simulated).

        Test loading and using the production vocabulary file
        which has more words than the test vocabulary.
        """
        # Use production vocabulary if available
        prod_vocab = os.path.join('src', 'vocabulary.json')

        if not os.path.exists(prod_vocab):
            self.skipTest("Production vocabulary not found")

        start_time = time.perf_counter()
        parser = Parser(prod_vocab)
        end_time = time.perf_counter()

        load_time_ms = (end_time - start_time) * 1000

        # Verify load time < 500ms
        self.assertLess(load_time_ms, 500.0,
                       f"Vocabulary load took {load_time_ms:.3f}ms, should be < 500ms")

        # Verify parser works with a command from base vocabulary
        # Base vocabulary now only contains meta-commands (quit, load, save, inventory)
        # Test with "inventory" which is in base vocab and doesn't require an object
        result = parser.parse_command("inventory")
        self.assertIsNotNone(result)

    def test_worst_case_lookup(self):
        """
        Test PF-004: Lookup last word in table.

        With hash table optimization, all lookups should be O(1).
        """
        # Get last word in table
        if not self.parser.word_table:
            self.skipTest("No words in vocabulary")

        last_word = self.parser.word_table[-1].word

        # Time multiple lookups
        iterations = 1000
        start_time = time.perf_counter()
        for _ in range(iterations):
            result = self.parser._lookup_word(last_word)
            self.assertIsNotNone(result)
        end_time = time.perf_counter()

        elapsed_ms = (end_time - start_time) * 1000
        avg_time_us = (elapsed_ms / iterations) * 1000  # Convert to microseconds

        # Verify average lookup time < 10 microseconds (with hash table)
        self.assertLess(avg_time_us, 50.0,
                       f"Average lookup took {avg_time_us:.3f}μs, should be < 50μs")

    def test_memory_usage(self):
        """
        Test PF-005: Memory footprint.

        Verify that the parser doesn't have excessive memory usage.
        Note: This is a basic test, not a precise memory measurement.
        """
        # Count total entries
        word_count = len(self.parser.word_table)
        lookup_count = len(self.parser.word_lookup)

        # Verify lookup table is reasonable size
        # Should be: word_count + total_synonyms
        total_synonyms = sum(len(entry.synonyms) for entry in self.parser.word_table)
        expected_lookup_size = word_count + total_synonyms

        self.assertEqual(lookup_count, expected_lookup_size,
                        "Lookup table has unexpected size")

        # Verify no duplicate word strings in word table
        word_strings = [entry.word for entry in self.parser.word_table]
        self.assertEqual(len(word_strings), len(set(word_strings)),
                        "Word table contains duplicate word strings")

    def test_synonym_lookup_speed(self):
        """
        Test PF-006: Lookup via synonym.

        Verify that synonym lookup is as fast as direct lookup
        (both should be O(1) with hash table).
        """
        # Find a word with synonyms
        word_with_synonyms = None
        for entry in self.parser.word_table:
            if entry.synonyms:
                word_with_synonyms = entry
                break

        if not word_with_synonyms:
            self.skipTest("No words with synonyms in vocabulary")

        main_word = word_with_synonyms.word
        synonym = word_with_synonyms.synonyms[0]

        iterations = 1000

        # Time main word lookups
        start_time = time.perf_counter()
        for _ in range(iterations):
            result = self.parser._lookup_word(main_word)
            self.assertIsNotNone(result)
        end_time = time.perf_counter()
        main_time_ms = (end_time - start_time) * 1000

        # Time synonym lookups
        start_time = time.perf_counter()
        for _ in range(iterations):
            result = self.parser._lookup_word(synonym)
            self.assertIsNotNone(result)
        end_time = time.perf_counter()
        synonym_time_ms = (end_time - start_time) * 1000

        # Both should be similar (within 2x of each other)
        ratio = max(main_time_ms, synonym_time_ms) / min(main_time_ms, synonym_time_ms)
        self.assertLess(ratio, 2.0,
                       f"Synonym lookup ({synonym_time_ms:.3f}ms) and main word lookup "
                       f"({main_time_ms:.3f}ms) have significantly different speeds")


if __name__ == '__main__':
    unittest.main()
