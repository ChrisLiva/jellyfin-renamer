"""Main configuration screen for the TUI."""

import os
from typing import Optional

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Label, RadioButton, RadioSet, Static

from ..components.directory_picker import DirectoryPicker
from ..components.file_selector import FileSelector
from .progress_screen import ProgressScreen


class MainScreen(Screen):
    """Main configuration screen for jellyfin-renamer."""

    BINDINGS = [
        Binding("f2", "browse_source", "Browse Source", show=True),
        Binding("f3", "browse_target", "Browse Target", show=True),
        Binding("f5", "start_processing", "Start Processing", show=True),
        Binding("escape", "exit_app", "Exit", show=True),
    ]

    DEFAULT_CSS = """
    MainScreen {
        background: $background;
    }
    
    .main-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        background: $surface;
        margin: 1;
        padding: 1;
    }
    
    .config-section {
        border: solid $accent;
        margin: 1;
        padding: 1;
        height: auto;
    }
    
    .section-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    .radio-group {
        margin: 1;
    }
    
    .checkbox-group {
        margin: 1;
    }
    
    .action-buttons {
        margin: 2;
        text-align: center;
    }
    
    .start-button {
        background: $success;
        margin: 0 1;
        min-width: 20;
    }
    
    .preview-button {
        background: $warning;
        margin: 0 1;
        min-width: 20;
    }
    
    .exit-button {
        background: $error;
        margin: 0 1;
        min-width: 20;
    }
    
    .validation-message {
        margin: 1;
        text-align: center;
        padding: 1;
    }
    
    .error-validation {
        color: $error;
        background: $background;
    }
    
    .success-validation {
        color: $success;
        background: $background;
    }
    """

    # Reactive attributes for configuration state
    source_directory = reactive("")
    target_directory = reactive("")
    content_type = reactive("auto")
    downmix_audio = reactive(False)
    selected_files = reactive([])
    is_valid_config = reactive(False)

    def __init__(self, name: Optional[str] = None) -> None:
        super().__init__(name=name)
        self.selected_files = []

    def compose(self) -> ComposeResult:
        """Create child widgets for the main screen."""
        with Vertical():
            # Title
            yield Static(
                "🎬 Jellyfin Media Renamer\nOrganize your media files beautifully",
                classes="main-title",
            )

            # Configuration section
            with Container(classes="config-section"):
                yield Label("Configuration", classes="section-title")

                # Directory pickers
                yield DirectoryPicker(
                    label="Source Directory (where your media files are)",
                    placeholder="Select source directory...",
                    initial_directory=os.getcwd(),
                    id="source_picker",
                )

                yield DirectoryPicker(
                    label="Target Directory (where organized files will go)",
                    placeholder="Select target directory...",
                    initial_directory=os.getcwd(),
                    id="target_picker",
                )

                # Content type selection
                with Container(classes="radio-group"):
                    yield Label("Content Type:")
                    with RadioSet(id="content_type_radio"):
                        yield RadioButton(
                            "Auto-detect (recommended)", value="auto", id="auto_radio"
                        )
                        yield RadioButton(
                            "Movies only", value="movies", id="movies_radio"
                        )
                        yield RadioButton("TV shows only", value="tv", id="tv_radio")

                # Audio processing option
                with Container(classes="checkbox-group"):
                    yield Checkbox(
                        "Enable FFmpeg audio processing (convert to stereo FLAC)",
                        id="audio_checkbox",
                    )

            # File selection section
            with Container(classes="config-section"):
                yield Label("File Selection", classes="section-title")
                yield FileSelector(id="file_selector")

            # Validation message
            yield Static("", id="validation_message", classes="validation-message")

            # Action buttons
            with Horizontal(classes="action-buttons"):
                yield Button("👀 Preview", id="preview_btn", classes="preview-button")
                yield Button(
                    "🚀 Start Processing", id="start_btn", classes="start-button"
                )
                yield Button("❌ Exit", id="exit_btn", classes="exit-button")

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        # Set initial radio button selection
        try:
            auto_radio = self.query_one("#auto_radio", RadioButton)
            auto_radio.press()
        except Exception:
            # UI elements not yet created, skip initialization
            pass

        self.validate_configuration()

    @on(DirectoryPicker.DirectoryChanged)
    def on_directory_changed(self, event: DirectoryPicker.DirectoryChanged) -> None:
        """Handle directory picker changes."""
        # Get the DirectoryPicker that sent this message
        sender = event.control if hasattr(event, 'control') else None
        if sender and sender.id == "source_picker":
            self.source_directory = event.directory
            # Update file selector when source directory changes
            if event.is_valid:
                file_selector = self.query_one("#file_selector", FileSelector)
                file_selector.set_source_directory(event.directory)
        elif sender and sender.id == "target_picker":
            self.target_directory = event.directory

        self.validate_configuration()

    @on(RadioSet.Changed)
    def on_content_type_changed(self, event: RadioSet.Changed) -> None:
        """Handle content type selection changes."""
        if event.radio_set.id == "content_type_radio":
            self.content_type = event.pressed.value
            self.validate_configuration()

    @on(Checkbox.Changed)
    def on_audio_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle audio processing checkbox changes."""
        if event.checkbox.id == "audio_checkbox":
            self.downmix_audio = event.value
            self.validate_configuration()

    @on(FileSelector.FilesSelected)
    def on_files_selected(self, event: FileSelector.FilesSelected) -> None:
        """Handle file selection changes."""
        self.selected_files = event.selected_files
        self.validate_configuration()

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "start_btn":
            self.action_start_processing()
        elif event.button.id == "preview_btn":
            self.action_preview_processing()
        elif event.button.id == "exit_btn":
            self.action_exit_app()

    def validate_configuration(self) -> None:
        """Validate the current configuration and update UI accordingly."""
        # Check if UI elements have been created yet
        try:
            source_picker = self.query_one("#source_picker", DirectoryPicker)
            target_picker = self.query_one("#target_picker", DirectoryPicker)
            validation_msg = self.query_one("#validation_message", Static)
            start_btn = self.query_one("#start_btn", Button)
            preview_btn = self.query_one("#preview_btn", Button)
        except Exception:
            # UI elements not yet created, skip validation
            return

        errors = []

        # Validate source directory
        if not source_picker.is_valid():
            errors.append("Invalid source directory")

        # Validate target directory
        if not target_picker.is_valid():
            errors.append("Invalid target directory")

        # Check if directories are the same
        if (
            source_picker.is_valid()
            and target_picker.is_valid()
            and source_picker.get_directory() == target_picker.get_directory()
        ):
            errors.append("Source and target directories cannot be the same")

        # Check if files are selected
        if not self.selected_files:
            errors.append("No files selected for processing")

        # Update validation message
        if errors:
            self.is_valid_config = False
            validation_msg.update(f"⚠️ {'; '.join(errors)}")
            validation_msg.set_class(True, "error-validation")
            validation_msg.set_class(False, "success-validation")
            start_btn.disabled = True
            preview_btn.disabled = True
        else:
            self.is_valid_config = True
            file_count = len(self.selected_files)
            validation_msg.update(f"✅ Ready to process {file_count} files")
            validation_msg.set_class(False, "error-validation")
            validation_msg.set_class(True, "success-validation")
            start_btn.disabled = False
            preview_btn.disabled = False

    def action_browse_source(self) -> None:
        """Action to browse source directory."""
        source_picker = self.query_one("#source_picker", DirectoryPicker)
        source_picker.toggle_browsing()

    def action_browse_target(self) -> None:
        """Action to browse target directory."""
        target_picker = self.query_one("#target_picker", DirectoryPicker)
        target_picker.toggle_browsing()

    def action_start_processing(self) -> None:
        """Action to start file processing."""
        if not self.is_valid_config:
            return

        # Gather configuration
        config = {
            "source_directory": self.source_directory,
            "target_directory": self.target_directory,
            "content_type": self.content_type,
            "downmix_audio": self.downmix_audio,
            "selected_files": self.selected_files,
        }

        # Navigate to progress screen
        progress_screen = ProgressScreen(config)
        self.app.push_screen(progress_screen)

    def action_preview_processing(self) -> None:
        """Action to preview what processing would do."""
        if not self.is_valid_config:
            return

        # Show preview dialog or screen
        from textual.containers import Container
        from textual.screen import ModalScreen
        from textual.widgets import Button, Label

        class PreviewScreen(ModalScreen):
            BINDINGS = [
                Binding("escape", "dismiss", "Close"),
            ]

            def __init__(self, config: dict) -> None:
                super().__init__()
                self.config = config

            def compose(self) -> ComposeResult:
                with Container(classes="main-container"):
                    yield Label("Processing Preview", classes="title")
                    yield Static(
                        f"Source: {self.config['source_directory']}\n"
                        f"Target: {self.config['target_directory']}\n"
                        f"Content Type: {self.config['content_type']}\n"
                        f"Audio Processing: {'Yes' if self.config['downmix_audio'] else 'No'}\n"
                        f"Files to Process: {len(self.config['selected_files'])}\n\n"
                        "Files will be organized according to Jellyfin naming conventions.\n"
                        "Movies will be placed in 'Movie Title (Year)/' folders.\n"
                        "TV shows will be placed in 'Show Name/Season XX/' folders.\n\n"
                        "Press ESC to close this preview.",
                        classes="preview-text",
                    )

        config = {
            "source_directory": self.source_directory,
            "target_directory": self.target_directory,
            "content_type": self.content_type,
            "downmix_audio": self.downmix_audio,
            "selected_files": self.selected_files,
        }

        self.app.push_screen(PreviewScreen(config))

    def action_exit_app(self) -> None:
        """Action to exit the application."""
        self.app.exit()

    def watch_source_directory(self, new_directory: str) -> None:
        """Watch for source directory changes."""
        self.validate_configuration()

    def watch_target_directory(self, new_directory: str) -> None:
        """Watch for target directory changes."""
        self.validate_configuration()

    def watch_selected_files(self, new_files: list) -> None:
        """Watch for selected files changes."""
        self.validate_configuration()

    def get_configuration(self) -> dict:
        """Get the current configuration."""
        return {
            "source_directory": self.source_directory,
            "target_directory": self.target_directory,
            "content_type": self.content_type,
            "downmix_audio": self.downmix_audio,
            "selected_files": self.selected_files,
        }
