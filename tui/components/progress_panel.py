"""Progress panel component for showing file processing progress."""

import time
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Label, Log, ProgressBar, Static

from ..utils.tui_helpers import format_file_size


class ProgressPanel(Widget):
    """A widget for displaying processing progress with multiple progress bars."""

    DEFAULT_CSS = """
    ProgressPanel {
        border: solid $primary;
        margin: 1;
        padding: 1;
        height: auto;
    }
    
    .progress-header {
        text-style: bold;
        color: $primary;
        text-align: center;
        margin-bottom: 1;
    }
    
    .overall-progress {
        margin: 1;
    }
    
    .file-progress {
        margin: 1;
    }
    
    .progress-label {
        margin-bottom: 1;
        color: $accent;
    }
    
    .status-grid {
        margin: 1;
        height: 6;
    }
    
    .status-item {
        text-align: center;
        color: $text;
        margin: 1;
    }
    
    .log-container {
        border: solid $accent;
        margin: 1;
        height: 10;
    }
    
    .control-buttons {
        margin: 1;
        text-align: center;
    }
    
    .cancel-button {
        background: $error;
    }
    
    .pause-button {
        background: $warning;
    }
    
    .resume-button {
        background: $success;
    }
    """

    class ProgressUpdate(Message):
        """Emitted when progress is updated."""

        def __init__(
            self,
            overall_progress: float,
            current_file: str = "",
            file_progress: float = 0.0,
            status: str = "",
        ) -> None:
            self.overall_progress = overall_progress
            self.current_file = current_file
            self.file_progress = file_progress
            self.status = status
            super().__init__()

    class ControlAction(Message):
        """Emitted when a control action is requested."""

        def __init__(self, action: str) -> None:
            self.action = action  # 'pause', 'resume', 'cancel'
            super().__init__()

    overall_progress = reactive(0.0)
    file_progress = reactive(0.0)
    current_file = reactive("")
    status = reactive("Ready")
    is_paused = reactive(False)
    is_cancelled = reactive(False)

    def __init__(
        self,
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ):
        super().__init__(name=name, id=id, classes=classes)
        self.start_time = time.time()
        self.files_completed = 0
        self.total_files = 0
        self.total_size_processed = 0
        self.total_size = 0

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Vertical():
            yield Label("Processing Progress", classes="progress-header")

            # Overall progress
            with Container(classes="overall-progress"):
                yield Label("Overall Progress:", classes="progress-label")
                yield ProgressBar(id="overall_bar", show_percentage=True)

            # Current file progress
            with Container(classes="file-progress"):
                yield Label("Current File:", classes="progress-label")
                yield Static("No file selected", id="current_file_label")
                yield ProgressBar(id="file_bar", show_percentage=True)

            # Status information grid
            with Horizontal(classes="status-grid"):
                yield Static("Files: 0/0", id="files_status", classes="status-item")
                yield Static("Size: 0 B", id="size_status", classes="status-item")
                yield Static(
                    "Speed: 0 files/min", id="speed_status", classes="status-item"
                )
                yield Static("ETA: --", id="eta_status", classes="status-item")

            # Control buttons
            with Horizontal(classes="control-buttons"):
                yield Button("Pause", id="pause_btn", classes="pause-button")
                yield Button("Cancel", id="cancel_btn", classes="cancel-button")

            # Log container
            with Container(classes="log-container"):
                yield Log(id="progress_log", auto_scroll=True)

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self.update_display()

    def update_progress(
        self,
        overall_progress: float,
        current_file: str = "",
        file_progress: float = 0.0,
        files_completed: int = 0,
        total_files: int = 0,
        size_processed: int = 0,
        total_size: int = 0,
    ) -> None:
        """Update the progress display."""
        self.overall_progress = max(0.0, min(100.0, overall_progress))
        self.file_progress = max(0.0, min(100.0, file_progress))
        self.current_file = current_file
        self.files_completed = files_completed
        self.total_files = total_files
        self.total_size_processed = size_processed
        self.total_size = total_size

        self.update_display()

        # Emit progress update event
        self.post_message(
            self.ProgressUpdate(
                overall_progress, current_file, file_progress, self.status
            )
        )

    def update_display(self) -> None:
        """Update all display elements."""
        # Update progress bars
        overall_bar = self.query_one("#overall_bar", ProgressBar)
        file_bar = self.query_one("#file_bar", ProgressBar)
        overall_bar.progress = self.overall_progress
        file_bar.progress = self.file_progress

        # Update current file label
        current_file_label = self.query_one("#current_file_label", Static)
        if self.current_file:
            filename = self.current_file.split("/")[-1]  # Get just the filename
            current_file_label.update(f"Processing: {filename}")
        else:
            current_file_label.update("No file selected")

        # Update status grid
        files_status = self.query_one("#files_status", Static)
        size_status = self.query_one("#size_status", Static)
        speed_status = self.query_one("#speed_status", Static)
        eta_status = self.query_one("#eta_status", Static)

        files_status.update(f"Files: {self.files_completed}/{self.total_files}")

        size_processed_str = format_file_size(self.total_size_processed)
        total_size_str = format_file_size(self.total_size)
        size_status.update(f"Size: {size_processed_str}/{total_size_str}")

        # Calculate speed and ETA
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 0 and self.files_completed > 0:
            files_per_minute = (self.files_completed / elapsed_time) * 60
            speed_status.update(f"Speed: {files_per_minute:.1f} files/min")

            # Calculate ETA
            if files_per_minute > 0 and self.total_files > self.files_completed:
                remaining_files = self.total_files - self.files_completed
                eta_minutes = remaining_files / files_per_minute
                if eta_minutes < 60:
                    eta_status.update(f"ETA: {eta_minutes:.1f}m")
                else:
                    eta_hours = eta_minutes / 60
                    eta_status.update(f"ETA: {eta_hours:.1f}h")
            else:
                eta_status.update("ETA: --")
        else:
            speed_status.update("Speed: 0 files/min")
            eta_status.update("ETA: --")

        # Update button states
        pause_btn = self.query_one("#pause_btn", Button)
        if self.is_paused:
            pause_btn.label = "Resume"
            pause_btn.set_class(True, "resume-button")
            pause_btn.set_class(False, "pause-button")
        else:
            pause_btn.label = "Pause"
            pause_btn.set_class(False, "resume-button")
            pause_btn.set_class(True, "pause-button")

    def log_message(self, message: str, level: str = "info") -> None:
        """Add a message to the log."""
        log_widget = self.query_one("#progress_log", Log)
        timestamp = time.strftime("%H:%M:%S")

        if level == "error":
            log_widget.write_line(f"[{timestamp}] ERROR: {message}")
        elif level == "warning":
            log_widget.write_line(f"[{timestamp}] WARNING: {message}")
        elif level == "success":
            log_widget.write_line(f"[{timestamp}] SUCCESS: {message}")
        else:
            log_widget.write_line(f"[{timestamp}] {message}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "pause_btn":
            if self.is_paused:
                self.resume_processing()
            else:
                self.pause_processing()
        elif event.button.id == "cancel_btn":
            self.cancel_processing()

    def pause_processing(self) -> None:
        """Pause the processing."""
        self.is_paused = True
        self.status = "Paused"
        self.update_display()
        self.log_message("Processing paused", "warning")
        self.post_message(self.ControlAction("pause"))

    def resume_processing(self) -> None:
        """Resume the processing."""
        self.is_paused = False
        self.status = "Processing"
        self.update_display()
        self.log_message("Processing resumed", "success")
        self.post_message(self.ControlAction("resume"))

    def cancel_processing(self) -> None:
        """Cancel the processing."""
        self.is_cancelled = True
        self.status = "Cancelled"
        self.update_display()
        self.log_message("Processing cancelled", "error")
        self.post_message(self.ControlAction("cancel"))

    def reset(self) -> None:
        """Reset the progress panel to initial state."""
        self.overall_progress = 0.0
        self.file_progress = 0.0
        self.current_file = ""
        self.status = "Ready"
        self.is_paused = False
        self.is_cancelled = False
        self.start_time = time.time()
        self.files_completed = 0
        self.total_files = 0
        self.total_size_processed = 0
        self.total_size = 0

        # Clear log
        log_widget = self.query_one("#progress_log", Log)
        log_widget.clear()

        self.update_display()

    def set_total_files(self, total_files: int, total_size: int = 0) -> None:
        """Set the total number of files and size for progress calculation."""
        self.total_files = total_files
        self.total_size = total_size
        self.update_display()

    def watch_overall_progress(self, new_progress: float) -> None:
        """Watch for overall progress changes."""
        self.update_display()

    def watch_file_progress(self, new_progress: float) -> None:
        """Watch for file progress changes."""
        self.update_display()

    def watch_current_file(self, new_file: str) -> None:
        """Watch for current file changes."""
        self.update_display()

    def watch_status(self, new_status: str) -> None:
        """Watch for status changes."""
        self.update_display()
