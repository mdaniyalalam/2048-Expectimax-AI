"""Console helpers shared by the CLI entry points."""

import os

def clear_screen():
    """Clear the terminal on Windows and Unix."""
    os.system("cls" if os.name == "nt" else "clear")

def ask(prompt, default, cast=str):
    """Prompt for a value converted with 'cast'; return 'default' if empty or invalid."""
    text = input(prompt).strip()
    try:
        return cast(text) if text else default
    except ValueError:
        return default

def pause(message="Press Enter to go back to the menu..."):
    """Wait for Enter, ignoring EOF and Ctrl+C."""
    try:
        input(f"\n{message}")
    except (EOFError, KeyboardInterrupt):
        pass
