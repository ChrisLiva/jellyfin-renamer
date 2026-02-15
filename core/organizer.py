import asyncio
import os
import re
import shutil
from collections import defaultdict

from tqdm import tqdm

from .file_processor import process_with_ffmpeg_async
from .parser import get_real_extension, parse_media_info

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


def handle_duplicate(target_path):
    """Handle duplicate file names by adding counter."""
    if not os.path.exists(target_path):
        return target_path

    base, ext = os.path.splitext(target_path)
    counter = 1
    while os.path.exists(f"{base}_{counter}{ext}"):
        counter += 1

    return f"{base}_{counter}{ext}"


def group_movies(all_files):
    """Group files by movie title and year."""
    movie_groups = defaultdict(list)

    for root, file in all_files:
        full_path = os.path.join(root, file)
        info = parse_media_info(file, "movies")
        key = f"{info['title']}{info['year'] or ''}"
        movie_groups[key].append(
            {
                "path": full_path,
                "file": file,
                "resolution": info["resolution"],
                "part": info["part"],
                "extra_type": info["extra_type"],
            }
        )

    return movie_groups


def group_tv(all_files):
    """Group files by series, season, and episode."""
    series_groups = defaultdict(lambda: defaultdict(list))

    for root, file in all_files:
        full_path = os.path.join(root, file)
        info = parse_media_info(file, "tv")

        series_key = info["title"]
        if info["year"]:
            series_key += f" ({info['year']})"

        file_info = {
            "path": full_path,
            "file": file,
            "series": info["title"],
            "season": info["season"],
            "episodes": info["episodes"],
            "year": info["year"],
            "resolution": info["resolution"],
            "part": info["part"],
            "extra_type": info["extra_type"],
        }

        series_groups[series_key][info["season"]].append(file_info)

    return series_groups


def prepare_movie_operations(movie_groups, target_dir):
    """Prepare all file copy operations for movies."""
    all_main_files = []
    all_extra_files = []

    for key, files in movie_groups.items():
        match = re.match(r"^(.*?)(\d{4})?$", key)
        title, year = match.groups() if match else (key, None)
        year_str = f" ({year})" if year else ""
        folder_name = f"{title}{year_str}"
        movie_folder = os.path.join(target_dir, folder_name)
        os.makedirs(movie_folder, exist_ok=True)

        main_files = [f for f in files if not f["extra_type"]]
        extra_files = [f for f in files if f["extra_type"]]

        version_counter = defaultdict(int)
        for file_info in main_files:
            res_str = f" - {file_info['resolution']}" if file_info["resolution"] else ""
            part_str = f" - part{file_info['part']}" if file_info["part"] else ""
            base_name = f"{folder_name}{res_str}{part_str}"

            version_key = f"{res_str}{part_str}"
            version_counter[version_key] += 1
            if len(main_files) > 1 and version_counter[version_key] > 1:
                base_name += f" - version{version_counter[version_key]}"

            target_file = f"{base_name}{os.path.splitext(file_info['file'])[1]}"
            target_path = os.path.join(movie_folder, target_file)
            target_path = handle_duplicate(target_path)
            all_main_files.append((file_info, target_path))

        for file_info in extra_files:
            extra_folder = os.path.join(movie_folder, file_info["extra_type"])
            os.makedirs(extra_folder, exist_ok=True)
            target_path = os.path.join(extra_folder, file_info["file"])
            target_path = handle_duplicate(target_path)
            all_extra_files.append((file_info, target_path))

    return all_main_files, all_extra_files


def generate_episode_filename(file_info, series_key, season_num):
    """Generate proper Jellyfin episode filename."""
    series_name = series_key.split(" (")[0]
    season_str = f"S{season_num:02d}"

    if file_info["episodes"]:
        if isinstance(file_info["episodes"], str) and "-E" in str(
            file_info["episodes"]
        ):
            episode_str = f"E{file_info['episodes']}"
        else:
            episode_str = f"E{file_info['episodes']:02d}"
    else:
        episode_str = "E01"

    part_str = f" Part {file_info['part']}" if file_info["part"] else ""
    resolution_str = f" - {file_info['resolution']}" if file_info["resolution"] else ""
    ext = get_real_extension(file_info["file"])

    return f"{series_name} {season_str}{episode_str}{part_str}{resolution_str}{ext}"


