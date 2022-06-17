from contextlib import nullcontext as does_not_raise
from io import StringIO
from pathlib import Path
from random import sample
from re import Match, fullmatch
from tempfile import TemporaryDirectory
from typing import ContextManager

from pydantic import ValidationError
from pytest import mark, raises

from repod.common.enums import tar_compression_types_for_filename_regex
from repod.errors import RepoManagementError
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


def test_buildenv(default_buildenv: str, default_invalid_buildenv: str) -> None:
    with does_not_raise():
        buildinfo.BuildEnv(buildenv=[default_buildenv])
    with raises(ValidationError):
        buildinfo.BuildEnv(buildenv=[default_invalid_buildenv])


def test_buildtool(default_package_name: str, default_invalid_package_name: str) -> None:
    with does_not_raise():
        buildinfo.BuildTool(buildtool=default_package_name)
    with raises(ValidationError):
        buildinfo.BuildTool(buildtool=default_invalid_package_name)


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


def test_installed(default_package_name: str, default_full_version: str, default_arch: str) -> None:
    with does_not_raise():
        buildinfo.Installed(installed=[f"{default_package_name}-{default_full_version}-{default_arch}"])


def test_invalid_installed(
    default_invalid_package_name: str,
    default_invalid_full_version: str,
) -> None:
    with raises(ValidationError):
        buildinfo.Installed(installed=[f"{default_invalid_package_name}-{default_invalid_full_version}-foo"])


def test_options(default_option: str, default_invalid_option: str) -> None:
    with does_not_raise():
        buildinfo.Options(options=[default_option])
    with raises(ValidationError):
        buildinfo.Options(options=[default_invalid_option])


def test_packager(default_packager: str) -> None:
    with does_not_raise():
        buildinfo.Packager(packager=default_packager)


def test_invalid_packager(default_invalid_packager: str) -> None:
    with raises(ValidationError):
        buildinfo.Packager(packager=default_invalid_packager)


def test_pkgarch(default_arch: str) -> None:
    with does_not_raise():
        buildinfo.PkgArch(pkgarch=default_arch)
    with raises(ValidationError):
        buildinfo.PkgArch(pkgarch="foo")


def test_pkgbase(default_package_name: str, default_invalid_package_name: str) -> None:
    with does_not_raise():
        buildinfo.PkgBase(pkgbase=default_package_name)
    with raises(ValidationError):
        buildinfo.PkgBase(pkgbase=default_invalid_package_name)


def test_pkgbuildsha256sum(sha256sum: str) -> None:
    with does_not_raise():
        buildinfo.PkgBuildSha256Sum(pkgbuild_sha256sum=sha256sum)
    with raises(ValidationError):
        buildinfo.PkgBuildSha256Sum(pkgbuild_sha256sum="f00")


def test_pkgname(default_package_name: str, default_invalid_package_name: str) -> None:
    with does_not_raise():
        buildinfo.PkgName(pkgname=default_package_name)
    with raises(ValidationError):
        buildinfo.PkgName(pkgname=default_invalid_package_name)


def test_pkgver(default_full_version: str, default_invalid_full_version: str) -> None:
    with does_not_raise():
        buildinfo.PkgVer(pkgver=default_full_version)
    with raises(ValidationError):
        buildinfo.PkgVer(pkgver=default_invalid_full_version)


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


def test_buildinfov2_validate_devtools_version(
    default_full_version: str,
    default_invalid_full_version: str,
    default_packager: str,
    sha256sum: str,
) -> None:
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
        assert isinstance(
            buildinfo.BuildInfo.from_file(
                await extract_file_from_tarfile(  # type: ignore[arg-type]
                    tarfile=open_tarfile(package),
                    file=".BUILDINFO",
                    as_stringio=True,
                )
            ),
            buildinfo.BuildInfo,
        )
