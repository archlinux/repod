from contextlib import nullcontext as does_not_raise
from typing import ContextManager

from pytest import mark, raises

from repod.common import enums


@mark.parametrize(
    "input_, result, expectation",
    [
        ("none", enums.CompressionTypeEnum.NONE, does_not_raise()),
        ("bzip2", enums.CompressionTypeEnum.BZIP2, does_not_raise()),
        ("bz2", enums.CompressionTypeEnum.BZIP2, does_not_raise()),
        ("gzip", enums.CompressionTypeEnum.GZIP, does_not_raise()),
        ("gz", enums.CompressionTypeEnum.GZIP, does_not_raise()),
        ("lzma", enums.CompressionTypeEnum.LZMA, does_not_raise()),
        ("xz", enums.CompressionTypeEnum.LZMA, does_not_raise()),
        ("zstandard", enums.CompressionTypeEnum.ZSTANDARD, does_not_raise()),
        ("zst", enums.CompressionTypeEnum.ZSTANDARD, does_not_raise()),
        ("foo", None, raises(RuntimeError)),
    ],
)
def test_compressiontypeenum(input_: str, result: enums.CompressionTypeEnum, expectation: ContextManager[str]) -> None:
    with expectation:
        assert enums.CompressionTypeEnum.from_string(input_=input_) == result


def test_compressiontypeenum_as_db_file_suffixes() -> None:
    assert enums.CompressionTypeEnum.as_db_file_suffixes()


def test_compressiontypeenum_as_files_file_suffixes() -> None:
    assert enums.CompressionTypeEnum.as_files_file_suffixes()


def test_architectureenum_as_or_regex() -> None:
    assert enums.ArchitectureEnum.as_or_regex()
