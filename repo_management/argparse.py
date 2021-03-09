import argparse
from pathlib import Path


class ArgParseFactory:
    """A factory class to create different types of argparse.ArgumentParser instances

    Attributes
    ----------
    parser: argparse.ArgumentParser
        The instance's ArgumentParser instance, which is created with a default verbose argument

    """

    def __init__(self, description: str = "default") -> None:
        self.parser = argparse.ArgumentParser(description=description)
        self.parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="verbose output",
        )

    @classmethod
    def db2json(self) -> argparse.ArgumentParser:
        """A class method to create an ArgumentParser for the db2json script

        Returns
        -------
        argparse.ArgumentParser
            An ArgumentParser instance specific for the db2json script
        """

        instance = self(
            description="Read a repository database and write all contained pkgbases to one JSON file each."
        )
        instance.parser.add_argument(
            "db_file", type=self.string_to_file_path, default=None, help="the repository database to read"
        )
        instance.parser.add_argument(
            "output_dir",
            type=self.string_to_dir_path,
            default=".",
            help="the directory into which to write the JSON output files (defaults to current directory)",
        )

        return instance.parser

    @classmethod
    def string_to_file_path(self, input_: str) -> Path:
        """Convert an input string into a Path to a file

        Parameters
        ----------
        input_: str
            A string that is used to create a Path

        Raises
        ------
        argparse.ArgumentTypeError:
            If a Path created from input_ does not exist or is not a file

        Returns
        -------
        Path
            A Path instance created from input_
        """

        path = Path(input_)
        if not path.exists():
            raise argparse.ArgumentTypeError(f"the file '{input_}' does not exist")
        if not path.is_file():
            raise argparse.ArgumentTypeError(f"not a file: {input_}")
        return path

    @classmethod
    def string_to_dir_path(self, input_: str) -> Path:
        """Convert an input string into a Path to a directory

        Parameters
        ----------
        input_: str
            A string that is used to create a Path

        Raises
        ------
        argparse.ArgumentTypeError:
            If a Path created from input_ does not exist or is not a directory

        Returns
        -------
        Path
            A Path instance created from input_
        """

        path = Path(input_)
        if not path.exists():
            raise argparse.ArgumentTypeError(f"the directory '{input_}' does not exist")
        if not path.is_dir():
            raise argparse.ArgumentTypeError(f"not a directory: {input_}")
        return path
