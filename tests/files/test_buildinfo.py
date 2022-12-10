"""Tests for repod.files.buildinfo."""
from contextlib import nullcontext as does_not_raise
from io import StringIO
from pathlib import Path
from random import sample
from re import Match, fullmatch
from tempfile import TemporaryDirectory
from typing import ContextManager

from pydantic import ValidationError
from pytest import mark, raises

from repod.common.enums import (
    ArchitectureEnum,
    tar_compression_types_for_filename_regex,
)
from repod.errors import RepoManagementError
from repod.files import buildinfo
from repod.files.common import extract_file_from_tarfile, open_tarfile
from tests.conftest import (
    create_default_arch,
    create_default_full_version,
    create_default_invalid_full_version,
    create_default_invalid_package_name,
    create_default_package_name,
)


@mark.parametrize(
    "number, expectation",
    [
        (0, does_not_raise()),
        (1, does_not_raise()),
        (-1, raises(ValidationError)),
    ],
)
def test_builddate(number: int, expectation: ContextManager[str]) -> None:
    """Tests for repod.files.buildinfo.BuildDate."""
    with expectation:
        buildinfo.BuildDate(builddate=number)


@mark.parametrize(
    "path, expectation",
    [
        ("/", does_not_raise()),
        ("/foo", does_not_raise()),
        ("foo", raises(ValidationError)),
        ("", raises(ValidationError)),
    ],
)
def test_builddir(
    path: str,
    expectation: ContextManager[str],
) -> None:
    """Tests for repod.files.buildinfo.BuildDir."""
    with expectation:
        buildinfo.BuildDir(builddir=path)


def test_buildenv(default_buildenv: str, default_invalid_buildenv: str) -> None:
    """Tests for repod.files.buildinfo.BuildEnv."""
    with does_not_raise():
        buildinfo.BuildEnv(buildenv=[default_buildenv])
    with raises(ValidationError):
        buildinfo.BuildEnv(buildenv=[default_invalid_buildenv])


def test_buildtool(default_package_name: str, default_invalid_package_name: str) -> None:
    """Tests for repod.files.buildinfo.BuildTool."""
    with does_not_raise():
        buildinfo.BuildTool(buildtool=default_package_name)
    with raises(ValidationError):
        buildinfo.BuildTool(buildtool=default_invalid_package_name)


def test_buildtoolver() -> None:
    """Tests for repod.files.buildinfo.BuildToolVer."""
    assert buildinfo.BuildToolVer(buildtoolver="foo")  # nosec: B101


@mark.parametrize(
    "installed, expectation",
    [
        (
            [f"{create_default_package_name()}-{create_default_full_version()}-{create_default_arch()}"],
            does_not_raise(),
        ),
        (
            [f"{create_default_invalid_package_name()}-{create_default_invalid_full_version()}-foo"],
            raises(ValidationError),
        ),
    ],
)
def test_installed(installed: list[str], expectation: ContextManager[str]) -> None:
    """Tests for repod.files.buildinfo.Installed."""
    with expectation:
        buildinfo.Installed(installed=installed)


def test_installed_as_models(
    default_arch: str,
    default_full_version: str,
    default_package_name: str,
) -> None:
    """Tests for repod.files.buildinfo.Installed.as_models."""
    assert [  # nosec: B101
        (
            buildinfo.PkgName(pkgname=default_package_name),
            buildinfo.PkgVer(pkgver=default_full_version),
            ArchitectureEnum(default_arch),
        )
    ] == buildinfo.Installed.as_models(installed=[f"{default_package_name}-{default_full_version}-{default_arch}"])


def test_options(default_option: str, default_invalid_option: str) -> None:
    """Tests for repod.files.buildinfo.Options."""
    with does_not_raise():
        buildinfo.Options(options=[default_option])
    with raises(ValidationError):
        buildinfo.Options(options=[default_invalid_option])


def test_packager(default_packager: str) -> None:
    """Tests for repod.files.buildinfo.Packager."""
    with does_not_raise():
        buildinfo.Packager(packager=default_packager)


def test_invalid_packager(default_invalid_packager: str) -> None:
    """Tests for repod.files.buildinfo.Packager."""
    with raises(ValidationError):
        buildinfo.Packager(packager=default_invalid_packager)


def test_pkgarch(default_arch: str) -> None:
    """Tests for repod.files.buildinfo.PkgArch."""
    with does_not_raise():
        buildinfo.PkgArch(pkgarch=default_arch)
    with raises(ValidationError):
        buildinfo.PkgArch(pkgarch="foo")


