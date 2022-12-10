"""Checks for various circumstances."""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections import defaultdict
from logging import debug, info
from pathlib import Path

from pydantic import HttpUrl

from repod.common.enums import ActionStateEnum, ArchitectureEnum, PkgTypeEnum
from repod.config.settings import UrlValidationSettings
from repod.errors import RepoManagementFileError
from repod.files import Package
from repod.files.pkginfo import PkgInfoV2, PkgType
from repod.repo.management import OutputPackageBase
from repod.repo.package.repofile import filename_parts
from repod.verification import PacmanKeyVerifier
from repod.version.alpm import pkg_vercmp


class Check(ABC):
    """An abstract base class to describe a check.

    Checks are Callables, that run a check (e.g. on an input) and must not alter data.

    Attributes
    ----------
    state: ActionStateEnum
        A member of ActionStateEnum indicating whether a Check is not started, started, failed or succeeded (defaults to
        ActionStateEnum.NOT_STARTED
    """

    state: ActionStateEnum = ActionStateEnum.NOT_STARTED

    @abstractmethod
    def __call__(self) -> ActionStateEnum:  # pragma: no cover
        """Call a Check.

        The method is expected to set the Check's state property to ActionStateEnum.STARTED, run a check
        operation, set the state property to either ActionStateEnum.SUCCESS or to ActionStateEnum.FAILED (depending on
        whether the check operation finished successfully or not, respectively) and return the state.

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS if the check passed successfully,
            ActionStateEnum.FAILED otherwise
        """
        pass


class PacmanKeyPackagesSignatureVerificationCheck(Check):
    """Verify a list of package signatures using pacman-key.

    This Check fails if any package can not be verified with its corresponding signature or if any of the
    package/signature lists is not of length two.

    Attributes
    ----------
    packages: list[list[Path]]
        A list of Path lists, that should contain a package and a corresponding signature Path each
    """

    def __init__(self, packages: list[list[Path]]) -> None:
        """Initialize an instance of PacmanKeyPackagesSignatureVerificationCheck.

        Parameters
        ----------
        package: list[list[Path]]
            A list of lists, containing up to two Paths each
        """
        self.packages = packages

    def __call__(self) -> ActionStateEnum:
        """Use an instance of PacmanKeyVerifier to verify a package and its signature.

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS if the check passed successfully,
            ActionStateEnum.FAILED otherwise
        """
        self.state = ActionStateEnum.STARTED

        if not all(len(package_list) == 2 for package_list in self.packages):
            info("Verification with pacman-key is requested, but not all packages provide a signature!")
            self.state = ActionStateEnum.FAILED
            return self.state

        verifier = PacmanKeyVerifier()
        debug(f"Verifying list of packages using pacman-key: {self.packages}")
        for package_list in self.packages:
            if verifier.verify(
                package=package_list[0],
                signature=package_list[1],
            ):
                debug("Package {package_list[0]} successfully verified using signature {package_list[1]}!")
            else:
                info(
                    f"Verification of package {package_list[0]} with signature {package_list[1]} "
                    "failed using pacman-key!"
                )
                self.state = ActionStateEnum.FAILED
                return self.state

        self.state = ActionStateEnum.SUCCESS
        return self.state


class DebugPackagesCheck(Check):
    """A Check to evaluate whether all instances in a list of packages are either debug or not debug packages.

    This Check currently only works successfully with packages that use PkgInfoV2, as before that PkgInfo
    implementation, figuring out whether a package is a debug package is merely guess work.
    Package files providing a PkgInfo version lower than PkgInfoV2 will always pass this test!

    Attributes
    ----------
    packages: list[Package]
        A list of Package instances to check
    debug: bool
        A boolean value indicating whether all Package instances should be debug packages or not
    """

    def __init__(self, packages: list[Package], debug: bool) -> None:
        """Initialize an instance of DebugPackagesCheck.

        Parameters
        ----------
        packages: list[Package]
            A list of Package instances to check
        debug: bool
            A boolean value indicating whether all Package instances should be either debug packages or not
        """
        self.packages = packages
        self.debug = debug

    def __call__(self) -> ActionStateEnum:
        """Check whether all instances of self.packages are supposed to be debug packages or not.

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS if the check is successful,
            ActionStateEnum.FAILED otherwise
        """
        self.state = ActionStateEnum.STARTED

        debug(f"Testing whether all packages are either default or debug packages: {self.packages}")
        if self.debug:
            if any(
                [
                    True
                    for package in self.packages
                    if isinstance(
                        package.pkginfo,  # type: ignore[attr-defined]
                        PkgInfoV2,
                    )
                    and PkgType(pkgtype=PkgTypeEnum.DEBUG) not in package.pkginfo.xdata  # type: ignore[attr-defined]
                ]
            ):
                info("A debug repository is targetted, but not all provided packages are debug packages!")
                self.state = ActionStateEnum.FAILED
                return self.state
        else:
            if any(
                [
                    True
                    for package in self.packages
                    if isinstance(
                        package.pkginfo,  # type: ignore[attr-defined]
                        PkgInfoV2,
                    )
                    and PkgType(pkgtype=PkgTypeEnum.DEBUG) in package.pkginfo.xdata  # type: ignore[attr-defined]
                ]
            ):
                info("A non-debug repository is targetted, but not all provided packages are non-debug packages!")
                self.state = ActionStateEnum.FAILED
                return self.state

        self.state = ActionStateEnum.SUCCESS
        return self.state


