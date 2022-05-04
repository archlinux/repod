import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyUrl, BaseModel, root_validator, validator

from repo_management import defaults


class Architecture(BaseModel):
    """A model describing a single "architecture" attribute

    Attributes
    ----------
    architecture: Path
        A string describing a valid architecture for a repository
    """

    architecture: Optional[str]

    @validator("architecture")
    def validate_architecture(cls, architecture: Optional[str]) -> Optional[str]:
        if architecture is None:
            return architecture
        if architecture not in defaults.ARCHITECTURES:
            raise ValueError(
                f"The architecture '{architecture}' is not supported (must be one of {defaults.ARCHITECTURES}"
            )
        return architecture


class Directory(BaseModel):
    """A model describing a single "directory" attribute

    Attributes
    ----------
    directory: Path
        A Path instance that identifies an absolute directory location for e.g. binary packages or source tarball data
    """

    directory: Path

    @validator("directory")
    def validate_directory(cls, directory: Path) -> Path:
        """A validator for the directory attribute

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
            An optional Path instance to validate. If a Path instance is provided, Directory.validate_directory() is
            used for validation

        Returns
        -------
        Optional[Path]
            A validated Path instance, if a Path is provided, else None
        """

        if package_pool is None:
            return package_pool
        else:
            return Path(Directory.validate_directory(directory=package_pool))


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
            An optional Path instance to validate. If a Path instance is provided, Directory.validate_directory() is
            used for validation

        Returns
        -------
        Optional[Path]
            A validated Path instance, if a Path is provided, else None
        """

        if source_pool is None:
            return source_pool
        else:
            return Path(Directory.validate_directory(directory=source_pool))


class ManagementRepo(Directory):
    """A model describing all required attributes to describe a repository used for managing one or more package
    repositories

    Attributes
    ----------
    directory: Path
        A Path instance describing the location of the management repository
    url: AnyUrl
        A URL describing the VCS upstream of the management repository
    """

    url: AnyUrl

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
