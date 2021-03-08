import re
import tarfile
from pathlib import Path
from typing import Iterator


def _read_db_file(db_path: Path, compression: str = "gz") -> tarfile.TarFile:
    """Read a repository database file

    Parameters
    ----------
    db_path: Path
        A pathlib.Path instance, representing the location of the database file
    compression: str
        The compression used for the database file (defaults to 'gz')

    Raises
    ------
    ValueError
        If the file represented by db_path does not exist
    tarfile.ReadError
        If the file could not be opened
    tarfile.CompressionError
        If the provided compression does not match the compression of the file or if the compression type is unknown

    Returns
    -------
    tarfile.Tarfile
        An instance of Tarfile
    """

    return tarfile.open(name=db_path, mode=f"r:{compression}")


def _read_db_file_member(db_file: tarfile.TarFile, regex: str = "(/desc|/files)$") -> Iterator[tarfile.TarInfo]:
    """Read the members of a database file, represented by an instance of tarfile.TarFile and yield the members as
    instances of tarfile.TarInfo

    Paramaters
    ----------
    tarfile.TarFile
        An instance of TarFile representing a repository database
    regex: str
        A regular expression used to filter the names of the members contained in db_file (defaults to
        '(/desc|/files)$')
    """

    for name in [name for name in db_file.getnames() if re.search(regex, name)]:
        yield db_file.getmember(name)