class MatchingArchitectureCheck(Check):
    """A Check to ensure that a list of packages match a target CPU architecture.

    Attributes
    ----------
    architecture: ArchitectureEnum
        An instance of ArchitectureEnum which identifies the target CPU architecture
    packages: list[Package]
        A list of Package instances to check
    """

    def __init__(self, architecture: ArchitectureEnum, packages: list[Package]) -> None:
        """Initialize an instance of MatchingArchitectureCheck.

        Parameters
        ----------
        architecture: ArchitectureEnum
            An instance of ArchitectureEnum which identifies the target CPU architecture
        packages: list[Package]
            A list of Package instances to check
        """
        self.architecture = architecture
        self.packages = packages

    def __call__(self) -> ActionStateEnum:
        """Check whether all instances of self.packages are supposed to be debug packages or not.

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS if the check is successful,
            ActionStateEnum.FAILED otherwise
        """
        self.state = ActionStateEnum.STARTED

        debug("Running check to test whether all packages match the target architecture...")

        non_matching: list[str] = []

        for package in self.packages:
            if (
                package.pkginfo.arch != self.architecture.value  # type: ignore[attr-defined]
                and package.pkginfo.arch != ArchitectureEnum.ANY.value  # type: ignore[attr-defined]
            ):
                non_matching.append(f"{package.pkginfo.name}/{package.pkginfo.arch}")  # type: ignore[attr-defined]

        if len(non_matching) > 0:
            self.state = ActionStateEnum.FAILED
            info(
                "Adding package(s) to repository failed as the following packages are not compatible with CPU "
                f"architecture {'(' + self.architecture.value + ')' if self.architecture else ''}: {non_matching}"
            )
        else:
            self.state = ActionStateEnum.SUCCESS

        return self.state


class MatchingFilenameCheck(Check):
    """A Check to ensure that package metadata matches the data from the package filename.

    Attributes
    ----------
    packages_and_paths: list[tuple[Package, Path]]
        A list of tuples of Package instances and Path instances to check
    """

    def __init__(self, packages_and_paths: list[tuple[Package, Path]]) -> None:
        """Initialize an instance of MatchingFilenameCheck.

        Parameters
        ----------
        packages_and_paths: list[tuple[Package, Path]]
            A list of tuples of Package instances and Path instances to check
        """
        self.packages_and_paths = packages_and_paths

    def __call__(self) -> ActionStateEnum:
        """Check that package metadata matches data from the filename.

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS if the check is successful,
            ActionStateEnum.FAILED otherwise
        """
        self.state = ActionStateEnum.STARTED

        debug("Running check to test whether package metadata and package filenames match...")

        non_matching: list[str] = []

        for package, path in self.packages_and_paths:
            pkginfo = package.pkginfo  # type: ignore[attr-defined]
            filename_data = filename_parts(path)
            pkg_data = {"arch": pkginfo.arch, "name": pkginfo.name, "version": pkginfo.version}
            for key, value in pkg_data.items():
                if filename_data[key] != value:
                    msg = f"{package.filename}: {filename_data[key]}/{value}"  # type: ignore[attr-defined]
                    non_matching.append(msg)

        if len(non_matching) > 0:
            self.state = ActionStateEnum.FAILED
            info(
                "Adding package(s) to repository failed as the following packages have a mismatch between package "
                f"filename and package metadata: {non_matching}"
            )
        else:
            self.state = ActionStateEnum.SUCCESS

        return self.state


