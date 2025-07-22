import os
from guessit import guessit


def parse_movie_info(filename):
    """Parse movie details using guessit."""
    info = guessit(filename)
    title = info.get("title", os.path.splitext(filename)[0])
    year = info.get("year")
    resolution = info.get("screen_size")
    part = info.get("part")
    extra_type = None
    if "other" in info:
        if "Trailer" in info["other"]:
            extra_type = "trailers"
        elif "BehindTheScenes" in info["other"] or "Featurette" in info["other"]:
            extra_type = "behind the scenes"
    return title, year, resolution, part, extra_type