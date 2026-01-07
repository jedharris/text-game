"""Matching strategies for reaction configurations.

Each strategy defines how to find the applicable reaction config
given the trigger context.
"""

from typing import Any, Dict, List, Optional, Tuple


class MatchStrategy:
    """Base class for match strategies."""

    def find_match(
        self,
        reactions: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Find matching reaction config.

        Args:
            reactions: Full reactions dict from entity properties
            context: Event context with trigger information

        Returns:
            (reaction_name, reaction_config) if match found, None otherwise
        """
        raise NotImplementedError


class ItemMatchStrategy(MatchStrategy):
    """Match based on accepted_items list."""

    def __init__(self, item_key: str = "accepted_items"):
        self.item_key = item_key

    def find_match(
        self,
        reactions: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Find reaction accepting the given item."""
        item = context.get("item")
        if not item:
            return None

        item_id = item.id if hasattr(item, "id") else str(item)
        item_lower = item_id.lower()

        # Search through named reactions
        for reaction_name, reaction_config in reactions.items():
            if reaction_name in ("handler", "reject_message"):
                continue
            if not isinstance(reaction_config, dict):
                continue

            accepted = reaction_config.get(self.item_key, [])

            # Check if item matches any accepted pattern (substring match)
            item_matches = any(
                pattern.lower() in item_lower for pattern in accepted
            )
            if item_matches:
                return (reaction_name, reaction_config)

        return None


class KeywordMatchStrategy(MatchStrategy):
    """Match based on keywords list."""

    def __init__(self, keyword_key: str = "keywords"):
        self.keyword_key = keyword_key

    def find_match(
        self,
        reactions: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Find reaction matching the given keyword."""
        keyword = context.get("keyword", "").lower()
        if not keyword:
            return None

        # Search through named reactions
        for reaction_name, reaction_config in reactions.items():
            if reaction_name in ("handler", "default_response"):
                continue

            keywords = reaction_config.get(self.keyword_key, [])
            keywords_lower = [k.lower() for k in keywords]
            if keyword in keywords_lower:
                return (reaction_name, reaction_config)

        return None


class NoMatchStrategy(MatchStrategy):
    """Single config, no matching required."""

    def find_match(
        self,
        reactions: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Return the entire reactions dict as single config."""
        if "handler" in reactions and len(reactions) == 1:
            return None  # Handler-only config handled separately

        # Return entire config (not nested in dict)
        return ("default", reactions)


class StateChangeMatchStrategy(MatchStrategy):
    """Match on state change type (fulfilled, abandoned, etc)."""

    def __init__(self, state_key: str = "state_change"):
        self.state_key = state_key

    def find_match(
        self,
        reactions: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Find reaction for the state change type."""
        state_change = context.get(self.state_key)
        if not state_change:
            return None

        # Look for exact state change name
        if state_change in reactions:
            return (state_change, reactions[state_change])

        return None


class ProgressiveMatchStrategy(MatchStrategy):
    """Match by index/count for progressive reveals."""

    def __init__(self, count_key: str = "examine_count"):
        self.count_key = count_key

    def find_match(
        self,
        reactions: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Find reaction at the given index."""
        count = context.get(self.count_key, 0)

        # Look for progressive_reveals list
        reveals = reactions.get("progressive_reveals", [])
        if not reveals:
            return None

        # Return reveal at index if it exists
        if count < len(reveals):
            return (f"reveal_{count}", reveals[count])

        # Return last reveal if past end
        return (f"reveal_{len(reveals)-1}", reveals[-1])
