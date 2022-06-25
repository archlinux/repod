from __future__ import annotations

import io
from enum import IntEnum
from logging import debug, warning
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from jinja2 import Environment, PackageLoader, TemplateNotFound
from pydantic import BaseModel, ValidationError

from repod.common.enums import FieldTypeEnum
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
    FileList,
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
from repod.errors import (
    RepoManagementFileError,
    RepoManagementFileNotFoundError,
    RepoManagementValidationError,
)
from repod.repo.management import outputpackage

DESC_JSON: Dict[str, Tuple[str, FieldTypeEnum]] = {
    "%BASE%": ("base", FieldTypeEnum.STRING),
    "%VERSION%": ("version", FieldTypeEnum.STRING),
    "%MAKEDEPENDS%": ("makedepends", FieldTypeEnum.STRING_LIST),
    "%CHECKDEPENDS%": ("checkdepends", FieldTypeEnum.STRING_LIST),
    "%FILENAME%": ("filename", FieldTypeEnum.STRING),
    "%NAME%": ("name", FieldTypeEnum.STRING),
    "%DESC%": ("desc", FieldTypeEnum.STRING),
    "%GROUPS%": ("groups", FieldTypeEnum.STRING_LIST),
    "%CSIZE%": ("csize", FieldTypeEnum.INT),
    "%ISIZE%": ("isize", FieldTypeEnum.INT),
    "%MD5SUM%": ("md5sum", FieldTypeEnum.STRING),
    "%SHA256SUM%": ("sha256sum", FieldTypeEnum.STRING),
    "%PGPSIG%": ("pgpsig", FieldTypeEnum.STRING),
    "%URL%": ("url", FieldTypeEnum.STRING),
    "%LICENSE%": ("license", FieldTypeEnum.STRING_LIST),
    "%ARCH%": ("arch", FieldTypeEnum.STRING),
    "%BUILDDATE%": ("builddate", FieldTypeEnum.INT),
    "%PACKAGER%": ("packager", FieldTypeEnum.STRING),
    "%REPLACES%": ("replaces", FieldTypeEnum.STRING_LIST),
    "%CONFLICTS%": ("conflicts", FieldTypeEnum.STRING_LIST),
    "%PROVIDES%": ("provides", FieldTypeEnum.STRING_LIST),
    "%DEPENDS%": ("depends", FieldTypeEnum.STRING_LIST),
    "%OPTDEPENDS%": ("optdepends", FieldTypeEnum.STRING_LIST),
    "%BACKUP%": ("backup", FieldTypeEnum.STRING_LIST),
}
FILES_JSON: Dict[str, Tuple[str, FieldTypeEnum]] = {"%FILES%": ("files", FieldTypeEnum.STRING_LIST)}
FILES_VERSIONS: Dict[int, Dict[str, Set[str]]] = {
    1: {
        "required": {
            "files",
        },
        "optional": set(),
    },
}
DEFAULT_FILES_VERSION = 1
DEFAULT_PACKAGE_DESC_VERSION = 1
PACKAGE_DESC_VERSIONS: Dict[int, Dict[str, Union[Set[str], int]]] = {
    1: {
        "required": {
            "arch",
            "base",
            "builddate",
            "csize",
            "desc",
            "filename",
            "isize",
            "license",
            "md5sum",
            "name",
            "packager",
            "sha256sum",
            "url",
            "version",
        },
        "optional": {
            "checkdepends",
            "conflicts",
            "depends",
            "backup",
            "groups",
            "makedepends",
            "optdepends",
            "pgpsig",
            "provides",
            "replaces",
        },
        "output_package_version": 1,
        "output_package_base_version": 1,
    }
}


class RepoDbMemberTypeEnum(IntEnum):
    """An IntEnum to distinguish different types of files in a repository sync database.

    Attributes
    ----------
    UNKNOWN: int
        An unsupported file of unknown type
    DESC: int
        A 'desc' description file of a package
    FILES: int
        A 'files' file of a package
    """

    UNKNOWN = 0
    DESC = 1
    FILES = 2


class RepoDbTypeEnum(IntEnum):
    """An IntEnum to distinguish types of binary repository database files

    Attributes
    ----------
    DEFAULT: int
        Use this to identify .db files
    FILES: int
        Use this to identify .files files
    """

    DEFAULT = 0
    FILES = 2


