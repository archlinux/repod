from __future__ import annotations

from io import StringIO
from logging import debug
from pathlib import Path
from typing import Dict, List, Set, Tuple, Union

from pydantic import BaseModel, constr

from repod.common.enums import FieldTypeEnum
from repod.common.models import (
    Arch,
    Backup,
    Base,
    BuildDate,
    CheckDepends,
    Conflicts,
    Depends,
    Desc,
    Groups,
    ISize,
    License,
    MakeDepends,
    Name,
    OptDepends,
    Packager,
    Provides,
    Replaces,
    SchemaVersionV1,
    SchemaVersionV2,
    Url,
    Version,
)
from repod.common.regex import PKGTYPE, VERSION
from repod.errors import RepoManagementError, RepoManagementFileError

PKGINFO_ASSIGNMENTS: Dict[str, Tuple[str, FieldTypeEnum]] = {
    "pkgname": ("name", FieldTypeEnum.STRING),
    "pkgbase": ("base", FieldTypeEnum.STRING),
    "pkgtype": ("pkgtype", FieldTypeEnum.STRING),
    "pkgver": ("version", FieldTypeEnum.STRING),
    "pkgdesc": ("desc", FieldTypeEnum.STRING),
    "url": ("url", FieldTypeEnum.STRING),
    "builddate": ("builddate", FieldTypeEnum.INT),
    "packager": ("packager", FieldTypeEnum.STRING),
    "size": ("isize", FieldTypeEnum.INT),
    "arch": ("arch", FieldTypeEnum.STRING),
    "license": ("license", FieldTypeEnum.STRING_LIST),
    "replaces": ("replaces", FieldTypeEnum.STRING_LIST),
    "group": ("groups", FieldTypeEnum.STRING_LIST),
    "conflict": ("conflicts", FieldTypeEnum.STRING_LIST),
    "provides": ("provides", FieldTypeEnum.STRING_LIST),
    "backup": ("backup", FieldTypeEnum.STRING_LIST),
    "depend": ("depends", FieldTypeEnum.STRING_LIST),
    "optdepend": ("optdepends", FieldTypeEnum.STRING_LIST),
    "makedepend": ("makedepends", FieldTypeEnum.STRING_LIST),
    "checkdepend": ("checkdepends", FieldTypeEnum.STRING_LIST),
}
PKGINFO_COMMENT_ASSIGNMENTS: Dict[str, Tuple[str, FieldTypeEnum]] = {
    "makepkg": ("makepkg_version", FieldTypeEnum.STRING),
    "fakeroot": ("fakeroot_version", FieldTypeEnum.STRING),
}
PKGINFO_VERSIONS: Dict[int, Dict[str, Set[str]]] = {
    1: {
        "required": {
            "arch",
            "base",
            "builddate",
            "desc",
            "fakeroot_version",
            "isize",
            "license",
            "makepkg_version",
            "name",
            "packager",
            "url",
            "version",
        },
        "optional": {
            "backup",
            "checkdepends",
            "conflicts",
            "depends",
            "groups",
            "makedepends",
            "optdepends",
            "provides",
            "replaces",
        },
    },
    2: {
        "required": {
            "arch",
            "base",
            "builddate",
            "desc",
            "fakeroot_version",
            "isize",
            "license",
            "makepkg_version",
            "name",
            "packager",
            "pkgtype",
            "url",
            "version",
        },
        "optional": {
            "backup",
            "checkdepends",
            "conflicts",
            "depends",
            "groups",
            "makedepends",
            "optdepends",
            "provides",
            "replaces",
        },
    },
}


class FakerootVersion(BaseModel):
    """A version of fakeroot

    Attributes
    ----------
    fakeroot_version: str
        A string representing a version of fakeroot
    """

    fakeroot_version: constr(regex=rf"^({VERSION})$")  # type: ignore[valid-type]  # noqa: F722


