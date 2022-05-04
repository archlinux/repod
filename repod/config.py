from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import tomli
from pydantic import BaseSettings, root_validator, validator
from pydantic.env_settings import SettingsSourceCallable

from repod import defaults, models


def _raise_on_path_equals_other(path: Path, path_name: str, other: Path, other_name: str) -> None:
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


def _raise_on_path_in_other(path: Path, path_name: str, other: Path, other_name: str) -> None:
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


def _raise_on_path_in_list_of_paths(path: Path, path_name: str, path_list: List[Path], other_name: str) -> None:
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
        _raise_on_path_equals_other(path=path, path_name=path_name, other=test_path, other_name=other_name)
        _raise_on_path_in_other(path=path, path_name=path_name, other=test_path, other_name=other_name)


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
    if defaults.SETTINGS_LOCATION.exists():
        config_files += [defaults.SETTINGS_LOCATION]
    if defaults.SETTINGS_OVERRIDE_LOCATION.exists():
        config_files += sorted(defaults.SETTINGS_OVERRIDE_LOCATION.glob("*.conf"))

    for config_file in config_files:
        with open(config_file, "rb") as file:
            output_dict | tomli.load(file)
    return output_dict


class Settings(models.Architecture, BaseSettings, models.PackagePool, models.SourcePool):
    """A class to describe a configuration for repod

    Attributes
    ----------
    repositories: List[PackageRepo]
        A list of PackageRepo instances that each define a binary package repository (with optional staging and testing
        locations). Each may define optional overrides for Architecture, ManagementRepo, PackagePool and SourcePool
    package_repo_base: Path
        A directory that serves as the base for all directories, that are defined for the package repositories and are
        used for storing symlinks to binary package files and their signatures (defaults to defaults.PACKAGE_REPO_BASE)
    source_repo_base: Path
        A directory that serves as the base for all directories, that are defined for the package repositories and are
        used for storing symlinks to source tarballs (defaults to defaults.SOURCE_REPO_BASE)
    architecture: Optional[str]
        An optional Architecture string (see defaults.ARCHITECTURES), that if set is used for each package repository
        to set its CPU architecture unless a package repository defines an architecture itself
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

    repositories: List[models.PackageRepo]
    management_repo: Optional[models.ManagementRepo]
    package_repo_base: Path = defaults.PACKAGE_REPO_BASE
    source_repo_base: Path = defaults.SOURCE_REPO_BASE

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
    def validate_repositories(cls, repositories: List[models.PackageRepo]) -> List[models.PackageRepo]:
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
            models.Directory.validate_directory(directory=directory)

        repositories: List[models.PackageRepo] = values.get("repositories")  # type: ignore[assignment]
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

        _raise_on_path_in_list_of_paths(
            path=source_repo_base,
            path_name="source repository base",
            path_list=management_repo_dirs,
            other_name="management repository",
        )
        _raise_on_path_in_list_of_paths(
            path=source_repo_base,
            path_name="source repository base",
            path_list=package_pool_dirs,
            other_name="package pool",
        )
        _raise_on_path_in_list_of_paths(
            path=source_repo_base,
            path_name="source repository base",
            path_list=source_pool_dirs,
            other_name="source pool",
        )
        _raise_on_path_in_list_of_paths(
            path=source_repo_base,
            path_name="source repository base",
            path_list=[package_repo_base],
            other_name="package repository base",
        )

        _raise_on_path_in_list_of_paths(
            path=package_repo_base,
            path_name="package repository base",
            path_list=package_pool_dirs,
            other_name="package pool",
        )
        _raise_on_path_in_list_of_paths(
            path=package_repo_base,
            path_name="package repository base",
            path_list=source_pool_dirs,
            other_name="source pool",
        )
        _raise_on_path_in_list_of_paths(
            path=package_repo_base,
            path_name="package repository base",
            path_list=[source_repo_base],
            other_name="source repository base",
        )
        _raise_on_path_in_list_of_paths(
            path=package_repo_base,
            path_name="package repository base",
            path_list=management_repo_dirs,
            other_name="management repository",
        )

        for source_pool_dir in source_pool_dirs:
            _raise_on_path_in_list_of_paths(
                path=source_pool_dir,
                path_name="source pool",
                path_list=package_pool_dirs,
                other_name="package pool",
            )
            _raise_on_path_in_list_of_paths(
                path=source_pool_dir,
                path_name="source pool",
                path_list=management_repo_dirs,
                other_name="management repository",
            )
            _raise_on_path_in_list_of_paths(
                path=source_pool_dir,
                path_name="source pool",
                path_list=[package_repo_base],
                other_name="package repository base",
            )
            _raise_on_path_in_list_of_paths(
                path=source_pool_dir,
                path_name="source pool",
                path_list=[source_repo_base],
                other_name="source repository base",
            )

        for package_pool_dir in package_pool_dirs:
            _raise_on_path_in_list_of_paths(
                path=package_pool_dir,
                path_name="package pool",
                path_list=source_pool_dirs,
                other_name="source pool",
            )
            _raise_on_path_in_list_of_paths(
                path=package_pool_dir,
                path_name="package pool",
                path_list=management_repo_dirs,
                other_name="management repository",
            )
            _raise_on_path_in_list_of_paths(
                path=package_pool_dir,
                path_name="package pool",
                path_list=[package_repo_base],
                other_name="package repository base",
            )
            _raise_on_path_in_list_of_paths(
                path=package_pool_dir,
                path_name="package pool",
                path_list=[source_repo_base],
                other_name="source repository base",
            )

        for management_repo_dir in management_repo_dirs:
            _raise_on_path_in_list_of_paths(
                path=management_repo_dir,
                path_name="management repository",
                path_list=package_pool_dirs,
                other_name="package pool",
            )
            _raise_on_path_in_list_of_paths(
                path=management_repo_dir,
                path_name="management repository",
                path_list=source_pool_dirs,
                other_name="source pool",
            )
            _raise_on_path_in_list_of_paths(
                path=management_repo_dir,
                path_name="management repository",
                path_list=[package_repo_base],
                other_name="package repository base",
            )
            _raise_on_path_in_list_of_paths(
                path=management_repo_dir,
                path_name="management repository",
                path_list=[source_repo_base],
                other_name="source repository base",
            )

        for repo in repositories:
            repo_package_pool = repo.package_pool or package_pool
            repo_source_pool = repo.source_pool or source_pool

            if repo_package_pool:
                _raise_on_path_equals_other(
                    path=package_repo_base,
                    path_name="package repository base",
                    other=repo_package_pool,
                    other_name="repository package pool",
                )
                _raise_on_path_in_other(
                    path=package_repo_base,
                    path_name="package repository base",
                    other=repo_package_pool,
                    other_name="repository package pool",
                )
                _raise_on_path_in_other(
                    path=repo_package_pool,
                    path_name="repository package pool",
                    other=package_repo_base,
                    other_name="package repository base",
                )
                _raise_on_path_equals_other(
                    path=source_repo_base,
                    path_name="source repository base",
                    other=repo_package_pool,
                    other_name="repository package pool",
                )
                _raise_on_path_in_other(
                    path=source_repo_base,
                    path_name="source repository base",
                    other=repo_package_pool,
                    other_name="repository package pool",
                )
                _raise_on_path_in_other(
                    path=repo_package_pool,
                    path_name="repository package pool",
                    other=source_repo_base,
                    other_name="source repository base",
                )

            if repo_source_pool:
                _raise_on_path_equals_other(
                    path=package_repo_base,
                    path_name="package repository base",
                    other=repo_source_pool,
                    other_name="repository source pool",
                )
                _raise_on_path_in_other(
                    path=package_repo_base,
                    path_name="package repository base",
                    other=repo_source_pool,
                    other_name="repository source pool",
                )
                _raise_on_path_equals_other(
                    path=source_repo_base,
                    path_name="source repository base",
                    other=repo_source_pool,
                    other_name="repository source pool",
                )
                _raise_on_path_in_other(
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

        repositories: List[models.PackageRepo] = values.get("repositories")  # type: ignore[assignment]
        architecture, management_repo, package_pool, source_pool, package_repo_base = (
            values.get("architecture"),
            values.get("management_repo"),
            values.get("package_pool"),
            values.get("source_pool"),
            values.get("package_repo_base"),
        )

        staging_dirs = [
            (
                package_repo_base  # type: ignore[operator]
                / repo.staging
                / Path(repo.architecture or architecture)  # type: ignore[arg-type]
            )
            for repo in repositories
            if repo.staging
        ]
        testing_dirs = [
            (
                package_repo_base  # type: ignore[operator]
                / repo.testing
                / Path(repo.architecture or architecture)  # type: ignore[arg-type]
            )
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

            repo_dir = (
                package_repo_base  # type: ignore[operator]
                / repo.name
                / Path(repo.architecture or architecture)  # type: ignore[arg-type]
            )
            _raise_on_path_in_list_of_paths(
                path=repo_dir,
                path_name="stable repository",
                path_list=staging_dirs,
                other_name="staging repository",
            )
            _raise_on_path_in_list_of_paths(
                path=repo_dir,
                path_name="stable repository",
                path_list=testing_dirs,
                other_name="testing repository",
            )
            _raise_on_path_in_list_of_paths(
                path=repo_dir,
                path_name="stable repository",
                path_list=management_repo_dirs,
                other_name="management repository",
            )

            if repo.staging:
                staging_dir = (
                    package_repo_base  # type: ignore[operator]
                    / repo.staging
                    / Path(repo.architecture or architecture)  # type: ignore[arg-type]
                )
                _raise_on_path_in_list_of_paths(
                    path=staging_dir,
                    path_name="the staging repository",
                    path_list=testing_dirs,
                    other_name="testing repository",
                )

            if repo.testing:
                testing_dir = (
                    package_repo_base  # type: ignore[operator]
                    / repo.testing
                    / Path(repo.architecture or architecture)  # type: ignore[arg-type]
                )
                _raise_on_path_in_list_of_paths(
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
