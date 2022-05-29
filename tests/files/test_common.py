from asyncio import AbstractEventLoop, get_event_loop
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from tarfile import TarFile
from typing import ContextManager, Generator, Optional, Tuple
from unittest.mock import patch

from pytest import fixture, mark, raises

from repod.common.enums import CompressionTypeEnum
from repod.errors import RepoManagementFileError, RepoManagementFileNotFoundError
from repod.files import common


@fixture(scope="module")
def event_loop() -> Generator[AbstractEventLoop, None, None]:
    loop = get_event_loop()
    yield loop
    loop.close()


@mark.parametrize(
    "file_type, compression_override, expectation",
    [
        (".bz2", None, does_not_raise()),
        (".gz", None, does_not_raise()),
        (".tar", None, does_not_raise()),
        (".xz", None, does_not_raise()),
        (".zst", None, does_not_raise()),
        (".txt", None, raises(RepoManagementFileError)),
        (".bz2", CompressionTypeEnum.GZIP, raises(RepoManagementFileError)),
        (".gz", CompressionTypeEnum.BZIP2, raises(RepoManagementFileError)),
        (".xz", CompressionTypeEnum.ZSTANDARD, raises(RepoManagementFileError)),
        (".zst", CompressionTypeEnum.LZMA, raises(RepoManagementFileError)),
        (".txt", CompressionTypeEnum.NONE, raises(RepoManagementFileError)),
        (".txt", "foo", raises(RepoManagementFileError)),
    ],
)
def test_open_tarfile(
    file_type: str,
    compression_override: Optional[str],
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
        case ".gz":
            path = gz_file
        case ".tar":
            path = tar_file
        case ".xz":
            path = xz_file
        case ".zst":
            path = zst_file
        case ".txt":
            path = text_file
    with expectation:
        with common.open_tarfile(
            path=path,
            compression=compression_override,
        ) as tarfile_file:
            assert isinstance(tarfile_file, TarFile)


def test_open_tarfile_sync_db_file(
    default_sync_db_file: Tuple[Path, Path],
    files_sync_db_file: Tuple[Path, Path],
) -> None:
    for path in default_sync_db_file + files_sync_db_file:
        with common.open_tarfile(
            path=path,
        ) as tarfile_file:
            assert isinstance(tarfile_file, TarFile)


def test_open_tarfile_relative_path() -> None:
    with raises(RepoManagementFileError):
        with common.open_tarfile(
            path=Path("foo"),
        ) as tarfile_file:
            assert isinstance(tarfile_file, TarFile)


async def test_extract_file_from_tarfile(zst_file: Path) -> None:
    with common.ZstdTarFile(zst_file) as tarfile:
        for member in tarfile.getmembers():
            if member.name.endswith(".txt"):
                assert await common.extract_file_from_tarfile(tarfile=tarfile, file=member.name)
            else:
                with raises(RepoManagementFileNotFoundError):
                    assert await common.extract_file_from_tarfile(tarfile=tarfile, file=member.name)

                with raises(RepoManagementFileNotFoundError):
                    assert await common.extract_file_from_tarfile(tarfile=tarfile, file=f"{member.name}foobar")


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
