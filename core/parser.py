import os
import re

from guessit import guessit


def get_filename_for_parsing(filename):
    """Get filename with only the last extension for parsing purposes."""
    parts = filename.split(".")
    if len(parts) < 2:
        return filename
    base_parts = parts[:-1]
    extension = parts[-1]
    base_name = ".".join(base_parts)
    return f"{base_name}.{extension}"


def get_base_filename_without_ext(filename):
    """Get base filename without any extensions, preserving extensions in episode names."""
    parts = filename.split(".")
    if len(parts) < 2:
        return filename
    return ".".join(parts[:-1])


def get_real_extension(filename):
    """Get the actual file extension (last extension only)."""
    parts = filename.split(".")
    if len(parts) < 2:
        return ""
    return f".{parts[-1]}"


def detect_extra_type(guessit_info):
    """Detect extra/special content type from guessit info."""
    if "other" not in guessit_info:
        return None

    others = guessit_info["other"]
    if not isinstance(others, list):
        others = [others]

    for other in others:
        other_str = str(other)
        if "Trailer" in other_str:
            return "trailers"
        if "BehindTheScenes" in other_str or "Featurette" in other_str:
            return "behind the scenes"
        if "Interview" in other_str:
            return "interviews"
        if "Deleted" in other_str:
            return "deleted scenes"

    return None


def detect_multi_part(filename, guessit_info):
    """Detect part information from filename."""
    if "part" in guessit_info:
        return guessit_info["part"]

    part_patterns = [
        r"[.\s-]part[.\s-]?(\d+)",
        r"[.\s-]pt[.\s-]?(\d+)",
        r"[.\s-]p(\d+)",
    ]

    filename_lower = filename.lower()
    for pattern in part_patterns:
        match = re.search(pattern, filename_lower)
        if match:
            return int(match.group(1))

    return None


def normalize_episode_range(episode):
    """Handle multi-episode formatting."""
    if not episode:
        return None

    if isinstance(episode, list):
        if len(episode) == 1:
            return episode[0]
        elif len(episode) == 2:
            return f"{episode[0]:02d}-E{episode[1]:02d}"
        else:
            return f"{episode[0]:02d}-E{episode[-1]:02d}"

    return episode


def parse_movie_info(filename):
    """Parse movie details using guessit."""
    info = guessit(filename)
    title = info.get("title", os.path.splitext(filename)[0])
    year = info.get("year")
    resolution = info.get("screen_size")
    part = info.get("part")
    extra_type = detect_extra_type(info)

    return {
        "title": title,
        "year": year,
        "resolution": resolution,
        "part": part,
        "extra_type": extra_type,
        "season": None,
        "episodes": None,
    }


def parse_tv_info(filename):
    """Parse TV show details using guessit and custom logic."""
    filename_for_parsing = get_filename_for_parsing(filename)
    info = guessit(filename_for_parsing)

    series = info.get("title", get_base_filename_without_ext(filename))
    season = info.get("season")
    episode = info.get("episode")
    year = info.get("year")
    resolution = info.get("screen_size")

    episodes = normalize_episode_range(episode)
    part = detect_multi_part(filename_for_parsing, info)
    extra_type = detect_extra_type(info)

    if season is None:
        season = 1

    return {
        "title": series,
        "year": year,
        "resolution": resolution,
        "part": part,
        "extra_type": extra_type,
        "season": season,
        "episodes": episodes,
    }


def parse_media_info(filename, content_type):
    """
    Unified parser for both movies and TV shows.

    Args:
        filename: The filename to parse
        content_type: Either "movies" or "tv"

    Returns:
        dict with keys: title, year, resolution, part, extra_type,
        and for TV: season, episodes
    """
    if content_type == "tv":
        return parse_tv_info(filename)
    return parse_movie_info(filename)
