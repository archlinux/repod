from abc import ABCMeta, abstractmethod
from logging import debug, info
from pathlib import Path
from typing import List

from repod.common.enums import ActionStateEnum, PkgTypeEnum
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
    packages: List[List[Path]]
        A list of Path lists, that should contain a package and a corresponding signature Path each
    """

    def __init__(self, packages: List[List[Path]]):
        """Initialize an instance of PacmanKeyPackagesSignatureVerificationCheck

        Parameters
        ----------
        package: List[List[Path]]
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
    packages: List[Package]
        A list of Package instances to check
    debug: bool
        A boolean value indicating whether all Package instances should be debug packages or not
    """

    def __init__(self, packages: List[Package], debug: bool):
        """Initialize an instance of DebugPackagesCheck

        Parameters
        ----------
        packages: List[Package]
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