class RepoDbMemberType(BaseModel):
    """A model describing a single 'member_type' attribute, which is used to identify/ distinguish different types of
    repository database file types (e.g. 'desc' and 'files' files, which are contained in a repository database file).

    Attributes
    ----------
    member_type: RepoDbMemberTypeEnum
        A member of RepoDbMemberTypeEnum
    """

    member_type: RepoDbMemberTypeEnum


class RepoDbMemberData(Name, RepoDbMemberType):
    """A model describing a set of attributes to provide the data of a 'desc' or 'files' file

    Attributes
    ----------
    name: str
        A package name
    member_type: RepoDbMemberTypeEnum
        A member of RepoDbMemberTypeEnum
    data: io.StringIO
        The contents of a 'desc' or 'files' file provided as a StringIO instance
    """

    data: io.StringIO

    class Config:
        arbitrary_types_allowed = True


def get_desc_json_keys() -> Set[str]:
    """Get the keys of repod.models.repo.DESC_JSON

    Returns
    -------
    Set[str]
        A set of strings representing the keys of repod.models.repo.DESC_JSON
    """

    return set(DESC_JSON.keys())


def get_desc_json_name(key: str) -> str:
    """Get the JSON name of a given key from the definition in repod.models.repo.DESC_JSON

    Parameters
    ----------
    key: str
        A string corresponding with one of the keys in repod.models.repo.DESC_JSON

    Raises
    ------
    RepoManagementFileError
        If an unknown key is encountered

    Returns
    -------
    str
        The JSON name of a given 'desc' file identifier provided by key
    """

    try:
        return DESC_JSON[key][0]
    except KeyError:
        raise RepoManagementFileError(f"The key {key} is not a known 'desc' file identifier.")


def get_desc_json_field_type(key: str) -> FieldTypeEnum:
    """Get the FieldTypeEnum of a given key from the definition in repod.models.repo.DESC_JSON

    Parameters
    ----------
    key: str
        A string corresponding with one of the keys in repod.models.repo.DESC_JSON

    Raises
    ------
    RepoManagementFileError
        If an unknown key is encountered

    Returns
    -------
    str
        The FieldTypeEnum of a given 'desc' file identifier provided by key
    """

    try:
        return DESC_JSON[key][1]
    except KeyError:
        raise RepoManagementFileError(f"The key {key} is not a known 'desc' file identifier.")


def get_files_json_keys() -> Set[str]:
    """Get the keys of repod.models.repo.FILES_JSON

    Returns
    -------
    Set[str]
        A set of strings representing the keys of repod.models.repo.FILES_JSON
    """

    return set(FILES_JSON.keys())


def get_files_json_name(key: str) -> str:
    """Get the JSON name of a given key from the definition in repod.models.repo.FILES_JSON

    Parameters
    ----------
    key: str
        A string corresponding with one of the keys in repod.models.repo.FILES_JSON

    Raises
    ------
    RepoManagementFileError
        If an unknown key is encountered

    Returns
    -------
    str
        The JSON name of a given 'files' file identifier provided by key
    """

    try:
        return FILES_JSON[key][0]
    except KeyError:
        raise RepoManagementFileError(f"The key {key} is not a known 'files' file identifier.")


def get_files_json_field_type(key: str) -> FieldTypeEnum:
    """Get the FieldTypeEnum of a given key from the definition in repod.models.repo.FILES_JSON

    Parameters
    ----------
    key: str
        A string corresponding with one of the keys in repod.models.repo.FILES_JSON

    Raises
    ------
    RepoManagementFileError
        If an unknown key is encountered

    Returns
    -------
    str
        The FieldTypeEnum of a given 'desc' file identifier provided by key
    """

    try:
        return FILES_JSON[key][1]
    except KeyError:
        raise RepoManagementFileError(f"The key {key} is not a known 'files' file identifier.")


