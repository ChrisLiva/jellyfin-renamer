"""Directory picker component for selecting source and target directories."""

import os
from pathlib import Path
from typing import Callable, Optional

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, DirectoryTree, Input, Label, Static

from ..utils.tui_helpers import validate_directory


class DirectoryPicker(Widget):
    """A widget for picking directories with validation and browsing."""

    DEFAULT_CSS = """
    DirectoryPicker {
        border: solid $accent;
        margin: 1;
        padding: 1;
        height: auto;
    }
    
    .directory-input {
        width: 1fr;
    }
    
    .browse-button {
        min-width: 10;
        margin-left: 1;
    }
    
    .error-text {
        color: $error;
        text-style: italic;
    }
    
    .valid-text {
        color: $success;
        text-style: italic;
    }
    
    .directory-tree {
        height: 15;
        display: none;
    }
    
    .directory-tree.visible {
        display: block;
    }
    """

    class DirectoryChanged(Message):
        """Emitted when the directory changes."""

        def __init__(self, directory: str, is_valid: bool) -> None:
            self.directory = directory
            self.is_valid = is_valid
            super().__init__()

    directory = reactive("", always_update=True)
    is_browsing = reactive(False)

    def __init__(
        self,
        label: str = "Directory",
        placeholder: str = "Enter directory path...",
        initial_directory: str = "",
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ):
        super().__init__(name=name, id=id, classes=classes)
        self.label_text = label
        self.placeholder = placeholder
        self.directory = initial_directory or os.getcwd()

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Vertical():
            yield Label(self.label_text, classes="directory-label")

            with Horizontal():
                yield Input(
                    value=self.directory,
                    placeholder=self.placeholder,
                    classes="directory-input",
                    id=f"{self.id}_input" if self.id else "directory_input",
                )
                yield Button(
                    "Browse",
                    classes="browse-button",
                    id=f"{self.id}_browse" if self.id else "browse",
                )

            yield Static(
                "",
                classes="status-text",
                id=f"{self.id}_status" if self.id else "status",
            )

            yield DirectoryTree(
                self.directory,
                classes="directory-tree",
                id=f"{self.id}_tree" if self.id else "tree",
            )

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        self.validate_current_directory()

    @on(Input.Changed)
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input field changes."""
        if event.input.id and f"{self.id}_input" in event.input.id:
            self.directory = event.value
            self.validate_current_directory()

    @on(Button.Pressed)
    def on_browse_pressed(self, event: Button.Pressed) -> None:
        """Handle browse button press."""
        if event.button.id and f"{self.id}_browse" in event.button.id:
            self.toggle_browsing()

    @on(DirectoryTree.DirectorySelected)
    def on_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        """Handle directory selection from tree."""
        if event.directory_tree.id and f"{self.id}_tree" in event.directory_tree.id:
            self.directory = str(event.path)
            self.update_input_value()
            self.validate_current_directory()
            self.is_browsing = False

    def toggle_browsing(self) -> None:
        """Toggle the directory tree visibility."""
        self.is_browsing = not self.is_browsing
        try:
            tree = self.query_one(
                f"#{self.id}_tree" if self.id else "#tree", DirectoryTree
            )

            if self.is_browsing:
                tree.add_class("visible")
                # Update tree to current directory if valid
                if os.path.isdir(self.directory):
                    tree.path = self.directory
            else:
                tree.remove_class("visible")
        except Exception:
            # UI elements not yet created, skip update
            pass

    def update_input_value(self) -> None:
        """Update the input field value."""
        try:
            input_widget = self.query_one(
                f"#{self.id}_input" if self.id else "#directory_input", Input
            )
            input_widget.value = self.directory
        except Exception:
            # UI elements not yet created, skip update
            pass

    def validate_current_directory(self) -> None:
        """Validate the current directory and update status."""
        # Check if UI elements have been created yet
        try:
            status_widget = self.query_one(
                f"#{self.id}_status" if self.id else "#status", Static
            )
        except Exception:
            # UI elements not yet created, skip validation
            return

        is_valid, error_message = validate_directory(self.directory)

        if is_valid:
            status_widget.update("✓ Valid directory")
            status_widget.set_class(True, "valid-text")
            status_widget.set_class(False, "error-text")
        else:
            status_widget.update(f"✗ {error_message}")
            status_widget.set_class(False, "valid-text")
            status_widget.set_class(True, "error-text")

        # Emit change event
        self.post_message(self.DirectoryChanged(self.directory, is_valid))

    def watch_directory(self, new_directory: str) -> None:
        """Watch for directory changes."""
        self.validate_current_directory()

    def watch_is_browsing(self, is_browsing: bool) -> None:
        """Watch for browsing state changes."""
        try:
            button = self.query_one(
                f"#{self.id}_browse" if self.id else "#browse", Button
            )
            button.label = "Cancel" if is_browsing else "Browse"
        except Exception:
            # UI elements not yet created, skip update
            pass

    def get_directory(self) -> str:
        """Get the current directory."""
        return self.directory

    def set_directory(self, directory: str) -> None:
        """Set the directory programmatically."""
        self.directory = directory
        self.update_input_value()
        self.validate_current_directory()

    def is_valid(self) -> bool:
        """Check if current directory is valid."""
        is_valid, _ = validate_directory(self.directory)
        return is_valid
