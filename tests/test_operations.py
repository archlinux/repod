import os
from pathlib import Path
from typing import Iterator

from pytest import fixture

from repo_management import models, operations

from .fixtures import create_db_file


@fixture(scope="function")
def create_gz_db_file() -> Iterator[Path]:
    db_file = create_db_file()
    yield db_file
    os.remove(db_file)


def test_db_file_as_models(create_gz_db_file: Path) -> None:
    for (name, model) in operations.db_file_as_models(db_path=create_gz_db_file):
        assert isinstance(name, str)
        assert isinstance(model, models.OutputPackageBase)