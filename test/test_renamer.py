#!/usr/bin/env python3
"""
Unit tests for jellyfin-renamer using pytest framework.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from core.organizer import organize
from core.parser import (
    get_base_filename_without_ext,
    get_real_extension,
    parse_media_info,
)
from core.subtitle_processor import build_subtitle_operations, parse_subtitle_lang


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
        ),
        (
            "Avatar (2009) 1080p - version1.mkv",
            "Avatar",
            2009,
            "1080p",
            None,
            None,
        ),
        (
            "The Hobbit - An Unexpected Journey (2012) 1080p - part1.mkv",
            "The Hobbit",
            2012,
            "1080p",
            1,
            None,
        ),
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
    info = parse_media_info(filename, "movies")

    assert info["title"] == expected_title, (
        f"Title mismatch: got '{info['title']}', expected '{expected_title}'"
    )
    assert info["year"] == expected_year, (
        f"Year mismatch: got {info['year']}, expected {expected_year}"
    )
    assert info["resolution"] == expected_resolution, (
        f"Resolution mismatch: got '{info['resolution']}', expected '{expected_resolution}'"
    )
    assert info["part"] == expected_part, (
        f"Part mismatch: got {info['part']}, expected {expected_part}"
    )
    assert info["extra_type"] == expected_extra_type, (
        f"Extra type mismatch: got {info['extra_type']}, expected {expected_extra_type}"
    )


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
        ),
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
    info = parse_media_info(filename, "tv")

    assert info["title"] == expected_series, (
        f"Series mismatch: got '{info['title']}', expected '{expected_series}'"
    )
    assert info["season"] == expected_season, (
        f"Season mismatch: got {info['season']}, expected {expected_season}"
    )
    assert info["episodes"] == expected_episodes, (
        f"Episodes mismatch: got {info['episodes']}, expected {expected_episodes}"
    )
    assert info["year"] == expected_year, (
        f"Year mismatch: got {info['year']}, expected {expected_year}"
    )
    assert info["resolution"] == expected_resolution, (
        f"Resolution mismatch: got '{info['resolution']}', expected '{expected_resolution}'"
    )
    assert info["part"] == expected_part, (
        f"Part mismatch: got {info['part']}, expected {expected_part}"
    )
    assert info["extra_type"] == expected_extra_type, (
        f"Extra type mismatch: got {info['extra_type']}, expected {expected_extra_type}"
    )


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

    test_videos_dir = Path("test_videos/movies")
    if test_videos_dir.exists():
        video_files = list(test_videos_dir.glob("*.mkv"))[:3]
        for video_file in video_files:
            shutil.copy2(video_file, source_dir)

        await organize(str(source_dir), str(target_dir), "movies", False)

        source_files = list(source_dir.glob("*"))
        target_files = list(target_dir.glob("**/*"))

        assert len(source_files) == 0, "Source should be empty after moving files"
        assert len(target_files) > 0, "Should have organized target files"

        organized_files = [f for f in target_files if f.is_file()]
        assert len(organized_files) > 0, "Should have at least one organized file"
    else:
        pytest.skip("No test videos found. Run create_test_videos.py first.")


@pytest.mark.asyncio
async def test_tv_organization(temp_dirs):
    """Test TV show organization functionality."""
    source_dir, target_dir = temp_dirs

    test_videos_dir = Path("test_videos/tv_shows")
    if test_videos_dir.exists():
        video_files = list(test_videos_dir.glob("*.mkv"))[:3]
        for video_file in video_files:
            shutil.copy2(video_file, source_dir)

        await organize(str(source_dir), str(target_dir), "tv", False)

        source_files = list(source_dir.glob("*"))
        target_files = list(target_dir.glob("**/*"))

        assert len(source_files) == 0, "Source should be empty after moving files"
        assert len(target_files) > 0, "Should have organized target files"

        season_folders = [f for f in target_files if f.is_dir() and "Season" in f.name]
        assert len(season_folders) > 0, "Should have at least one season folder"
    else:
        pytest.skip("No test videos found. Run create_test_videos.py first.")


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
    try:
        info = parse_media_info(filename, "movies")
        assert info["title"] is not None, f"Parser should return a title for {filename}"
    except Exception as e:
        pytest.fail(f"Movie parsing failed for {filename}: {e}")

    try:
        info = parse_media_info(filename, "tv")
        assert info["title"] is not None, (
            f"Parser should return a series for {filename}"
        )
    except Exception as e:
        pytest.fail(f"TV parsing failed for {filename}: {e}")


@pytest.mark.parametrize(
    "filename,expected_stem,expected_lang",
    [
        ("Movie.2020.1080p.en.srt", "Movie.2020.1080p", "en"),
        ("Movie.2020.1080p.srt", "Movie.2020.1080p", None),
        ("Movie.2020.1080p.eng.srt", "Movie.2020.1080p", "eng"),
        ("Show.S01E01.720p.fr.ass", "Show.S01E01.720p", "fr"),
        ("Show.S01E01.720p.ass", "Show.S01E01.720p", None),
        ("Movie.2020.1080p.de.vtt", "Movie.2020.1080p", "de"),
        ("Movie.2020.1080p.idx", "Movie.2020.1080p", None),
        ("Movie.2020.1080p.zh.idx", "Movie.2020.1080p", "zh"),
    ],
)
def test_parse_subtitle_lang(filename, expected_stem, expected_lang):
    """Test subtitle filename parsing for stem and language code extraction."""
    stem, lang = parse_subtitle_lang(filename)
    assert stem == expected_stem, f"Stem mismatch: got '{stem}', expected '{expected_stem}'"
    assert lang == expected_lang, f"Lang mismatch: got '{lang}', expected '{expected_lang}'"


def test_build_subtitle_operations(tmp_path):
    """Test that subtitle operations are correctly matched to their video files."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    target_dir = tmp_path / "target"
    target_dir.mkdir()

    video_file = source_dir / "Movie.2020.1080p.mkv"
    video_file.touch()
    (source_dir / "Movie.2020.1080p.en.srt").touch()
    (source_dir / "Movie.2020.1080p.srt").touch()
    (source_dir / "Movie.2020.1080p.en.idx").touch()
    (source_dir / "Movie.2020.1080p.en.sub").touch()
    (source_dir / "unrelated.srt").touch()

    file_info = {
        "path": str(video_file),
        "file": "Movie.2020.1080p.mkv",
    }
    target_path = str(target_dir / "Movie (2020)" / "Movie (2020) - 1080p.mkv")
    all_main_files = [(file_info, target_path)]

    ops = build_subtitle_operations(all_main_files)

    assert len(ops) == 4, f"Expected 4 ops, got {len(ops)}: {ops}"

    by_source = {op["source"]: op for op in ops}

    en_op = by_source[str(source_dir / "Movie.2020.1080p.en.srt")]
    assert en_op["lang"] == "en"
    assert en_op["target"].endswith("Movie (2020) - 1080p.en.srt")

    plain_op = by_source[str(source_dir / "Movie.2020.1080p.srt")]
    assert plain_op["lang"] is None
    assert plain_op["target"].endswith("Movie (2020) - 1080p.srt")

    idx_op = by_source[str(source_dir / "Movie.2020.1080p.en.idx")]
    assert idx_op["lang"] == "en"
    assert idx_op["target"].endswith("Movie (2020) - 1080p.en.idx")

    sub_op = by_source[str(source_dir / "Movie.2020.1080p.en.sub")]
    assert sub_op["lang"] == "en"
    assert sub_op["target"].endswith("Movie (2020) - 1080p.en.sub")


