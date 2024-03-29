"""Handling of .MTREE files."""
from __future__ import annotations

import io
import re
from logging import debug
from pathlib import Path

from pydantic import (
    BaseModel,
    NonNegativeFloat,
    NonNegativeInt,
    ValidationError,
    conint,
    constr,
)

from repod.common.models import SchemaVersionV1
from repod.common.regex import ABSOLUTE_MTREE_PATH, MD5, RELATIVE_MTREE_PATH, SHA256
from repod.errors import RepoManagementValidationError


class SystemGID(BaseModel):
    """The group ID of a system group.

    Attributes
    ----------
    gid: int
        A group ID >0, <1000
    """

    gid: conint(ge=0, lt=1000)  # type: ignore[valid-type]


class LinkTarget(BaseModel):
    """The target location of a symlink.

    Attributes
    ----------
    link: str | None
        An optional string representing a relative or absolute file
    """

    link: constr(  # type: ignore[valid-type]
        regex=rf"^({RELATIVE_MTREE_PATH}|{ABSOLUTE_MTREE_PATH})$"  # noqa: F722
    ) | None


class Md5(BaseModel):
    """An MD5 checksum.

    Attributes
    ----------
    md5: str | None
        An optional string representing an MD5 checksum
    """

    md5: constr(regex=rf"^{MD5}$") | None  # type: ignore[valid-type]  # noqa: F722


class FileMode(BaseModel):
    """A numeric unix file mode.

    Attributes
    ----------
    mode: str
        A three or four digit long string, consisting only of valid file modes
    """

    mode: constr(regex=r"^[01234567]{3,4}$")  # type: ignore[valid-type]  # noqa: F722


class MTreeEntryName(BaseModel):
    """A file name in mtree representation.

    The mtree format allows for encoding characters using a block of backslash and three octal digits (see
    https://man.archlinux.org/man/mtree.5#General_Format).

    Attributes
    ----------
    name: str
        A string representing an absolute file location in mtree format
    """

    name: constr(regex=rf"^{ABSOLUTE_MTREE_PATH}$")  # type: ignore[valid-type]  # noqa: F722


class Sha256(BaseModel):
    """A SHA-256 checksum.

    Attributes
    ----------
    sha256:
        An optional string representing a SHA-256 checksum
    """

    sha256: constr(regex=rf"^{SHA256}$") | None  # type: ignore[valid-type]  # noqa: F722


class FileSize(BaseModel):
    """A file size in bytes.

    Attributes
    ----------
    size: int
        A non-negative integer describing a file size in bytes
    """

    size: NonNegativeInt | None


class UnixTime(BaseModel):
    """A timestamp in seconds since the epoch.

    Attributes
    ----------
    time: float
        A float > 0 representing a unix timestamp (seconds since the epoch)
    """

    time: NonNegativeFloat


class MTreeEntryType(BaseModel):
    """A file type for mtree entries (see https://man.archlinux.org/man/mtree.5#Keywords).

    Attributes
    ----------
    type_: str
        A string representing a valid mtree type (one of block, char, dir, fifo, file, link or socket)
    """

    type_: constr(regex=r"^(block|char|dir|fifo|file|link|socket)$")  # type: ignore[valid-type]  # noqa: F722


class SystemUID(BaseModel):
    """The user ID of a system user.

    Attributes
    ----------
    uid: int
        A user ID >0, <1000
    """

    uid: conint(ge=0, lt=1000)  # type: ignore[valid-type]


