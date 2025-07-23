# Jellyfin Renamer

A Python tool to organize and rename movie and TV show files for Jellyfin media server. This tool automatically parses media information from filenames, creates organized folder structures, and processes audio to FLAC stereo format using FFmpeg.

Follows Jellyfin recommendations on media organization:
https://jellyfin.org/docs/general/server/media/movies
https://jellyfin.org/docs/general/server/media/shows

## Features

- **Command-Line Interface**: Direct CLI access for automation and scripting
- **Smart Media Parsing**: Uses `guessit` library to extract movie/TV titles, years, resolution, and parts from filenames
- **Jellyfin-Compatible Structure**: Creates organized folder structures that work well with Jellyfin
- **Advanced Audio Processing**: Optionally converts audio to FLAC stereo with EBU R128 loudness normalization optimized for outdoor viewing
- **Extras Support**: Automatically categorizes trailers, behind-the-scenes content, and other extras
- **Progress Tracking**: Shows detailed progress bars for all operations with real-time updates
- **Concurrent Processing**: Processes multiple files with FFmpeg concurrently (max 2 at a time)
- **Duplicate Handling**: Automatically handles duplicate filenames and versions
- **Mixed Content Support**: Auto-detects and organizes both movies and TV shows in the same run

## Prerequisites

- Python 3.13 or higher
- FFmpeg installed and available in your PATH
- UV package manager (recommended) or pip

## Project Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd jellyfin-renamer
```

### 2. Install Dependencies

#### Using UV (Recommended)

1. **Install UV** (if not already installed):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # or
   brew install uv
   ```

2. **Create virtual environment and install dependencies**:

   ```bash
   uv venv
   uv sync
   ```

3. **Install development dependencies** (for testing):

   ```bash
   uv sync --group dev
   ```

#### Using pip (Alternative)

1. **Create a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:

   ```bash
   pip install -e .
   pip install -e ".[test]"
   ```

### 3. Verify Installation

```bash
# Check if the main script runs
python jellyfin-renamer.py --help

# Check if pytest is available
python -m pytest --version
```

## Running Tests

### Automated Test Suite

The project includes a comprehensive test suite that creates test videos, runs tests, and cleans up automatically:

```bash
# Using UV
uv run python test/run_tests.py

# Using pip/venv
python test/run_tests.py
```

### Manual Test Execution

If you prefer to run tests manually:

```bash
# Create test videos
python test/create_test_videos.py

# Run pytest with verbose output
python -m pytest test/test_renamer.py -v

# Clean up test videos
python test/cleanup_test_videos.py
```

### Test Coverage

The test suite covers:

- **Movie parsing**: Various filename patterns and edge cases
- **TV show parsing**: Season/episode detection and naming
- **Content type detection**: Auto-detection of movies vs TV shows
- **File organization**: Directory structure creation and file copying
- **Extension handling**: Complex filenames with multiple extensions
- **Edge cases**: Special characters, numbers in titles, etc.

## Usage

### Command-Line Interface

```bash
python jellyfin-renamer.py <source_directory> <target_directory> [options]
```

#### Arguments

- `source_directory`: Path to the directory containing your media files
- `target_directory`: Path where you want the organized media to be saved

#### Options

- `--content-type {movies,tv,auto}`: Type of content to process (default: auto)
- `--downmix-audio`: Optional flag to process audio with FFmpeg (default: False)
  - Converts audio to stereo FLAC format
  - Applies EBU R128 loudness normalization with settings optimized for outdoor viewing:
    - Integrated loudness: -14 LUFS
    - True peak: -1.5 dBTP
    - Loudness range: 9 LU

#### Examples

```bash
# Using UV (recommended)
uv run python jellyfin-renamer.py /path/to/media /path/to/jellyfin/media
uv run python jellyfin-renamer.py /path/to/media /path/to/jellyfin/media --downmix-audio
uv run python jellyfin-renamer.py /path/to/movies /path/to/jellyfin/movies --content-type movies
uv run python jellyfin-renamer.py /path/to/tv /path/to/jellyfin/tv --content-type tv

# Using pip/venv
python jellyfin-renamer.py /path/to/media /path/to/jellyfin/media
python jellyfin-renamer.py /path/to/media /path/to/jellyfin/media --downmix-audio
```

## How It Works

