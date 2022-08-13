from __future__ import annotations

import re
from typing import List, Optional

from email_validator import EmailNotValidError, validate_email
from pydantic import (
    BaseModel,
    HttpUrl,
    NonNegativeInt,
    PositiveInt,
    conint,
    constr,
    validator,
)

from repod.common.regex import (
    ARCHITECTURE,
    BASE64,
    EPOCH,
    FILENAME,
    MD5,
    PACKAGE_NAME,
    PACKAGER_NAME,
    PKGREL,
    RELATIVE_PATH,
    SHA256,
    VERSION,
)
from repod.version import alpm
from repod.version.util import cmp


class Arch(BaseModel):
    """A model describing a single 'arch' attribute

    Attributes
    ----------
    arch: str
        The attribute can be used to describe the (required) data below an %ARCH% identifier in a 'desc' file, which
        identifies a package's architecture
    """

    arch: constr(regex=f"^{ARCHITECTURE}$")  # type: ignore[valid-type]  # noqa: F722


class Backup(BaseModel):
    """A model describing a single 'backup' attribute

    Attributes
    ----------
    backup: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %BACKUP% identifier in a 'desc' file, which
        identifies which file(s) of a package pacman will create backups for
    """

    backup: Optional[List[constr(regex=f"^{RELATIVE_PATH}$")]]  # type: ignore[valid-type]  # noqa: F722


class Base(BaseModel):
    """A model describing a single 'base' attribute

    Attributes
    ----------
    base: str
        The attribute can be used to describe the (required) data below a %BASE% identifier in a 'desc' file, which
        identifies a package's pkgbase
    """

    base: constr(regex=f"^{PACKAGE_NAME}$")  # type: ignore[valid-type]  # noqa: F722


class BuildDate(BaseModel):
    """A model describing a single 'builddate' attribute

    Attributes
    ----------
    builddate: int
        The attribute can be used to describe the (required) data below a %BUILDDATE% identifier in a 'desc' file,
        which identifies a package's build date (represented in seconds since the epoch)
    """

    builddate: NonNegativeInt


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

    csize: NonNegativeInt


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

    filename: constr(regex=f"^{FILENAME}$")  # type: ignore[valid-type]  # noqa: F722


class FileList(BaseModel):
    """A model describing an optional list of files

    Attributes
    ----------
    files: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %FILES% identifier in a 'files' file, which
        identifies which file(s) belong to a package
    """

    files: Optional[List[constr(regex=f"^{RELATIVE_PATH}$")]]  # type: ignore[valid-type]  # noqa: F722

    @validator("files")
    def validate_no_file_in_home(cls, files: List[str]) -> Optional[List[str]]:
        if files:
            for file in files:
                if re.search("^(home/).+$", file):
                    raise ValueError("A package must not provide files in /home")

        return files


class Groups(BaseModel):
    """A model describing a single 'groups' attribute

    Attributes
    ----------
    groups: Optional[List[str]]
        The attribute can be used to describe the (optional) data below a %GROUPS% identifier in a 'desc' file, which
        identifies a package's groups
    """

    groups: Optional[List[constr(regex=f"^{PACKAGE_NAME}$")]]  # type: ignore[valid-type]  # noqa: F722


class ISize(BaseModel):
    """A model describing a single 'isize' attribute

    Attributes
    ----------
    isize: int
        The attribute can be used to describe the (required) data below an %ISIZE% identifier in a 'desc' file, which
        identifies a package's installed size
    """

    isize: NonNegativeInt


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

    md5sum: constr(regex=MD5)  # type: ignore[valid-type]


class Name(BaseModel):
    """A model describing a single 'name' attribute

    Attributes
    ----------
    name: str
        The attribute can be used to describe the (required) data below a %NAME% identifier in a 'desc' file, which
        identifies a package's name
    """

    name: constr(regex=f"^{PACKAGE_NAME}$")  # type: ignore[valid-type]  # noqa: F722


class Packager(BaseModel):
    """A model describing a single 'packager' attribute

    Attributes
    ----------
    packager: str
        The attribute can be used to describe the (required) data below a %PACKAGER% identifier in a 'desc' file, which
        identifies a package's packager
    """

    packager: constr(regex=(rf"^{PACKAGER_NAME}\s<(.*)>$"))  # type: ignore[valid-type]  # noqa: F722

    @validator("packager")
    def validate_packager_has_valid_email(cls, packager: str) -> str:

        email = packager.replace(">", "").split("<")[1]
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError as e:
            raise ValueError(f"The packager email is not valid: {email}\n{e}")

        return packager


class PgpSig(BaseModel):
    """A model describing a single 'pgpsig' attribute

    Attributes
    ----------
    pgpsig: str
        The attribute can be used to describe the (optional) data below a %PGPSIG% identifier in a 'desc' file, which
        identifies a package's PGP signature
    """

    pgpsig: Optional[constr(regex=f"^{BASE64}$")]  # type: ignore[valid-type]  # noqa: F722


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


class SchemaVersionV1(BaseModel):
    """A model describing a schema version 1

    Attributes
    ----------
    schema_version: PositiveInt
        A schema version - 1 - for a model
    """

    schema_version: conint(ge=1, le=1) = 1  # type: ignore[valid-type]


class SchemaVersionV2(BaseModel):
    """A model describing a schema version 2

    Attributes
    ----------
    schema_version: PositiveInt
        A schema version - 2 - for a model
    """

    schema_version: conint(ge=2, le=2) = 2  # type: ignore[valid-type]


