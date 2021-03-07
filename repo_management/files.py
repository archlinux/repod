import tarfile
from pathlib import Path


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
