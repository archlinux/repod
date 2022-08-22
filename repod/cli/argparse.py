import os
from argparse import ArgumentParser, ArgumentTypeError
from pathlib import Path

from repod.common.enums import ArchitectureEnum


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
            "-c",
            "--config",
            type=self.string_to_file_path,
            help="configuration file",
        )
        self.parser.add_argument(
            "-d",
            "--debug",
            action="store_true",
            dest="debug_mode",
            help="debug output",
        )
        self.parser.add_argument(
            "-s",
            "--system",
            action="store_true",
            help="system mode",
        )
        self.parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            dest="verbose_mode",
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

        repo_parser = subcommands.add_parser(name="repo", help="interact with repositories")
        repo_subcommands = repo_parser.add_subparsers(dest="repo")

        repo_importdb_parser = repo_subcommands.add_parser(
            name="importdb",
            help="import state from a repository sync database",
        )
        repo_importdb_parser.add_argument(
            "file",
            type=cls.string_to_file_path,
            help=("repository sync database"),
        )
        repo_importdb_parser.add_argument(
            "name",
            type=Path,
            help=("name of repository to import to"),
        )
        repo_importdb_parser.add_argument(
            "-a",
            "--architecture",
            type=ArchitectureEnum,
            help=(
                "target a repository with a specific architecture "
                "(if multiple of the same name but differing architecture exist)"
            ),
        )
        mutual_exclusive_repo_import = repo_importdb_parser.add_mutually_exclusive_group()
        mutual_exclusive_repo_import.add_argument(
            "-D",
            "--debug",
            action="store_true",
            help="import to debug repository",
        )
        mutual_exclusive_repo_import.add_argument(
            "-S",
            "--staging",
            action="store_true",
            help="import to staging repository",
        )
        mutual_exclusive_repo_import.add_argument(
            "-T",
            "--testing",
            action="store_true",
            help="import to testing repository",
        )

        repo_importpkg_parser = repo_subcommands.add_parser(
            name="importpkg",
            help="import packages of the same pkgbase to a repo",
        )
        repo_importpkg_parser.add_argument(
            "file",
            nargs="+",
            type=cls.string_to_file_path,
            help="package files",
        )
        repo_importpkg_parser.add_argument(
            "name",
            type=Path,
            help=("name of repository to import to"),
        )
        repo_importpkg_parser.add_argument(
            "-a",
            "--architecture",
            type=ArchitectureEnum,
            help=(
                "target a repository with a specific architecture "
                "(if multiple of the same name but differing architecture exist)"
            ),
        )
        repo_importpkg_parser.add_argument(
            "-d",
            "--dry-run",
            action="store_true",
            help="only show output, but do not write output to file",
        )
        repo_importpkg_parser.add_argument(
            "-p", "--pretty", action="store_true", help="pretty print output (only applies to dry-run mode)"
        )
        repo_importpkg_parser.add_argument(
            "-s",
            "--with-signature",
            action="store_true",
            help="locate and use a signature file for each provided package file",
        )
        mutual_exclusive_repo_importpkg = repo_importpkg_parser.add_mutually_exclusive_group()
        mutual_exclusive_repo_importpkg.add_argument(
            "-D",
            "--debug",
            action="store_true",
            help="import to debug repository",
        )
        mutual_exclusive_repo_importpkg.add_argument(
            "-S",
            "--staging",
            action="store_true",
            help="import to staging repository",
        )
        mutual_exclusive_repo_importpkg.add_argument(
            "-T",
            "--testing",
            action="store_true",
            help="import to testing repository",
        )

        repo_writedb_parser = repo_subcommands.add_parser(
            name="writedb",
            help="export state to repository sync database",
        )
        repo_writedb_parser.add_argument(
            "name",
            type=Path,
            help=("name of repository to write to"),
        )
        repo_writedb_parser.add_argument(
            "-a",
            "--architecture",
            type=ArchitectureEnum,
            help=(
                "target a repository with a specific architecture "
                "(if multiple of the same name but differing architecture exist)"
            ),
        )
        mutual_exclusive_repo_export = repo_writedb_parser.add_mutually_exclusive_group()
        mutual_exclusive_repo_export.add_argument(
            "-D",
            "--debug",
            action="store_true",
            help="export from debug repository",
        )
        mutual_exclusive_repo_export.add_argument(
            "-S",
            "--staging",
            action="store_true",
            help="export from staging repository",
        )
        mutual_exclusive_repo_export.add_argument(
            "-T",
            "--testing",
            action="store_true",
            help="export from testing repository",
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
