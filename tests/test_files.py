import os
import shutil
import tarfile
import tempfile
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import Iterator

from pytest import fixture, mark, raises

from repo_management import convert, defaults, errors, files, models

from .fixtures import create_db_file, create_empty_json_files


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


@fixture(scope="function")
def empty_json_files_in_dir() -> Iterator[Path]:
    directory = create_empty_json_files()
    yield directory
    shutil.rmtree(directory)


@fixture(scope="function")
def empty_dir() -> Iterator[Path]:
    directory = tempfile.mkdtemp()
    yield Path(directory)
    shutil.rmtree(directory)


@fixture(scope="function")
def empty_file() -> Iterator[Path]:
    [foo, file_name] = tempfile.mkstemp()
    yield Path(file_name)


@fixture(scope="function")
def broken_json_file() -> Iterator[Path]:
    [foo, json_file] = tempfile.mkstemp(suffix=".json")
    with open(json_file, "w") as input_file:
        input_file.write("garbage")
    yield Path(json_file)


@fixture(scope="function")
def invalid_json_file() -> Iterator[Path]:
    [foo, json_file] = tempfile.mkstemp(suffix=".json")
    with open(json_file, "w") as input_file:
        input_file.write('{"foo": "bar"}')
    yield Path(json_file)


@mark.asyncio
async def test__read_db_file(create_gz_db_file: Path) -> None:
    with does_not_raise():
        assert await files._read_db_file(create_gz_db_file)


@mark.asyncio
async def test__read_db_file_wrong_compression(create_gz_db_file: Path) -> None:
    with raises(tarfile.CompressionError):
        assert await files._read_db_file(create_gz_db_file, compression="foo")


@mark.asyncio
async def test__read_db_file_does_not_exist(create_null_db_file: Path) -> None:
    with raises(FileNotFoundError):
        assert await files._read_db_file(create_null_db_file)


@mark.asyncio
async def test__read_db_file_wrong_db_compression(create_bzip_db_file: Path) -> None:
    with raises(tarfile.ReadError):
        assert await files._read_db_file(create_bzip_db_file)


@mark.asyncio
async def test__read_db_file_member_as_model(create_gz_db_file: Path) -> None:
    async for member in files._db_file_member_as_model(db_file=await files._read_db_file(create_gz_db_file)):
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
@mark.asyncio
async def test__extract_db_member_package_name(
    member_name: str,
    result: str,
) -> None:
    assert await files._extract_db_member_package_name(name=member_name) == result


@mark.asyncio
async def test__json_files_in_directory(empty_json_files_in_dir: Path, empty_dir: Path) -> None:
    async for json_file in files._json_files_in_directory(path=empty_json_files_in_dir):
        assert isinstance(json_file, Path)

    with raises(errors.RepoManagementFileNotFoundError):
        async for json_file in files._json_files_in_directory(path=empty_dir):
            assert isinstance(json_file, Path)


@mark.asyncio
async def test__read_pkgbase_json_file(broken_json_file: Path, invalid_json_file: Path) -> None:
    with raises(errors.RepoManagementFileError):
        await files._read_pkgbase_json_file(path=broken_json_file)
    with raises(errors.RepoManagementValidationError):
        await files._read_pkgbase_json_file(path=invalid_json_file)


@mark.asyncio
async def test__write_db_file(empty_dir: Path) -> None:
    with files._write_db_file(empty_dir / Path("foo.db")) as database:
        assert isinstance(database, tarfile.TarFile)


@mark.parametrize(
    "model, db_type",
    [
        (
            models.OutputPackageBase(
                base="foo",
                packager="foobar",
                version="1.0.0-1",
                packages=[
                    models.OutputPackage(
                        arch="foo",
                        builddate=1,
                        csize=1,
                        desc="foo",
                        filename="foo",
                        files=["foo", "bar"],
                        isize=1,
                        license=["foo"],
                        md5sum="foo",
                        name="foo",
                        pgpsig="foo",
                        sha256sum="foo",
                        url="foo",
                    ),
                ],
            ),
            defaults.RepoDbType.DEFAULT,
        ),
        (
            models.OutputPackageBase(
                base="foo",
                packager="foobar",
                version="1.0.0-1",
                packages=[
                    models.OutputPackage(
                        arch="foo",
                        builddate=1,
                        csize=1,
                        desc="foo",
                        filename="foo",
                        files=["foo", "bar"],
                        isize=1,
                        license=["foo"],
                        md5sum="foo",
                        name="foo",
                        pgpsig="foo",
                        sha256sum="foo",
                        url="foo",
                    ),
                ],
            ),
            defaults.RepoDbType.FILES,
        ),
    ],
)
@mark.asyncio
async def test__stream_package_base_to_db(
    model: models.OutputPackageBase,
    db_type: defaults.RepoDbType,
    empty_file: Path,
) -> None:
    with files._write_db_file(path=empty_file) as database:
        await files._stream_package_base_to_db(
            db=database,
            model=model,
            repodbfile=convert.RepoDbFile(),
            db_type=db_type,
        )
