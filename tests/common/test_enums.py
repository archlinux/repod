"""Tests for repod.common.enums."""
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
    """Tests for repod.common.enums.CompressionTypeEnum.from_string."""
    with expectation:
        assert enums.CompressionTypeEnum.from_string(input_=input_) == result  # nosec: B101


@mark.parametrize("files", [(True), (False)])
def test_compressiontypeenum_db_tar_suffix(files: bool) -> None:
    """Tests for repod.common.enums.CompressionTypeEnum.db_tar_suffix."""
    for compression_type in enums.CompressionTypeEnum:
        return_value = enums.CompressionTypeEnum.db_tar_suffix(compression_type=compression_type, files=files)
        if files:
            assert return_value.startswith(".files.tar")  # nosec: B101
        else:
            assert return_value.startswith(".db.tar")  # nosec: B101

        assert return_value.endswith(compression_type.value)  # nosec: B101


def test_compressiontypeenum_as_db_file_suffixes() -> None:
    """Tests for repod.common.enums.CompressionTypeEnum.as_db_file_suffixes."""
    assert enums.CompressionTypeEnum.as_db_file_suffixes()  # nosec: B101


def test_compressiontypeenum_as_files_file_suffixes() -> None:
    """Tests for repod.common.enums.CompressionTypeEnum.as_files_file_suffixes."""
    assert enums.CompressionTypeEnum.as_files_file_suffixes()  # nosec: B101


def test_architectureenum_as_or_regex() -> None:
    """Tests for repod.common.enums.ArchitectureEnum.as_or_regex."""
    assert enums.ArchitectureEnum.as_or_regex()  # nosec: B101


@mark.parametrize(
    "debug, staging, testing, return_value, expectation",
    [
        (False, False, False, enums.RepoTypeEnum.STABLE, does_not_raise()),
        (False, True, False, enums.RepoTypeEnum.STAGING, does_not_raise()),
        (False, False, True, enums.RepoTypeEnum.TESTING, does_not_raise()),
        (True, False, False, enums.RepoTypeEnum.STABLE_DEBUG, does_not_raise()),
        (True, True, False, enums.RepoTypeEnum.STAGING_DEBUG, does_not_raise()),
        (True, False, True, enums.RepoTypeEnum.TESTING_DEBUG, does_not_raise()),
        (True, True, True, None, raises(RuntimeError)),
    ],
)
def test_repotypeenum_from_bool(
    debug: bool,
    staging: bool,
    testing: bool,
    return_value: enums.RepoTypeEnum,
    expectation: ContextManager[str],
) -> None:
    """Tests for repod.common.enums.RepoTypeEnum.from_bool."""
    with expectation:
        assert (  # nosec: B101
            enums.RepoTypeEnum.from_bool(debug=debug, staging=staging, testing=testing) == return_value
        )
