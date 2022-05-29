from contextlib import nullcontext as does_not_raise
from io import StringIO
from pathlib import Path
from random import sample
from tempfile import TemporaryDirectory
from typing import ContextManager
from unittest.mock import patch

from pydantic import ValidationError
from pytest import mark, raises

from repod.errors import (
    RepoManagementError,
    RepoManagementFileError,
    RepoManagementFileNotFoundError,
)
from repod.files import buildinfo
from repod.files.common import extract_file_from_tarfile, open_tarfile


@mark.parametrize(
    "number, expectation",
    [
        (0, does_not_raise()),
        (1, does_not_raise()),
        (-1, raises(ValidationError)),
    ],
)
def test_builddate(number: int, expectation: ContextManager[str]) -> None:
    with expectation:
        buildinfo.BuildDate(builddate=number)


def test_builddir(absolute_dir: str, invalid_absolute_dir: str) -> None:
    with does_not_raise():
        buildinfo.BuildDir(builddir=absolute_dir)
    with raises(ValidationError):
        buildinfo.BuildDir(builddir=invalid_absolute_dir)


def test_buildenv(buildenv: str, invalid_buildenv: str) -> None:
    with does_not_raise():
        buildinfo.BuildEnv(buildenv=[buildenv])
    with raises(ValidationError):
        buildinfo.BuildEnv(buildenv=[invalid_buildenv])


def test_buildtool(package_name: str, invalid_package_name: str) -> None:
    with does_not_raise():
        buildinfo.BuildTool(buildtool=package_name)
    with raises(ValidationError):
        buildinfo.BuildTool(buildtool=invalid_package_name)


def test_buildtoolver() -> None:
    assert buildinfo.BuildToolVer(buildtoolver="foo")


@mark.parametrize(
    "format_, expectation",
    [
        (1, does_not_raise()),
        (0, raises(ValidationError)),
        (2, raises(ValidationError)),
    ],
)
def test_formatv1(format_: int, expectation: ContextManager[str]) -> None:
    with expectation:
        buildinfo.FormatV1(format_=format_)


@mark.parametrize(
    "format_, expectation",
    [
        (2, does_not_raise()),
        (1, raises(ValidationError)),
        (3, raises(ValidationError)),
    ],
)
def test_formatv2(format_: int, expectation: ContextManager[str]) -> None:
    with expectation:
        buildinfo.FormatV2(format_=format_)


def test_installed(package_name: str, epoch_version_pkgrel: str, arch: str) -> None:
    with does_not_raise():
        buildinfo.Installed(installed=[f"{package_name}-{epoch_version_pkgrel}-{arch}"])


def test_invalid_installed(
    invalid_package_name: str,
    invalid_epoch_version_pkgrel: str,
) -> None:
    with raises(ValidationError):
        buildinfo.Installed(installed=[f"{invalid_package_name}-{invalid_epoch_version_pkgrel}-foo"])


def test_options(option: str, invalid_option: str) -> None:
    with does_not_raise():
        buildinfo.Options(options=[option])
    with raises(ValidationError):
        buildinfo.Options(options=[invalid_option])


def test_packager(packager_name: str, email: str) -> None:
    with does_not_raise():
        buildinfo.Packager(packager=f"{packager_name} <{email}>")


def test_invalid_packager(invalid_packager_name: str, invalid_email: str) -> None:
    with raises(ValidationError):
        buildinfo.Packager(packager=f"{invalid_packager_name} <{invalid_email}>")


def test_pkgarch(arch: str) -> None:
    with does_not_raise():
        buildinfo.PkgArch(pkgarch=arch)
    with raises(ValidationError):
        buildinfo.PkgArch(pkgarch="foo")


def test_pkgbase(package_name: str, invalid_package_name: str) -> None:
    with does_not_raise():
        buildinfo.PkgBase(pkgbase=package_name)
    with raises(ValidationError):
        buildinfo.PkgBase(pkgbase=invalid_package_name)


def test_pkgbuildsha256sum(sha256sum: str) -> None:
    with does_not_raise():
        buildinfo.PkgBuildSha256Sum(pkgbuild_sha256sum=sha256sum)
    with raises(ValidationError):
        buildinfo.PkgBuildSha256Sum(pkgbuild_sha256sum="f00")


def test_pkgname(package_name: str, invalid_package_name: str) -> None:
    with does_not_raise():
        buildinfo.PkgName(pkgname=package_name)
    with raises(ValidationError):
        buildinfo.PkgName(pkgname=invalid_package_name)


