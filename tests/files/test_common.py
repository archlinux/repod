from contextlib import nullcontext as does_not_raise
from pathlib import Path
from tarfile import TarFile
from typing import ContextManager, List, Optional, Set, Tuple, Union
from unittest.mock import patch

from pytest import mark, raises

from repod.common.enums import CompressionTypeEnum
from repod.errors import RepoManagementFileError, RepoManagementFileNotFoundError
from repod.files import common


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


@mark.parametrize(
    "file, as_stringio, gzip_compressed, expectation",
    [
        (".BUILDINFO", True, False, does_not_raise()),
        (".MTREE", True, True, does_not_raise()),
        (".PKGINFO", True, False, does_not_raise()),
        (".BUILDINFO", False, False, does_not_raise()),
        (".MTREE", False, True, does_not_raise()),
        (".PKGINFO", False, False, does_not_raise()),
        ("foo", False, False, raises(RepoManagementFileNotFoundError)),
        ("empty_dir", False, False, raises(RepoManagementFileNotFoundError)),
        (".PKGINFO", False, True, raises(RepoManagementFileError)),
    ],
)
async def test_extract_file_from_tarfile(
    file: str,
    as_stringio: bool,
    gzip_compressed: bool,
    expectation: ContextManager[str],
    default_package_file: Tuple[Path, ...],
) -> None:
    with common.open_tarfile(path=default_package_file[0], compression=None, mode="r") as tarfile:
        with expectation:
            await common.extract_file_from_tarfile(
                tarfile=tarfile,
                file=file,
                as_stringio=as_stringio,
                gzip_compressed=gzip_compressed,
            )


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


@mark.parametrize(
    "names, expectation",
    [
        ([".BUILDINFO", ".MTREE", ".PKGINFO", "text_file"], True),
        ({".BUILDINFO", ".MTREE", ".PKGINFO", "text_file"}, True),
        (["foo", "bar"], False),
        ({"foo", "bar"}, False),
    ],
)
def test_names_in_tarfile(
    names: Union[List[str], Set[str]],
    expectation: bool,
    default_package_file: Tuple[Path, ...],
) -> None:
    with common.open_tarfile(path=default_package_file[0], compression=None, mode="r") as tarfile:
        assert common.names_in_tarfile(tarfile=tarfile, names=names) is expectation