class MakepkgVersion(BaseModel):
    """A version of makepkg

    Attributes
    ----------
    makepkg_version: str
        A string representing a version of makepkg
    """

    makepkg_version: constr(regex=rf"^({VERSION})$")  # type: ignore[valid-type]  # noqa: F722


class PkgType(BaseModel):
    """A package type

    Attributes
    ----------
    pkgtype: str
        A string representing a valid package type (one of repod.common.enums.PkgTypeEnum)
    """

    pkgtype: constr(regex=rf"^{PKGTYPE}$")  # type: ignore[valid-type]  # noqa: F722


class PkgInfo(BaseModel):
    """The representation of a .PKGINFO file

    This is a template class and should not be used directly. Instead instatiate one of the classes derived from it.
    """

    @classmethod
    def from_file(cls, data: StringIO) -> PkgInfo:
        """Create an instance of PkgInfo from an io.StringIO representing the contents of a PKGINFO file

        Parameters
        ----------
        data: io.StringIO
            A text stream representing the contents of a .PKGINFO file

        Returns
        -------
        PkgInfo
            An instance of PkgInfo
        """

        pkg_info_version = 0
        entries: Dict[str, Union[int, str, List[str]]] = {}

        for line in data:
            debug(f"Parsing .PKGINFO line: {line}")
            if line.startswith("#"):
                for keyword in PKGINFO_COMMENT_ASSIGNMENTS.keys():
                    if keyword in line:
                        key = keyword
                        value = line.strip().split()[-1]
                        assignment_key = PKGINFO_COMMENT_ASSIGNMENTS.get(key)
            else:
                try:
                    key, value = [x.strip() for x in line.strip().split(" = ", 1)]
                    assignment_key = PKGINFO_ASSIGNMENTS.get(key)
                except ValueError as e:
                    raise RepoManagementFileError(
                        f"An error occurred while trying to parse the .PKGINFO line {line}\n{e}"
                    )

            if isinstance(assignment_key, tuple):
                match assignment_key[1]:
                    case FieldTypeEnum.INT:
                        entries[assignment_key[0]] = int(value)
                    case FieldTypeEnum.STRING:
                        entries[assignment_key[0]] = str(value)
                    case FieldTypeEnum.STRING_LIST:
                        entry = entries.get(assignment_key[0])
                        if entry is not None and isinstance(entry, list):
                            entry.append(str(value))
                        else:
                            entries[assignment_key[0]] = [str(value)]
                    # NOTE: the catch all can never be reached but is here to satisfy our tooling
                    case _:  # pragma: no cover
                        raise RuntimeError(
                            "An invalid field type has been encountered while attempting to read a .PKGINFO file.\n"
                            "This most likely means a new field type has been introduced, but the .PKGINFO parser has "
                            "not been extended to make use of it!"
                        )

        for version in range(len(PKGINFO_VERSIONS), 0, -1):
            debug(f"Testing data against .PKGINFO version {version}.")
            if PKGINFO_VERSIONS[version]["required"].issubset(set(entries.keys())):
                debug(f".PKGINFO version {version} matches provided data!")
                pkg_info_version = version
                break

        match pkg_info_version:
            case 1:
                return PkgInfoV1(**entries)
            case 2:
                return PkgInfoV2(**entries)
            case _:
                raise RepoManagementError(
                    f"Encountered unhandled .PKGINFO version {pkg_info_version} when trying to match data {entries}!"
                )


