"""Simplifies file handling."""

import csv
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from io import TextIOWrapper
from pathlib import Path

from .loghandler import setup_logger

logger = setup_logger(__name__)


class FileMode(Enum):
    """The mode how the file will be open.

    Example: Read, Write etc.
    """

    READ = "r"
    WRITE = "w"


class OverWrite(Enum):
    """Declare to overwrite a file."""

    YES = True
    NO = False


@dataclass
class FileHandler:
    """Provides multiple function for working with files."""

    path: str | Path

    def __post_init__(self) -> None:
        """Set attributes after initilization."""
        if isinstance(self.path, str):
            self.path = Path(self.path)

    def _open_file(self, filemode: FileMode, func: Callable, data: dict | list | None = None) -> list | dict:
        """Open a file and process that data with a given function."""
        try:
            with Path.open(self.path, mode=filemode.value, encoding="utf-8") as file:
                if filemode.name == "READ":
                    return func(file)
                if filemode.name == "WRITE":
                    func(file, data)

        except (FileNotFoundError, IsADirectoryError) as err:
            logger.error(f"{err.strerror}: '{err.filename}'")  # noqa: TRY400
            sys.exit(1)

    def _load_json(self, data: TextIOWrapper) -> dict:
        """Load json file."""
        try:
            json_data = json.load(data)
        except json.decoder.JSONDecodeError as err:
            logger.error(f"Invalid json file format. Error at line {err.lineno} in '{data.name}'")
            sys.exit(1)
        else:
            logger.debug(f"Successfully loaded '{data.name}'")
            return json_data

    def _save_json(self, file: TextIOWrapper, data: dict) -> None:
        """Save json file."""
        try:
            json_object = json.dumps(data, indent=4)
            file.write(json_object)
        except Exception:
            logger.error(f"An undefined error occoured, while write file {file}")
        else:
            logger.debug(f"Successfully saved '{file.name}'")

    def _load_csv(self, data: TextIOWrapper) -> list[dict]:
        """Load csv file."""
        return list(csv.DictReader(data, delimiter=","))

    def _load_txt(self, data: TextIOWrapper) -> str:
        """Load text file."""
        return data.read()

    def read(self) -> dict | list[dict] | str:
        """Read different file formats.

        supported file formats: .json, .csv .txt
        """
        suffix = self.path.suffix
        if suffix == ".json":
            return self._open_file(FileMode.READ, self._load_json)
        if suffix == ".csv":
            return self._open_file(FileMode.READ, self._load_csv)
        if suffix == ".txt":
            return self._open_file(FileMode.READ, self._load_txt)

        logger.error(f"File suffix '{suffix}' not supported.")
        sys.exit(1)

    def write(self, data: dict | list, overwrite: OverWrite) -> None:
        """Write different file formats.

        supported file formats: .json, .csv
        """
        suffix = self.path.suffix
        if not self.path.exists() or overwrite.value:
            if suffix == ".json":
                self._open_file(FileMode.WRITE, self._save_json, data)
            else:
                logger.error(f"File suffix '{suffix}' not supported.")
                sys.exit(1)


if __name__ == "__main__":
    json_file = FileHandler(".test/test.json")
    json_config = json_file.read()
    print(json_config)

    csv_file = FileHandler(".test/test.csv")
    csv_config = csv_file.read()
    print(csv_config)
