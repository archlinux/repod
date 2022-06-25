from __future__ import annotations

import contextlib
import io
import re
import tarfile
import time
from pathlib import Path
from typing import AsyncIterator, Iterator

import aiofiles
import orjson

from repod import errors
from repod.config.defaults import DB_DIR_MODE, DB_FILE_MODE, DB_GROUP, DB_USER
from repod.files.common import extract_file_from_tarfile, open_tarfile  # noqa: F401
from repod.files.package import Package  # noqa: F401
from repod.repo import management
from repod.repo.package import RepoDbMemberData, RepoDbMemberTypeEnum, RepoDbTypeEnum


async def _extract_db_member_package_name(name: str) -> str:
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


async def _db_file_member_as_model(
    db_file: tarfile.TarFile, regex: str = "(/desc|/files)$"
) -> AsyncIterator[RepoDbMemberData]:
    """Iterate over the members of a database file, represented by an instance of tarfile.TarFile and yield the members
    as instances of RepoDbMemberData

    The method filters the list of evaluated members using a regular expression. Depending on member name one of
    RepoDbMemberTypeEnum is chosen.

    Parameters
    ----------
    tarfile.TarFile
        An instance of TarFile representing a repository database
    regex: str
        A regular expression used to filter the names of the members contained in db_file (defaults to
        '(/desc|/files)$')
    """

    for name in [name for name in db_file.getnames() if re.search(regex, name)]:
        file_type = RepoDbMemberTypeEnum.UNKNOWN
        if re.search("(/desc)$", name):
            file_type = RepoDbMemberTypeEnum.DESC
        if re.search("(/files)$", name):
            file_type = RepoDbMemberTypeEnum.FILES

        yield RepoDbMemberData(
            member_type=file_type,
            name=await _extract_db_member_package_name(name=name),
            data=io.StringIO(
                io.BytesIO(
                    db_file.extractfile(name).read(),  # type: ignore[union-attr]
                )
                .read()
                .decode("utf-8"),
            ),
        )


async def _json_files_in_directory(path: Path) -> AsyncIterator[Path]:
    """Yield JSON files found in a directory

    Parameters
    ----------
    path: Path
        A Path to search in for JSON files

    Raises
    ------
    errors.RepoManagementFileNotFoundError
        If there are no JSON files found below

    Returns
    -------
    AsyncIterator[Path]
        An iterator over the files found in the directory defined by path
    """

    file_list = sorted(path.glob("*.json"))
    if not file_list:
        raise errors.RepoManagementFileNotFoundError(f"There are no JSON files in {path}!")

    for json_file in file_list:
        yield json_file


async def _read_pkgbase_json_file(path: Path) -> management.OutputPackageBase:
    """Read a JSON file that represents a pkgbase and return it as OutputPackageBase

    Parameters
    ----------
    path: Path
        A Path to to a JSON file

    Raises
    ------
    errors.RepoManagementFileError
        If the JSON file can not be decoded
    errors.RepoManagementValidationError
        If the JSON file can not be validated using OutputPackageBase

    Returns
    -------
    OutputPackageBase
        A pydantic model representing a pkgbase
    """

    async with aiofiles.open(path, "r") as input_file:
        try:
            model = management.OutputPackageBase.from_dict(data=orjson.loads(await input_file.read()))
            return model
        except orjson.JSONDecodeError as e:
            raise errors.RepoManagementFileError(f"The JSON file '{path}' could not be decoded!\n{e}")


@contextlib.contextmanager
def _write_db_file(path: Path, compression: str = "gz") -> Iterator[tarfile.TarFile]:
    """Open a repository database file for writing

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

    with tarfile.open(name=path, mode=f"w:{compression}") as t:
        yield t


async def _stream_package_base_to_db(
    db: tarfile.TarFile,
    model: management.OutputPackageBase,
    db_type: RepoDbTypeEnum,
) -> None:
    """Stream descriptor files for packages of a pkgbase to a repository database

    Allows streaming to a default repository database or a files database

    Parameters
    ----------
    db: tarfile.TarFile
        The repository database to stream to
    model: OutputPackageBase
        The model to use for streaming descriptor files to the repository database
    db_type: RepoDbTypeEnum
        The type of database to stream to
    """

    for (desc_model, files_model) in await model.get_packages_as_models():
        dirname = f"{desc_model.get_name()}-{model.get_version()}"
        directory = tarfile.TarInfo(dirname)
        directory.type = tarfile.DIRTYPE
        directory.mtime = int(time.time())
        directory.uname = DB_USER
        directory.gname = DB_GROUP
        directory.mode = int(DB_DIR_MODE, base=8)
        db.addfile(directory)

        desc_content = io.StringIO()
        await desc_model.render(output=desc_content)
        desc_file = tarfile.TarInfo(f"{dirname}/desc")
        desc_file.size = len(desc_content.getvalue().encode())
        desc_file.mtime = int(time.time())
        desc_file.uname = DB_USER
        desc_file.gname = DB_GROUP
        desc_file.mode = int(DB_FILE_MODE, base=8)
        db.addfile(desc_file, io.BytesIO(desc_content.getvalue().encode()))
        if db_type == RepoDbTypeEnum.FILES:
            files_content = io.StringIO()
            await files_model.render(output=files_content)
            files_file = tarfile.TarInfo(f"{dirname}/files")
            files_file.size = len(files_content.getvalue().encode())
            files_file.mtime = int(time.time())
            files_file.uname = DB_USER
            files_file.gname = DB_GROUP
            files_file.mode = int(DB_FILE_MODE, base=8)
            db.addfile(files_file, io.BytesIO(files_content.getvalue().encode()))
