import io
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pyalpm import vercmp
from pydantic import AnyUrl, BaseModel, root_validator, validator

from repo_management import defaults


class Arch(BaseModel):
    """A model describing a single 'arch' attribute

    Attributes
    ----------
    arch: str
        The attribute can be used to describe the (required) data below an %ARCH% identifier in a 'desc' file, which
        identifies a package's architecture
    """

    arch: str


class Backup(BaseModel):
    """A model describing a single 'backup' attribute

    Attributes
    ----------
    backup: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %BACKUP% identifier in a 'desc' file, which
        identifies which file(s) of a package pacman will create backups for
    """

    backup: Optional[List[str]]


class Base(BaseModel):
    """A model describing a single 'base' attribute

    Attributes
    ----------
    base: str
        The attribute can be used to describe the (required) data below a %BASE% identifier in a 'desc' file, which
        identifies a package's pkgbase
    """

    base: str


class BuildDate(BaseModel):
    """A model describing a single 'builddate' attribute

    Attributes
    ----------
    builddate: int
        The attribute can be used to describe the (required) data below a %BUILDDATE% identifier in a 'desc' file,
        which identifies a package's build date (represented in seconds since the epoch)
    """

    builddate: int

    @validator("builddate")
    def builddate_greater_zero(cls, builddate: int) -> int:
        if builddate < 0:
            raise ValueError("The build date must be greater than zero.")

        return builddate


class CheckDepends(BaseModel):
    """A model describing a single 'checkdepends' attribute

    Attributes
    ----------
    checkdepends: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %CHECKDEPENDS% identifier in a 'desc' file,
        which identifies a package's checkdepends
    """

    checkdepends: Optional[List[str]]


class Conflicts(BaseModel):
    """A model describing a single 'conflicts' attribute

    Attributes
    ----------
    conflicts: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %CONFLICTS% identifier in a 'desc' file, which
        identifies what other package(s) a package conflicts with
    """

    conflicts: Optional[List[str]]


class CSize(BaseModel):
    """A model describing a single 'csize' attribute

    Attributes
    ----------
    csize: int
        The attribute can be used to describe the (required) data below a %CSIZE% identifier in a 'desc' file, which
        identifies a package's size
    """

    csize: int

    @validator("csize")
    def csize_greater_equal_zero(cls, csize: int) -> int:
        if csize < 0:
            raise ValueError("The csize must be greater than or equal zero.")

        return csize


class Depends(BaseModel):
    """A model describing a single 'depends' attribute

    Attributes
    ----------
    depends: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %DEPENDS% identifier in a 'desc' file, which
        identifies what other package(s) a package depends on
    """

    depends: Optional[List[str]]


class Desc(BaseModel):
    """A model describing a single 'desc' attribute

    Attributes
    ----------
    desc: str
        The attribute can be used to describe the (required) data below a %DESC% identifier in a 'desc' file, which
        identifies a package's description
    """

    desc: str


class FileName(BaseModel):
    """A model describing a single 'filename' attribute

    Attributes
    ----------
    filename: str
        The attribute can be used to describe the (required) data below a %FILENAME% identifier in a 'desc' file, which
        identifies a package's file name
    """

    filename: str


class Files(BaseModel):
    """A model describing a single 'files' attribute

    Attributes
    ----------
    files: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %FILES% identifier in a 'files' file, which
        identifies which file(s) belong to a package
    """

    files: Optional[List[str]]


class Groups(BaseModel):
    """A model describing a single 'groups' attribute

    Attributes
    ----------
    groups: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %GROUPS% identifier in a 'desc' file, which
        identifies a package's groups
    """

    groups: Optional[List[str]]


class ISize(BaseModel):
    """A model describing a single 'isize' attribute

    Attributes
    ----------
    isize: int
        The attribute can be used to describe the (required) data below an %ISIZE% identifier in a 'desc' file, which
        identifies a package's installed size
    """

    isize: int

    @validator("isize")
    def isize_greater_equal_zero(cls, isize: int) -> int:
        if isize < 0:
            raise ValueError("The isize must be greater than or equal zero.")

        return isize


class License(BaseModel):
    """A model describing a single 'license' attribute

    Attributes
    ----------
    license: List[str]
        The attribute can be used to describe the (required) data below a %LICENSE% identifier in a 'desc' file, which
        identifies a package's license(s)
    """

    license: List[str]


