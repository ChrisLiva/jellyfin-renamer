#!/usr/bin/env python3
"""
Unit tests for jellyfin-renamer using pytest framework.
"""
import shutil
import tempfile
from pathlib import Path

import pytest

from core.dry_run import render_dry_run_movies, render_dry_run_tv
from core.movie_organizer import group_files_by_movie, organize_movies, prepare_file_operations
from core.movie_parser import parse_movie_info
from core.tv_organizer import group_files_by_series, handle_duplicate_files, organize_tv_shows, prepare_tv_operations
from core.tv_parser import detect_content_type, parse_tv_info


@pytest.mark.parametrize(
    "filename,expected_title,expected_year,expected_resolution,expected_part,expected_extra_type",
    [
        (
            "The.Matrix.1999.1080p.BluRay.x264.mkv",
            "The Matrix",
            1999,
            "1080p",
            None,
            None,
        ),
        ("Inception.2010.720p.BluRay.x264.mp4", "Inception", 2010, "720p", None, None),
        (
            "The Lord of the Rings - The Fellowship of the Ring (2001) 1080p.mkv",
            "The Lord of the Rings",
            2001,
            "1080p",
            None,
            None,
        ),  # guessit truncates long titles
        (
            "Avatar (2009) 1080p - version1.mkv",
            "Avatar",
            2009,
            "1080p",
            None,
            None,
        ),  # guessit doesn't detect "version1" as extra_type
        (
            "The Hobbit - An Unexpected Journey (2012) 1080p - part1.mkv",
            "The Hobbit",
            2012,
            "1080p",
            1,
            None,
        ),  # guessit detects part correctly
        (
            "The Matrix (1999) 1080p - Trailer.mkv",
            "The Matrix",
            1999,
            "1080p",
            None,
            "trailers",
        ),
        (
            "Dr. Strangelove or How I Learned to Stop Worrying and Love the Bomb (1964) 1080p.mkv",
            "Dr Strangelove or How I Learned to Stop Worrying and Love the Bomb",
            1964,
            "1080p",
            None,
            None,
        ),
    ],
)
def test_movie_parsing(
    filename,
    expected_title,
    expected_year,
    expected_resolution,
    expected_part,
    expected_extra_type,
):
    """Test movie filename parsing with various patterns."""
    title, year, resolution, part, extra_type = parse_movie_info(filename)

    assert (
        title == expected_title
    ), f"Title mismatch: got '{title}', expected '{expected_title}'"
    assert year == expected_year, f"Year mismatch: got {year}, expected {expected_year}"
    assert (
        resolution == expected_resolution
    ), f"Resolution mismatch: got '{resolution}', expected '{expected_resolution}'"
    assert (
        part == expected_part
    ), f"Part mismatch: got '{part}', expected '{expected_part}'"
    assert (
        extra_type == expected_extra_type
    ), f"Extra type mismatch: got '{extra_type}', expected '{expected_extra_type}'"


