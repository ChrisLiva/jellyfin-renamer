import asyncio
import os
import shutil
from collections import defaultdict

from tqdm import tqdm

from .dry_run import render_dry_run_tv
from .file_processor import process_with_ffmpeg_async
from .tv_parser import get_real_extension, parse_tv_info

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


def group_files_by_series(all_files):
    """Group files by series, season, and episode."""
    series_groups = defaultdict(lambda: defaultdict(list))

    for root, file in all_files:
        full_path = os.path.join(root, file)
        series, season, episodes, year, resolution, part, extra_type = parse_tv_info(
            file
        )

        # Create series key with year
        series_key = f"{series}"
        if year:
            series_key += f" ({year})"

        # Use season 1 as default if not detected
        if season is None:
            season = 1

        # Store file info
        file_info = {
            "path": full_path,
            "file": file,
            "series": series,
            "season": season,
            "episodes": episodes,
            "year": year,
            "resolution": resolution,
            "part": part,
            "extra_type": extra_type,
        }

        series_groups[series_key][season].append(file_info)

    return series_groups


def prepare_tv_operations(series_groups, target_dir):
    """Prepare TV show file operations. Pure function — no filesystem access."""
    all_main_files = []
    all_extra_files = []
    seen_targets = set()

    for series_key, seasons in series_groups.items():
        series_folder = os.path.join(target_dir, series_key)

        for season_num, files in seasons.items():
            season_folder = os.path.join(series_folder, f"Season {season_num:02d}")

            # Separate main files and extras
            main_files = [f for f in files if not f["extra_type"]]
            extra_files = [f for f in files if f["extra_type"]]

            # Process main files
            for file_info in main_files:
                target_filename = generate_episode_filename(
                    file_info, series_key, season_num
                )
                target_path = os.path.join(season_folder, target_filename)
                target_path = handle_duplicate_files(target_path, seen_targets)
                all_main_files.append((file_info, target_path))

            # Process extra files
            for file_info in extra_files:
                extra_folder = os.path.join(season_folder, file_info["extra_type"])
                target_path = os.path.join(extra_folder, file_info["file"])
                target_path = handle_duplicate_files(target_path, seen_targets)
                all_extra_files.append((file_info, target_path))

    return all_main_files, all_extra_files


def generate_episode_filename(file_info, series_key, season_num):
    """Generate proper Jellyfin episode filename."""
    series_name = series_key.split(" (")[0]  # Remove year for filename
    season_str = f"S{season_num:02d}"

    # Handle episode formatting
    if file_info["episodes"]:
        if isinstance(file_info["episodes"], str) and "-E" in str(
            file_info["episodes"]
        ):
            # Multi-episode format: S01E01-E02
            episode_str = f"E{file_info['episodes']}"
        else:
            # Single episode: S01E01
            episode_str = f"E{file_info['episodes']:02d}"
    else:
        episode_str = "E01"  # Default

    # Add part information
    part_str = ""
    if file_info["part"]:
        part_str = f" Part {file_info['part']}"

    # Add resolution
    resolution_str = ""
    if file_info["resolution"]:
        resolution_str = f" - {file_info['resolution']}"

    # Get file extension using the real extension function
    ext = get_real_extension(file_info["file"])

    return f"{series_name} {season_str}{episode_str}{part_str}{resolution_str}{ext}"


def handle_duplicate_files(target_path, seen_targets):
    """Handle duplicate file names using in-memory tracking."""
    if target_path not in seen_targets:
        seen_targets.add(target_path)
        return target_path

    base, ext = os.path.splitext(target_path)
    counter = 1
    while f"{base}_{counter}{ext}" in seen_targets:
        counter += 1

    result = f"{base}_{counter}{ext}"
    seen_targets.add(result)
    return result


async def organize_tv_shows(source_dir, target_dir, downmix_audio=False, dry_run=False, print_summary=True):
    """Main TV show organization function.

    When dry_run=True, returns (move_count, ffmpeg_count) tuple.
    Set print_summary=False when called from organize_mixed_content (which prints its own combined summary).
    """
    # Scan source directory
    all_files = scan_source_directory(source_dir)

    if not all_files:
        if dry_run:
            print(f"No video files found in {source_dir}")
        return (0, 0) if dry_run else None

    # Group files
    series_groups = group_files_by_series(all_files)

    # Prepare operations (pure — no filesystem access)
    all_main_files, all_extra_files = prepare_tv_operations(series_groups, target_dir)

    if dry_run:
        return render_dry_run_tv(
            all_main_files, all_extra_files, target_dir, downmix_audio,
            print_summary=print_summary,
        )

    # --- Normal execution below (existing code) ---

    # Create directories
    print("\nCreating series and season directories...")
    with tqdm(series_groups.items(), desc="Creating folders") as pbar:
        for series_key, seasons in pbar:
            series_folder = os.path.join(target_dir, series_key)
            os.makedirs(series_folder, exist_ok=True)

            for season_num in seasons.keys():
                season_folder = os.path.join(series_folder, f"Season {season_num:02d}")
                os.makedirs(season_folder, exist_ok=True)

    # Create extra folders
    for file_info, target_path in all_extra_files:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

    # Copy or move main files
    action = "Copying" if downmix_audio else "Moving"
    print(f"\n{action} and renaming episode files...")

    ffmpeg_tasks = []
    with tqdm(all_main_files, desc=f"{action} episodes") as pbar:
        for file_info, target_path in pbar:
            if downmix_audio:
                shutil.copy2(file_info["path"], target_path)
            else:
                shutil.move(file_info["path"], target_path)

            if downmix_audio:
                base, ext = os.path.splitext(target_path)
                temp_path = f"{base}.temp{ext}"
                ffmpeg_tasks.append((target_path, temp_path))

    # Move extra files
    if all_extra_files:
        print("\nMoving extra files...")
        with tqdm(all_extra_files, desc="Moving extras") as pbar:
            for file_info, target_path in pbar:
                shutil.move(file_info["path"], target_path)

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
