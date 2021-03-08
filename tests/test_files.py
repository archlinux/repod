import os
import tarfile
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import Iterator

from pytest import fixture, mark, raises

from repo_management import files, models

from .fixtures import create_db_file


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


def test__read_db_file_member_as_model(create_gz_db_file: Path) -> None:
    for member in files._db_file_member_as_model(db_file=files._read_db_file(create_gz_db_file)):
        assert isinstance(member, models.RepoDbMemberData)


@mark.parametrize(
    "member_name, result",
    [
        ("foo-bar-1.0.0-42", "foo-bar"),
        ("foobar-1.0.0-42", "foobar"),
        ("foo-bar-1.0.0-42/desc", "foo-bar"),
        ("foo-bar-1.0.0-42/files", "foo-bar"),
        ("foobar-1.0.0-42/desc", "foobar"),
        ("foobar-1.0.0-42/files", "foobar"),
    ],
)
def test__extract_db_member_package_name(
    member_name: str,
    result: str,
) -> None:
    assert files._extract_db_member_package_name(name=member_name) == result