@pytest.mark.parametrize(
    "filename,expected_series,expected_season,expected_episodes,expected_year,expected_resolution,expected_part,expected_extra_type",
    [
        (
            "Breaking.Bad.S01E01.720p.BluRay.x264.mkv",
            "Breaking Bad",
            1,
            1,
            None,
            "720p",
            None,
            None,
        ),
        (
            "Game of Thrones S01E01 1080p.mp4",
            "Game of Thrones",
            1,
            1,
            None,
            "1080p",
            None,
            None,
        ),
        (
            "Breaking.Bad.S01E01-E02.720p.BluRay.x264.mkv",
            "Breaking Bad",
            1,
            "01-E02",
            None,
            "720p",
            None,
            None,
        ),
        (
            "Breaking Bad (2008) S01E01 720p.mkv",
            "Breaking Bad",
            1,
            1,
            2008,
            "720p",
            None,
            None,
        ),
        (
            "Breaking.Bad.S01E01.Part1.720p.BluRay.x264.mkv",
            "Breaking Bad",
            1,
            1,
            None,
            "720p",
            1,
            None,
        ),
        (
            "Breaking.Bad.S01E01.Trailer.720p.BluRay.x264.mkv",
            "Breaking Bad",
            1,
            1,
            None,
            "720p",
            None,
            "trailers",
        ),
        (
            "The Lord of the Rings - The Rings of Power S01E01 1080p.mkv",
            "The Lord of the Rings",
            1,
            1,
            None,
            "1080p",
            None,
            None,
        ),  # guessit truncates long series names
        (
            "Mr.Robot.S01E01.eps1.0_hellofriend.mov.1080p.DTS-HD.MA.5.1.AVC.REMUX.mkv",
            "Mr Robot",
            1,
            1,
            None,
            "1080p",
            None,
            None,
        ),
    ],
)
def test_tv_parsing(
    filename,
    expected_series,
    expected_season,
    expected_episodes,
    expected_year,
    expected_resolution,
    expected_part,
    expected_extra_type,
):
    """Test TV show filename parsing with various patterns."""
    series, season, episodes, year, resolution, part, extra_type = parse_tv_info(
        filename
    )

    assert (
        series == expected_series
    ), f"Series mismatch: got '{series}', expected '{expected_series}'"
    assert (
        season == expected_season
    ), f"Season mismatch: got {season}, expected {expected_season}"
    assert (
        episodes == expected_episodes
    ), f"Episodes mismatch: got {episodes}, expected {expected_episodes}"
    assert year == expected_year, f"Year mismatch: got {year}, expected {expected_year}"
    assert (
        resolution == expected_resolution
    ), f"Resolution mismatch: got '{resolution}', expected '{expected_resolution}'"
    assert (
        part == expected_part
    ), f"Part mismatch: got '{part}', expected '{expected_part}'"
    assert (
        extra_type == expected_extra_type
    ), f"Extra type mismatch: got '{extra_type}', expected '{expected_extra_type}'"


@pytest.mark.parametrize(
    "filename,expected_type",
    [
        ("The.Matrix.1999.1080p.BluRay.x264.mkv", "movie"),
        ("Breaking.Bad.S01E01.720p.BluRay.x264.mkv", "tv"),
        ("Game of Thrones S01E01 1080p.mp4", "tv"),
        ("Inception.2010.720p.BluRay.x264.mp4", "movie"),
        ("Random.File.2020.1080p.mkv", "movie"),  # Default to movie
    ],
)
def test_content_type_detection(filename, expected_type):
    """Test content type detection."""
    detected_type = detect_content_type(filename)
    assert (
        detected_type == expected_type
    ), f"Content type mismatch: got '{detected_type}', expected '{expected_type}'"


