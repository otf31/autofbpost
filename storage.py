"""Local file access through fsspec; browser uploads require local paths."""
from fnmatch import fnmatch
from pathlib import Path

from fsspec.implementations.local import LocalFileSystem

local_files = LocalFileSystem()


def matching_files(directory: str, patterns: list[str] | None = None) -> list[str]:
    return sorted(
        entry["name"]
        for entry in local_files.ls(directory, detail=True)
        if entry["type"] == "file"
        and (patterns is None or any(fnmatch(Path(entry["name"]).name, pattern) for pattern in patterns))
    )