class PackageDesc(BaseModel):
    """A template class with helper methods to create instances of one of its (versioned) subclasses

    This class should not be instantiated directly, as it only provides generic instance methods for its subclasses.

    NOTE: The `from_dict()` classmethod is used to create one of the versioned subclasses.
    """

    @classmethod
    def from_dict(cls, data: Dict[str, Union[int, str, List[str]]]) -> PackageDesc:
        """Create an instance of one of PackageDesc's subclasses from a dict

        This method should be used with data derived from reading a 'desc' file from a repository sync database.

        Parameters
        ----------
        data: Dict[str, Union[int, str, List[str]]]
            A dict containing data required to instantiate a subclass of PackageDesc

        Raises
        ------
        RepoManagementValidationError
            If a ValidationError is encountered while instantiating one of PackageDesc's subclasses
            If no supported schema_version can be found

        Returns
        -------
        PackageDesc
            An instance of one of the subclasses of PackageDesc
        """

        def derive_package_desc_version(data: Set[str]) -> Optional[int]:
            """Derive which PackageDesc subclass to instantiate

            Parameters
            ----------
            data: Set[str]
                 A set of strings representing the keys of the data dict passed to PackageDesc.from_dict()

            Returns
            -------
            Optional[int]
                The integer representing the version of the PackageDesc subclass, else None
            """

            for version, config in sorted(PACKAGE_DESC_VERSIONS.items(), reverse=True):

                debug(f"Comparing 'desc' data to schema version {version}")
                config_required: Set[str] = config["required"]  # type: ignore[assignment]
                config_optional: Set[str] = config["optional"]  # type: ignore[assignment]
                if config_required.issubset(data):
                    optionals = data - config_required

                    if len(optionals) > len(config_optional):
                        continue
                    else:
                        unmatched_optional = 0
                        for optional in optionals:
                            if optional not in config_optional:
                                unmatched_optional += 1

                    if unmatched_optional != 0:
                        continue

                    return version
                else:
                    continue

            return None

        detected_version = derive_package_desc_version(data=set(data.keys()))
        debug(f"Detected schema version of 'desc' file: {detected_version}")

        if detected_version is not None and (detected_version < DEFAULT_PACKAGE_DESC_VERSION):
            warning(f"Detected 'desc' version {detected_version}, but {DEFAULT_PACKAGE_DESC_VERSION} is the default!")

        match detected_version:
            case 1:
                try:
                    return PackageDescV1(**data)
                except ValidationError as e:
                    raise RepoManagementValidationError(
                        "A validation error occured while attempting to instantiate a PackageDescV1 using the data:\n"
                        f"{data}\n{e}"
                    )
            case _:
                raise RepoManagementValidationError(f"The data format of the 'desc' file is unknown:\n{data}")

    async def render(self, output: io.StringIO) -> None:
        """Use a 'desc' jinja template to write the PackageDesc contents to an output stream

        Parameters
        ----------
        output: io.StringIO
            An output stream to write to

        Raises
        ------
        RepoManagementFileNotFoundError
            If no matching template can be found
        """

        env = Environment(
            loader=PackageLoader("repod", "templates"),
            trim_blocks=True,
            lstrip_blocks=True,
            enable_async=True,
        )
        template_file = f"desc_v{self.get_schema_version()}.j2"

        debug(f"Rendering PackageDesc data using template file {template_file}...")

        try:
            template = env.get_template(template_file)
        except TemplateNotFound:
            raise RepoManagementFileNotFoundError(f"The 'desc' template file {template_file} could not be found!")
        output.write(await template.render_async(self.dict()))

    def get_output_package(self, files: Optional[Files]) -> outputpackage.OutputPackage:
        """Transform the PackageDesc model and an optional Files model into an OutputPackage model

        NOTE: This method only successfully returns if the instance of the class using it defines the required fields!
        The PackageDesc class does not do that!

        Parameters
        ----------
        files: Optional[Files]:
            A pydantic model, that represents the list of files, that belong to the package described by self

        Raises
        ------
        RuntimeError
            If called on the PackageDesc template class
            If there is no matching OutputPackage schema_version defined in the configuration for the given
            PackageDesc.schema_version (bug in PACKAGE_DESC_VERSIONS).
        RepoManagementValidationError
            If no configuration is available for a given PackageDesc.schema_version

        Returns
        -------
        OutputPackage
            A pydantic model, that describes a package and its list of files
        """

        schema_version = self.get_schema_version()
        schema_config = PACKAGE_DESC_VERSIONS.get(schema_version)
        desc_dict = self.dict()
        if schema_config:
            output_package_version = schema_config.get("output_package_version")
            match output_package_version:
                case 1:
                    if files:
                        desc_dict["files"] = files

                    return outputpackage.OutputPackageV1(**desc_dict)
                case _:
                    raise RuntimeError(
                        f"The OutputPackage version '{output_package_version}' is not valid. This is a bug!"
                    )
        else:
            raise RepoManagementValidationError(
                f"The schema version '{schema_version}' is not valid for creating a "
                "OutputPackage from a PackageDesc!"
            )

    def get_output_package_base(self, files: Optional[Files]) -> outputpackage.OutputPackageBase:
        """Transform the PackageDesc model and an Files model into an OutputPackageBase model

        NOTE: This method only successfully returns if the instance of the class using it defines the required fields!
        The PackageDesc class does not do that!

        Parameters
        ----------
        files: Optional[Files]:
            A pydantic model, that represents the list of files, that belong to the package described by self

        Raises
        ------
        RuntimeError
            If called on the PackageDesc template class
            If there is no matching OutputPackage schema_version defined in the configuration for the given
            PackageDesc.schema_version (bug in PACKAGE_DESC_VERSIONS).
        RepoManagementValidationError
            If no configuration is available for a given PackageDesc.schema_version

        Returns
        -------
        OutputPackageBase
            A pydantic model, that describes a package base and one of it's split packages
        """

        schema_version = self.get_schema_version()
        schema_config = PACKAGE_DESC_VERSIONS.get(schema_version)
        desc_dict = self.dict()
        if schema_config:
            output_package_version = schema_config.get("output_package_base_version")
            match output_package_version:
                case 1:
                    desc_dict.update({"packages": [self.get_output_package(files=files)]})
                    return outputpackage.OutputPackageBaseV1(**desc_dict)
                case _:
                    raise RuntimeError(
                        f"The OutputPackageBase version '{output_package_version}' is not valid. This is a bug!"
                    )
        else:
            raise RepoManagementValidationError(
                f"The schema version '{schema_version}' is not valid for creating a "
                "OutputPackageBase from a PackageDesc!"
            )

    def get_base(self) -> str:
        """Get the base attribute of the PackageDesc instance

        NOTE: This method only successfully returns if the instance of the class using it defines the `base` field! The
        PackageDesc class does not do that!

        Raises
        ------
        RuntimeError
            If the method is called on an instance of the PackageDesc template class

        Returns
        -------
        str
            The base attribute of a PackageDesc subclass
        """

        if hasattr(self, "base"):
            return str(self.base)  # type: ignore[attr-defined]
        else:
            raise RuntimeError(
                "It is not possible to retrieve the 'base' attribute from the template class PackageDesc!"
            )

    def get_name(self) -> str:
        """Get the name attribute of the PackageDesc instance

        NOTE: This method only successfully returns if the instance of the class using it defines the `name` field! The
        PackageDesc class does not do that!

        Raises
        ------
        RuntimeError
            If the method is called on an instance of the PackageDesc template class

        Returns
        -------
        str
            The name attribute of a PackageDesc subclass
        """

        if hasattr(self, "name"):
            return str(self.name)  # type: ignore[attr-defined]
        else:
            raise RuntimeError(
                "It is not possible to retrieve the 'name' attribute from the template class PackageDesc!"
            )

    def get_schema_version(self) -> int:
        """Get the schema_version attribute of the PackageDesc instance

        NOTE: This method only successfully returns if the instance of the class using it defines the `schema_version`
        field! The PackageDesc class does not do that!

        Raises
        ------
        RuntimeError
            If the method is called on an instance of the PackageDesc template class

        Returns
        -------
        int
            The schema_version attribute of a PackageDesc subclass
        """

        if hasattr(self, "schema_version"):
            return int(self.schema_version)  # type: ignore[attr-defined]
        else:
            raise RuntimeError(
                "It is not possible to retrieve the 'schema_version' attribute from the templatet class PackageDesc!"
            )


