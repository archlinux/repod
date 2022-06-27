import os
from argparse import ArgumentParser, ArgumentTypeError
from pathlib import Path


class ArgParseFactory:
    """A factory class to create different types of ArgumentParser instances

    Attributes
    ----------
    parser: ArgumentParser
        The instance's ArgumentParser instance, which is created with a default verbose argument

    """

    def __init__(self, description: str = "default") -> None:
        self.parser = ArgumentParser(description=description)
        self.parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="verbose output",
        )

    @classmethod
    def db2json(cls) -> ArgumentParser:
        """A class method to create an ArgumentParser for the db2json script

        Returns
        -------
        ArgumentParser
            An ArgumentParser instance specific for the db2json script
        """

        instance = cls(description="Read a repository database and write all contained pkgbases to one JSON file each.")
        instance.parser.add_argument(
            "db_file", type=cls.string_to_file_path, default=None, help="the repository database to read"
        )
        instance.parser.add_argument(
            "output_dir",
            type=cls.string_to_dir_path,
            default=".",
            help="the directory into which to write the JSON output files (defaults to current directory)",
        )

        return instance.parser

    @classmethod
    def json2db(cls) -> ArgumentParser:
        """A class method to create an ArgumentParser for the json2db script

        Returns
        -------
        ArgumentParser
            An ArgumentParser instance specific for the json2db script
        """

        instance = cls(
            description="Read a set of JSON files from a directory and create a repository database from them."
        )
        instance.parser.add_argument(
            "-f",
            "--files",
            action="store_true",
            help="create a .files database instead of a .db database",
        )
        instance.parser.add_argument(
            "input_dir",
            type=cls.string_to_dir_path,
            default=".",
            help="the directory from which to read the JSON files (defaults to current directory)",
        )
        instance.parser.add_argument(
            "db_file",
            type=cls.string_to_writable_file_path,
            default=None,
            help="the repository database to write to (the parent directory needs to exist)",
        )

        return instance.parser

    @classmethod
    def string_to_writable_file_path(cls, input_: str) -> Path:
        """Convert an input string into a Path to a file

        This method checks whether an (existing) file is writable. If the file does not exist the parent directory is
        checked for existence and whether it is writable.

        Parameters
        ----------
        input_: str
            A string that is used to create a Path

        Raises
        ------
        ArgumentTypeError:
            If a Path created from input_ does not exist or is not a file

        Returns
        -------
        Path
            A Path instance created from input_
        """

        path = Path(input_)
        if path.exists():
            if not path.is_file():
                raise ArgumentTypeError(f"not a file: '{input_}'")
            if not os.access(path, os.W_OK):
                raise ArgumentTypeError(f"the file '{input_}' is not writable")
        else:
            if not path.parent.exists():
                raise ArgumentTypeError(f"the parent directory of '{input_}' does not exist")
            if not path.parent.is_dir():
                raise ArgumentTypeError(f"parent is not a directory: '{input_}'")
            if not os.access(path.parent, os.W_OK):
                raise ArgumentTypeError(f"the parent directory of '{input_}' is not writable")
        return path

    @classmethod
    def string_to_file_path(cls, input_: str) -> Path:
        """Convert an input string into a Path to a file

        Parameters
        ----------
        input_: str
            A string that is used to create a Path

        Raises
        ------
        ArgumentTypeError:
            If a Path created from input_ does not exist or is not a file

        Returns
        -------
        Path
            A Path instance created from input_
        """

        path = Path(input_)
        if not path.exists():
            raise ArgumentTypeError(f"the file '{input_}' does not exist")
        if not path.is_file():
            raise ArgumentTypeError(f"not a file: {input_}")
        return path

    @classmethod
    def string_to_dir_path(cls, input_: str) -> Path:
        """Convert an input string into a Path to a directory

        Parameters
        ----------
        input_: str
            A string that is used to create a Path

        Raises
        ------
        ArgumentTypeError:
            If a Path created from input_ does not exist or is not a directory

        Returns
        -------
        Path
            A Path instance created from input_
        """

        path = Path(input_)
        if not path.exists():
            raise ArgumentTypeError(f"the directory '{input_}' does not exist")
        if not path.is_dir():
            raise ArgumentTypeError(f"not a directory: {input_}")
        return path
