#!/usr/bin/env python3
"""
Test video generator for jellyfin-renamer project.
Creates short test videos covering various edge cases for movies and TV shows.
"""

import subprocess
from pathlib import Path


def create_test_video(output_path, duration=1):
    """Create a short test video using FFmpeg."""
    cmd = [
        "ffmpeg",
        "-f",
        "lavfi",
        "-i",
        f"testsrc=duration={duration}:size=320x240:rate=1",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=1000:duration={duration}",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-shortest",
        "-y",  # Overwrite output
        str(output_path),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"Created: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating {output_path}: {e}")
        return False


def create_test_directory():
    """Create test directory structure."""
    test_dir = Path("test_videos")
    test_dir.mkdir(exist_ok=True)

    # Create subdirectories for different test scenarios
    (test_dir / "movies").mkdir(exist_ok=True)
    (test_dir / "tv_shows").mkdir(exist_ok=True)
    (test_dir / "edge_cases").mkdir(exist_ok=True)

    return test_dir


def generate_movie_test_files(test_dir):
    """Generate movie test files with various naming patterns."""
    movies_dir = test_dir / "movies"

    movie_tests = [
        # Basic movie patterns
        "The.Matrix.1999.1080p.BluRay.x264.mkv",
        "Inception.2010.720p.BluRay.x264.mp4",
        "Interstellar.2014.4K.UHD.BluRay.x265.mkv",
        # Movies with special characters
        "The Lord of the Rings - The Fellowship of the Ring (2001) 1080p.mkv",
        "Pulp Fiction (1994) 720p.mp4",
        "The Shawshank Redemption (1994) 4K.mkv",
        # Movies with parts
        "The Hobbit - An Unexpected Journey (2012) 1080p - part1.mkv",
        "The Hobbit - The Desolation of Smaug (2013) 1080p - part2.mkv",
        "The Hobbit - The Battle of the Five Armies (2014) 1080p - part3.mkv",
        # Movies with multiple versions
        "Avatar (2009) 1080p - version1.mkv",
        "Avatar (2009) 1080p - version2.mkv",
        "Avatar (2009) 720p - version1.mp4",
        # Movies with no year
        "Casablanca.720p.BluRay.x264.mkv",
        "Gone with the Wind.1080p.BluRay.x264.mp4",
        # Movies with complex titles
        "Dr. Strangelove or How I Learned to Stop Worrying and Love the Bomb (1964) 1080p.mkv",
        "The Good, the Bad and the Ugly (1966) 720p.mp4",
        "2001: A Space Odyssey (1968) 4K.mkv",
        # Movies with different extensions
        "Titanic (1997) 1080p.avi",
        "Jurassic Park (1993) 720p.mov",
        "The Godfather (1972) 1080p.wmv",
        # Movies with extra content
        "The Matrix (1999) 1080p - Trailer.mkv",
        "Inception (2010) 720p - BehindTheScenes.mp4",
        "Interstellar (2014) 4K - Featurette.mkv",
        "Avatar (2009) 1080p - Interview.mkv",
        "Titanic (1997) 720p - Deleted Scenes.avi",
    ]

    for filename in movie_tests:
        file_path = movies_dir / filename
        create_test_video(file_path)


