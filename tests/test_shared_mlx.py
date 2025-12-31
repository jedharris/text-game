"""Tests for shared MLX backend."""

import unittest
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from src.shared_mlx import SharedMLXBackend
    import mlx.core as mx
    HAS_MLX = True
except ImportError:
    HAS_MLX = False


@unittest.skipIf(not HAS_MLX, "MLX not available (requires Apple Silicon)")
class TestSharedMLXBackend(unittest.TestCase):
    """Test SharedMLXBackend with real MLX model.

    These tests load an actual model, so they're slower than typical unit tests.
    They validate that:
    1. Model loads successfully
    2. Multiple independent caches can be created
    3. Caches share the same model instance
    4. Memory usage is reasonable
    """

    @classmethod
    def setUpClass(cls):
        """Load model once for all tests."""
        # Use 7B model as specified in the plan
        cls.model_path = "mlx-community/Qwen2.5-7B-Instruct-4bit"
        print(f"\nLoading model {cls.model_path} (this may take 10-20 seconds)...")
        cls.backend = SharedMLXBackend(cls.model_path)
        print("Model loaded successfully")

    def test_model_loads_once(self):
        """Backend loads model weights once."""
        self.assertIsNotNone(self.backend.model)
        self.assertIsNotNone(self.backend.tokenizer)
        self.assertEqual(self.backend.model_path, self.model_path)

    def test_multiple_caches_created(self):
        """Multiple independent caches can be created."""
        narrator_cache, narrator_tokens = self.backend.create_narrator_cache(
            "You are a narrator."
        )
        parser_cache, parser_tokens = self.backend.create_parser_cache(
            "You are a parser."
        )

        # Both should return caches
        self.assertIsNotNone(narrator_cache)
        self.assertIsNotNone(parser_cache)

        # Token counts should be positive
        self.assertGreater(narrator_tokens, 0)
        self.assertGreater(parser_tokens, 0)

        # Caches are independent objects (different memory addresses)
        self.assertIsNot(narrator_cache, parser_cache)

    def test_cache_independence(self):
        """Caches maintain independent state."""
        cache1, tokens1 = self.backend.create_narrator_cache("Short prompt.")
        cache2, tokens2 = self.backend.create_parser_cache(
            "Much longer prompt with more tokens to ensure different cache sizes."
        )

        # Different prompt lengths should result in different token counts
        self.assertNotEqual(tokens1, tokens2)

        # Caches should have different offsets
        offset1 = cache1[0].offset
        offset2 = cache2[0].offset

        # Both should have cached some tokens
        self.assertGreater(offset1, 0)
        self.assertGreater(offset2, 0)

    def test_cache_warming(self):
        """Cache warming actually caches tokens."""
        system_prompt = "You are a test assistant with specific instructions."
        cache, token_count = self.backend.create_parser_cache(system_prompt)

        # Cache should have non-zero offset
        self.assertGreater(cache[0].offset, 0)

        # Cache offset should match or exceed token count
        # (may be slightly more due to chat template formatting)
        self.assertGreaterEqual(cache[0].offset, token_count)

        # Cache state should exist for each layer
        for layer_cache in cache:
            self.assertIsNotNone(layer_cache.state)

    def test_different_system_prompts(self):
        """Different system prompts result in different token counts."""
        short_cache, short_tokens = self.backend.create_narrator_cache("Brief.")
        long_cache, long_tokens = self.backend.create_parser_cache(
            "This is a much longer system prompt with many more words "
            "that should result in significantly more tokens being cached."
        )

        # Longer prompt should have more tokens
        self.assertGreater(long_tokens, short_tokens)

        # Cache offsets should reflect the different prompt sizes
        self.assertGreater(long_cache[0].offset, short_cache[0].offset)

    def test_cache_can_be_used_for_generation(self):
        """Cached model can generate text."""
        from mlx_lm import generate
        from mlx_lm.sample_utils import make_sampler

        # Create a cache
        cache, token_count = self.backend.create_parser_cache(
            "You are a helpful assistant."
        )

        # Build a user message
        user_messages = [{"role": "user", "content": "Say 'hello' and nothing else."}]
        user_prompt = self.backend.tokenizer.apply_chat_template(
            user_messages,
            add_generation_prompt=True,
            tokenize=False
        )

        # Generate with the cached model
        sampler = make_sampler(temp=0.0)  # Deterministic
        response = generate(
            self.backend.model,
            self.backend.tokenizer,
            prompt=user_prompt,
            max_tokens=10,
            sampler=sampler,
            prompt_cache=cache,
            verbose=False
        )

        # Should get some response
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)

    def test_memory_usage(self):
        """Memory usage is reasonable for 7B model with 2 caches."""
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            mem_before = process.memory_info().rss / 1024**3  # GB

            # Create two caches with realistic system prompts
            narrator_prompt = """You are a fantasy game narrator.
            Provide vivid, engaging descriptions while maintaining consistency.
            Follow the JSON protocol for all responses."""

            parser_prompt = """You are a command parser for a text adventure game.
            Convert natural language to JSON commands with exact entity IDs.
            Valid verbs: take, drop, examine, use, go, open, close, unlock, inventory, look."""

            narrator_cache, _ = self.backend.create_narrator_cache(narrator_prompt)
            parser_cache, _ = self.backend.create_parser_cache(parser_prompt)

            mem_after = process.memory_info().rss / 1024**3  # GB
            mem_used = mem_after - mem_before

            # Memory usage should be less than 7GB for 7B 4-bit model + 2 caches
            # (Model ~4-6GB + caches ~100MB each)
            print(f"\nMemory used by caches: {mem_used:.2f} GB")
            self.assertLess(mem_used, 7.0,
                          f"Memory usage {mem_used:.2f}GB exceeds 7GB limit")

        except ImportError:
            self.skipTest("psutil not available for memory profiling")


if __name__ == '__main__':
    unittest.main()
