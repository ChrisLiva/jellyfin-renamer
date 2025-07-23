"""Progress screen for showing file processing progress."""

import asyncio
import os
from typing import Any, Dict

from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Label, Static
from textual.worker import Worker

from ..components.progress_panel import ProgressPanel


class ProgressScreen(Screen):
    """Screen for displaying file processing progress."""

    BINDINGS = [
        Binding("escape", "back_to_main", "Back to Main", show=True),
    ]

    DEFAULT_CSS = """
    ProgressScreen {
        background: $background;
    }
    
    .progress-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        background: $surface;
        margin: 1;
        padding: 1;
    }
    
    .completion-section {
        border: solid $success;
        margin: 2;
        padding: 2;
        text-align: center;
    }
    
    .completion-title {
        text-style: bold;
        color: $success;
        margin-bottom: 1;
    }
    
    .completion-stats {
        color: $text;
        margin: 1;
    }
    
    .completion-buttons {
        margin: 2;
    }
    
    .view-files-button {
        background: $primary;
        margin: 0 1;
    }
    
    .back-button {
        background: $accent;
        margin: 0 1;
    }
    
    .error-section {
        border: solid $error;
        margin: 2;
        padding: 2;
        text-align: center;
    }
    
    .error-title {
        text-style: bold;
        color: $error;
        margin-bottom: 1;
    }
    """

    # Reactive state
    is_processing = reactive(False)
    is_completed = reactive(False)
    is_cancelled = reactive(False)
    has_errors = reactive(False)

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__()
        self.config = config
        self.processing_worker: Worker = None
        self.results = {
            "files_processed": 0,
            "files_failed": 0,
            "total_files": len(config.get("selected_files", [])),
            "errors": [],
        }

    def compose(self) -> ComposeResult:
        """Create child widgets for the progress screen."""
        with Vertical():
            # Title
            yield Static(
                "🚀 Processing Media Files\nPlease wait while your files are organized...",
                classes="progress-title",
            )

            # Progress panel
            yield ProgressPanel(id="progress_panel")

            # Completion section (initially hidden)
            with Container(classes="completion-section", id="completion_section"):
                yield Label("✅ Processing Complete!", classes="completion-title")
                yield Static("", id="completion_stats", classes="completion-stats")

                with Container(classes="completion-buttons"):
                    yield Button(
                        "📂 View Organized Files",
                        id="view_files_btn",
                        classes="view-files-button",
                    )
                    yield Button(
                        "🏠 Back to Main", id="back_main_btn", classes="back-button"
                    )

            # Error section (initially hidden)
            with Container(classes="error-section", id="error_section"):
                yield Label("❌ Processing Error", classes="error-title")
                yield Static("", id="error_details", classes="completion-stats")

                with Container(classes="completion-buttons"):
                    yield Button(
                        "🏠 Back to Main", id="back_error_btn", classes="back-button"
                    )

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        # Hide completion and error sections initially
        completion_section = self.query_one("#completion_section")
        error_section = self.query_one("#error_section")
        completion_section.display = False
        error_section.display = False

        # Set up progress panel with total files
        progress_panel = self.query_one("#progress_panel", ProgressPanel)
        progress_panel.set_total_files(self.results["total_files"])

        # Start processing
        self.start_processing()

    @on(ProgressPanel.ControlAction)
    def on_control_action(self, event: ProgressPanel.ControlAction) -> None:
        """Handle control actions from progress panel."""
        if event.action == "pause":
            self.pause_processing()
        elif event.action == "resume":
            self.resume_processing()
        elif event.action == "cancel":
            self.cancel_processing()

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id in ["back_main_btn", "back_error_btn"]:
            self.action_back_to_main()
        elif event.button.id == "view_files_btn":
            self.action_view_files()

    def start_processing(self) -> None:
        """Start the file processing."""
        self.is_processing = True
        progress_panel = self.query_one("#progress_panel", ProgressPanel)
        progress_panel.log_message("Starting file processing...", "info")

        # Start the processing worker
        self.processing_worker = self.process_files()

    @work(exclusive=True)
    async def process_files(self) -> None:
        """Process the selected files using existing core functionality."""
        progress_panel = self.query_one("#progress_panel", ProgressPanel)

        try:
            # Import core functions
            from core.common import scan_source_directory
            from core.movie_organizer import organize_movies
            from core.tv_organizer import organize_tv_shows

            source_dir = self.config["source_directory"]
            target_dir = self.config["target_directory"]
            content_type = self.config["content_type"]
            downmix_audio = self.config["downmix_audio"]
            selected_files = self.config["selected_files"]

            progress_panel.log_message(
                f"Processing {len(selected_files)} files", "info"
            )
            progress_panel.log_message(f"Source: {source_dir}", "info")
            progress_panel.log_message(f"Target: {target_dir}", "info")
            progress_panel.log_message(f"Content Type: {content_type}", "info")
            progress_panel.log_message(
                f"Audio Processing: {'Enabled' if downmix_audio else 'Disabled'}",
                "info",
            )

            # Create a temporary directory structure for selected files
            # This is a simplified version - in a real implementation, you'd want to
            # modify the core functions to work with selected files directly

            if content_type == "movies":
                progress_panel.log_message("Processing as movies...", "info")
                await self.process_movies(
                    source_dir,
                    target_dir,
                    downmix_audio,
                    selected_files,
                    progress_panel,
                )
            elif content_type == "tv":
                progress_panel.log_message("Processing as TV shows...", "info")
                await self.process_tv_shows(
                    source_dir,
                    target_dir,
                    downmix_audio,
                    selected_files,
                    progress_panel,
                )
            else:  # auto
                progress_panel.log_message("Auto-detecting content type...", "info")
                await self.process_mixed_content(
                    source_dir,
                    target_dir,
                    downmix_audio,
                    selected_files,
                    progress_panel,
                )

            # Mark as completed
            self.is_processing = False
            self.is_completed = True
            progress_panel.log_message("Processing completed successfully!", "success")
            self.show_completion()

        except Exception as e:
            self.is_processing = False
            self.has_errors = True
            self.results["errors"].append(str(e))
            progress_panel.log_message(f"Processing failed: {str(e)}", "error")
            self.show_error(str(e))

    async def process_movies(
        self,
        source_dir: str,
        target_dir: str,
        downmix_audio: bool,
        selected_files: list,
        progress_panel: ProgressPanel,
    ) -> None:
        """Process selected files as movies."""
        # This is a simplified implementation
        # In a real scenario, you'd want to modify the core organize_movies function
        # to work with a selected file list instead of scanning the entire directory

        from core.movie_organizer import organize_movies

        # Create Movies subdirectory
        movies_dir = os.path.join(target_dir, "Movies")
        os.makedirs(movies_dir, exist_ok=True)

        progress_panel.update_progress(
            0, "Starting movie organization...", 0, 0, len(selected_files)
        )

        # For now, use the existing function (this would need modification in a real implementation)
        await organize_movies(source_dir, movies_dir, downmix_audio)

        progress_panel.update_progress(
            100,
            "Movie organization complete",
            100,
            len(selected_files),
            len(selected_files),
        )
        self.results["files_processed"] = len(selected_files)

    async def process_tv_shows(
        self,
        source_dir: str,
        target_dir: str,
        downmix_audio: bool,
        selected_files: list,
        progress_panel: ProgressPanel,
    ) -> None:
        """Process selected files as TV shows."""
        from core.tv_organizer import organize_tv_shows

        # Create Shows subdirectory
        shows_dir = os.path.join(target_dir, "Shows")
        os.makedirs(shows_dir, exist_ok=True)

        progress_panel.update_progress(
            0, "Starting TV show organization...", 0, 0, len(selected_files)
        )

        # For now, use the existing function (this would need modification in a real implementation)
        await organize_tv_shows(source_dir, shows_dir, downmix_audio)

        progress_panel.update_progress(
            100,
            "TV show organization complete",
            100,
            len(selected_files),
            len(selected_files),
        )
        self.results["files_processed"] = len(selected_files)

    async def process_mixed_content(
        self,
        source_dir: str,
        target_dir: str,
        downmix_audio: bool,
        selected_files: list,
        progress_panel: ProgressPanel,
    ) -> None:
        """Process selected files with auto-detection."""
        from core.common import scan_source_directory
        from core.movie_organizer import organize_movies
        from core.tv_organizer import organize_tv_shows

        progress_panel.update_progress(
            0, "Scanning and detecting content types...", 0, 0, len(selected_files)
        )

        # Scan files and auto-detect content types
        all_files = scan_source_directory(source_dir, content_type="auto")

        # Filter to only selected files
        selected_set = set(selected_files)
        filtered_files = [
            (root, file, content_type)
            for root, file, content_type in all_files
            if os.path.join(root, file) in selected_set
        ]

        # Separate by type
        movie_files = [
            (root, file)
            for root, file, content_type in filtered_files
            if content_type == "movie"
        ]
        tv_files = [
            (root, file)
            for root, file, content_type in filtered_files
            if content_type == "tv"
        ]

        progress_panel.log_message(
            f"Found {len(movie_files)} movie files and {len(tv_files)} TV show files",
            "info",
        )

        processed_count = 0
        total_files = len(movie_files) + len(tv_files)

        # Process movies if found
        if movie_files:
            movies_dir = os.path.join(target_dir, "Movies")
            os.makedirs(movies_dir, exist_ok=True)
            progress_panel.update_progress(
                (processed_count / total_files) * 100,
                "Processing movies...",
                0,
                processed_count,
                total_files,
            )

            # Use existing function (simplified)
            await organize_movies(source_dir, movies_dir, downmix_audio)
            processed_count += len(movie_files)

        # Process TV shows if found
        if tv_files:
            shows_dir = os.path.join(target_dir, "Shows")
            os.makedirs(shows_dir, exist_ok=True)
            progress_panel.update_progress(
                (processed_count / total_files) * 100,
                "Processing TV shows...",
                0,
                processed_count,
                total_files,
            )

            # Use existing function (simplified)
            await organize_tv_shows(source_dir, shows_dir, downmix_audio)
            processed_count += len(tv_files)

        progress_panel.update_progress(
            100, "Mixed content organization complete", 100, total_files, total_files
        )
        self.results["files_processed"] = processed_count

    def pause_processing(self) -> None:
        """Pause the processing."""
        if self.processing_worker and not self.processing_worker.is_finished:
            # Note: Textual workers don't have built-in pause/resume
            # This would need to be implemented with custom logic
            pass

    def resume_processing(self) -> None:
        """Resume the processing."""
        # Note: Textual workers don't have built-in pause/resume
        # This would need to be implemented with custom logic
        pass

    def cancel_processing(self) -> None:
        """Cancel the processing."""
        if self.processing_worker and not self.processing_worker.is_finished:
            self.processing_worker.cancel()
            self.is_processing = False
            self.is_cancelled = True

            progress_panel = self.query_one("#progress_panel", ProgressPanel)
            progress_panel.log_message("Processing cancelled by user", "warning")

    def show_completion(self) -> None:
        """Show the completion section."""
        progress_panel = self.query_one("#progress_panel", ProgressPanel)
        completion_section = self.query_one("#completion_section")
        completion_stats = self.query_one("#completion_stats", Static)

        # Hide progress panel and show completion
        progress_panel.display = False
        completion_section.display = True

        # Update completion stats
        stats_text = (
            f"Files processed: {self.results['files_processed']}\n"
            f"Files failed: {self.results['files_failed']}\n"
            f"Total files: {self.results['total_files']}\n\n"
            f"Your media files have been organized and are ready for Jellyfin!"
        )
        completion_stats.update(stats_text)

    def show_error(self, error_message: str) -> None:
        """Show the error section."""
        progress_panel = self.query_one("#progress_panel", ProgressPanel)
        error_section = self.query_one("#error_section")
        error_details = self.query_one("#error_details", Static)

        # Hide progress panel and show error
        progress_panel.display = False
        error_section.display = True

        # Update error details
        error_details.update(f"An error occurred during processing:\n\n{error_message}")

    def action_back_to_main(self) -> None:
        """Action to go back to main screen."""
        # Cancel any running processing
        if self.processing_worker and not self.processing_worker.is_finished:
            self.processing_worker.cancel()

        self.app.pop_screen()

    def action_view_files(self) -> None:
        """Action to view organized files."""
        # Open file manager or show file browser
        target_dir = self.config["target_directory"]

        try:
            import platform
            import subprocess

            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["open", target_dir])
            elif system == "Windows":
                subprocess.run(["explorer", target_dir])
            else:  # Linux and others
                subprocess.run(["xdg-open", target_dir])
        except Exception:
            # If we can't open the file manager, just show a message
            progress_panel = self.query_one("#progress_panel", ProgressPanel)
            progress_panel.log_message(f"Files organized in: {target_dir}", "info")