@pytest.fixture
def temp_dirs():
    """Create temporary source and target directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        source_dir = Path(temp_dir) / "source"
        target_dir = Path(temp_dir) / "target"
        source_dir.mkdir()
        target_dir.mkdir()
        yield source_dir, target_dir


@pytest.mark.asyncio
async def test_movie_organization(temp_dirs):
    """Test movie organization functionality."""
    source_dir, target_dir = temp_dirs

    # Copy some test movies to source
    test_videos_dir = Path("test_videos/movies")
    if test_videos_dir.exists():
        video_files = list(test_videos_dir.glob("*.mkv"))[:3]  # Test with first 3 files
        for video_file in video_files:
            shutil.copy2(video_file, source_dir)

        # Run organization
        await organize_movies(str(source_dir), str(target_dir))

        # Check results
        source_files = list(source_dir.glob("*"))
        target_files = list(target_dir.glob("**/*"))

        assert len(source_files) > 0, "Should have source files"
        assert len(target_files) > 0, "Should have organized target files"

        # Verify at least one organized file exists
        organized_files = [f for f in target_files if f.is_file()]
        assert len(organized_files) > 0, "Should have at least one organized file"
    else:
        pytest.skip("No test videos found. Run create_test_videos.py first.")


@pytest.mark.asyncio
async def test_tv_organization(temp_dirs):
    """Test TV show organization functionality."""
    source_dir, target_dir = temp_dirs

    # Copy some test TV shows to source
    test_videos_dir = Path("test_videos/tv_shows")
    if test_videos_dir.exists():
        video_files = list(test_videos_dir.glob("*.mkv"))[:3]  # Test with first 3 files
        for video_file in video_files:
            shutil.copy2(video_file, source_dir)

        # Run organization
        await organize_tv_shows(str(source_dir), str(target_dir))

        # Check results
        source_files = list(source_dir.glob("*"))
        target_files = list(target_dir.glob("**/*"))

        assert len(source_files) > 0, "Should have source files"
        assert len(target_files) > 0, "Should have organized target files"

        # Verify season folders are created
        season_folders = [f for f in target_files if f.is_dir() and "Season" in f.name]
        assert len(season_folders) > 0, "Should have at least one season folder"
    else:
        pytest.skip("No test videos found. Run create_test_videos.py first.")


def test_prepare_file_operations_is_pure(tmp_path):
    """prepare_file_operations() should work without touching the filesystem."""
    # Use a target dir that does NOT exist — proves no os.makedirs/os.path.exists
    nonexistent_target = str(tmp_path / "nonexistent" / "deep" / "path")

    all_files = [
        (str(tmp_path), "Inception.2010.1080p.BluRay.mkv"),
        (str(tmp_path), "Inception.2010.720p.BluRay.mkv"),
    ]
    movie_groups = group_files_by_movie(all_files)
    main_files, extra_files = prepare_file_operations(movie_groups, nonexistent_target)

    assert len(main_files) == 2
    assert len(extra_files) == 0
    # Target paths should be under the nonexistent target dir
    for file_info, target_path in main_files:
        assert target_path.startswith(nonexistent_target)
    # The nonexistent dir should still not exist
    assert not (tmp_path / "nonexistent").exists()


def test_prepare_tv_operations_is_pure(tmp_path):
    """prepare_tv_operations() should work without touching the filesystem."""
    nonexistent_target = str(tmp_path / "nonexistent" / "deep" / "path")

    all_files = [
        (str(tmp_path), "Breaking.Bad.S01E01.720p.BluRay.x264.mkv"),
        (str(tmp_path), "Breaking.Bad.S01E02.720p.BluRay.x264.mkv"),
    ]
    series_groups = group_files_by_series(all_files)
    main_files, extra_files = prepare_tv_operations(series_groups, nonexistent_target)

    assert len(main_files) == 2
    assert len(extra_files) == 0
    for file_info, target_path in main_files:
        assert target_path.startswith(nonexistent_target)
        assert "Season 01" in target_path
    assert not (tmp_path / "nonexistent").exists()


@pytest.mark.parametrize(
    "filename",
    [
        "Movie.Title.2020.1080p.BluRay.x264.mkv.old",
        "TV.Show.S01E01.720p.BluRay.x264.mp4.backup",
        "NoExtensionMovie.2020.1080p",
        "Movie Title With Spaces (2020) 1080p.mkv",
        "Movie_Title_With_Underscores_2020_1080p.mkv",
        "2.Fast.2.Furious.2003.1080p.BluRay.x264.mkv",
        "The.100.S01E01.720p.BluRay.x264.mkv",
        "Mr.Robot.S01E01.eps1.0_hellofriend.mov.1080p.DTS-HD.MA.5.1.AVC.REMUX-FraMeSToR.mkv",
    ],
)
def test_edge_cases(filename):
    """Test edge case handling - ensure parsers don't crash on unusual filenames."""
    # Test movie parsing doesn't crash
    try:
        title, year, resolution, part, extra_type = parse_movie_info(filename)
        assert title is not None, f"Movie parser should return a title for {filename}"
    except Exception as e:
        pytest.fail(f"Movie parsing failed for {filename}: {e}")

    # Test TV parsing doesn't crash
    try:
        series, season, episodes, year, resolution, part, extra_type = parse_tv_info(
            filename
        )
        assert series is not None, f"TV parser should return a series for {filename}"
    except Exception as e:
        pytest.fail(f"TV parsing failed for {filename}: {e}")

    # Test content type detection doesn't crash
    try:
        content_type = detect_content_type(filename)
        assert content_type in [
            "movie",
            "tv",
        ], f"Content type should be 'movie' or 'tv', got {content_type}"
    except Exception as e:
        pytest.fail(f"Content type detection failed for {filename}: {e}")