def generate_tv_show_test_files(test_dir):
    """Generate TV show test files with various naming patterns."""
    tv_dir = test_dir / "tv_shows"

    tv_tests = [
        # Standard TV show patterns
        "Breaking.Bad.S01E01.720p.BluRay.x264.mkv",
        "Game.of.Thrones.S01E01.1080p.BluRay.x264.mp4",
        "The.Wire.S01E01.720p.BluRay.x264.mkv",
        # Different season/episode formats
        "Breaking Bad S01E01 720p.mkv",
        "Game of Thrones Season 1 Episode 1 1080p.mp4",
        "The Wire S1E1 720p.mkv",
        "Stranger Things S01E01 1080p.mp4",
        # Multi-episode ranges
        "Breaking.Bad.S01E01-E02.720p.BluRay.x264.mkv",
        "Game.of.Thrones.S01E01-E02.1080p.BluRay.x264.mp4",
        "The.Wire.S01E01-E03.720p.BluRay.x264.mkv",
        # Shows with years
        "Breaking Bad (2008) S01E01 720p.mkv",
        "Game of Thrones (2011) S01E01 1080p.mp4",
        "The Wire (2002) S01E01 720p.mkv",
        # Shows with parts
        "Breaking.Bad.S01E01.Part1.720p.BluRay.x264.mkv",
        "Game.of.Thrones.S01E01.Part2.1080p.BluRay.x264.mp4",
        "The.Wire.S01E01.Part1.720p.BluRay.x264.mkv",
        # Shows with special characters
        "The Lord of the Rings - The Rings of Power S01E01 1080p.mkv",
        "Star Trek - The Next Generation S01E01 720p.mp4",
        "Marvel's Agents of S.H.I.E.L.D. S01E01 1080p.mkv",
        # Shows with different extensions
        "Breaking Bad S01E01 720p.avi",
        "Game of Thrones S01E01 1080p.mov",
        "The Wire S01E01 720p.wmv",
        # Shows with extra content
        "Breaking.Bad.S01E01.Trailer.720p.BluRay.x264.mkv",
        "Game.of.Thrones.S01E01.BehindTheScenes.1080p.BluRay.x264.mp4",
        "The.Wire.S01E01.Featurette.720p.BluRay.x264.mkv",
        "Stranger.Things.S01E01.Interview.1080p.mp4",
        "Westworld.S01E01.Deleted.Scenes.720p.mkv",
        # Shows with complex episode numbers
        "Breaking.Bad.S01E10.720p.BluRay.x264.mkv",
        "Game.of.Thrones.S01E10.1080p.BluRay.x264.mp4",
        "The.Wire.S01E10.720p.BluRay.x264.mkv",
        # Shows with multiple seasons
        "Breaking.Bad.S02E01.720p.BluRay.x264.mkv",
        "Game.of.Thrones.S02E01.1080p.BluRay.x264.mp4",
        "The.Wire.S02E01.720p.BluRay.x264.mkv",
        # Shows with no season info (should default to season 1)
        "Breaking.Bad.E01.720p.BluRay.x264.mkv",
        "Game.of.Thrones.E01.1080p.BluRay.x264.mp4",
        "The.Wire.E01.720p.BluRay.x264.mkv",
        # Shows with episode titles that contain file extensions
        "Mr.Robot.S01E01.eps1.0_hellofriend.mov.1080p.DTS-HD.MA.5.1.AVC.REMUX-FraMeSToR.mkv",
        "Mr.Robot.S01E02.eps1.1_ones-and-zer0es.mov.720p.BluRay.x264.mp4",
        "Mr.Robot.S01E03.eps1.2_d3bug.mov.1080p.WEB-DL.x264.mkv",
    ]

    for filename in tv_tests:
        file_path = tv_dir / filename
        create_test_video(file_path)


