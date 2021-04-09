import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterator

from pytest import fixture, mark

from repo_management import models, operations

from .fixtures import create_db_file, create_json_files


@fixture(scope="function")
def create_gz_db_file() -> Iterator[Path]:
    db_file = create_db_file()
    yield db_file
    os.remove(db_file)


@fixture(scope="function")
def create_dir_path() -> Iterator[Path]:
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@fixture(scope="function")
def dummy_json_files_in_dir() -> Iterator[Path]:
    temp_dir = create_json_files()
    yield temp_dir
    shutil.rmtree(temp_dir)


@fixture(scope="function")
def empty_file() -> Iterator[Path]:
    [foo, file_name] = tempfile.mkstemp()
    yield Path(file_name)


@mark.asyncio
async def test_db_file_as_models(create_gz_db_file: Path) -> None:
    async for (name, model) in operations.db_file_as_models(db_path=create_gz_db_file):
        assert isinstance(name, str)
        assert isinstance(model, models.OutputPackageBase)


@mark.asyncio
async def test_dump_db_to_json_files(
    create_gz_db_file: Path,
    create_dir_path: Path,
) -> None:
    await operations.dump_db_to_json_files(input_path=create_gz_db_file, output_path=create_dir_path)


@mark.asyncio
async def test_create_db_from_json_files(dummy_json_files_in_dir: Path, empty_file: Path) -> None:
    await operations.create_db_from_json_files(input_path=dummy_json_files_in_dir, output_path=empty_file)
