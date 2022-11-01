from __future__ import annotations

import os
from logging import debug
from pathlib import Path
from typing import Any

import tomli
from pydantic import (
    AnyUrl,
    BaseModel,
    BaseSettings,
    HttpUrl,
    PrivateAttr,
    root_validator,
    validator,
)
from pydantic.env_settings import SettingsSourceCallable

from repod.common.enums import (
    ArchitectureEnum,
    CompressionTypeEnum,
    FilesVersionEnum,
    PackageDescVersionEnum,
    PkgVerificationTypeEnum,
    RepoDirTypeEnum,
    RepoTypeEnum,
    SettingsTypeEnum,
)
from repod.config.defaults import (
    DEFAULT_ARCHITECTURE,
    DEFAULT_DATABASE_COMPRESSION,
    DEFAULT_NAME,
    MANAGEMENT_REPO_BASE,
    ORJSON_OPTION,
    PACKAGE_POOL_BASE,
    PACKAGE_REPO_BASE,
    SETTINGS_LOCATION,
    SETTINGS_OVERRIDE_LOCATION,
    SOURCE_POOL_BASE,
    SOURCE_REPO_BASE,
)

DIR_MODE = "0755"
CUSTOM_CONFIG: Path | None = None


def to_absolute_path(path: Path, base_path: Path) -> Path:
    """Turn provided directory into absolute Path

    Parameters
    ----------
    directory: Path
        An absolute or relative directory
    base_path: Path
        An absolute directory that is prepended to directory if it is relative

    Raises
    ------
    ValueError
        If base_path is relative

    Returns
    -------
    Path
        An absolute directory Path
    """

    if not base_path.is_absolute():
        raise ValueError(f"The base_path must be absolute, but '{base_path}' is provided!")

    if not path.is_absolute():
        debug(f"Converting path {path} to {base_path / path}...")
        path = base_path / path

    return path


def create_and_validate_directory(directory: Path) -> None:
    """Create a directory (if it does not exist yet) and ensure that it is writable

    Parameters
    ----------
    directory: Path
        A directory path to create and validate

    Returns
    -------
    Path
        An absolute path
    """

    if not directory.exists():
        debug(f"Creating directory {directory}...")
        try:
            directory.mkdir(mode=int(DIR_MODE, base=8), parents=True, exist_ok=True)
        except PermissionError as e:
            raise ValueError(e)

    if not directory.is_dir():
        raise ValueError(f"Not a directory: '{directory}'.")
    if not os.access(directory, os.W_OK):
        raise ValueError(f"The directory '{directory}' is not writable.")


class Architecture(BaseModel):
    """A model describing a single "architecture" attribute

    Attributes
    ----------
    architecture: ArchitectureEnum
        An ArchitectureEnum member describing a valid architecture for a repository
    """

    architecture: ArchitectureEnum | None


class DatabaseCompression(BaseModel):
    """Compression type for repository sync databases

    Attributes
    ----------
    database_compression: CompressionTypeEnum
        A member of CompressionTypeEnum (defaults to DEFAULT_DATABASE_COMPRESSION)
    """

    database_compression: CompressionTypeEnum | None


class PackagePool(BaseModel):
    """A model describing a single "package_pool" attribute

    Attributes
    ----------
    package_pool: Path
        An optional Path instance that identifies an absolute directory location for package tarball data
    """

    package_pool: Path | None


class SourcePool(BaseModel):
    """A model describing a single "source_pool" attribute

    Attributes
    ----------
    source_pool: Path
        An optional Path instance that identifies an absolute directory location for source tarball data
    """

    source_pool: Path | None


class SyncDbSettings(BaseModel):
    """Settings for repository sync databases

    Attributes
    ----------
    desc_version: PackageDescVersionEnum
        The desc version to export to (defaults to PackageDescVersionEnum.DEFAULT)
    files_version: FilesVersionEnum
        The files version to export to (defaults to FilesVersionEnum.DEFAULT)
    """

    desc_version: PackageDescVersionEnum = PackageDescVersionEnum.DEFAULT
    files_version: FilesVersionEnum = FilesVersionEnum.DEFAULT


