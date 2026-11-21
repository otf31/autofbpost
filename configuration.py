import os

from textual import on
from textual.app import ComposeResult
from textual.containers import Center, Container, Horizontal, VerticalScroll
from textual.validation import ValidationResult, Validator
from textual.widgets import Button, Input, Label, Switch

from common_functions import Config, load_configuration, write_conf_file
from ui import PageHeading, WorkspaceScreen


class ValidDir(Validator):
    def __init__(self, label: str):
        super().__init__()
        self.label = label

    def validate(self, value: str) -> ValidationResult:
        if value == "":
            return self.failure(f"{self.label} cannot be empty")

        if self.is_valid_dir(value):
            return self.success()
        else:
            return self.failure(f"{self.label}: choose an existing folder.")

    @staticmethod
    def is_valid_dir(value: str) -> bool:
        return os.path.isdir(value)


class Configuration(WorkspaceScreen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield PageHeading(
            "Settings", "WORKSPACE / Configure your publishing environment"
        )
        with VerticalScroll(id="settings-body"):
            with Horizontal(classes="setting-card"):
                yield Label("01 / Browser", classes="label")
                with Container(classes="input-container"):
                    yield Input(
                        None,
                        id="cbp",
                        classes="input",
                        placeholder="/usr/bin/google-chrome",
                    )
                    yield Label(
                        "Path to your Chrome / Chromium executable", classes="hint"
                    )
                    yield Label("", id="chrome-status", classes="field-status")
                    yield Label(
                        "", id="chrome-error", classes="field-error", markup=False
                    )
            with Horizontal(classes="setting-card"):
                yield Label("02 / Content library", classes="label")
                with Container(classes="input-container"):
                    yield Input(
                        "",
                        id="pfp",
                        classes="input",
                        select_on_focus=True,
                        placeholder="/home/user/posts",
                        validators=[ValidDir("Content library")],
                        validate_on=["changed", "blur", "submitted"],
                    )
                    yield Label(
                        "Folder containing groups.csv and your post folders",
                        classes="hint",
                    )
                    yield Label("", id="posts-status", classes="field-status")
                    yield Label(
                        "", id="posts-error", classes="field-error", markup=False
                    )
            with Horizontal(classes="setting-card"):
                yield Label("03 / Browser visibility", classes="label")
                with Container(classes="input-container"):
                    yield Switch(False, id="headless", classes="switch")
                    yield Label(
                        "Enable to publish without a visible browser window.",
                        classes="hint",
                    )

        with Center(classes="action-bar"):
            yield Button("Cancel", action="app.pop_screen")
            yield Button("Save", id="save-button", variant="primary")

    def set_config_values(self):
        config = load_configuration()

        chrome_binary = self.query_one("#cbp", Input)
        posts_folder = self.query_one("#pfp", Input)
        headless = self.query_one("#headless", Switch)

        chrome_binary.value = config["CHROME_BINARY_PATH"]
        posts_folder.value = config["POSTS_FOLDER_PATH"]
        headless.value = config["HEADLESS"]

        self.show_content_validation(posts_folder.validate(posts_folder.value))
        self.validate_browser()

    def on_screen_resume(self) -> None:
        self.set_config_values()

    def show_content_validation(self, result: ValidationResult | None) -> bool:
        errors = result.failure_descriptions if result and not result.is_valid else []
        self.query_one("#posts-error", Label).update("\n".join(errors))
        self.query_one("#pfp", Input).set_class(bool(errors), "field-invalid")
        self.query_one("#pfp", Input).set_class(not errors, "field-valid")
        self.query_one("#posts-status", Label).update("Folder found" if not errors else "")
        return not errors

    @on(Input.Changed, "#pfp")
    def content_library_changed(self, event: Input.Changed) -> None:
        self.show_content_validation(event.validation_result)

    @on(Input.Changed, "#cbp")
    def browser_changed(self) -> None:
        self.validate_browser()

    def validate_browser(self) -> bool:
        field = self.query_one("#cbp", Input)
        valid = os.path.isfile(field.value)
        field.set_class(not valid, "field-invalid")
        field.set_class(valid, "field-valid")
        self.query_one("#chrome-error", Label).update("" if valid else "Choose an existing browser executable.")
        self.query_one("#chrome-status", Label).update("Browser file found" if valid else "")
        return valid

    @on(Button.Pressed, "#save-button")
    def save(self):
        posts_folder = self.query_one("#pfp", Input)

        chrome = self.query_one("#cbp", Input)
        chrome_valid = self.validate_browser()
        posts_valid = self.show_content_validation(posts_folder.validate(posts_folder.value))
        if not chrome_valid or not posts_valid:
            (chrome if not chrome_valid else posts_folder).focus()
            return

        chrome_binary_path = self.query_one("#cbp", Input).value
        posts_folder_path = self.query_one("#pfp", Input).value
        headless = self.query_one("#headless", Switch).value

        config: Config = {
            "CHROME_BINARY_PATH": chrome_binary_path,
            "POSTS_FOLDER_PATH": posts_folder_path,
            "HEADLESS": headless,
        }

        write_conf_file(config)

        self.app.notify("Configuration saved", timeout=1)
        self.app.pop_screen()