@pytest.mark.asyncio
async def test_subtitle_organization(temp_dirs):
    """Test that subtitle files are moved alongside their reorganized video files."""
    source_dir, target_dir = temp_dirs

    video_file = source_dir / "Movie.2020.1080p.mkv"
    video_file.write_bytes(b"fake video content")
    subtitle_file = source_dir / "Movie.2020.1080p.en.srt"
    subtitle_file.write_text("1\n00:00:01,000 --> 00:00:04,000\nHello world\n")

    await organize(str(source_dir), str(target_dir), "movies", False)

    subtitle_files = list(target_dir.glob("**/*.srt"))
    assert len(subtitle_files) == 1, (
        f"Expected 1 subtitle in target, got {len(subtitle_files)}: {subtitle_files}"
    )

    subtitle_name = subtitle_files[0].name
    assert ".en.srt" in subtitle_name, (
        f"Expected language code in subtitle filename, got: {subtitle_name}"
    )

    video_files = list(target_dir.glob("**/*.mkv"))
    assert len(video_files) == 1
    assert subtitle_files[0].parent == video_files[0].parent, (
        "Subtitle should be in the same folder as the video"
    )


class TestExtensionHandling:
    """Test class for extension handling specifically."""

    def test_multiple_extensions_mr_robot(self):
        """Test handling of Mr. Robot style filenames with multiple extensions."""
        filename = "Mr.Robot.S01E01.eps1.0_hellofriend.mov.1080p.DTS-HD.MA.5.1.AVC.REMUX-FraMeSToR.mkv"
        info = parse_media_info(filename, "tv")

        assert info["title"] == "Mr Robot"
        assert info["season"] == 1
        assert info["episodes"] == 1
        assert info["resolution"] == "1080p"

    def test_multiple_extensions_preserve_episode_names(self):
        """Test that extensions in episode names are preserved."""
        filename = "Show.S01E01.episode.name.with.dots.mov.mkv"

        base = get_base_filename_without_ext(filename)
        ext = get_real_extension(filename)

        assert base == "Show.S01E01.episode.name.with.dots.mov"
        assert ext == ".mkv"
