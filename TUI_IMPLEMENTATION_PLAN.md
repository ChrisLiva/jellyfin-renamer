# Jellyfin Renamer TUI Implementation Plan

## Overview

This document outlines the plan to implement a beautiful and modern Terminal User Interface (TUI) using Textual for the jellyfin-renamer application. The TUI will provide an interactive alternative to the current CLI while preserving all existing functionality.

The user should be able to navigate the entire TUI using keyboard arrow keys, spacebar for select, escape for "back", and enter for continue.

Textual Repo: https://github.com/Textualize/textual

## Goals

- Create a beautiful, modern TUI interface
- Preserve existing CLI functionality
- Provide intuitive file and directory selection
- Show real-time progress with beautiful progress bars
- Maintain excellent user experience
- Use reusable, modular components

## Current Application Analysis

### Core Functionality

- **File Organization**: Automatically organizes movies and TV shows
- **Content Detection**: Auto-detects content type (movies/TV shows)
- **FFmpeg Integration**: Optional audio processing with FFmpeg
- **Mixed Content**: Handles both movies and TV shows in same directory
- **Async Processing**: Non-blocking file operations

### Current Architecture

```
jellyfin-renamer/
├── jellyfin-renamer.py      # Main CLI entry point
├── core/
│   ├── common.py            # Shared utilities
│   ├── file_processor.py    # FFmpeg integration
│   ├── movie_organizer.py   # Movie file organization
│   ├── movie_parser.py      # Movie file parsing
│   ├── tv_organizer.py      # TV show organization
│   └── tv_parser.py         # TV show parsing
└── test/                    # Test files
```

## TUI Architecture

### 1. **File Structure**

```
jellyfin-renamer/
├── jellyfin-renamer.py      # Main entry point (CLI + TUI)
├── core/                    # Existing core functionality
├── tui/                     # New TUI components
│   ├── __init__.py
│   ├── app.py               # Main TUI application
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── main_screen.py   # Main configuration screen
│   │   ├── file_browser.py  # File/directory browser
│   │   └── progress_screen.py # Processing progress screen
│   ├── components/
│   │   ├── __init__.py
│   │   ├── directory_picker.py
│   │   ├── file_selector.py
│   │   ├── progress_panel.py
│   │   └── status_bar.py
│   └── utils/
│       ├── __init__.py
│       └── tui_helpers.py
└── test/
```

### 2. **Core Components**

#### **Main Application (`tui/app.py`)**

- Entry point for TUI mode
- Handles CLI vs TUI mode detection
- Manages screen transitions
- Coordinates between screens

#### **Main Screen (`tui/screens/main_screen.py`)**

- **Header**: Beautiful title with app branding
- **Configuration Panel**:
  - Source directory picker (with browse button)
  - Target directory picker (with browse button)
  - Content type selector (Movies/TV/Auto)
  - FFmpeg audio processing toggle
- **File Selection Panel**:
  - File tree browser for source directory
  - Multi-select capability
  - File count and size summary
- **Action Panel**:
  - Start processing button
  - Preview mode button
  - Clear selection button

#### **File Browser Screen (`tui/screens/file_browser.py`)**

- Tree view of source directory
- File type icons (video files highlighted)
- Multi-select with checkboxes
- Search/filter functionality
- File size and type information
- Breadcrumb navigation

#### **Progress Screen (`tui/screens/progress_screen.py`)**

- **Overall Progress**: Main progress bar for entire operation
- **File Progress**: Individual file progress bars
- **Status Information**:
  - Current file being processed
  - Files completed/total
  - Processing speed
  - Estimated time remaining
- **Log Panel**: Real-time processing logs
- **Action Buttons**: Pause/Resume/Cancel

#### **Reusable Components**

##### **DirectoryPicker (`tui/components/directory_picker.py`)**

- Beautiful directory selection with validation
- Browse button integration
- Path validation and error handling
- Auto-completion for common paths

##### **FileSelector (`tui/components/file_selector.py`)**

- Multi-select file browser with search
- File type filtering
- Size and date information
- Checkbox selection interface

##### **ProgressPanel (`tui/components/progress_panel.py`)**

- Animated progress bars with status
- Multiple progress levels (overall + per-file)
- Real-time speed and ETA display
- Pause/resume functionality

##### **StatusBar (`tui/components/status_bar.py`)**

- Real-time status information
- File count and size summaries
- Processing statistics
- Error and warning indicators

## User Experience Flow

### 1. **Startup**

- App detects CLI vs TUI mode based on arguments
- CLI mode: Existing functionality
- TUI mode: Launch beautiful interface

### 2. **Configuration Screen**

- User selects source directory
- User selects target directory
- User chooses content type (Movies/TV/Auto)
- User toggles FFmpeg audio processing
- Real-time validation and feedback

### 3. **File Selection**