class MTreeEntry(BaseModel):
    """An entry in an MTree.

    This is a template class and should not be used directly. Instead instantiate one of the classes derived from it.
    """

    def get_file_path(self) -> Path:
        """Return the file name as a Path.

        The mtree format allows for encoding characters using a block of backslash and three octal digits (see
        https://man.archlinux.org/man/mtree.5#General_Format).
        This method finds and replaces occurences of these encoded characters.

        Raises
        ------
        RuntimeError
            If called on the template class MTreeEntry

        Returns
        -------
        Path
            The Path representation of name
        """
        if not hasattr(self, "name"):
            raise RuntimeError("It is not possible to retrieve a file path from the template class MTreeEntry!")

        output_name = self.name

        if len(re.findall(r"\\[0-9A-F]{3}", output_name)) > 0:
            output_name = output_name.encode("latin1").decode("unicode-escape").encode("latin1").decode("utf8")
            debug(f"Converted MTree path {self.name} to {output_name}.")

        return Path(output_name)

    def get_link_path(self, resolve: bool = False) -> Path | None:
        """Return the link as a Path.

        The mtree format allows for encoding characters using a block of backslash and three octal digits (see
        https://man.archlinux.org/man/mtree.5#General_Format).
        This method finds and replaces occurences of these encoded characters.
        Any relative paths are converted to absolute ones.

        Parameters
        ----------
        resolve: bool
            Whether to fully resolve the link - defaults to False

        Raises
        ------
        RuntimeError
            If called on the template class MTreeEntry

        Returns
        -------
        Path | None
            The Path representation of link, or None if there is None
        """
        if not hasattr(self, "link"):
            raise RuntimeError("It is not possible to retrieve a file path from the template class MTreeEntry!")

        output_name = self.link
        if output_name is None:
            return output_name

        if len(re.findall(r"\\[0-9A-F]{3}", output_name)) > 0:
            output_name = output_name.encode("latin1").decode("unicode-escape").encode("latin1").decode("utf8")
            debug(f"Converted MTree path {self.name} to {output_name}.")  # type: ignore[attr-defined]

        output_path = Path(output_name)

        if not resolve or output_path.is_absolute():
            return output_path
        else:
            if output_name.startswith(".."):
                return (self.get_file_path() / output_path).resolve()
            else:
                return (self.get_file_path() / ".." / output_path).resolve()

    def get_type(self) -> str:
        """Return the type as a string.

        Raises
        ------
        RuntimeError
            If called on the template class MTreeEntry

        Returns
        -------
        str
            The type of the MTreeEntry
        """
        if not hasattr(self, "type_"):
            raise RuntimeError("It is not possible to retrieve a type from the template class MTreeEntry!")

        return str(self.type_)


class MTreeEntryV1(
    MTreeEntry,
    SchemaVersionV1,
    FileMode,
    FileSize,
    LinkTarget,
    Md5,
    MTreeEntryName,
    MTreeEntryType,
    Sha256,
    UnixTime,
    SystemGID,
    SystemUID,
):
    """An entry in an MTree (version 1).

    Attributes
    ----------
    gid: int
        A group ID >0, <1000
    link: str | None
        An optional string representing a relative or absolute file
    md5: str | None
        A optional string representing an MD5 checksum
    mode: str
        A three or four digit long string, consisting only of valid file modes
    name: str
        A string representing an absolute file location in mtree format
    schema_version: int
        A schema version (defaults to 1)
    sha256:
        An optional string representing a SHA-256 checksum
    size: int
        A non-negative integer describing a file size in bytes
    time: float
        A float > 0 representing a unix timestamp (seconds since the epoch)
    type_: str
        A string representing a valid mtree type (one of block, char, dir, fifo, file, link or socket)
    uid: int
        A user ID >0, <1000
    """

    pass


