import csv
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Center, Container
from textual.widgets import Button, DataTable, Label

from common_functions import load_configuration
from constants import HiSTORY_FILE_PATH
from storage import local_files
from ui import PageHeading, WorkspaceScreen


class History(WorkspaceScreen):
    DEFAULT_CSS = """
    History {
        padding: 1 2;

        Container {
            align-horizontal: center;
        }

        DataTable {
            height: 1fr;
            width: auto;
        }

        Center {
            margin-top: 1;
        }
    }
    """

    def __init__(self):
        super().__init__()

        config = load_configuration()
        self.posts_folder_path = config["POSTS_FOLDER_PATH"]

    def compose(self) -> ComposeResult:
        yield PageHeading("History", "WORKSPACE / A record of your publishing activity")
        with Container(id="history-panel"):
            yield Label("ACTIVITY ARCHIVE", classes="section-title")
            yield DataTable(zebra_stripes=True)
            yield Label("No publications yet\nYour publishing activity will appear here after your first run.", id="history-empty", classes="empty-state", markup=False)
        with Center(classes="action-bar"):
            yield Button("Close", action="app.pop_screen")

    def load(self):
        data_table = self.query_one(DataTable)

        # Clear data table, rows and columns
        data_table.clear(columns=True)

        empty = self.query_one("#history-empty", Label)
        try:
            with local_files.open(str(Path(self.posts_folder_path) / HiSTORY_FILE_PATH), "rt", encoding="utf-8", newline="") as history_file:
                reader = csv.reader(history_file, delimiter=";")
                header = next(reader, None)
                if header:
                    data_table.add_columns(*header)
                    for row in reader:
                        if row:
                            data_table.add_row(*row)
            empty.update("No publications yet\nYour publishing activity will appear here after your first run.")
        except (OSError, UnicodeError, csv.Error):
            empty.update("No history available\nCheck your content library in Settings, or publish to create your first record.")
        data_table.display = data_table.row_count > 0
        empty.display = not data_table.display

    def on_screen_resume(self):
        self.load()
