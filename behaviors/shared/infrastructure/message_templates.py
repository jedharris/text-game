"""Template substitution for reaction messages.

Supports variable substitution in message strings using {var} syntax.
"""

from typing import Any, Dict


def substitute_templates(message: str, context: Dict[str, Any]) -> str:
    """Substitute variables in message template.

    Args:
        message: Message template with {var} placeholders
        context: Context dict with variable values

    Returns:
        Message with variables substituted

    Examples:
        >>> substitute_templates("The {target} accepts your {item}",
        ...                      {"target": "wolf", "item": "meat"})
        'The wolf accepts your meat'
    """
    if not message:
        return message

    # Simple format string substitution
    # Context values are converted to strings
    safe_context = {k: str(v) for k, v in context.items() if v is not None}

    try:
        return message.format(**safe_context)
    except KeyError as e:
        # Missing variable - return original message
        return message
    except Exception:
        # Any other error - return original message
        return message


def get_message(config: Dict[str, Any], spec: Any) -> str:
    """Get message from config using spec's message keys.

    Args:
        config: Reaction configuration
        spec: ReactionSpec with message_key and fallback_message_key

    Returns:
        Message string (may be empty)
    """
    # Try primary message key
    message = config.get(spec.message_key)
    if message:
        return message

    # Try fallback message key
    message = config.get(spec.fallback_message_key)
    if message:
        return message

    # Try generic "message" key
    return config.get("message", "")
