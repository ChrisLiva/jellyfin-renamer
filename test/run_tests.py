#!/usr/bin/env python3
"""
Test runner script that creates test videos, runs pytest, and cleans up.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n=== {description} ===")
    try:
        subprocess.run(command, shell=True, check=True, capture_output=False)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with exit code {e.returncode}")
        return False


def main():
    """Run the full test suite."""
    print("🧪 Running Jellyfin Renamer Test Suite")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("test/create_test_videos.py").exists():
        print(
            "❌ Error: test scripts not found. Make sure you're in the project root directory."
        )
        sys.exit(1)

    success = True

    # Step 1: Create test videos
    success &= run_command("python test/create_test_videos.py", "Creating test videos")

    if not success:
        print("\n❌ Failed to create test videos. Aborting test run.")
        sys.exit(1)

    # Step 2: Run pytest
    success &= run_command(
        "python -m pytest test/test_renamer.py -v", "Running pytest tests"
    )

    # Step 3: Cleanup test videos (run regardless of test results)
    cleanup_success = run_command(
        "python test/cleanup_test_videos.py", "Cleaning up test videos"
    )

    # Final results
    print("\n" + "=" * 50)
    if success and cleanup_success:
        print("🎉 All tests completed successfully!")
        sys.exit(0)
    elif success:
        print("⚠️  Tests passed but cleanup failed")
        sys.exit(1)
    else:
        print("❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
