# AGENTS.md - Agentic Coding Guidelines

This file provides guidance for agentic coding agents working in this repository.

## Project Overview

Jellyfin Renamer is a Python CLI tool that organizes and renames movie/TV show files for the Jellyfin media server. It parses media metadata from filenames using `guessit`, creates Jellyfin-compatible folder structures, and optionally converts audio to stereo FLAC via FFmpeg.

## Commands

### Running the Tool

```bash
uv run python jellyfin-renamer.py <source> <target> --content-type {movies,tv} [--downmix-audio]
```

### Testing

```bash
# Full test pipeline (creates test videos, runs pytest, cleans up)
uv run python test/run_tests.py

# Unit tests only (no FFmpeg required)
uv run python -m pytest test/test_renamer.py -v

# Single test (run specific test by name)
uv run python -m pytest test/test_renamer.py -v -k "test_name"

# Single test with async
uv run python -m pytest test/test_renamer.py -v -k "test_name" --tb=short
```

### Development Setup

```bash
# Create virtual environment and install dependencies
uv venv && uv sync
```

## Code Style Guidelines

### General

- Python 3.13+ required
- Use `uv` as the package manager (not pip/poetry)
- Async-first: use `asyncio` for concurrent operations
- Progress tracking with `tqdm`

### Imports

Order imports in each file:
1. Standard library (`os`, `asyncio`, `re`, `subprocess`, etc.)
2. Third-party packages (`guessit`, `tqdm`, `pytest`)
3. Local relative imports (`from .module import ...`)

```python
# Example import order
import os
import asyncio
from collections import defaultdict

from tqdm import tqdm

from .parser import parse_media_info
```

### Naming Conventions

- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE` at module level
- Private functions: prefix with `_`

```python
# Functions
def parse_media_info(filename, content_type):
def scan_source_directory(source_dir):

# Classes  
class MediaOrganizer:

# Constants
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".iso"}

# Private
def _helper_function():
```

### Type Hints

Python 3.13+ is used. Add type hints where beneficial, especially for:
- Function parameters and return types
- Complex data structures (dicts, lists)

```python
def parse_media_info(filename: str, content_type: str) -> dict:
def prepare_movie_operations(movie_groups: dict, target_dir: str) -> tuple[list, list]:
```

### Error Handling

- Use try/except blocks for operations that may fail
- Handle specific exceptions when possible
- Return `False` or `None` on failure rather than raising for expected errors
- Log errors appropriately (print to stderr or use pbar.write)

```python
try:
    result = process_file()
    return True
except subprocess.CalledProcessError as e:
    if pbar:
        pbar.write(f"Error: {e}")
    return False
```

### Async Patterns

- Use `asyncio.Semaphore` to limit concurrent operations (default: 2)
- Use `ThreadPoolExecutor` for blocking operations (FFmpeg)
- Always use `asyncio.run()` in the entry point

```python
semaphore = asyncio.Semaphore(2)

async def process_single_file(path):
    async with semaphore:
        await process_with_ffmpeg_async(path)
```

### Docstrings

Use triple quotes for docstrings. Keep them concise:

```python
def parse_media_info(filename, content_type):
    """Parse media details using guessit."""
    ...
```

### File Organization

- Entry point: `jellyfin-renamer.py` — CLI with argparse
- Core modules in `core/` directory
- Tests in `test/` directory
- Parser modules: extract metadata from filenames
- Organizer modules: orchestrate file operations

### Testing Conventions

- Use `pytest` as the test framework
- Use `@pytest.mark.parametrize` for test cases
- Use `@pytest.mark.asyncio` for async tests
- Use fixtures for setup/teardown
- Include edge case tests

```python
@pytest.mark.parametrize("filename,expected", [
    ("Movie.2020.1080p.mkv", "Movie"),
    ("Show.S01E01.720p.mkv", "Show"),
])
def test_parsing(filename, expected):
    result = parse_media_info(filename, "movies")
    assert result["title"] == expected

@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "source", Path(tmpdir) / "target"

@pytest.mark.asyncio
async def test_organization(temp_dirs):
    ...
```

### Constants

Define constants at module level. Group related constants:

```python
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".iso"}

CONTENT_TYPES = ["movies", "tv"]

EXTRA_TYPE_MAPPING = {
    "Trailer": "trailers",
    "BehindTheScenes": "behind the scenes",
}
```

### Progress Bars

Use `tqdm` for progress tracking:

```python
with tqdm(all_files, desc="Processing") as pbar:
    for item in pbar:
        process(item)
        pbar.set_description(f"Current: {item}")
```

### Code to Avoid

- Do not use `print()` for debugging (use pbar.write or logging)
- Do not commit secrets, keys, or credentials
- Do not make assumptions about FFmpeg availability without checking
- Do not use blocking I/O in async functions without executors

## Architecture

```
jellyfin-renamer.py      # Entry point, CLI argument parsing
core/
├── parser.py           # Unified parser for movies and TV shows
├── organizer.py        # Unified organizer for both content types
├── file_processor.py   # Async FFmpeg wrapper
└── common.py           # Shared utilities
```

## Key Patterns

1. **Unified Parser → Organizer Pipeline**: Single parser extracts metadata, single organizer handles file operations
2. **Explicit Content Type**: User must specify `--content-type movies` or `--content-type tv`
3. **Jellyfin Structure**: Output follows Jellyfin naming conventions
4. **FFmpeg Processing**: Optional audio downmix with concurrency limit of 2
