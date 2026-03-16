# Design: `--dry-run` Option

## Summary

Add a `--dry-run` flag that shows what file operations would occur without touching the filesystem. Output is a grouped tree view printed to stdout with no progress bars.

## CLI Interface

```
uv run python jellyfin-renamer.py <source> <target> --dry-run [--content-type {movies,tv,auto}] [--downmix-audio]
```

- `--dry-run` is combinable with all existing flags.
- When active, zero filesystem side effects occur: no directories created, no files moved/copied, no FFmpeg invoked.

## Approach: Pure Prepare Functions + Renderer

### Refactor `prepare_*` functions to be pure

Remove all `os.makedirs()` and `os.path.exists()` calls from `prepare_file_operations()` (movie_organizer.py) and `prepare_tv_operations()` (tv_organizer.py).

- Directory creation moves into the organizer functions, after prepare but before execute.
- Duplicate target path detection switches from `os.path.exists()` to an in-memory set of seen paths, applying the counter logic without disk access.

The prepare functions become: data in, operation list out.

### New module: `core/dry_run.py`

A renderer function that takes operation lists and `downmix_audio` flag, prints a grouped tree to stdout.

**Movie output format:**
```
Inception (2010)/
  Inception (2010).mkv  <-  /src/inception.mkv  [MOVE]
  Inception (2010) - 1080p.mkv  <-  /src/inception.1080p.mkv  [COPY + FFMPEG]
  Trailers/
    inception-trailer.mkv  <-  /src/inception-trailer.mkv  [MOVE]
```

**TV output format:**
```
Breaking Bad (2008)/
  Season 01/
    Breaking Bad S01E01.mkv  <-  /src/bb.s01e01.mkv  [MOVE]
    Breaking Bad S01E02.mkv  <-  /src/bb.s01e02.mkv  [MOVE]
  Season 02/
    Breaking Bad S02E01.mkv  <-  /src/bb.s02e01.mkv  [COPY + FFMPEG]
```

**Operation labels:**
- `[MOVE]` — default when `--downmix-audio` is off
- `[COPY + FFMPEG]` — main files when `--downmix-audio` is on
- `[MOVE]` — extras always (never FFmpeg-processed)

**Summary line** at the end:
```
3 files would be moved, 2 files would be copied + processed with FFmpeg
```

### Organizer flow

```
scan -> group -> prepare (pure) -> dry_run ? render_dry_run() : create_dirs + execute
```

When `dry_run=True`: call renderer, return immediately.
When `dry_run=False`: create directories, execute file operations as today.

Both `organize_movies()` and `organize_tv_shows()` gain a `dry_run=False` parameter. `organize_mixed_content()` passes it through and skips top-level `Movies/`/`Shows/` directory creation when dry-running.

## Testing

Tests in `test/test_renamer.py`:

- Verify `--dry-run` produces expected stdout for movie files
- Verify `--dry-run` produces expected stdout for TV files
- Verify `--dry-run` with `--downmix-audio` shows `[COPY + FFMPEG]` labels
- Verify zero filesystem side effects (target dir remains empty)
- Verify refactored `prepare_*` functions produce correct operation lists without disk access

No FFmpeg required for any dry-run tests.
