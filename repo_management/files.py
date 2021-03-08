import io
import re
import tarfile
from pathlib import Path
from typing import Iterator

from repo_management import defaults, models


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


def _extract_db_member_package_name(name: str) -> str:
    """Extract and return the package name from a repository database member name

    Parameters
    ----------
    name: str
        The name of a member of a repository database (i.e. one of tarfile.Tarfile.getnames())

    Returns
    str
        The package name extracted from name
    """

    return "".join(re.split("(-)", re.sub("(/desc|/files)$", "", name))[:-4])


def _db_file_member_as_model(
    db_file: tarfile.TarFile, regex: str = "(/desc|/files)$"
) -> Iterator[models.RepoDbMemberData]:
    """Iterate over the members of a database file, represented by an instance of tarfile.TarFile and yield the members
    as instances of models.RepoDbMemberData

    The method filters the list of evaluated members using a regular expression. Depending on member name one of
    defaults.RepoDbMemberType is chosen.

    Paramaters
    ----------
    tarfile.TarFile
        An instance of TarFile representing a repository database
    regex: str
        A regular expression used to filter the names of the members contained in db_file (defaults to
        '(/desc|/files)$')
    """

    for name in [name for name in db_file.getnames() if re.search(regex, name)]:
        file_type = defaults.RepoDbMemberType.UNKNOWN
        if re.search("(/desc)$", name):
            file_type = defaults.RepoDbMemberType.DESC
        if re.search("(/files)$", name):
            file_type = defaults.RepoDbMemberType.FILES

        yield models.RepoDbMemberData(
            member_type=file_type,
            name=_extract_db_member_package_name(name=name),
            data=io.StringIO(
                io.BytesIO(
                    db_file.extractfile(name).read(),  # type: ignore
                )
                .read()
                .decode("utf-8"),
            ),
        )
