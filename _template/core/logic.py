"""Core business logic for Example Tool. Shared by app.py (web) and cli.py (CLI)."""

from typing import Optional


def greet(name: str, shout: bool = False, punctuation: Optional[str] = "!") -> str:
    """Return a greeting. Pure function: no HTTP, no printing, no global state."""
    message = f"Hello, {name.strip() or 'world'}{punctuation or ''}"
    return message.upper() if shout else message
