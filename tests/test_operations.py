import tempfile
from pathlib import Path

import py
from pytest import fixture, mark

from repo_management import models, operations

from .fixtures import create_db_file, create_json_files


@fixture(scope="function")
def create_gz_db_file(tmpdir: py.path.local) -> Path:
    return create_db_file(tmpdir)


@fixture(scope="function")
def create_dir_path(tmpdir: py.path.local) -> Path:
    return Path(tempfile.mkdtemp(dir=tmpdir))


@fixture(scope="function")
def dummy_json_files_in_dir(tmpdir: py.path.local) -> Path:
    create_json_files(tmpdir)
    return Path(tmpdir)


@fixture(scope="function")
def empty_file(tmpdir: py.path.local) -> Path:
    [foo, file_name] = tempfile.mkstemp(dir=tmpdir)
    return Path(file_name)


@mark.asyncio
async def test_db_file_as_models(create_gz_db_file: Path) -> None:
    async for (name, model) in operations.db_file_as_models(db_path=create_gz_db_file):
        assert isinstance(name, str)
        assert isinstance(model, models.OutputPackageBaseV1)


@mark.asyncio
async def test_dump_db_to_json_files(
    create_gz_db_file: Path,
    create_dir_path: Path,
) -> None:
    await operations.dump_db_to_json_files(input_path=create_gz_db_file, output_path=create_dir_path)


@mark.asyncio
async def test_create_db_from_json_files(dummy_json_files_in_dir: Path, empty_file: Path) -> None:
    await operations.create_db_from_json_files(input_path=dummy_json_files_in_dir, output_path=empty_file)