def test_pkgver(epoch_version_pkgrel: str, invalid_epoch_version_pkgrel: str) -> None:
    with does_not_raise():
        buildinfo.PkgVer(pkgver=epoch_version_pkgrel)
    with raises(ValidationError):
        buildinfo.PkgVer(pkgver=invalid_epoch_version_pkgrel)


def test_startdir(absolute_dir: str, invalid_absolute_dir: str) -> None:
    with does_not_raise():
        buildinfo.StartDir(startdir=absolute_dir)
    with raises(ValidationError):
        buildinfo.StartDir(startdir=invalid_absolute_dir)


def test_buildinfo_from_file(
    buildinfov1_stringio: StringIO,
    buildinfov2_stringio: StringIO,
) -> None:
    with does_not_raise():
        assert isinstance(buildinfo.BuildInfo.from_file(data=buildinfov1_stringio), buildinfo.BuildInfoV1)
        assert isinstance(buildinfo.BuildInfo.from_file(data=buildinfov2_stringio), buildinfo.BuildInfoV2)

    with raises(RepoManagementError):
        buildinfo.BuildInfo.from_file(data=StringIO(initial_value="foo = bar\n"))


@mark.parametrize(
    "file_is, raises_os_error, expectation",
    [
        ("file", False, does_not_raise()),
        ("file", True, raises(RepoManagementFileError)),
        ("missing", False, raises(RepoManagementFileNotFoundError)),
        ("missing", True, raises(RepoManagementFileNotFoundError)),
        ("bytesio", False, does_not_raise()),
    ],
)
def test_read_buildinfo(
    file_is: str,
    raises_os_error: bool,
    expectation: ContextManager[str],
    valid_buildinfov1_file: Path,
    valid_buildinfov2_file: Path,
) -> None:
    with expectation:
        match file_is:
            case "file":
                for buildinfo_path in [valid_buildinfov1_file, valid_buildinfov2_file]:
                    if raises_os_error:
                        with patch("builtins.open") as open_mock:
                            open_mock.side_effect = OSError
                            buildinfo.read_buildinfo(buildinfo=buildinfo_path)
                    else:
                        buildinfo.read_buildinfo(buildinfo=buildinfo_path)
            case "bytesio":
                for buildinfo_path in [valid_buildinfov1_file, valid_buildinfov2_file]:
                    with open(buildinfo_path, "rb") as buildinfo_file:
                        buildinfo.read_buildinfo(buildinfo=buildinfo_file)
            case "missing":
                buildinfo.read_buildinfo(buildinfo=Path("/foo"))


def test_buildinfov2_validate_devtools_version(sha256sum: str, invalid_epoch_version_pkgrel: str) -> None:
    with raises(ValidationError):
        buildinfo.BuildInfoV2(
            builddate=1,
            builddir="/foo",
            buildenv=[],
            buildtool="devtools",
            buildtoolver=f"{invalid_epoch_version_pkgrel}-any",
            installed=[],
            options=[],
            packager="Foobar McFooface <foobar@mcfooface.tld>",
            pkgarch="any",
            pkgbase="foo",
            pkgbuild_sha256sum=sha256sum,
            pkgname="foo",
            pkgver="1.0.0-1",
            startdir="/bar",
        )


def test_export_schemas() -> None:
    with TemporaryDirectory() as tmp:
        buildinfo.export_schemas(output=str(tmp))
        buildinfo.export_schemas(output=tmp)

    with raises(RuntimeError):
        buildinfo.export_schemas(output="/foobar")

    with raises(RuntimeError):
        buildinfo.export_schemas(output=Path("/foobar"))


@mark.integration
@mark.skipif(
    not Path("/var/cache/pacman/pkg/").exists(),
    reason="Package cache in /var/cache/pacman/pkg/ does not exist",
)
async def test_read_buildinfo_files() -> None:
    packages = sorted(Path("/var/cache/pacman/pkg/").glob("*.zst"))
    if len(packages) > 50:
        packages = sample(packages, 50)
    for package in packages:
        print(f"DEBUG::: Reading .BUILDINFO file from package {package}...")
        assert isinstance(
            buildinfo.BuildInfo.from_file(
                data=buildinfo.read_buildinfo(
                    await extract_file_from_tarfile(
                        tarfile=open_tarfile(package),
                        file=".BUILDINFO",
                    )
                )
            ),
            buildinfo.BuildInfo,
        )
