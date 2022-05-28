from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import ContextManager
from unittest.mock import patch

from pytest import mark, raises

from repod.common.enums import CompressionTypeEnum
from repod.errors import RepoManagementFileError, RepoManagementFileNotFoundError
from repod.files import common


@mark.parametrize(
    "file_type, expectation",
    [
        (".bz2", does_not_raise()),
        (".gz", does_not_raise()),
        (".xz", does_not_raise()),
        (".zst", does_not_raise()),
        (".foo", raises(RepoManagementFileError)),
    ],
)
@mark.asyncio
async def test_open_package_file(
    file_type: str,
    bz2_file: Path,
    gz_file: Path,
    xz_file: Path,
    zst_file: Path,
    expectation: ContextManager[str],
) -> None:
    match file_type:
        case ".bz2":
            path = bz2_file
        case ".gz":
            path = gz_file
        case ".xz":
            path = xz_file
        case ".zst":
            path = zst_file
        case ".foo":
            path = Path("foo.foo")
    with expectation:
        assert await common.open_package_file(path=path)


async def test_extract_from_package_file(zst_file: Path) -> None:
    with common.ZstdTarFile(zst_file) as tarfile:
        for member in tarfile.getmembers():
            if member.name.endswith(".txt"):
                assert await common.extract_from_package_file(tarfile, member.name)
            else:
                with raises(RepoManagementFileNotFoundError):
                    assert await common.extract_from_package_file(tarfile, member.name)

                with raises(RepoManagementFileNotFoundError):
                    assert await common.extract_from_package_file(tarfile, f"{member.name}foobar")


def test_zstdtarfile_raises(zst_file: Path) -> None:
    with patch.object(common.TarFile, "__init__") as tarfile_mock:
        tarfile_mock.side_effect = Exception("FAIL")
        with raises(RepoManagementFileError):
            common.ZstdTarFile(name=zst_file, mode="r")


@mark.parametrize(
    "file_type, expectation",
    [
        (".bz2", does_not_raise()),
        (".gz", does_not_raise()),
        (".tar", does_not_raise()),
        (".txt", raises(RepoManagementFileError)),
        (".xz", does_not_raise()),
        (".zst", does_not_raise()),
    ],
)
def test_compression_type_of_tarfile(
    file_type: str,
    expectation: ContextManager[str],
    bz2_file: Path,
    gz_file: Path,
    tar_file: Path,
    text_file: Path,
    xz_file: Path,
    zst_file: Path,
) -> None:
    match file_type:
        case ".bz2":
            path = bz2_file
            result = CompressionTypeEnum.BZIP2
        case ".gz":
            path = gz_file
            result = CompressionTypeEnum.GZIP
        case ".tar":
            path = tar_file
            result = CompressionTypeEnum.NONE
        case ".txt":
            path = text_file
            result = None
        case ".xz":
            path = xz_file
            result = CompressionTypeEnum.LZMA
        case ".zst":
            path = zst_file
            result = CompressionTypeEnum.ZSTANDARD
        case ".foo":
            path = Path("foo.foo")
    with expectation:
        assert common.compression_type_of_tarfile(path=path) == result
