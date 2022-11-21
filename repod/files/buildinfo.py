from __future__ import annotations

from io import StringIO
from pathlib import Path
from re import fullmatch
from typing import Any

from pydantic import BaseModel, NonNegativeInt, constr, root_validator, validator

from repod.common.enums import ArchitectureEnum, FieldTypeEnum
from repod.common.models import Packager, SchemaVersionV1, SchemaVersionV2
from repod.common.regex import (
    ARCHITECTURE,
    BUILDENVS,
    EPOCH,
    OPTIONS,
    PACKAGE_NAME,
    PKGREL,
    SHA256,
    VERSION,
)
from repod.errors import RepoManagementError

BUILDINFO_ASSIGNMENTS: dict[str, tuple[str, FieldTypeEnum]] = {
    "builddate": ("builddate", FieldTypeEnum.INT),
    "builddir": ("builddir", FieldTypeEnum.STRING),
    "buildenv": ("buildenv", FieldTypeEnum.STRING_LIST),
    "buildtool": ("buildtool", FieldTypeEnum.STRING),
    "buildtoolver": ("buildtoolver", FieldTypeEnum.STRING),
    "format": ("schema_version", FieldTypeEnum.INT),
    "installed": ("installed", FieldTypeEnum.STRING_LIST),
    "options": ("options", FieldTypeEnum.STRING_LIST),
    "packager": ("packager", FieldTypeEnum.STRING),
    "pkgarch": ("pkgarch", FieldTypeEnum.STRING),
    "pkgbase": ("pkgbase", FieldTypeEnum.STRING),
    "pkgbuild_sha256sum": ("pkgbuild_sha256sum", FieldTypeEnum.STRING),
    "pkgname": ("pkgname", FieldTypeEnum.STRING),
    "pkgver": ("pkgver", FieldTypeEnum.STRING),
    "startdir": ("startdir", FieldTypeEnum.STRING),
}


class BuildDate(BaseModel):
    """A build date in seconds since the epoch

    Attributes
    ----------
    builddate: NonNegativeInt
        A number >= 0
    """

    builddate: NonNegativeInt


class BuildDir(BaseModel):
    """An absolute build directory

    Attributes
    ----------
    builddir: str
        A string representing an absolute directory
    """

    builddir: str

    @validator("builddir")
    def validate_builddir(cls, builddir: str) -> str:
        """Validate the builddir attribute

        The builddir attribute may not contain strings that represent absolute Paths or Paths in the home directory

        Parameters
        ----------
        builddir: str
            A string, representing a path

        Returns
        -------
        str
            A validated string, representing an absolute Path
        """

        path = Path(builddir)
        if not path.is_absolute():
            raise ValueError(f"A relative path as builddir is not valid: {path}")

        return builddir


class BuildEnv(BaseModel):
    """A list of build environment options

    For valid values refer to BUILDENV in https://man.archlinux.org/man/makepkg.conf.5#OPTIONS

    Attributes
    ----------
    buildenv: list[str]
        A list of strings as described by makepkg.conf's BUILDENV option
    """

    buildenv: list[constr(regex=rf"^{BUILDENVS}$")]  # type: ignore[valid-type]  # noqa: F722


class BuildTool(BaseModel):
    """The build tool used to create a package

    Attributes
    ----------
    buildtool: str
        The package name of the build tool used to create a package
    """

    buildtool: constr(regex=rf"^{PACKAGE_NAME}$")  # type: ignore[valid-type]  # noqa: F722


class BuildToolVer(BaseModel):
    """The package version of the build tool used to create a package

    Attributes
    ----------
    buildtoolver: str
        The version of the build tool used to create a package
    """

    buildtoolver: str


class Installed(BaseModel):
    """A list of package names and versions installed during the creation of a package

    Attributes
    ----------
    installed: list[str]
        A list of strings representing <package_name>-<epoch><version>-<pkgrel>-<architecture> of packages installed
        during the creation of a package
    """

    installed: list[  # type: ignore[valid-type]
        constr(regex=rf"^({PACKAGE_NAME})-({EPOCH}|){VERSION}-{PKGREL}-{ARCHITECTURE}$")  # noqa: F722
    ]

    @classmethod
    def as_models(cls, installed: list[str]) -> list[tuple[PkgName, PkgVer, ArchitectureEnum]]:
        """Return a list of installed dependencies as models

        Parameters
        ----------
        installed: list[str]
            A list of strings, each describing pkgname-version-architecture

        Raises
        ------
        ValidationError
            If any of the entries in installed can not be validated using PkgName, PkgVer, Architecture

        Returns
        -------
        list[tuple[PkgName, PkgVer, ArchitectureEnum]]
            A list of PkgName, PkgVer and ArchitectureEnum tuples, which describe each entry in installed
        """

        return [
            (
                PkgName(pkgname="-".join(dep.split("-")[0:-3])),
                PkgVer(pkgver="-".join(dep.split("-")[-3:-1])),
                ArchitectureEnum(dep.split("-")[-1]),
            )
            for dep in installed
        ]


