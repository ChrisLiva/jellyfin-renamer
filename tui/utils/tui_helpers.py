"""Helper utilities for the TUI interface."""

import os
from pathlib import Path
from typing import List


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human readable format."""
    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


def get_video_extensions() -> List[str]:
    """Get list of supported video file extensions."""
    return [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".iso"]


def validate_directory(path: str) -> tuple[bool, str]:
    """
    Validate directory path.

    Returns:
        tuple: (is_valid, error_message)
    """
    if not path:
        return False, "Path cannot be empty"

    if not os.path.exists(path):
        return False, "Directory does not exist"

    if not os.path.isdir(path):
        return False, "Path is not a directory"

    if not os.access(path, os.R_OK):
        return False, "Directory is not readable"

    return True, ""


def is_video_file(filename: str) -> bool:
    """Check if file is a video file based on extension."""
    return Path(filename).suffix.lower() in get_video_extensions()


def get_file_info(file_path: str) -> dict:
    """Get file information including size and type."""
    try:
        stat = os.stat(file_path)
        return {
            "size": stat.st_size,
            "size_formatted": format_file_size(stat.st_size),
            "is_video": is_video_file(file_path),
            "extension": Path(file_path).suffix.lower(),
            "name": Path(file_path).name,
        }
    except OSError:
        return {
            "size": 0,
            "size_formatted": "0 B",
            "is_video": False,
            "extension": "",
            "name": Path(file_path).name,
        }


def scan_directory_for_videos(directory: str) -> List[dict]:
    """
    Scan directory for video files and return file information.

    Returns:
        List of dictionaries with file information
    """
    videos = []

    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if is_video_file(file):
                    file_path = os.path.join(root, file)
                    file_info = get_file_info(file_path)
                    file_info["path"] = file_path
                    file_info["relative_path"] = os.path.relpath(file_path, directory)
                    videos.append(file_info)
    except PermissionError:
        pass  # Skip directories we can't access

    return videos


def get_directory_size(directory: str) -> int:
    """Get total size of all files in directory."""
    total_size = 0
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                except OSError:
                    pass  # Skip files we can't access
    except PermissionError:
        pass  # Skip directories we can't access

    return total_size