class PkgInfoV1(
    Arch,
    Backup,
    Base,
    BuildDate,
    CheckDepends,
    Conflicts,
    Depends,
    Desc,
    FakerootVersion,
    Groups,
    ISize,
    Packager,
    License,
    MakeDepends,
    MakepkgVersion,
    Name,
    OptDepends,
    PkgInfo,
    Provides,
    Replaces,
    SchemaVersionV1,
    Url,
    Version,
):
    """A PkgInfo version 1

    Attributes
    ----------
    arch: str
        A string representing a CPU architecture
    backup: Optional[List[str]]
        An optional list of strings representing relative file paths
    base: str
        A string representing a pkgbase
    builddate: int
        A number representing a build date (in seconds since the epoch)
    checkdepends: Optional[List[str]]
        An optional list of strings representing package names a package requires for tests
    conflicts: Optional[List[str]]
        An optional list of strings representing package names a package conflicts with
    depends: Optional[List[str]]
        An optional list of strings representing package names a package depends on
    desc: str
        A string that serves as description for a package
    fakeroot_version: str
        A string representing a version of fakeroot
    groups: Optional[List[str]]
        An optional list of strings representing group names a package belongs to
    isize: int
        A number representing the installed sized of a package in bytes
    packager: str
        A string describing the UID of a package's packager
    license: List[str]
        A list of strings describing the license identifiers that apply to a package
    makedepends: Optional[List[str]]
        An optional list of strings representing package names a package requires for building
    makepkg_version: str
        A string representing a version of makepkg
    name: str
        A string representing the name of a package
    optdepends: Optional[List[str]]
        An optional list of strings representing package names a package requires optionally
    provides: Optional[List[str]]
        An optional list of strings representing package names a package provides
    replaces: Optional[List[str]]
        An optional list of strings representing package names a package replaces
    url: str
        A string representing the upstream URL of a package
    version: str
        A string representing the full version (optional epoch, version and pkgrel) of a package
    """

    pass


class PkgInfoV2(
    Arch,
    Backup,
    Base,
    BuildDate,
    CheckDepends,
    Conflicts,
    Depends,
    Desc,
    FakerootVersion,
    Groups,
    ISize,
    Packager,
    License,
    MakeDepends,
    MakepkgVersion,
    Name,
    OptDepends,
    PkgInfo,
    PkgType,
    Provides,
    Replaces,
    SchemaVersionV2,
    Url,
    Version,
):
    """A PkgInfo version 2

    Attributes
    ----------
    arch: str
        A string representing a CPU architecture
    backup: Optional[List[str]]
        An optional list of strings representing relative file paths
    base: str
        A string representing a pkgbase
    builddate: int
        A number representing a build date (in seconds since the epoch)
    checkdepends: Optional[List[str]]
        An optional list of strings representing package names a package requires for tests
    conflicts: Optional[List[str]]
        An optional list of strings representing package names a package conflicts with
    depends: Optional[List[str]]
        An optional list of strings representing package names a package depends on
    desc: str
        A string that serves as description for a package
    fakeroot_version: str
        A string representing a version of fakeroot
    groups: Optional[List[str]]
        An optional list of strings representing group names a package belongs to
    isize: int
        A number representing the installed sized of a package in bytes
    packager: str
        A string describing the UID of a package's packager
    license: List[str]
        A list of strings describing the license identifiers that apply to a package
    makedepends: Optional[List[str]]
        An optional list of strings representing package names a package requires for building
    makepkg_version: str
        A string representing a version of makepkg
    name: str
        A string representing the name of a package
    optdepends: Optional[List[str]]
        An optional list of strings representing package names a package requires optionally
    pkgtype: str
        A string representing a valid package type (one of repod.common.enums.PkgTypeEnum)
    provides: Optional[List[str]]
        An optional list of strings representing package names a package provides
    replaces: Optional[List[str]]
        An optional list of strings representing package names a package replaces
    url: str
        A string representing the upstream URL of a package
    version: str
        A string representing the full version (optional epoch, version and pkgrel) of a package
    """

    pass


def export_schemas(output: Union[Path, str]) -> None:
    """Export the JSON schema of selected pydantic models to an output directory

    Parameters
    ----------
    output: Path
        A path to which to output the JSON schema files

    Raises
    ------
    RuntimeError
        If output is not an existing directory
    """

    classes = [PkgInfoV1, PkgInfoV2]

    if isinstance(output, str):
        output = Path(output)

    if not output.exists():
        raise RuntimeError(f"The output directory {output} must exist!")

    for class_ in classes:
        with open(output / f"{class_.__name__}.json", "w") as f:
            print(class_.schema_json(indent=2), file=f)
