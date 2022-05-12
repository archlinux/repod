from logging import debug
from pathlib import Path
from tarfile import TarFile
from tarfile import open as tarfile_open
from typing import IO, Dict, Literal, Optional, Union

from pyzstd import CParameter, ZstdDict, ZstdFile

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


async def open_package_file(path: Path) -> TarFile:
    """Open a package file as a TarFile

    Parameters
    ----------
    path: Path
        A pathlib.Path instance, representing the location of the package

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

    debug(f"Reading package file {path}...")

    match path.suffix:
        case ".bz2" | ".gz" | ".xz":
            return tarfile_open(name=path, mode=f"r:{path.suffix.replace('.', '')}")
        case ".zst":
            return ZstdTarFile(name=path, mode="r")
        case _:
            raise RepoManagementFileError(
                f"Unknown file suffix {path.suffix} encountered while trying to read package file {path}!"
            )


async def extract_from_package_file(package: TarFile, file: str) -> IO[bytes]:
    """Extract a file from a package

    Parameters
    ----------
    package: TarFile
        A TarFile instance representing a package
    file: str
        A string representing the name of a file contained in package

    Raises
    ------
    RepoManagementFileNotFoundError
        If the requested file does not exist in the package or if the requested package is neither a file nor a symlink

    Returns
    -------
    IO[bytes]
        A bytes stream that represents the file to extract
    """

    debug(f"Extracting file {file} from {str(package.name)}...")

    try:
        extracted = package.extractfile(file)
    except KeyError as e:
        raise RepoManagementFileNotFoundError(f"File {file} not found in {str(package.name)}!\n{e}")

    if extracted is None:
        raise RepoManagementFileNotFoundError(f"File {file} in {str(package.name)} is not a file or a symbolic link!")

    return extracted