class Files(BaseModel):
    """A template class to describe files in the context of 'files' files in a repository sync database

    This class should not be instantiated directly, as it only provides generic instance methods for its subclasses.

    NOTE: The `from_dict()` classmethod is used to create one of the versioned subclasses.
    """

    @classmethod
    def from_dict(cls, data: Dict[str, List[str]]) -> Files:
        """Class method to create one of Files' subclasses from a dict

        This method is supposed to be called with data derived from a 'files' file.

        Parameters
        ----------
        data: Dict[str, List[str]]
            A dict with required data read from a 'files' file, which is used to instantiate one of Files' subclasses

        Raises
        ------
        RepoManagementValidationError
            If a ValidationError occurs when instatiating one of Files' subclasses or if no valid schema version for the
            data could be derived.

        Returns
        -------
        Files
            A Files instance (technically only one of its subclasses), instantiated from data
        """

        def derive_files_version(data: Set[str]) -> Optional[int]:
            """Derive which Files subclass to instantiate

            Parameters
            ----------
            data: Set[str]
                 A set of strings representing the keys of the data dict passed to Files.from_dict()

            Returns
            -------
            Optional[int]
                The integer representing the schema version of the Files subclass, else None
            """

            for version, config in sorted(FILES_VERSIONS.items(), reverse=True):

                debug(f"Comparing 'files' data to schema version {version}")
                config_required = config["required"]
                config_optional = config["optional"]
                if config_required.issubset(data):
                    optionals = data - config_required

                    if len(optionals) > len(config_optional):
                        continue
                    else:
                        unmatched_optional = 0
                        for optional in optionals:
                            if optional not in config_optional:
                                unmatched_optional += 1

                    if unmatched_optional != 0:
                        continue

                    return version
                else:
                    continue

            return None

        detected_version = derive_files_version(data=set(data.keys()))
        debug(f"Detected schema version of 'files' file: {detected_version}")

        if detected_version is not None and (detected_version < DEFAULT_FILES_VERSION):
            warning(f"Detected 'files' version {detected_version}, but {DEFAULT_FILES_VERSION} is the default!")

        match detected_version:
            case 1:
                try:
                    return FilesV1(**data)
                except ValidationError as e:
                    raise RepoManagementValidationError(
                        "A validation error occured while attempting to instantiate a FilesV1 using the data:\n"
                        f"{data}\n{e}"
                    )
            case _:
                raise RepoManagementValidationError(
                    f"The data format '{detected_version}' of the 'files' file is unknown:\n{data}"
                )

    async def render(self, output: io.StringIO) -> None:
        """Use a 'files' jinja template to write the Files contents to an output stream

        Parameters
        ----------
        output: io.StringIO
            An output stream to write to

        Raises
        ------
        RepoManagementFileNotFoundError
            If no matching template can be found
        """

        env = Environment(
            loader=PackageLoader("repod", "templates"),
            trim_blocks=True,
            lstrip_blocks=True,
            enable_async=True,
        )
        template_file = f"files_v{self.get_schema_version()}.j2"

        debug(f"Rendering Files data using template file {template_file}...")

        try:
            template = env.get_template(template_file)
        except TemplateNotFound:
            raise RepoManagementFileNotFoundError(f"The 'files' template file {template_file} could not be found!")
        output.write(await template.render_async(self.dict()))

    def get_schema_version(self) -> int:
        """Get the schema_version of the Files instance

        NOTE: This method only successfully returns if the instance of the class using it actually defines the
        `schema_version` field!

        Raises
        ------
        RuntimeError
            If the method is called on an instance of the Files template class

        Returns
        -------
        int
            The schema_version attribute of a Files subclass
        """

        if hasattr(self, "schema_version"):
            return int(self.schema_version)  # type: ignore[attr-defined]
        else:
            raise RuntimeError(
                "It is not possible to retrieve the 'schema_version' attribute from the Files template class!"
            )


class FilesV1(Files, FileList, SchemaVersionV1):
    """A pydantic model to describe files in the context of 'files' files in a repository sync database (version 1)

    Attributes
    ----------
    files: Optional[List[str]]
        An optional list of files. This is the data below a %FILES% identifier in a 'files' file, which identifies which
        file(s) belong to a package
    """

    pass


class PackageDescV1(
    PackageDesc,
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
):
    """A model describing all identifiers in a 'desc' file (version 1)

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
    schema_version: PositiveInt
        A positive integer - 1 - identifying the schema version of the object
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

    classes = [FilesV1, PackageDescV1]

    if isinstance(output, str):
        output = Path(output)

    if not output.exists():
        raise RuntimeError(f"The output directory {output} must exist!")

    for class_ in classes:
        with open(output / f"{class_.__name__}.json", "w") as f:
            print(class_.schema_json(indent=2), file=f)
