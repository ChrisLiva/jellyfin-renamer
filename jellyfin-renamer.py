import argparse
import asyncio

from core.organizer import organize


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organize media files for Jellyfin.")
    parser.add_argument("source_dir", help="Source directory")
    parser.add_argument("target_dir", help="Target directory")
    parser.add_argument(
        "--content-type",
        choices=["movies", "tv"],
        required=True,
        help="Type of content to process",
    )
    parser.add_argument(
        "--downmix-audio",
        action="store_true",
        default=False,
        help="Downmix audio to stereo FLAC using FFmpeg (default: False)",
    )
    args = parser.parse_args()

    asyncio.run(
        organize(
            args.source_dir, args.target_dir, args.content_type, args.downmix_audio
        )
    )