class MakeDepends(BaseModel):
    """A model describing a single 'makedepends' attribute

    Attributes
    ----------
    makedepends: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %MAKEDEPENDS% identifier in a 'desc' file,
        which identifies a package's makedepends
    """

    makedepends: Optional[List[str]]


class Md5Sum(BaseModel):
    """A model describing a single 'md5sum' attribute

    Attributes
    ----------
    md5sum: str
        The attribute can be used to describe the (required) data below an %MD5SUM% identifier in a 'desc' file, which
        identifies a package's md5 checksum
    """

    md5sum: str


class Name(BaseModel):
    """A model describing a single 'name' attribute

    Attributes
    ----------
    name: str
        The attribute can be used to describe the (required) data below a %NAME% identifier in a 'desc' file, which
        identifies a package's name
    """

    name: str

    @validator("name")
    def name_contains_only_allowed_chars(cls, name: str) -> str:
        disallowed_start_chars = [".", "-"]
        for char in disallowed_start_chars:
            if name.startswith(char):
                raise ValueError(f"The package name '{name}' can not start with any of '{disallowed_start_chars}'.")

        allowed_chars = ["@", ".", "_", "+", "-"]
        remaining_chars: List[str] = []
        for char in name:
            if (not char.isalnum() or (not char.isdigit() and not char.islower())) and char not in allowed_chars:
                remaining_chars += [char]
        if remaining_chars:
            raise ValueError(
                f"The package name '{name}' can not contain '{remaining_chars}' but must consist only of alphanumeric "
                f"chars and any of '{allowed_chars}'."
            )

        return name


class Packager(BaseModel):
    """A model describing a single 'packager' attribute

    Attributes
    ----------
    packager: str
        The attribute can be used to describe the (required) data below a %PACKAGER% identifier in a 'desc' file, which
        identifies a package's packager
    """

    packager: str


class PgpSig(BaseModel):
    """A model describing a single 'pgpsig' attribute

    Attributes
    ----------
    pgpsig: str
        The attribute can be used to describe the (required) data below a %PGPSIG% identifier in a 'desc' file, which
        identifies a package's PGP signature
    """

    pgpsig: str


class Provides(BaseModel):
    """A model describing a single 'provides' attribute

    Attributes
    ----------
    provides: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %PROVIDES% identifier in a 'desc' file, which
        identifies what other package(s) a package provides
    """

    provides: Optional[List[str]]


class Replaces(BaseModel):
    """A model describing a single 'replaces' attribute

    Attributes
    ----------
    replaces: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %REPLACES% identifier in a 'desc' file, which
        identifies what other package(s) a package replaces
    """

    replaces: Optional[List[str]]


class RepoDbMemberType(BaseModel):
    """A model describing a single 'member_type' attribute, which is used to identify/ distinguish different types of
    repository database file types (e.g. 'desc' and 'files' files, which are contained in a repository database file).

    Attributes
    ----------
    member_type: defaults.RepoDbMemberType
        A member of the IntEnum defaults.RepoDbMemberType
    """

    member_type: defaults.RepoDbMemberType


class Sha256Sum(BaseModel):
    """A model describing a single 'sha256sum' attribute

    Attributes
    ----------
    sha256sum: str
        The attribute can be used to describe the (required) data below an %SHA256SUM% identifier in a 'desc' file,
        which identifies a package's sha256 checksum
    """

    sha256sum: str


class OptDepends(BaseModel):
    """A model describing a single 'optdepends' attribute

    Attributes
    ----------
    optdepends: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %OPTDEPENDS% identifier in a 'desc' file,
        which identifies what other package(s) a package optionally depends on
    """

    optdepends: Optional[List[str]]


class Url(BaseModel):
    """A model describing a single 'url' attribute

    Attributes
    ----------
    url: str
        The attribute can be used to describe the (required) data below a %URL% identifier in a 'desc' file, which
        identifies a package's URL
    """

    url: str


