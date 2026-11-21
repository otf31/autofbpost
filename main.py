import math

import httpx
from packaging.version import Version
from textual import events, on
from textual.app import App, ComposeResult
from textual.containers import Center, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Footer, Label

from about import About
from common_functions import validate_conf_file
from configuration import Configuration
from constants import APP_VERSION, DEV_MODE, GITHUB_RELEASE_API, WEBPAGE_URL
from history import History
from machine_id import MachineId
from manual_mode import ManualMode
from publish import Publish
from ui import Dashboard


class Autofbpost(App[None]):
    CSS_PATH = "styles.tcss"

    def on_mount(self):
        self.theme = "textual-dark"

    AUTO_FOCUS = None
    ENABLE_COMMAND_PALETTE = False
    SCREENS = {
        "publish": Publish,
        "manual-mode": ManualMode,
        "machine-id": MachineId,
        "configuration": Configuration,
        "history": History,
        "about": About,
    }
    BINDINGS = {
        ("h", "push_screen('history')", "History"),
        ("s", "push_screen('configuration')", "Settings"),
        ("a", "push_screen('about')", "About"),
    }

    def compose(self) -> ComposeResult:
        with Dashboard(id="home"):
            with Vertical(id="navigation"):
                yield Label("[bold]AF[/] / workspace", id="nav-brand")
                yield Label("WORKSPACE", classes="nav-caption")
                yield Button("History", action="app.push_screen('history')")
                yield Button("Settings", action="app.push_screen('configuration')")
                yield Label("RESOURCES", classes="nav-caption")
                yield Button("About", action="app.push_screen('about')")
                yield Button("Device ID", id="id")
                yield Button("Exit", action="app.quit")
                yield Label(f"AutoFBPost\nv{APP_VERSION}", id="nav-version")
            with VerticalScroll(id="workspace"):
                with Horizontal(id="masthead"):
                    yield Label("AutoFBPost", id="brand")
                    yield Label("GROUP PUBLISHING", id="workspace-tag")
                yield Label("Publishing workspace", id="hero-title")
                yield Label(
                    "Manage your content and Facebook groups.", id="hero-description"
                )
                with Center(classes="home-row"):
                    with Vertical(id="buttons"):
                        yield Label("01 / PUBLISH", classes="card-kicker")
                        yield Label("New publication", classes="card-title")
                        yield Label(
                            "Review images, descriptions and destinations before you go live.",
                            classes="card-description",
                        )
                        yield Button(
                            "Create a publication  →", id="publish", variant="primary"
                        )
                with Center(classes="home-row"):
                    with Horizontal(id="connection-card"):
                        with Vertical(id="connection-copy"):
                            yield Label("02 / CONNECT", classes="card-kicker")
                            yield Label("Connect your account", classes="card-title")
                            yield Label(
                                "Sign in or switch profiles in manual mode.",
                                classes="card-description",
                            )
                        yield Button("Open browser", id="manual-mode")
        yield Footer()

    @on(Button.Pressed, "#publish")
    def show_publish_screen(self):
        self.push_screen(Publish())

    @on(Button.Pressed, "#manual-mode")
    def show_manual_mode_screen(self):
        self.push_screen(ManualMode())

    @on(Button.Pressed, "#id")
    def show_id_screen(self):
        self.push_screen(MachineId())

    async def on_load(self):  # noqa
        # Write default configuration if there is no configuration file
        validate_conf_file()

        if not DEV_MODE:
            self.run_worker(self.check_updates())

    async def check_updates(self):
        async with httpx.AsyncClient() as client:
            res = await client.get(GITHUB_RELEASE_API, timeout=5)
            data = res.json()

        latest_tag = data["tag_name"].lstrip("v")  # remove "v"

        if Version(latest_tag) > Version(APP_VERSION):
            self.notify(
                f"{latest_tag} (current: {APP_VERSION})\n"
                f"Press [underline]u[/] to open download page",
                title="Update available!",
                severity="warning",
                timeout=math.inf,
            )
        else:
            self.notify("You are up to date")

    def open_website(self) -> None:
        self.open_url(WEBPAGE_URL)

    async def on_key(self, event: events.Key):
        if event.key.lower() == "u":
            self.open_website()


if __name__ == "__main__":
    app = Autofbpost()

    app.run()
