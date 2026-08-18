import re

from guessit import guessit


def get_filename_for_parsing(filename):
    """Get filename with only the last extension for parsing purposes."""
    # Split by dots to handle multiple extensions
    parts = filename.split(".")
    if len(parts) < 2:
        return filename

    # Keep everything except the last part (which is the real extension)
    base_parts = parts[:-1]
    extension = parts[-1]

    # Rejoin with dots but use only the last extension
    base_name = ".".join(base_parts)
    return f"{base_name}.{extension}"


def get_base_filename_without_ext(filename):
    """Get base filename without any extensions, preserving extensions in episode names."""
    # Split by dots
    parts = filename.split(".")
    if len(parts) < 2:
        return filename

    # Return everything except the last part (the real extension)
    return ".".join(parts[:-1])


def get_real_extension(filename):
    """Get the actual file extension (last extension only)."""
    parts = filename.split(".")
    if len(parts) < 2:
        return ""
    return f".{parts[-1]}"


def parse_tv_info(filename):
    """Parse TV show details using guessit and custom logic."""
    # Handle multiple extensions - use only the last one as the actual extension
    filename_for_parsing = get_filename_for_parsing(filename)

    info = guessit(filename_for_parsing)

    # Basic info extraction
    series = info.get("title", get_base_filename_without_ext(filename))
    season = info.get("season")
    episode = info.get("episode")
    year = info.get("year")
    resolution = info.get("screen_size")

    # Handle multi-episode detection
    episodes = normalize_episode_range(episode)

    # Handle multi-part detection
    part = detect_multi_part(filename_for_parsing, info)

    # Handle extras
    extra_type = detect_extra_type(info)

    return series, season, episodes, year, resolution, part, extra_type


def normalize_episode_range(episode):
    """Handle multi-episode formatting."""
    if not episode:
        return None

    # If episode is already a list (multi-episode), format as range
    if isinstance(episode, list):
        if len(episode) == 1:
            return episode[0]
        elif len(episode) == 2:
            return f"{episode[0]:02d}-E{episode[1]:02d}"
        else:
            # Handle more than 2 episodes
            return f"{episode[0]:02d}-E{episode[-1]:02d}"

    # Single episode
    return episode


def detect_multi_part(filename, guessit_info):
    """Detect part information from filename."""
    # Check guessit first
    if "part" in guessit_info:
        return guessit_info["part"]

    # Custom patterns for parts
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


def detect_extra_type(guessit_info):
    """Detect extra/special content type."""
    if "other" in guessit_info:
        others = guessit_info["other"]
        if not isinstance(others, list):
            others = [others]

        for other in others:
            if "Trailer" in str(other):
                return "trailers"
            elif "BehindTheScenes" in str(other) or "Featurette" in str(other):
                return "behind the scenes"
            elif "Interview" in str(other):
                return "interviews"
            elif "Deleted" in str(other):
                return "deleted scenes"

    return None


def extract_series_info(filename):
    """Extract series name and year, handling edge cases."""
    info = guessit(filename)
    series = info.get("title", "")
    year = info.get("year")

    # Clean up series name
    if series:
        # Remove common artifacts
        series = re.sub(r"\b(season|s)\s*\d+\b", "", series, flags=re.IGNORECASE)
        series = series.strip()

    return series, year


def detect_content_type(filename):
    """Detect if file is movie or TV show."""
    info = guessit(filename)

    # Strong indicators of TV shows
    if info.get("season") is not None or info.get("episode") is not None:
        return "tv"

    # Check for common TV show patterns in filename
    tv_patterns = [
        r"[sS]\d{1,2}[eE]\d{1,2}",  # S01E01 pattern
        r"[sS]eason\s*\d+",  # Season pattern
        r"[eE]pisode\s*\d+",  # Episode pattern
    ]

    for pattern in tv_patterns:
        if re.search(pattern, filename):
            return "tv"

    # Default to movie if no TV indicators found
    return "movie"
