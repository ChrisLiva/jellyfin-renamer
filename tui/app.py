"""Main TUI application for jellyfin-renamer."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from .screens.main_screen import MainScreen


class JellyfinRenamerApp(App):
    """Main Textual application for jellyfin-renamer."""

    TITLE = "Jellyfin Media Renamer"
    SUB_TITLE = "Organize your media files beautifully"
    CSS_PATH = "app.tcss"
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True, priority=True),
        Binding("ctrl+c", "quit", "Quit", show=False, priority=True),
        Binding("f1", "help", "Help", show=True),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app starts."""
        self.push_screen(MainScreen())

    def action_help(self) -> None:
        """Show help information."""
        from textual.containers import Container
        from textual.screen import Screen
        from textual.widgets import Static

        class HelpScreen(Screen):
            BINDINGS = [
                Binding("escape", "app.pop_screen", "Back"),
                Binding("q", "app.quit", "Quit"),
            ]

            def compose(self) -> ComposeResult:
                with Container(classes="main-container"):
                    yield Static(
                        "Jellyfin Media Renamer - Help\n\n"
                        "Global Keyboard Shortcuts:\n"
                        "  Q / Ctrl+C  - Quit application\n"
                        "  F1          - Show this help\n"
                        "  ESC         - Go back/close modal\n\n"
                        "Main Screen:\n"
                        "  F2          - Browse source directory\n"
                        "  F3          - Browse target directory\n"
                        "  F5          - Start processing\n"
                        "  Tab         - Navigate between fields\n"
                        "  Enter       - Activate focused element\n\n"
                        "File Browser:\n"
                        "  F5          - Refresh file list\n"
                        "  ESC         - Back to main screen\n\n"
                        "Directory Picker:\n"
                        "  Enter       - Select directory/expand\n"
                        "  ESC         - Cancel selection\n"
                        "  Arrow Keys  - Navigate\n\n"
                        "Press ESC to close this help.",
                        classes="title",
                    )

        self.push_screen(HelpScreen())

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
