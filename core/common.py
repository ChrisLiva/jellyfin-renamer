import os
from .tv_parser import detect_content_type

# Supported video extensions
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".iso"}


def scan_source_directory(source_dir, content_type="auto"):
    """Scan directory for video files with content type detection."""
    all_files = []
    for root, _, files in os.walk(source_dir):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in VIDEO_EXTS:
                if content_type == "auto":
                    # Auto-detect content type for each file
                    detected_type = detect_content_type(file)
                    all_files.append((root, file, detected_type))
                else:
                    # Use specified content type
                    all_files.append((root, file, content_type))
    return all_files


def prepare_ffmpeg_tasks(file_operations, downmix_audio):
    """Prepare FFmpeg processing tasks."""
    if not downmix_audio:
        return []
    
    ffmpeg_tasks = []
    for file_info, target_path in file_operations:
        base, ext = os.path.splitext(target_path)
        temp_path = f"{base}.temp{ext}"
        ffmpeg_tasks.append((target_path, temp_path))
    
    return ffmpeg_tasks