class PkgbasesVersionUpdateCheck(Check):
    """A Check to ensure, that pkgbases are updated, not downgraded.

    Attributes
    ----------
    new_pkgbases: list[OutputPackageBase]
        A list of updated OutputPackageBase instances
    current_pkgbases: list[OutputPackageBase]
        A list of current OutputPackageBase instances
    """

    def __init__(
        self,
        new_pkgbases: list[OutputPackageBase],
        current_pkgbases: list[OutputPackageBase],
    ) -> None:
        """Initialize an instance of PkgbasesVersionUpdateCheck.

        Parameters
        ----------
        new_pkgbases: list[OutputPackageBase]
            A list of updated OutputPackageBase instances
        current_pkgbases: list[OutputPackageBase]
            A list of current OutputPackageBase instances
        """
        self.new_pkgbases = new_pkgbases
        self.current_pkgbases = current_pkgbases

    def __call__(self) -> ActionStateEnum:
        """Check, that pkgbases are updated, not downgraded.

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS if the check passed successfully,
            ActionStateEnum.FAILED otherwise
        """
        self.state = ActionStateEnum.STARTED

        debug("Running check to test whether all pkgbases are being upgraded, not downgraded...")

        current_names_versions = [
            {"name": c_pkgbase.base, "version": c_pkgbase.version}  # type: ignore[attr-defined]
            for c_pkgbase in self.current_pkgbases
        ]

        for pkgbase in self.new_pkgbases:
            name = pkgbase.base  # type: ignore[attr-defined]
            version = pkgbase.version  # type: ignore[attr-defined]
            if name in [c_dict.get("name") for c_dict in current_names_versions]:
                c_version = [
                    str(c_dict.get("version")) for c_dict in current_names_versions if str(c_dict.get("name")) == name
                ][0]
                if (
                    pkg_vercmp(
                        c_version,
                        version,
                    )
                    >= 0
                ):
                    info(
                        f"The version of {name} currently "
                        f"in the repository is newer than the provided one: {c_version} vs. {version}"
                    )
                    self.state = ActionStateEnum.FAILED
                    return self.state

        self.state = ActionStateEnum.SUCCESS
        return self.state


