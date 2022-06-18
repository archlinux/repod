import os
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import tomli
from pydantic import AnyUrl, BaseModel, BaseSettings, constr, root_validator, validator
from pydantic.env_settings import SettingsSourceCallable

from repod.common.regex import ARCHITECTURE
from repod.config.defaults import (
    MANAGEMENT_REPO,
    PACKAGE_REPO_BASE,
    SETTINGS_LOCATION,
    SETTINGS_OVERRIDE_LOCATION,
    SOURCE_REPO_BASE,
)


def validate_directory(directory: Path) -> Path:
    """A validator for an absolute and writable directory Path

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


class Architecture(BaseModel):
    """A model describing a single "architecture" attribute

    Attributes
    ----------
    architecture: Path
        A string describing a valid architecture for a repository
    """

    architecture: Optional[constr(regex=f"^{ARCHITECTURE}$")]  # type: ignore[valid-type]  # noqa: F722


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
            An optional Path instance to validate. If a Path instance is provided, validate_directory() is used for
            validation

        Returns
        -------
        Optional[Path]
            A validated Path instance, if a Path is provided, else None
        """

        if package_pool is None:
            return package_pool
        else:
            return Path(validate_directory(directory=package_pool))


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
            An optional Path instance to validate. If a Path instance is provided, validate_directory() is used for
            validation

        Returns
        -------
        Optional[Path]
            A validated Path instance, if a Path is provided, else None
        """

        if source_pool is None:
            return source_pool
        else:
            return Path(validate_directory(directory=source_pool))


class ManagementRepo(BaseModel):
    """A model describing all required attributes to describe a repository used for managing one or more package
    repositories

    Attributes
    ----------
    directory: Path
        A Path instance describing the location of the management repository
    url: AnyUrl
        A URL describing the VCS upstream of the management repository
    """

    directory: Path = MANAGEMENT_REPO
    url: AnyUrl

    @validator("directory")
    def validate_directory(cls, directory: Path) -> Path:
        """A validator for the directory attribute

        Parameters
        ----------
        directory: Path
            A Path, that describes the location for the ManagementRepo

        Returns
        -------
        Path
            A validated Path
        """

        return Path(validate_directory(directory=directory))

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
            f"The {path_name} directory '{path}' " f"can not be the same as the {other_name} directory '{other}'."
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

    if set(path.parts).issuperset(set(other.parts)):
        raise ValueError(
            f"The {path_name} directory '{path}' " f"can not reside in the {other_name} directory '{other}'."
        )


def raise_on_path_in_list_of_paths(path: Path, path_name: str, path_list: List[Path], other_name: str) -> None:
    """Raise when a Path instance is in a list of Path instances

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
        If path is in path_list
    """

    for test_path in path_list:
        raise_on_path_equals_other(path=path, path_name=path_name, other=test_path, other_name=other_name)
        raise_on_path_in_other(path=path, path_name=path_name, other=test_path, other_name=other_name)


def read_toml_configuration_settings(settings: BaseSettings) -> Dict[str, Any]:
    """Read the configuration file(s)

    Parameters
    ----------
    settings: BaseSettings
        A BaseSettings instance

    Returns
    -------
    Dict[str, Any]
        A dict containing the data from the read out configuration file(s)
    """

    output_dict: Dict[str, Any] = {}
    config_files: List[Path] = []
    if SETTINGS_LOCATION.exists():
        config_files += [SETTINGS_LOCATION]
    if SETTINGS_OVERRIDE_LOCATION.exists():
        config_files += sorted(SETTINGS_OVERRIDE_LOCATION.glob("*.conf"))

    for config_file in config_files:
        with open(config_file, "rb") as file:
            output_dict | tomli.load(file)
    return output_dict


class Settings(Architecture, BaseSettings, PackagePool, SourcePool):
    """A class to describe a configuration for repod

    Attributes
    ----------
    repositories: List[PackageRepo]
        A list of PackageRepo instances that each define a binary package repository (with optional staging and testing
        locations). Each may define optional overrides for Architecture, ManagementRepo, PackagePool and SourcePool
    package_repo_base: Path
        A directory that serves as the base for all directories, that are defined for the package repositories and are
        used for storing symlinks to binary package files and their signatures (defaults to PACKAGE_REPO_BASE)
    source_repo_base: Path
        A directory that serves as the base for all directories, that are defined for the package repositories and are
        used for storing symlinks to source tarballs (defaults to SOURCE_REPO_BASE)
    architecture: Optional[str]
        An optional Architecture string (see Architecture), that if set is used for each package
        repository to set its CPU architecture unless a package repository defines an architecture itself
        NOTE: It is mandatory to provide an architecture for each package repository!
    management_repo: Optional[ManagementRepo]
        An optional ManagementRepo, that if set is used for each package repository to manage the state of each package
        repository, unless a package repository defines a management repository itself
        NOTE: It is mandatory to provide a management repository for each package repository!
    package_pool: Optional[Path]
        An optional directory, that if set is used for each package repository to store the binary packages and their
        signatures in, unless a package repository defines a package pool itself. From this directory the active
        packages are symlinked into their respective package repository directories
        NOTE: It is mandatory to provide a package pool for each package repository!
    source_pool: Optional[Path]
        An optional directory, that if set is used for each package repository to store the binary source tarballs for
        each package in, unless a package repository defines a source pool itself. From this directory the active
        source tarballs of packages are symlinked into their respective package repository directories
        NOTE: It is mandatory to provide a source pool for each package repository!
    """

    repositories: List[PackageRepo]
    management_repo: Optional[ManagementRepo]
    package_repo_base: Path = PACKAGE_REPO_BASE
    source_repo_base: Path = SOURCE_REPO_BASE

    class Config:
        env_file_encoding = "utf-8"

        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> Tuple[SettingsSourceCallable, ...]:
            return (
                init_settings,
                read_toml_configuration_settings,
                env_settings,
                file_secret_settings,
            )

    @validator("repositories")
    def validate_repositories(cls, repositories: List[PackageRepo]) -> List[PackageRepo]:
        """A validator for the repositories attribute, ensuring that there is at least one repository defined

        Parameters
        ----------
        repositories: List[PackageRepo]
            A list of PackageRepo instances to validate

        Raises
        ------
        ValueError
            If there are no repositories defined

        Returns
        -------
        List[PackageRepo]
            A list of validated PackageRepo instances
        """

        if not repositories:
            raise ValueError("There are no repositories defined!")

        return repositories

    @root_validator
    def validate_package_repo_base_source_repo_base(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """A root_validator to ensure, that package_repo_base and source_repo_base are valid

        Parameters
        ----------
        values: Dict[str, Any]
            A dict with all values of the Settings instance

        Raises
        ------
        ValueError
            If either path does not exists, is not absolute, or is not writable,
            if package_repo_base and source_repo_base are the same,
            if either of the two equals the other or is located in the respective other,
            if either of the two is equal to or located in any of the management repository directories, source pool
            directories or package pool directories,
            or if any of the management repository directories resides below the package_repo_base or source_repo_base
            directories.

        Returns
        -------
        values: Dict[str, Any]
            The unmodified dict with all values of the Settings instance
        """

        package_repo_base: Path = values.get("package_repo_base")  # type: ignore[assignment]
        source_repo_base: Path = values.get("source_repo_base")  # type: ignore[assignment]
        for directory in [package_repo_base, source_repo_base]:
            validate_directory(directory=directory)

        repositories: List[PackageRepo] = values.get("repositories")  # type: ignore[assignment]
        management_repo, package_pool, source_pool = (
            values.get("management_repo"),
            values.get("package_pool"),
            values.get("source_pool"),
        )
        management_repo_dirs = (
            [repo.management_repo.directory for repo in repositories if repo.management_repo]
            + [management_repo.directory]
            if management_repo
            else []
        )
        package_pool_dirs = (
            [repo.package_pool for repo in repositories if repo.package_pool] + [package_pool] if package_pool else []
        )
        source_pool_dirs = (
            [repo.source_pool for repo in repositories if repo.source_pool] + [source_pool] if source_pool else []
        )

        raise_on_path_in_list_of_paths(
            path=source_repo_base,
            path_name="source repository base",
            path_list=management_repo_dirs,
            other_name="management repository",
        )
        raise_on_path_in_list_of_paths(
            path=source_repo_base,
            path_name="source repository base",
            path_list=package_pool_dirs,
            other_name="package pool",
        )
        raise_on_path_in_list_of_paths(
            path=source_repo_base,
            path_name="source repository base",
            path_list=source_pool_dirs,
            other_name="source pool",
        )
        raise_on_path_in_list_of_paths(
            path=source_repo_base,
            path_name="source repository base",
            path_list=[package_repo_base],
            other_name="package repository base",
        )

        raise_on_path_in_list_of_paths(
            path=package_repo_base,
            path_name="package repository base",
            path_list=package_pool_dirs,
            other_name="package pool",
        )
        raise_on_path_in_list_of_paths(
            path=package_repo_base,
            path_name="package repository base",
            path_list=source_pool_dirs,
            other_name="source pool",
        )
        raise_on_path_in_list_of_paths(
            path=package_repo_base,
            path_name="package repository base",
            path_list=[source_repo_base],
            other_name="source repository base",
        )
        raise_on_path_in_list_of_paths(
            path=package_repo_base,
            path_name="package repository base",
            path_list=management_repo_dirs,
            other_name="management repository",
        )

        for source_pool_dir in source_pool_dirs:
            raise_on_path_in_list_of_paths(
                path=source_pool_dir,
                path_name="source pool",
                path_list=package_pool_dirs,
                other_name="package pool",
            )
            raise_on_path_in_list_of_paths(
                path=source_pool_dir,
                path_name="source pool",
                path_list=management_repo_dirs,
                other_name="management repository",
            )
            raise_on_path_in_list_of_paths(
                path=source_pool_dir,
                path_name="source pool",
                path_list=[package_repo_base],
                other_name="package repository base",
            )
            raise_on_path_in_list_of_paths(
                path=source_pool_dir,
                path_name="source pool",
                path_list=[source_repo_base],
                other_name="source repository base",
            )

        for package_pool_dir in package_pool_dirs:
            raise_on_path_in_list_of_paths(
                path=package_pool_dir,
                path_name="package pool",
                path_list=source_pool_dirs,
                other_name="source pool",
            )
            raise_on_path_in_list_of_paths(
                path=package_pool_dir,
                path_name="package pool",
                path_list=management_repo_dirs,
                other_name="management repository",
            )
            raise_on_path_in_list_of_paths(
                path=package_pool_dir,
                path_name="package pool",
                path_list=[package_repo_base],
                other_name="package repository base",
            )
            raise_on_path_in_list_of_paths(
                path=package_pool_dir,
                path_name="package pool",
                path_list=[source_repo_base],
                other_name="source repository base",
            )

        for management_repo_dir in management_repo_dirs:
            raise_on_path_in_list_of_paths(
                path=management_repo_dir,
                path_name="management repository",
                path_list=package_pool_dirs,
                other_name="package pool",
            )
            raise_on_path_in_list_of_paths(
                path=management_repo_dir,
                path_name="management repository",
                path_list=source_pool_dirs,
                other_name="source pool",
            )
            raise_on_path_in_list_of_paths(
                path=management_repo_dir,
                path_name="management repository",
                path_list=[package_repo_base],
                other_name="package repository base",
            )
            raise_on_path_in_list_of_paths(
                path=management_repo_dir,
                path_name="management repository",
                path_list=[source_repo_base],
                other_name="source repository base",
            )

        for repo in repositories:
            repo_package_pool = repo.package_pool or package_pool
            repo_source_pool = repo.source_pool or source_pool

            if repo_package_pool:
                raise_on_path_equals_other(
                    path=package_repo_base,
                    path_name="package repository base",
                    other=repo_package_pool,
                    other_name="repository package pool",
                )
                raise_on_path_in_other(
                    path=package_repo_base,
                    path_name="package repository base",
                    other=repo_package_pool,
                    other_name="repository package pool",
                )
                raise_on_path_in_other(
                    path=repo_package_pool,
                    path_name="repository package pool",
                    other=package_repo_base,
                    other_name="package repository base",
                )
                raise_on_path_equals_other(
                    path=source_repo_base,
                    path_name="source repository base",
                    other=repo_package_pool,
                    other_name="repository package pool",
                )
                raise_on_path_in_other(
                    path=source_repo_base,
                    path_name="source repository base",
                    other=repo_package_pool,
                    other_name="repository package pool",
                )
                raise_on_path_in_other(
                    path=repo_package_pool,
                    path_name="repository package pool",
                    other=source_repo_base,
                    other_name="source repository base",
                )

            if repo_source_pool:
                raise_on_path_equals_other(
                    path=package_repo_base,
                    path_name="package repository base",
                    other=repo_source_pool,
                    other_name="repository source pool",
                )
                raise_on_path_in_other(
                    path=package_repo_base,
                    path_name="package repository base",
                    other=repo_source_pool,
                    other_name="repository source pool",
                )
                raise_on_path_equals_other(
                    path=source_repo_base,
                    path_name="source repository base",
                    other=repo_source_pool,
                    other_name="repository source pool",
                )
                raise_on_path_in_other(
                    path=source_repo_base,
                    path_name="source repository base",
                    other=repo_source_pool,
                    other_name="repository source pool",
                )

        return values

    @root_validator
    def validate_existing_paths_for_repositories(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """A root_validator to ensure, that each PackageRepo has an Architecture, a ManagementRepo, a PackagePool and a
        SourcePool

        Parameters
        ----------
        values: Dict[str, Any]
            A dict with all values of the Settings instance

        Raises
        ------
        ValueError
            If a repository has no Architecture, ManagementRepo, PackagePool or SourcePool associated with it,
            if the stable repository directory is also one of the management repository, staging or testing directories,
            if a repository's staging repository directory is one of the testing repository directories,
            if a repository's testing repository directory is one of the staging repository directories,
            or if a duplicate repository (name and architecture) exists.

        Returns
        -------
        values: Dict[str, Any]
            The unmodified dict with all values of the Settings instance
        """

        architecture: Optional[str] = values.get("architecture")
        management_repo: Optional[ManagementRepo] = values.get("management_repo")
        package_pool: Optional[Path] = values.get("package_pool")
        repositories: List[PackageRepo] = values.get("repositories")  # type: ignore[assignment]
        source_pool: Optional[Path] = values.get("source_pool")
        package_repo_base: Path = values.get("package_repo_base")  # type: ignore[assignment]

        staging_dirs = [
            (package_repo_base / repo.staging / Path(repo.architecture or architecture))  # type: ignore[arg-type]
            for repo in repositories
            if repo.staging
        ]
        testing_dirs = [
            (package_repo_base / repo.testing / Path(repo.architecture or architecture))  # type: ignore[arg-type]
            for repo in repositories
            if repo.testing
        ]
        management_repo_dirs = (
            [repo.management_repo.directory for repo in repositories if repo.management_repo]
            + [management_repo.directory]
            if management_repo
            else []
        )

        for repo in repositories:
            if not repo.architecture and not architecture:
                raise ValueError(f"The repository '{repo.name}' does not have a CPU architecture associated with it.")
            if not repo.management_repo and not management_repo:
                raise ValueError(
                    f"The repository '{repo.name}' does not have a management repository associated with it."
                )
            if not repo.package_pool and not package_pool:
                raise ValueError(f"The repository '{repo.name}' does not have a package pool associated with it.")
            if not repo.source_pool and not source_pool:
                raise ValueError(f"The repository '{repo.name}' does not have a source pool associated with it.")

            repo_dir = package_repo_base / repo.name / Path(repo.architecture or architecture)  # type: ignore[arg-type]
            raise_on_path_in_list_of_paths(
                path=repo_dir,
                path_name="stable repository",
                path_list=staging_dirs,
                other_name="staging repository",
            )
            raise_on_path_in_list_of_paths(
                path=repo_dir,
                path_name="stable repository",
                path_list=testing_dirs,
                other_name="testing repository",
            )
            raise_on_path_in_list_of_paths(
                path=repo_dir,
                path_name="stable repository",
                path_list=management_repo_dirs,
                other_name="management repository",
            )

            if repo.staging:
                staging_dir = (
                    package_repo_base / repo.staging / Path(repo.architecture or architecture)  # type: ignore[arg-type]
                )
                raise_on_path_in_list_of_paths(
                    path=staging_dir,
                    path_name="the staging repository",
                    path_list=testing_dirs,
                    other_name="testing repository",
                )

            if repo.testing:
                testing_dir = (
                    package_repo_base / repo.testing / Path(repo.architecture or architecture)  # type: ignore[arg-type]
                )
                raise_on_path_in_list_of_paths(
                    path=testing_dir,
                    path_name="testing repository",
                    path_list=staging_dirs,
                    other_name="staging repository",
                )

        names_architectures = [(inner.name, inner.architecture or architecture) for inner in repositories]
        if len(set(names_architectures)) < len(names_architectures):
            duplicates = [k for k, v in Counter(names_architectures).items() if v > 1]
            raise ValueError(
                f"The following {'combination' if len(duplicates) == 1 else 'combinations'} of (stable) "
                f"repository name and architecture {'is' if len(duplicates) == 1 else 'are'} not unique: {duplicates}"
            )

        return values
