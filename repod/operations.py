from os.path import join
from pathlib import Path
from typing import AsyncIterator, Dict, Optional, Tuple

import aiofiles
import orjson

from repod.common.enums import CompressionTypeEnum
from repod.files import _db_file_member_as_model, open_tarfile
from repod.repo.management import OutputPackageBase
from repod.repo.package import (
    Files,
    PackageDesc,
    RepoDbMemberTypeEnum,
    RepoDbTypeEnum,
    SyncDatabase,
)


async def db_file_as_models(
    db_path: Path, compression: Optional[CompressionTypeEnum] = None
) -> AsyncIterator[Tuple[str, OutputPackageBase]]:
    """Read a repository database and yield the name of each pkgbase and the respective data (represented as an instance
    of OutputPackageBase) in a Tuple.

    Parameters
    ----------
    db_path: Path
        A Path representing a repository database file
    compression: str
        The compression used for the repository database file (support depends on tarfile). Defaults to "gz" (gzip
        compression)

    Returns
    -------
    Iterator[Tuple[str, OutputPackageBase]]:
        A Tuple holding the name of a pkgbase and its accompanying data in an instance of OutputPackageBase
    """

    packages: Dict[str, OutputPackageBase] = {}
    package_descs: Dict[str, PackageDesc] = {}
    package_files: Dict[str, Files] = {}

    with open_tarfile(path=db_path, compression=compression) as db_tarfile:
        async for member in _db_file_member_as_model(db_file=db_tarfile):
            match member.member_type:
                case RepoDbMemberTypeEnum.DESC:
                    package_descs.update({member.name: await PackageDesc.from_stream(data=member.data)})
                case RepoDbMemberTypeEnum.FILES:
                    package_files.update({member.name: await Files.from_stream(data=member.data)})
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
    input_path: Path, output_path: Path, db_type: RepoDbTypeEnum = RepoDbTypeEnum.DEFAULT
) -> None:
    """Create a repository database from a list of JSON files found in a directory

    Parameters
    ----------
    input_path: Path
        A directory from which to read JSON files
    output_path: Path
        A file to which to write a repository database
    db_type: RepoDbTypeEnum
        A member of RepoDbTypeEnum to define what type of repository database to create:
        Either RepoDbTypeEnum.DEFAULT for the default .db database or RepoDbTypeEnum.FILES for the .files
        database (defaults to RepoDbTypeEnum.DEFAULT)
    """

    sync_db = SyncDatabase(database=output_path, database_type=db_type, compression_type=CompressionTypeEnum.GZIP)
    await sync_db.stream_management_repo(path=input_path)