class TestExtensionHandling:
    """Test class for extension handling specifically."""

    def test_multiple_extensions_mr_robot(self):
        """Test handling of Mr. Robot style filenames with multiple extensions."""
        filename = "Mr.Robot.S01E01.eps1.0_hellofriend.mov.1080p.DTS-HD.MA.5.1.AVC.REMUX-FraMeSToR.mkv"
        series, season, episodes, year, resolution, part, extra_type = parse_tv_info(
            filename
        )

        assert series == "Mr Robot"
        assert season == 1
        assert episodes == 1
        # The key test: the extension handling should work properly
        assert resolution == "1080p"  # Should still detect resolution

    def test_multiple_extensions_preserve_episode_names(self):
        """Test that extensions in episode names are preserved."""
        from core.tv_parser import get_base_filename_without_ext, get_real_extension

        filename = "Show.S01E01.episode.name.with.dots.mov.mkv"

        base = get_base_filename_without_ext(filename)
        ext = get_real_extension(filename)

        assert base == "Show.S01E01.episode.name.with.dots.mov"
        assert ext == ".mkv"


def test_movie_prepare_duplicate_detection(tmp_path):
    """Duplicate movie files should get version suffixes via in-memory tracking."""
    all_files = [
        (str(tmp_path), "Inception.2010.1080p.BluRay.mkv"),
        (str(tmp_path), "Inception.2010.1080p.WEB.mkv"),
    ]
    movie_groups = group_files_by_movie(all_files)
    main_files, _ = prepare_file_operations(movie_groups, str(tmp_path / "target"))

    paths = [t for _, t in main_files]
    assert len(paths) == len(set(paths)), "All target paths should be unique"


def test_tv_handle_duplicate_files_in_memory():
    """handle_duplicate_files() should use in-memory set for dedup."""
    seen = set()
    path1 = handle_duplicate_files("/target/Show S01E01.mkv", seen)
    path2 = handle_duplicate_files("/target/Show S01E01.mkv", seen)

    assert path1 == "/target/Show S01E01.mkv"
    assert path2 == "/target/Show S01E01_1.mkv"
    assert path1 in seen
    assert path2 in seen


def test_dry_run_movie_output(tmp_path, capsys):
    """Dry-run should print grouped tree for movies."""
    all_files = [
        (str(tmp_path), "Inception.2010.1080p.BluRay.mkv"),
    ]
    movie_groups = group_files_by_movie(all_files)
    target = str(tmp_path / "target")
    main_files, extra_files = prepare_file_operations(movie_groups, target)

    render_dry_run_movies(main_files, extra_files, target, downmix_audio=False)

    output = capsys.readouterr().out
    assert "Inception (2010)/" in output
    assert "[MOVE]" in output
    assert "Inception.2010.1080p.BluRay.mkv" in output or "Inception (2010)" in output
    assert "would be moved" in output


def test_dry_run_tv_output(tmp_path, capsys):
    """Dry-run should print grouped tree for TV shows."""
    all_files = [
        (str(tmp_path), "Breaking.Bad.S01E01.720p.BluRay.x264.mkv"),
        (str(tmp_path), "Breaking.Bad.S01E02.720p.BluRay.x264.mkv"),
    ]
    series_groups = group_files_by_series(all_files)
    target = str(tmp_path / "target")
    main_files, extra_files = prepare_tv_operations(series_groups, target)

    render_dry_run_tv(main_files, extra_files, target, downmix_audio=False)

    output = capsys.readouterr().out
    assert "Breaking Bad/" in output
    assert "Season 01/" in output
    assert "[MOVE]" in output
    assert "would be moved" in output


