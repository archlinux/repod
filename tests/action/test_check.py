from logging import DEBUG
from pathlib import Path
from unittest.mock import patch

from pytest import LogCaptureFixture, mark

from repod.action import check
from repod.common.enums import ActionStateEnum, ArchitectureEnum
from repod.files.package import Package
from repod.files.pkginfo import PkgType


@mark.parametrize(
    "with_signature, verifies, return_value",
    [
        (True, True, ActionStateEnum.SUCCESS),
        (True, False, ActionStateEnum.FAILED),
        (False, True, ActionStateEnum.FAILED),
        (False, False, ActionStateEnum.FAILED),
    ],
)
def test_pacmankeypackagessignatureverificationcheck(
    with_signature: bool,
    verifies: bool,
    return_value: ActionStateEnum,
    default_package_file: tuple[Path, ...],
) -> None:
    check_ = check.PacmanKeyPackagesSignatureVerificationCheck(
        packages=[[default_package_file[0], default_package_file[1]]]
        if with_signature
        else [[default_package_file[0]]],
    )
    with patch("repod.action.check.PacmanKeyVerifier.verify", return_value=verifies):
        assert check_() == return_value


@mark.parametrize(
    "debug, package_type, return_value",
    [
        (True, "debug_v2", ActionStateEnum.SUCCESS),
        (True, "default_v1", ActionStateEnum.SUCCESS),
        (True, "default_v2", ActionStateEnum.FAILED),
        (False, "debug_v2", ActionStateEnum.FAILED),
        (False, "default_v1", ActionStateEnum.SUCCESS),
        (False, "default_v2", ActionStateEnum.SUCCESS),
    ],
)
def test_debugpackagescheck(
    debug: bool,
    package_type: str,
    return_value: ActionStateEnum,
    packagev1: Package,
    packagev1_pkginfov2: Package,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    match package_type:
        case "default_v1":
            packagev1_pkginfov2.pkginfo.xdata = []  # type: ignore[attr-defined]
            packages = [packagev1]
        case "default_v2":
            packagev1_pkginfov2.pkginfo.xdata = [PkgType(pkgtype="pkg")]  # type: ignore[attr-defined]
            packages = [packagev1_pkginfov2]
        case "debug_v2":
            packagev1_pkginfov2.pkginfo.xdata = [PkgType(pkgtype="debug")]  # type: ignore[attr-defined]
            packages = [packagev1_pkginfov2]
    print(packages)

    check_ = check.DebugPackagesCheck(
        debug=debug,
        packages=packages,
    )

    assert check_() == return_value


@mark.parametrize(
    "matching_arch, return_value",
    [
        (True, ActionStateEnum.SUCCESS),
        (False, ActionStateEnum.FAILED),
    ],
)
def test_matchingarchitecturecheck(
    matching_arch: bool,
    return_value: ActionStateEnum,
    packagev1: Package,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    if matching_arch:
        architecture = ArchitectureEnum(packagev1.pkginfo.arch)  # type: ignore[attr-defined]
    else:
        architecture = ArchitectureEnum.ANY

    check_ = check.MatchingArchitectureCheck(architecture=architecture, packages=[packagev1])
    assert check_() == return_value