class Options(BaseModel):
    """A list of makepkg.conf OPTIONS used during the creation of a package

    For valid values refer to the OPTIONS subsection in https://man.archlinux.org/man/makepkg.conf.5#OPTIONS

    Attributes
    ----------
    options: list[str]
        A list of strings representing makepkg.conf OPTIONS used during the creation of a package
    """

    options: list[constr(regex=rf"^{OPTIONS}$")]  # type: ignore[valid-type]  # noqa: F722


class PkgArch(BaseModel):
    """A CPU architecture for a package

    Refer to the arch subsection in https://man.archlinux.org/man/PKGBUILD.5.en#OPTIONS_AND_DIRECTIVES for details

    Attributes
    ----------
    pkgarch: str
        A valid CPU architecture for a package
    """

    pkgarch: constr(regex=rf"^{ARCHITECTURE}$")  # type: ignore[valid-type]  # noqa: F722


class PkgBase(BaseModel):
    """A pkgbase for a package

    Refer to https://man.archlinux.org/man/PKGBUILD.5.en#PACKAGE_SPLITTING for details on pkgbase

    Attributes
    ----------
    pkgbase: str
        A string representing a valid pkgbase for a package
    """

    pkgbase: constr(regex=rf"^{PACKAGE_NAME}$")  # type: ignore[valid-type]  # noqa: F722


class PkgBuildSha256Sum(BaseModel):
    """A SHA-256 checksum for a PKGBUILD file of a package

    Attributes
    ----------
    pkgbuild_sha256sum: str
        A string representing a SHA-256 checksum for a PKGBUILD of a package
    """

    pkgbuild_sha256sum: constr(regex=rf"{SHA256}")  # type: ignore[valid-type]  # noqa: F722


class PkgName(BaseModel):
    """A pkgname of a package

    Refer to the pkgname section in https://man.archlinux.org/man/PKGBUILD.5.en#OPTIONS_AND_DIRECTIVES for details

    Attributes
    ----------
    pkgname: str
        A string representing a valid pkgname of a package
    """

    pkgname: constr(regex=rf"^{PACKAGE_NAME}$")  # type: ignore[valid-type]  # noqa: F722


class PkgVer(BaseModel):
    """A version string for a package, consisting of epoch, pkgver and pkgrel

    Refer to the epoch, pkgrel and pkgver sections in https://man.archlinux.org/man/PKGBUILD.5.en#OPTIONS_AND_DIRECTIVES
    for details

    Attributes
    ----------
    pkgver: str
        A valid package version string which includes epoch, version and pkgrel
    """

    pkgver: constr(regex=rf"^({EPOCH}|){VERSION}-{PKGREL}$")  # type: ignore[valid-type]  # noqa: F722


class StartDir(BaseModel):
    """An absolute directory used as startdir for a package

    Refer to the startdir subsection in https://man.archlinux.org/man/PKGBUILD.5.en#PACKAGING_FUNCTIONS

    Attributes
    ----------
    startdir: str
        A string representing the absolute startdir directory of a package
    """

    startdir: str

    @validator("startdir")
    def validate_startdir(cls, startdir: str) -> str:
        """Validate the startdir attribute

        The startdir attribute may not contain strings that represent absolute Paths or Paths in the home directory

        Parameters
        ----------
        startdir: str
            A string, representing a path

        Returns
        -------
        str
            A validated string, representing an absolute Path
        """

        path = Path(startdir)
        if not path.is_absolute():
            raise ValueError(f"A relative path as startdir is not valid: {path}")

        return startdir


class BuildInfo(BaseModel):
    """The representation of a .BUILDINFO file

    This is a template class and should not be used directly. Instead instantiate one of the classes derived from it.
    """

    @classmethod
    def from_file(cls, data: StringIO) -> BuildInfo:
        """Create an instance of BuildInfo from an io.StringIO representing the contents of a BUILDINFO file

        Parameters
        ----------
        data: io.StringIO
            A text stream representing the contents of a .BUILDINFO file

        Returns
        -------
        BuildInfo
            An instance of BuildInfo
        """

        entries: dict[str, int | str | list[str]] = {}

        for line in data:
            [key, value] = [x.strip() for x in line.strip().split("=")]

            assignment_key = BUILDINFO_ASSIGNMENTS.get(key)
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
                        continue

        match entries.get("schema_version"):
            case 1:
                return BuildInfoV1(**entries)
            case 2:
                return BuildInfoV2(**entries)
            case _:
                raise RepoManagementError(
                    f"Encountered unhandled .BUILDINFO schema_version {entries.get('schema_version')}!"
                )


