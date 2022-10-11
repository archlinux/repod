from copy import deepcopy
from logging import DEBUG
from pathlib import Path
from unittest.mock import patch

from pytest import LogCaptureFixture, mark

from repod.action import check
from repod.common.enums import ActionStateEnum, ArchitectureEnum
from repod.errors import RepoManagementFileError
from repod.files.package import Package
from repod.files.pkginfo import PkgType
from repod.repo.management import OutputPackageBase


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


@mark.parametrize(
    "increase_version, return_value",
    [
        (True, ActionStateEnum.SUCCESS),
        (False, ActionStateEnum.FAILED),
    ],
)
def test_pkgbasesversionupdatecheck(
    increase_version: bool,
    return_value: ActionStateEnum,
    outputpackagebasev1: OutputPackageBase,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    new_outputpackagebase1 = deepcopy(outputpackagebasev1)
    new_outputpackagebase2 = deepcopy(outputpackagebasev1)
    if increase_version:
        new_outputpackagebase1.version = "2:1.0.0-1"  # type: ignore[attr-defined]
        new_outputpackagebase2.version = "2:1.0.0-1"  # type: ignore[attr-defined]
        new_outputpackagebase2.base = "baz"  # type: ignore[attr-defined]

    check_ = check.PkgbasesVersionUpdateCheck(
        new_pkgbases=[new_outputpackagebase1, new_outputpackagebase2],
        current_pkgbases=[outputpackagebasev1],
    )
    assert check_() == return_value


@mark.parametrize(
    "change_new_base, increase_version, create_symlink, from_file_raises, return_value",
    [
        (False, False, True, False, ActionStateEnum.SUCCESS),
        (False, False, False, False, ActionStateEnum.SUCCESS),
        (True, False, False, False, ActionStateEnum.SUCCESS),
        (True, False, True, False, ActionStateEnum.FAILED),
        (True, False, True, True, ActionStateEnum.FAILED),
        (True, True, True, False, ActionStateEnum.FAILED),
    ],
)
def test_packagesneworupdatedcheck(
    change_new_base: bool,
    increase_version: bool,
    create_symlink: bool,
    from_file_raises: bool,
    return_value: ActionStateEnum,
    outputpackagebasev1: OutputPackageBase,
    outputpackagebasev1_json_files_in_dir: Path,
    tmp_path: Path,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    if change_new_base:
        outputpackagebasev1.base = "beh"  # type: ignore[attr-defined]

    if increase_version:
        outputpackagebasev1.version = "2:1.0.0-1"  # type: ignore[attr-defined]

    if create_symlink:
        (outputpackagebasev1_json_files_in_dir / "pkgnames").mkdir()
        for name in ["foo", "bar"]:
            (outputpackagebasev1_json_files_in_dir / "pkgnames" / f"{name}.json").symlink_to("../foo.json")

    check_ = check.PackagesNewOrUpdatedCheck(
        directory=outputpackagebasev1_json_files_in_dir,
        new_pkgbases=[outputpackagebasev1],
        current_pkgbases=[],
    )
    if from_file_raises:
        with patch("repod.action.check.OutputPackageBase.from_file", side_effect=RepoManagementFileError):
            assert check_() == return_value
    else:
        assert check_() == return_value
