from abc import ABCMeta, abstractmethod
from logging import debug, info
from pathlib import Path

from repod.common.enums import ActionStateEnum, ArchitectureEnum, PkgTypeEnum
from repod.files import Package
from repod.files.pkginfo import PkgInfoV2, PkgType
from repod.verification import PacmanKeyVerifier


class Check(metaclass=ABCMeta):
    """An abstract base class to describe a check

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
        """The call method of a Check

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
    """Verify a list of package signatures using pacman-key

    This Check fails if any package can not be verified with its corresponding signature or if any of the
    package/signature lists is not of length two.

    Attributes
    ----------
    packages: list[list[Path]]
        A list of Path lists, that should contain a package and a corresponding signature Path each
    """

    def __init__(self, packages: list[list[Path]]):
        """Initialize an instance of PacmanKeyPackagesSignatureVerificationCheck

        Parameters
        ----------
        package: list[list[Path]]
            A list of lists, containing up to two Paths each
        """

        self.packages = packages

    def __call__(self) -> ActionStateEnum:
        """Use an instance of PacmanKeyVerifier to verify a package and its signature

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
    """A Check to evaluate whether all instances in a list of packages are either debug or not debug packages

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

    def __init__(self, packages: list[Package], debug: bool):
        """Initialize an instance of DebugPackagesCheck

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
        """Check whether all instances of self.packages are supposed to be debug packages or not

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
    """A Check to ensure that a list of packages match a target CPU architecture

    Attributes
    ----------
    architecture: ArchitectureEnum
        An instance of ArchitectureEnum which identifies the target CPU architecture
    packages: list[Package]
        A list of Package instances to check
    """

    def __init__(self, architecture: ArchitectureEnum, packages: list[Package]):
        """Initialize an instance of DebugPackagesCheck

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
        """Check whether all instances of self.packages are supposed to be debug packages or not

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
