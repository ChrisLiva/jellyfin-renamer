# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Jellyfin Renamer is a Python CLI tool that organizes and renames movie/TV show files for the Jellyfin media server. It parses media metadata from filenames using `guessit`, creates Jellyfin-compatible folder structures, and optionally converts audio to stereo FLAC via FFmpeg.

## Commands

### Running
```bash
uv run python jellyfin-renamer.py <source> <target> [--content-type {movies,tv,auto}] [--downmix-audio]
```

### Testing
```bash
# Full test pipeline (creates test videos, runs pytest, cleans up)
uv run python test/run_tests.py

# Unit tests only (no FFmpeg required)
uv run python -m pytest test/test_renamer.py -v

# Single test
uv run python -m pytest test/test_renamer.py -v -k "test_name"
```

### Setup
```bash
uv venv && uv sync
```

## Architecture

**Entry point**: `jellyfin-renamer.py` — CLI with argparse, routes to organizers based on `--content-type`.

**`core/` modules follow a parser → organizer pipeline:**

- **Parsers** (`movie_parser.py`, `tv_parser.py`) — Extract metadata (title, year, season, episode, resolution, extras) from filenames using `guessit`. `tv_parser.py` also handles content type detection, multi-episode ranges, and extra type categorization (trailers, behind-the-scenes, etc.).
- **Organizers** (`movie_organizer.py`, `tv_organizer.py`) — Orchestrate the workflow: scan → group files → create directory structure → copy/rename files. Both are async with tqdm progress tracking.
- **`file_processor.py`** — Async FFmpeg wrapper using ThreadPoolExecutor with `asyncio.Semaphore` limiting to 2 concurrent processes. Converts audio to stereo FLAC while copying video/subtitles unchanged.
- **`common.py`** — Shared utilities: `scan_source_directory()`, `prepare_ffmpeg_tasks()`, `VIDEO_EXTS` constant (`.mp4, .mkv, .avi, .mov, .wmv, .iso`).

## Key Conventions

- Python 3.13+ required; use `uv` as the package manager
- Async throughout: organizers use `asyncio`, FFmpeg processing is async with concurrency limits
- Output folder structure follows Jellyfin naming conventions: `Movies/Title (Year)/` and `Shows/Series/Season XX/`
- Extras (trailers, interviews, deleted scenes) go in categorized subfolders within the media folder
- Duplicate files get version-numbered names
