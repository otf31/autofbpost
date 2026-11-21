from textual.app import ComposeResult
from textual.containers import Center, CenterMiddle, Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Link

from constants import APP_VERSION, EMAIL, REPOSITORY_URL, WEBPAGE_URL


class About(ModalScreen):
    def compose(self) -> ComposeResult:
        with Grid():
            with Center():
                yield Label("AutoFBPost", classes="modal-title")
            with Center():
                yield Label(f"Version: {APP_VERSION}", variant="primary")
            with Center():
                yield Label("Developed by: ")
                yield Link("@otf31", url=f"mailto:{EMAIL}", tooltip=EMAIL)
            with CenterMiddle():
                yield Link("Github repository", url=REPOSITORY_URL)
            with Center():
                yield Label("Visit us ")
                yield Link("here", url=WEBPAGE_URL, tooltip=WEBPAGE_URL)
            yield Button("Close", action="app.pop_screen")