class Sha256Sum(BaseModel):
    """A model describing a single 'sha256sum' attribute

    Attributes
    ----------
    sha256sum: str
        The attribute can be used to describe the (required) data below an %SHA256SUM% identifier in a 'desc' file,
        which identifies a package's sha256 checksum
    """

    sha256sum: constr(regex=SHA256)  # type: ignore[valid-type]


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

    url: HttpUrl


class Epoch(BaseModel):
    """A model dscribing a single 'epoch' attribute

    The epoch denotes a downgrade in version of a given package (a version with an epoch trumps one without)

    Attributes
    ----------
    epoch: PositiveInt
        A string representing a valid epoch of a package
    """

    epoch: PositiveInt

    def vercmp(self, epoch: Epoch) -> int:
        """Compare the epoch with another

        The comparison algorithm is based on pyalpm's/ pacman's vercmp behavior.

        Returns
        -------
        int
            -1 if self.epoch is older than epoch
            0 if self.epoch is equal to epoch
            1 if self.epoch is newer than epoch
        """

        return cmp(self.epoch, epoch.epoch)


class PkgRel(BaseModel):
    """A model dscribing a single 'pkgrel' attribute

    The pkgrel denotes the build version of a given package

    Attributes
    ----------
    pkgrel: str
        A string representing a valid pkgrel of a package
    """

    pkgrel: constr(regex=rf"^{PKGREL}$")  # type: ignore[valid-type]  # noqa: F722

    def as_list(self) -> List[str]:
        """Return the pkgrel components as list

        The version string is split by "."

        Returns
        -------
        List[str]
            A list of strings representing the components of the pkgrel
        """

        return [str(part) for part in self.pkgrel.split(".")]

    def vercmp(self, pkgrel: PkgRel) -> int:
        """Compare the pkgrel with another

        The comparison algorithm is based on pyalpm's/ pacman's vercmp behavior.

        Returns
        -------
        int
            -1 if self.pkgrel is older than pkgrel
            0 if self.pkgrel is equal to pkgrel
            1 if self.pkgrel is newer than pkgrel
        """

        return alpm.vercmp(self.pkgrel, pkgrel.pkgrel)


class PkgVer(BaseModel):
    """A model dscribing a single 'pkgver' attribute

    The pkgver denotes the upstream version of a given package

    Attributes
    ----------
    pkgver: str
        A string representing a valid pkgver of a package
    """

    pkgver: constr(regex=rf"^({VERSION})$")  # type: ignore[valid-type]  # noqa: F722

    def as_list(self) -> List[str]:
        """Return the pkgver components as list

        The version string is split on none alpanum characters

        Returns
        -------
        List[str]
            A list of strings representing the components of the pkgver
        """

        return [part for part in re.split(r"[^a-zA-Z\d]", self.pkgver) if part]

    def vercmp(self, pkgver: PkgVer) -> int:
        """Compare the pkgver with another

        The comparison algorithm is based on pyalpm's/ pacman's vercmp behavior.
        If PYALPM_VERCMP is True, pyalpm has been imported and its implementation of vercmp() is used.

        Returns
        -------
        int
            -1 if self.pkgver is older than pkgver
            0 if self.pkgver is equal to pkgver
            1 if self.pkgver is newer than pkgver
        """

        return alpm.vercmp(self.pkgver, pkgver.pkgver)


class Version(BaseModel):
    """A model describing a single 'version' attribute

    Attributes
    ----------
    version: str
        The attribute can be used to describe the (required) data below a %VERSION% identifier in a 'desc' file, which
        identifies a package's version (this is the accumulation of epoch, pkgver and pkgrel)
    """

    version: constr(regex=rf"^({EPOCH}|){VERSION}-{PKGREL}$")  # type: ignore[valid-type]  # noqa: F722

    def get_epoch(self) -> Optional[Epoch]:
        """Return the epoch of the version

        Returns
        -------
        Optional[int]
            An optional string representing the epoch of the version
        """

        if ":" in self.version:
            return Epoch(epoch=self.version.split(":")[0])
        else:
            return None

    def get_pkgver(self) -> PkgVer:
        """Return the pkgver of the version

        Returns
        -------
        PkgVer
            A PkgVer representing the pkgver of the version
        """

        pkgver_pkgrel = self.version.split(":")[1] if ":" in self.version else self.version
        return PkgVer(pkgver=str(pkgver_pkgrel.split("-")[0]))

    def get_pkgrel(self) -> PkgRel:
        """Return the pkgrel of the version

        Returns
        -------
        PkgRel
            A PkgRel representing the pkgrel of the version
        """

        pkgver_pkgrel = self.version.split(":")[1] if ":" in self.version else self.version
        return PkgRel(pkgrel=str(pkgver_pkgrel.split("-")[1]))

    def vercmp(self, version: Version) -> int:
        """Compare the version with another

        The comparison algorithm is based on pyalpm's/ pacman's vercmp behavior.
        If PYALPM_VERCMP is True, pyalpm has been imported and its implementation of vercmp() is used.

        Returns
        -------
        int
            -1 if self.version is older than version
            0 if self.version is equal to version
            1 if self.version is newer than version
        """

        return alpm.pkg_vercmp(self.version, version.version)

    def is_older_than(self, version: Version) -> bool:
        """Check whether the version is older than a provided version

        Parameters
        ----------
        version: Version
            Another version to compare that of self to

        Returns
        -------
        True if self.version is older than the provided version, False otherwise.
        """

        return True if self.vercmp(version=version) < 0 else False

    def is_newer_than(self, version: Version) -> bool:
        """Check whether the version is newer than a provided version

        Parameters
        ----------
        version: Version
            Another version to compare that of self to

        Returns
        -------
        True if self.version is newer than the provided version, False otherwise.
        """

        return True if self.vercmp(version=version) > 0 else False
