import asyncio
import json
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor

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
        list of dicts with keys: source, target, lang, embed
        Embed ops also have: sub_source
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
        sub_files = scan_subtitle_files(source_dir)

        # Group by extension for idx/sub pairing logic
        by_path = {p: p for p in sub_files}
        claimed_subs = set()  # .sub paths claimed by embed ops

        # First pass: handle .idx files (potential VobSub embeds)
        for sub_path in sub_files:
            sub_filename = os.path.basename(sub_path)
            sub_ext = os.path.splitext(sub_filename)[1].lower()
            if sub_ext != ".idx":
                continue

            sub_stem, lang = parse_subtitle_lang(sub_filename)
            matched_target = video_map.get(sub_stem)
            if matched_target is None:
                continue

            target_ext = os.path.splitext(matched_target)[1].lower()
            # Derive the paired .sub path
            sub_base = os.path.splitext(sub_path)[0]  # strip .idx
            paired_sub = sub_base + ".sub"

            if target_ext == ".mkv" and os.path.exists(paired_sub):
                # Embed op: source=idx, target=video mkv, sub_source=.sub
                ops.append({
                    "source": sub_path,
                    "target": matched_target,
                    "lang": lang,
                    "embed": True,
                    "sub_source": paired_sub,
                })
                claimed_subs.add(paired_sub)
            else:
                # Fallback: copy/move .idx normally
                target_dir = os.path.dirname(matched_target)
                target_video_base = os.path.splitext(os.path.basename(matched_target))[0]
                if lang:
                    target_subtitle = os.path.join(target_dir, f"{target_video_base}.{lang}.idx")
                else:
                    target_subtitle = os.path.join(target_dir, f"{target_video_base}.idx")
                ops.append({
                    "source": sub_path,
                    "target": target_subtitle,
                    "lang": lang,
                    "embed": False,
                })

        # Second pass: all other subtitle types (including unclaimed .sub files)
        for sub_path in sub_files:
            sub_filename = os.path.basename(sub_path)
            sub_ext = os.path.splitext(sub_filename)[1].lower()
            if sub_ext == ".idx":
                continue  # already handled
            if sub_path in claimed_subs:
                continue  # claimed by an embed op

            sub_stem, lang = parse_subtitle_lang(sub_filename)
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
                "embed": False,
            })

    return ops


async def embed_vobsub_async(video_path, idx_path, lang, pbar=None):
    """Embed a VobSub (.idx/.sub) pair into an MKV file in-place."""
    # Probe for existing subtitle stream count to get correct metadata index
    probe_cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-select_streams", "s", video_path,
    ]
    try:
        probe = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        sub_count = len(json.loads(probe.stdout).get("streams", []))
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        sub_count = 0

    base, ext = os.path.splitext(video_path)
    temp_path = f"{base}.temp{ext}"

    cmd = [
        "ffmpeg", "-i", video_path, "-i", idx_path,
        "-map", "0", "-map", "1",
        "-c", "copy",
    ]
    if lang:
        cmd += [f"-metadata:s:s:{sub_count}", f"language={lang}"]
    cmd += ["-y", temp_path]

    try:
        if pbar:
            pbar.set_description(f"Embedding: {os.path.basename(idx_path)}")
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            await loop.run_in_executor(
                executor,
                lambda: subprocess.run(cmd, check=True, capture_output=True, text=True),
            )
        os.replace(temp_path, video_path)
        if pbar:
            pbar.update(1)
        return True
    except subprocess.CalledProcessError as e:
        if pbar:
            pbar.write(f"FFmpeg error embedding {idx_path}: {e.stderr}")
            pbar.update(1)
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False


async def process_subtitle_operations(subtitle_ops, downmix_audio):
    """Process all subtitle operations with a progress bar."""
    embed_ops = [op for op in subtitle_ops if op.get("embed")]
    copy_ops = [op for op in subtitle_ops if not op.get("embed")]

    if copy_ops:
        with tqdm(copy_ops, desc="Processing subtitles") as pbar:
            for op in pbar:
                os.makedirs(os.path.dirname(op["target"]), exist_ok=True)
                if downmix_audio:
                    shutil.copy2(op["source"], op["target"])
                else:
                    shutil.move(op["source"], op["target"])

    if embed_ops:
        with tqdm(embed_ops, desc="Embedding VobSub subtitles") as pbar:
            for op in pbar:
                success = await embed_vobsub_async(op["target"], op["source"], op["lang"], pbar)
                if success and not downmix_audio:
                    for f in [op["source"], op["sub_source"]]:
                        if os.path.exists(f):
                            os.remove(f)
