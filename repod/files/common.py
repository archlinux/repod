from gzip import BadGzipFile
from gzip import open as gzip_open
from io import BytesIO, StringIO
from logging import debug
from pathlib import Path
from tarfile import ReadError, TarFile
from tarfile import open as tarfile_open
from typing import IO, Dict, List, Literal, Optional, Set, Union

import magic
from pyzstd import CParameter, ZstdDict, ZstdFile

from repod.common.enums import CompressionTypeEnum
from repod.errors import RepoManagementFileError, RepoManagementFileNotFoundError


class ZstdTarFile(TarFile):
    """A class to provide reading and writing of zstandard files using TarFile functionality"""

    def __init__(  # type: ignore[no-untyped-def]
        self,
        name: Union[str, Path],
        mode: Literal["r", "a", "w", "x"] = "r",
        level_or_option: Union[None, int, Dict[CParameter, int]] = None,
        zstd_dict: Optional[ZstdDict] = None,
        **kwargs,
    ) -> None:
        self.zstd_file = ZstdFile(
            filename=name,
            mode=mode,
            level_or_option=level_or_option,
            zstd_dict=zstd_dict,
        )

        try:
            super().__init__(fileobj=self.zstd_file, mode=mode, **kwargs)
        except Exception as e:
            self.zstd_file.close()
            raise RepoManagementFileError(f"An error occured while trying to open the file {name}!\n{e}")

    def close(self) -> None:
        try:
            super().close()
        finally:
            self.zstd_file.close()


def compression_type_of_tarfile(path: Path) -> CompressionTypeEnum:
    """Retrieve the compression type of a tar file

    Parameters
    ----------
    path: Path
        The path to a tar file

    Raises
    ------
    RepoManagementFileError
        If an unknown compression type is encountered

    Returns
    -------
    CompressionTypeEnum
        A member of CompressionTypeEnum, that reflects the compression type of tar file at path
    """

    with open(path, "rb") as f:
        file_start_bytes: bytes = f.read(2048)

    # Try and detect the instance of the libmagic shared library (loaded via
    # ctypes) used by the magic.py shipped with file.
    if hasattr(magic, "_libraries"):  # pragma: no cover
        file = magic.detect_from_content(file_start_bytes).name  # type: ignore[attr-defined]
    else:
        file = magic.from_buffer(file_start_bytes)
    file = " ".join(file.split()[0:3]).lower().strip(",")
    debug(f"Type of file {path} detected as: {file}")

    match file:
        case "posix tar archive":
            return CompressionTypeEnum.NONE
        case "bzip2 compressed data":
            return CompressionTypeEnum.BZIP2
        case "gzip compressed data":
            return CompressionTypeEnum.GZIP
        case "xz compressed data":
            return CompressionTypeEnum.LZMA
        case "zstandard compressed data":
            return CompressionTypeEnum.ZSTANDARD
        case _:
            raise RepoManagementFileError(
                f"An error occured while attempting to retrieve the compression type of tar file: {path}!\n"
                "Unknown compression type encountered."
            )


def open_tarfile(
    path: Path,
    compression: Optional[CompressionTypeEnum] = None,
    mode: Literal["r", "w", "x"] = "r",
) -> TarFile:
    """Open a file as a TarFile

    This function distinguishes between bzip2, gzip, lzma and zstandard compression depending on file suffix.
    The detection can be overridden by providing either a file suffix or compression type.

    Parameters
    ----------
    path: Path
        A Path to a file
    compression: Optional[CompressionTypeEnum]
        An optional compression type to override the detection based on mime type.
    mode: Literal["r", "w", "x"]
        A mode to open the file with (defaults to "r").
        "r" - open file for reading
        "w" - open file for writing
        "x" - create file

    Raises
    ------
    ValueError
        If the file represented by db_path does not exist
    tarfile.ReadError
        If the file could not be opened
    RepoManagementFileError
        If the compression type is unknown

    Returns
    -------
    tarfile.Tarfile
        An instance of Tarfile
    """

    debug(f"Opening file {path}...")

    if not path.is_absolute():
        raise RepoManagementFileError(f"An error occured while attempting to resolve a file path: {path} is relative!")
    if path.is_symlink():
        path = path.resolve()

    compression_type = compression if compression else compression_type_of_tarfile(path=path)

    match compression_type:
        case CompressionTypeEnum.NONE | CompressionTypeEnum.BZIP2 | CompressionTypeEnum.GZIP | CompressionTypeEnum.LZMA:
            try:
                return tarfile_open(name=path, mode=f"{mode}:{compression_type.value}")
            except ReadError as e:
                raise RepoManagementFileError(
                    f"An error occured attempting to read tar file {path} using compression type "
                    f"{compression_type.value}.\n{e}"
                )
        case CompressionTypeEnum.ZSTANDARD:
            return ZstdTarFile(name=path, mode=mode)
        case _:
            raise RepoManagementFileError(
                f"Unknown compression type {compression_type} encountered while attempting to open file {path}!"
            )


async def extract_file_from_tarfile(
    tarfile: TarFile,
    file: str,
    as_stringio: bool = False,
    gzip_compressed: bool = False,
) -> Union[IO[bytes], StringIO]:
    """Extract a file from a TarFile and return it as a bytes stream or text I/O buffer

    Parameters
    ----------
    tarfile: TarFile
        An instance of TarFile
    file: str
        A string representing the name of a file contained in tarfile
    as_stringio: bool
        Whether to return the data as StringIO (defaults to False)
    gzip_compressed: bool
        Whether the target file in tarfile is gzip compressed (defaults to False)

    Raises
    ------
    RepoManagementFileNotFoundError
        If the requested file does not exist in the tarfile or if the requested file is neither a file nor a symlink
    RepoManagementFileError
        If gzip_compressed is True and file is not a gzip compressed file or the gzip compressed file is corrupted

    Returns
    -------
    IO[bytes]
        A bytes stream that represents the file to extract
    """

    debug(f"Extracting file {file} from {str(tarfile.name)}...")

    try:
        extracted = tarfile.extractfile(file)
        if extracted is None:
            raise RepoManagementFileNotFoundError(
                f"File {file} in {str(tarfile.name)} is not a file or a symbolic link!"
            )
    except KeyError as e:
        raise RepoManagementFileNotFoundError(f"File {file} not found in {str(tarfile.name)}!\n{e}")

    if gzip_compressed:
        try:
            with gzip_open(extracted) as extracted_file:
                if as_stringio:
                    return StringIO(BytesIO(extracted_file.read()).read().decode("utf-8"))
                else:
                    return BytesIO(extracted_file.read())
        except BadGzipFile as e:
            raise RepoManagementFileError(f"An error occured trying to read the gzip compressed file {file}\n{e}\n")
    else:
        if as_stringio:
            return StringIO(initial_value=extracted.read().decode("utf-8"))
        else:
            return extracted


def names_in_tarfile(tarfile: TarFile, names: Union[List[str], Set[str]]) -> bool:
    """Check whether a list of names is found in the list of names of a TarFile

    Parameters
    ----------
    tarfile: TarFile
        A TarFile to lookup names in
    names: Union[List[str], Set[str]]
        A list or set of names to lookup

    Returns
    -------
    bool
        True if all names can be found in the list of TarFile names, else False
    """

    if isinstance(names, list):
        names = set(names)

    if names == set([name for name in tarfile.getnames() if name in names]):
        return True
    else:
        return False
