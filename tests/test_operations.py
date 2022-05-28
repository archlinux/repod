import tempfile
from asyncio import AbstractEventLoop, get_event_loop
from pathlib import Path
from typing import Generator, Tuple

import py
from pytest import fixture, mark

from repod import models, operations

from .fixtures import create_json_files


@fixture(scope="module")
def event_loop() -> Generator[AbstractEventLoop, None, None]:
    loop = get_event_loop()
    yield loop
    loop.close()


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
async def test_db_file_as_models(files_sync_db_file: Tuple[Path, Path]) -> None:
    async for (name, model) in operations.db_file_as_models(db_path=files_sync_db_file[0]):
        assert isinstance(name, str)
        assert isinstance(model, models.package.OutputPackageBaseV1)


@mark.asyncio
async def test_dump_db_to_json_files(
    files_sync_db_file: Tuple[Path, Path],
    create_dir_path: Path,
) -> None:
    await operations.dump_db_to_json_files(input_path=files_sync_db_file[0], output_path=create_dir_path)


@mark.asyncio
async def test_create_db_from_json_files(dummy_json_files_in_dir: Path, empty_file: Path) -> None:
    await operations.create_db_from_json_files(input_path=dummy_json_files_in_dir, output_path=empty_file)