class Version(BaseModel):
    """A model describing a single 'version' attribute

    Attributes
    ----------
    version: str
        The attribute can be used to describe the (required) data below a %VERSION% identifier in a 'desc' file, which
        identifies a package's version (this is the accumulation of epoch, pkgver and pkgrel)
    """

    version: str

    @validator("version")
    def version_is_valid(cls, version: str) -> str:
        allowed_chars = [":", ".", "_", "+", "-"]

        if version.endswith("-0"):
            raise ValueError("The first pkgrel of a package release always needs to start at 1.")
        for char in allowed_chars:
            if version.startswith(char):
                raise ValueError("The first character of a package version must not be '{char}'.")

        remaining_chars: List[str] = []
        for char in version:
            if not char.isalnum() and char not in allowed_chars:
                remaining_chars += [char]
        if remaining_chars:
            raise ValueError(
                f"Package versions can not contain '{remaining_chars}' but must consist of alphanumeric chars and any "
                f"of '{allowed_chars}'."
            )

        return version

    def is_older_than(self, version: str) -> bool:
        """Check whether the version is older than a provided version

        Parameters
        ----------
        version: str
            Another version string to compare that of self to

        Returns
        -------
        True if self.version is older than the provided version, False otherwise.
        """

        if vercmp(self.version, version) < 0:
            return True
        else:
            return False

    def is_newer_than(self, version: str) -> bool:
        """Check whether the version is newer than a provided version

        Parameters
        ----------
        version: str
            Another version string to compare that of self to

        Returns
        -------
        True if self.version is newer than the provided version, False otherwise.
        """

        if vercmp(self.version, version) > 0:
            return True
        else:
            return False


class OutputPackage(
    Arch,
    Backup,
    BuildDate,
    CheckDepends,
    Conflicts,
    CSize,
    Depends,
    Desc,
    FileName,
    Files,
    Groups,
    ISize,
    License,
    Md5Sum,
    Name,
    OptDepends,
    PgpSig,
    Provides,
    Replaces,
    Sha256Sum,
    Url,
):
    """A model describing all required attributes that define a package in the context of an output file

    Attributes
    ----------
    arch: str
        The attribute can be used to describe the (required) data below an %ARCH% identifier in a 'desc' file, which
        identifies a package's architecture
    backup: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %BACKUP% identifier in a 'desc' file, which
        identifies which file(s) of a package pacman will create backups for
    builddate: int
        The attribute can be used to describe the (required) data below a %BUILDDATE% identifier in a 'desc' file,
        which identifies a package's build date (represented in seconds since the epoch)
    checkdepends: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %CHECKDEPENDS% identifier in a 'desc' file,
        which identifies a package's checkdepends
    conflicts: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %CONFLICTS% identifier in a 'desc' file, which
        identifies what other package(s) a package conflicts with
    csize: int
        The attribute can be used to describe the (required) data below a %CSIZE% identifier in a 'desc' file, which
        identifies a package's size
    depends: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %DEPENDS% identifier in a 'desc' file, which
        identifies what other package(s) a package depends on
    desc: str
        The attribute can be used to describe the (required) data below a %DESC% identifier in a 'desc' file, which
        identifies a package's description
    filename: str
        The attribute can be used to describe the (required) data below a %FILENAME% identifier in a 'desc' file, which
        identifies a package's file name
    files: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %FILES% identifier in a 'files' file, which
        identifies which file(s) belong to a package
    groups: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %GROUPS% identifier in a 'desc' file, which
        identifies a package's groups
    isize: int
        The attribute can be used to describe the (required) data below an %ISIZE% identifier in a 'desc' file, which
        identifies a package's installed size
    license: List[str]
        The attribute can be used to describe the (required) data below a %LICENSE% identifier in a 'desc' file, which
        identifies a package's license(s)
    md5sum: str
        The attribute can be used to describe the (required) data below an %MD5SUM% identifier in a 'desc' file, which
        identifies a package's md5 checksum
    name: str
        The attribute can be used to describe the (required) data below a %NAME% identifier in a 'desc' file, which
        identifies a package's name
    optdepends: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %OPTDEPENDS% identifier in a 'desc' file,
        which identifies what other package(s) a package optionally depends on
    pgpsig: str
        The attribute can be used to describe the (required) data below a %PGPSIG% identifier in a 'desc' file, which
        identifies a package's PGP signature
    provides: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %PROVIDES% identifier in a 'desc' file, which
        identifies what other package(s) a package provides
    replaces: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %REPLACES% identifier in a 'desc' file, which
        identifies what other package(s) a package replaces
    sha256sum: str
        The attribute can be used to describe the (required) data below an %SHA256SUM% identifier in a 'desc' file,
        which identifies a package's sha256 checksum
    url: str
        The attribute can be used to describe the (required) data below a %URL% identifier in a 'desc' file, which
        identifies a package's URL
    """

    pass


