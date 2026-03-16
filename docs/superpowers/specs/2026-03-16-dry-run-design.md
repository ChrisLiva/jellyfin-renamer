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

Remove all `os.makedirs()` and `os.path.exists()` calls from:

- `prepare_file_operations()` in `movie_organizer.py`
- `prepare_tv_operations()` in `tv_organizer.py`
- `handle_duplicate_files()` in `tv_organizer.py` (also uses `os.path.exists()`)

Changes:

- Directory creation moves into the organizer functions, after prepare but before execute. The redundant directory creation pass already in the organizer loops can serve this purpose — remove the duplicated `os.makedirs` from prepare.
- Duplicate target path detection switches from `os.path.exists()` to an in-memory set of seen paths, applying the counter logic without disk access.
- All tqdm progress bars are skipped when `dry_run=True` — the branch happens right after grouping, before any tqdm-wrapped loops for directory creation or file operations.

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

**Auto mode (`--content-type auto`) output:**

When auto-detecting, movies and TV shows appear under separate headings:
```
=== Movies ===

Inception (2010)/
  Inception (2010).mkv  <-  /src/inception.mkv  [MOVE]

=== TV Shows ===

Breaking Bad (2008)/
  Season 01/
    Breaking Bad S01E01.mkv  <-  /src/bb.s01e01.mkv  [MOVE]
```

If only one type is detected, only that heading appears. The summary line at the end covers all files across both types.

**Edge case — no files found:**

If the source directory contains no recognized video files, print:
```
No video files found in <source_dir>
```

### Organizer flow

```
scan -> group -> prepare (pure) -> dry_run ? render_dry_run() : create_dirs + execute
```

When `dry_run=True`: call renderer, return immediately.
When `dry_run=False`: create directories, execute file operations as today.

Both `organize_movies()` and `organize_tv_shows()` gain a `dry_run=False` parameter. `organize_mixed_content()` passes it through and skips top-level `Movies/`/`Shows/` directory creation when dry-running.

## Testing

Tests in `test/test_renamer.py`, using `tmp_path` fixtures and `capsys` for stdout capture:

- **Dry-run movie output**: Create temp source with video files, run `organize_movies(dry_run=True)`, capture stdout, assert grouped tree format matches expected output.
- **Dry-run TV output**: Same approach for `organize_tv_shows(dry_run=True)`.
- **Dry-run auto mode**: Verify combined output with `=== Movies ===` / `=== TV Shows ===` headings.
- **`--downmix-audio` labels**: Verify `[COPY + FFMPEG]` for main files vs `[MOVE]` for extras.
- **Zero side effects**: Assert target directory is empty after dry-run (no dirs or files created).
- **No files found**: Verify "No video files found" message for empty source dir.
- **Pure prepare functions**: Call `prepare_file_operations()` and `prepare_tv_operations()` with test data, verify correct operation lists returned. "Without disk access" verified by using a non-existent target path — the function should not fail since it no longer touches the filesystem.
- **In-memory duplicate detection**: Verify that when multiple files would map to the same target name, the counter suffix is applied correctly.

No FFmpeg required for any dry-run tests.
