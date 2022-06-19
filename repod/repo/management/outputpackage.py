from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, ValidationError

from repod import errors
from repod.common.models import (
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
    SchemaVersionV1,
    Sha256Sum,
    Url,
    Version,
)
from repod.repo.package.syncdb import Files, FilesV1, PackageDesc, PackageDescV1

OUTPUT_PACKAGE_BASE_VERSIONS: Dict[int, Dict[str, Union[int, Set[str]]]] = {
    1: {
        "required": {
            "base",
            "makedepends",
            "packager",
            "packages",
            "version",
        },
        "files_version": 1,
        "output_package_version": 1,
        "package_desc_version": 1,
    },
}
DEFAULT_OUTPUT_PACKAGE_BASE_VERSION = 1


class OutputPackage(BaseModel):
    """A template class to describe all required attributes that define a package in the context of an output file

    This class should not be instantiated directly. Use one of its subclasses instead!
    """

    pass


class OutputPackageV1(
    OutputPackage,
    Arch,
    Backup,
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
    Md5Sum,
    Name,
    OptDepends,
    PgpSig,
    Provides,
    Replaces,
    SchemaVersionV1,
    Sha256Sum,
    Url,
):
    """A model describing all required attributes that define a package in the context of an output file (version 1)

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
    schema_version: PositiveInt
        A positive integer - 1 - identifying the schema version of the object
    sha256sum: str
        The attribute can be used to describe the (required) data below an %SHA256SUM% identifier in a 'desc' file,
        which identifies a package's sha256 checksum
    url: str
        The attribute can be used to describe the (required) data below a %URL% identifier in a 'desc' file, which
        identifies a package's URL
    """

    files: Optional[Files] = None


