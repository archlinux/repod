import re
from typing import List, Optional

from email_validator import EmailNotValidError, validate_email
from pyalpm import vercmp
from pydantic import BaseModel, HttpUrl, NonNegativeInt, conint, constr, validator

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
            validate_email(email)
        except EmailNotValidError as e:
            raise ValueError(f"The packager email is not valid: {email}\n{e}")

        return packager


class PgpSig(BaseModel):
    """A model describing a single 'pgpsig' attribute

    Attributes
    ----------
    pgpsig: str
        The attribute can be used to describe the (required) data below a %PGPSIG% identifier in a 'desc' file, which
        identifies a package's PGP signature
    """

    pgpsig: constr(regex=f"^{BASE64}$")  # type: ignore[valid-type]  # noqa: F722


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


class Version(BaseModel):
    """A model describing a single 'version' attribute

    Attributes
    ----------
    version: str
        The attribute can be used to describe the (required) data below a %VERSION% identifier in a 'desc' file, which
        identifies a package's version (this is the accumulation of epoch, pkgver and pkgrel)
    """

    version: constr(regex=rf"^({EPOCH}|){VERSION}-{PKGREL}$")  # type: ignore[valid-type]  # noqa: F722

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

        return True if vercmp(self.version, version) < 0 else False

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

        return True if vercmp(self.version, version) > 0 else False
