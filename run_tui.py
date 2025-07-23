#!/usr/bin/env python3
"""
Simple entry point for the Jellyfin Renamer TUI.

This script provides an easy way to launch the TUI without command-line arguments.
"""

import sys


def main():
    """Launch the TUI application."""
    try:
        from tui import JellyfinRenamerApp

        print("🚀 Starting Jellyfin Media Renamer TUI...")
        print("Press Ctrl+C or Q to quit at any time")
        print("Press F1 for help")
        print("-" * 50)

        app = JellyfinRenamerApp()
        app.run()

    except ImportError as e:
        print("❌ Error: TUI dependencies not available.")
        print("Please install the required dependencies:")
        print("   pip install textual textual-dev")
        print(f"Details: {e}")
        return 1

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("Please check your installation and try again.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