class PackageDesc(
    Arch,
    Backup,
    Base,
    BuildDate,
    CheckDepends,
    Conflicts,
    CSize,
    Depends,
    Desc,
    FileName,
    Groups,
    ISize,
    License,
    MakeDepends,
    Md5Sum,
    Name,
    OptDepends,
    Packager,
    PgpSig,
    Provides,
    Replaces,
    Sha256Sum,
    Url,
    Version,
):
    """A model describing all identifiers in a 'desc' file

    Attributes
    ----------
    arch: str
        The attribute can be used to describe the (required) data below an %ARCH% identifier in a 'desc' file, which
        identifies a package's architecture
    backup: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %BACKUP% identifier in a 'desc' file, which
        identifies which file(s) of a package pacman will create backups for
    base: str
        The attribute can be used to describe the (required) data below a %BASE% identifier in a 'desc' file, which
        identifies a package's pkgbase
    builddate: int
        The attribute can be used to describe the (required) data below a %BUILDDATE% identifier in a 'desc' file,
        which identifies a package's build date (represented in seconds since the epoch)
    checkdepends: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %CHECKDEPENDS% identifier in a 'desc' file,
        which identifies a package's checkdepends
    conflicts: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %CONFLICTS% identifier in a 'desc' file, which
        identifies what other package(s) a package conflicts with
    csize: int
        The attribute can be used to describe the (required) data below a %CSIZE% identifier in a 'desc' file, which
        identifies a package's size
    depends: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %DEPENDS% identifier in a 'desc' file, which
        identifies what other package(s) a package depends on
    desc: str
        The attribute can be used to describe the (required) data below a %DESC% identifier in a 'desc' file, which
        identifies a package's description
    filename: str
        The attribute can be used to describe the (required) data below a %FILENAME% identifier in a 'desc' file, which
        identifies a package's file name
    groups: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %GROUPS% identifier in a 'desc' file, which
        identifies a package's groups
    isize: int
        The attribute can be used to describe the (required) data below an %ISIZE% identifier in a 'desc' file, which
        identifies a package's installed size
    license: List[str]
        The attribute can be used to describe the (required) data below a %LICENSE% identifier in a 'desc' file, which
        identifies a package's license(s)
    makedepends: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %MAKEDEPENDS% identifier in a 'desc' file,
        which identifies a package's makedepends
    md5sum: str
        The attribute can be used to describe the (required) data below an %MD5SUM% identifier in a 'desc' file, which
        identifies a package's md5 checksum
    name: str
        The attribute can be used to describe the (required) data below a %NAME% identifier in a 'desc' file, which
        identifies a package's name
    optdepends: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %OPTDEPENDS% identifier in a 'desc' file,
        which identifies what other package(s) a package optionally depends on
    packager: str
        The attribute can be used to describe the (required) data below a %PACKAGER% identifier in a 'desc' file, which
        identifies a package's packager
    pgpsig: str
        The attribute can be used to describe the (required) data below a %PGPSIG% identifier in a 'desc' file, which
        identifies a package's PGP signature
    provides: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %PROVIDES% identifier in a 'desc' file, which
        identifies what other package(s) a package provides
    replaces: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %REPLACES% identifier in a 'desc' file, which
        identifies what other package(s) a package replaces
    sha256sum: str
        The attribute can be used to describe the (required) data below an %SHA256SUM% identifier in a 'desc' file,
        which identifies a package's sha256 checksum
    url: str
        The attribute can be used to describe the (required) data below a %URL% identifier in a 'desc' file, which
        identifies a package's URL
    version: str
        The attribute can be used to describe the (required) data below a %VERSION% identifier in a 'desc' file, which
        identifies a package's version (this is the accumulation of epoch, pkgver and pkgrel)
    """

    def get_output_package(self, files: Optional[Files]) -> OutputPackage:
        """Transform the PackageDesc model and an optional Files model into an OutputPackage model

        Parameters
        ----------
        files: Optional[Files]:
            A pydantic model, that represents the list of files, that belong to the package described by self

        Returns
        -------
        OutputPackage
            A pydantic model, that describes a package and its list of files
        """

        desc_dict = self.dict()
        # remove attributes, that are represented on the pkgbase level
        for name in ["base", "makedepends", "packager", "version"]:
            if desc_dict.get(name):
                del desc_dict[name]

        if files:
            return OutputPackage(**desc_dict, **files.dict())
        else:
            return OutputPackage(**desc_dict)


