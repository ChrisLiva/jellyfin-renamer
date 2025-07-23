"""File browser screen for advanced file selection."""

import os
from pathlib import Path
from typing import List, Set

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, DirectoryTree, Input, Label, Static, Tree
from textual.widgets.tree import TreeNode

from ..utils.tui_helpers import format_file_size, get_file_info, is_video_file


class FileBrowserScreen(Screen):
    """Screen for browsing and selecting files in a tree view."""

    BINDINGS = [
        Binding("f5", "refresh", "Refresh", show=True),
        Binding("ctrl+a", "select_all", "Select All", show=True),
        Binding("ctrl+d", "deselect_all", "Deselect All", show=True),
        Binding("escape", "back", "Back", show=True),
    ]

    DEFAULT_CSS = """
    FileBrowserScreen {
        background: $background;
    }
    
    .browser-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        background: $surface;
        margin: 1;
        padding: 1;
    }
    
    .browser-controls {
        margin: 1;
        padding: 1;
        border: solid $accent;
    }
    
    .search-container {
        margin: 1;
    }
    
    .tree-container {
        border: solid $accent;
        margin: 1;
        height: 1fr;
    }
    
    .info-panel {
        border: solid $accent;
        margin: 1;
        padding: 1;
        height: 8;
    }
    
    .action-buttons {
        margin: 1;
        text-align: center;
    }
    
    .select-button {
        background: $success;
        margin: 0 1;
    }
    
    .cancel-button {
        background: $error;
        margin: 0 1;
    }
    
    .video-file-node {
        color: $success;
        text-style: bold;
    }
    
    .directory-node {
        color: $warning;
        text-style: bold;
    }
    
    .selected-node {
        background: $primary;
        color: $text;
    }
    
    .breadcrumb {
        background: $surface;
        color: $primary;
        padding: 1;
        margin: 1;
        text-style: bold;
    }
    """

    # Reactive state
    current_directory = reactive("")
    selected_files: Set[str] = reactive(set())
    search_term = reactive("")

    def __init__(
        self, initial_directory: str = "", selected_files: Set[str] = None
    ) -> None:
        super().__init__()
        self.current_directory = initial_directory or os.getcwd()
        self.selected_files = selected_files or set()
        self.file_tree_data = {}  # Store file information

    def compose(self) -> ComposeResult:
        """Create child widgets for the file browser."""
        with Vertical():
            # Title
            yield Static(
                "📁 File Browser\nSelect media files to process",
                classes="browser-title",
            )

            # Breadcrumb
            yield Static("", id="breadcrumb", classes="breadcrumb")

            # Controls
            with Container(classes="browser-controls"):
                with Horizontal():
                    yield Label("Search:")
                    yield Input(
                        placeholder="Search files...",
                        id="search_input",
                        classes="search-container",
                    )

                with Horizontal():
                    yield Button("📂 Up Directory", id="up_btn")
                    yield Button("🔄 Refresh", id="refresh_btn")
                    yield Button("☑️ Select All Video", id="select_all_btn")
                    yield Button("☐ Deselect All", id="deselect_all_btn")

            # File tree
            with Container(classes="tree-container"):
                yield Tree("", id="file_tree")

            # Info panel
            with Container(classes="info-panel"):
                yield Label("Selection Info", classes="section-title")
                yield Static("No files selected", id="selection_info")

            # Action buttons
            with Horizontal(classes="action-buttons"):
                yield Button(
                    "✅ Use Selected Files", id="select_btn", classes="select-button"
                )
                yield Button("❌ Cancel", id="cancel_btn", classes="cancel-button")

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        self.update_breadcrumb()
        self.populate_tree()
        self.update_selection_info()

    @on(Input.Changed, "#search_input")
    def on_search_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        self.search_term = event.value
        self.populate_tree()

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "up_btn":
            self.action_up_directory()
        elif event.button.id == "refresh_btn":
            self.action_refresh()
        elif event.button.id == "select_all_btn":
            self.action_select_all()
        elif event.button.id == "deselect_all_btn":
            self.action_deselect_all()
        elif event.button.id == "select_btn":
            self.action_use_selected()
        elif event.button.id == "cancel_btn":
            self.action_back()

    @on(Tree.NodeSelected)
    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection."""
        node = event.node
        file_path = str(node.data) if node.data else ""

        if os.path.isfile(file_path):
            # Toggle file selection
            if file_path in self.selected_files:
                self.selected_files.remove(file_path)
                node.remove_class("selected-node")
            else:
                self.selected_files.add(file_path)
                node.add_class("selected-node")

            self.update_selection_info()
        elif os.path.isdir(file_path):
            # Navigate to directory
            self.current_directory = file_path
            self.update_breadcrumb()
            self.populate_tree()

    def populate_tree(self) -> None:
        """Populate the tree with files and directories."""
        tree = self.query_one("#file_tree", Tree)
        tree.clear()

        if not os.path.exists(self.current_directory):
            tree.root.add_leaf("Directory not found")
            return

        try:
            # Get directory contents
            items = []
            for item in os.listdir(self.current_directory):
                item_path = os.path.join(self.current_directory, item)

                # Skip hidden files unless explicitly searching for them
                if item.startswith(".") and not self.search_term:
                    continue

                # Apply search filter
                if self.search_term and self.search_term.lower() not in item.lower():
                    continue

                items.append((item, item_path))

            # Sort: directories first, then files
            items.sort(key=lambda x: (not os.path.isdir(x[1]), x[0].lower()))

            # Add items to tree
            for item_name, item_path in items:
                if os.path.isdir(item_path):
                    # Directory
                    node = tree.root.add(f"📁 {item_name}", data=item_path)
                    node.add_class("directory-node")
                elif is_video_file(item_name):
                    # Video file
                    file_info = get_file_info(item_path)
                    display_name = f"🎬 {item_name} ({file_info['size_formatted']})"
                    node = tree.root.add_leaf(display_name, data=item_path)
                    node.add_class("video-file-node")

                    # Mark as selected if already in selection
                    if item_path in self.selected_files:
                        node.add_class("selected-node")
                else:
                    # Other file
                    node = tree.root.add_leaf(f"📄 {item_name}", data=item_path)

            # Expand root by default
            tree.root.expand()

        except PermissionError:
            tree.root.add_leaf("Permission denied")
        except Exception as e:
            tree.root.add_leaf(f"Error: {str(e)}")

    def update_breadcrumb(self) -> None:
        """Update the breadcrumb navigation."""
        breadcrumb = self.query_one("#breadcrumb", Static)

        # Create a shortened path for display
        path_parts = Path(self.current_directory).parts
        if len(path_parts) > 4:
            display_path = os.path.join(path_parts[0], "...", *path_parts[-3:])
        else:
            display_path = self.current_directory

        breadcrumb.update(f"📍 Current Directory: {display_path}")

    def update_selection_info(self) -> None:
        """Update the selection information panel."""
        info_widget = self.query_one("#selection_info", Static)

        if not self.selected_files:
            info_widget.update("No files selected")
            return

        # Calculate total size and count
        total_size = 0
        video_count = 0

        for file_path in self.selected_files:
            if os.path.exists(file_path) and is_video_file(file_path):
                file_info = get_file_info(file_path)
                total_size += file_info["size"]
                video_count += 1

        size_text = format_file_size(total_size)
        info_widget.update(
            f"Selected: {video_count} video files\n"
            f"Total size: {size_text}\n"
            f"Ready for processing: {'Yes' if video_count > 0 else 'No'}"
        )

    def action_up_directory(self) -> None:
        """Navigate to parent directory."""
        parent_dir = os.path.dirname(self.current_directory)
        if parent_dir != self.current_directory:  # Avoid infinite loop at root
            self.current_directory = parent_dir
            self.update_breadcrumb()
            self.populate_tree()

    def action_refresh(self) -> None:
        """Refresh the current directory."""
        self.populate_tree()
        self.update_selection_info()

    def action_select_all(self) -> None:
        """Select all video files in current directory."""
        try:
            for item in os.listdir(self.current_directory):
                item_path = os.path.join(self.current_directory, item)
                if os.path.isfile(item_path) and is_video_file(item):
                    self.selected_files.add(item_path)

            self.populate_tree()  # Refresh to show selections
            self.update_selection_info()
        except (PermissionError, OSError):
            pass

    def action_deselect_all(self) -> None:
        """Deselect all files."""
        self.selected_files.clear()
        self.populate_tree()  # Refresh to show deselections
        self.update_selection_info()

    def action_use_selected(self) -> None:
        """Use the selected files and return to main screen."""
        # Filter to only video files that actually exist
        valid_files = [
            file_path
            for file_path in self.selected_files
            if os.path.exists(file_path) and is_video_file(file_path)
        ]

        # Pass the selection back to the calling screen
        self.dismiss(valid_files)

    def action_back(self) -> None:
        """Go back without using selection."""
        self.dismiss(None)

    def watch_current_directory(self, new_directory: str) -> None:
        """Watch for directory changes."""
        self.update_breadcrumb()
        self.populate_tree()

    def watch_selected_files(self, new_selection: Set[str]) -> None:
        """Watch for selection changes."""
        self.update_selection_info()

    def get_selected_files(self) -> List[str]:
        """Get list of selected file paths."""
        return list(self.selected_files)
