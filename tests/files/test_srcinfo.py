from contextlib import nullcontext as does_not_raise
from io import StringIO
from logging import DEBUG
from pathlib import Path
from typing import ContextManager

from pytest import LogCaptureFixture, mark, raises

from repod.common.enums import FieldTypeEnum
from repod.errors import FileParserError
from repod.files import srcinfo


@mark.parametrize(
    "from_file, split_pkg, dupe_pkgbase, pkgname_first, body_first, pkgname_missing, expectation",
    [
        (True, True, False, False, False, False, does_not_raise()),
        (True, False, False, False, False, False, does_not_raise()),
        (False, True, False, False, False, False, does_not_raise()),
        (False, False, False, False, False, False, does_not_raise()),
        (False, False, True, False, False, False, raises(FileParserError)),
        (False, False, False, True, False, False, raises(FileParserError)),
        (False, False, False, False, True, False, raises(FileParserError)),
        (False, False, False, False, False, True, raises(FileParserError)),
    ],
)
def test_srcinfo_from_file(
    from_file: bool,
    split_pkg: bool,
    dupe_pkgbase: bool,
    pkgname_first: bool,
    body_first: bool,
    pkgname_missing: bool,
    expectation: ContextManager[str],
    srcinfov1_single_stringio: StringIO,
    srcinfov1_split_stringio: StringIO,
    srcinfov1_single_file: Path,
    srcinfov1_split_file: Path,
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    data: Path | StringIO

    match from_file, split_pkg:
        case True, True:
            data = srcinfov1_split_file
        case True, False:
            data = srcinfov1_single_file
        case False, True:
            data = srcinfov1_split_stringio
        case False, False:
            data = srcinfov1_single_stringio

    if dupe_pkgbase:
        data = StringIO(initial_value="pkgbase = foo\npkgbase = bar")

    if pkgname_first:
        data = StringIO(initial_value="pkgname = foo\npkgbase = bar")

    if body_first:
        data = StringIO(initial_value="arch = foo\npkgbase = bar")

    if pkgname_missing:
        data = StringIO(
            initial_value=(
                "pkgbase = bar\n"
                "arch = x86_64\n"
                "license = GPL\n"
                "pkgdesc = desc\n"
                "pkgrel = 1\n"
                "pkgver = 1.0.0\n"
                "url = https://foobar.com\n"
            )
        )

    print()
    with expectation:
        assert isinstance(srcinfo.SrcInfo.from_file(data=data), srcinfo.SrcInfo)  # pyright: ignore  # nosec: B101


@mark.parametrize(
    "line, key, value, field_type, expectation",
    [
        ("pkgbase = foo", "pkgbase", "foo", FieldTypeEnum.STRING, does_not_raise()),
        ("\tpkgbase = foo", "pkgbase", "foo", FieldTypeEnum.STRING, does_not_raise()),
        ("pkgdesc = foo", "pkgdesc", "foo", FieldTypeEnum.STRING, does_not_raise()),
        ("\tpkgdesc = foo", "pkgdesc", "foo", FieldTypeEnum.STRING, does_not_raise()),
        ("epoch = 1", "epoch", "1", FieldTypeEnum.INT, does_not_raise()),
        ("\tepoch = 1", "epoch", "1", FieldTypeEnum.INT, does_not_raise()),
        ("\tpkgdesc = foo", "pkgdesc", "foo", FieldTypeEnum.STRING, does_not_raise()),
        ("foo = bar", None, None, None, raises(FileParserError)),
        ("\tfoo = bar", None, None, None, raises(FileParserError)),
        ("foobar", None, None, None, raises(FileParserError)),
    ],
)
def test_parse_pairs(
    line: str,
    key: str,
    value: int | str | list[str],
    field_type: FieldTypeEnum,
    expectation: ContextManager[str],
    caplog: LogCaptureFixture,
) -> None:
    caplog.set_level(DEBUG)

    with expectation:
        assert (key, value, field_type) == srcinfo.parse_pairs(line=line)  # nosec: B101


@mark.parametrize(
    "key, value, field_type, entries, expectation",
    [
        ("foo", "bar", FieldTypeEnum.STRING, {}, does_not_raise()),
        ("foo", "bar", FieldTypeEnum.STRING_LIST, {}, does_not_raise()),
        ("foo", "bar", FieldTypeEnum.STRING_LIST, {"foo": ["baz"]}, does_not_raise()),
        ("foo", "1", FieldTypeEnum.INT, {}, does_not_raise()),
        ("foo", "bar", FieldTypeEnum.STRING, {"foo": "bar"}, raises(FileParserError)),
        ("foo", "bar", FieldTypeEnum.INT, {}, raises(FileParserError)),
        ("foo", "1", FieldTypeEnum.INT, {"foo": 1}, raises(FileParserError)),
        ("foo", "bar", FieldTypeEnum.KEY_VALUE_LIST, {}, raises(FileParserError)),
    ],
)
def test_pairs_to_entries_raises(
    key: str,
    value: str,
    field_type: FieldTypeEnum,
    entries: dict[str, int | str | list[str]],
    expectation: ContextManager[str],
) -> None:
    with expectation:
        srcinfo.pairs_to_entries(key=key, value=value, field_type=field_type, entries=entries)


def test_export_schemas(tmp_path: Path) -> None:
    srcinfo.export_schemas(output=str(tmp_path))
    srcinfo.export_schemas(output=tmp_path)

    with raises(RuntimeError):
        srcinfo.export_schemas(output="/foobar")

    with raises(RuntimeError):
        srcinfo.export_schemas(output=Path("/foobar"))
