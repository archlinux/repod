from contextlib import nullcontext as does_not_raise
from io import StringIO
from logging import DEBUG
from pathlib import Path
from random import sample
from re import Match, fullmatch
from typing import Any, ContextManager, Union
from unittest.mock import patch

from pydantic import ValidationError
from pytest import LogCaptureFixture, mark, raises

from repod.common.enums import FieldTypeEnum, tar_compression_types_for_filename_regex
from repod.errors import RepoManagementError, RepoManagementFileError
from repod.files import pkginfo
from repod.files.common import extract_file_from_tarfile, open_tarfile


@mark.parametrize(
    "line, separator, key, value, field_type, expectation",
    [
        ("# fakeroot 1.0.0", " = ", "fakeroot_version", "1.0.0", FieldTypeEnum.STRING, does_not_raise()),
        ("# makepkg 1.0.0", " = ", "makepkg_version", "1.0.0", FieldTypeEnum.STRING, does_not_raise()),
        ("pkgbase = foo", " = ", "base", "foo", FieldTypeEnum.STRING, does_not_raise()),
        ("foo = bar", " = ", None, None, None, raises(RepoManagementFileError)),
        ("foobar", " = ", None, None, None, raises(RepoManagementFileError)),
    ],
)
def test_parse_pairs(
    line: str,
    separator: str,
    key: str,
    value: Union[int, str, list[str]],
    field_type: FieldTypeEnum,
    expectation: ContextManager[str],
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    with expectation:
        assert (key, value, field_type) == pkginfo.parse_pairs(line=line, separator=separator)


@mark.parametrize(
    "key, value, field_type, input_entries, output_entries, expectation",
    [
        (
            "pkgtype",
            "debug",
            FieldTypeEnum.STRING,
            {"xdata": []},
            {"xdata": [pkginfo.PkgType(pkgtype="debug")]},
            does_not_raise(),
        ),
        (
            "pkgtype",
            "debug",
            FieldTypeEnum.STRING,
            {},
            {"xdata": [pkginfo.PkgType(pkgtype="debug")]},
            does_not_raise(),
        ),
        ("size", "20", FieldTypeEnum.INT, {}, {"size": 20}, does_not_raise()),
        ("name", "foo", FieldTypeEnum.STRING, {}, {"name": "foo"}, does_not_raise()),
        ("license", "foo", FieldTypeEnum.STRING_LIST, {}, {"license": ["foo"]}, does_not_raise()),
        (
            "xdata",
            "pkgtype=debug",
            FieldTypeEnum.KEY_VALUE_LIST,
            {},
            {"xdata": [pkginfo.PkgType(pkgtype="debug")]},
            does_not_raise(),
        ),
    ],
)
def test_pairs_to_entries(
    key: str,
    value: str,
    field_type: FieldTypeEnum,
    input_entries: dict[str, Any],
    output_entries: dict[str, Any],
    expectation: ContextManager[str],
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    with expectation:
        pkginfo.pairs_to_entries(
            key=key,
            value=value,
            field_type=field_type,
            entries=input_entries,
        )
        assert input_entries == output_entries


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
        assert isinstance(pkginfo.PkgInfo.from_file(data=pkginfov2_stringio), pkginfo.PkgInfoV2)

    with patch(
        "repod.files.pkginfo.PKGINFO_VERSIONS",
        pkginfo.PKGINFO_VERSIONS | {len(pkginfo.PKGINFO_VERSIONS) + 1: {"required": {"foo"}}},
    ):
        with raises(RepoManagementError):
            assert isinstance(pkginfo.PkgInfo.from_file(data=pkginfov2_stringio), pkginfo.PkgInfoV2)

    with patch("repod.files.pkginfo.PKGINFO_VERSIONS", {1: pkginfo.PKGINFO_VERSIONS[1]}):
        with does_not_raise():
            assert isinstance(pkginfo.PkgInfo.from_file(data=pkginfov1_stringio), pkginfo.PkgInfoV1)

    with raises(RepoManagementError):
        pkginfo.PkgInfo.from_file(data=StringIO(initial_value="base = foo\n"))


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
                await extract_file_from_tarfile(  # type: ignore[arg-type]
                    tarfile=open_tarfile(package),
                    file=".PKGINFO",
                    as_stringio=True,
                )
            ),
            pkginfo.PkgInfo,
        )
