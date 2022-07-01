import os
from argparse import ArgumentParser, ArgumentTypeError
from pathlib import Path

from repod.config.defaults import DEFAULT_DATABASE_COMPRESSION


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
            "-d",
            "--debug",
            action="store_true",
            help="debug output",
        )
        self.parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="verbose output",
        )

    @classmethod
    def repod_file(cls) -> ArgumentParser:
        """A class method to create an ArgumentParser for the repod-file script

        Returns
        -------
        ArgumentParser
            An ArgumentParser instance specific for the repod-file script
        """

        instance = cls(description="File actions for packages, management repository and sync databases.")
        subcommands = instance.parser.add_subparsers(dest="subcommand")

        package = subcommands.add_parser(name="package", help="interact with package files")
        package_subcommands = package.add_subparsers(dest="package")

        package_inspect_parser = package_subcommands.add_parser(name="inspect", help="inspect package files")
        package_inspect_parser.add_argument(
            "file",
            nargs="+",
            type=cls.string_to_file_path,
            help="package files",
        )
        mutual_exclusive_inspect = package_inspect_parser.add_mutually_exclusive_group()
        mutual_exclusive_inspect.add_argument("-B", "--buildinfo", action="store_true", help="only inspect .BUILDINFO")
        mutual_exclusive_inspect.add_argument("-M", "--mtree", action="store_true", help="only inspect .MTREE")
        mutual_exclusive_inspect.add_argument("-P", "--pkginfo", action="store_true", help="only inspect .PKGINFO")
        package_inspect_parser.add_argument("-p", "--pretty", action="store_true", help="pretty print output")
        package_inspect_parser.add_argument(
            "-s",
            "--with-signature",
            action="store_true",
            help="locate and use a signature file for each provided package file",
        )

        package_import_parser = package_subcommands.add_parser(
            name="import",
            help="import package files of the same pkgbase to the management repo",
        )
        package_import_parser.add_argument(
            "file",
            nargs="+",
            type=cls.string_to_file_path,
            help="package files",
        )
        package_import_parser.add_argument(
            "repo",
            type=cls.string_to_dir_path,
            help=("directory in a management repository to write output to"),
        )
        package_import_parser.add_argument(
            "-d",
            "--dry-run",
            action="store_true",
            help="only show output, but do not write output to file",
        )
        package_import_parser.add_argument("-p", "--pretty", action="store_true", help="pretty print output")
        package_import_parser.add_argument(
            "-s",
            "--with-signature",
            action="store_true",
            help="locate and use a signature file for each provided package file",
        )

        management = subcommands.add_parser(name="management", help="interact with management repositories")
        management_subcommands = management.add_subparsers(dest="management")

        management_import_parser = management_subcommands.add_parser(
            name="import",
            help="import from repository sync database",
        )
        management_import_parser.add_argument(
            "file",
            type=cls.string_to_file_path,
            help=("repository sync database"),
        )
        management_import_parser.add_argument(
            "repo",
            type=cls.string_to_dir_path,
            help=("directory in a management repository to write output to"),
        )

        management_export_parser = management_subcommands.add_parser(
            name="export",
            help="export to repository sync database",
        )
        management_export_parser.add_argument(
            "repo",
            type=cls.string_to_dir_path,
            help=("directory in a management repository to read JSON files from"),
        )
        management_export_parser.add_argument(
            "file",
            type=Path,
            help=("repository sync database to write to"),
        )
        management_export_parser.add_argument(
            "-c",
            "--compression",
            choices=["none", "bz2", "bzip2", "gz", "gzip", "lzma", "xz", "zst", "zstandard"],
            default=DEFAULT_DATABASE_COMPRESSION.value,
            help=f"database compression (defaults to {DEFAULT_DATABASE_COMPRESSION.value})",
        )

        syncdb = subcommands.add_parser(name="syncdb", help="interact with repository sync databases")
        syncdb_subcommands = syncdb.add_subparsers(dest="syncdb")

        syncdb_import_parser = syncdb_subcommands.add_parser(
            name="import",
            help="import from management repository",
        )
        syncdb_import_parser.add_argument(
            "repo",
            type=cls.string_to_dir_path,
            help=("directory in a management repository to import from"),
        )
        syncdb_import_parser.add_argument(
            "file",
            type=Path,
            help=("repository sync database to write to"),
        )
        syncdb_import_parser.add_argument(
            "-c",
            "--compression",
            choices=["none", "bz2", "bzip2", "gz", "gzip", "lzma", "xz", "zst", "zstandard"],
            default=DEFAULT_DATABASE_COMPRESSION.value,
            help=f"database compression (defaults to {DEFAULT_DATABASE_COMPRESSION.value})",
        )

        syncdb_export_parser = syncdb_subcommands.add_parser(
            name="export",
            help="export to management repository",
        )
        syncdb_export_parser.add_argument(
            "file",
            type=cls.string_to_file_path,
            help=("repository sync database to read from"),
        )
        syncdb_export_parser.add_argument(
            "repo",
            type=cls.string_to_dir_path,
            help=("directory in a syncdb repository to write JSON files to"),
        )

        schema = subcommands.add_parser(name="schema", help="JSON schema commands")
        schema_subcommands = schema.add_subparsers(dest="schema")

        schema_export_parser = schema_subcommands.add_parser(
            name="export",
            help="export JSON schemas to directory",
        )
        schema_export_parser.add_argument(
            "dir",
            type=cls.string_to_dir_path,
            help=("directory to which to write JSON files to"),
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


def sphinx_repod_file() -> ArgumentParser:
    """Return ArgParseFactory.repod_file() for sphinx."""
    return ArgParseFactory.repod_file()