class PackagesNewOrUpdatedCheck(Check):
    """A Check to ensure, that packages are new or updated.

    Attributes
    ----------
    directory: Path
        A Path to the directory in a management repository where to look for OutputPackageBases
    new_pkgbases: list[OutputPackageBase]
        A list of updated OutputPackageBase instances
    current_pkgbases: list[OutputPackageBase]
        A list of current OutputPackageBase instances
    """

    def __init__(
        self,
        directory: Path,
        new_pkgbases: list[OutputPackageBase],
        current_pkgbases: list[OutputPackageBase],
    ) -> None:
        """Initialize an instance of PackagesNewOrUpdatedCheck.

        Parameters
        ----------
        directory: Path
            A Path to the directory in a management repository where to look for OutputPackageBases
        new_pkgbases: list[OutputPackageBase]
            A list of updated OutputPackageBase instances
        current_pkgbases: list[OutputPackageBase]
            A list of current OutputPackageBase instances
        """
        self.directory = directory
        self.new_pkgbases = new_pkgbases
        self.current_pkgbases = current_pkgbases

    def __call__(self) -> ActionStateEnum:
        """Check, that packages are new or updated.

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS if the check passed successfully,
            ActionStateEnum.FAILED otherwise
        """
        self.state = ActionStateEnum.STARTED

        debug("Running check to test that all packages are either new or updated...")

        current_pkgbases = [
            {
                "name": c_pkgbase.base,  # type: ignore[attr-defined]
                "packages": [pkg.name for pkg in c_pkgbase.packages],  # type: ignore[attr-defined]
                "version": c_pkgbase.version,  # type: ignore[attr-defined]
            }
            for c_pkgbase in self.current_pkgbases
        ]
        new_pkgbases = [
            {
                "name": pkgbase.base,  # type: ignore[attr-defined]
                "packages": [pkg.name for pkg in pkgbase.packages],  # type: ignore[attr-defined]
                "version": pkgbase.version,  # type: ignore[attr-defined]
            }
            for pkgbase in self.new_pkgbases
        ]

        for pkgbase in new_pkgbases:
            target_pkgbase_file = self.directory / Path(str(pkgbase.get("name")) + ".json")

            for package in pkgbase.get("packages", []):
                target_package_file = self.directory / "pkgnames" / Path(package + ".json")
                target_package_pkgbase = target_package_file.resolve().name.replace(".json", "")
                original_pkgbase_in_new_pkgbases = any(
                    True for pkgbase in new_pkgbases if pkgbase.get("name") == target_package_pkgbase
                )
                original_pkgbase_provides_package = any(
                    [
                        True
                        for pkgbase in new_pkgbases
                        if pkgbase.get("name") == target_package_pkgbase and package in str(pkgbase.get("packages"))
                    ]
                )

                # the pkgbase of the new package does not match an existing pkgbase (in current_pkgbases or
                # new_pkgbases), but a file exists and provides a version newer than the one added
                if (
                    target_package_file.is_symlink()
                    and target_package_file.resolve() != target_pkgbase_file
                    and pkgbase.get("name") not in [pkgbase.get("name") for pkgbase in current_pkgbases]
                ):
                    try:
                        old_pkgbase = asyncio.run(OutputPackageBase.from_file(target_package_file.resolve()))
                    except RepoManagementFileError as e:
                        info(e)
                        self.state = ActionStateEnum.FAILED
                        return self.state

                    old_version = old_pkgbase.get_version()
                    new_version = str(pkgbase.get("version"))

                    if pkg_vercmp(old_version, new_version) >= 0:
                        info(
                            f"The version of the added {package} (provided by pkgbase {pkgbase.get('name')}) "
                            "is newer or equal to the one already in the repository (provided by pkgbase "
                            f"{target_package_pkgbase}): {old_version} (old) vs. {new_version} (new)"
                        )
                        self.state = ActionStateEnum.FAILED
                        return self.state

                # the pkgbase of the new package does not match an existing pkgbase and the update also does not
                # remove the package from the previous pkgbase
                if (
                    target_package_file.is_symlink()
                    and target_package_file.resolve() != target_pkgbase_file
                    and (
                        not original_pkgbase_in_new_pkgbases
                        or (original_pkgbase_in_new_pkgbases and original_pkgbase_provides_package)
                    )
                ):
                    info(
                        f"The package {package} is currently provided by "
                        f"pkgbase {target_package_pkgbase}, but the new pkgbase "
                        f"{pkgbase.get('name')} now tries to provide it, "
                        f"without removing the package from the pkgbase {target_package_pkgbase}."
                    )
                    self.state = ActionStateEnum.FAILED
                    return self.state

        self.state = ActionStateEnum.SUCCESS
        return self.state


class SourceUrlCheck(Check):
    """Check that pkgbases have a source url, if their repository validation settings require it.

    Attributes
    ----------
    new_pkgbases: dict[str, HttpUrl | None]
        A dict representing new pkgbases and their respective optional upstream URL (to check)
    current_pkgbase_urls: dict[str, HttpUrl | None]
        A dict representing current pkgbases and their respective optional upstream URL
    url_validation_settings: UrlValidationSettings | None
        An optional UrlValidationSettings instance with which to validate source URLs of the provided new_pkgbases
    """

    def __init__(
        self,
        new_pkgbases: list[OutputPackageBase],
        current_pkgbases: list[OutputPackageBase],
        url_validation_settings: UrlValidationSettings | None,
    ) -> None:
        """Initialize an instance of SourceUrlCheck.

        Parameters
        ----------
        new_pkgbases: list[OutputPackageBase]
            A list of OutputPackageBase instances representing new pkgbases to check
        current_pkgbases: list[OutputPackageBase]
            A list of current OutputPackageBase instances (a subset of new_pkgbases)
        url_validation_settings: UrlValidationSettings | None
            An optional UrlValidationSettings instance with which to validate source URLs of the provided new_pkgbases
        """
        self.new_pkgbase_urls: dict[str, HttpUrl | None] = {
            pkgbase.base: pkgbase.source_url for pkgbase in new_pkgbases  # type: ignore[attr-defined]
        }
        self.current_pkgbase_urls: dict[str, HttpUrl | None] = {
            pkgbase.base: pkgbase.source_url for pkgbase in current_pkgbases  # type: ignore[attr-defined]
        }
        self.url_validation_settings = url_validation_settings

    def __call__(self) -> ActionStateEnum:
        """Check that pkgbases have a source url, if their repository validation settings require it.

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS if the check passed successfully,
            ActionStateEnum.FAILED otherwise
        """
        self.state = ActionStateEnum.STARTED

        debug("Running check to validate the URLs of pkgbases... ")

        if not self.url_validation_settings:
            debug("No URL validation required, skipping check...")
            self.state = ActionStateEnum.SUCCESS
            return self.state

        for pkgbase, url in self.new_pkgbase_urls.items():
            url = url or self.current_pkgbase_urls.get(pkgbase)

            if not url:
                info(f"The pkgbase {pkgbase} does neither already have a source URL set nor is one provided for it!")
                self.state = ActionStateEnum.FAILED
                return self.state

            if not self.url_validation_settings.validate_url(url=url):
                info(
                    f"The source URL of the pkgbase {pkgbase} ({url}) does not validate "
                    "against the repository's settings!"
                )
                self.state = ActionStateEnum.FAILED
                return self.state

        self.state = ActionStateEnum.SUCCESS
        return self.state