class MTree(BaseModel):
    """A class to describe an mtree file.

    Attributes
    ----------
    files: list[File]
        A list of File instances, representing the entries in an mtree file
    """

    entries: list[MTreeEntry]

    @classmethod
    def from_file(cls, data: io.StringIO) -> MTree:
        """Create an instance of MTree from an io.StringIO representing the contents of an mtree file.

        Parameters
        ----------
        data: io.StringIO
            A text stream representing the contents of an mtree file

        Raises
        ------
        RepoManagementValidationError
            If a ValidationError occurs during validation of the data

        Returns
        -------
        MTree
            An instance of MTree, derived from data
        """

        def sanitize_mtree_pairs(
            settings_list: list[list[str]],
            settings_dict: dict[str, float | int | str],
        ) -> None:
            """Sanitize mtree pairs in a list and add them to a dict.

            Parameters
            ----------
            settings_list: list[list[str]]
                A list of string lists, that represent mtree key-value pairs
            settings_dict: dict[str, float | int | str]
                A dict to which sanitized mtree key-value pairs are added
            """
            for setting in settings_list:
                settings_key = setting[0]
                setting_value = setting[1].strip("\n")
                match settings_key:
                    case "gid" | "uid" | "size":
                        settings_dict[settings_key] = int(setting_value)
                    case "time":
                        settings_dict[settings_key] = float(setting_value)
                    case "type":
                        # NOTE: do not overload type()
                        settings_dict["type_"] = setting_value
                    case "mode":
                        # NOTE: ensure that file modes are zero-filled and of length 4
                        settings_dict[settings_key] = setting_value.zfill(4)
                    case "md5digest" | "sha1digest" | "sha256digest" | "sha384digest" | "sha512digest":
                        # NOTE: only use the name of the digest as key to be more flexible in reusing the model
                        settings_dict[settings_key.replace("digest", "")] = setting_value
                    case _:
                        settings_dict[settings_key] = setting_value

        base_settings: dict[str, float | int | str] = {}
        entries: list[MTreeEntry] = []

        for line in data:
            if line.startswith("/set"):
                settings_list = [assignment.split("=") for assignment in line.split(" ")[1:]]
                sanitize_mtree_pairs(settings_list=settings_list, settings_dict=base_settings)

            elif line.startswith("."):
                file_settings: dict[str, float | int | str] = {}
                file_settings["name"] = line.split()[0][1:]

                # provide a list of all settings in an entry line (skip empty assigments due to multiple whitespace)
                settings_list = [assignment.split("=") for assignment in line.split()[1:] if assignment]
                sanitize_mtree_pairs(settings_list=settings_list, settings_dict=file_settings)

                try:
                    entries.append(
                        MTreeEntryV1(
                            gid=file_settings.get("gid") or base_settings.get("gid"),
                            link=file_settings.get("link"),
                            md5=file_settings.get("md5") or base_settings.get("md5"),
                            mode=file_settings.get("mode") or base_settings.get("mode"),
                            name=file_settings.get("name"),
                            sha256=file_settings.get("sha256") or base_settings.get("sha256"),
                            size=file_settings.get("size") or base_settings.get("size"),
                            time=file_settings.get("time") or base_settings.get("time"),
                            type_=file_settings.get("type_") or base_settings.get("type_"),
                            uid=file_settings.get("uid") or base_settings.get("uid"),
                        )
                    )
                except ValidationError as e:
                    raise RepoManagementValidationError(
                        f"An error occured when validating mtree data!\n"
                        f"Basic settings: {base_settings}\n"
                        f"File settings: {file_settings}\n"
                        f"{e}"
                    )
            else:
                continue

        return MTree(entries=entries)

    def get_paths(self, show_all: bool = False) -> list[Path]:
        """Return the list of Paths described by the entries of the MTree.

        Parameters
        ----------
        show_all: bool
            Also show files that are not installed on target systems (defaults to False)

        Returns
        -------
        list[Path]
            A list of Paths
        """
        path_list: list[Path] = []

        for entry in self.entries:
            path = entry.get_file_path()
            if path in [Path("/.BUILDINFO"), Path("/.INSTALL"), Path("/.MTREE"), Path("/.PKGINFO")] and not show_all:
                continue

            path_list.append(path)

        return path_list


def export_schemas(output: Path | str) -> None:
    """Export the JSON schema of selected pydantic models to an output directory.

    Parameters
    ----------
    output: Path
        A path to which to output the JSON schema files

    Raises
    ------
    RuntimeError
        If output is not an existing directory
    """
    classes = [MTreeEntryV1]

    if isinstance(output, str):
        output = Path(output)

    if not output.exists():
        raise RuntimeError(f"The output directory {output} must exist!")

    for class_ in classes:
        with open(output / f"{class_.__name__}.json", "w") as f:
            print(class_.schema_json(indent=2), file=f)
