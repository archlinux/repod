import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterator

from mock import Mock
from pytest import fixture, raises

from repo_management import models, operations

from .fixtures import create_db_file


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


def test_db_file_as_models(create_gz_db_file: Path) -> None:
    for (name, model) in operations.db_file_as_models(db_path=create_gz_db_file):
        assert isinstance(name, str)
        assert isinstance(model, models.OutputPackageBase)


def test_dump_db_to_json_files(
    create_gz_db_file: Path,
    create_dir_path: Path,
) -> None:
    operations.dump_db_to_json_files(input_path=create_gz_db_file, output_path=create_dir_path)


def test_dump_db_to_json_files_raises() -> None:
    input_path = Mock(
        exists=Mock(side_effect=[False, True, True, True]),
        is_file=Mock(side_effect=[False, True, True]),
    )
    output_path = Mock(
        exists=Mock(side_effect=[False, True]),
        is_dir=Mock(side_effect=[False]),
    )

    counter = 0
    while counter < 4:
        with raises(RuntimeError):
            operations.dump_db_to_json_files(input_path=input_path, output_path=output_path)
        counter += 1
