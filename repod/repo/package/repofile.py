from itertools import zip_longest
from logging import debug, info
from pathlib import Path
from re import Match, fullmatch
from shutil import copy2
from typing import Any, Dict, List

from pydantic import BaseModel, root_validator

from repod.common.enums import RepoFileEnum
from repod.common.regex import PACKAGE_PATH, PACKAGE_SIGNATURE_PATH
from repod.errors import RepoManagementFileError


def shared_base_path(path_a: Path, path_b: Path) -> Path:
    """Return the shared base path of two absolute paths

    Parameters
    ----------
    path_a: Path
        An absolute path
    path_b: Path
        An absolute path

    Raises
    ------
    ValueError
        If either path_a or path_b are not absolute paths

    Returns
    -------
    Path
        The shared base path of path_a and path_b
    """

    debug(f"Calculating the shared base path of {path_a} and {path_b}...")
    for path in (path_a, path_b):
        if not path.is_absolute():
            raise ValueError(f"The path {path} is not absolute!")

    output_list: List[str] = []
    # NOTE: we skip branch check here, because coveragepy does not detect that we can never have any of the Path objects
    # return an empty list of parts, as they are ensured to be absolute
    for part_a, part_b in zip_longest(path_a.parts, path_b.parts, fillvalue=None):  # pragma: no branch
        if part_a is not None and part_b is not None and part_a == part_b:
            output_list.append(part_a)
        else:
            break

    debug(f"Calculated shared base path: {Path(*output_list)}")
    return Path(*output_list)


def relative_to_shared_base(path_a: Path, path_b: Path) -> Path:
    """Return a Path to path_a, relative to the shared base path of path_a and path_b

    This function calls shared_base_path() to determine the shared base path of path_a and path_b.

    Parameters
    ----------
    path_a: Path
        An absolute path
    path_b: Path
        An absolute path

    Returns
    -------
    Path
        The path to path_a, relative to the shared base path of path_a and path_b
    """

    debug(f"Calculating a path relative to the shared base path of {path_a} and {path_b}...")
    shared_base = shared_base_path(path_a=path_a, path_b=path_b)
    parent_distance = len(path_b.parent.parts) - len(shared_base.parts)
    debug(f"The parent distance of {path_a} to {shared_base} is {parent_distance}.")

    return_path: Path
    if parent_distance > 0:
        return_path = Path(*(["../"] * parent_distance)) / path_a.relative_to(shared_base)
    else:
        return_path = path_a.relative_to(shared_base)

    debug(f"Calculated path relative to the shared base path {shared_base}: {return_path}")
    return return_path


