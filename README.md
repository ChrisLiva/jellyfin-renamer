# Jellyfin Renamer

A Python CLI tool to organize and rename movie and TV show files for Jellyfin. Parses media metadata from filenames using `guessit`, creates Jellyfin-compatible folder structures, and optionally converts audio to stereo FLAC via FFmpeg.

Follows Jellyfin naming conventions:
- https://jellyfin.org/docs/general/server/media/movies
- https://jellyfin.org/docs/general/server/media/shows

## Features

- **Smart parsing**: Extracts title, year, season/episode, resolution, and extras from filenames
- **Jellyfin-compatible structure**: `Movies/Title (Year)/` and `Shows/Series/Season XX/`
- **Extras support**: Auto-categorizes trailers, behind-the-scenes, interviews, etc.
- **Dry run**: Preview all changes before touching any files
- **Audio processing**: Optional stereo FLAC conversion via FFmpeg (concurrent, max 2 at a time)
- **Duplicate handling**: Auto-versions duplicate filenames
- **Mixed content**: Auto-detects and separates movies and TV shows in one pass

## Prerequisites

- Python 3.13+
- `uv` package manager (recommended)
- FFmpeg in PATH (only required for `--downmix-audio`)

## Installation

```bash
git clone https://github.com/ChrisLiva/jellyfin-renamer
cd jellyfin-renamer
uv venv && uv sync
```

## Usage

```bash
uv run jellyfin-renamer <source> <target> [options]
```

### Options

| Flag | Description |
|------|-------------|
| `--content-type {movies,tv,auto}` | Content type to process (default: `auto`) |
| `--dry-run` | Preview changes without moving or copying any files |
| `--downmix-audio` | Convert audio to stereo FLAC via FFmpeg |

### Always dry-run first

Use `--dry-run` to see exactly what the tool will do before it touches your files:

```bash
uv run jellyfin-renamer /path/to/media /path/to/jellyfin --dry-run
```

This prints a grouped tree of all planned moves without writing anything. Once the output looks right, run without `--dry-run` to apply.

### Examples

```bash
# Preview (safe — no files are moved)
uv run jellyfin-renamer /media /jellyfin --dry-run
uv run jellyfin-renamer /media /jellyfin --dry-run --content-type movies

# Apply
uv run jellyfin-renamer /media /jellyfin
uv run jellyfin-renamer /movies /jellyfin --content-type movies
uv run jellyfin-renamer /tv /jellyfin --content-type tv
uv run jellyfin-renamer /media /jellyfin --downmix-audio
```

## Output Structure

### Movies

```
Target/Movies/
├── Movie Title (2023)/
│   ├── Movie Title (2023) - 1080p.mp4
│   ├── trailers/
│   │   └── Movie Title (2023) - Trailer.mp4
│   └── behind the scenes/
│       └── Movie Title (2023) - Featurette.mp4
└── Another Movie (2022)/
    └── Another Movie (2022) - 720p.mp4
```

### TV Shows

```
Target/Shows/
└── Show Name/
    ├── Season 01/
    │   ├── Show Name - S01E01 - 1080p.mp4
    │   └── Show Name - S01E02 - 720p.mp4
    └── Season 02/
        └── Show Name - S02E01 - 4K.mp4
```

## Supported Formats

`.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.iso`

## Testing

```bash
# Full test suite (creates test videos, runs pytest, cleans up)
uv run python test/run_tests.py

# Unit tests only (no FFmpeg required)
uv run python -m pytest test/test_renamer.py -v
```

## Troubleshooting

- **FFmpeg not found**: Install FFmpeg and ensure it's in your PATH (only needed for `--downmix-audio`)
- **Permission errors**: Check read permissions on source and write permissions on target
- **Unexpected output**: Run with `--dry-run` first to inspect how filenames are parsed
