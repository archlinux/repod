import io
from typing import List, Optional, Tuple

from pyalpm import vercmp
from pydantic import BaseModel, validator

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

    def get_packages_as_models(self) -> List[Tuple[PackageDesc, Files]]:
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
