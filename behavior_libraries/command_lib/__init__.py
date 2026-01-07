"""Command handlers that fire hooks.

This module contains vocabulary-based command handlers that parse user input
and fire appropriate hooks. Command handlers NEVER access entity properties
or contain game logic - they only validate input and fire hooks.

All game logic resides in reaction infrastructure that subscribes to hooks.
"""