class RepoDbMemberData(Name, RepoDbMemberType):
    """A model describing a set of attributes to provide the data of a 'desc' or 'files' file

    Attributes
    ----------
    name: str
        A package name
    member_type: defaults.RepoDbMemberType
        A member of the IntEnum defaults.RepoDbMemberType
    data: io.StringIO
        The contents of a 'desc' or 'files' file provided as a StringIO instance
    """

    data: io.StringIO

    class Config:
        arbitrary_types_allowed = True


class OutputPackageBase(
    Base,
    MakeDepends,
    Packager,
    Version,
):
    """A model describing all required attributes for an output file, that describes a list of packages based upon a
    pkgbase

    Attributes
    ----------
    base: str
        The attribute can be used to describe the (required) data below a %BASE% identifier in a 'desc' file, which
        identifies a package's pkgbase
    makedepends: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %MAKEDEPENDS% identifier in a 'desc' file,
        which identifies a package's makedepends
    packager: str
        The attribute can be used to describe the (required) data below a %PACKAGER% identifier in a 'desc' file, which
        identifies a package's packager
    packages: List[OutputPackage]
        A list of OutputPackage instances that belong to the pkgbase identified by base
    version: str
        The attribute can be used to describe the (required) data below a %VERSION% identifier in a 'desc' file, which
        identifies a package's version (this is the accumulation of epoch, pkgver and pkgrel)
    """

    packages: List[OutputPackage]

    async def get_packages_as_models(self) -> List[Tuple[PackageDesc, Files]]:
        """Return the list of packages as tuples of PackageDesc and Files models

        Returns
        -------
        List[Tuple[PackageDesc, Files]]
            A list of tuples with one PackageDesc and one Files each
        """

        return [
            (
                PackageDesc(
                    arch=package.arch,
                    backup=package.backup,
                    base=self.base,
                    builddate=package.builddate,
                    checkdepends=package.checkdepends,
                    conflicts=package.conflicts,
                    csize=package.csize,
                    depends=package.depends,
                    desc=package.desc,
                    filename=package.filename,
                    groups=package.groups,
                    isize=package.isize,
                    license=package.license,
                    makedepends=self.makedepends,
                    md5sum=package.md5sum,
                    name=package.name,
                    optdepends=package.optdepends,
                    packager=self.packager,
                    pgpsig=package.pgpsig,
                    provides=package.provides,
                    replaces=package.replaces,
                    sha256sum=package.sha256sum,
                    url=package.url,
                    version=self.version,
                ),
                Files(files=package.files),
            )
            for package in self.packages
        ]


class Architecture(BaseModel):
    """A model describing a single "architecture" attribute

    Attributes
    ----------
    architecture: Path
        A string describing a valid architecture for a repository
    """

    architecture: Optional[str]

    @validator("architecture")
    def validate_architecture(cls, architecture: Optional[str]) -> Optional[str]:
        if architecture is None:
            return architecture
        if architecture not in defaults.ARCHITECTURES:
            raise ValueError(
                f"The architecture '{architecture}' is not supported (must be one of {defaults.ARCHITECTURES}"
            )
        return architecture


class Directory(BaseModel):
    """A model describing a single "directory" attribute

    Attributes
    ----------
    directory: Path
        A Path instance that identifies an absolute directory location for e.g. binary packages or source tarball data
    """

    directory: Path

    @validator("directory")
    def validate_directory(cls, directory: Path) -> Path:
        """A validator for the directory attribute

        Parameters
        ----------
        directory: Path
            A Path instance to validate

        Raises
        ------
        ValueError
            If directory is not absolute, not a directory, not writable, or if the directory's parent is not writable
            (in case the directory does not exist yet

        Returns
        -------
        Path
            A validated Path instances representing an absolute directory
        """

        if not directory.is_absolute():
            raise ValueError(f"The directory '{directory}' is not an absolute path.")
        if directory.exists():
            if not directory.is_dir():
                raise ValueError(f"Not a directory: '{directory}'.")
            if not os.access(directory, os.W_OK):
                raise ValueError(f"The directory '{directory}' is not writable.")
        else:
            if not directory.parent.exists():
                raise ValueError(f"The parent directory of '{directory}' does not exist")
            if not directory.parent.is_dir():
                raise ValueError(f"The parent of '{directory}' is not a directory.")
            if not os.access(directory.parent, os.W_OK):
                raise ValueError(f"The parent directory of '{directory}' is not writable.")

        return directory


