from os.path import join
from pathlib import Path
from typing import AsyncIterator, Dict, Optional, Tuple

import aiofiles
import orjson

from repod import convert, models
from repod.files import (
    _db_file_member_as_model,
    _json_files_in_directory,
    _read_pkgbase_json_file,
    _stream_package_base_to_db,
    _write_db_file,
    open_tarfile,
)


async def db_file_as_models(
    db_path: Path, compression: Optional[str] = "gzip"
) -> AsyncIterator[Tuple[str, models.OutputPackageBase]]:
    """Read a repository database and yield the name of each pkgbase and the respective data (represented as an instance
    of models.OutputPackageBase) in a Tuple.

    Parameters
    ----------
    db_path: Path
        A Path representing a repository database file
    compression: str
        The compression used for the repository database file (support depends on tarfile). Defaults to "gz" (gzip
        compression)

    Returns
    -------
    Iterator[Tuple[str, models.OutputPackageBase]]:
        A Tuple holding the name of a pkgbase and its accompanying data in an instance of models.OutputPackageBase
    """

    packages: Dict[str, models.OutputPackageBase] = {}
    package_descs: Dict[str, models.PackageDesc] = {}
    package_files: Dict[str, models.Files] = {}

    with open_tarfile(path=db_path, compression=compression) as db_tarfile:
        async for member in _db_file_member_as_model(db_file=db_tarfile):
            match member.member_type:
                case models.RepoDbMemberTypeEnum.DESC:
                    desc_data: models.PackageDesc = await convert.file_data_to_model(  # type: ignore[assignment]
                        name=member.name, data=member.data, data_type=member.member_type
                    )
                    package_descs.update({member.name: desc_data})
                case models.RepoDbMemberTypeEnum.FILES:
                    files_data: models.Files = await convert.file_data_to_model(  # type: ignore[assignment]
                        name=member.name, data=member.data, data_type=member.member_type
                    )
                    package_files.update({member.name: files_data})
                case _:  # pragma: no cover
                    # NOTE: this case can never be reached, but we add it to make tests happy
                    raise RuntimeError(
                        f"The database file {db_path} contains the member {member.name} of the unsupported type "
                        f"{member.member_type}!"
                    )

    for (name, package_desc) in package_descs.items():
        if packages.get(package_desc.get_base()):
            packages[package_desc.get_base()].add_packages(
                [package_desc.get_output_package(files=package_files.get(name))]
            )
        else:
            packages.update(
                {
                    package_desc.get_base(): package_desc.get_output_package_base(files=package_files.get(name)),
                }
            )

    for (name, package) in packages.items():
        yield (name, package)


async def dump_db_to_json_files(input_path: Path, output_path: Path) -> None:
    """Read a repository database file and dump each pkgbase contained in it to a separate JSON file below a defined
    output directory

    Parameters
    ----------
    input_path: Path
        The input file to read and parse
    output_path: Path
        A directory in which to
    """

    async for name, model in db_file_as_models(db_path=input_path):
        async with aiofiles.open(join(output_path, f"{name}.json"), "wb") as output_file:
            await output_file.write(
                orjson.dumps(
                    model.dict(), option=orjson.OPT_INDENT_2 | orjson.OPT_APPEND_NEWLINE | orjson.OPT_SORT_KEYS
                )
            )


async def create_db_from_json_files(
    input_path: Path, output_path: Path, db_type: models.RepoDbTypeEnum = models.RepoDbTypeEnum.DEFAULT
) -> None:
    """Create a repository database from a list of JSON files found in a directory

    Parameters
    ----------
    input_path: Path
        A directory from which to read JSON files
    output_path: Path
        A file to which to write a repository database
    db_type: models.RepoDbTypeEnum
        A member of models.RepoDbTypeEnum to define what type of repository database to create:
        Either models.RepoDbTypeEnum.DEFAULT for the default .db database or models.RepoDbTypeEnum.FILES for the .files
        database (defaults to models.RepoDbTypeEnum.DEFAULT)
    """

    repodbfile = convert.RepoDbFile()
    with _write_db_file(path=output_path) as database:
        async for path in _json_files_in_directory(path=input_path):
            model = await _read_pkgbase_json_file(path)
            await _stream_package_base_to_db(
                db=database,
                model=model,
                repodbfile=repodbfile,
                db_type=db_type,
            )
