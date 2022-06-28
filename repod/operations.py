from os.path import join
from pathlib import Path

import aiofiles
import orjson

from repod.common.enums import CompressionTypeEnum
from repod.repo.package import RepoDbTypeEnum, SyncDatabase


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

    for name, model in await SyncDatabase(database=input_path).outputpackagebases():
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