class PackagePool(BaseModel):
    """A model describing a single "package_pool" attribute

    Attributes
    ----------
    package_pool: Path
        An optional Path instance that identifies an absolute directory location for package tarball data
    """

    package_pool: Optional[Path]

    @validator("package_pool")
    def validate_package_pool(cls, package_pool: Optional[Path]) -> Optional[Path]:
        """A validator for the package_pool attribute

        Parameters
        ----------
        package_pool: Optional[Path]
            An optional Path instance to validate. If a Path instance is provided, Directory.validate_directory() is
            used for validation

        Returns
        -------
        Optional[Path]
            A validated Path instance, if a Path is provided, else None
        """

        if package_pool is None:
            return package_pool
        else:
            return Path(Directory.validate_directory(directory=package_pool))


class SourcePool(BaseModel):
    """A model describing a single "source_pool" attribute

    Attributes
    ----------
    source_pool: Path
        An optional Path instance that identifies an absolute directory location for source tarball data
    """

    source_pool: Optional[Path]

    @validator("source_pool")
    def validate_source_pool(cls, source_pool: Optional[Path]) -> Optional[Path]:
        """A validator for the source_pool attribute

        Parameters
        ----------
        source_pool: Optional[Path]
            An optional Path instance to validate. If a Path instance is provided, Directory.validate_directory() is
            used for validation

        Returns
        -------
        Optional[Path]
            A validated Path instance, if a Path is provided, else None
        """

        if source_pool is None:
            return source_pool
        else:
            return Path(Directory.validate_directory(directory=source_pool))


class ManagementRepo(Directory):
    """A model describing all required attributes to describe a repository used for managing one or more package
    repositories

    Attributes
    ----------
    directory: Path
        A Path instance describing the location of the management repository
    url: AnyUrl
        A URL describing the VCS upstream of the management repository
    """

    url: AnyUrl

    @validator("url")
    def validate_url(cls, url: AnyUrl) -> AnyUrl:
        """A validator for the url attribute

        Parameters
        ----------
        url: AnyUrl
            An instance of AnyUrl, that describes an upstream repository URL

        Raises
        ------
        ValueError
            If the url scheme is not one of "https" or "ssh" or if the url scheme is "ssh", but no user is provided in
            the URL string

        Returns
        -------
        AnyUrl
            A validated instance of AnyUrl
        """

        valid_schemes = ["https", "ssh"]
        if url.scheme not in valid_schemes:
            raise ValueError(
                f"The scheme '{url.scheme}' of the url ({url}) is not valid (must be one of {valid_schemes})"
            )
        if url.scheme == "ssh" and not url.user:
            raise ValueError(f"When using ssh a user is required (but none is provided): '{url}'")

        return url


