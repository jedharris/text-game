"""Test suite for text adventure game parser."""
import unittest
import sys
from pathlib import Path


# Automatic module cleanup for all test modules
# This function will be injected into every test module's namespace
def _cleanup_test_module():
    """Clean up module cache pollution after all tests in a module complete."""
    # Remove all behaviors.*, behavior_libraries.*, and examples.* modules from sys.modules
    # This includes both successfully imported modules and failed import attempts
    to_remove = [k for k in list(sys.modules.keys())
                 if k.startswith('behaviors.') or k == 'behaviors' or
                    k.startswith('behavior_libraries.') or k == 'behavior_libraries' or
                    k.startswith('examples.') or k == 'examples']
    for key in to_remove:
        del sys.modules[key]

    # Remove game directories from sys.path
    project_root = Path(__file__).parent.parent
    for game_name in ['big_game', 'spatial_game', 'extended_game', 'actor_interaction_test']:
        game_dir = str(project_root / "examples" / game_name)
        while game_dir in sys.path:
            sys.path.remove(game_dir)


# Hook into unittest's module loading to inject tearDownModule
_original_load_tests_from_module = unittest.TestLoader.loadTestsFromModule

def _patched_load_tests_from_module(self, module, *args, **kwargs):
    """Patched loader that injects tearDownModule into test modules."""
    # Inject tearDownModule if not already present
    if not hasattr(module, 'tearDownModule'):
        module.tearDownModule = _cleanup_test_module
        # Debug: verify injection worked
        if not hasattr(module, 'tearDownModule'):
            print(f"WARNING: Failed to inject tearDownModule into {module.__name__}")

    # Call original loader
    return _original_load_tests_from_module(self, module, *args, **kwargs)

# Apply the patch
unittest.TestLoader.loadTestsFromModule = _patched_load_tests_from_module  # type: ignore[method-assign]
