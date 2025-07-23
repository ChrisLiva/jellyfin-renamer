"""File selector component for choosing which files to process."""

import os
from typing import List, Set

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Checkbox, DataTable, Label, Static

from ..utils.tui_helpers import format_file_size, scan_directory_for_videos


class FileSelector(Widget):
    """A widget for selecting video files to process."""

    DEFAULT_CSS = """
    FileSelector {
        border: solid $accent;
        margin: 1;
        padding: 1;
        height: auto;
    }
    
    .file-table {
        height: 20;
        margin: 1;
    }
    
    .selection-controls {
        margin: 1;
    }
    
    .file-stats {
        margin: 1;
        text-align: center;
        color: $accent;
    }
    
    .video-file-row {
        background: $surface;
    }
    
    .selected-file-row {
        background: $primary 30%;
    }
    """

    class FilesSelected(Message):
        """Emitted when file selection changes."""

        def __init__(self, selected_files: List[str], total_size: int) -> None:
            self.selected_files = selected_files
            self.total_size = total_size
            super().__init__()

    source_directory = reactive("", always_update=True)
    selected_files: Set[str] = reactive(set())

    def __init__(
        self,
        source_directory: str = "",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ):
        super().__init__(name=name, id=id, classes=classes)
        self.source_directory = source_directory
        self.files = []
        self.selected_files = set()

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Vertical():
            yield Label("Video Files", classes="file-selector-title")

            with Horizontal(classes="selection-controls"):
                yield Button("Select All", id="select_all", classes="secondary")
                yield Button("Clear All", id="clear_all", classes="secondary")
                yield Button("Refresh", id="refresh", classes="secondary")

            yield DataTable(
                id="file_table",
                classes="file-table",
                cursor_type="row",
                zebra_stripes=True,
            )

            yield Static("No files loaded", id="file_stats", classes="file-stats")

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self.setup_table()
        if self.source_directory:
            self.refresh_files()

    def setup_table(self) -> None:
        """Set up the data table columns."""
        table = self.query_one("#file_table", DataTable)
        table.add_columns("Select", "Filename", "Size", "Path")
        table.cursor_type = "row"

    @on(Button.Pressed, "#select_all")
    def select_all_files(self) -> None:
        """Select all video files."""
        self.selected_files = {file_info["path"] for file_info in self.files}
        self.update_table_display()
        self.update_stats()
        self.emit_selection_change()

    @on(Button.Pressed, "#clear_all")
    def clear_all_files(self) -> None:
        """Clear all file selections."""
        self.selected_files = set()
        self.update_table_display()
        self.update_stats()
        self.emit_selection_change()

    @on(Button.Pressed, "#refresh")
    def refresh_files(self) -> None:
        """Refresh the file list from the source directory."""
        if not self.source_directory or not os.path.isdir(self.source_directory):
            self.files = []
            self.selected_files = set()
            self.update_table_display()
            self.update_stats()
            return

        # Scan for video files
        self.files = scan_directory_for_videos(self.source_directory)

        # Clear selection if files changed
        valid_files = {file_info["path"] for file_info in self.files}
        self.selected_files = self.selected_files.intersection(valid_files)

        self.update_table_display()
        self.update_stats()
        self.emit_selection_change()

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in the table."""
        if event.row_index < len(self.files):
            file_info = self.files[event.row_index]
            file_path = file_info["path"]

            # Toggle selection
            if file_path in self.selected_files:
                self.selected_files.remove(file_path)
            else:
                self.selected_files.add(file_path)

            self.update_table_display()
            self.update_stats()
            self.emit_selection_change()

    def update_table_display(self) -> None:
        """Update the table display with current files and selection."""
        try:
            table = self.query_one("#file_table", DataTable)
            table.clear()

            for file_info in self.files:
                file_path = file_info["path"]
                is_selected = file_path in self.selected_files

                select_indicator = "☑" if is_selected else "☐"
                filename = file_info["name"]
                size = file_info["size_formatted"]
                relative_path = file_info["relative_path"]

                row_key = table.add_row(
                    select_indicator, filename, size, relative_path, key=file_path
                )

                # Style selected rows
                if is_selected:
                    table.set_row_styles(row_key, "selected-file-row")
        except Exception:
            # UI elements not yet created, skip update
            pass

    def update_stats(self) -> None:
        """Update the file statistics display."""
        try:
            stats_widget = self.query_one("#file_stats", Static)

            total_files = len(self.files)
            selected_count = len(self.selected_files)

            if total_files == 0:
                stats_widget.update("No video files found")
                return

            # Calculate total size of selected files
            total_size = sum(
                file_info["size"]
                for file_info in self.files
                if file_info["path"] in self.selected_files
            )

            size_text = format_file_size(total_size) if total_size > 0 else "0 B"

            stats_widget.update(
                f"Selected: {selected_count}/{total_files} files ({size_text})"
            )
        except Exception:
            # UI elements not yet created, skip update
            pass

    def emit_selection_change(self) -> None:
        """Emit selection change event."""
        total_size = sum(
            file_info["size"]
            for file_info in self.files
            if file_info["path"] in self.selected_files
        )

        self.post_message(self.FilesSelected(list(self.selected_files), total_size))

    def set_source_directory(self, directory: str) -> None:
        """Set the source directory and refresh files."""
        self.source_directory = directory
        self.refresh_files()

    def get_selected_files(self) -> List[str]:
        """Get list of selected file paths."""
        return list(self.selected_files)

    def watch_source_directory(self, new_directory: str) -> None:
        """Watch for source directory changes."""
        self.refresh_files()