- User browses source directory
- Multi-select files to process
- Preview of file organization
- File count and size summary
- Search and filter capabilities

### 4. **Processing**

- Beautiful progress interface
- Real-time file processing updates
- Individual file progress bars
- Processing logs and status
- Pause/resume/cancel options

### 5. **Completion**

- Summary screen with results
- Success/error statistics
- Option to view organized files
- Return to main screen or exit

## Technical Implementation

### 1. **Dependencies**

Add to `pyproject.toml`:

```toml
dependencies = [
    "guessit>=3.8.0",
    "tqdm>=4.67.1",
    "textual>=0.54.0",        # Main TUI framework
    "textual-dev>=0.54.0",    # Development tools
]
```

### 2. **Async Integration**

- Convert existing async file processing to work with Textual's event loop
- Real-time progress updates using Textual's reactive system
- Non-blocking UI updates during file operations
- Proper error handling and user feedback

### 3. **Theme & Styling**

- Modern, clean design with consistent color scheme
- Smooth animations and transitions
- Responsive layout that adapts to terminal size
- Beautiful icons and visual indicators
- Dark/light theme support

### 4. **CLI Compatibility**

- All current command-line arguments work
- TUI mode activated with `--tui` flag
- Fallback to CLI mode if TUI dependencies not available
- Preserve existing functionality completely

## Advanced Features

### 1. **Smart Defaults**

- Remember last used directories
- Auto-detect content type based on file patterns
- Intelligent file selection based on common patterns
- Smart path suggestions

### 2. **Real-time Feedback**

- Live file scanning with progress
- Instant content type detection display
- Real-time file size calculations
- Immediate validation feedback

### 3. **Error Handling**

- Beautiful error dialogs
- Graceful handling of permission issues
- Clear error messages with actionable suggestions
- Recovery options for failed operations

### 4. **Accessibility**

- Keyboard navigation support
- Screen reader compatibility
- High contrast mode support
- Configurable key bindings

## Development Phases

### **Phase 1: Core TUI Structure**

- [ ] Set up Textual dependencies
- [ ] Create basic TUI application structure
- [ ] Implement main screen layout
- [ ] Add CLI/TUI mode detection
- [ ] Basic navigation between screens

### **Phase 2: Configuration Components**

- [ ] Implement DirectoryPicker component
- [ ] Add content type selector
- [ ] Create FFmpeg toggle component
- [ ] Add validation and error handling
- [ ] Implement configuration persistence

### **Phase 3: File Browser**

- [ ] Create FileSelector component
- [ ] Implement tree view for directories
- [ ] Add multi-select functionality
- [ ] Create search and filter features
- [ ] Add file information display

### **Phase 4: Progress Screen**

- [ ] Implement ProgressPanel component
- [ ] Create real-time progress bars
- [ ] Add processing log display
- [ ] Implement pause/resume functionality
- [ ] Add completion summary

### **Phase 5: Integration & Polish**

- [ ] Integrate with existing core functionality
- [ ] Add async file processing support
- [ ] Implement error handling and recovery
- [ ] Add themes and styling
- [ ] Performance optimization

### **Phase 6: Testing & Documentation**

- [ ] Comprehensive testing
- [ ] User documentation
- [ ] Developer documentation
- [ ] Performance testing
- [ ] Accessibility testing

## Key Benefits

### **User Experience**

- **Beautiful Interface**: Modern, intuitive design
- **Real-time Feedback**: Live progress and status updates
- **Easy Navigation**: Intuitive keyboard and mouse controls
- **Error Recovery**: Graceful handling of issues

### **Developer Experience**

- **Modular Design**: Reusable components for easy maintenance
- **Type Safety**: Full type hints and validation
- **Testing**: Comprehensive test coverage
- **Documentation**: Clear code and user documentation

### **Technical Benefits**

- **CLI Compatibility**: Preserves existing functionality
- **Cross-platform**: Works on all platforms that support Textual
- **Performance**: Efficient async processing
- **Accessibility**: Keyboard navigation and screen reader support

## Success Metrics

### **User Experience**

- Intuitive navigation (users can complete tasks without documentation)
- Fast response times (< 100ms for UI interactions)
- Clear error messages and recovery options
- Beautiful, modern appearance

### **Technical**

- Zero breaking changes to existing CLI functionality
- Full test coverage for new TUI components
- Performance parity with CLI mode
- Cross-platform compatibility

### **Maintainability**

- Modular component architecture
- Clear separation of concerns
- Comprehensive documentation
- Easy to extend and modify

## Conclusion

This TUI implementation will transform the jellyfin-renamer from a command-line tool into a beautiful, interactive application while preserving all existing functionality. The modular design ensures maintainability and extensibility, while the focus on user experience will make the application accessible to a wider audience.

The implementation will be done in phases, allowing for incremental development and testing. Each phase builds upon the previous one, ensuring a solid foundation for the next iteration.