class PackageRepo(Architecture, PackagePool, SourcePool):
    """A model providing all required attributes to describe a package repository

    Attributes
    ----------
    architecture: Optional[str]
        An optional string, that serves as an override to the application-wide architecture.
        The attribute defines the CPU architecture for the package repository
    package_pool: Optional[Path]
        An optional directory, that serves as an override to the application-wide package_pool.
        The attribute defines the location to store the binary packages and their signatures in
    source_pool: Optional[Path]
        An optional directory, that serves as an override to the application-wide source_pool.
        The attribute defines the location to store the source tarballs in
    name: str
        The required name of a package repository
    staging: Optional[str]
        The optional name of a staging repository associated with a package repository
    testing: Optional[str]
        The optional name of a testing repository associated with a package repository
    management_repo: Optional[ManagementRepo]
        An optional instance of ManagementRepo, that serves as an override to the application-wide management_repo
        The attribute defines the directory and upstream VCS repository that is used to track changes to a package
        repository
    """

    name: Path
    staging: Optional[Path]
    testing: Optional[Path]
    management_repo: Optional[ManagementRepo]

    @validator("name")
    def validate_name(cls, name: Union[Path, str]) -> Path:
        """A validator for the name attribute, which converts string input to a valid Path

        Parameters
        ----------
        name: Path
            A Path instance name string to validate

        Raises
        ------
        ValueError
            If the path name is an empty string, is absolute, consists of a directory structure, starts with one of the
            disallowed characters (".", "-"), or is not a lower-case, alphanumeric (plus "_" and "-") string.

        Returns
        Path
            A validated name string
        """

        if isinstance(name, str):
            name = Path(name)

        if len(name.name) == 0:
            raise ValueError("The package repository can not be an empty string.")

        if name.is_absolute():
            raise ValueError("The package repository name '{name.name}' can not be an absolute path.")

        if len(name.parts) > 1:
            raise ValueError("The package repository name '{name.name}' can not describe a directory structure.")

        disallowed_start_chars = [".", "-"]
        for char in disallowed_start_chars:
            if name.name.startswith(char):
                raise ValueError(
                    f"The package repository name '{name}' can not start with any of '{disallowed_start_chars}'."
                )

        allowed_chars = ["_", "-"]
        remaining_chars: List[str] = []
        for char in name.name:
            if (
                not char.isalnum() or (not char.isdigit() and not char.islower()) or char.isspace()
            ) and char not in allowed_chars:
                remaining_chars += [char]
        if remaining_chars:
            raise ValueError(
                f"The package repository name '{name}' can not contain '{remaining_chars}' "
                f"but must consist only of alphanumeric chars and any of '{allowed_chars}'."
            )

        return name

    @validator("staging", "testing", pre=True)
    def validate_optional_staging_testing(cls, name: Optional[Path]) -> Optional[Path]:
        """A validator for the optional staging and testing attributes

        Parameters
        ----------
        name: Optional[Path]
            An optional relative Path to validate. If a string is provided, PackageRepo.validate_name() is used.

        Returns
        -------
        Optional[Path]
            A validated name string, else None
        """

        if name is None:
            return name
        else:
            return Path(PackageRepo.validate_name(name=name))

    @root_validator
    def validate_unique_staging_testing(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """A root validator for the optional staging and testing attributes ensuring both are not the same string

        Parameters
        ----------
        values: Dict[str, Any]
            A dict with all values of the PackageRepo instance

        Raises
        ------
        ValueError
            If staging and testing are the same string

        Returns
        -------
        values: Dict[str, Any]
            The unmodified dict with all values of the PackageRepo instance
        """

        name, staging, testing = values.get("name"), values.get("staging"), values.get("testing")
        if staging and testing and staging == testing:
            raise ValueError(
                f"The testing repository '{testing.name}' is the same as the staging repository '{staging.name}'"
            )
        if name and staging and name == staging:
            raise ValueError(
                f"The staging repository '{staging.name}' is the same as the stable repository '{name.name}'"
            )
        if name and testing and name == testing:
            raise ValueError(
                f"The testing repository '{testing.name}' is the same as the stable repository '{name.name}'"
            )
        return values

    @root_validator
    def validate_unique_package_pool_source_pool(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """A root validator for the optional package_pool and source_pool attributes ensuring both are not the same Path

        Parameters
        ----------
        values: Dict[str, Any]
            A dict with all values of the PackageRepo instance

        Raises
        ------
        ValueError
            If package_pool and source_pool are the same Path

        Returns
        -------
        values: Dict[str, Any]
            The unmodified dict with all values of the PackageRepo instance
        """

        source_pool, package_pool = values.get("source_pool"), values.get("package_pool")
        if source_pool and package_pool and source_pool == package_pool:
            raise ValueError(f"The package pool '{package_pool}' is the same as the source pool '{source_pool}'")
        return values

    @root_validator
    def validate_unique_management_repo_directory(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """A root validator for the optional management_repo, package_pool and source_pool attributes ensuring the first
        does not use the same directory as the latter two

        Parameters
        ----------
        values: Dict[str, Any]
            A dict with all values of the PackageRepo instance

        Raises
        ------
        ValueError
            If management_repo.directory is the same Path as either package_pool or source_pool

        Returns
        -------
        values: Dict[str, Any]
            The unmodified dict with all values of the PackageRepo instance
        """

        management_repo, package_pool, source_pool = (
            values.get("management_repo"),
            values.get("package_pool"),
            values.get("source_pool"),
        )
        if management_repo and package_pool and management_repo.directory == package_pool:
            raise ValueError(
                f"The management_repo location '{management_repo.directory}' is "
                f"the same as the package pool '{package_pool}'"
            )
        if management_repo and source_pool and management_repo.directory == source_pool:
            raise ValueError(
                f"The management_repo location '{management_repo.directory}' is "
                f"the same as the source pool '{source_pool}'"
            )
        return values
