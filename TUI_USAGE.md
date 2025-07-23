# Jellyfin Renamer TUI Usage Guide

The Jellyfin Renamer now includes a beautiful Terminal User Interface (TUI) that makes organizing your media files intuitive and interactive.

## Quick Start

### Launch TUI Mode

You can start the TUI in several ways:

```bash
# Method 1: Using the main script with --tui flag
python jellyfin-renamer.py --tui

# Method 2: Using the dedicated TUI launcher
python run_tui.py

# Method 3: Using UV (if you have it)
uv run python run_tui.py
```

### First Time Setup

When you first launch the TUI, you'll see the main configuration screen with several sections:

1. **Configuration Panel** - Set up your directories and options
2. **File Selection Panel** - Choose which files to process
3. **Action Buttons** - Start processing, preview, or exit

## Interface Overview

### Main Screen Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                   🎬 Jellyfin Media Renamer                     │
│                Organize your media files beautifully           │
├─────────────────────────────────────────────────────────────────┤
│ Configuration                                                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Source Directory: [Browse] [/path/to/source]               │ │
│ │ Target Directory: [Browse] [/path/to/target]               │ │
│ │ Content Type: ○ Auto-detect ○ Movies ○ TV Shows           │ │
│ │ ☐ Enable FFmpeg audio processing                          │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ File Selection                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ [Select All] [Clear All] [Refresh]                         │ │
│ │ ☑ Movie1.mkv (1.2 GB)                                     │ │
│ │ ☑ Movie2.mp4 (800 MB)                                     │ │
│ │ ☐ TVShow.S01E01.mkv (600 MB)                              │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ✅ Ready to process 2 files                                    │
│                                                                 │
│         [👀 Preview] [🚀 Start Processing] [❌ Exit]           │
└─────────────────────────────────────────────────────────────────┘
```

### Keyboard Shortcuts

#### Global Shortcuts

- **Q** or **Ctrl+C** - Quit application
- **F1** - Show help
- **ESC** - Go back/close modal
- **Tab** - Navigate between fields

#### Main Screen Shortcuts

- **F2** - Browse source directory
- **F3** - Browse target directory
- **F5** - Start processing
- **Enter** - Activate focused element

#### File Browser Shortcuts

- **F5** - Refresh file list
- **Ctrl+A** - Select all video files
- **Ctrl+D** - Deselect all files
- **ESC** - Back to main screen

## Step-by-Step Workflow

### 1. Configure Directories

#### Source Directory

1. Click the "Browse" button next to "Source Directory" or press **F2**
2. Navigate through the directory tree
3. Select the folder containing your media files
4. The directory will be validated automatically

#### Target Directory

1. Click the "Browse" button next to "Target Directory" or press **F3**
2. Choose where you want the organized files to go
3. This should be different from your source directory

### 2. Choose Content Type

Select how you want the files to be processed:

- **Auto-detect (recommended)** - Automatically detects movies vs TV shows
- **Movies only** - Treats all files as movies
- **TV shows only** - Treats all files as TV episodes

### 3. Configure Audio Processing

Check the "Enable FFmpeg audio processing" box if you want to:

- Convert audio to stereo FLAC format
- Apply EBU R128 loudness normalization
- Optimize for outdoor/projector viewing

**Note:** Requires FFmpeg to be installed on your system.

### 4. Select Files

The file selector will automatically scan your source directory and show all video files:

#### File Selection Options

- **Individual Selection** - Click on files to toggle selection
- **Select All** - Click "Select All" to choose all video files
- **Clear All** - Click "Clear All" to deselect everything
- **Refresh** - Click "Refresh" to rescan the directory

#### File Information

Each file shows:

- Filename
- File size
- Selection status (☑ selected, ☐ unselected)

### 5. Preview Processing

Before starting, click **"👀 Preview"** to see:

- Summary of your configuration
- How many files will be processed
- Expected output structure
- Naming conventions that will be used

### 6. Start Processing

When you're ready:

1. Click **"🚀 Start Processing"**
2. You'll be taken to the progress screen
3. Watch real-time progress with:
   - Overall progress bar
   - Current file being processed
   - Processing speed and ETA
   - Live log of operations

#### Progress Screen Features

- **Pause/Resume** - Control processing
- **Cancel** - Stop processing at any time
- **Real-time logs** - See what's happening
- **Statistics** - Files processed, speed, time remaining

### 7. Completion

When processing finishes:

- View processing statistics
- Click **"📂 View Organized Files"** to open the target directory
- Click **"🏠 Back to Main"** to process more files

## Advanced Features

### Directory Browsing

The built-in directory browser includes:

- **Tree Navigation** - Expand/collapse folders
- **Breadcrumb Navigation** - See current path
- **Search** - Filter files and folders
- **Quick Actions** - Up directory, refresh, select all

### File Type Detection

The TUI automatically identifies:

- **Video Files** - MP4, MKV, AVI, MOV, WMV, ISO
- **File Sizes** - Human-readable format (MB, GB)
- **Invalid Files** - Files that can't be processed

### Error Handling

The TUI gracefully handles:

- **Permission Errors** - Shows clear error messages
- **Invalid Directories** - Real-time validation
- **Processing Errors** - Detailed error reporting
- **Cancellation** - Safe operation stopping

## Output Structure

### Movies

```
Target Directory/Movies/
├── Movie Title (2023)/
│   ├── Movie Title (2023) - 1080p.mkv
│   └── Movie Title (2023) - 4K.mp4
└── Another Movie (2022)/
    └── Another Movie (2022) - 720p.mp4
