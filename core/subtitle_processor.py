import os
import shutil

from tqdm import tqdm

from .parser import get_base_filename_without_ext

SUBTITLE_EXTS = {".srt", ".vtt", ".ass", ".ssa", ".sub", ".idx", ".sup"}

KNOWN_LANG_CODES = {
    "en", "fr", "de", "es", "it", "pt", "ja", "ko", "zh", "ru", "nl",
    "sv", "pl", "ar", "he", "tr", "da", "fi", "no", "cs", "hu", "ro",
    "eng", "fra", "deu", "spa", "ita", "por", "jpn", "kor", "zho", "rus",
    "nld", "swe", "pol", "ara", "heb", "tur", "dan", "fin", "nor", "ces",
    "hun", "ron",
}


def parse_subtitle_lang(filename):
    """
    Parse subtitle filename to extract video stem and optional language code.

    Returns (video_stem, lang_code) or (video_stem, None).

    Examples:
        "Movie.2020.1080p.en.srt"  →  ("Movie.2020.1080p", "en")
        "Movie.2020.1080p.srt"     →  ("Movie.2020.1080p", None)
        "Movie.2020.1080p.eng.srt" →  ("Movie.2020.1080p", "eng")
    """
    parts = filename.rsplit(".", 1)
    if len(parts) < 2 or f".{parts[1].lower()}" not in SUBTITLE_EXTS:
        return (filename, None)

    stem_without_ext = parts[0]

    stem_parts = stem_without_ext.rsplit(".", 1)
    if len(stem_parts) == 2 and stem_parts[1].lower() in KNOWN_LANG_CODES:
        return (stem_parts[0], stem_parts[1].lower())

    return (stem_without_ext, None)


def scan_subtitle_files(directory):
    """Return paths of all subtitle files in directory (non-recursive)."""
    try:
        entries = os.listdir(directory)
    except OSError:
        return []

    subtitle_files = []
    for entry in entries:
        full_path = os.path.join(directory, entry)
        if not os.path.isfile(full_path):
            continue
        if os.path.splitext(entry)[1].lower() in SUBTITLE_EXTS:
            subtitle_files.append(full_path)

    return subtitle_files


def build_subtitle_operations(all_main_files):
    """
    Build a list of subtitle operations based on organized video files.

    Args:
        all_main_files: list of (file_info, target_path) tuples

    Returns:
        list of dicts with keys: source, target, lang
    """
    dir_to_videos = {}
    for file_info, target_path in all_main_files:
        source_dir = os.path.dirname(file_info["path"])
        video_stem = get_base_filename_without_ext(file_info["file"])
        if source_dir not in dir_to_videos:
            dir_to_videos[source_dir] = {}
        dir_to_videos[source_dir][video_stem] = target_path

    ops = []
    for source_dir, video_map in dir_to_videos.items():
        for sub_path in scan_subtitle_files(source_dir):
            sub_filename = os.path.basename(sub_path)
            sub_stem, lang = parse_subtitle_lang(sub_filename)
            sub_ext = os.path.splitext(sub_filename)[1].lower()

            matched_target = video_map.get(sub_stem)
            if matched_target is None:
                continue

            target_dir = os.path.dirname(matched_target)
            target_video_base = os.path.splitext(os.path.basename(matched_target))[0]

            if lang:
                target_subtitle = os.path.join(
                    target_dir, f"{target_video_base}.{lang}{sub_ext}"
                )
            else:
                target_subtitle = os.path.join(
                    target_dir, f"{target_video_base}{sub_ext}"
                )

            ops.append({
                "source": sub_path,
                "target": target_subtitle,
                "lang": lang,
            })

    return ops


async def process_subtitle_operations(subtitle_ops, downmix_audio):
    """Process all subtitle operations with a progress bar."""
    with tqdm(subtitle_ops, desc="Processing subtitles") as pbar:
        for op in pbar:
            os.makedirs(os.path.dirname(op["target"]), exist_ok=True)
            if downmix_audio:
                shutil.copy2(op["source"], op["target"])
            else:
                shutil.move(op["source"], op["target"])