def test_pkgbase(default_package_name: str, default_invalid_package_name: str) -> None:
    """Tests for repod.files.buildinfo.PkgBase."""
    with does_not_raise():
        buildinfo.PkgBase(pkgbase=default_package_name)
    with raises(ValidationError):
        buildinfo.PkgBase(pkgbase=default_invalid_package_name)


def test_pkgbuildsha256sum(sha256sum: str) -> None:
    """Tests for repod.files.buildinfo.PkgBuildSha256Sum."""
    with does_not_raise():
        buildinfo.PkgBuildSha256Sum(pkgbuild_sha256sum=sha256sum)
    with raises(ValidationError):
        buildinfo.PkgBuildSha256Sum(pkgbuild_sha256sum="f00")


def test_pkgname(default_package_name: str, default_invalid_package_name: str) -> None:
    """Tests for repod.files.buildinfo.PkgName."""
    with does_not_raise():
        buildinfo.PkgName(pkgname=default_package_name)
    with raises(ValidationError):
        buildinfo.PkgName(pkgname=default_invalid_package_name)


def test_pkgver(default_full_version: str, default_invalid_full_version: str) -> None:
    """Tests for repod.files.buildinfo.PkgVer."""
    with does_not_raise():
        buildinfo.PkgVer(pkgver=default_full_version)
    with raises(ValidationError):
        buildinfo.PkgVer(pkgver=default_invalid_full_version)


@mark.parametrize(
    "path, expectation",
    [
        ("/", does_not_raise()),
        ("/foo", does_not_raise()),
        ("foo", raises(ValidationError)),
        ("", raises(ValidationError)),
    ],
)
def test_startdir(path: str, expectation: ContextManager[str]) -> None:
    """Tests for invalid repod.files.buildinfo.StartDir."""
    with expectation:
        buildinfo.StartDir(startdir=path)


def test_buildinfo_from_file(
    buildinfov1_stringio: StringIO,
    buildinfov2_stringio: StringIO,
) -> None:
    """Tests for repod.files.buildinfo.BuildInfo.from_file."""
    with does_not_raise():
        assert isinstance(  # nosec: B101
            buildinfo.BuildInfo.from_file(data=buildinfov1_stringio), buildinfo.BuildInfoV1
        )
        assert isinstance(  # nosec: B101
            buildinfo.BuildInfo.from_file(data=buildinfov2_stringio), buildinfo.BuildInfoV2
        )

    with raises(RepoManagementError):
        buildinfo.BuildInfo.from_file(data=StringIO(initial_value="foo = bar\n"))


def test_buildinfov2_validate_devtools_version(
    default_full_version: str,
    default_invalid_full_version: str,
    default_packager: str,
    sha256sum: str,
) -> None:
    """Tests for repod.files.buildinfo.BuildInfoV2.validate_devtools_version."""
    with raises(ValidationError):
        buildinfo.BuildInfoV2(
            builddate=1,
            builddir="/foo",
            buildenv=[],
            buildtool="devtools",
            buildtoolver=f"{default_invalid_full_version}-any",
            installed=[],
            options=[],
            packager=default_packager,
            pkgarch="any",
            pkgbase="foo",
            pkgbuild_sha256sum=sha256sum,
            pkgname="foo",
            pkgver=default_full_version,
            startdir="/bar",
        )


def test_export_schemas() -> None:
    """Tests for repod.files.buildinfo.export_schemas."""
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
    """Integration tests for repod.files.buildinfo.BuildInfo.from_file."""
    packages = sorted(
        [
            path
            for path in list(Path("/var/cache/pacman/pkg/").iterdir())
            if isinstance(fullmatch(rf"^.*\.pkg\.tar({tar_compression_types_for_filename_regex()})$", str(path)), Match)
        ]
    )
    if len(packages) > 50:
        packages = sample(packages, 50)
    for package in packages:
        print(f"DEBUG::: Reading .BUILDINFO file from package {package}...")
        assert isinstance(  # nosec: B101
            buildinfo.BuildInfo.from_file(
                await extract_file_from_tarfile(  # type: ignore[arg-type]
                    tarfile=open_tarfile(package),
                    file=".BUILDINFO",
                    as_stringio=True,
                )
            ),
            buildinfo.BuildInfo,
        )