class UrlValidationSettings(BaseModel):
    """Settings for URL validation

    Attributes
    ----------
    urls: list[HttpUrl]
        A list of HttpUrl objects to be used for validation
    tls_required: bool
        A boolean value indicating whether the urls (and those validated against) require TLS
    """

    urls: list[HttpUrl]
    tls_required: bool

    @root_validator
    def validate_urls(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Validate the URLs

        Parameters
        ----------
        values: dict[str, Any]
            A dict with all values of the UrlValidationSettings instance

        Raises
        ------
        ValueError
            If tls_required is True, but any of the urls does not use TLS.

        Returns
        -------
        values: dict[str, Any]
            The unmodified dict with all values of the UrlValidationSettings instance
        """

        urls: list[HttpUrl] = values.get("urls")  # type: ignore[assignment]
        tls_required: bool = values.get("tls_required")  # type: ignore[assignment]

        for url in urls:
            if tls_required and url.scheme != "https":
                raise ValueError(f"The url {url} requires TLS, but its scheme is {url.scheme}!")

        return values

    def validate_url(self, url: AnyUrl) -> bool:
        """Validate a URL

        Parameters
        ----------
        url: AnyUrl
            A URL to validate

        Returns
        -------
        bool
            True if the URL validates against the UrlValidationSettings object, False otherwise
        """

        if self.tls_required and url.scheme != "https":
            debug(f"The URL {url} does not provide TLS!")
            return False

        url_strings = [str(_url) for _url in self.urls]
        if not any(True for url_string in url_strings if str(url).startswith(url_string)):
            debug(f"The URL {url} does not match any of the URLs {url_strings}!")
            return False

        return True


class ManagementRepo(BaseModel):
    """A model describing all required attributes to describe a repository used for managing one or more package
    repositories

    Attributes
    ----------
    directory: Path
        A Path instance describing the location of the management repository
    url: AnyUrl | None
        A URL describing the VCS upstream of the management repository
    json_dumps_option: int
        An option for orjson (see https://github.com/ijl/orjson#option) on how to serialize data
    """

    directory: Path
    url: AnyUrl | None
    json_dumps_option: int = ORJSON_OPTION

    @validator("url")
    def validate_url(cls, url: AnyUrl | None) -> AnyUrl | None:
        """A validator for the url attribute

        Parameters
        ----------
        url: AnyUrl | None
            An instance of AnyUrl, that describes an upstream repository URL

        Raises
        ------
        ValueError
            If the url is set and the scheme is not one of "https" or "ssh" or if the url scheme is "ssh", but no user
            is provided in the URL string

        Returns
        -------
        AnyUrl | None
            A validated instance of AnyUrl or None
        """

        if url is None:
            return url
        valid_schemes = ["https", "ssh"]
        if url.scheme not in valid_schemes:
            raise ValueError(
                f"The scheme '{url.scheme}' of the url ({url}) is not valid (must be one of {valid_schemes})"
            )
        if url.scheme == "ssh" and not url.user:
            raise ValueError(f"When using ssh a user is required (but none is provided): '{url}'")

        return url


class PackageRepo(Architecture, DatabaseCompression, PackagePool, SourcePool):
    """A model providing all required attributes to describe a package repository

    Attributes
    ----------
    architecture: ArchitectureEnum | None
        An optional ArchitectureEnum member, that serves as an override to the application-wide architecture. The
        attribute defines the CPU architecture for the package repository
    database_compression: CompressionTypeEnum
        A member of CompressionTypeEnum (defaults to DEFAULT_DATABASE_COMPRESSION)
    debug: Path | None
        The optional name of a debug repository associated with a package repository
    package_pool: Path | None
        An optional directory, that serves as an override to the application-wide package_pool.
        The attribute defines the location to store the binary packages and their signatures in
    source_pool: Path | None
        An optional directory, that serves as an override to the application-wide source_pool.
        The attribute defines the location to store the source tarballs in
    name: Path
        The required name of a package repository
    staging: Path | None
        The optional name of a staging repository associated with a package repository
    staging_debug: Path | None
        The optional name of a staging debug repository associated with a package repository (a staging repository must
        be defined when using this)
    testing: Path | None
        The optional name of a testing repository associated with a package repository
    testing_debug: Path | None
        The optional name of a testing debug repository associated with a package repository (a testing repository must
        be defined when using this)
    management_repo: ManagementRepo | None
        An optional instance of ManagementRepo, that serves as an override to the application-wide management_repo
        The attribute defines the directory and upstream VCS repository that is used to track changes to a package
        repository
    package_url_validation: UrlValidationSettings | None
        An optional instance of UrlValidationSettings for validating the source_url of packages in the PackageRepo

    PrivateAttributes
    -----------------
    _debug_management_repo_dir: Path
        The absolute path to the directory in a management repository used for the PackageRepo's debug packages (unset
        by default)
    _debug_repo_dir: Path
        The absolute path to the directory used for package files for the PackageRepo's debug packages (unset by
        default)
    _debug_source_repo_dir: Path
        The absolute path to the directory used for source tarballs for the PackageRepo's debug packages (unset by
        default)
    _package_pool_dir: Path
        The absolute path to the directory used as package pool directory for the PackageRepo (unset by default)
    _source_pool_dir: Path
        The absolute path to the directory used as source pool directory for the PackageRepo (unset by default)
    _stable_management_repo_dir: Path
        The absolute path to the directory in a management repository used for the PackageRepo's stable packages (unset
        by default)
    _stable_repo_dir: Path
        The absolute path to the directory used for package files for the PackageRepo's stable packages (unset by
        default)
    _stable_source_repo_dir: Path
        The absolute path to the directory used for source tarballs for the PackageRepo's stable packages (unset by
        default)
    _staging_management_repo_dir: Path
        The absolute path to the directory in a management repository used for the PackageRepo's staging packages (unset
        by default)
    _staging_repo_dir: Path
        The absolute path to the directory used for package files for the PackageRepo's staging packages (unset by
        default)
    _staging_source_repo_dir: Path
        The absolute path to the directory used for source tarballs for the PackageRepo's staging packages (unset by
        default)
    _staging_debug_management_repo_dir: Path
        The absolute path to the directory in a management repository used for the PackageRepo's staging debug packages
        (unset by default)
    _staging_debug_repo_dir: Path
        The absolute path to the directory used for package files for the PackageRepo's staging debug packages (unset by
        default)
    _staging_debug_source_repo_dir: Path
        The absolute path to the directory used for source tarballs for the PackageRepo's staging debug packages (unset
        by default)
    _testing_management_repo_dir: Path
        The absolute path to the directory in a management repository used for the PackageRepo's testing packages (unset
        by default)
    _testing_repo_dir: Path
        The absolute path to the directory used for package files for the PackageRepo's testing packages (unset by
        default)
    _testing_source_repo_dir: Path
        The absolute path to the directory used for source tarballs for the PackageRepo's testing packages (unset by
        default)
    _testing_debug_management_repo_dir: Path
        The absolute path to the directory in a management repository used for the PackageRepo's testing debug packages
        (unset by default)
    _testing_debug_repo_dir: Path
        The absolute path to the directory used for package files for the PackageRepo's testing debug packages (unset by
        default)
    _testing_debug_source_repo_dir: Path
        The absolute path to the directory used for source tarballs for the PackageRepo's testing debug packages (unset
        by default)
    """

    _debug_management_repo_dir: Path = PrivateAttr()
    _debug_repo_dir: Path = PrivateAttr()
    _debug_source_repo_dir: Path = PrivateAttr()

    _package_pool_dir: Path = PrivateAttr()
    _source_pool_dir: Path = PrivateAttr()

    _stable_management_repo_dir: Path = PrivateAttr()
    _stable_repo_dir: Path = PrivateAttr()
    _stable_source_repo_dir: Path = PrivateAttr()

    _staging_management_repo_dir: Path = PrivateAttr()
    _staging_repo_dir: Path = PrivateAttr()
    _staging_source_repo_dir: Path = PrivateAttr()

    _staging_debug_management_repo_dir: Path = PrivateAttr()
    _staging_debug_repo_dir: Path = PrivateAttr()
    _staging_debug_source_repo_dir: Path = PrivateAttr()

    _testing_management_repo_dir: Path = PrivateAttr()
    _testing_repo_dir: Path = PrivateAttr()
    _testing_source_repo_dir: Path = PrivateAttr()

    _testing_debug_management_repo_dir: Path = PrivateAttr()
    _testing_debug_repo_dir: Path = PrivateAttr()
    _testing_debug_source_repo_dir: Path = PrivateAttr()

    name: Path
    debug: Path | None
    staging: Path | None
    staging_debug: Path | None
    testing: Path | None
    testing_debug: Path | None
    management_repo: ManagementRepo | None
    package_url_validation: UrlValidationSettings | None

    @validator("name", pre=True)
    def validate_repo_name(cls, name: Path | str) -> Path:
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

        disallowed_start_chars = [".", "-"]
        for char in disallowed_start_chars:
            if name.name.startswith(char):
                raise ValueError(
                    f"The package repository name '{name}' can not start with any of '{disallowed_start_chars}'."
                )

        allowed_chars = ["_", "-"]
        remaining_chars: list[str] = []
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

        debug(f"Repository name after validation: {name}")
        return name

    @validator("debug", "staging", "staging_debug", "testing", "testing_debug")
    def validate_optional_staging_testing(cls, name: Path | None) -> Path | None:
        """A validator for the optional debug, staging, staging_debug, testing and testing_debug attributes

        Parameters
        ----------
        name: Path | None
            An optional relative Path to validate. If a string is provided, PackageRepo.validate_name() is used.

        Returns
        -------
        Path | None
            A validated name string, else None
        """

        if name is not None:
            name = Path(PackageRepo.validate_repo_name(name=name))

        return name

    @root_validator(skip_on_failure=True)
    def validate_unique_repository_dirs(cls, values: dict[str, Any]) -> dict[str, Any]:
        """A root validator for the optional debug, staging, staging_debug, testing and testing_debug attributes
        ensuring all are not the same string

        Parameters
        ----------
        values: dict[str, Any]
            A dict with all values of the PackageRepo instance

        Raises
        ------
        ValueError
            If paths for stable, debug, staging, staging_debug, testing or testing_debug overlap with one another

        Returns
        -------
        values: dict[str, Any]
            The unmodified dict with all values of the PackageRepo instance
        """

        stable_repo: Path = values.get("name")  # type: ignore[assignment]
        debug_repo: Path | None = values.get("debug")
        staging_repo: Path | None = values.get("staging")
        staging_debug_repo: Path | None = values.get("staging_debug")
        testing_repo: Path | None = values.get("testing")
        testing_debug_repo: Path | None = values.get("testing_debug")
        stable_repo_list = [stable_repo] if stable_repo else []
        debug_repo_list = [debug_repo] if debug_repo else []
        staging_repo_list = [staging_repo] if staging_repo else []
        staging_debug_repo_list = [staging_debug_repo] if staging_debug_repo else []
        testing_repo_list = [testing_repo] if testing_repo else []
        testing_debug_repo_list = [testing_debug_repo] if testing_debug_repo else []

        debug(f"stable_repo: {stable_repo}")

        if staging_debug_repo and not staging_repo:
            raise ValueError("A staging debug repository can not exist without a staging repository!")
        if testing_debug_repo and not testing_repo:
            raise ValueError("A testing debug repository can not exist without a testing repository!")
        if (staging_debug_repo or testing_debug_repo) and not debug_repo:
            raise ValueError("A testing or staging debug repository can not exist without a stable debug repository!")
        if debug_repo and ((staging_repo and not staging_debug_repo) or (testing_repo and not testing_debug_repo)):
            raise ValueError(
                "A testing or staging debug repository must exist if staging or testing are used "
                "and a stable debug repository is present!"
            )

        options: list[tuple[Path | None, str, list[Path], str]] = [
            (stable_repo, "stable repository", debug_repo_list, "stable debug repository"),
            (stable_repo, "stable repository", staging_repo_list, "staging repository"),
            (stable_repo, "stable repository", staging_debug_repo_list, "staging debug repository"),
            (stable_repo, "stable repository", testing_repo_list, "testing repository"),
            (stable_repo, "stable repository", testing_debug_repo_list, "testing debug repository"),
            (debug_repo, "debug repository", stable_repo_list, "stable repository"),
            (debug_repo, "debug repository", staging_repo_list, "staging repository"),
            (debug_repo, "debug repository", staging_debug_repo_list, "staging debug repository"),
            (debug_repo, "debug repository", testing_repo_list, "testing repository"),
            (debug_repo, "debug repository", testing_debug_repo_list, "testing debug repository"),
            (staging_repo, "staging repository", stable_repo_list, "stable repository"),
            (staging_repo, "staging repository", debug_repo_list, "stable debug repository"),
            (staging_repo, "staging repository", staging_debug_repo_list, "staging debug repository"),
            (staging_repo, "staging repository", testing_repo_list, "testing repository"),
            (staging_repo, "staging repository", testing_debug_repo_list, "testing debug repository"),
            (staging_debug_repo, "staging debug repository", stable_repo_list, "stable repository"),
            (staging_debug_repo, "staging debug repository", debug_repo_list, "stable debug repository"),
            (staging_debug_repo, "staging debug repository", staging_repo_list, "staging repository"),
            (staging_debug_repo, "staging debug repository", testing_repo_list, "testing repository"),
            (staging_debug_repo, "staging debug repository", testing_debug_repo_list, "testing debug repository"),
            (testing_repo, "testing repository", stable_repo_list, "stable repository"),
            (testing_repo, "testing repository", debug_repo_list, "stable debug repository"),
            (testing_repo, "testing repository", staging_repo_list, "staging repository"),
            (testing_repo, "testing repository", staging_debug_repo_list, "staging debug repository"),
            (testing_repo, "testing repository", testing_debug_repo_list, "testing debug repository"),
            (testing_debug_repo, "testing debug repository", stable_repo_list, "stable repository"),
            (testing_debug_repo, "testing debug repository", debug_repo_list, "stable debug repository"),
            (testing_debug_repo, "testing debug repository", staging_repo_list, "staging repository"),
            (testing_debug_repo, "testing debug repository", staging_debug_repo_list, "staging debug repository"),
            (testing_debug_repo, "testing debug repository", testing_repo_list, "testing repository"),
        ]

        for option in options:
            raise_on_path_in_list_of_paths(
                path=option[0],
                path_name=option[1],
                path_list=option[2],
                other_name=option[3],
            )

        return values


def raise_on_path_equals_other(path: Path, path_name: str, other: Path, other_name: str) -> None:
    """Raise on two Path instances pointing at the same file

    Parameters
    ----------
    path: Path
        A path
    path_name: str
        A string describing the purpose of the Path
    path: Path
        Another path
    path_name: str
        A string describing the purpose of the other Path

    Raises
    ------
    ValueError
        If path and other point at the same file
    """

    if path == other:
        raise ValueError(
            f"The {path_name} directory '{path}' can not be the same as the {other_name} directory '{other}'."
        )


def raise_on_path_in_other(path: Path, path_name: str, other: Path, other_name: str) -> None:
    """Raise when a Path instance is located in another

    Parameters
    ----------
    path: Path
        A path
    path_name: str
        A string describing the purpose of the Path
    path: Path
        Another path
    path_name: str
        A string describing the purpose of the other Path

    Raises
    ------
    ValueError
        If path is located below other
    """

    try:
        path.relative_to(other)
    except ValueError:
        return
    else:
        raise ValueError(f"The {path_name} directory '{path}' can not reside in the {other_name} directory '{other}'.")


def raise_on_path_in_list_of_paths(
    path: Path | None,
    path_name: str,
    path_list: list[Path],
    other_name: str,
) -> None:
    """Raise when a Path instance is in a list of Path instances

    Parameters
    ----------
    path | None: Path
        An optional Path
    path_name: str
        A string describing the purpose of the Path
    path_list: list[Path | None]
        A list of optional Paths
    path_name: str
        A string describing the purpose of the other Path

    Raises
    ------
    ValueError
        If path is in path_list
    """

    debug(f"Testing if {path} is located in or equals to any of {', '.join([str(path) for path in path_list])}...")
    if not path:
        return

    for test_path in path_list:
        raise_on_path_equals_other(path=path, path_name=path_name, other=test_path, other_name=other_name)
        raise_on_path_in_other(path=path, path_name=path_name, other=test_path, other_name=other_name)


def validate_repo_paths(
    repo_dirs: list[Path],
    repo_dir_name: str,
    repo_dir_options: list[tuple[list[Path], str]],
    self_dup_ok: bool = False,
    self_nested_ok: bool = False,
) -> None:
    """Validate repository directories of the same type against themselves and others

    Parameters
    ----------
    repo_dirs: list[Path]
        A list of Paths, that represent repository directories of the same type
    repo_dir_name: str
        A name representing the type of repository directory
    repo_dir_options: list[tuple[list[Path | None], str]]
        A list of tuples, which will be used as the path_list and other_name parameter in a call to
        raise_on_path_in_list_of_paths()
    self_dup_ok: bool
        A boolean value indicating whether repo_dirs may contain duplicates (defaults to False)
    self_nested_ok: bool
        A boolean value indicating whether repo_dirs may contain nested dirs (defaults to False)

    Raises
    ------
    ValueError
        If repo_dirs contains a duplicate entry or if the call to raise_on_path_in_list_of_paths() raises.
    """

    if not self_dup_ok:
        dupes = [repo_dir for repo_dir in repo_dirs if repo_dirs.count(repo_dir) > 1]
        if dupes:
            raise ValueError(
                f"Duplicate {repo_dir_name} directories detected: {', '.join([str(repo_dir) for repo_dir in dupes])}"
            )

    if not self_nested_ok:
        for repo_dir in repo_dirs:
            for other_repo_dir in [other_dir for other_dir in repo_dirs if other_dir != repo_dir]:
                raise_on_path_in_other(
                    path=repo_dir,
                    path_name=repo_dir_name,
                    other=other_repo_dir,
                    other_name=repo_dir_name,
                )

    for repo_dir in repo_dirs:

        for option in repo_dir_options:
            raise_on_path_in_list_of_paths(
                path=repo_dir,
                path_name=repo_dir_name,
                path_list=option[0],
                other_name=option[1],
            )


def read_toml_configuration_settings(settings: BaseSettings) -> dict[str, Any]:
    """Read the configuration file(s)

    Parameters
    ----------
    settings: BaseSettings
        A BaseSettings instance

    Returns
    -------
    dict[str, Any]
        A dict containing the data from the read out configuration file(s)
    """

    output_dict: dict[str, Any] = {}
    config_files: list[Path] = []
    if CUSTOM_CONFIG:
        debug("Detected custom config location...")
        config_files += [CUSTOM_CONFIG]
    else:
        if isinstance(settings, UserSettings):
            debug("Detected user-mode settings...")
            if SETTINGS_LOCATION[SettingsTypeEnum.USER].exists():
                config_files += [SETTINGS_LOCATION[SettingsTypeEnum.USER]]
            if SETTINGS_OVERRIDE_LOCATION[SettingsTypeEnum.USER].exists():
                config_files += sorted(SETTINGS_OVERRIDE_LOCATION[SettingsTypeEnum.USER].glob("*.conf"))
        if isinstance(settings, SystemSettings):
            debug("Detected system-mode settings...")
            if SETTINGS_LOCATION[SettingsTypeEnum.SYSTEM].exists():
                config_files += [SETTINGS_LOCATION[SettingsTypeEnum.SYSTEM]]
            if SETTINGS_OVERRIDE_LOCATION[SettingsTypeEnum.SYSTEM].exists():
                config_files += sorted(SETTINGS_OVERRIDE_LOCATION[SettingsTypeEnum.SYSTEM].glob("*.conf"))

    debug(f"Found config files to read: {config_files}")
    for config_file in config_files:
        debug(f"Reading config file {config_file}...")
        with open(config_file, "rb") as file:
            file_dict = tomli.load(file)
            debug(f"Read configuration: {file_dict}")
            output_dict = output_dict | file_dict

    debug(f"Combined configuration: {output_dict}")
    return output_dict


class Settings(Architecture, BaseSettings, DatabaseCompression, PackagePool, SourcePool):
    """A class to describe a configuration for repod

    NOTE: Do not initialize this class directly and instead use UserSettings (for per-user configuration) or
    SystemSettings (for system-wide configuration) instead, as the Settings class lacks the required private attributes
    which define default directory locations.

    Attributes
    ----------
    architecture: ArchitectureEnum
        An optional ArchitectureEnum member, that (if set) defines the CPU architecture for any package repository which
        does not define one itself (defaults to DEFAULT_ARCHITECTURE).
    database_compression: CompressionTypeEnum
        A member of CompressionTypeEnum which defines the default database compression for any package repository
        without a database compression set (defaults to DEFAULT_DATABASE_COMPRESSION).
    management_repo: ManagementRepo | None
        An optional ManagementRepo, that (if set) defines a management repository setup for each package repository
        which does not define one itself.
        If unset, a default one is created during validation.
    package_pool: Path | None
        An optional relative or absolute directory, that is used as PackagePool for each PackageRepo, which does not
        define one itself.
        If a relative path is provided, it is prepended with _package_pool_base during validation.
        If an absolute path is provided, it is used as is.
        If unset, it is set to _package_pool_base / DEFAULT_NAME during validation.
    package_verification: PkgVerificationTypeEnum | None
        An optional member of PkgVerificationTypeEnum, which defines which verification scheme to apply for the detached
        package signatures.
    repositories: list[PackageRepo]
        A list of PackageRepos that each define a binary package repository (with optional debug, staging and testing
        locations). Each may define optional overrides for Architecture, ManagementRepo, PackagePool and SourcePool
        If no repository is defined, a default one is created during validation.
    source_pool: Path | None
        An optional relative or absolute directory, that is used as SourcePool for each PackageRepo, which does not
        define one itself.
        If a relative path is provided, it is prepended with _source_pool_base during validation.
        If an absolute path is provided, it is used as is.
        If unset, it is set to _source_pool_base / DEFAULT_NAME during validation.

    PrivateAttributes
    -----------------
    _settings_type: SettingsTypeEnum
        The type of Settings an instance represents (unset by default)
    _management_repo_base: Path
        The absolute path to the directory used as base for management repositories (unset by default)
    _package_pool_base: Path
        The absolute path to the directory used as base for package pool directories (unset by default)
    _package_repo_base: Path
        The absolute path to the directory used as base for package repository directories (unset by default)
    _source_pool_base: Path
        The absolute path to the directory used as base for source pool directories (unset by default)
    _source_repo_base: Path
        The absolute path to the directory used as base for source repository directories (unset by default)
    """

    _settings_type: SettingsTypeEnum = PrivateAttr()
    _management_repo_base: Path = PrivateAttr()
    _package_pool_base: Path = PrivateAttr()
    _package_repo_base: Path = PrivateAttr()
    _source_pool_base: Path = PrivateAttr()
    _source_repo_base: Path = PrivateAttr()

    architecture: ArchitectureEnum = DEFAULT_ARCHITECTURE
    database_compression: CompressionTypeEnum = DEFAULT_DATABASE_COMPRESSION
    management_repo: ManagementRepo | None
    repositories: list[PackageRepo] = []
    package_verification: PkgVerificationTypeEnum | None
    syncdb_settings: SyncDbSettings = SyncDbSettings()

    class Config:
        env_file_encoding = "utf-8"

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            return (
                init_settings,
                read_toml_configuration_settings,
                env_settings,
                file_secret_settings,
            )

    @validator("management_repo")
    def validate_management_repo(cls, management_repo: ManagementRepo | None) -> ManagementRepo:
        """Validate the ManagementRepo and return a default if none is set

        Return a default ManagementRepo created by a call to get_default_managementrepo() if none is set.

        Parameters
        ----------
        management_repo: ManagementRepo | None
            The optional ManagementRepo

        Returns
        -------
        ManagementRepo
            The instance's ManagementRepo or a default one
        """

        if not management_repo:
            debug("No configured global management repository found! Setting up default...")
            management_repo = get_default_managementrepo(settings_type=cls._settings_type)

        return management_repo

    @validator("repositories")
    def validate_repositories(cls, repositories: list[PackageRepo]) -> list[PackageRepo]:
        """Validator for the repositories attribute

        If the attribute is not set or is an empty list, it will be populated with a default generated by
        get_default_packagerepo()

        Parameters
        ----------
        repositories:  list[PackageRepo]
            A list of PackageRepo instances to validate

        Returns
        -------
        list[PackageRepo]
            A validated list of PackageRepo instances
        """

        if not repositories:
            debug("No configured package repository found! Setting up default...")
            repositories = [get_default_packagerepo(settings_type=cls._settings_type)]

        return repositories

    @root_validator
    def consolidate_and_create_repositories(
        cls,
        values: dict[str, Any],
    ) -> dict[str, Any]:
        """Consolidate repositories with global data and create respective directories

        Private attributes of each PackageRepo are consolidated with the global defaults provided by the Settings
        object.
        Application wide defaults are either provided by private attributes or by manually set attributes on the
        Settings object.

        Parameters
        ----------
        values: dict[str, Any]
            A dict representing the keys and values of the Settings object

        Returns
        -------
        dict[str, Any]
            A dict of validated keys and values of the Settings object
        """

        debug("Consolidating and creating repository directories...")

        repositories = cls.consolidate_repositories_with_defaults(
            architecture=values.get("architecture"),
            database_compression=values.get("database_compression"),
            management_repo=values.get("management_repo"),  # type: ignore[arg-type]
            package_pool=to_absolute_path(
                path=values.get("package_pool") or cls._package_pool_base / DEFAULT_NAME,
                base_path=cls._package_pool_base,
            ),
            repositories=values.get("repositories"),  # type: ignore[arg-type]
            source_pool=to_absolute_path(
                path=values.get("source_pool") or cls._source_pool_base / DEFAULT_NAME,
                base_path=cls._source_pool_base,
            ),
        )

        cls.ensure_non_overlapping_repositories(repositories=repositories)
        cls.create_repository_directories(repositories=repositories)

        return values

    @classmethod
    def consolidate_repositories_with_defaults(  # noqa: C901
        cls,
        architecture: ArchitectureEnum,
        database_compression: CompressionTypeEnum,
        management_repo: ManagementRepo,
        package_pool: Path,
        repositories: list[PackageRepo],
        source_pool: Path,
    ) -> list[PackageRepo]:
        """Consolidate each repository with global defaults

        The settings-wide defaults are used if a repository does not define the respective attribute.
        The consolidated attributes (e.g. canonicalized paths) are persisted using the dedicated private attribute of
        each PackageRepo object.

        Parameters
        ----------
        architecture: ArchitectureEnum
            The settings-wide default CPU architecture
        database_compression: CompressionTypeEnum
            The settings-wide default database compression
        management_repo: ManagementRepo
            The settings-wide default management repo
        package_pool: Path
            The settings-wide default package_pool
        repositories: list[PackageRepo]
            The list of package repositories
        source_pool: Path
            The settings-wide default source_pool

        Returns
        -------
        list[PackageRepo]
            The validated and consolidated list of PackageRepo objects
        """

        debug("Consolidating repositories with defaults...")

        for repo in repositories:
            if not repo.architecture and architecture:
                debug(f"Using global architecture ({architecture.value}) for repo {repo.name}.")
                repo.architecture = architecture
            if not repo.database_compression and database_compression:
                debug(f"Using global database compression ({database_compression.value}) for repo {repo.name}.")
                repo.database_compression = database_compression
            if not repo.management_repo and management_repo:
                debug(f"Using global management_repo ({management_repo}) for repo {repo.name}.")
                repo.management_repo = management_repo
            if not repo.package_pool and package_pool:
                debug(f"Using global package_pool ({package_pool}) for repo {repo.name}.")
                repo.package_pool = package_pool
            if not repo.source_pool and source_pool:
                debug(f"Using global source_pool ({source_pool}) for repo {repo.name}.")
                repo.source_pool = source_pool

            repo._stable_repo_dir = to_absolute_path(
                path=repo.name / repo.architecture.value,  # type: ignore[union-attr]
                base_path=cls._package_repo_base,
            )
            repo._stable_source_repo_dir = to_absolute_path(
                path=repo.name / repo.architecture.value,  # type: ignore[union-attr]
                base_path=cls._source_repo_base,
            )
            repo._stable_management_repo_dir = to_absolute_path(
                path=(
                    repo.management_repo.directory  # type: ignore[union-attr]
                    / repo.architecture.value  # type: ignore[union-attr]
                    / (repo.name.name if repo.name.is_absolute() else repo.name)
                ),
                base_path=cls._management_repo_base,
            )

            if repo.debug:
                repo._debug_repo_dir = to_absolute_path(
                    path=repo.debug / repo.architecture.value,  # type: ignore[union-attr]
                    base_path=cls._package_repo_base,
                )
                repo._debug_source_repo_dir = to_absolute_path(
                    path=repo.debug / repo.architecture.value,  # type: ignore[union-attr]
                    base_path=cls._source_repo_base,
                )
                repo._debug_management_repo_dir = to_absolute_path(
                    path=(
                        repo.management_repo.directory  # type: ignore[union-attr]
                        / repo.architecture.value  # type: ignore[union-attr]
                        / (repo.debug.name if repo.debug.is_absolute() else repo.debug)
                    ),
                    base_path=cls._management_repo_base,
                )

            if repo.staging:
                repo._staging_repo_dir = to_absolute_path(
                    path=repo.staging / repo.architecture.value,  # type: ignore[union-attr]
                    base_path=cls._package_repo_base,
                )
                repo._staging_source_repo_dir = to_absolute_path(
                    path=repo.staging / repo.architecture.value,  # type: ignore[union-attr]
                    base_path=cls._source_repo_base,
                )
                repo._staging_management_repo_dir = to_absolute_path(
                    path=(
                        repo.management_repo.directory  # type: ignore[union-attr]
                        / repo.architecture.value  # type: ignore[union-attr]
                        / (repo.staging.name if repo.staging.is_absolute() else repo.staging)
                    ),
                    base_path=cls._management_repo_base,
                )

                if repo.staging_debug:
                    repo._staging_debug_repo_dir = to_absolute_path(
                        path=repo.staging_debug / repo.architecture.value,  # type: ignore[union-attr]
                        base_path=cls._package_repo_base,
                    )
                    repo._staging_debug_source_repo_dir = to_absolute_path(
                        path=repo.staging_debug / repo.architecture.value,  # type: ignore[union-attr]
                        base_path=cls._source_repo_base,
                    )
                    repo._staging_debug_management_repo_dir = to_absolute_path(
                        path=(
                            repo.management_repo.directory  # type: ignore[union-attr]
                            / repo.architecture.value  # type: ignore[union-attr]
                            / (repo.staging_debug.name if repo.staging_debug.is_absolute() else repo.staging_debug)
                        ),
                        base_path=cls._management_repo_base,
                    )

            if repo.testing:
                repo._testing_repo_dir = to_absolute_path(
                    path=repo.testing / repo.architecture.value,  # type: ignore[union-attr]
                    base_path=cls._package_repo_base,
                )
                repo._testing_source_repo_dir = to_absolute_path(
                    path=repo.testing / repo.architecture.value,  # type: ignore[union-attr]
                    base_path=cls._source_repo_base,
                )
                repo._testing_management_repo_dir = to_absolute_path(
                    path=(
                        repo.management_repo.directory  # type: ignore[union-attr]
                        / repo.architecture.value  # type: ignore[union-attr]
                        / (repo.testing.name if repo.testing.is_absolute() else repo.testing)
                    ),
                    base_path=cls._management_repo_base,
                )
                if repo.testing_debug:
                    repo._testing_debug_repo_dir = to_absolute_path(
                        path=repo.testing_debug / repo.architecture.value,  # type: ignore[union-attr]
                        base_path=cls._package_repo_base,
                    )
                    repo._testing_debug_source_repo_dir = to_absolute_path(
                        path=repo.testing_debug / repo.architecture.value,  # type: ignore[union-attr]
                        base_path=cls._source_repo_base,
                    )
                    repo._testing_debug_management_repo_dir = to_absolute_path(
                        path=(
                            repo.management_repo.directory  # type: ignore[union-attr]
                            / repo.architecture.value  # type: ignore[union-attr]
                            / (repo.testing_debug.name if repo.testing_debug.is_absolute() else repo.testing_debug)
                        ),
                        base_path=cls._management_repo_base,
                    )

            repo._package_pool_dir = to_absolute_path(
                path=repo.package_pool,  # type: ignore[arg-type]
                base_path=cls._package_pool_base,
            )
            repo._source_pool_dir = to_absolute_path(
                path=repo.source_pool,  # type: ignore[arg-type]
                base_path=cls._source_pool_base,
            )

        return repositories

    @classmethod
    def create_repository_directories(cls, repositories: list[PackageRepo]) -> None:
        """Create the directories associated with package repositories

        Create directories only if the do not exist yet and validate that the directories are writeable.

        Parameters
        ----------
        repositories: list[PackageRepo]
            A list of package repositories for which to create directories
        """

        for repo in repositories:
            debug(f"Creating directories of repo {repo.name}...")
            create_and_validate_directory(directory=repo._stable_management_repo_dir)
            create_and_validate_directory(directory=repo._stable_repo_dir)
            create_and_validate_directory(directory=repo._stable_source_repo_dir)

            if repo.debug:
                create_and_validate_directory(directory=repo._debug_repo_dir)
                create_and_validate_directory(directory=repo._debug_source_repo_dir)
                create_and_validate_directory(directory=repo._debug_management_repo_dir)

            if repo.staging:
                create_and_validate_directory(directory=repo._staging_repo_dir)
                create_and_validate_directory(directory=repo._staging_source_repo_dir)
                create_and_validate_directory(directory=repo._staging_management_repo_dir)
            if repo.staging_debug:
                create_and_validate_directory(directory=repo._staging_debug_repo_dir)
                create_and_validate_directory(directory=repo._staging_debug_source_repo_dir)
                create_and_validate_directory(directory=repo._staging_debug_management_repo_dir)

            if repo.testing:
                create_and_validate_directory(directory=repo._testing_repo_dir)
                create_and_validate_directory(directory=repo._testing_source_repo_dir)
                create_and_validate_directory(directory=repo._testing_management_repo_dir)
            if repo.testing_debug:
                create_and_validate_directory(directory=repo._testing_debug_repo_dir)
                create_and_validate_directory(directory=repo._testing_debug_source_repo_dir)
                create_and_validate_directory(directory=repo._testing_debug_management_repo_dir)

            create_and_validate_directory(directory=repo._package_pool_dir)
            create_and_validate_directory(directory=repo._source_pool_dir)

    @classmethod
    def ensure_non_overlapping_repositories(cls, repositories: list[PackageRepo]) -> None:  # noqa: C901
        """Ensure that all repositories do not have overlapping directories

        Ensure that
            * there are no duplicate repository names
            * there are no overlapping directory structures amongst stable, debug, staging, staging debug, testing and
              testing debug repository directories (management and package repositories)
            * there are no overlapping directory structures with the package and or source pool directories

        Parameters
        ----------
        repositories: list[PackageRepo]
            A list of package repositories for which to create directories
        """

        debug("Ensuring package repositories have no overlapping directories...")

        stable_repo_dirs: list[Path] = [repo._stable_repo_dir for repo in repositories]
        debug(f"Repository directories (stable): {stable_repo_dirs}")

        stable_management_repo_dirs: list[Path] = [repo._stable_management_repo_dir for repo in repositories]
        debug(f"Management repository directories (stable): {stable_management_repo_dirs}")

        debug_management_repo_dirs: list[Path] = [
            repo._debug_management_repo_dir for repo in repositories if repo.debug
        ]
        debug(f"Management repository directories (debug): {debug_management_repo_dirs}")

        staging_management_repo_dirs: list[Path] = [
            repo._staging_management_repo_dir for repo in repositories if repo.staging
        ]
        debug(f"Management repository directories (staging): {staging_management_repo_dirs}")

        staging_debug_management_repo_dirs: list[Path] = [
            repo._staging_debug_management_repo_dir for repo in repositories if repo.staging_debug
        ]
        debug(f"Management repository directories (staging): {staging_debug_management_repo_dirs}")

        testing_management_repo_dirs: list[Path] = [
            repo._testing_management_repo_dir for repo in repositories if repo.testing
        ]
        debug(f"Management repository directories (testing): {testing_management_repo_dirs}")

        testing_debug_management_repo_dirs: list[Path] = [
            repo._testing_debug_management_repo_dir for repo in repositories if repo.testing_debug
        ]
        debug(f"Management repository directories (testing): {testing_management_repo_dirs}")

        package_pool_dirs: list[Path] = [repo._package_pool_dir for repo in repositories if repo.package_pool]
        debug(f"Package pool directories: {package_pool_dirs}")

        source_pool_dirs: list[Path] = [repo._source_pool_dir for repo in repositories if repo.source_pool]
        debug(f"Source pool directories: {source_pool_dirs}")

        debug_repo_dirs: list[Path] = [repo._debug_repo_dir for repo in repositories if repo.debug]
        debug(f"Debug repository directories: {debug_repo_dirs}")

        staging_repo_dirs: list[Path] = [repo._staging_repo_dir for repo in repositories if repo.staging]
        debug(f"Staging repository directories: {staging_repo_dirs}")

        staging_debug_repo_dirs: list[Path] = [
            repo._staging_debug_repo_dir for repo in repositories if repo.staging_debug
        ]
        debug(f"Staging debug repository directories: {staging_debug_repo_dirs}")

        testing_repo_dirs: list[Path] = [repo._testing_repo_dir for repo in repositories if repo.testing]
        debug(f"Testing repository directories: {testing_repo_dirs}")

        testing_debug_repo_dirs: list[Path] = [
            repo._testing_debug_repo_dir for repo in repositories if repo.testing_debug
        ]
        debug(f"Testing debug repository directories: {testing_debug_repo_dirs}")

        package_repos_options: list[tuple[list[Path], str]] = [
            (stable_repo_dirs, "stable repository"),
            (debug_repo_dirs, "stable debug repository"),
            (staging_repo_dirs, "staging repository"),
            (staging_debug_repo_dirs, "staging debug repository"),
            (testing_repo_dirs, "testing repository"),
            (testing_debug_repo_dirs, "testing debug repository"),
        ]
        management_repos_options: list[tuple[list[Path], str]] = [
            (stable_management_repo_dirs, "stable management repository"),
            (debug_management_repo_dirs, "stable debug management repository"),
            (staging_management_repo_dirs, "staging management repository"),
            (staging_debug_management_repo_dirs, "staging debug management repository"),
            (testing_management_repo_dirs, "testing management repository"),
            (testing_debug_management_repo_dirs, "testing debug management repository"),
        ]
        pool_dirs_options: list[tuple[list[Path], str]] = [
            (package_pool_dirs, "package pool"),
            (source_pool_dirs, "source pool"),
        ]

        validate_repo_paths(
            repo_dirs=stable_management_repo_dirs,
            repo_dir_name="stable management repository",
            repo_dir_options=[
                (debug_management_repo_dirs, "stable debug management repository"),
                (staging_management_repo_dirs, "staging management repository"),
                (staging_debug_management_repo_dirs, "staging debug management repository"),
                (testing_management_repo_dirs, "testing management repository"),
                (testing_debug_management_repo_dirs, "testing debug management repository"),
            ]
            + pool_dirs_options
            + package_repos_options,
        )

        validate_repo_paths(
            repo_dirs=debug_management_repo_dirs,
            repo_dir_name="stable debug management repository",
            repo_dir_options=[
                (stable_management_repo_dirs, "stable management repository"),
                (staging_management_repo_dirs, "staging management repository"),
                (staging_debug_management_repo_dirs, "staging debug management repository"),
                (testing_management_repo_dirs, "testing management repository"),
                (testing_debug_management_repo_dirs, "testing debug management repository"),
            ]
            + pool_dirs_options
            + package_repos_options,
        )

        validate_repo_paths(
            repo_dirs=staging_management_repo_dirs,
            repo_dir_name="staging management repository",
            repo_dir_options=[
                (stable_management_repo_dirs, "stable management repository"),
                (debug_management_repo_dirs, "stable debug management repository"),
                (staging_debug_management_repo_dirs, "staging debug management repository"),
                (testing_management_repo_dirs, "testing management repository"),
                (testing_debug_management_repo_dirs, "testing debug management repository"),
            ]
            + pool_dirs_options
            + package_repos_options,
        )

        validate_repo_paths(
            repo_dirs=staging_debug_management_repo_dirs,
            repo_dir_name="staging debug management repository",
            repo_dir_options=[
                (stable_management_repo_dirs, "stable management repository"),
                (debug_management_repo_dirs, "stable debug management repository"),
                (staging_management_repo_dirs, "staging management repository"),
                (testing_management_repo_dirs, "testing management repository"),
                (testing_debug_management_repo_dirs, "testing debug management repository"),
            ]
            + pool_dirs_options
            + package_repos_options,
        )

        validate_repo_paths(
            repo_dirs=testing_management_repo_dirs,
            repo_dir_name="testing management repository",
            repo_dir_options=[
                (stable_management_repo_dirs, "stable management repository"),
                (debug_management_repo_dirs, "stable debug management repository"),
                (staging_management_repo_dirs, "staging management repository"),
                (staging_debug_management_repo_dirs, "staging debug management repository"),
                (testing_debug_management_repo_dirs, "testing debug management repository"),
            ]
            + pool_dirs_options
            + package_repos_options,
        )

        validate_repo_paths(
            repo_dirs=testing_debug_management_repo_dirs,
            repo_dir_name="testing debug management repository",
            repo_dir_options=[
                (stable_management_repo_dirs, "stable management repository"),
                (debug_management_repo_dirs, "stable debug management repository"),
                (staging_management_repo_dirs, "staging management repository"),
                (staging_debug_management_repo_dirs, "staging debug management repository"),
                (testing_management_repo_dirs, "testing management repository"),
            ]
            + pool_dirs_options
            + package_repos_options,
        )

        validate_repo_paths(
            repo_dirs=package_pool_dirs,
            repo_dir_name="package pool",
            repo_dir_options=[
                (source_pool_dirs, "source pool"),
            ]
            + management_repos_options
            + package_repos_options,
            self_dup_ok=True,
        )

        validate_repo_paths(
            repo_dirs=source_pool_dirs,
            repo_dir_name="source pool",
            repo_dir_options=[
                (package_pool_dirs, "package pool"),
            ]
            + management_repos_options
            + package_repos_options,
            self_dup_ok=True,
        )

        validate_repo_paths(
            repo_dirs=stable_repo_dirs,
            repo_dir_name="stable repository",
            repo_dir_options=[
                (debug_repo_dirs, "stable debug repository"),
                (staging_repo_dirs, "staging repository"),
                (staging_debug_repo_dirs, "staging debug repository"),
                (testing_repo_dirs, "testing repository"),
                (testing_debug_repo_dirs, "testing debug repository"),
            ]
            + management_repos_options
            + pool_dirs_options,
        )

        validate_repo_paths(
            repo_dirs=debug_repo_dirs,
            repo_dir_name="debug repository",
            repo_dir_options=[
                (stable_repo_dirs, "stable repository"),
                (staging_repo_dirs, "staging repository"),
                (staging_debug_repo_dirs, "staging debug repository"),
                (testing_repo_dirs, "testing repository"),
                (testing_debug_repo_dirs, "testing debug repository"),
            ]
            + management_repos_options
            + pool_dirs_options,
        )

        validate_repo_paths(
            repo_dirs=staging_repo_dirs,
            repo_dir_name="staging repository",
            repo_dir_options=[
                (stable_repo_dirs, "stable repository"),
                (debug_repo_dirs, "stable debug repository"),
                (staging_debug_repo_dirs, "staging debug repository"),
                (testing_repo_dirs, "testing repository"),
                (testing_debug_repo_dirs, "testing debug repository"),
            ]
            + management_repos_options
            + pool_dirs_options,
        )

        validate_repo_paths(
            repo_dirs=staging_debug_repo_dirs,
            repo_dir_name="staging debug repository",
            repo_dir_options=[
                (stable_repo_dirs, "stable repository"),
                (debug_repo_dirs, "stable debug repository"),
                (staging_repo_dirs, "staging repository"),
                (testing_repo_dirs, "testing repository"),
                (testing_debug_repo_dirs, "testing debug repository"),
            ]
            + management_repos_options
            + pool_dirs_options,
        )

        validate_repo_paths(
            repo_dirs=testing_repo_dirs,
            repo_dir_name="testing repository",
            repo_dir_options=[
                (stable_repo_dirs, "stable repository"),
                (debug_repo_dirs, "stable debug repository"),
                (staging_repo_dirs, "staging repository"),
                (staging_debug_repo_dirs, "staging debug repository"),
                (testing_debug_repo_dirs, "testing debug repository"),
            ]
            + management_repos_options
            + pool_dirs_options,
        )

        validate_repo_paths(
            repo_dirs=testing_debug_repo_dirs,
            repo_dir_name="testing debug repository",
            repo_dir_options=[
                (stable_repo_dirs, "stable repository"),
                (debug_repo_dirs, "stable debug repository"),
                (staging_repo_dirs, "staging repository"),
                (staging_debug_repo_dirs, "staging debug repository"),
                (testing_repo_dirs, "testing repository"),
            ]
            + management_repos_options
            + pool_dirs_options,
        )

    def get_repo(self, name: Path, architecture: ArchitectureEnum | None) -> PackageRepo:
        """Get a repository

        Parameters
        ----------
        name: Path
            The name of the repository
        architecture: ArchitectureEnum | None
            The optional architecture of the repository

        Raises
        ------
        RuntimeError
            If more than one non-stable repository is targetted.
            If no repository matching the name can be found.

        Returns
        -------
        PackageRepo
            A package repository
        """

        names_arches = [(repo.name, repo.architecture) for repo in self.repositories]
        name_matches = [data for data in names_arches if data[0] == name]
        if not architecture and len(name_matches) > 1:
            raise RuntimeError(
                "An error occured while trying to get to a repository: "
                f"Specifying only a name ({name}) but no architecture while several repositories of the same name "
                f"({[str(data[0]) + ' (' + data[1].value + ')' for data in name_matches]}) "  # type: ignore[union-attr]
                "exist, would yield ambivalent results."
            )

        for repo in self.repositories:
            if (architecture is not None and repo.name == name and repo.architecture == architecture) or (
                architecture is None and repo.name == name
            ):
                return repo

        raise RuntimeError(
            f"Unable to find '{name}' {'(' + architecture.value + ')' if architecture else ''} in the available "
            f"repositories ({[str(name_) for name_ in [repo.name for repo in self.repositories]]})"
        )

    def get_repo_architecture(self, name: Path, architecture: ArchitectureEnum | None) -> ArchitectureEnum:
        """Get a repository's configured CPU architecture

        Parameters
        ----------
        name: Path
            The name of the repository
        architecture: ArchitectureEnum | None
            The optional architecture of the repository

        Returns
        -------
        ArchitectureEnum
            A member of ArchitectureEnum, which represents the CPU architecture of the repository
        """

        repo = self.get_repo(name=name, architecture=architecture)
        return repo.architecture

    def get_repo_database_compression(
        self,
        name: Path,
        architecture: ArchitectureEnum | None,
    ) -> CompressionTypeEnum:
        """Return the database compression type of a repository

        Parameters
        ----------
        name: Path
            The name of the repository
        architecture: ArchitectureEnum | None
            An optional member of ArchitectureEnum to define the CPU architecture of the repository

        Returns
        -------
        CompressionTypeEnum
            The database compression type of the repository identified by name and architecture
        """

        repo = self.get_repo(name=name, architecture=architecture)
        return repo.database_compression

    def get_repo_path(
        self,
        repo_dir_type: RepoDirTypeEnum,
        name: Path,
        architecture: ArchitectureEnum | None,
        repo_type: RepoTypeEnum,
    ) -> Path:
        """Return an absolute Path of a repository

        Parameters
        ----------
        repo_dir_type: RepoDirTypeEnum
            A member of RepoDirTypeEnum to define which type of repository path to return
        name: Path
            The name of the repository
        architecture: ArchitectureEnum | None
            An optional member of ArchitectureEnum to define the CPU architecture of the repository
        repo_type: RepoTypeEnum
            A member of RepoTypeEnum, that defines which type of repository is targeted.

        Raises
        ------
        RuntimeError
            If more than one non-stable repository is targetted.
            If no repository matching the name can be found.

        Returns
        -------
        Path
            An absolute Path which may describe stable, stable debug, staging, staging debug, testing or testing debug
            directory of a binary package repository, a management repository directory or the package pool directory of
            a PackageRepo
        """

        repo = self.get_repo(name=name, architecture=architecture)

        match repo_dir_type, repo_type:
            case RepoDirTypeEnum.MANAGEMENT, RepoTypeEnum.STABLE:
                return repo._stable_management_repo_dir
            case RepoDirTypeEnum.MANAGEMENT, RepoTypeEnum.STABLE_DEBUG:
                if not repo.debug:
                    raise RuntimeError(f"The repository {name} does not have a debug repository!")
                return repo._debug_management_repo_dir
            case RepoDirTypeEnum.MANAGEMENT, RepoTypeEnum.STAGING:
                if not repo.staging:
                    raise RuntimeError(f"The repository {name} does not have a staging repository!")
                return repo._staging_management_repo_dir
            case RepoDirTypeEnum.MANAGEMENT, RepoTypeEnum.STAGING_DEBUG:
                if not repo.staging:
                    raise RuntimeError(f"The repository {name} does not have a staging repository!")
                if not repo.staging_debug:
                    raise RuntimeError(f"The repository {name} does not have a staging debug repository!")
                return repo._staging_debug_management_repo_dir
            case RepoDirTypeEnum.MANAGEMENT, RepoTypeEnum.TESTING:
                if not repo.testing:
                    raise RuntimeError(f"The repository {name} does not have a testing repository!")
                return repo._testing_management_repo_dir
            case RepoDirTypeEnum.MANAGEMENT, RepoTypeEnum.TESTING_DEBUG:
                if not repo.testing:
                    raise RuntimeError(f"The repository {name} does not have a testing repository!")
                if not repo.testing_debug:
                    raise RuntimeError(f"The repository {name} does not have a testing debug repository!")
                return repo._testing_debug_management_repo_dir
            case RepoDirTypeEnum.PACKAGE, RepoTypeEnum.STABLE:
                return repo._stable_repo_dir
            case RepoDirTypeEnum.PACKAGE, RepoTypeEnum.STABLE_DEBUG:
                if not repo.debug:
                    raise RuntimeError(f"The repository {name} does not have a debug repository!")
                return repo._debug_repo_dir
            case RepoDirTypeEnum.PACKAGE, RepoTypeEnum.STAGING:
                if not repo.staging:
                    raise RuntimeError(f"The repository {name} does not have a staging repository!")
                return repo._staging_repo_dir
            case RepoDirTypeEnum.PACKAGE, RepoTypeEnum.STAGING_DEBUG:
                if not repo.staging:
                    raise RuntimeError(f"The repository {name} does not have a staging repository!")
                if not repo.staging_debug:
                    raise RuntimeError(f"The repository {name} does not have a staging debug repository!")
                return repo._staging_debug_repo_dir
            case RepoDirTypeEnum.PACKAGE, RepoTypeEnum.TESTING:
                if not repo.testing:
                    raise RuntimeError(f"The repository {name} does not have a testing repository!")
                return repo._testing_repo_dir
            case RepoDirTypeEnum.PACKAGE, RepoTypeEnum.TESTING_DEBUG:
                if not repo.testing:
                    raise RuntimeError(f"The repository {name} does not have a testing repository!")
                if not repo.testing_debug:
                    raise RuntimeError(f"The repository {name} does not have a testing debug repository!")
                return repo._testing_debug_repo_dir
            case RepoDirTypeEnum.POOL, _:
                return repo._package_pool_dir
            case _:
                raise RuntimeError(f"An unknown error occurred while trying to retrieve a repository path for {name}!")

    def get_management_repo_stability_paths(
        self,
        name: Path,
        architecture: ArchitectureEnum | None,
        repo_type: RepoTypeEnum,
    ) -> tuple[list[Path], list[Path]]:
        """Return the management repository directories of stability layers above and below the current

        Parameters
        ----------
        name: Path
            The name of the repository
        architecture: ArchitectureEnum | None
            The optional CPU architecture of the repository
        repo_type: RepoTypeEnum
            A member of RepoTypeEnum identifying the stability layer for which the layers above and below are returned

        Raises
        ------
        RuntimeError
            If the provided repo_type can not be used to retrieve stability layers

        Returns
        -------
        tuple[list[Path], list[Path]]
            A tuple of two Path lists that represent the stability layers above (first list) and below (second list) the
            stability layer represented by repo_type.
        """

        repo = self.get_repo(name=name, architecture=architecture)

        match repo_type:
            case RepoTypeEnum.STABLE:
                above = []
                above += [repo._staging_management_repo_dir] if repo.staging else []
                above += [repo._testing_management_repo_dir] if repo.testing else []
                return (above, [])
            case RepoTypeEnum.STABLE_DEBUG:
                if not repo.debug:
                    raise RuntimeError(
                        f"The repository {name} ({architecture.value if architecture else ''}) has no debug repository!"
                    )

                above = []
                above += [repo._staging_debug_management_repo_dir] if repo.staging else []
                above += [repo._testing_debug_management_repo_dir] if repo.testing else []
                return (above, [])
            case RepoTypeEnum.STAGING:
                if not repo.staging:
                    raise RuntimeError(
                        f"The repository {name} ({architecture.value if architecture else ''}) "
                        "has no staging repository!"
                    )

                below = [repo._stable_management_repo_dir]
                below += [repo._testing_management_repo_dir] if repo.testing else []
                return ([], below)
            case RepoTypeEnum.STAGING_DEBUG:
                if not repo.debug:
                    raise RuntimeError(
                        f"The repository {name} ({architecture.value if architecture else ''}) has no debug repository!"
                    )
                if not repo.staging:
                    raise RuntimeError(
                        f"The repository {name} ({architecture.value if architecture else ''}) "
                        "has no staging repository!"
                    )

                below = [repo._debug_management_repo_dir]
                below += [repo._testing_debug_management_repo_dir] if repo.testing else []
                return ([], below)
            case RepoTypeEnum.TESTING:
                if not repo.testing:
                    raise RuntimeError(
                        f"The repository {name} ({architecture.value if architecture else ''}) "
                        "has no testing repository!"
                    )

                return ([repo._staging_management_repo_dir] if repo.staging else [], [repo._stable_management_repo_dir])
            case RepoTypeEnum.TESTING_DEBUG:
                if not repo.debug:
                    raise RuntimeError(
                        f"The repository {name} ({architecture.value if architecture else ''}) has no debug repository!"
                    )
                if not repo.testing:
                    raise RuntimeError(
                        f"The repository {name} ({architecture.value if architecture else ''}) "
                        "has no testing repository!"
                    )

                return (
                    [repo._staging_debug_management_repo_dir] if repo.staging else [],
                    [repo._debug_management_repo_dir],
                )
            case _:
                raise RuntimeError(f"Can not derive stability layers above and below {repo_type}")

    def get_repo_management_repo(
        self,
        name: Path,
        architecture: ArchitectureEnum | None,
    ) -> ManagementRepo:
        """Get the ManagementRepo of a PackageRepo

        Parameters
        ----------
        name: Path
            The name of the repository
        architecture: ArchitectureEnum
            The architecture of the repository

        Returns
        -------
        ManagementRepo
            The ManagementRepo of the repository identified by name and architecture
        """

        repo = self.get_repo(name=name, architecture=architecture)
        return repo.management_repo  # type: ignore[return-value]


class UserSettings(Settings):
    """User-level Settings, which assume XDG compliant configuration locations and defaults

    Attributes
    ----------
    architecture: ArchitectureEnum
        An optional ArchitectureEnum member, that (if set) defines the CPU architecture for any package repository which
        does not define one itself (defaults to DEFAULT_ARCHITECTURE).
    database_compression: CompressionTypeEnum
        A member of CompressionTypeEnum which defines the default database compression for any package repository
        without a database compression set (defaults to DEFAULT_DATABASE_COMPRESSION).
    management_repo: ManagementRepo | None
        An optional ManagementRepo, that (if set) defines a management repository setup for each package repository
        which does not define one itself.
        If unset, a default one is created during validation.
    repositories: list[PackageRepo]
        A list of PackageRepos that each define a binary package repository (with optional staging and testing
        locations). Each may define optional overrides for Architecture, ManagementRepo, PackagePool and SourcePool
        If no repository is defined, a default one is created during validation.
    package_pool: Path | None
        An optional relative or absolute directory, that is used as PackagePool for each PackageRepo, which does not
        define one itself.
        If a relative path is provided, it is prepended with _package_pool_base during validation.
        If an absolute path is provided, it is used as is.
        If unset, it is set to _package_pool_base / DEFAULT_NAME during validation.
    source_pool: Path | None
        An optional relative or absolute directory, that is used as SourcePool for each PackageRepo, which does not
        define one itself.
        If a relative path is provided, it is prepended with _source_pool_base during validation.
        If an absolute path is provided, it is used as is.
        If unset, it is set to _source_pool_base / DEFAULT_NAME during validation.

    PrivateAttributes
    -----------------
    _settings_type: SettingsTypeEnum
        The type of Settings an instance represents (SettingsTypeEnum.USER)
    _management_repo_base: Path
        The absolute path to the directory used as base for management repositories
        (MANAGEMENT_REPO_BASE[SettingsTypeEnum.USER])
    _package_pool_base: Path
        The absolute path to the directory used as base for package pool directories
        (PACKAGE_POOL_BASE[SettingsTypeEnum.USER])
    _package_repo_base: Path
        The absolute path to the directory used as base for package repository directories
        (PACKAGE_REPO_BASE[SettingsTypeEnum.USER])
    _source_pool_base: Path
        The absolute path to the directory used as base for source pool directories
        (SOURCE_POOL_BASE[SettingsTypeEnum.USER])
    _source_repo_base: Path
        The absolute path to the directory used as base for source repository directories
        (SOURCE_REPO_BASE[SettingsTypeEnum.USER])
    """

    _settings_type = SettingsTypeEnum.USER
    _management_repo_base = MANAGEMENT_REPO_BASE[SettingsTypeEnum.USER]
    _package_pool_base = PACKAGE_POOL_BASE[SettingsTypeEnum.USER]
    _package_repo_base = PACKAGE_REPO_BASE[SettingsTypeEnum.USER]
    _source_pool_base = SOURCE_POOL_BASE[SettingsTypeEnum.USER]
    _source_repo_base = SOURCE_REPO_BASE[SettingsTypeEnum.USER]


class SystemSettings(Settings):
    """System-level Settings, which assume system-wide configuration locations and defaults

    Attributes
    ----------
    architecture: ArchitectureEnum
        An optional ArchitectureEnum member, that (if set) defines the CPU architecture for any package repository which
        does not define one itself (defaults to DEFAULT_ARCHITECTURE).
    database_compression: CompressionTypeEnum
        A member of CompressionTypeEnum which defines the default database compression for any package repository
        without a database compression set (defaults to DEFAULT_DATABASE_COMPRESSION).
    management_repo: ManagementRepo | None
        An optional ManagementRepo, that (if set) defines a management repository setup for each package repository
        which does not define one itself.
        If unset, a default one is created during validation.
    repositories: list[PackageRepo]
        A list of PackageRepos that each define a binary package repository (with optional staging and testing
        locations). Each may define optional overrides for Architecture, ManagementRepo, PackagePool and SourcePool
        If no repository is defined, a default one is created during validation.
    package_pool: Path | None
        An optional relative or absolute directory, that is used as PackagePool for each PackageRepo, which does not
        define one itself.
        If a relative path is provided, it is prepended with _package_pool_base during validation.
        If an absolute path is provided, it is used as is.
        If unset, it is set to _package_pool_base / DEFAULT_NAME during validation.
    source_pool: Path | None
        An optional relative or absolute directory, that is used as SourcePool for each PackageRepo, which does not
        define one itself.
        If a relative path is provided, it is prepended with _source_pool_base during validation.
        If an absolute path is provided, it is used as is.
        If unset, it is set to _source_pool_base / DEFAULT_NAME during validation.

    PrivateAttributes
    -----------------
    _settings_type: SettingsTypeEnum
        The type of Settings an instance represents (SettingsTypeEnum.SYSTEM)
    _management_repo_base: Path
        The absolute path to the directory used as base for management repositories
        (MANAGEMENT_REPO_BASE[SettingsTypeEnum.SYSTEM])
    _package_pool_base: Path
        The absolute path to the directory used as base for package pool directories
        (PACKAGE_POOL_BASE[SettingsTypeEnum.SYSTEM])
    _package_repo_base: Path
        The absolute path to the directory used as base for package repository directories
        (PACKAGE_REPO_BASE[SettingsTypeEnum.SYSTEM])
    _source_pool_base: Path
        The absolute path to the directory used as base for source pool directories
        (SOURCE_POOL_BASE[SettingsTypeEnum.SYSTEM])
    _source_repo_base: Path
        The absolute path to the directory used as base for source repository directories
        (SOURCE_REPO_BASE[SettingsTypeEnum.SYSTEM])
    """

    _settings_type = SettingsTypeEnum.SYSTEM
    _management_repo_base = MANAGEMENT_REPO_BASE[SettingsTypeEnum.SYSTEM]
    _package_pool_base = PACKAGE_POOL_BASE[SettingsTypeEnum.SYSTEM]
    _package_repo_base = PACKAGE_REPO_BASE[SettingsTypeEnum.SYSTEM]
    _source_pool_base = SOURCE_POOL_BASE[SettingsTypeEnum.SYSTEM]
    _source_repo_base = SOURCE_REPO_BASE[SettingsTypeEnum.SYSTEM]


def get_default_managementrepo(settings_type: SettingsTypeEnum) -> ManagementRepo:
    """Return a default ManagementRepo instance depending on settings type


    Parameters
    ----------
    settings_type: SettingsTypeEnum
        A settings type

    Raises
    ------
    RuntimeError
        If the provided SettingsTypeEnum member is not valid

    Returns
    -------
    ManagementRepo
        A ManagementRepo using system-wide locations if SettingsTypeEnum.SYSTEM is provided, or a ManagementRepo using
        per-user locations if SettingsTypeEnum.USER is provided.
    """

    debug(f"Creating default ManagementRepo for settings_type {settings_type.value}...")
    match settings_type:
        case SettingsTypeEnum.SYSTEM:
            return ManagementRepo(directory=MANAGEMENT_REPO_BASE[SettingsTypeEnum.SYSTEM] / DEFAULT_NAME)
        case SettingsTypeEnum.USER:
            return ManagementRepo(directory=MANAGEMENT_REPO_BASE[SettingsTypeEnum.USER] / DEFAULT_NAME)
        case _:
            raise RuntimeError("Invalid settings_type provided for creating a default ManagementRepo!")


def get_default_packagerepo(settings_type: SettingsTypeEnum) -> PackageRepo:
    """Return a default PackageRepo

    If SettingsTypeEnum.SYSTEM is provided as settings_type, a PackageRepo using system wide default directories is
    returned.
    If SettingsTypeEnum.USER is provided as settings_type, a PackageRepo using per-user default directories is returned.

    Parameters
    ----------
    settings_type: SettingsTypeEnum
        A settings type based upon which the PackageRepo is created

    Raises
    ------
    RuntimeError
        If an invalid SettingsTypeEnum member is provided

    Returns
    -------
    PackageRepo
        A PackageRepo instance with defaults based upon settings_type
    """

    debug(f"Creating default PackageRepo for settings_type: {settings_type.value}...")
    match settings_type:
        case SettingsTypeEnum.USER:
            return PackageRepo(
                architecture=DEFAULT_ARCHITECTURE,
                name=DEFAULT_NAME,
                management_repo=ManagementRepo(directory=MANAGEMENT_REPO_BASE[SettingsTypeEnum.USER] / DEFAULT_NAME),
                package_pool=PACKAGE_POOL_BASE[SettingsTypeEnum.USER] / DEFAULT_NAME,
                source_pool=SOURCE_POOL_BASE[SettingsTypeEnum.USER] / DEFAULT_NAME,
            )
        case SettingsTypeEnum.SYSTEM:
            return PackageRepo(
                name=DEFAULT_NAME,
                architecture=DEFAULT_ARCHITECTURE,
                management_repo=ManagementRepo(directory=MANAGEMENT_REPO_BASE[SettingsTypeEnum.SYSTEM] / DEFAULT_NAME),
                package_pool=PACKAGE_POOL_BASE[SettingsTypeEnum.SYSTEM] / DEFAULT_NAME,
                source_pool=SOURCE_POOL_BASE[SettingsTypeEnum.SYSTEM] / DEFAULT_NAME,
            )
        case _:
            raise RuntimeError("Invalid settings_type provided for creating a default PackageRepo!")