def generate_edge_case_test_files(test_dir):
    """Generate edge case test files."""
    edge_dir = test_dir / "edge_cases"

    # Files that can be created as videos
    video_edge_tests = [
        # Very long filenames
        "This.Is.A.Very.Long.Movie.Title.That.Tests.The.Limits.Of.Filename.Parsing.With.Many.Words.And.Special.Characters.2020.1080p.BluRay.x264.mkv",
        "This.Is.A.Very.Long.TV.Show.Title.That.Tests.The.Limits.Of.Filename.Parsing.With.Many.Words.And.Special.Characters.S01E01.720p.BluRay.x264.mp4",
        # Files with numbers in titles
        "2.Fast.2.Furious.2003.1080p.BluRay.x264.mkv",
        "3.10.to.Yuma.2007.720p.BluRay.x264.mp4",
        "24.S01E01.720p.BluRay.x264.mkv",
        "21.Jump.Street.2012.1080p.BluRay.x264.mkv",
        # Files with special characters
        "The.Matrix.Reloaded.(2003).1080p.BluRay.x264.mkv",
        "Mission.Impossible.2.(2000).720p.BluRay.x264.mp4",
        "X-Men.2.(2003).1080p.BluRay.x264.mkv",
        # Files with spaces and special characters
        "Movie Title With Spaces (2020) 1080p.mkv",
        "TV Show With Spaces S01E01 720p.mp4",
        "Movie.Title.With.Dots.2020.1080p.mkv",
        "TV.Show.With.Dots.S01E01.720p.mp4",
        # Files with underscores
        "Movie_Title_With_Underscores_2020_1080p.mkv",
        "TV_Show_With_Underscores_S01E01_720p.mp4",
        # Files with mixed case
        "MOVIE.TITLE.2020.1080P.BLURAY.X264.MKV",
        "tv.show.s01e01.720p.bluray.x264.mp4",
        "Movie.Title.2020.1080p.BluRay.x264.mkv",
        # Files with year-like numbers that aren't years
        "The.100.S01E01.720p.BluRay.x264.mkv",
        "24.S01E01.720p.BluRay.x264.mkv",
        "21.Jump.Street.2012.1080p.BluRay.x264.mkv",
        # Files with resolution-like numbers that aren't resolutions
        "Movie.Title.2020.1080p.BluRay.x264.mkv",
        "TV.Show.S01E01.720p.BluRay.x264.mp4",
        # Files with no detectable content type
        "Random.File.2020.1080p.mkv",
        "Test.File.720p.mp4",
    ]

    # Create video files
    for filename in video_edge_tests:
        file_path = edge_dir / filename
        create_test_video(file_path)

    # Create non-video files for testing edge cases
    non_video_files = [
        # Multiple extensions (create as text files)
        (
            "Movie.Title.2020.1080p.BluRay.x264.mkv.old",
            "This is a test file with multiple extensions",
        ),
        (
            "TV.Show.S01E01.720p.BluRay.x264.mp4.backup",
            "This is a test file with multiple extensions",
        ),
        (
            "Test.File.2020.1080p.mkv.tmp",
            "This is a test file with multiple extensions",
        ),
        # Files with no extension
        ("NoExtensionMovie.2020.1080p", "This is a test file without extension"),
        ("NoExtensionTV.S01E01.720p", "This is a test file without extension"),
        # Files with only extension
        (".mkv", "This is a test file with only extension"),
        (".mp4", "This is a test file with only extension"),
        # ISO files (create as text files for testing)
        ("Movie.Title.2020.1080p.BluRay.iso", "This is a test ISO file"),
        ("TV.Show.S01E01.720p.BluRay.iso", "This is a test ISO file"),
    ]

    for filename, content in non_video_files:
        file_path = edge_dir / filename
        try:
            with open(file_path, "w") as f:
                f.write(content)
            print(f"Created: {file_path}")
        except Exception as e:
            print(f"Error creating {file_path}: {e}")


def main():
    """Main function to create all test videos."""
    print("Creating test video files for jellyfin-renamer...")

    # Check if FFmpeg is available
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: FFmpeg is required but not found. Please install FFmpeg first.")
        return

    # Create test directory
    test_dir = create_test_directory()

    print("\nGenerating movie test files...")
    generate_movie_test_files(test_dir)

    print("\nGenerating TV show test files...")
    generate_tv_show_test_files(test_dir)

    print("\nGenerating edge case test files...")
    generate_edge_case_test_files(test_dir)

    print(f"\nTest videos created in: {test_dir}")
    print("You can now use these files to test your jellyfin-renamer functionality.")

    # Print summary
    movie_count = len(
        list((test_dir / "movies").glob("*.mp4"))
        + list((test_dir / "movies").glob("*.mkv"))
        + list((test_dir / "movies").glob("*.avi"))
        + list((test_dir / "movies").glob("*.mov"))
        + list((test_dir / "movies").glob("*.wmv"))
        + list((test_dir / "movies").glob("*.iso"))
    )
    tv_count = len(
        list((test_dir / "tv_shows").glob("*.mp4"))
        + list((test_dir / "tv_shows").glob("*.mkv"))
        + list((test_dir / "tv_shows").glob("*.avi"))
        + list((test_dir / "tv_shows").glob("*.mov"))
        + list((test_dir / "tv_shows").glob("*.wmv"))
        + list((test_dir / "tv_shows").glob("*.iso"))
    )
    edge_count = len(
        list((test_dir / "edge_cases").glob("*.mp4"))
        + list((test_dir / "edge_cases").glob("*.mkv"))
        + list((test_dir / "edge_cases").glob("*.avi"))
        + list((test_dir / "edge_cases").glob("*.mov"))
        + list((test_dir / "edge_cases").glob("*.wmv"))
        + list((test_dir / "edge_cases").glob("*.iso"))
    )

    print(f"\nSummary:")
    print(f"- Movies: {movie_count} files")
    print(f"- TV Shows: {tv_count} files")
    print(f"- Edge Cases: {edge_count} files")
    print(f"- Total: {movie_count + tv_count + edge_count} files")


if __name__ == "__main__":
    main()
