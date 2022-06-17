from contextlib import nullcontext as does_not_raise
from io import StringIO
from logging import DEBUG
from pathlib import Path
from random import sample
from re import Match, fullmatch
from typing import ContextManager
from unittest.mock import patch

from pydantic import ValidationError
from pytest import LogCaptureFixture, mark, raises

from repod.common.enums import tar_compression_types_for_filename_regex
from repod.errors import (
    RepoManagementError,
    RepoManagementFileError,
    RepoManagementFileNotFoundError,
)
from repod.files import pkginfo
from repod.files.common import extract_file_from_tarfile, open_tarfile


def test_fakerootversion(default_version: str, default_invalid_version: str) -> None:
    with does_not_raise():
        pkginfo.FakerootVersion(fakeroot_version=default_version)
    with raises(ValidationError):
        pkginfo.FakerootVersion(fakeroot_version=default_invalid_version)


def test_makepkgversion(default_version: str, default_invalid_version: str) -> None:
    with does_not_raise():
        pkginfo.MakepkgVersion(makepkg_version=default_version)
    with raises(ValidationError):
        pkginfo.MakepkgVersion(makepkg_version=default_invalid_version)


def test_pkgtype(default_pkgtype: str, default_invalid_pkgtype: str) -> None:
    with does_not_raise():
        pkginfo.PkgType(pkgtype=default_pkgtype)
    with raises(ValidationError):
        pkginfo.PkgType(pkgtype=default_invalid_pkgtype)


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
def test_read_pkginfo(
    file_is: str,
    raises_os_error: bool,
    expectation: ContextManager[str],
    valid_pkginfov1_file: Path,
    valid_pkginfov2_file: Path,
) -> None:
    with expectation:
        match file_is:
            case "file":
                for pkginfo_path in [valid_pkginfov1_file, valid_pkginfov2_file]:
                    if raises_os_error:
                        with patch("builtins.open") as open_mock:
                            open_mock.side_effect = OSError
                            pkginfo.read_pkginfo(pkginfo=pkginfo_path)
                    else:
                        pkginfo.read_pkginfo(pkginfo=pkginfo_path)
            case "bytesio":
                for pkginfo_path in [valid_pkginfov1_file, valid_pkginfov2_file]:
                    with open(pkginfo_path, "rb") as pkginfo_file:
                        pkginfo.read_pkginfo(pkginfo=pkginfo_file)
            case "missing":
                pkginfo.read_pkginfo(pkginfo=Path("/foo"))


def test_export_schemas(tmp_path: Path) -> None:
    pkginfo.export_schemas(output=str(tmp_path))
    pkginfo.export_schemas(output=tmp_path)

    with raises(RuntimeError):
        pkginfo.export_schemas(output="/foobar")

    with raises(RuntimeError):
        pkginfo.export_schemas(output=Path("/foobar"))


def test_pkginfo_from_file(
    caplog: LogCaptureFixture,
    pkginfov1_stringio: StringIO,
    pkginfov2_stringio: StringIO,
) -> None:
    caplog.set_level(DEBUG)
    with does_not_raise():
        assert isinstance(pkginfo.PkgInfo.from_file(data=pkginfov1_stringio), pkginfo.PkgInfoV1)
        assert isinstance(pkginfo.PkgInfo.from_file(data=pkginfov2_stringio), pkginfo.PkgInfoV2)

    with raises(RepoManagementError):
        pkginfo.PkgInfo.from_file(data=StringIO(initial_value="foo = bar\n"))

    with raises(RepoManagementError):
        pkginfo.PkgInfo.from_file(data=StringIO(initial_value="foo = bar = baz\n"))

    with raises(RepoManagementError):
        pkginfo.PkgInfo.from_file(data=StringIO(initial_value=" \n"))


@mark.integration
@mark.skipif(
    not Path("/var/cache/pacman/pkg/").exists(),
    reason="Package cache in /var/cache/pacman/pkg/ does not exist",
)
async def test_read_pkginfo_files() -> None:
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
        print(f"DEBUG::: Reading .PKGINFO file from package {package}...")
        assert isinstance(
            pkginfo.PkgInfo.from_file(
                data=pkginfo.read_pkginfo(
                    await extract_file_from_tarfile(
                        tarfile=open_tarfile(package),
                        file=".PKGINFO",
                    )
                )
            ),
            pkginfo.PkgInfo,
        )