def prepare_tv_operations(series_groups, target_dir):
    """Prepare TV show file operations."""
    all_main_files = []
    all_extra_files = []

    for series_key, seasons in series_groups.items():
        series_folder = os.path.join(target_dir, series_key)
        os.makedirs(series_folder, exist_ok=True)

        for season_num, files in seasons.items():
            season_folder = os.path.join(series_folder, f"Season {season_num:02d}")
            os.makedirs(season_folder, exist_ok=True)

            main_files = [f for f in files if not f["extra_type"]]
            extra_files = [f for f in files if f["extra_type"]]

            for file_info in main_files:
                target_filename = generate_episode_filename(
                    file_info, series_key, season_num
                )
                target_path = os.path.join(season_folder, target_filename)
                target_path = handle_duplicate(target_path)
                all_main_files.append((file_info, target_path))

            for file_info in extra_files:
                extra_folder = os.path.join(season_folder, file_info["extra_type"])
                os.makedirs(extra_folder, exist_ok=True)
                target_path = os.path.join(extra_folder, file_info["file"])
                target_path = handle_duplicate(target_path)
                all_extra_files.append((file_info, target_path))

    return all_main_files, all_extra_files


async def run_ffmpeg_processing(ffmpeg_tasks, pbar):
    """Run FFmpeg processing with concurrency limit."""
    semaphore = asyncio.Semaphore(2)

    async def process_single_file(original_path, temp_path):
        async with semaphore:
            success = await process_with_ffmpeg_async(original_path, temp_path, pbar)
            if success:
                os.replace(temp_path, original_path)
            else:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

    tasks = [
        process_single_file(original_path, temp_path)
        for original_path, temp_path in ffmpeg_tasks
    ]
    await asyncio.gather(*tasks)


async def organize(source_dir, target_dir, content_type, downmix_audio=False):
    """
    Main organization function for both movies and TV shows.

    Args:
        source_dir: Source directory containing media files
        target_dir: Target directory for organized files
        content_type: Either "movies" or "tv"
        downmix_audio: Whether to downmix audio to stereo FLAC
    """
    all_files = scan_source_directory(source_dir)

    if not all_files:
        print(f"No video files found in {source_dir}")
        return

    print(f"\nAnalyzing {content_type} files...")

    if content_type == "movies":
        groups = group_movies(all_files)
        print(f"Found {len(groups)} movie(s)")
        print("\nCreating directories...")
        for key in tqdm(groups.keys(), desc="Creating folders"):
            match = re.match(r"^(.*?)(\d{4})?$", key)
            title, year = match.groups() if match else (key, None)
            year_str = f" ({year})" if year else ""
            folder_name = f"{title}{year_str}"
            movie_folder = os.path.join(target_dir, folder_name)
            os.makedirs(movie_folder, exist_ok=True)
        all_main_files, all_extra_files = prepare_movie_operations(groups, target_dir)
    else:
        groups = group_tv(all_files)
        total_episodes = sum(
            len(episodes)
            for seasons in groups.values()
            for episodes in seasons.values()
        )
        print(f"Found {len(groups)} series with {total_episodes} episode(s)")
        print("\nCreating directories...")
        for series_key, seasons in tqdm(groups.items(), desc="Creating folders"):
            series_folder = os.path.join(target_dir, series_key)
            os.makedirs(series_folder, exist_ok=True)
            for season_num in seasons.keys():
                season_folder = os.path.join(series_folder, f"Season {season_num:02d}")
                os.makedirs(season_folder, exist_ok=True)
        all_main_files, all_extra_files = prepare_tv_operations(groups, target_dir)

    action = "Copying" if downmix_audio else "Moving"
    print(f"\n{action} main files...")

    ffmpeg_tasks = []
    with tqdm(all_main_files, desc=f"{action} files") as pbar:
        for file_info, target_path in pbar:
            if downmix_audio:
                shutil.copy2(file_info["path"], target_path)
            else:
                shutil.move(file_info["path"], target_path)

            if downmix_audio:
                base, ext = os.path.splitext(target_path)
                temp_path = f"{base}.temp{ext}"
                ffmpeg_tasks.append((target_path, temp_path))

    if all_extra_files:
        print("\nMoving extra files...")
        with tqdm(all_extra_files, desc="Moving extras") as pbar:
            for file_info, target_path in pbar:
                shutil.move(file_info["path"], target_path)

    if downmix_audio and ffmpeg_tasks:
        print(f"\nProcessing {len(ffmpeg_tasks)} file(s) with FFmpeg...")
        await run_ffmpeg_processing(ffmpeg_tasks, None)

    print("\nDone!")