1. **Scanning**: The tool scans the source directory for video files (mp4, mkv, avi, mov, wmv, iso)
2. **Content Detection**: Auto-detects whether files are movies or TV shows based on filename patterns
3. **Parsing**: Uses `guessit` to extract media information from filenames
4. **Grouping**: Groups files by title and year (movies) or series and season (TV shows)
5. **Organizing**: Creates folder structures like `Movie Title (2023)/` or `Show Name/Season 01/`
6. **Copying**: Copies files to their new locations with proper naming
7. **Processing**: Optionally processes audio using FFmpeg (when `--downmix-audio` is used):
   - Converts to stereo FLAC format
   - Applies EBU R128 loudness normalization for consistent volume levels
   - Preserves video and subtitle streams without re-encoding
8. **Extras**: Organizes trailers, behind-the-scenes content, etc. into subfolders

## Supported Video Formats

- MP4 (.mp4)
- MKV (.mkv)
- AVI (.avi)
- MOV (.mov)
- WMV (.wmv)
- ISO (.iso)

## Output Structure

### Movies

```
Target Directory/Movies/
├── Movie Title (2023)/
│   ├── Movie Title (2023) - 1080p.mp4
│   ├── Movie Title (2023) - 4K.mp4
│   ├── trailers/
│   │   └── Movie Title (2023) - Trailer.mp4
│   └── behind the scenes/
│       └── Movie Title (2023) - Featurette.mp4
└── Another Movie (2022)/
    └── Another Movie (2022) - 720p.mp4
```

### TV Shows

```
Target Directory/Shows/
├── Show Name/
│   ├── Season 01/
│   │   ├── Show Name - S01E01 - Episode Title - 1080p.mp4
│   │   └── Show Name - S01E02 - Episode Title - 720p.mp4
│   └── Season 02/
│       └── Show Name - S02E01 - Episode Title - 4K.mp4
```

## Validation and Quality Assurance

### 1. Pre-Processing Validation

Before running the tool on your entire media library:

```bash
# Test with a small subset of files
mkdir test_source test_target
cp /path/to/your/media/*.mkv test_source/  # Copy a few files
python jellyfin-renamer.py test_source test_target
```

### 2. Output Validation

After processing, verify:

- **File Structure**: Check that folders are created correctly
- **File Naming**: Ensure files are named consistently
- **Content Preservation**: Verify no data loss during processing
- **Audio Quality**: If using `--downmix-audio`, test audio output

### 3. Jellyfin Integration Testing

1. **Add to Jellyfin Library**: Point Jellyfin to your organized media directory
2. **Scan Library**: Trigger a library scan in Jellyfin
3. **Verify Metadata**: Check that Jellyfin correctly identifies movies/shows
4. **Test Playback**: Ensure files play correctly in Jellyfin

### 4. Performance Monitoring

Monitor these metrics during processing:

- **Processing Speed**: Files per minute
- **Disk Usage**: Ensure sufficient space for output
- **Audio Processing**: FFmpeg conversion time (if using `--downmix-audio`)
- **Error Rate**: Check for failed operations

## Dependencies

### Core Dependencies

- **guessit>=3.8.0**: For parsing media information from filenames
- **tqdm>=4.67.1**: For progress bars during processing

### Development Dependencies

- **pytest>=8.4.1**: Testing framework
- **pytest-asyncio>=1.1.0**: Async test support

## Audio Processing Details

When using the `--downmix-audio` flag, the tool applies advanced audio processing:

- **Format**: Converts audio to FLAC stereo for better compatibility and lossless quality
- **Loudness Normalization**: Uses EBU R128 standard with FFmpeg's `loudnorm` filter
  - **Integrated Loudness**: -14 LUFS (louder than broadcast standard for outdoor viewing)
  - **True Peak**: -1.5 dBTP (prevents clipping)
  - **Loudness Range**: 9 LU (maintains dynamic range)
- **Stream Preservation**: Video and subtitle streams are copied without re-encoding
- **Concurrent Processing**: FFmpeg operations run concurrently (max 2 at a time) to optimize performance

## Troubleshooting

### Common Issues

1. **FFmpeg not found**: Ensure FFmpeg is installed and in your PATH
2. **Permission errors**: Check file permissions on source and target directories
3. **Disk space**: Ensure sufficient space for output files
4. **Unsupported formats**: Check that your video files are in supported formats

### Debug Mode

For detailed logging, you can modify the script to add debug output or run with Python's verbose mode:

```bash
python -v jellyfin-renamer.py source target
```

## Notes

- Progress bars show the status of all operations
- Duplicate filenames are automatically handled with version numbers
- The tool preserves original files and creates copies in the target directory
- Audio processing settings are optimized for outdoor/projector viewing where ambient noise is higher
- Mixed content processing automatically separates movies and TV shows into different directories