class BuildInfoV1(
    BuildDate,
    BuildDir,
    BuildEnv,
    BuildInfo,
    Installed,
    Options,
    Packager,
    PkgArch,
    PkgBase,
    PkgBuildSha256Sum,
    PkgName,
    PkgVer,
    SchemaVersionV1,
):
    """The representation of a .BUILDINFO file (version 1)

    Attributes
    ----------
    builddate: NonNegativeInt
        A number >= 0
    builddir: str
        A string representing an absolute directory
    buildenv: list[str]
        A list of strings as described by makepkg.conf's BUILDENV option
    installed: list[str]
        A list of strings representing <package_name>-<epoch><version>-<pkgrel>-<architecture> of packages installed
        during the creation of a package
    options: list[str]
        A list of strings representing makepkg.conf OPTIONS used during the creation of a package
    packager: str
        A string representing a packager UID (e.g. "First Last <mail@example.tld>")
    pkgarch: str
        A valid CPU architecture for a package
    pkgbase: str
        A string representing a valid pkgbase for a package
    pkgbuild_sha256sum: str
        A string representing a SHA-256 checksum for a PKGBUILD of a package
    pkgname: str
        A string representing a valid pkgname of a package
    pkgver: str
        A valid package version string which includes epoch, version and pkgrel
    schema_version: int
        1 - representing `format = 1` in the .BUILDINFO file; schema_version is chosen for uniformity
    """

    pass


class BuildInfoV2(
    BuildDate,
    BuildDir,
    BuildEnv,
    BuildInfo,
    BuildTool,
    BuildToolVer,
    Installed,
    Options,
    Packager,
    PkgArch,
    PkgBase,
    PkgBuildSha256Sum,
    PkgName,
    PkgVer,
    SchemaVersionV2,
    StartDir,
):
    """The representation of a .BUILDINFO file (version 2)

    Attributes
    ----------
    builddate: NonNegativeInt
        A number >= 0
    builddir: str
        A string representing an absolute directory
    buildenv: list[str]
        A list of strings as described by makepkg.conf's BUILDENV option
    buildtool: str
        The package name of the build tool used to create a package
    buildtoolver: str
        The version of the build tool used to create a package
    installed: list[str]
        A list of strings representing <package_name>-<epoch><version>-<pkgrel>-<architecture> of packages installed
        during the creation of a package
    options: list[str]
        A list of strings representing makepkg.conf OPTIONS used during the creation of a package
    packager: str
        A string representing a packager UID (e.g. "First Last <mail@example.tld>")
    pkgarch: str
        A valid CPU architecture for a package
    pkgbase: str
        A string representing a valid pkgbase for a package
    pkgbuild_sha256sum: str
        A string representing a SHA-256 checksum for a PKGBUILD of a package
    pkgname: str
        A string representing a valid pkgname of a package
    pkgver: str
        A valid package version string which includes epoch, version and pkgrel
    schema_version: int
        2 - representing `format = 2` in the .BUILDINFO file; schema_version is chosen for uniformity
    startdir: str
        A string representing the absolute startdir directory of a package
    """

    @root_validator
    def validate_devtools_version(cls, values: dict[str, Any]) -> dict[str, Any]:
        """A root validator that ensures the use of a valid version string when devtools is the buildtool

        Parameters
        ----------
        values: dict[str, Any]
            A dict with all values of a BuildInfoV2 object

        Raises
        ------
        ValueError
            If buildtool is "devtools" and buildtoolver does not follow the format
            <optional_epoch><pkgver>-<pkgrel>-<arch>

        Returns
        -------
        values: dict[str, Any]
            The unmodified dict with all values of a BuildInfoV2 instance
        """

        buildtool, buildtoolver = str(values.get("buildtool")), str(values.get("buildtoolver"))
        if buildtool == "devtools" and not fullmatch(rf"^({EPOCH}|){VERSION}-{PKGREL}-{ARCHITECTURE}$", buildtoolver):
            raise ValueError(
                "When building with devtools the buildtoolver must be of the format "
                f"<optional_epoch><pkgver>-<pkgrel>-<arch>, but it is {buildtoolver}!"
            )

        return values


def export_schemas(output: Path | str) -> None:
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

    classes = [BuildInfoV1, BuildInfoV2]

    if isinstance(output, str):
        output = Path(output)

    if not output.exists():
        raise RuntimeError(f"The output directory {output} must exist!")

    for class_ in classes:
        with open(output / f"{class_.__name__}.json", "w") as f:
            print(class_.schema_json(indent=2), file=f)