class StabilityLayerCheck(Check):
    """A Check to compare the versions of pkgbases in the stability layers above and below them.

    Attributes
    ----------
    pkgbases: list[OutputPackageBase]
        A list of OutputPackageBase objects, that represent the pkgbases to be checked
    pkgbases_above: list[OutputPackageBase]
        A list of OutputPackageBase objects, that represent the pkgbases in stability layers above those in pkgbases
    pkgbases_below: list[OutputPackageBase]
        A list of OutputPackageBase objects, that represent the pkgbases in stability layers below those in pkgbases
    """

    def __init__(
        self,
        pkgbases: list[OutputPackageBase],
        pkgbases_above: list[OutputPackageBase],
        pkgbases_below: list[OutputPackageBase],
    ) -> None:
        """Initialize an instance of StabilityLayerCheck.

        Parameters
        ----------
        pkgbases: list[OutputPackageBase]
            A list of OutputPackageBase objects, that represent the pkgbases to be checked
        pkgbases_above: list[OutputPackageBase]
            A list of OutputPackageBase objects, that represent the pkgbases in stability layers above those in pkgbases
        pkgbases_below: list[OutputPackageBase]
            A list of OutputPackageBase objects, that represent the pkgbases in stability layers below those in pkgbases
        """
        self.pkgbases = pkgbases
        self.pkgbases_above = pkgbases_above
        self.pkgbases_below = pkgbases_below

    def __call__(self) -> ActionStateEnum:
        """Check that pkgbases are not newer than pkgbases_above and not older than pkgbases_below.

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS if the check passed successfully,
            ActionStateEnum.FAILED otherwise
        """
        self.state = ActionStateEnum.STARTED

        for pkgbase in self.pkgbases:
            name = pkgbase.base  # type: ignore[attr-defined]
            version = pkgbase.get_version()
            above_versions = [
                pkgbase_above.get_version()
                for pkgbase_above in self.pkgbases_above
                if pkgbase_above.base == pkgbase.base  # type: ignore[attr-defined]
            ]
            for above_version in above_versions:
                if pkg_vercmp(a=version, b=above_version) >= 0:
                    info(
                        f"The version of {name} ({version}) is newer than what is available "
                        f"in a stability layer above: {above_version}"
                    )
                    self.state = ActionStateEnum.FAILED
                    return self.state

            below_versions = [
                pkgbase_below.get_version()
                for pkgbase_below in self.pkgbases_below
                if pkgbase_below.base == pkgbase.base  # type: ignore[attr-defined]
            ]
            for below_version in below_versions:
                if pkg_vercmp(a=version, b=below_version) <= 0:
                    info(
                        f"The version of {name} ({version}) is older than what is available "
                        f"in a stability layer below: {below_version}"
                    )
                    self.state = ActionStateEnum.FAILED
                    return self.state

        self.state = ActionStateEnum.SUCCESS
        return self.state