```

### TV Shows

```
Target Directory/Shows/
├── Show Name/
│   ├── Season 01/
│   │   ├── Show Name - S01E01 - Episode Title - 1080p.mkv
│   │   └── Show Name - S01E02 - Episode Title - 720p.mkv
│   └── Season 02/
│       └── Show Name - S02E01 - Episode Title - 4K.mkv
```

### Mixed Content (Auto-detect)

```
Target Directory/
├── Movies/
│   └── Movie Title (2023)/
│       └── Movie Title (2023) - 1080p.mkv
└── Shows/
    └── Show Name/
        └── Season 01/
            └── Show Name - S01E01 - Episode Title.mkv
```

## Tips and Best Practices

### Before Processing

1. **Backup your files** - Always have a backup of original files
2. **Test with a few files** - Try a small batch first
3. **Check directory permissions** - Ensure read/write access
4. **Verify FFmpeg installation** - If using audio processing

### During Processing

1. **Don't close the terminal** - Let processing complete
2. **Monitor the logs** - Watch for any errors
3. **Use pause if needed** - You can pause and resume processing

### After Processing

1. **Verify results** - Check that files were organized correctly
2. **Test in Jellyfin** - Import the organized library
3. **Clean up source** - Remove or archive original files

## Troubleshooting

### Common Issues

#### "TUI dependencies not available"

```bash
# Install required packages
pip install textual textual-dev
# or with UV
uv add textual textual-dev
```

#### "Permission denied"

- Check that you have read access to source directory
- Check that you have write access to target directory
- Try running with elevated permissions if necessary

#### "FFmpeg not found"

- Install FFmpeg on your system
- Ensure FFmpeg is in your PATH
- Disable audio processing if FFmpeg is not needed

#### "No files selected"

- Ensure your source directory contains video files
- Check that files have supported extensions (.mp4, .mkv, etc.)
- Try refreshing the file list

### Getting Help

- Press **F1** in the TUI for keyboard shortcuts
- Check the main README.md for general usage
- Review error messages in the progress logs
- Ensure all dependencies are installed

## CLI Mode Compatibility

The TUI doesn't replace the original CLI mode. You can still use:

```bash
# CLI mode (original functionality)
python jellyfin-renamer.py /source/path /target/path --content-type auto --downmix-audio

# TUI mode (new interactive interface)
python jellyfin-renamer.py --tui
```

Both modes use the same core processing engine, so results will be identical.

## Performance

The TUI is designed to be efficient:

- **Async Processing** - Non-blocking file operations
- **Real-time Updates** - Live progress without performance impact
- **Memory Efficient** - Minimal memory usage for large file sets
- **Responsive UI** - Smooth interactions even during processing

Enjoy organizing your media files with the beautiful new TUI! 🎬✨