class RepoFile(BaseModel):
    """Class to interact with files in a repository

    Attributes
    ----------
    file_type: RepoFileEnum
        A RepoFileEnum member defining which type of file is targeted
    file_path: Path
        The path to the file
    symlink_path: Path
        The path to a symlink to file_path
    """

    file_type: RepoFileEnum
    file_path: Path
    symlink_path: Path

    @classmethod
    def validate_path(cls, path: Path, regex: str) -> None:
        """Validate path to match regex

        Parameters
        ----------
        path: Path
            A path to match
        regex: str
            A regular expression to match path against

        Raises
        ------
        ValueError
            If path does not match regex
        """

        if not isinstance(fullmatch(regex, str(path)), Match):
            raise ValueError(f"The path {path} does not match the regular expression {regex}.")

    @classmethod
    def get_file_type_regex(cls, file_type: RepoFileEnum) -> str:
        """Return the regular expression associated with a given RepodFileEnum member

        Parameters
        ----------
        file_type: RepoFileEnum
            A member of RepoFileEnum

        Returns
        -------
        str
            The regular expression string associated with file_type
        """

        match file_type:
            case RepoFileEnum.PACKAGE:
                return rf"^{PACKAGE_PATH}$"
            case RepoFileEnum.PACKAGE_SIGNATURE:
                return rf"^{PACKAGE_SIGNATURE_PATH}$"
            case _:
                raise RuntimeError(f"Invalid RepoFile.file_type encountered: {file_type}")

    @root_validator
    def validate_paths(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validator for absolute Paths

        Parameters
        ----------
        values: Dict[str, Any]
            A dict with all values of the RepoFile instance

        Raises
        ------
        ValueError
            If file_path and symlink_path are equal.
            If path does not match the PACKAGE_PATH regular expression

        Returns
        -------
        Path
            The validated Path
        """

        file_type = values.get("file_type")
        regex = RepoFile.get_file_type_regex(file_type=file_type)

        paths: List[Path] = []
        paths.append(values.get("file_path"))  # type: ignore[arg-type]
        paths.append(values.get("symlink_path"))  # type: ignore[arg-type]

        if paths[0] == paths[1]:
            raise ValueError(
                f"The file_path ({paths[0]}) and the symlink_path ({paths[1]}) attributes must not be equal!"
            )

        for path in paths:
            RepoFile.validate_path(regex=regex, path=path)

        return values

    def check_file_path_exists(self, exists: bool = True) -> None:
        """Ensure that file_path exists

        Parameters
        ----------
        exists: bool
            Whether file_path should exist or not (defaults to True)

        Raises
        ------
        RepoManagementFileError
            If self.file_path does not exist
        """

        if exists:
            if not self.file_path.exists():
                raise RepoManagementFileError(
                    f"An error occured checking for the existence of a file: {self.file_path} does not exist!"
                )
        else:
            if self.file_path.exists():
                raise RepoManagementFileError(
                    f"An error occured checking for the existence of a file: {self.file_path} exists already!"
                )

    def check_symlink_path_exists(self, exists: bool = True) -> None:
        """Ensure that symlink_path exists

        Parameters
        ----------
        exists: bool
            Whether symlink_path should exist or not (defaults to True)

        Raises
        ------
        RepoManagementFileError
            If self.symlink_path does not exist
        """

        if exists:
            if not self.symlink_path.exists():
                raise RepoManagementFileError(
                    "An error occured checking for the existence of a symlink: {self.symlink_path} does not exist!"
                )
        else:
            if self.symlink_path.exists():
                raise RepoManagementFileError(
                    "An error occured checking for the existence of a symlink: {self.symlink_path} exists already!"
                )

    def copy_from(self, path: Path) -> None:
        """Copy file from a provided Path to file_path

        Before doing further checks, RepoFile.validate_path() is run on path.

        Parameters
        ----------
        path: Path
            Path to move from

        Raises
        ------
        RepoManagementFileError
            If path does not exist
        """

        info(f"Copy {self.file_path} from {path}...")
        RepoFile.validate_path(path=path, regex=RepoFile.get_file_type_regex(file_type=self.file_type))
        if not path.exists():
            raise RepoManagementFileError(f"Error on trying to move file: The input file {path} does not exist!")

        self.check_file_path_exists(exists=False)
        copy2(src=path, dst=self.file_path)

    def move_from(self, path: Path) -> None:
        """Move file from a provided Path to file_path

        Before doing further checks, RepoFile.validate_path() is run on path.

        Parameters
        ----------
        path: Path
            Path to move from

        Raises
        ------
        RepoManagementFileError
            If path does not exist
        """

        info(f"Move {self.file_path} from {path}...")
        RepoFile.validate_path(path=path, regex=RepoFile.get_file_type_regex(file_type=self.file_type))
        if not path.exists():
            raise RepoManagementFileError(f"Error on trying to move file: The input file {path} does not exist!")

        self.check_file_path_exists(exists=False)
        path.rename(target=self.file_path)

    def link(self, check: bool = True) -> None:
        """Link the symlink_path to file_path using a relative symlink

        Parameters
        ----------
        check: bool
            Whether to check if the symlink_path exists already prior to linking (defaults to True)

        Raises
        ------
        RepoManagementFileError
            If the file exists already
        """

        info(f"Link {self.symlink_path} to {self.file_path}...")
        if check:
            debug(f"Checking that {self.symlink_path} does not yet exist...")
            self.check_symlink_path_exists(exists=False)

        try:
            self.symlink_path.symlink_to(relative_to_shared_base(path_a=self.file_path, path_b=self.symlink_path))
        except FileExistsError:
            raise RepoManagementFileError(
                f"An error occured attempting to symlink {self.symlink_path} to {self.file_path}."
                f"{self.symlink_path} exists already!"
            )

    def unlink(self, check: bool = True) -> None:
        """Unlink the symlink_path from file_path

        Parameters
        ----------
        check: bool
            Whether to check that the symlink_path does not exist prior to removal (defaults to True)

        Raises
        ------
        RepoManagementFileError
            If the file does not exist and check = True
        """

        info(f"Unlink {self.symlink_path} from {self.file_path}...")
        if check:
            debug(f"Checking that {self.symlink_path} exists...")
            self.check_symlink_path_exists()

        self.symlink_path.unlink(missing_ok=not check)

    def remove(self, force: bool = False, unlink: bool = False) -> None:
        """Remove file_path and optionally unlink symlink_path from file_path

        Parameters
        ----------
        force: bool
            Whether to not check for path existence before unlinking and to ignore errors on removing non-existing files
            (defaults to False)
        """

        info(f"Removing {self.file_path}...")
        if not force:
            debug(f"Checking that {self.file_path} exists...")
            self.check_file_path_exists()

        self.file_path.unlink(missing_ok=force)

        if unlink:
            info(f"Removing {self.symlink_path}...")
            if not force:
                debug(f"Checking that {self.symlink_path} exists...")
                self.check_symlink_path_exists()
            self.unlink(check=not force)
