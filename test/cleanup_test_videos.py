#!/usr/bin/env python3
"""
Cleanup script for test videos.
Removes the test_videos directory and all generated test files.
"""

import shutil
from pathlib import Path


def cleanup_test_videos():
    """Remove the test_videos directory and all its contents."""
    test_dir = Path("test_videos")

    if test_dir.exists():
        try:
            shutil.rmtree(test_dir)
            print(f"✓ Removed test directory: {test_dir}")
        except Exception as e:
            print(f"✗ Error removing {test_dir}: {e}")
    else:
        print(f"✓ Test directory {test_dir} does not exist (already cleaned up)")


if __name__ == "__main__":
    print("Cleaning up test videos...")
    cleanup_test_videos()
    print("Cleanup completed!")
