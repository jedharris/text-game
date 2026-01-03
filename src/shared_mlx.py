"""Shared MLX model backend for multiple prompt caches.

Enables memory-efficient use of a single MLX model for multiple purposes
(e.g., narrator and parser) by loading model weights once and creating
separate prompt caches for each use case.
"""

import logging
import os
from typing import Tuple, Any

logger = logging.getLogger(__name__)

# Check for MLX-LM availability
try:
    import mlx.core as mx
    from mlx_lm import load
    from mlx_lm.models.cache import make_prompt_cache
    HAS_MLX = True
except ImportError:
    HAS_MLX = False
    # Define dummy types for type checking when MLX not available
    mx = None  # type: ignore
    load = None  # type: ignore
    make_prompt_cache = None  # type: ignore


class SharedMLXBackend:
    """Shared MLX model instance for multiple uses with separate caches.

    This class loads an MLX model once and provides factory methods to create
    independent prompt caches for different purposes. Each cache has its own
    system prompt and maintains separate conversation state, but they all share
    the same underlying model weights.

    Example:
        >>> backend = SharedMLXBackend("mlx-community/Qwen2.5-7B-Instruct-4bit")
        >>> narrator_cache = backend.create_narrator_cache("You are a narrator...")
        >>> parser_cache = backend.create_parser_cache("You are a parser...")

        # Both caches use the same model, saving ~4-6GB memory
    """

    def __init__(self, model_path: str):
        """Load model and tokenizer once.

        Args:
            model_path: HuggingFace model path (e.g., "mlx-community/Qwen2.5-7B-Instruct-4bit")

        Raises:
            ImportError: If mlx-lm is not installed
            Exception: If model loading fails
        """
        if not HAS_MLX:
            raise ImportError(
                "MLX framework not available. Install with: pip install mlx-lm\n"
                "Note: MLX requires Apple Silicon (M1/M2/M3)"
            )

        self.model_path = model_path

        logger.info(f"Loading shared MLX model: {model_path}")

        # Set reasonable timeout for HuggingFace Hub network requests (5 seconds)
        # This prevents hanging when network is slow or unavailable
        # If model is cached locally, it will load from cache after timeout
        if 'HF_HUB_ETAG_TIMEOUT' not in os.environ:
            os.environ['HF_HUB_ETAG_TIMEOUT'] = '5'

        # load() returns (model, tokenizer, config) - we only need first two
        self.model, self.tokenizer = load(model_path)[:2]
        logger.info("Shared MLX model loaded successfully")

    def create_narrator_cache(self, system_prompt: str) -> Tuple[Any, int]:
        """Create and warm a prompt cache for narration.

        Creates an independent cache pre-warmed with the narrator's system prompt.
        This cache should be used for all narrator-related generation.

        Args:
            system_prompt: System prompt for narrator (narration protocol + style)

        Returns:
            Tuple of (cache, token_count) where cache is the warmed prompt cache
            and token_count is the number of tokens in the cached system prompt
        """
        logger.info("Creating narrator prompt cache")
        cache = make_prompt_cache(self.model)
        token_count = self._warm_cache(cache, system_prompt)
        logger.info(f"Narrator cache warmed with {token_count} tokens")
        return cache, token_count

    def create_parser_cache(self, system_prompt: str) -> Tuple[Any, int]:
        """Create and warm a prompt cache for command parsing.

        Creates an independent cache pre-warmed with the parser's system prompt.
        This cache should be used for all parser-related generation.

        Args:
            system_prompt: System prompt for parser (parsing instructions + verb list)

        Returns:
            Tuple of (cache, token_count) where cache is the warmed prompt cache
            and token_count is the number of tokens in the cached system prompt
        """
        logger.info("Creating parser prompt cache")
        cache = make_prompt_cache(self.model)
        token_count = self._warm_cache(cache, system_prompt)
        logger.info(f"Parser cache warmed with {token_count} tokens")
        return cache, token_count

    def _warm_cache(self, cache: Any, system_prompt: str) -> int:
        """Warm a cache with system prompt and return token count.

        Processes the system prompt through the model to fill the cache's KV state.
        Subsequent generations using this cache will only need to process new tokens.

        Args:
            cache: The prompt cache to warm
            system_prompt: System prompt text to cache

        Returns:
            Number of tokens in the cached system prompt
        """
        # Build system message in chat format
        messages = [{"role": "system", "content": system_prompt}]

        # Apply chat template (don't add generation prompt - user message comes next)
        prompt = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=False,
            tokenize=False
        )

        # Tokenize
        tokens = self.tokenizer.encode(prompt)
        token_count = len(tokens)

        # Process through model to warm cache
        prompt_array = mx.array(tokens)
        self.model(prompt_array[None], cache=cache)

        # Evaluate to ensure cache state is computed
        mx.eval([c.state for c in cache])

        return token_count
