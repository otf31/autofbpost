"""Shared presentation components for the terminal workspace."""
from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalGroup
from textual.screen import Screen
from textual.widgets import Label


class Dashboard(Horizontal):
    def on_resize(self, event: events.Resize) -> None:
        self.set_class(event.size.width < 100, "compact")


class WorkspaceScreen(Screen):
    def on_resize(self, event: events.Resize) -> None:
        self.set_class(event.size.width < 100, "compact")


class PageHeading(VerticalGroup):
    def __init__(self, title: str, subtitle: str):
        super().__init__(classes="page-heading")
        self.title = title
        self.subtitle = subtitle

    def compose(self) -> ComposeResult:
        yield Label(self.title, classes="page-title")
        yield Label(self.subtitle, classes="page-subtitle")