def test_dry_run_ffmpeg_labels(tmp_path, capsys):
    """Dry-run with downmix_audio should show [COPY + FFMPEG] for main files."""
    all_files = [
        (str(tmp_path), "Inception.2010.1080p.BluRay.mkv"),
    ]
    movie_groups = group_files_by_movie(all_files)
    target = str(tmp_path / "target")
    main_files, extra_files = prepare_file_operations(movie_groups, target)

    render_dry_run_movies(main_files, extra_files, target, downmix_audio=True)

    output = capsys.readouterr().out
    assert "[COPY + FFMPEG]" in output
    assert "would be copied + processed with FFmpeg" in output


def test_dry_run_extras_always_move(tmp_path, capsys):
    """Extras should show [MOVE] even when downmix_audio is True."""
    all_files = [
        (str(tmp_path), "Inception.2010.1080p.BluRay.mkv"),
        (str(tmp_path), "The Matrix (1999) 1080p - Trailer.mkv"),
    ]
    movie_groups = group_files_by_movie(all_files)
    target = str(tmp_path / "target")
    main_files, extra_files = prepare_file_operations(movie_groups, target)

    render_dry_run_movies(main_files, extra_files, target, downmix_audio=True)

    output = capsys.readouterr().out
    # Main files get COPY + FFMPEG
    assert "[COPY + FFMPEG]" in output
    # Verify extras were detected
    assert len(extra_files) > 0, "Trailer should be classified as an extra"
    # Find trailer output lines and verify they show [MOVE]
    trailer_lines = [
        line for line in output.splitlines()
        if "<-" in line and ("trailers/" in line.lower() or "Trailer" in line)
    ]
    assert trailer_lines, "Expected at least one trailer output line"
    for line in trailer_lines:
        assert "[MOVE]" in line, f"Extras should always be [MOVE], got: {line}"


def test_dry_run_extras_subfolder_tree(tmp_path, capsys):
    """Extras should appear under their subfolder in the tree."""
    all_files = [
        (str(tmp_path), "The Matrix (1999) 1080p - Trailer.mkv"),
    ]
    movie_groups = group_files_by_movie(all_files)
    target = str(tmp_path / "target")
    main_files, extra_files = prepare_file_operations(movie_groups, target)

    render_dry_run_movies(main_files, extra_files, target, downmix_audio=False)

    output = capsys.readouterr().out
    assert "trailers/" in output.lower()


@pytest.mark.asyncio
async def test_movie_dry_run_no_side_effects(tmp_path):
    """Dry-run should not create any files or directories."""
    source_dir = tmp_path / "source"
    target_dir = tmp_path / "target"
    source_dir.mkdir()
    target_dir.mkdir()

    # Create a dummy video file
    (source_dir / "Inception.2010.1080p.BluRay.mkv").write_bytes(b"\x00" * 100)

    await organize_movies(str(source_dir), str(target_dir), dry_run=True)

    # Target should be empty
    assert list(target_dir.iterdir()) == []
    # Source file should still exist (not moved)
    assert (source_dir / "Inception.2010.1080p.BluRay.mkv").exists()


@pytest.mark.asyncio
async def test_tv_dry_run_no_side_effects(tmp_path):
    """Dry-run should not create any files or directories."""
    source_dir = tmp_path / "source"
    target_dir = tmp_path / "target"
    source_dir.mkdir()
    target_dir.mkdir()

    (source_dir / "Breaking.Bad.S01E01.720p.BluRay.x264.mkv").write_bytes(b"\x00" * 100)

    await organize_tv_shows(str(source_dir), str(target_dir), dry_run=True)

    assert list(target_dir.iterdir()) == []
    assert (source_dir / "Breaking.Bad.S01E01.720p.BluRay.x264.mkv").exists()
