import os
import shutil
import tarfile
import tempfile
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import Iterator, List

from pytest import fixture, raises

from repo_management import files


def create_db_file(compression: str = "gz", remove_db: bool = False) -> Path:
    (file_number, db_file) = tempfile.mkstemp(suffix=".db")
    temp_dirs = [
        tempfile.mkdtemp(),
        tempfile.mkdtemp(),
        tempfile.mkdtemp(),
        tempfile.mkdtemp(),
    ]

    files: List[str] = []
    for tmp_dir in temp_dirs:
        for file_name in ["desc", "files"]:
            with open(f"{tmp_dir}/{file_name}", "x"):
                files += [f"{tmp_dir}/{file_name}"]

    with tarfile.open(db_file, f"w:{compression}") as db_tar:
        for name in temp_dirs + files:
            db_tar.add(name)

    for name in temp_dirs:
        shutil.rmtree(name)
    if remove_db:
        os.remove(db_file)

    return Path(db_file)


@fixture(scope="function")
def create_gz_db_file() -> Iterator[Path]:
    db_file = create_db_file()
    yield db_file
    os.remove(db_file)


@fixture(scope="function")
def create_bzip_db_file() -> Iterator[Path]:
    db_file = create_db_file(compression="bz2")
    yield db_file
    os.remove(db_file)


@fixture(scope="function")
def create_null_db_file() -> Iterator[Path]:
    yield create_db_file(remove_db=True)


def test__read_db_file(create_gz_db_file: Path) -> None:
    with does_not_raise():
        assert files._read_db_file(create_gz_db_file)


def test__read_db_file_wrong_compression(create_gz_db_file: Path) -> None:
    with raises(tarfile.CompressionError):
        assert files._read_db_file(create_gz_db_file, compression="foo")


def test__read_db_file_does_not_exist(create_null_db_file: Path) -> None:
    with raises(FileNotFoundError):
        assert files._read_db_file(create_null_db_file)


def test__read_db_file_wrong_db_compression(create_bzip_db_file: Path) -> None:
    with raises(tarfile.ReadError):
        assert files._read_db_file(create_bzip_db_file)


def test__read_db_file_member(create_gz_db_file: Path) -> None:
    for member in files._read_db_file_member(db_file=files._read_db_file(create_gz_db_file)):
        assert member
