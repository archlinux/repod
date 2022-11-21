from copy import deepcopy
from logging import DEBUG
from pathlib import Path
from shutil import rmtree
from unittest.mock import patch

from pydantic import AnyUrl
from pydantic.tools import parse_obj_as
from pytest import LogCaptureFixture, mark

from repod.action import check
from repod.common.enums import ActionStateEnum, ArchitectureEnum
from repod.config.settings import UrlValidationSettings
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
    "package_arch, repo_arch, return_value",
    [
        (ArchitectureEnum.AARCH64, ArchitectureEnum.AARCH64, ActionStateEnum.SUCCESS),
        (ArchitectureEnum.ANY, ArchitectureEnum.AARCH64, ActionStateEnum.SUCCESS),
        (ArchitectureEnum.ANY, ArchitectureEnum.ANY, ActionStateEnum.SUCCESS),
        (ArchitectureEnum.AARCH64, ArchitectureEnum.ANY, ActionStateEnum.FAILED),
        (ArchitectureEnum.AARCH64, ArchitectureEnum.X86_64, ActionStateEnum.FAILED),
    ],
)
def test_matchingarchitecturecheck(
    package_arch: ArchitectureEnum,
    repo_arch: ArchitectureEnum,
    return_value: ActionStateEnum,
    packagev1: Package,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    packagev1.pkginfo.arch = package_arch.value  # type: ignore[attr-defined]
    check_ = check.MatchingArchitectureCheck(architecture=repo_arch, packages=[packagev1])
    assert check_() == return_value


@mark.parametrize(
    "filename, arch, name, version, return_value",
    [
        ("foo-1:1.0.0-1-any.pkg.tar.zst", "any", "foo", "1:1.0.0-1", ActionStateEnum.SUCCESS),
        ("foo-1:1.0.0-1-any.pkg.tar.zst", "x86_64", "foo", "1:1.0.0-1", ActionStateEnum.FAILED),
        ("foo-1:1.0.0-1-any.pkg.tar.zst", "any", "bar", "1:1.0.0-1", ActionStateEnum.FAILED),
        ("foo-1:1.0.0-1-any.pkg.tar.zst", "any", "foo", "2:1.0.0-1", ActionStateEnum.FAILED),
        ("foo-1:1.0.0-1-any.pkg.tar.zst", "any", "foo", "1:2.0.0-1", ActionStateEnum.FAILED),
        ("foo-1:1.0.0-1-any.pkg.tar.zst", "any", "foo", "1:1.0.2-1", ActionStateEnum.FAILED),
        ("foo-1:1.0.0-1-any.pkg.tar.zst", "any", "foo", "1:1.0.0-2", ActionStateEnum.FAILED),
    ],
)
def test_matchingfilenamecheck(
    filename: str,
    name: str,
    version: str,
    arch: str,
    return_value: ActionStateEnum,
    packagev1: Package,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    packagev1.filename = filename  # type: ignore[attr-defined]
    packagev1.pkginfo.name = name  # type: ignore[attr-defined]
    packagev1.pkginfo.version = version  # type: ignore[attr-defined]
    packagev1.pkginfo.arch = arch  # type: ignore[attr-defined]
    check_ = check.MatchingFilenameCheck(packages_and_paths=[(packagev1, Path(filename))])
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

    if not create_symlink:
        rmtree(outputpackagebasev1_json_files_in_dir / "pkgnames")

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


@mark.parametrize(
    "require_validation, new_pkgbase_provides_url, current_pkgbase_provides_url, url_matches, return_value",
    [
        (False, True, True, True, ActionStateEnum.SUCCESS),
        (False, False, False, False, ActionStateEnum.SUCCESS),
        (True, True, False, True, ActionStateEnum.SUCCESS),
        (True, False, True, True, ActionStateEnum.SUCCESS),
        (True, False, False, True, ActionStateEnum.FAILED),
        (True, False, False, True, ActionStateEnum.FAILED),
        (True, True, False, False, ActionStateEnum.FAILED),
        (True, False, True, False, ActionStateEnum.FAILED),
    ],
)
def test_sourceurlcheck(
    require_validation: bool,
    new_pkgbase_provides_url: bool,
    current_pkgbase_provides_url: bool,
    url_matches: bool,
    return_value: ActionStateEnum,
    outputpackagebasev1: OutputPackageBase,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    new_pkgbase = outputpackagebasev1
    current_pkgbase = deepcopy(new_pkgbase)
    if new_pkgbase_provides_url:
        new_pkgbase.source_url = parse_obj_as(AnyUrl, "https://foobar.com/foo/bar")  # type: ignore[attr-defined]
    if current_pkgbase_provides_url:
        current_pkgbase.source_url = parse_obj_as(AnyUrl, "https://foobar.com/foo/bar")  # type: ignore[attr-defined]

    check_ = check.SourceUrlCheck(
        new_pkgbases=[new_pkgbase],
        current_pkgbases=[current_pkgbase],
        url_validation_settings=UrlValidationSettings(
            urls=["https://foobar.com/foo/"] if url_matches else ["https://beh.com/foo/"],
            tls_required=True,
        )
        if require_validation
        else None,
    )

    assert check_() == return_value


@mark.parametrize(
    "pkgbase_version, pkgbase_above_version, pkgbase_below_version, return_value",
    [
        ("1.0.0-1", None, None, ActionStateEnum.SUCCESS),
        ("1.0.0-1", "2.0.0-1", None, ActionStateEnum.SUCCESS),
        ("1.0.0-1", "2.0.0-1", "0.0.1-1", ActionStateEnum.SUCCESS),
        ("1.0.0-1", None, "0.0.1-1", ActionStateEnum.SUCCESS),
        ("1.0.0-1", "0.0.1-1", None, ActionStateEnum.FAILED),
        ("1.0.0-1", None, "2.0.0-1", ActionStateEnum.FAILED),
    ],
)
def test_stabilitylayercheck(
    pkgbase_version: str,
    pkgbase_above_version: str,
    pkgbase_below_version: str,
    return_value: ActionStateEnum,
    outputpackagebasev1: OutputPackageBase,
) -> None:

    pkgbases = []
    pkgbases_above = []
    pkgbases_below = []

    pkgbase = outputpackagebasev1
    pkgbase.version = pkgbase_version  # type: ignore[attr-defined]
    pkgbases.append(pkgbase)

    if pkgbase_above_version is not None:
        pkgbase_above = deepcopy(pkgbase)
        pkgbase_above.version = pkgbase_above_version  # type: ignore[attr-defined]
        pkgbases_above.append(pkgbase_above)

    if pkgbase_below_version is not None:
        pkgbase_below = deepcopy(pkgbase)
        pkgbase_below.version = pkgbase_below_version  # type: ignore[attr-defined]
        pkgbases_below.append(pkgbase_below)

    check_ = check.StabilityLayerCheck(
        pkgbases=pkgbases,
        pkgbases_above=pkgbases_above,
        pkgbases_below=pkgbases_below,
    )
    assert check_() == return_value


@mark.parametrize(
    "in_available_requirements, return_value",
    [
        (True, ActionStateEnum.SUCCESS),
        (False, ActionStateEnum.FAILED),
    ],
)
def test_reproduciblebuildenvironmentcheck(
    in_available_requirements: bool,
    return_value: ActionStateEnum,
    outputpackagebasev1: OutputPackageBase,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    check_ = check.ReproducibleBuildEnvironmentCheck(
        pkgbases=[outputpackagebasev1],
        available_requirements=set(outputpackagebasev1.buildinfo.installed)  # type: ignore[attr-defined]
        if in_available_requirements
        else {},
    )
    assert check_() == return_value
