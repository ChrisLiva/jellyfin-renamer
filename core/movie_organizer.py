import asyncio
import os
import re
import shutil
from collections import defaultdict

from tqdm import tqdm

from .file_processor import process_with_ffmpeg_async
from .movie_parser import parse_movie_info

# Supported video extensions
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".iso"}


def scan_source_directory(source_dir):
    """Scan source directory and return all video files."""
    all_files = []
    for root, _, files in os.walk(source_dir):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in VIDEO_EXTS:
                all_files.append((root, file))
    return all_files


def group_files_by_movie(all_files):
    """Group files by movie title and year."""
    movie_groups = defaultdict(list)

    for root, file in all_files:
        full_path = os.path.join(root, file)
        title, year, resolution, part, extra_type = parse_movie_info(file)
        key = f"{title}{year or ''}"
        movie_groups[key].append(
            {
                "path": full_path,
                "file": file,
                "resolution": resolution,
                "part": part,
                "extra_type": extra_type,
            }
        )

    return movie_groups


def prepare_file_operations(movie_groups, target_dir):
    """Prepare all file copy operations and return lists of main and extra files to process."""
    all_main_files = []
    all_extra_files = []

    for key, files in movie_groups.items():
        title, year = re.match(r"^(.*?)(\d{4})?$", key).groups()
        year_str = f" ({year})" if year else ""
        folder_name = f"{title}{year_str}"
        movie_folder = os.path.join(target_dir, folder_name)
        os.makedirs(movie_folder, exist_ok=True)

        # Separate main files and extras
        main_files = [f for f in files if not f["extra_type"]]
        extra_files = [f for f in files if f["extra_type"]]

        # Prepare main files with target paths
        version_counter = defaultdict(int)
        for file_info in main_files:
            res_str = f" - {file_info['resolution']}" if file_info["resolution"] else ""
            part_str = f" - part{file_info['part']}" if file_info["part"] else ""
            base_name = f"{folder_name}{res_str}{part_str}"

            # Check for duplicates and add version if needed
            version_key = f"{res_str}{part_str}"
            version_counter[version_key] += 1
            if len(main_files) > 1 and version_counter[version_key] > 1:
                base_name += f" - version{version_counter[version_key]}"

            target_file = f"{base_name}{os.path.splitext(file_info['file'])[1]}"
            target_path = os.path.join(movie_folder, target_file)

            # Avoid overwrite by adding unique suffix if needed
            if os.path.exists(target_path):
                base, ext = os.path.splitext(target_path)
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                target_path = f"{base}_{counter}{ext}"

            all_main_files.append((file_info, target_path))

        # Prepare extra files
        for file_info in extra_files:
            extra_folder = os.path.join(movie_folder, file_info["extra_type"])
            os.makedirs(extra_folder, exist_ok=True)
            target_path = os.path.join(extra_folder, file_info["file"])

            # Avoid overwrite
            if os.path.exists(target_path):
                base, ext = os.path.splitext(target_path)
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                target_path = f"{base}_{counter}{ext}"

            all_extra_files.append((file_info, target_path))

    return all_main_files, all_extra_files


async def organize_movies(source_dir, target_dir, downmix_audio=False):
    """Organize movies from source to target in Jellyfin format."""

    # Scan source directory
    all_files = scan_source_directory(source_dir)

    # Group files with progress bar
    print("\nAnalyzing files...")
    with tqdm(all_files, desc="Analyzing files") as pbar:
        movie_groups = group_files_by_movie(all_files)
        for _ in pbar:
            pass

    # Create directories and prepare operations
    print("\nCreating directories...")
    with tqdm(movie_groups.items(), desc="Creating folders") as pbar:
        for key, files in pbar:
            title, year = re.match(r"^(.*?)(\d{4})?$", key).groups()
            year_str = f" ({year})" if year else ""
            folder_name = f"{title}{year_str}"
            movie_folder = os.path.join(target_dir, folder_name)
            os.makedirs(movie_folder, exist_ok=True)

    all_main_files, all_extra_files = prepare_file_operations(movie_groups, target_dir)

    # Copy main files
    print("\nCopying and renaming main files...")

    ffmpeg_tasks = []
    with tqdm(all_main_files, desc="Copying main files") as pbar:
        for file_info, target_path in pbar:
            shutil.copy2(file_info["path"], target_path)

            if downmix_audio:
                base, ext = os.path.splitext(target_path)
                temp_path = f"{base}.temp{ext}"
                ffmpeg_tasks.append((target_path, temp_path))

    # Copy extra files
    if all_extra_files:
        print("\nCopying extra files...")
        with tqdm(all_extra_files, desc="Copying extras") as pbar:
            for file_info, target_path in pbar:
                shutil.copy2(file_info["path"], target_path)

    # Process with FFmpeg if needed
    if downmix_audio and ffmpeg_tasks:
        print(
            f"\nProcessing {len(ffmpeg_tasks)} file(s) with FFmpeg (max 2 concurrent)..."
        )

        semaphore = asyncio.Semaphore(2)

        async def process_single_file(original_path, temp_path, pbar):
            async with semaphore:
                success = await process_with_ffmpeg_async(
                    original_path, temp_path, pbar
                )
                if success:
                    os.replace(temp_path, original_path)
                else:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

        with tqdm(total=len(ffmpeg_tasks), desc="FFmpeg processing") as pbar:
            tasks = [
                process_single_file(original_path, temp_path, pbar)
                for original_path, temp_path in ffmpeg_tasks
            ]
            await asyncio.gather(*tasks)
