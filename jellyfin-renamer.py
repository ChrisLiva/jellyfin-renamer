import argparse
import asyncio
import os

from core.common import scan_source_directory
from core.movie_organizer import organize_movies
from core.tv_organizer import organize_tv_shows


async def organize_mixed_content(source_dir, target_dir, downmix_audio=False):
    """Organize mixed content by auto-detecting content type."""
    print("Scanning for mixed content...")

    # Scan files and auto-detect content types
    all_files = scan_source_directory(source_dir, content_type="auto")

    # Separate files by detected type
    movie_files = [
        (root, file)
        for root, file, content_type in all_files
        if content_type == "movie"
    ]
    tv_files = [
        (root, file) for root, file, content_type in all_files if content_type == "tv"
    ]

    print(f"Found {len(movie_files)} movie files and {len(tv_files)} TV show files")

    # Create separate target directories
    movies_dir = os.path.join(target_dir, "Movies")
    shows_dir = os.path.join(target_dir, "Shows")

    # Process movies if found
    if movie_files:
        os.makedirs(movies_dir, exist_ok=True)
        print("\n=== Processing Movies ===")
        # Create a temporary source structure for movie organizer
        await organize_movies(source_dir, movies_dir, downmix_audio)

    # Process TV shows if found
    if tv_files:
        os.makedirs(shows_dir, exist_ok=True)
        print("\n=== Processing TV Shows ===")
        await organize_tv_shows(source_dir, shows_dir, downmix_audio)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organize media files for Jellyfin.")
    parser.add_argument("source_dir", help="Source directory")
    parser.add_argument("target_dir", help="Target directory")
    parser.add_argument(
        "--content-type",
        choices=["movies", "tv", "auto"],
        default="auto",
        help="Type of content to process (default: auto)",
    )
    parser.add_argument(
        "--downmix-audio",
        action="store_true",
        default=False,
        help="Downmix audio to stereo FLAC using FFmpeg (default: False)",
    )
    args = parser.parse_args()

    if args.content_type == "movies":
        asyncio.run(
            organize_movies(args.source_dir, args.target_dir, args.downmix_audio)
        )
    elif args.content_type == "tv":
        asyncio.run(
            organize_tv_shows(args.source_dir, args.target_dir, args.downmix_audio)
        )
    else:  # auto
        asyncio.run(
            organize_mixed_content(args.source_dir, args.target_dir, args.downmix_audio)
        )
