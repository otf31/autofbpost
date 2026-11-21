import json
import secrets
from asyncio import sleep
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Callable, Literal, TypedDict

import rtoml
from platformdirs import user_config_dir
from rich.console import group
from rich.panel import Panel
from typing_extensions import TypeVar

from constants import APP_NAME, CONFIG_FILE_PATH, DEFAULT_CONFIG
from storage import local_files


class Config(TypedDict):
    CHROME_BINARY_PATH: str
    POSTS_FOLDER_PATH: str
    HEADLESS: bool


class StyledPanel(Panel):
    """
    A styled panel with a message and an optional title.
    :param msg: Message inside the panel.
    :param title: Optional panel title.
    :param msg_type: info, error, warning or success.
        If error, the application will exit.
    """

    def __init__(
        self,
        msg: Any,
        title=None,
        msg_type: Literal["info", "error", "warning", "success"] = "info",
    ):
        super().__init__(msg, title=title, expand=False)

        self.msg_type = msg_type
        self.title = title
        self.msg_type = msg_type

        if msg_type == "error":
            self.style = "red"
        elif msg_type == "warning":
            self.style = "yellow"
        elif msg_type == "success":
            self.style = "green"


T = TypeVar("T")


# def print_panels_group[T]( -> doesn't work in executable file
def panels_group(
    iterable: list[T],
    extract_msg: Callable[[T], str],
    title: str = None,
    children_msg_type: Literal["info", "error", "warning", "success"] = "info",
) -> Panel:
    """
    Print a group of panels.
    :param iterable: The list of items to iterate.
    :param extract_msg: A callable that extracts the message from the item.
    :param title: The title of the main panel.
    :param children_msg_type: The type of the children panels. Default is info.
    """

    @group()
    def get_panels():
        for i in iterable:
            msg = extract_msg(i)

            yield StyledPanel(str(msg), msg_type=children_msg_type)

    return Panel(get_panels(), title=title)


async def wait_random_seconds(start: int, end: int = None) -> None:
    """
    Wait a random time between start and end seconds.
    :param start: The start time in seconds
    :param end: The end time in seconds, if None, the end time will be equal to start time
    and the function will wait exactly the start time.
    """
    if end is None:
        end = start

    await sleep(secrets.randbelow(end - start + 1) + start)


def configuration_path() -> str:
    """Keep the per-user location previously used by UserConfigFS."""
    return str(Path(user_config_dir(APP_NAME, appauthor=None)) / CONFIG_FILE_PATH)


def validate_conf_file() -> None:
    """
    Create if the configuration file does not exists and write with the default
    configuration. If the configuration file exists but it does not have valid keys,
    it will be overwritten with the default configuration.
    """
    path = configuration_path()
    if not local_files.exists(path):
        write_conf_file(DEFAULT_CONFIG)
        return
    try:
        with local_files.open(path, "rt", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except JSONDecodeError:
        write_conf_file(DEFAULT_CONFIG)
    else:
        if not isinstance(config, dict) or not all(key in config for key in DEFAULT_CONFIG):
            write_conf_file(DEFAULT_CONFIG)


def load_configuration() -> Config:
    """
    Load a configuration file.
    :return: The configuration dictionary.
    """
    validate_conf_file()
    with local_files.open(configuration_path(), "rt", encoding="utf-8") as config_file:
        return json.load(config_file)


def write_conf_file(config: Config) -> None:
    """
    Write a configuration file.
    :param config: The configuration dictionary.
    """
    path = configuration_path()
    local_files.makedirs(str(Path(path).parent), exist_ok=True)
    with local_files.open(path, "wt", encoding="utf-8") as config_file:
        json.dump(config, config_file, indent=4)


def get_locales_fb_strings(lang: str) -> dict[str, dict[str, str] | str]:
    """
    Get the Facebook strings for a specific language.
    :param lang: The language code.
    :return: The Facebook strings depending on the language.
    """
    path = Path(get_executable_dir_location()) / "locales_fb" / f"{lang}.toml"
    with local_files.open(str(path), "rt", encoding="utf-8") as locale_file:
        return rtoml.load(locale_file)


def get_executable_dir_location() -> str:
    """
    Get the executable location.
    :return: The executable location.
    """
    return str(Path(__file__).resolve().parent)
