from __future__ import annotations

import io
import re
from enum import IntEnum
from logging import debug, warning
from pathlib import Path
from tarfile import DIRTYPE, TarFile, TarInfo
from time import time
from typing import Dict, List, Optional, Set, Tuple, Union

from jinja2 import Environment, PackageLoader, TemplateNotFound
from pydantic import BaseModel, ValidationError

from repod.common.enums import (
    CompressionTypeEnum,
    FieldTypeEnum,
    FilesVersionEnum,
    PackageDescVersionEnum,
)
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
from repod.files.common import open_tarfile
from repod.repo.management import outputpackage

DB_USER = "root"
DB_GROUP = "root"
DB_FILE_MODE = "0644"
DB_DIR_MODE = "0755"
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
    },
    2: {
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
            "provides",
            "replaces",
        },
        "output_package_version": 1,
        "output_package_base_version": 1,
    },
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


class SyncDatabase(BaseModel):
    """A model describing a repository sync database

    Attributes
    ----------
    database: Path
        The path to the database that the instance manages
    database_type: RepoDbTypeEnum
        The type of database that the instance manages
    compression_type: CompressionTypeEnum
        The compression type which is used for  the database
    """

    database: Path
    database_type: Optional[RepoDbTypeEnum]
    compression_type: Optional[CompressionTypeEnum]
    desc_version: PackageDescVersionEnum
    files_version: FilesVersionEnum

    @classmethod
    async def outputpackagebase_to_tarfile(
        cls,
        tarfile: TarFile,
        database_type: Optional[RepoDbTypeEnum],
        model: outputpackage.OutputPackageBase,
        packagedesc_version: PackageDescVersionEnum,
        files_version: FilesVersionEnum,
    ) -> None:
        """Stream descriptor files derived from an OutputPackageBase to a TarFile

        Allows streaming to a default repository database or a files database

        Parameters
        ----------
        tarfile: TarFile
            A TarFile to stream data to
        db_type: RepoDbTypeEnum
            The type of database to stream to
        model: OutputPackageBase
            The OutputPackageBase instance to derive descriptor files from
        packagedesc_version: PackageDescVersionEnum
            The version of PackageDesc to use
        files_version: FilesVersionEnum
            The version of Files to use
        """

        for (desc_model, files_model) in await model.get_packages_as_models(
            packagedesc_version=packagedesc_version,
            files_version=files_version,
        ):
            dirname = f"{desc_model.get_name()}-{model.get_version()}"
            directory = TarInfo(dirname)
            directory.type = DIRTYPE
            directory.mtime = int(time())
            directory.uname = DB_USER
            directory.gname = DB_GROUP
            directory.mode = int(DB_DIR_MODE, base=8)
            tarfile.addfile(directory)

            desc_content = io.StringIO()
            await desc_model.render(output=desc_content)
            desc_file = TarInfo(f"{dirname}/desc")
            desc_file.size = len(desc_content.getvalue().encode())
            desc_file.mtime = int(time())
            desc_file.uname = DB_USER
            desc_file.gname = DB_GROUP
            desc_file.mode = int(DB_FILE_MODE, base=8)
            tarfile.addfile(desc_file, io.BytesIO(desc_content.getvalue().encode()))

            if database_type == RepoDbTypeEnum.FILES:
                files_content = io.StringIO()
                await files_model.render(output=files_content)
                files_file = TarInfo(f"{dirname}/files")
                files_file.size = len(files_content.getvalue().encode())
                files_file.mtime = int(time())
                files_file.uname = DB_USER
                files_file.gname = DB_GROUP
                files_file.mode = int(DB_FILE_MODE, base=8)
                tarfile.addfile(files_file, io.BytesIO(files_content.getvalue().encode()))

    async def add(self, model: outputpackage.OutputPackageBase) -> None:
        """Write descriptor files for packages of a single pkgbase to the repository sync database

        Parameters
        ----------
        model: OutputPackageBase
            The model to use for streaming descriptor files to the repository database
        """

        debug(f"Opening file {self.database} for writing...")

        with open_tarfile(
            path=self.database,
            compression=self.compression_type,
            mode="w",
        ) as database_file:
            await SyncDatabase.outputpackagebase_to_tarfile(
                tarfile=database_file,
                database_type=self.database_type,
                model=model,
                packagedesc_version=self.desc_version,
                files_version=self.files_version,
            )

    async def outputpackagebases(self) -> List[Tuple[str, outputpackage.OutputPackageBase]]:
        """Read a repository database and yield the name of each pkgbase and the respective data (represented as an
        instance of OutputPackageBase) in a Tuple.

        Returns
        -------
        Iterator[Tuple[str, OutputPackageBase]]:
            A Tuple holding the name of a pkgbase and its accompanying data in an instance of OutputPackageBase
        """

        packages: Dict[str, outputpackage.OutputPackageBase] = {}
        package_descs: Dict[str, PackageDesc] = {}
        package_files: Dict[str, Files] = {}

        with open_tarfile(path=self.database, compression=self.compression_type) as db_file:
            for file_name in [
                file_name for file_name in db_file.getnames() if re.search(r"(/desc|/files)$", file_name)
            ]:
                pkgname = "".join(re.split("(-)", re.sub(r"(/desc|/files)$", "", file_name))[:-4])

                if re.search("(/desc)$", file_name):
                    package_descs.update(
                        {
                            pkgname: await PackageDesc.from_stream(
                                data=io.StringIO(
                                    io.BytesIO(
                                        db_file.extractfile(file_name).read(),  # type: ignore[union-attr]
                                    )
                                    .read()
                                    .decode("utf-8"),
                                )
                            ),
                        },
                    )
                elif re.search("(/files)$", file_name):
                    package_files.update(
                        {
                            pkgname: await Files.from_stream(
                                data=io.StringIO(
                                    io.BytesIO(
                                        db_file.extractfile(file_name).read(),  # type: ignore[union-attr]
                                    )
                                    .read()
                                    .decode("utf-8"),
                                )
                            )
                        },
                    )
                else:  # pragma: no cover
                    # NOTE: this branch can never be reached, but we add it to make tests happy
                    raise RuntimeError(
                        f"The database file {self.database} contains the member {file_name} of an unsupported type!"
                    )

        for (name, package_desc) in package_descs.items():
            if packages.get(package_desc.get_base()):
                packages[package_desc.get_base()].add_packages(
                    [package_desc.get_output_package(files=package_files.get(name))]
                )
            else:
                packages.update(
                    {
                        package_desc.get_base(): package_desc.get_output_package_base(files=package_files.get(name)),
                    }
                )

        return list(packages.items())

    async def stream_management_repo(self, path: Path) -> None:
        """Stream descriptor files read from the JSON files of a management repository to the repository sync database

        Parameters
        ----------
        path: Path
            The directory containing the files of the management repository

        Raises
        ------
        RepoManagementFileNotFoundError
            If no JSON files are found in path
        """

        file_list = sorted(path.glob("*.json"))
        if not file_list:
            raise RepoManagementFileNotFoundError(f"There are no JSON files in {path}!")

        with open_tarfile(self.database, compression=self.compression_type, mode="w") as database_file:
            for json_file in file_list:
                await SyncDatabase.outputpackagebase_to_tarfile(
                    tarfile=database_file,
                    database_type=self.database_type,
                    model=await outputpackage.OutputPackageBase.from_file(path=json_file),
                    packagedesc_version=self.desc_version,
                    files_version=self.files_version,
                )


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

        debug(f"Creating Files from data: {data}")
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
            case 2:
                try:
                    return PackageDescV2(**data)
                except ValidationError as e:
                    raise RepoManagementValidationError(
                        "A validation error occured while attempting to instantiate a PackageDescV2 using the data:\n"
                        f"{data}\n{e}"
                    )
            case _:
                raise RepoManagementValidationError(f"The data format of the 'desc' file is unknown:\n{data}")

    @classmethod
    async def from_stream(cls, data: io.StringIO) -> PackageDesc:
        """Initialize a PackageDesc from an input stream

        Parameters
        ----------
        data: io.StringIO
            A buffered I/O that represents a 'desc' file

        Raises
        ------
        errors.RepoManagementValidationError
            If a pydantic.error_wrappers.ValidationError is raised (e.g. due to a missing attribute) or if a ValueError
            is raised when converting data

        Returns
        -------
        PackageDesc
            A PackageDesc instance based on data
        """

        current_header = ""
        current_type: FieldTypeEnum
        int_types: Dict[str, int] = {}
        string_types: Dict[str, str] = {}
        string_list_types: Dict[str, List[str]] = {}
        keys = get_desc_json_keys()

        for line in data:
            line = line.strip()
            if not line:
                continue

            if line in keys:
                current_header = get_desc_json_name(key=line)
                current_type = get_desc_json_field_type(line)
                # FIXME: find better way to provide a default (None or empty list for STRING_LIST as they all are
                # Optional[List[str]]
                if current_header and current_type == FieldTypeEnum.STRING_LIST:
                    string_list_types[current_header] = []

                continue

            if current_header:
                try:
                    match current_type:
                        case FieldTypeEnum.STRING_LIST:
                            string_list_types[current_header] += [line]
                        case FieldTypeEnum.STRING:
                            string_types[current_header] = line
                        case FieldTypeEnum.INT:
                            int_types[current_header] = int(line)
                        case _:  # pragma: no cover
                            pass
                except ValueError as e:
                    raise RepoManagementValidationError(
                        "An error occured while attempting to cast values for a 'desc' file!\n"
                        f"\n{data.getvalue()}\n{e}"
                    )

        desc_dict: Dict[str, Union[int, str, List[str]]] = {**int_types, **string_types, **string_list_types}
        try:
            return PackageDesc.from_dict(desc_dict)
        except RepoManagementValidationError as e:
            raise RepoManagementValidationError(
                "An error occured while validating a 'desc' file!\n" f"\n{data.getvalue()}\n{e}"
            )

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

    @classmethod
    async def from_stream(cls, data: io.StringIO) -> Files:
        """Initialize a Files from an input stream

        Parameters
        ----------
        data: io.StringIO
            A buffered I/O that represents the contents of a 'files' file

        Raises
        ------
        errors.RepoManagementValidationError
            If a pydantic.error_wrappers.ValidationError is raised (e.g. due to a missing attribute)

        Returns
        -------
        Files
            A Files instance based on data
        """

        current_header = ""
        current_type: FieldTypeEnum
        string_list_types: Dict[str, List[str]] = {}
        keys = get_files_json_keys()

        for line in data:
            line = line.strip()
            if not line:
                continue

            if line in keys:
                current_header = get_files_json_name(key=line)
                current_type = get_files_json_field_type(line)
                debug(f"Found header {current_header} of type {current_type}")
                string_list_types[current_header] = []
                continue

            if current_header:
                debug(f"Adding value {line} for header {current_header}")
                string_list_types[current_header] += [line]

        try:
            return Files.from_dict(data=string_list_types)
        except RepoManagementValidationError as e:
            raise RepoManagementValidationError(
                f"An error occured while validating a 'files' file!\n" f"\n{data.getvalue()}\n{e}"
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
        The attribute can be used to describe the (optional) data below a %PGPSIG% identifier in a 'desc' file, which
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


class PackageDescV2(
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

    classes = [FilesV1, PackageDescV1, PackageDescV2]

    if isinstance(output, str):
        output = Path(output)

    if not output.exists():
        raise RuntimeError(f"The output directory {output} must exist!")

    for class_ in classes:
        with open(output / f"{class_.__name__}.json", "w") as f:
            print(class_.schema_json(indent=2), file=f)