class ReproducibleBuildEnvironmentCheck(Check):
    """A Check ensuring all build requirements of OutputPackageBases can covered by a set of available requirements.

    Attributes
    ----------
    pkgbases: list[OutputPackageBase]
        A list of OutputPackageBase objects, that represent the pkgbases to be checked
    available_requirements: set[str]
        A set of package information strings (name, version, architecture), which are matched against the build
        requirements of pkgbases
    """

    def __init__(
        self,
        pkgbases: list[OutputPackageBase],
        available_requirements: set[str],
    ) -> None:
        """Initialize an instance of ReproducibleBuildEnvironmentCheck.

        Parameters
        ----------
        pkgbases: list[OutputPackageBase]
            A list of OutputPackageBase objects, that represent the pkgbases to be checked
        available_requirements: set[str]
            A set of package information strings (name, version, architecture), which are matched against the build
            requirements of pkgbases
        """
        self.pkgbases = pkgbases
        self.available_requirements = available_requirements

    def __call__(self) -> ActionStateEnum:
        """Check all build requirements of OutputPackageBases can be met by a set of available requirements.

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS if the check passed successfully,
            ActionStateEnum.FAILED otherwise
        """
        self.state = ActionStateEnum.STARTED

        missing_requirements: dict[str, list[str]] = defaultdict(list)

        for pkgbase in self.pkgbases:
            for requirement in pkgbase.buildinfo.installed:  # type: ignore[attr-defined]
                if requirement not in self.available_requirements:
                    missing_requirements[pkgbase.base].append(requirement)  # type: ignore[attr-defined]

        self.state = ActionStateEnum.SUCCESS
        if missing_requirements:
            self.state = ActionStateEnum.FAILED
            key_value_list = [f"\n{key} => {', '.join(value)}" for key, value in missing_requirements.items()]
            info(
                "The following build requirements can not be met with this transaction, existing packages "
                "in the repositories, or the archive:"
                f"{''.join(key_value_list)}"
            )

        return self.state


class UniqueInRepoGroupCheck(Check):
    """A Check ensuring unique lists of pkgbase and package names among a group of management repository directories.

    Attributes
    ----------
    pkgbase_names: list[str]
        A list of pkgbases to look for in the management repository directories contained in repo_management_dirs
    package_names: list[str]
        A list of packages to look for in the management repository directories contained in repo_management_dirs
    repo_management_dirs: dict[Path, list[Path]]
        A dict describing a repository name and all of its management repository directories
    """

    def __init__(
        self,
        pkgbase_names: list[str],
        package_names: list[str],
        repo_management_dirs: dict[Path, list[Path]],
    ) -> None:
        """Initialize an instance of UniqueInRepoGroupCheck.

        Parameters
        ----------
        pkgbase_names: list[str]
            A list of pkgbases to look for in the management repository directories contained in repo_management_dirs
        package_names: list[str]
            A list of packages to look for in the management repository directories contained in repo_management_dirs
        repo_management_dirs: dict[Path, list[Path]]
            A dict describing a repository name and all of its management repository directories
        """
        self.pkgbase_names = pkgbase_names
        self.package_names = package_names
        self.repo_management_dirs = repo_management_dirs

    def __call__(self) -> ActionStateEnum:
        """Check, that lists of pkgbase and package names are unique among a group of management repository directories.

        Returns
        -------
        ActionStateEnum
            ActionStateEnum.SUCCESS if the check passed successfully,
            ActionStateEnum.FAILED otherwise
        """
        self.state = ActionStateEnum.STARTED

        existing_pkgbases: dict[str, list[str]] = defaultdict(list)
        existing_packages: dict[str, list[str]] = defaultdict(list)

        for repo, management_dirs in self.repo_management_dirs.items():
            for management_dir in management_dirs:
                for pkgbase in self.pkgbase_names:
                    file = management_dir / f"{pkgbase}.json"
                    tmp_file = management_dir / f"{pkgbase}.json.tmp"
                    if file.exists() or tmp_file.exists():
                        existing_pkgbases[str(repo)].append(pkgbase)

                for package in self.package_names:
                    file = management_dir / "pkgnames" / f"{package}.json"
                    tmp_file = management_dir / "pkgnames" / f"{package}.json.tmp"
                    if file.exists() or tmp_file.exists():
                        existing_packages[str(repo)].append(package)

        self.state = ActionStateEnum.SUCCESS
        if existing_pkgbases or existing_packages:
            self.state = ActionStateEnum.FAILED
            pkgbases = [
                f"\nRepository '{key}' already contains the pkgbase(s) {', '.join(value)}."
                for key, value in existing_pkgbases.items()
            ]
            packages = [
                f"\nRepository '{key}' already contains the package(s) {', '.join(value)}."
                for key, value in existing_pkgbases.items()
            ]
            info(
                "Duplicate pkgbases and/ or packages detected in repository group:"
                f"{''.join(pkgbases)}"
                f"{''.join(packages)}"
            )

        return self.state
