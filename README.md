# Jellyfin Renamer

A Python CLI tool that organizes and renames movie and TV show files for Jellyfin media server. Parses media metadata from filenames using `guessit`, creates Jellyfin-compatible folder structures, and optionally converts audio to stereo FLAC via FFmpeg.

Follows Jellyfin recommendations on media organization:
- https://jellyfin.org/docs/general/server/media/movies
- https://jellyfin.org/docs/general/server/media/shows

## Features

- **Smart Media Parsing** — Uses `guessit` to extract titles, years, resolution, parts, and extras from filenames
- **Jellyfin-Compatible Structure** — Creates organized folder structures following Jellyfin naming conventions
- **Subtitle Handling** — Moves subtitle files alongside their videos; embeds VobSub (`.idx`/`.sub`) pairs into MKV containers
- **Audio Downmixing** — Optionally converts audio to stereo FLAC using FFmpeg while preserving video/subtitle streams
- **Extras Support** — Categorizes trailers, behind-the-scenes, interviews, and deleted scenes into subfolders
- **Concurrent Processing** — FFmpeg operations run concurrently (max 2 at a time) with progress tracking
- **Duplicate Handling** — Automatically versions duplicate filenames

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip
- FFmpeg installed and in PATH (only needed for `--downmix-audio`)

## Installation

See the [Installation Guide](INSTALL.md) for detailed instructions.

### Quick Setup

```bash
git clone https://github.com/ChrisLiva/jellyfin-renamer
cd jellyfin-renamer
uv venv && uv sync
```

## Usage

```bash
uv run python jellyfin-renamer.py <source> <target> --content-type {movies,tv} [--downmix-audio]
```

### Arguments

| Argument | Description |
|---|---|
| `source` | Directory containing media files |
| `target` | Directory for organized output |
| `--content-type` | **Required.** Either `movies` or `tv` |
| `--downmix-audio` | Copy files and convert audio to stereo FLAC (default: move files without processing) |

### Examples

```bash
# Organize movies (moves files)
uv run python jellyfin-renamer.py /path/to/media /path/to/jellyfin/movies --content-type movies

# Organize TV shows (moves files)
uv run python jellyfin-renamer.py /path/to/media /path/to/jellyfin/tv --content-type tv

# Organize movies with audio downmixing (copies files, then processes with FFmpeg)
uv run python jellyfin-renamer.py /path/to/media /path/to/jellyfin/movies --content-type movies --downmix-audio
```

> **Note:** Without `--downmix-audio`, files are **moved** (not copied) from source to target. With `--downmix-audio`, files are **copied** first, then processed in place with FFmpeg.

## Output Structure

### Movies

```
Target/
├── Movie Title (2023)/
│   ├── Movie Title (2023) - 1080p.mkv
│   ├── Movie Title (2023) - 1080p.en.srt
│   ├── trailers/
│   │   └── trailer.mp4
│   └── behind the scenes/
│       └── featurette.mp4
└── Another Movie (2022)/
    └── Another Movie (2022).mkv
```

### TV Shows

```
Target/
└── Show Name/
    ├── Season 01/
    │   ├── Show Name S01E01 - 1080p.mkv
    │   └── Show Name S01E02 - 720p.mkv
    └── Season 02/
        └── Show Name S02E01.mkv
```

## How It Works

1. **Scan** — Finds video files (`.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.iso`) in the source directory
2. **Parse** — Extracts metadata from filenames using `guessit`
3. **Group** — Groups by title/year (movies) or series/season (TV)
4. **Organize** — Creates Jellyfin folder structure and moves/copies files with proper naming
5. **Subtitles** — Moves matching subtitle files alongside videos; embeds VobSub pairs into MKVs
6. **FFmpeg** *(optional)* — Converts audio to stereo FLAC, preserving video and subtitle streams

## Architecture

```
jellyfin-renamer.py          # CLI entry point (argparse → organizer)
core/
├── parser.py                # Filename parsing via guessit (movies & TV)
├── organizer.py             # Scan, group, create dirs, move/copy files
├── file_processor.py        # Async FFmpeg wrapper (stereo FLAC conversion)
└── subtitle_processor.py    # Subtitle file matching, copying, VobSub embedding
```

## Testing

```bash
# Full test pipeline (creates test videos, runs pytest, cleans up)
uv run python test/run_tests.py

# Unit tests only (no FFmpeg required)
uv run python -m pytest test/test_renamer.py -v

# Single test
uv run python -m pytest test/test_renamer.py -v -k "test_name"
```

## Dependencies

- [guessit](https://github.com/guessit-io/guessit) — Media filename parsing
- [tqdm](https://github.com/tqdm/tqdm) — Progress bars
- [pytest](https://docs.pytest.org/) / [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) — Testing (dev)
