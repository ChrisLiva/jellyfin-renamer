# Jellyfin Renamer - Installation Guide

This guide will help you install the jellyfin-renamer tool on your system so you can use it from anywhere via the command line.

## Prerequisites

Before running the install script, make sure you have:

1. **Python 3.13 or higher** installed on your system
2. **Git** (to clone the repository)
3. **Administrator/sudo access** (for installing dependencies)

## Installation Steps

### 1. Clone the Repository

First, clone the jellyfin-renamer repository to your local machine:

```bash
git clone https://github.com/ChrisLiva/jellyfin-renamer
cd jellyfin-renamer
```

### 2. Run the Install Script

#### For macOS and Linux:

```bash
chmod +x install.sh
./install.sh
```

#### For Windows:

```cmd
install.bat
```

### 3. What the Install Script Does

The install script will automatically:

1. **Check Python version** - Ensures you have Python 3.13+
2. **Install UV package manager** - If not already installed
3. **Install FFmpeg** - Required for audio processing (optional but recommended)
4. **Install project dependencies** - All required Python packages
5. **Create a system-wide executable** - Makes `jellyfin-renamer` available from anywhere
6. **Add to PATH** - Automatically adds the tool to your system PATH
7. **Test the installation** - Verifies everything works correctly

### 4. Post-Installation

After running the install script:

1. **Restart your terminal/command prompt** (or run `source ~/.bashrc` on Linux/macOS)
2. **Test the installation** by running:
   ```bash
   jellyfin-renamer --help
   ```

## Usage

Once installed, you can use the tool from anywhere:

```bash
# Basic usage
jellyfin-renamer /path/to/media /path/to/jellyfin/media

# With audio processing
jellyfin-renamer /path/to/media /path/to/jellyfin/media --downmix-audio

# Process only movies
jellyfin-renamer /path/to/movies /path/to/jellyfin/movies --content-type movies

# Process only TV shows
jellyfin-renamer /path/to/tv /path/to/jellyfin/tv --content-type tv

# Get help
jellyfin-renamer --help
```

## Troubleshooting

### Common Issues

1. **"jellyfin-renamer command not found"**

   - Restart your terminal/command prompt
   - On Linux/macOS, run: `source ~/.bashrc` or `source ~/.zshrc`

2. **Python version error**

   - Install Python 3.13 or higher from https://python.org

3. **FFmpeg not found**

   - The tool will work without FFmpeg, but audio processing won't be available
   - Install FFmpeg manually: https://ffmpeg.org/download.html

4. **Permission errors**
   - Run the install script with appropriate permissions
   - On Linux/macOS, you might need to use `sudo` for some operations

### Manual Installation

If the automatic install script doesn't work, you can install manually:

1. **Install Python 3.13+**
2. **Install UV**: `pip install uv`
3. **Install FFmpeg** (optional)
4. **Install dependencies**: `uv sync`
5. **Run directly**: `uv run python jellyfin-renamer.py --help`

## Uninstalling

To remove the jellyfin-renamer tool:

1. **Remove the executable**:

   - Linux/macOS: `rm ~/.local/bin/jellyfin-renamer`
   - Windows: `del %USERPROFILE%\.local\bin\jellyfin-renamer.bat`

2. **Remove from PATH** (if added automatically):

   - Edit your shell profile file (`.bashrc`, `.zshrc`, etc.)
   - Remove the line that adds `~/.local/bin` to PATH

3. **Delete the project directory** (optional):
   - Remove the entire jellyfin-renamer folder

## Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Ensure all prerequisites are met
3. Try running the tool with verbose output for debugging
4. Check the main README.md for detailed usage information

## Features

The installed tool includes all features from the original jellyfin-renamer:

- ✅ Smart media parsing and organization
- ✅ Jellyfin-compatible folder structures
- ✅ Audio processing with FFmpeg (optional)
- ✅ Progress tracking and concurrent processing
- ✅ Support for movies, TV shows, and mixed content
- ✅ Extras and special features handling
- ✅ Duplicate file handling
- ✅ Cross-platform compatibility