class OutputPackageBase(BaseModel):
    """A template class with helper methods to create instances of one of its (versioned) subclasses

    This class should not be instantiated directly, as it only provides generic instance methods for its subclasses.

    NOTE: The `from_dict()` classmethod is used to create one of the versioned subclasses.
    """

    @classmethod
    def from_dict(cls, data: Dict[str, Union[Any, List[Any]]]) -> OutputPackageBase:
        """Create an instance of one of OutputPackageBase's subclasses from a dict

        This method expects data derived from reading a pkgbase JSON file from the management repository.
        By default this method will prefer to create an instances of OutputPackageBase's subclasses as identified by
        DEFAULT_OUTPUT_PACKAGE_BASE_VERSION (if it is newer than the schema_version retrieved from the data).

        Parameters
        ----------
        data: Dict[str, Union[Any, List[Any]]]
            A dict containing data required to instantiate a subclass of OutputPackageBase

        Raises
        ------
        RepoManagementValidationError
            If an invalid schema_version is encountered when reading data
            If a ValidationError is encountered during instantiation of one of the OutputPackage subclasses
            If an unsupported schema_version is encountered

        Returns
        -------
        OutputPackageBase
            An instance of one of the subclasses of OutputPackageBase
        """

        def default_output_package_from_dict(version: int, package: Dict[str, Any]) -> OutputPackage:
            """Create the default OutputPackage subclass for a OutputPackageBase from a dict

            Parameters
            ----------
            version: int
                The schema_version of the OutputPackageBase subclass for which to create an instance of a subclass of
                OutputPackage
            package: Dict[str, Any]
                A dict describing the attributes of an OutputPackage instance

            Returns
            -------
            OutputPackage
                A subclass of OutputPackage that is the default for the given OutputPackageBase schema_version
            """

            output_versions: List[Optional[int]] = []
            output_versions.insert(
                0,
                OUTPUT_PACKAGE_BASE_VERSIONS[version]["output_package_version"],  # type: ignore[arg-type]
            )
            output_versions.insert(
                1,
                OUTPUT_PACKAGE_BASE_VERSIONS[version]["files_version"],  # type: ignore[arg-type]
            )
            match output_versions:
                case [1, 1]:
                    files = package.get("files")
                    if files:
                        if files.get("schema_version"):
                            del files["schema_version"]
                        package["files"] = FilesV1(**files)

                    return OutputPackageV1(**package)
                # NOTE: the catch all can never be reached but is here to satisfy our tooling
                case _:  # pragma: no cover
                    raise RuntimeError(f"Invalid version ({version} provided for OUTPUT_PACKAGE_BASE_VERSIONS.")

        used_schema_version = data.get("schema_version")
        if isinstance(used_schema_version, int):
            if DEFAULT_OUTPUT_PACKAGE_BASE_VERSION > used_schema_version:
                used_schema_version = DEFAULT_OUTPUT_PACKAGE_BASE_VERSION
                del data["schema_version"]
            elif DEFAULT_OUTPUT_PACKAGE_BASE_VERSION < used_schema_version:
                raise errors.RepoManagementValidationError(
                    f"The unsupported schema version ({used_schema_version}) has been encountered, when "
                    f"attempting to read data:\n{data}"
                )

        match used_schema_version:
            case 1:
                if isinstance(data.get("packages"), list):
                    data["packages"] = [
                        default_output_package_from_dict(version=used_schema_version, package=package)
                        for package in data.get("packages")  # type: ignore[union-attr]
                    ]
                try:
                    return OutputPackageBaseV1(**data)
                except ValidationError as e:
                    raise errors.RepoManagementValidationError(
                        "A validation error occured while attempting to instantiate an OutputPackageBaseV1 using data:"
                        f"\n'{data}'\n{e}"
                    )
            case _:
                raise errors.RepoManagementValidationError(
                    f"The unsupported schema version ({used_schema_version}) has been encountered, when "
                    f"attempting to read data:\n{data}"
                )

    def add_packages(self, packages: List[OutputPackage]) -> None:
        """Add packages to an instance of one of OutputPackageBase's subclasses

        NOTE: This method only operates successfully if the instance of the class using it actually defines the
        `packages` field! The OutputPackageBase class does not do that!

        Parameters
        ----------
        packages: List[OutputPackage]
            A list of OutputPackage instances to add

        Raises
        ------
        RuntimeError
            If called on the OutputPackageBase template class
        """

        if hasattr(self, "packages"):
            # TODO: only add OutputPackage subclasses that are compatible with the OutputPackageBase version, else
            # attempt conversion
            self.packages += packages  # type: ignore[attr-defined]
        else:
            raise RuntimeError("It is not possible to add packages to the template class OutputPackageBase!")

    def get_version(self) -> str:
        """Get version of an instance of one of OutputPackage's subclasses

        NOTE: This method only successfully returns if the instance of the class using it defines the `get_version`
        field! The OutputPackageBase class does not do that!

        Raises
        ------
        RuntimeError
            If called on the OutputPackageBase template class

        Returns
        -------
        str
            The version string of the OutputPackageBase
        """

        if hasattr(self, "version"):
            return str(self.version)  # type: ignore[attr-defined]
        else:
            raise RuntimeError(
                "It is not possible to return the version attribute of the template class OutputPackageBase!"
            )

    async def get_packages_as_models(self) -> List[Tuple[PackageDesc, Files]]:
        """Return the list of packages as tuples of PackageDesc and Files models

        Depending on the mapping in OUTPUT_PACKAGE_BASE_VERSIONS, which targets the schema_version of OutputPackageBase
        subclasses, different subclasses of PackageDesc are returned.

        NOTE: This method only successfully returns if the instance of the class using it defines the required fields!
        The OutputPackageBase class does not do that!

        Raises
        ------
        RuntimeError
            If an unknown schema_version is encountered in the OutputPackageBase instance
            If this method is called on the template class OutputPackageBase (instead of on one of its subclasses)

        Returns
        -------
        List[Tuple[PackageDesc, Files]]
            A list of tuples with one PackageDesc and one Files each
        """

        if hasattr(self, "schema_version"):
            output_versions: List[Optional[int]] = []
            schema_version = OUTPUT_PACKAGE_BASE_VERSIONS.get(self.schema_version)  # type: ignore[attr-defined]
            if schema_version:
                output_versions.insert(0, schema_version.get("package_desc_version"))  # type: ignore[arg-type]
                output_versions.insert(1, schema_version.get("files_version"))  # type: ignore[arg-type]

            match output_versions:
                case [1, 1]:
                    return [
                        (
                            PackageDescV1(
                                arch=package.arch,
                                backup=package.backup,
                                base=self.base,  # type: ignore[attr-defined]
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
                                makedepends=self.makedepends,  # type: ignore[attr-defined]
                                md5sum=package.md5sum,
                                name=package.name,
                                optdepends=package.optdepends,
                                packager=self.packager,  # type: ignore[attr-defined]
                                pgpsig=package.pgpsig,
                                provides=package.provides,
                                replaces=package.replaces,
                                sha256sum=package.sha256sum,
                                url=package.url,
                                version=self.version,  # type: ignore[attr-defined]
                            ),
                            FilesV1(files=package.files.files if package.files else []),
                        )
                        for package in self.packages  # type: ignore[attr-defined]
                    ]
                case _:
                    raise RuntimeError(
                        f"Unknown schema_version ({self.schema_version}) provided "  # type: ignore[attr-defined]
                        "while attempting to retrieve packages and their files from an instance of "
                        f"'{self.__class__.__name__}'!"
                    )
        else:
            raise RuntimeError(
                "Packages and their files can not be retrieved from the templatae class OutputPackageBase!"
            )


class OutputPackageBaseV1(
    OutputPackageBase,
    Base,
    MakeDepends,
    Packager,
    SchemaVersionV1,
    Version,
):
    """A model describing all required attributes for an output file, that describes a list of packages based upon a
    pkgbase (version 1)

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
    schema_version: PositiveInt
        A positive integer - 1 - identifying the schema version of the object
    version: str
        The attribute can be used to describe the (required) data below a %VERSION% identifier in a 'desc' file, which
        identifies a package's version (this is the accumulation of epoch, pkgver and pkgrel)
    """

    packages: List[OutputPackage]


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

    classes = [OutputPackageV1, OutputPackageBaseV1]

    if isinstance(output, str):
        output = Path(output)

    if not output.exists():
        raise RuntimeError(f"The output directory {output} must exist!")

    for class_ in classes:
        with open(output / f"{class_.__name__}.json", "w") as f:
            print(class_.schema_json(indent=2), file=f)
