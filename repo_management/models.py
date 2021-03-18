import io
from typing import List, Optional, Tuple

from pydantic import BaseModel

from repo_management import defaults


class Base(BaseModel):
    """A model describing the %BASE% header in a 'desc' file, which type it represents and whether it is required or
    not"""

    base: str


class Version(BaseModel):
    """A model describing the %VERSION% header in a 'desc' file, which type it represents and whether it is required or
    not"""

    version: str


class MakeDepends(BaseModel):
    """A model describing the %MAKEDEPENDS% header in a 'desc' file, which type it represents and whether it is required
    or not"""

    makedepends: Optional[List[str]]


class CheckDepends(BaseModel):
    """A model describing the %CHECKDEPENDS% header in a 'desc' file, which type it represents and whether it is
    required or not"""

    checkdepends: Optional[List[str]]


class FileName(BaseModel):
    """A model describing the %FILENAME% header in a 'desc' file, which type it represents and whether it is required or
    not"""

    filename: str


class Name(BaseModel):
    """A model describing the %NAME% header in a 'desc' file, which type it represents and whether it is required or
    not"""

    name: str


class Desc(BaseModel):
    """A model describing the %DESC% header in a 'desc' file, which type it represents and whether it is required or
    not"""

    desc: str


class Groups(BaseModel):
    """A model describing the %GROUPS% header in a 'desc' file, which type it represents and whether it is required or
    not"""

    groups: Optional[List[str]]


class CSize(BaseModel):
    """A model describing the %CSIZE% header in a 'desc' file, which type it represents and whether it is required or
    not"""

    csize: int


class ISize(BaseModel):
    """A model describing the %ISIZE% header in a 'desc' file, which type it represents and whether it is required or
    not"""

    isize: int


class Md5Sum(BaseModel):
    """A model describing the %MD5SUM% header in a 'desc' file, which type it represents and whether it is required or
    not"""

    md5sum: str


class Sha256Sum(BaseModel):
    """A model describing the %SHA256SUM% header in a 'desc' file, which type it represents and whether it is required
    or not"""

    sha256sum: str


class PgpSig(BaseModel):
    """A model describing the %PGPSIG% header in a 'desc' file, which type it represents and whether it is required or
    not"""

    pgpsig: str


class Url(BaseModel):
    """A model describing the %URL% header in a 'desc' file, which type it represents and whether it is required or
    not"""

    url: str


class License(BaseModel):
    """A model describing the %LICENSE% header in a 'desc' file, which type it represents and whether it is required or
    not"""

    license: Optional[List[str]]


class Arch(BaseModel):
    """A model describing the %ARCH% header in a 'desc' file, which type it represents and whether it is required or
    not"""

    arch: str


class BuildDate(BaseModel):
    """A model describing the %BUILDDATE% header in a 'desc' file, which type it represents and whether it is required
    or not"""

    builddate: int


class Packager(BaseModel):
    """A model describing the %PACKAGER% header in a 'desc' file, which type it represents and whether it is required
    or not"""

    packager: str


class Replaces(BaseModel):
    """A model describing the %REPLACES% header in a 'desc' file, which type it represents and whether it is required or
    not"""

    replaces: Optional[List[str]]


class Conflicts(BaseModel):
    """A model describing the %CONFLICTS% header in a 'desc' file, which type it represents and whether it is required or
    not"""

    conflicts: Optional[List[str]]


class Provides(BaseModel):
    """A model describing the %PROVIDES% header in a 'desc' file, which type it represents and whether it is required or
    not"""

    provides: Optional[List[str]]


class Depends(BaseModel):
    """A model describing the %DEPENDS% header in a 'desc' file, which type it represents and whether it is required or
    not"""

    depends: Optional[List[str]]


class OptDepends(BaseModel):
    """A model describing the %OPTDEPENDS% header in a 'desc' file, which type it represents and whether it is required
    or not"""

    optdepends: Optional[List[str]]


class Backup(BaseModel):
    """A model describing the %BACKUP% header in a 'desc' file, which type it represents and whether it is required
    or not"""

    backup: Optional[List[str]]


class Files(BaseModel):
    """A model describing the %FILES% header in a 'files' file, which type it represents and whether it is required or
    not"""

    files: Optional[List[str]]


class PackageFiles(Name, Files):
    pass


class OutputPackage(
    Arch,
    Backup,
    BuildDate,
    Conflicts,
    CSize,
    Depends,
    Desc,
    CheckDepends,
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
    """A model describing all required attributes for a package in the context of an output file, that describes a
    (potential) list of packages based upon its pkgbase
    """

    pass


class PackageDesc(
    Arch,
    Backup,
    Base,
    BuildDate,
    Conflicts,
    CSize,
    Depends,
    Desc,
    CheckDepends,
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
    """A model describing all headers in a 'desc' file, which type they represent and whether they are required or
    not"""

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


class RepoDbMemberType(BaseModel):
    """A model describing an attribute used to identify/ distinguish different types of repo database file types (e.g.
    'desc' and 'files' files, which are contained in a repository database file).
    The file types are distinguished with the help of the IntEnum defaults.REpoDbFileType
    """

    member_type: defaults.RepoDbMemberType


class RepoDbMemberData(Name, RepoDbMemberType):
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
